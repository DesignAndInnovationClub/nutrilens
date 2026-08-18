import cv2
import numpy as np
import streamlit as st
import zxingcpp

def barcode_scanner():
    """Robust barcode scanner supporting both live camera input and gallery photo uploads."""
    
    st.subheader("📷 Scan or Upload Barcode")
    
    # Give users options on how they want to provide the image
    input_method = st.radio("Choose input method:", ["Live Camera Capture", "Upload from Gallery"], horizontal=True)
    
    image_bytes = None

    if input_method == "Live Camera Capture":
        camera_file = st.camera_input("Take a picture of the food package barcode")
        if camera_file is not None:
            image_bytes = camera_file.getvalue()
    else:
        upload_file = st.file_uploader("Upload product photo or barcode image", type=["jpg", "jpeg", "png"])
        if upload_file is not None:
            image_bytes = upload_file.getvalue()

    if image_bytes is not None:
        # Convert raw bytes to OpenCV frame
        frame = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)

        if frame is None:
            st.error("Could not process the image. Please try another file.")
            return None

        # Optional preview of the selected image
        st.image(framechannels_to_rgb(frame) if 'framechannels_to_rgb' in globals() else cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), caption="Processed Image", width=300)

        # Apply zxing-cpp processing pipeline
        gaussian = cv2.GaussianBlur(frame, (0, 0), 2.0)
        sharpened = cv2.addWeighted(frame, 1.5, gaussian, -0.5, 0)

        try:
            results = zxingcpp.read_barcodes(sharpened, try_rotate=True, try_downscale=True)

            if results:
                scanned_data = results[0].text
                st.success(f"Barcode successfully scanned: {scanned_data}")
                return scanned_data
            else:
                # Fallback to original frame
                results_fallback = zxingcpp.read_barcodes(frame)
                if results_fallback:
                    scanned_data = results_fallback[0].text
                    st.success(f"Barcode successfully scanned: {scanned_data}")
                    return scanned_data
                
                st.warning("No barcode detected in this image. Make sure the barcode lines are clear and visible.")

        except Exception as e:
            st.error(f"Scanning error: {e}")

    return None