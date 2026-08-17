import cv2
from pyzbar import pyzbar 
import streamlit as st
import numpy as np

def barcode_scanner():
    """Lightweight barcode scanner that opens instantly without hanging the server."""
    
    # Native browser camera input widget
    camera_image = st.camera_input("Take a clear picture of the food barcode")
    scanned_data = None

    if camera_image is not None:
        # Convert Streamlit image buffer into an OpenCV-compatible NumPy array
        bytes_data = camera_image.getvalue()
        frame = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)

        # Convert straight to grayscale for maximum pyzbar decoding speed
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Decode barcodes directly from the snapshot
        barcodes = pyzbar.decode(gray)

        if barcodes:
            for barcode in barcodes:
                scanned_data = barcode.data.decode("utf-8")
                st.success(f"Barcode successfully scanned: {scanned_data}")
                return scanned_data
        else:
            st.warning("No barcode detected. Please try getting closer or ensuring good lighting.")

    return scanned_data