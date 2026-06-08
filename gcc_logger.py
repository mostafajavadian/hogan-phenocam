import asyncio
import sys
import cv2
import os
import csv
import numpy as np
import pandas as pd
from datetime import datetime
import pytz
from astral import LocationInfo
from astral.sun import elevation
from playwright.async_api import async_playwright

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

def calculate_advanced_phenology(image, mask_path='canopy_mask.png'):
    mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
    if mask is None:
        print("Warning: canopy_mask.png not found. Calculating full frame.")
        mask = np.ones(image.shape[:2], dtype=np.uint8) * 255

    b, g, r = cv2.split(image.astype(float))
    total = b + g + r
    total[total == 0] = 1 
    
    gcc = g / total
    rcc = r / total
    bcc = b / total
    exg = (2 * g) - r - b
    
    valid_mask = mask == 255
    
    if not np.any(valid_mask):
        return None, mask
        
    stats = {
        'gcc_mean': np.mean(gcc[valid_mask]),
        'gcc_median': np.median(gcc[valid_mask]),
        'gcc_90th': np.percentile(gcc[valid_mask], 90),
        'rcc_median': np.median(rcc[valid_mask]),
        'bcc_median': np.median(bcc[valid_mask]),
        'exg_median': np.median(exg[valid_mask])
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

    city = LocationInfo("Worcester", "Massachusetts", "US/Eastern", 42.2626, -71.8023)
    sun_elev = elevation(city.observer, now)
    is_daylight = sun_elev > 5.0 

    fresh_link = await get_live_m3u8(webcam_url)
    
    if fresh_link:
        cap = cv2.VideoCapture(fresh_link)
        ret, frame = cap.read()
        cap.release()
        
        if ret:
            stats, mask = calculate_advanced_phenology(frame)
            
            # 1. Append the new row of data
            with open(csv_file, mode='a', newline='') as file:
                writer = csv.writer(file)
                if write_header:
                    # Added 'is_outlier' column
                    writer.writerow(["timestamp", "gcc_mean", "gcc_median", "gcc_90th", "rcc_median", "bcc_median", "exg_median", "is_outlier"])
                
                if is_daylight and stats:
                    print(f"[{timestamp_str}] Daylight (Elev: {sun_elev:.1f}°). GCC 90th: {stats['gcc_90th']:.4f}")
                    writer.writerow([
                        timestamp_str, round(stats['gcc_mean'], 4), round(stats['gcc_median'], 4), 
                        round(stats['gcc_90th'], 4), round(stats['rcc_median'], 4), 
                        round(stats['bcc_median'], 4), round(stats['exg_median'], 4), 0
                    ])
                else:
                    print(f"[{timestamp_str}] Nighttime/Twilight (Elev: {sun_elev:.1f}°). Skipping data.")
                    writer.writerow([timestamp_str, "", "", "", "", "", "", 0])

            # 2. Daily Outlier Detection using Pandas (IQR Method)
            try:
                df = pd.read_csv(csv_file)
                df['datetime'] = pd.to_datetime(df['timestamp'])
                df['date'] = df['datetime'].dt.date
                
                # Reset all flags to recalculate cleanly
                df['is_outlier'] = 0 
                
                # Group by day and calculate bounds
                grouped = df[df['gcc_90th'].notnull()].groupby('date')
                for date, group in grouped:
                    if len(group) >= 4: # Need enough points in a day to find outliers
                        q1 = group['gcc_90th'].quantile(0.25)
                        q3 = group['gcc_90th'].quantile(0.75)
                        iqr = q3 - q1
                        lower_bound = q1 - 1.5 * iqr
                        upper_bound = q3 + 1.5 * iqr
                        
                        # Find indices of outliers and flag them
                        outlier_indices = group[(group['gcc_90th'] < lower_bound) | (group['gcc_90th'] > upper_bound)].index
                        df.loc[outlier_indices, 'is_outlier'] = 1
                
                # Clean up and overwrite CSV
                df.drop(columns=['datetime', 'date'], inplace=True)
                df.to_csv(csv_file, index=False)
                print("Daily outlier check complete.")
            except Exception as e:
                print(f"Outlier processing skipped/failed: {e}")

            # 3. Save the image
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cv2.drawContours(frame, contours, -1, (0, 255, 0), 2)
            cv2.imwrite("latest_image.jpg", frame)
                
        else:
            print("Failed to read frame.")
    else:
        print("Could not intercept stream.")

if __name__ == "__main__":
    asyncio.run(main())
