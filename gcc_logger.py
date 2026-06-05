import asyncio
import sys
import cv2
import os
import csv
import numpy as np
from datetime import datetime
import pytz
from playwright.async_api import async_playwright

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

def calculate_roi_stats(image, mask_path='canopy_mask.png'):
    mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
    if mask is None:
        print("Warning: canopy_mask.png not found. Calculating full frame.")
        mask = np.ones(image.shape[:2], dtype=np.uint8) * 255

    b, g, r = cv2.split(image.astype(float))
    total = b + g + r
    total[total == 0] = 1 
    
    gcc = g / total
    valid_pixels = gcc[mask == 255]
    
    if len(valid_pixels) == 0:
        return None, mask
        
    stats = {
        'mean': np.mean(valid_pixels),
        'median': np.median(valid_pixels),
        'min': np.min(valid_pixels),
        'max': np.max(valid_pixels),
        'q25': np.percentile(valid_pixels, 25),
        'q75': np.percentile(valid_pixels, 75)
    }
    
    return stats, mask

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
    
    eastern = pytz.timezone('US/Eastern')
    now = datetime.now(eastern)
    timestamp_str = now.strftime('%Y-%m-%d %H:%M:%S')
    
    write_header = not os.path.exists(csv_file)

    fresh_link = await get_live_m3u8(webcam_url)
    
    if fresh_link:
        cap = cv2.VideoCapture(fresh_link)
        ret, frame = cap.read()
        cap.release()
        
        if ret:
            stats, mask = calculate_roi_stats(frame)
            
            if stats:
                print(f"[{timestamp_str}] Median GCC: {stats['median']:.4f}")
                
                # Log to CSV
                with open(csv_file, mode='a', newline='') as file:
                    writer = csv.writer(file)
                    if write_header:
                        writer.writerow(["timestamp", "gcc_mean", "gcc_median", "gcc_min", "gcc_max", "gcc_q25", "gcc_q75"])
                    
                    writer.writerow([
                        timestamp_str, 
                        round(stats['mean'], 4), 
                        round(stats['median'], 4), 
                        round(stats['min'], 4), 
                        round(stats['max'], 4), 
                        round(stats['q25'], 4), 
                        round(stats['q75'], 4)
                    ])
                    
                # ALWAYS save the latest image with the ROI overlaid
                contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                cv2.drawContours(frame, contours, -1, (0, 255, 0), 2)
                
                # Overwrite the latest_image.jpg file
                cv2.imwrite("latest_image.jpg", frame)
                print("Saved new latest_image.jpg with ROI overlay.")
            else:
                print("Error: No valid pixels found in mask.")
                
        else:
            print("Failed to read frame.")
    else:
        print("Could not intercept stream.")

if __name__ == "__main__":
    asyncio.run(main())
