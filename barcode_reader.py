import torch
import cv2
from pyzbar import pyzbar 
import streamlit as st
import numpy as np

# Load model globally outside the function so it only loads ONCE at startup
@st.cache_resource
def load_model():
    try:
        device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
        model = torch.hub.load('ultralytics/yolov5', 'custom', path='model.pt', force_reload=False).to(device)
        return model
    except Exception as e:
        st.error(f"Error loading model.pt: {e}")
        return None

def barcode_scanner():
    model = load_model()
    if model is None:
        st.stop()

    camera_image = st.camera_input("Take a picture of the food package / barcode")
    scanned_data = None

    if camera_image is not None:
        bytes_data = camera_image.getvalue()
        frame = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)

        results = model(frame)
        detections = results.pandas().xyxy[0]

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

    return scanned_data