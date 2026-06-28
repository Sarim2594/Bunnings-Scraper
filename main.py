import os
import json
import time
import random
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC

URL_TO_SCRAPE = "https://www.bunnings.com.au/products/paint-decorating/wood-finishes"
WEBSITE_LINK = "https://www.bunnings.com.au"
EXCEL_FILE = "bunnings2.xlsx"
COOKIES_FILE = "cookies.json"
WAIT_TIME = 10


def init_driver():
    options = Options()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--start-maximized")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(options=options)


def load_cookies():
    try:
        with open(COOKIES_FILE, "r") as file:
            return json.load(file)
    except Exception:
        return []


def convert_to_selenium_cookie(cookie):
    return {
        "name": cookie["name"],
        "value": cookie["value"],
        "domain": cookie["domain"],
        "path": cookie["path"],
        "secure": cookie.get("secure", False),
        "expiry": int(cookie["expirationDate"]) if "expirationDate" in cookie else None,
    }


def apply_cookies(driver):
    driver.get(WEBSITE_LINK)
    time.sleep(3)
    for cookie in load_cookies():
        try:
            driver.add_cookie(convert_to_selenium_cookie(cookie))
        except Exception:
            continue
    driver.refresh()
    time.sleep(5)


def get_columns():
    if os.path.exists(EXCEL_FILE):
        return pd.read_excel(EXCEL_FILE).columns.tolist()
    return []


def get_scraped_tools():
    if not os.path.exists(EXCEL_FILE):
        return set()
    try:
        df = pd.read_excel(EXCEL_FILE)
        return df["URL"].dropna() if "URL" in df.columns else set()
    except Exception:
        return set()


def save_to_excel(data, columns):
    for col in columns:
        data.setdefault(col, "N/A")
    if not data.get("Price") or not data.get("Model no."):
        data["review_required"] = True
    else:
        data["review_required"] = ""
    new_row = {col: data.get(col, "N/A") for col in columns}
    df = (
        pd.read_excel(EXCEL_FILE)
        if os.path.exists(EXCEL_FILE)
        else pd.DataFrame(columns=columns)
    )
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df = df.loc[:, ~df.columns.str.contains("^Unnamed")]
    df.to_excel(EXCEL_FILE, index=False)


def reset_data(columns):
    return {col: "N/A" for col in columns}


def update_data_dict(data, columns, label, value):
    if label not in columns:
        columns.append(label)
    data[label] = value


def get_tool_type(driver):
    breadcrumb_items = driver.find_elements(
        By.CSS_SELECTOR, 'nav[aria-label="Breadcrumb"] ol li.show-hide-item'
    )
    if breadcrumb_items:
        return breadcrumb_items[-1].text.strip()
    return "N/A"


def extract_links(driver, scraped_tools):
    links = []
    try:
        if driver.find_elements(
            By.XPATH, "//h2[contains(text(), 'Sorry, we hit a snag!')]"
        ):
            print("⚠ Page error. Skipping.")
            breakpoint()
    except:
        pass
    try:
        products = WebDriverWait(driver, WAIT_TIME).until(
            EC.presence_of_all_elements_located((By.TAG_NAME, "article"))
        )
        for product in products:
            try:
                href = (
                    product.find_element(By.TAG_NAME, "a")
                    .get_attribute("href")
                    .strip()
                    .rstrip("/")
                )
                if href not in scraped_tools:
                    links.append(href)
            except:
                continue
    except:
        print("⚠ No products found.")
    return links


def scrape_bunnings(driver, scraped_tools, columns):
    links = extract_links(driver, scraped_tools)
    for url in links:
        time.sleep(random.uniform(2, 4))
        driver.get(url)
        extract_specifications(driver, scraped_tools, columns, url)
        time.sleep(random.uniform(1, 3))


def extract_specifications(driver, scraped_tools, columns, tool_url):
    time.sleep(random.uniform(2, 4))
    data = reset_data(columns)

    wait = WebDriverWait(driver, 2)
    try:
        elements = wait.until(
            EC.presence_of_all_elements_located(
                (
                    By.XPATH,
                    "//h2[contains(text(), 'Oops! This product is no longer available.')]",
                )
            )
        )
        if elements:
            print("⚠ Product unavailable. Skipping.")
            return
    except:
        pass
    try:
        elements = wait.until(
            EC.presence_of_all_elements_located(
                (By.XPATH, "//h2[contains(text(), 'Sorry, we hit a snag!')]")
            )
        )
        if elements:
            print("⚠ Page error. Skipping.")
            breakpoint()
    except:
        pass
    try:
        not_found = wait.until(
            EC.presence_of_element_located(
                (
                    By.CSS_SELECTOR,
                    "MuiTypography-root.link-headings.increase-h2.MuiTypography-h2",
                )
            )
        )
        if not_found.text.strip() == "Sorry, page not found!":
            return
    except:
        pass
    try:
        badges = wait.until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "div.absolute.right-5 div.pdpBadgeText")
            )
        )
        badges = [badge.text.strip() for badge in badges]
        if "Marketplace" in badges:
            print("⚠ Marketplace listing. Skipping.")
            return
    except:
        pass

    try:
        driver.find_element(By.CSS_SELECTOR, "span[aria-labelledby='Online Only']")
        update_data_dict(data, columns, "Online only", True)
    except:
        update_data_dict(data, columns, "Online only", False)

    try:
        brand = driver.find_element(
            By.CSS_SELECTOR, "a[data-locator='product-brand-name']"
        ).text.strip()
        update_data_dict(data, columns, "Brand", brand)
    except:
        update_data_dict(data, columns, "Brand", "N/A")

    try:
        name_elem = WebDriverWait(driver, 3).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, ".MuiTypography-root.sc-500f213-2")
            )
        )
        tool_name = name_elem.text
        update_data_dict(data, columns, "Tool name", tool_name)
    except:
        print("⚠ Tool name not found.")
        return

    try:
        price = driver.find_element(
            By.CSS_SELECTOR, 'p[data-locator="product-price"]'
        ).text
        update_data_dict(data, columns, "Price", price)
    except:
        update_data_dict(data, columns, "Price", "N/A")

    update_data_dict(data, columns, "Tool Type", get_tool_type(driver))
    update_data_dict(data, columns, "URL", tool_url)

    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        try:
            spec_tab = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.ID, "radix-8"))
            )
            if spec_tab.text != "Specifications":
                spec_tab = WebDriverWait(driver, 100).until(
                    EC.presence_of_element_located((By.ID, "radix-7"))
                )
            driver.execute_script("arguments[0].click();", spec_tab)
        except:
            print("⚠ Specification tab not found.")

        elements = driver.find_elements(By.CSS_SELECTOR, "div.p-4")

        for element in elements:
            try:
                label = element.find_element(
                    By.CSS_SELECTOR, "dt.mb-1.text-xs.font-bold"
                ).text.strip()
                value = element.find_element(
                    By.CSS_SELECTOR, "dd.font-normal"
                ).text.strip()
                update_data_dict(data, columns, label, value)
            except:
                pass
            try:
                paragraphs = element.find_elements(By.TAG_NAME, "p")
                if (
                    len(paragraphs) >= 2
                    and paragraphs[0].text.strip() == "Model Number"
                ):
                    update_data_dict(
                        data, columns, "Model no.", paragraphs[1].text.strip()
                    )
                    break
            except:
                pass

        try:
            if (
                WebDriverWait(driver, 10)
                .until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "h3.pb-4.font-heading.text-xl.font-extrabold")
                    )
                )
                .text.strip()
                == "Dimensions"
            ):
                while True:
                    try:
                        label = WebDriverWait(driver, 100).until(
                            EC.visibility_of_all_elements_located(
                                (
                                    By.CSS_SELECTOR,
                                    "div.grid.grid-cols-4.content-center th p.text-xs.font-bold",
                                )
                            )
                        )
                        while len(label) > 3:
                            label.pop()
                        label = [l.text.strip() for l in label]
                        value = WebDriverWait(driver, 100).until(
                            EC.visibility_of_all_elements_located(
                                (
                                    By.CSS_SELECTOR,
                                    "div.grid.grid-cols-4.content-center div.h-12 p.text-center",
                                )
                            )
                        )
                        value = [v.text.strip() for v in value]
                        for v, l in zip(value, label):
                            update_data_dict(data, columns, l, v)
                        break
                    except:
                        print("⚠ Manually check dimensions.")
                        breakpoint()
        except:
            print("⚠ Unable to find dimensions.")

        try:
            weight = (
                WebDriverWait(driver, 10)
                .until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "div.font-body.pb-6 div.border-b-4.p-5 span")
                    )
                )
                .text.strip()
            )
            for w in weight.split():
                if "kg" in w.lower():
                    update_data_dict(data, columns, "Weight", w)
                    break
        except:
            print("⚠ Weight not found.")

        try:
            features = [
                f.text
                for f in driver.find_elements(
                    By.CSS_SELECTOR, "[data-locator='features_list'] li"
                )
            ]
            if features:
                update_data_dict(data, columns, "Features", ", ".join(features))
            description = driver.find_element(
                By.CSS_SELECTOR, ".whitespace-pre-wrap"
            ).text.strip()
            update_data_dict(data, columns, "Description", description)
        except Exception as e:
            print("⚠ Description/features error:", e)

        try:
            manual_tab = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.ID, "radix-9"))
            )
            driver.execute_script("arguments[0].click();", manual_tab)
            manual = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        "//a[contains(@aria-label, 'Manual') or contains(@aria-label, 'Instructions')]",
                    )
                )
            )
            update_data_dict(data, columns, "User Manual", manual.get_attribute("href"))
            if data.get("Motor Type") == "N/A":
                if "brushless" in tool_name.lower():
                    update_data_dict(data, columns, "Motor Type", "Brushless")
                else:
                    update_data_dict(data, columns, "Motor Type", "Brushed")
        except:
            update_data_dict(data, columns, "User Manual", "N/A")

    except Exception as e:
        print(f"⚠ Extraction error: {e}")

    save_to_excel(data, columns)
    scraped_tools.append(tool_url)


def main():
    driver = init_driver()
    apply_cookies(driver)
    columns = get_columns()
    scraped_tools = get_scraped_tools()
    scraped_tools = [url.strip().rstrip("/") for url in scraped_tools]  # Clean URLs

    for l in range(1, 14):
        print(f"Page count is {l}/13")
        driver.get(f"{URL_TO_SCRAPE}?page={l}")
        scrape_bunnings(driver, scraped_tools, columns)

    driver.quit()


if __name__ == "__main__":
    main()
