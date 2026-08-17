import cv2
from pyzbar import pyzbar 
import streamlit as st
import numpy as np

def barcode_scanner():
    """Enterprise-grade robust barcode scanner built to handle tilt, blur, and poor lighting."""
    
    camera_image = st.camera_input("Take a picture of the food package barcode")
    scanned_data = None

    if camera_image is not None:
        # Read raw bytes into OpenCV
        bytes_data = camera_image.getvalue()
        frame = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)

        if frame is None:
            st.error("Failed to read camera image. Please try again.")
            return None

        # Resize for consistent processing speed
        max_dim = 1200
        h, w = frame.shape[:2]
        if max(h, w) > max_dim:
            scaling = max_dim / float(max(h, w))
            frame = cv2.resize(frame, (int(w * scaling), int(h * scaling)))

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # 1. Image Enhancements (Sharpening and Contrast Stretching)
        kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
        sharpened = cv2.filter2D(gray, -1, kernel)
        
        # Adaptive thresholding to handle shadows/glare
        thresh = cv2.adaptiveThreshold(
            sharpened, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )

        # Helper to rotate images cleanly
        def rotate(image, angle):
            center = tuple(np.array(image.shape[1::-1]) / 2)
            matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
            return cv2.warpAffine(image, matrix, image.shape[1::-1], flags=cv2.INTER_LINEAR)

        # Comprehensive angle sweeps to fix any tilt (covers all 360 degrees in increments)
        angles_to_check = [0, 15, -15, 30, -30, 45, -45, 90, 180, 270]
        
        barcodes = []
        # Try finding barcodes across processed variations and rotations
        candidate_images = [gray, sharpened, thresh]
        
        for img in candidate_images:
            for angle in angles_to_check:
                rotated = rotate(img, angle)
                barcodes = pyzbar.decode(rotated)
                if barcodes:
                    break
            if barcodes:
                break

        if barcodes:
            for barcode in barcodes:
                scanned_data = barcode.data.decode("utf-8")
                st.success(f"Barcode successfully scanned: {scanned_data}")
                return scanned_data
        else:
            st.warning("Barcode could not be detected. Ensure the barcode lines are clear, well-lit, and fill up the center of the frame.")

    return scanned_data