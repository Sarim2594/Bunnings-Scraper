# Bunnings Product Scraper

This repository contains a Python-based web scraper that automatically extracts product information from the Bunnings Australia website. Specifically, it is currently configured to scrape the "Paint Decorating - Wood Finishes" category.

## Overview

The scraper uses Selenium WebDriver for browser automation to navigate through the Bunnings catalog, load product pages, and extract detailed specifications. To bypass basic bot detection and anti-scraping measures, it loads session cookies and uses a randomized delay between requests. The extracted data is saved into an Excel spreadsheet for easy analysis.

## Features

- **Automated Browser Control**: Uses Selenium with anti-detection flags (`--disable-blink-features=AutomationControlled`).
- **Session Handling**: Loads cookies from a `cookies.json` file to bypass anti-bot challenges and maintain sessions.
- **Resilient Extraction**: Skips unavailable products, handles "page not found" errors, and skips third-party Marketplace listings to ensure only valid Bunnings stock is recorded.
- **Progress Tracking**: Reads the existing output Excel file (`bunnings2.xlsx`) and only scrapes products that haven't been scraped yet. This allows you to pause and resume the script without duplicating work.
- **Comprehensive Data Collection**: Extracts a wide range of product details including:
  - Brand and Product Name
  - Price
  - Category / Tool Type (via breadcrumbs)
  - Online Only status
  - Specifications (Model Number, Dimensions, Weight, Motor Type)
  - Features & Detailed Description
  - Link to User Manual / Instructions

## Prerequisites

- **Python 3.7+**
- **Google Chrome**: Must be installed on your machine.
- **ChromeDriver**: Compatible with your installed version of Chrome.

### Required Python Packages

Install the required dependencies using pip:

```bash
pip install selenium pandas openpyxl
```

*(Note: `openpyxl` is required by Pandas to write and append to Excel files.)*

## Setup & Configuration

1. **Clone or Download** the project to your local machine.
2. **Cookies Configuration**:
   - The script expects a `cookies.json` file in the same directory.
   - Browse to the Bunnings website in your normal browser, solve any captchas, and use a browser extension (like "EditThisCookie" or "Export-Cookie-JSON") to export your session cookies.
   - Save the exported JSON array into a file named `cookies.json`.
3. **Target URL Modification** (Optional):
   - Open `main.py` and modify the `URL_TO_SCRAPE` variable to point to a different category if needed.
   - Adjust the page range in the `main()` function (`for l in range(1, 14):`) based on the total number of pages available in your chosen category.

## Usage

Run the script from your terminal:

```bash
python main.py
```

### Execution Flow

1. The script initializes a Chrome browser instance.
2. It navigates to the Bunnings homepage, applies the cookies from `cookies.json`, and refreshes the page to apply the session.
3. It iterates through the predefined range of pages of the target category.
4. On each page, it collects the URLs of all listed products.
5. It visits each product URL individually (with random 1-4 second time delays to simulate human behavior) and extracts the specifications.
6. Data is continuously appended to `bunnings2.xlsx` after each product is scraped. If the script crashes or is stopped manually, your data up to that point is saved securely.

## Output

The output is an Excel file named `bunnings2.xlsx`. 
- If the file doesn't exist, it will be created automatically. 
- If it does exist, new scraped products will be appended to it. 
- The scraper also flags products that might require manual review (e.g., missing price or missing model number) in a designated `review_required` column.

## Disclaimer

This scraper is built for educational and research purposes. Web scraping may violate the Terms of Service of some websites. Ensure you comply with Bunnings' terms of use and local regulations regarding automated data collection. Use responsibly and avoid sending too many requests in a short period to prevent server strain or getting your IP address blocked.
