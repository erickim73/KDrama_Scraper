# Import necessary libraries
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
import time
from urllib.parse import urlparse, urlunparse
import requests

# Function to clean release year
def clean_release_year(release_year):
    if not release_year:
        return "N/A"
    release_year = release_year.replace("â€“", "-").replace("–", "-").strip("-").strip()
    return release_year

# Function to scrape image URL from IMDb page
def scrape_image_url(kdrama_link):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    response = requests.get(kdrama_link, headers=headers)
    if response.status_code == 200:
        detail_soup = BeautifulSoup(response.content, 'html.parser')
        og_image = detail_soup.find('meta', property='og:image')
        return og_image['content'] if og_image and 'content' in og_image.attrs else "N/A"
    return "N/A"

# Initialize selenium webdriver with service
driver_path = "C:\\chromedriver.exe"  # Update this path if necessary
service = Service(driver_path)
driver = webdriver.Chrome(service=service)

try:
    url = "https://www.imdb.com/search/title/?title_type=tv_series&release_date=2016-01-01,2024-12-31&user_rating=6.5,10&num_votes=500,&interests=in0000209&sort=user_rating,desc"
    driver.get(url)

    # Load more Kdramas function
    def load_more_kdramas():
        try:
            while True:
                more_button_50 = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), '50 more')]/button"))
                )
                more_button_50.click()
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//a[contains(@href, '/title/')]"))
                )
                try:
                    more_button_17 = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), '17 more')]/button"))
                    )
                    more_button_17.click()
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, "//a[contains(@href, '/title/')]"))
                    )
                except Exception:
                    break
        except Exception as e:
            print(f"Error while loading Kdramas: {e}")

    load_more_kdramas()

    # Parse the search results page
    soup = BeautifulSoup(driver.page_source, "html.parser")
    kdrama_links = [f"https://www.imdb.com{link_tag.get('href')}" for link_tag in soup.find_all("a", class_="ipc-title-link-wrapper") if link_tag.get("href") and "/title/" in link_tag.get("href")]

    print(f"Total Kdrama links found (limited to 10): {len(kdrama_links)}")

    kdrama_data = []

    # Extract details from each Kdrama link
    for idx, kdrama_link in enumerate(kdrama_links, start=1): 
        print(f"Scraping Kdrama {idx}: {kdrama_link}")
        driver.get(kdrama_link)
        time.sleep(1)

        detail_soup = BeautifulSoup(driver.page_source, "html.parser")
        name = detail_soup.find("span", class_="hero__primary-text").get_text(strip=True) if detail_soup.find("span", class_="hero__primary-text") else "N/A"
        original_title_div = detail_soup.find("div", class_="sc-ec65ba05-1 fUCCIx")
        original_title = original_title_div.get_text(strip=True).replace("Original title:", "").strip() if original_title_div else "N/A"

        details_ul = detail_soup.find("ul", class_="ipc-inline-list ipc-inline-list--show-dividers sc-ec65ba05-2 joVhBE baseAlt")
        if details_ul:
            details_items = details_ul.find_all("li", class_="ipc-inline-list__item")
            show_type = details_items[0].get_text(strip=True) if len(details_items) > 0 else "N/A"
            release_year = clean_release_year(details_items[1].get_text(strip=True)) if len(details_items) > 1 else "N/A"
            age_rating = details_items[2].get_text(strip=True) if len(details_items) > 2 else "N/A"
            duration = details_items[3].get_text(strip=True) if len(details_items) > 3 else "N/A"
        else:
            show_type = release_year = age_rating = duration = "N/A"

        episodes = detail_soup.find("div", {"data-testid": "episodes-header"}).find("span", class_="ipc-title__subtext").get_text(strip=True) if detail_soup.find("div", {"data-testid": "episodes-header"}) else "N/A"
        seasons = detail_soup.find("span", class_="ipc-btn__text").get_text().split()[0] if detail_soup.find("span", class_="ipc-btn__text") and "Season" in detail_soup.find("span", class_="ipc-btn__text").get_text() else "N/A"
        years = detail_soup.find("select", id="browse-episodes-year").get("aria-label", "N/A").split()[0] if detail_soup.find("select", id="browse-episodes-year") else "N/A"

        rating_span = detail_soup.find("span", class_="sc-d541859f-1 imUuxf")
        rating = rating_span.get_text() if rating_span else "N/A"
        num_ratings_div = detail_soup.find("div", class_="sc-d541859f-3 dwhNqC")
        num_ratings = num_ratings_div.get_text().replace(",", "") if num_ratings_div else "N/A"
        poster_link = scrape_image_url(kdrama_link)
        video_link = detail_soup.find('video', class_='jw-video jw-reset')['src'] if detail_soup.find('video', class_='jw-video jw-reset') else "N/A"

        genres = [chip.get_text(strip=True) for chip in detail_soup.find_all('a', class_='ipc-chip ipc-chip--on-baseAlt')]
        description_tag = detail_soup.find('span', {'data-testid': 'plot-l'})
        description = description_tag.get_text(strip=True) if description_tag else "N/A"
        stars = [actor.get_text(strip=True) for actor in detail_soup.find_all('a', class_='ipc-metadata-list-item__list-content-item ipc-metadata-list-item__list-content-item--link')[:3]]

        # Streaming services extraction and handling empty cases
        streaming_services = detail_soup.find_all('div', class_='ipc-slate-card')
        services = []
        allowed_services = [
            "Netflix", "Prime Video", "The Roku Channel", "Hulu", "Tubi", 
            "Freevee", "Paramount+", "Best TV Ever"
        ]

        for service in streaming_services:
            streaming_link_tag = service.find('a', class_='ipc-lockup-overlay')
            if streaming_link_tag:
                service_name = streaming_link_tag.get('aria-label', 'N/A')
                service_link = streaming_link_tag['href'] if 'href' in streaming_link_tag.attrs else 'N/A'

                if any(allowed_service in service_name for allowed_service in allowed_services):
                    if "Netflix" in service_name or "Prime Video" in service_name:
                        parsed_url = urlparse(service_link)
                        service_link = urlunparse(parsed_url._replace(query=""))
                    if service_link.startswith("/"):
                        service_link = f"https://www.imdb.com{service_link}"
                    services.append(f"{service_name} ({service_link})")

        # If no streaming services were found, set it to "N/A"
        if not services:
            services.append("N/A")

        kdrama_info = {
            "Name": name,
            "Original Title": original_title,
            "Show Type": show_type,
            "Release Year": release_year,
            "Age Rating": age_rating,
            "Duration": duration,
            "Episodes": episodes,
            "Seasons": seasons,
            "Years": years,
            "Rating": rating,
            "Number of Ratings": num_ratings,
            "Poster Link": poster_link,
            "Trailer Link": video_link,
            "Genres": ', '.join(genres),
            "Description": description,
            "Stars": ', '.join(stars),
            "Streaming Services": ', '.join(services)
        }
        kdrama_data.append(kdrama_info)

        
finally:
    driver.quit()

kdrama_df = pd.DataFrame(kdrama_data)
output_file = "kdramas.csv"
kdrama_df.to_csv(output_file, index=False)
print(f"Data scraped and saved to {output_file}.")
