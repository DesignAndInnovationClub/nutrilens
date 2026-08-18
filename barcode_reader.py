import cv2
import numpy as np
import streamlit as st
import zxingcpp

def barcode_scanner():
    st.subheader("📷 Scan or Upload Barcode")
    input_method = st.radio("Choose input method:", ["Live Camera Capture", "Upload from Gallery"], horizontal=True)
    
    image_bytes = None
    if input_method == "Live Camera Capture":
        camera_file = st.camera_input("Take a picture of the barcode")
        if camera_file is not None:
            image_bytes = camera_file.getvalue()
    else:
        upload_file = st.file_uploader("Upload barcode image", type=["jpg", "jpeg", "png"])
        if upload_file is not None:
            image_bytes = upload_file.getvalue()

    if image_bytes is not None:
        frame = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
        if frame is None:
            st.error("Could not process the image.")
            return None

        # --- DIGITAL ZOOM / CROP SLIDER ---
        # Allows users to crop into the center if the barcode is too small/far away
        h, w, _ = frame.shape
        st.write("🔍 **Digital Zoom / Adjust Focus Area**")
        zoom_level = st.slider("Zoom Level", min_value=1.0, max_value=3.0, value=1.0, step=0.1)

        if zoom_level > 1.0:
            crop_h, crop_w = int(h / zoom_level), int(w / zoom_level)
            start_h, start_w = (h - crop_h) // 2, (w - crop_w) // 2
            frame = frame[start_h:start_h+crop_h, start_w:start_w+crop_w]
            frame = cv2.resize(frame, (w, h))  # Scale back up

        # Sharpening filter to fix blur
        gaussian = cv2.GaussianBlur(frame, (0, 0), 2.0)
        sharpened = cv2.addWeighted(frame, 1.5, gaussian, -0.5, 0)

        try:
            results = zxingcpp.read_barcodes(sharpened, try_rotate=True, try_downscale=True)
            if results:
                scanned_data = results[0].text
                st.success(f"Barcode successfully scanned: {scanned_data}")
                return scanned_data
            else:
                results_fallback = zxingcpp.read_barcodes(frame)
                if results_fallback:
                    scanned_data = results_fallback[0].text
                    st.success(f"Barcode successfully scanned: {scanned_data}")
                    return scanned_data
                st.warning("No barcode detected. Try adjusting the zoom slider or uploading a clearer image.")
        except Exception as e:
            st.error(f"Scanning error: {e}")

    return None