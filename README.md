# Holy Cross Phenocam: Automated GCC Tracking

An automated, serverless data pipeline that continuously tracks vegetation phenology and water stress using the live webcam overlooking the Hogan Courtyard at the College of the Holy Cross.

## 📊 Live Dashboard
**[View the Interactive Phenocam Dashboard Here](https://mostafajavadian.github.io/hogan-phenocam/)**

## 🔬 Scientific Overview
This project extracts the **Green Chromatic Coordinate (GCC)** from an HDOnTap live webcam feed to monitor the seasonal ecohydrological state of the campus canopy. The GCC is calculated as:
`GCC = G / (R + G + B)`

By utilizing a static Region of Interest (ROI) mask, the script isolates the tree canopies from the surrounding brick buildings and sky, ensuring the phenological signal accurately reflects vegetation health and seasonal transitions.

## ⚙️ Architecture & Tech Stack
This repository operates entirely in the cloud with zero hosting costs, utilizing:
* **Python & OpenCV:** For image processing and array manipulation.
* **Playwright:** To operate a headless Chromium browser and intercept dynamic, token-protected `.m3u8` stream URLs.
* **GitHub Actions:** A cron-scheduled CI/CD workflow that runs the extraction script every 30 minutes.
* **GitHub Pages & Plotly.js:** Hosts the front-end interactive time-series dashboard.

## 🚀 Features
1. **High-Frequency Monitoring:** Automatically captures and processes a frame every 30 minutes.
2. **Lightweight Storage:** Appends data to a single `phenocam_data.csv` rather than hoarding gigabytes of raw images, keeping the repository well under GitHub's storage limits.
3. **Midday Image Archiving:** Automatically saves one `latest_midday.jpg` at 12:00 PM EST daily to provide visual context alongside the data graph.
4. **Timezone Aware:** Data is standardized to US Eastern Time to accurately reflect local daylight constraints.

## 💻 Local Development
If you need to clone this repository to redraw the canopy mask or run tests locally:

1. Clone the repository and install dependencies:
   ```bash
   pip install playwright opencv-python-headless numpy pandas pytz
