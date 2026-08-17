import torch
import cv2
from pyzbar import pyzbar 


def barcode_scanner():
    device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
    model = torch.hub.load('ultralytics/yolov5', 'custom', path='model.pt').to(device)

    cap = cv2.VideoCapture(0)


    barcode_scanned = False 

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

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
                    print(f"Barcode successfully scanned: {scanned_data}")
  
                    barcode_scanned = True
                    break

            if barcode_scanned:
                break

        cv2.imshow('Result', frame)

        if barcode_scanned:
            print("Stopping camera feed.")
            cv2.waitKey(1000)  # Optional: Brief delay to view final frame
            break

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

   
    cap.release()
    cv2.destroyAllWindows() # Call the function to fetch product info
    return scanned_data  # Return the scanned barcode data


