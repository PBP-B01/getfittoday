import os
import time
import re
from datetime import datetime, timezone, timedelta
from seleniumbase import SB
from bs4 import BeautifulSoup
import pandas as pd

GMT7 = timezone(timedelta(hours=7))

SCRIPT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
CHAT_LOGS = []

def add_logs(log_message):
    """Appends a timestamped log message to the global log list and a file."""
    timestamp = f"[{datetime.now(GMT7).strftime('%Y-%m-%d %H:%M:%S')}] {log_message}"
    CHAT_LOGS.append(timestamp)
    print(timestamp)
    logs_path = os.path.join(SCRIPT_DIRECTORY, "tokopedia_scraper_logs.txt")
    with open(logs_path, "a", encoding="utf-8") as logsfile:
        logsfile.write(timestamp + "\n")

def append_to_excel(df, search_query):
    """Appends scraped product data from a DataFrame to an Excel file."""
    safe_query = re.sub(r'[\\/*?:"<>|]', "", search_query)
    excel_filename = f"tokopedia_data_{safe_query}.xlsx"
    excel_path = os.path.join(SCRIPT_DIRECTORY, excel_filename)
    add_logs(f"Preparing to save {len(df)} products for query '{search_query}' to {excel_path}...")

    try:
        df_to_save = df.copy()

        final_columns = [
            'Product Name',
            'Price (Rp)',
            'Rating',
            'Units Sold',
            'Image URL'
        ]

        if os.path.exists(excel_path):
            add_logs(f"Appending data to existing file: {excel_path}")
            existing_df = pd.read_excel(excel_path, sheet_name='Products')
            
            combined_df = pd.concat([existing_df, df_to_save], ignore_index=True)
            
            combined_df.drop_duplicates(subset=['Product URL'], keep='last', inplace=True)
            
            output_df = combined_df[final_columns]
            output_df.to_excel(excel_path, sheet_name='Products', index=False)
            add_logs(f"Successfully updated {excel_path}. Total products now: {len(output_df)}")
        else:
            add_logs(f"Creating new file: {excel_path}")
            
            output_df = df_to_save[final_columns]
            output_df.to_excel(excel_path, sheet_name='Products', index=False)
            add_logs(f"Successfully created {excel_path} and saved {len(output_df)} rows.")

    except Exception as e:
        add_logs(f"Error saving data to Excel: {e}")

def parse_product_data(soup):
    """Parses the HTML soup to extract product details."""
    add_logs("Parsing product data from page source...")
    products = []
    product_cards = soup.find_all('div', class_='css-5wh65g')
    add_logs(f"Found {len(product_cards)} potential product cards.")

    for card in product_cards:
        try:
            name = None
            price = None
            rating = None
            sold = None
            image_url = None
            product_url = None

            # Extract Product Name
            name_tag = card.find('span', class_='+tnoqZhn89+NHUA43BpiJg==')
            if name_tag:
                name = name_tag.text.strip()

            # Extract Price
            price_tag = card.find(class_=re.compile(r'HJhoi0tEIlowsgSNDNWVXg==|YZHqvX\+8TVU2YltRC9S\+oA=='))
            if price_tag:
                price_raw = price_tag.text.strip()
                price = int(re.sub(r'[^\d]', '', price_raw))

            # Extract Rating
            rating_tag = card.find('span', class_='_2NfJxPu4JC-55aCJ8bEsyw==')
            if rating_tag:
                rating = rating_tag.text.strip()

            # Extract Units Sold
            sold_tag = card.find('span', class_='u6SfjDD2WiBlNW7zHmzRhQ==')
            if sold_tag:
                sold = sold_tag.text.strip()

            # Extract Image URL
            img_tag = card.find('img', alt='product-image')
            if img_tag and img_tag.has_attr('src'):
                image_url = img_tag['src']

            # Extract Product URL
            link_tag = card.find('a', class_=re.compile(r'Ui5-B4CDAk4Cv-cjLm4o0g=='))
            if link_tag and link_tag.has_attr('href'):
                product_url = link_tag['href']

            if name and price and product_url:
                products.append({
                    'Product Name': name,
                    'Price (Rp)': price,
                    'Rating': rating if rating else 'N/A',
                    'Units Sold': sold if sold else 'N/A',
                    'Image URL': image_url if image_url else 'N/A',
                    'Product URL': product_url
                })
            else:
                add_logs(f"Skipping a card due to missing essential data (Name, Price, or URL). Name found: {name is not None}, Price found: {price is not None}, URL found: {product_url is not None}")

        except Exception as e:
            add_logs(f"Skipping a card due to a parsing error: {e}")
            continue

    add_logs(f"Successfully parsed {len(products)} products.")
    return products

def run_scraper(target_url, search_query):
    """
    Runs one full cycle of the scraper for a given Tokopedia URL.
    Tries up to 3 times to load the page and find product data.
    """
    add_logs(f"Starting scrape cycle for query: '{search_query}'...")
    max_attempts = 3

    for attempt in range(max_attempts):
        product_data = []
        try:
            add_logs(f"Attempt {attempt + 1}/{max_attempts} for query '{search_query}'...")
            with SB(uc=True, headless=True, incognito=True, locale_code="id") as sb:
                sb.uc_open_with_reconnect(target_url, reconnect_time=5)
                add_logs("Waiting for initial product data to load...")
                sb.wait_for_element('div.css-5wh65g', timeout=60)

                add_logs("Initial data loaded. Proceeding with scrape.")
                time.sleep(5)

                add_logs("Scrolling down to load more products...")
                scroll_count = 5
                for i in range(scroll_count):
                    sb.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    add_logs(f"Scroll iteration {i+1}/{scroll_count}...")
                    time.sleep(3)

                html = sb.get_page_source()
                soup = BeautifulSoup(html, 'html.parser')
                product_data = parse_product_data(soup)

                if product_data:
                    df = pd.DataFrame(product_data).sort_values(by='Price (Rp)').reset_index(drop=True)
                    append_to_excel(df, search_query)
                    add_logs(f"Scrape cycle for '{search_query}' finished successfully on this attempt.")
                    return
                else:
                    add_logs(f"No products found for '{search_query}' on this attempt.")
                    if attempt == max_attempts - 1:
                        add_logs(f"No products found for '{search_query}' after {max_attempts} attempts.")

        except Exception as e:
            add_logs(f"Attempt {attempt + 1} for query '{search_query}' failed: {e}")
            if attempt < max_attempts - 1:
                add_logs("Retrying...")
                time.sleep(10)
            else:
                add_logs(f"All attempts for query '{search_query}' failed.")

def main():
    """Main function to run the Tokopedia product scraper once."""

    SEARCH_QUERY = "bola+basket"
    TARGET_URL = f"https://www.tokopedia.com/search?st=&q={SEARCH_QUERY}&srp_component_id=02.01.00.00&srp_page_id=&srp_page_title=&navsource="

    add_logs(f"=== Starting scrape run for query: '{SEARCH_QUERY}'. ===")
    run_scraper(TARGET_URL, SEARCH_QUERY)
    add_logs("=== Scrape run finished. ===")

if __name__ == "__main__":
    main()