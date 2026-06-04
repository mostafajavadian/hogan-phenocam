import asyncio
import sys
import cv2
import os
from datetime import datetime
from playwright.async_api import async_playwright

# Fix for Windows asyncio loop when running outside Jupyter
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

async def get_live_m3u8(page_url):
    """Intercepts the HDOnTap network traffic to grab the live stream URL."""
    m3u8_url = None

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        def handle_response(response):
            nonlocal m3u8_url
            if "chunklist.m3u8" in response.url or "playlist.m3u8" in response.url:
                m3u8_url = response.url

        page.on("response", handle_response)

        print("Loading page and intercepting network traffic...")
        await page.goto(page_url)
        await page.wait_for_timeout(5000) 
        await browser.close()

    return m3u8_url

async def main():
    webcam_url = "https://hdontap.com/stream/178090/holy-cross-hogan-courtyard-live-webcam/"

    # 1. Get current date and time
    now = datetime.now()
    year_str = now.strftime('%Y')
    month_str = now.strftime('%m') # '01' to '12'

    # 2. Build the directory path: phenology_images/YYYY/MM
    # If you want this to save directly to your local Google Drive, 
    # change base_dir to your Drive path, e.g., r"C:\Users\mj2387\Google Drive\phenology_images"
    base_dir = "phenology_images"
    save_dir = os.path.join(base_dir, year_str, month_str)

    # Create the directories if they don't exist
    os.makedirs(save_dir, exist_ok=True)

    # 3. Format the filename: HC1_YYYY_MM_DD_HH_MM.jpg
    filename = f"HC1_{now.strftime('%Y_%m_%d_%H_%M')}.jpg"
    filepath = os.path.join(save_dir, filename)

    # 4. Fetch the stream and capture the image
    fresh_link = await get_live_m3u8(webcam_url)

    if fresh_link:
        print("Stream intercepted. Extracting frame...")
        cap = cv2.VideoCapture(fresh_link)
        ret, frame = cap.read()
        cap.release()

        if ret:
            # Save the image to the constructed path
            cv2.imwrite(filepath, frame)
            print(f"Success! Image saved to:\n{filepath}")
        else:
            print("Failed to read frame from the video stream.")
    else:
        print("Could not intercept the stream link.")

if __name__ == "__main__":
    asyncio.run(main())
