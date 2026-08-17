import torch
import cv2
from pyzbar import pyzbar 
import streamlit as st
import numpy as np
import pathlib

# Fix for path compatibility across different operating systems (Windows vs Linux cloud servers)
try:
    temp = pathlib.PosixPath
    pathlib.PosixPath = pathlib.WindowsPath if pathlib.Path('.').drive else pathlib.PosixPath
except Exception:
    pass

@st.cache_resource
def load_model():
    """Loads the YOLOv5 model safely and caches it so it doesn't reload or hang."""
    try:
        # Force CPU-only mode for stability and to prevent memory limits on free cloud tiers
        device = torch.device('cpu')
        
        # Direct load to avoid torch.hub external network timeouts
        model = torch.load('model.pt', map_location=device)
        
        if hasattr(model, 'eval'):
            model.eval()
            
        return model
    except Exception as e:
        st.error(f"Failed to load model.pt: {e}")
        return None

def barcode_scanner():
    # Initialize the model
    model = load_model()
    if model is None:
        st.stop()

    # Native browser camera input widget (works on mobile phones and laptops)
    camera_image = st.camera_input("Take a picture of the food package / barcode")
    scanned_data = None

    if camera_image is not None:
        # Convert Streamlit image buffer into an OpenCV-compatible NumPy array
        bytes_data = camera_image.getvalue()
        frame = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)

        # Run YOLOv5 object detection on the captured frame
        try:
            results = model(frame)
            detections = results.pandas().xyxy[0]
        except Exception as e:
            st.error(f"Error during model inference: {e}")
            return None

        # Check for barcodes within detected bounding boxes
        for i, detection in detections.iterrows():
            x1, y1, x2, y2 = detection[['xmin', 'ymin', 'xmax', 'ymax']]
            x1, y1, x2, y2 = [round(num) for num in [x1, y1, x2, y2]]

            h, w, _ = frame.shape
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w, x2), min(h, y2)

            if x2 > x1 and y2 > y1:
                cropped_img = frame[y1:y2, x1:x2]
                gray = cv2.cvtColor(cropped_img, cv2.COLOR_BGR2GRAY)
                barcodes = pyzbar.decode(gray)

                for barcode in barcodes:
                    scanned_data = barcode.data.decode("utf-8")
                    st.success(f"Barcode successfully scanned: {scanned_data}")
                    return scanned_data

        # Fallback: Scan the entire frame if YOLO bounds missed the exact barcode edges
        gray_full = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        full_barcodes = pyzbar.decode(gray_full)
        for barcode in full_barcodes:
            scanned_data = barcode.data.decode("utf-8")
            st.success(f"Barcode successfully scanned: {scanned_data}")
            return scanned_data

        if not scanned_data:
            st.warning("No barcode detected. Please try again with better lighting or get closer.")

    return scanned_data