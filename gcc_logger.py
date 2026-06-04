import asyncio
import sys
import cv2
import os
import csv
import numpy as np
from datetime import datetime
from playwright.async_api import async_playwright

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

def calculate_masked_gcc(image, mask_path='canopy_mask.png'):
    mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
    if mask is None:
        print("Warning: canopy_mask.png not found. Calculating full frame.")
        mask = np.ones(image.shape[:2], dtype=np.uint8) * 255

    b, g, r = cv2.split(image.astype(float))
    total = b + g + r
    total[total == 0] = 1 
    
    gcc = g / total
    valid_pixels = gcc[mask == 255]
    
    return np.mean(valid_pixels)

async def get_live_m3u8(page_url):
    m3u8_url = None
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        def handle_response(response):
            nonlocal m3u8_url
            if "chunklist.m3u8" in response.url or "playlist.m3u8" in response.url:
                m3u8_url = response.url
                
        page.on("response", handle_response)
        await page.goto(page_url)
        await page.wait_for_timeout(5000) 
        await browser.close()
    return m3u8_url

async def main():
    webcam_url = "https://hdontap.com/stream/178090/holy-cross-hogan-courtyard-live-webcam/"
    csv_file = "phenocam_data.csv"
    
    now = datetime.now()
    timestamp_str = now.strftime('%Y-%m-%d %H:%M:%S')
    
    # Check if CSV exists to write headers
    write_header = not os.path.exists(csv_file)

    fresh_link = await get_live_m3u8(webcam_url)
    
    if fresh_link:
        cap = cv2.VideoCapture(fresh_link)
        ret, frame = cap.read()
        cap.release()
        
        if ret:
            gcc_val = calculate_masked_gcc(frame)
            print(f"[{timestamp_str}] GCC Captured: {gcc_val:.4f}")
            
            # Log to CSV
            with open(csv_file, mode='a', newline='') as file:
                writer = csv.writer(file)
                if write_header:
                    writer.writerow(["timestamp", "gcc"])
                writer.writerow([timestamp_str, round(gcc_val, 4)])
        else:
            print("Failed to read frame.")
    else:
        print("Could not intercept stream.")

if __name__ == "__main__":
    asyncio.run(main())