#!/usr/bin/env python3
import streamlit as st
import pandas as pd
import re
import time

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.jdsports.co.uk"
DEFAULT_URL = (
    "https://www.jdsports.co.uk/men/mens-footwear/brand/adidas,nike/colour/white/"
)


def get_product_links(listing_url):
    # Use an updated User-Agent string
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }
    resp = requests.get(listing_url, headers=headers)
    soup = BeautifulSoup(resp.text, "html.parser")
    product_links = []

    # Look for all <a> tags with href attributes and filter those that look like product links
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith("/product/"):
            full_url = BASE_URL + href.split("?")[0]  # remove any query params
            if full_url not in product_links:
                product_links.append(full_url)

    # Debug: Uncomment the following line to print the total count of product links found
    # print(f"Debug: Found {len(product_links)} product links.")

    return product_links


def extract_product_info(product_url):
    # Use an updated User-Agent string
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    resp = requests.get(product_url, headers=headers)
    soup = BeautifulSoup(resp.text, "html.parser")

    title_tag = soup.find("h1")
    title = title_tag.get_text(strip=True) if title_tag else "No title found"

    care_section = "No Care & Material section found"

    # Use regex to search for a header containing both 'care' and 'material', allowing for variations in case
    care_material_header = soup.find(
        lambda tag: tag.name in ["h3", "h4"]
        and tag.string
        and re.search(r"care.*material", tag.string, re.IGNORECASE)
    )

    if care_material_header:
        # Instead of stopping at the very next sibling, gather text from all siblings until the next header.
        content_parts = []
        for sibling in care_material_header.next_siblings:
            # Break when encountering another header tag
            if getattr(sibling, "name", None) in ["h3", "h4"]:
                break
            # Only process tag elements with text (this avoids strings that might be just newlines)
            if hasattr(sibling, "get_text"):
                text = sibling.get_text(" ", strip=True)
                if text:
                    content_parts.append(text)
        if content_parts:
            care_section = " ".join(content_parts).strip()
        else:
            care_section = "Found Care & Material header but no content next to it."

    return title, care_section


st.title("JD Sports Product Scraper 🏃‍♂️👟")
st.write(
    "Scrape white Adidas and Nike men's shoes from JD Sports UK or any page you like!"
)

url_placeholder = st.empty()
run_button_placeholder = st.empty()
default_url_set = st.session_state.get("default_url_set", False)

if not default_url_set:
    st.session_state["listing_url"] = DEFAULT_URL
    st.session_state["default_url_set"] = True

listing_url = url_placeholder.text_input(
    "Listing URL to scrape:", value=st.session_state["listing_url"]
)
run_scraper = run_button_placeholder.button("Run Scraper")
wait_time = st.slider(
    "Delay between requests (in seconds):", min_value=1, max_value=30, value=10
)

if run_scraper:
    st.success(f"Scraping from: {listing_url}")
    product_links = get_product_links(listing_url)
    st.success(f"Found {len(product_links)} product links!")

    progress_bar = st.progress(0)
    all_products = []
    result_table = st.empty()
    st.markdown(
        "<style>thead th:nth-child(1), thead th:nth-child(2) { width: 300px !important; }</style>",
        unsafe_allow_html=True,
    )

    for idx, link in enumerate(product_links):
        title, care = extract_product_info(link)
        all_products.append({"title": title, "care_material": care, "link": link})
        progress_bar.progress((idx + 1) / len(product_links))
        df = pd.DataFrame(all_products, columns=["title", "care_material", "link"])
        result_table.dataframe(df)
        time.sleep(wait_time)  # User-configured delay

    st.success("Scraping complete!")
    final_df = pd.DataFrame(all_products, columns=["title", "care_material", "link"])
    st.dataframe(final_df)

    csv_filename = "products.csv"
    st.download_button(
        "Download CSV",
        data=final_df.to_csv(index=False),
        file_name=csv_filename,
        mime="text/csv",
    )
