import torch
import cv2
from pyzbar import pyzbar 
import streamlit as st
import numpy as np
from PIL import Image

def barcode_scanner():
    # Load your YOLOv5 model (cached so it doesn't reload every time)
    @st.cache_resource
    def load_model():
        device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
        model = torch.hub.load('ultralytics/yolov5', 'custom', path='model.pt').to(device)
        return model

    model = load_model()

    # Streamlit widget that safely opens the device/phone camera in the browser
    camera_image = st.camera_input("Take a picture of the food package / barcode")

    scanned_data = None

    if camera_image is not None:
        # Convert the uploaded Streamlit image buffer into an OpenCV-compatible NumPy array
        bytes_data = camera_image.getvalue()
        frame = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)

        # Run YOLOv5 object detection on the captured frame
        results = model(frame)
        detections = results.pandas().xyxy[0]

        barcode_scanned = False

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
                    barcode_scanned = True
                    break

            if barcode_scanned:
                break
        
        if not scanned_data and not detections.empty:
            # Fallback: try scanning the whole frame if YOLO crops missed the direct barcode code
            gray_full = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            full_barcodes = pyzbar.decode(gray_full)
            for barcode in full_barcodes:
                scanned_data = barcode.data.decode("utf-8")
                st.success(f"Barcode successfully scanned: {scanned_data}")
                break

        if not scanned_data:
            st.warning("No barcode detected. Please try again with better lighting or get closer.")

    return scanned_data