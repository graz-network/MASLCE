import os
import re
import time
import random
import logging

from bs4 import BeautifulSoup
import pandas as pd
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.firefox.options import Options

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_page(liste_url):
    """
    Function to navigate through a list of URLs, simulate human browsing by waiting for random intervals,
    and collect the page sources.
    """
    options = Options()
    options.headless = True  # Run in headless mode for efficiency
    try:
        driver = webdriver.Firefox(options=options)
        driver.set_page_load_timeout(30)  # Set timeout for page load
        pages = []
        page_counter = 0  # Initialize a counter for the number of pages visited

        for page_nb in range(1, 31):
            page_url = f"{liste_url}{page_nb}"
            try:
                driver.get(page_url)
                rnd = random.randint(2, 9)
                time.sleep(rnd)
                pages.append(driver.page_source.encode("utf-8"))
                page_counter += 1  # Increment the counter
                logging.info(f"GET_PAGE: {page_url}")
            except WebDriverException as e:
                logging.error(f"Error accessing {page_url}: {e}")
        
        logging.info(f"Total pages visited: {page_counter}")
        return pages
    except WebDriverException as e:
        logging.error(f"Error initializing WebDriver: {e}")
    finally:
        driver.quit()  # Ensure the driver is closed even if an error occurs

def save_pages(pages, dir):
    """
    Function to save the collected pages to the specified directory.
    """
    os.makedirs(f"{dir}", exist_ok=True)
    for page_nb, page in enumerate(pages):
        file_path = os.path.join(dir, f"page_{page_nb}.html")
        with open(file_path, "wb") as f_out:
            f_out.write(page)
            logging.info(f"SAVE_PAGES: {file_path}")

def parse_pages(dir):
    """
    Function to parse saved pages from a directory and collect URLs and titles.
    """
    pages_paths = os.listdir(dir)
    results = pd.DataFrame(columns=["URL", "TITLE"])

    for pages_path in pages_paths:
        logging.info(f"PARSE_PAGES: {pages_path}")
        with open(os.path.join(dir, pages_path), "rb") as f_in:
            page = f_in.read().decode("utf-8")
            page_results = parse_page(page)
            results = pd.concat([results, page_results], ignore_index=True)
    
    return results

def parse_page(page):
    """
    Function to parse individual page content and extract URLs and titles.
    """
    result = pd.DataFrame(columns=["URL", "TITLE"])
    soup = BeautifulSoup(page, "html.parser")
    for div in soup.find_all("div", class_="elm elst"):
        logging.info("PARSE_PAGE -> ")
        a_tag = div.find('a', href=True)
        if a_tag:
            result = result._append({"URL": a_tag['href'], "TITLE": a_tag.get_text(strip=True)}, ignore_index=True)
            logging.info(f"PARSE_Tag_HREF -> {a_tag['href']}")
            logging.info(f"PARSE_Tag_TITLE -> {a_tag.get_text(strip=True)}")
            get_content_page(a_tag['href'])
    
    return result

def get_content_page(url):
    """
    Function to retrieve and save the content of a given URL.
    """
    options = Options()
    options.headless = True  # Run in headless mode for efficiency
    try:
        driver = webdriver.Firefox(options=options)
        driver.set_page_load_timeout(30)  # Set timeout for page load
        page_url = f"https://www.petitesannonces.ch{url}"
        page_id = re.search(r'/a/(\d+)', url).group(1)
        driver.get(page_url)
        rnd = random.randint(2, 9)
        time.sleep(rnd)
        page = driver.page_source.encode("utf-8")
        logging.info(f"GET_PAGE_CONTENT: {page_url}")
        os.makedirs("content_petitesannonces_iphone", exist_ok=True)
        file_path = os.path.join("content_petitesannonces_iphone", f"page_content_{page_id}.html")
        with open(file_path, "wb") as f_out:
            f_out.write(page)
            logging.info(f"SAVE_CONTENT_PAGES: {file_path}")
    except WebDriverException as e:
        logging.error(f"Error accessing content page {url}: {e}")
    finally:
        driver.quit()  # Ensure the driver is closed even if an error occurs

def parse_content(dir):
    """
    Function to parse content pages from a directory and collect relevant information.
    """
    pages_paths = os.listdir(dir)
    results = pd.DataFrame(columns=["URL", "TITLE", "DOMAIN", "ACTIVITE", "CONTENT"])

    for pages_path in pages_paths:
        logging.info(f"PARSE_PAGES_CONTENT: {pages_path}")
        with open(os.path.join(dir, pages_path), "rb") as f_in:
            page = f_in.read().decode("utf-8")
            soup = BeautifulSoup(page, "html.parser")
            logging.info("PARSE_PAGE -> ")
            for div in soup.find_all("div", class_="ccm clm"):
                titre = soup.find('h1', class_='cti').get_text(strip=True) if soup.find('h1', class_='cti') else None
                contenu = soup.find('div', class_="cdk bls").get_text(strip=True) if soup.find('div', class_="cdk bls") else None
                # Extraction du prix
                prix_match = re.search(r'Prix\s*:\s*(\d+)', contenu) if contenu else None
                prix = prix_match.group(1) if prix_match else None
                # Extraction du pseudo et du lien href
                pseudo_tag = soup.find('a', class_='bold')
                pseudo = pseudo_tag.get_text(strip=True) if pseudo_tag else None
                pseudo_href = pseudo_tag['href'] if pseudo_tag else None

                results = results._append({"TITLE": titre, "PRIX": prix, "CONTENT": contenu,"PSEUDO": pseudo, "PROFILE": pseudo_href, "URL": pages_path}, ignore_index=True)
                logging.info(f"PARSE_Tag_TITLE -> {titre}")
                logging.info(f"PARSE_Tag_PRIX -> {prix}")
                logging.info(f"PARSE_Tag_CONTENT -> {contenu}")
                logging.info(f"PARSE_Tag_PSEUDO -> {pseudo}")
                logging.info(f"PARSE_Tag_PROFILE -> {pseudo_href}")
                logging.info(f"PARSE_Tag_HREF -> {pages_path}")

    return results

def main():
    """
    Main function to execute the web scraping and parsing process.
    """
    site_url = "https://www.petitesannonces.ch"
    base_url = f"{site_url}/r/420216"
    liste_url = f"{base_url}?ob=price&p="
    
    #pages = get_page(liste_url)
    #save_pages(pages, "data_petitesannonces_iphone")
    
    #results = parse_pages("data_petitesannonces_iphone")
    #results.to_csv("liste_results_petitesannonces_iphone.csv", index=False)
    #logging.info("PRINT_RESULTS -> ")
    #logging.info(results)
    
    annonces = parse_content("content_petitesannonces_iphone")
    annonces.to_csv("liste_annonce_petitesannonces_iphone.csv", index=False, sep=';', quotechar='"')
    logging.info("PRINT_ANNONCES.CSV ")
    #logging.info(annonces)

if __name__ == "__main__":
    main()

# Copyright (c) David Graz
