import asyncio
import sys
import cv2
import numpy as np
from playwright.async_api import async_playwright

# This line fixes the Windows subprocess issue when running outside Jupyter
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

def calculate_gcc(image):
    # Convert to float to prevent uint8 overflow
    b, g, r = cv2.split(image.astype(float))
    total = b + g + r
    total[total == 0] = 1 

    gcc = g / total
    return np.mean(gcc)

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

        print("Loading page and intercepting network traffic...")
        await page.goto(page_url)
        await page.wait_for_timeout(5000) 
        await browser.close()

    return m3u8_url

async def main():
    webcam_url = "https://hdontap.com/stream/178090/holy-cross-hogan-courtyard-live-webcam/"

    fresh_link = await get_live_m3u8(webcam_url)

    if fresh_link:
        print(f"Success! Intercepted URL:\n{fresh_link}\n")

        print("Extracting frame...")
        cap = cv2.VideoCapture(fresh_link)
        ret, frame = cap.read()
        cap.release()

        if ret:
            gcc_val = calculate_gcc(frame)
            print(f"Current GCC (Full Frame): {gcc_val:.4f}")

            # Save the frame so you can build your ROI mask
            cv2.imwrite("hogan_courtyard_reference.jpg", frame)
            print("Saved image as 'hogan_courtyard_reference.jpg'")
        else:
            print("Failed to read frame.")
    else:
        print("Could not intercept the stream link.")

if __name__ == "__main__":
    asyncio.run(main())
