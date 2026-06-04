import cv2
import os
import time
from datetime import datetime

stream_url = "https://live.hdontap.com/hls/hosb1/hogan_holycross.stream/chunklist.m3u8?e=1772098855&eh=edge03.nginx.hdontap.com&t=MyjWmNrSHhAoivqhrcYdCA"

# Use the absolute path to force the exact save location
base_dir = r"C:\Users\mj2387\OneDrive - University of Arizona\ETC\Small studies\Holy_Cross_Pehnology_Livecam\Code\phenology_images"

cap = cv2.VideoCapture(stream_url)

# Try reading up to 5 times in case the stream is slow to open
success = False
for i in range(5):
    success, frame = cap.read()
    if success:
        break
    time.sleep(2)

if success:
    now = datetime.now()
    year = now.strftime("%Y")
    month = now.strftime("%m")
    day = now.strftime("%d")
    
    save_path = os.path.join(base_dir, year, month, day)
    os.makedirs(save_path, exist_ok=True)
    
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    filename = f"gcc_{timestamp}.jpg"
    full_file_path = os.path.join(save_path, filename)
    
    cv2.imwrite(full_file_path, frame)
        
cap.release()