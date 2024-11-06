from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
import time
from urllib.parse import urlparse, urlunparse
import os
import requests


# Function to clean release year
def clean_release_year(release_year):
    if not release_year:
        return "N/A"
    release_year = release_year.replace("â€“", "-").replace("–", "-")
    release_year = release_year.strip("-").strip()
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
        if og_image and 'content' in og_image.attrs:
            return og_image['content']
    return "N/A"

# Initialize selenium webdriver with service
driver_path = "C:\\chromedriver.exe"  # Update this path if necessary
service = Service(driver_path)
driver = webdriver.Chrome(service=service)

try:
    url = "https://www.imdb.com/list/ls500782119/?sort=user_rating%2Cdesc"
    driver.get(url)

    # Load more K-dramas
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

    soup = BeautifulSoup(driver.page_source, "html.parser")
    kdrama_links = []
    for link_tag in soup.find_all("a", class_="ipc-title-link-wrapper"):
        href = link_tag.get("href")
        if href and "/title/" in href:
            full_url = f"https://www.imdb.com{href}"
            kdrama_links.append(full_url)
        # if len(kdrama_links) >= 5:  #Stop after collecting 5 links
        #     break

    print(f"Total Kdrama links found: {len(kdrama_links)}")

    existing_kdramas = set()
    if os.path.exists('kdramas.csv'):
        existing_df = pd.read_csv('kdramas.csv', encoding='utf-8')
        existing_kdramas = set(existing_df['Name'].dropna().unique())

    kdrama_data = []

    for idx, kdrama_link in enumerate(kdrama_links, start=1):
        print(f"Scraping Kdrama {idx}: {kdrama_link}")
        driver.get(kdrama_link)
        time.sleep(1)

        detail_soup = BeautifulSoup(driver.page_source, "html.parser")

        name_span = detail_soup.find("span", class_="hero__primary-text")
        name = name_span.get_text(strip=True) if name_span else "N/A"

        if name in existing_kdramas:
            print(f"Skipping {name}, already in CSV.")
            continue

        original_title_div = detail_soup.find("div", class_="sc-ec65ba05-1 fUCCIx")
        if original_title_div:
            original_title_text = original_title_div.get_text(strip=True)
            original_title = original_title_text.replace("Original title:", "").strip()
        else:
            original_title = "N/A"

        details_ul = detail_soup.find("ul", class_="ipc-inline-list ipc-inline-list--show-dividers sc-ec65ba05-2 joVhBE baseAlt")
        if details_ul:
            details_items = details_ul.find_all("li", class_="ipc-inline-list__item")
            show_type = details_items[0].get_text(strip=True) if len(details_items) > 0 else "N/A"
            release_year_raw = details_items[1].get_text(strip=True) if len(details_items) > 1 else "N/A"
            release_year = clean_release_year(release_year_raw)
            age_rating = details_items[2].get_text(strip=True) if len(details_items) > 2 else "N/A"
            duration = details_items[3].get_text(strip=True) if len(details_items) > 3 else "N/A"
        else:
            show_type = release_year = age_rating = duration = "N/A"
        
        episodes_header = detail_soup.find("div", {"data-testid": "episodes-header"})
        episodes = episodes_header.find("span", class_="ipc-title__subtext").get_text(strip=True) if episodes_header else "N/A"
        
        # Extract number of seasons
        seasons = "N/A"
        # Check for different possible tags
        season_span = detail_soup.find("span", class_="ipc-btn__text")  # Case: span tag
        season_label = detail_soup.find("label", for_="browse-episodes-season")  # Case: label tag
        season_select = detail_soup.find("select", id="browse-episodes-season")  # Case: select tag

        if season_span and "Season" in season_span.get_text():
            seasons = season_span.get_text().strip().split()[0]  # Extract the number before "Season"
        elif season_label:
            seasons = season_label.get_text().strip().split()[0]  # Extract the number before "seasons"
        elif season_select:
            seasons = season_select.get("aria-label", "N/A").split()[0]  # Extract number from aria-label
            
        # Extract number of years
        years = "N/A"
        years_select = detail_soup.find("select", id="browse-episodes-year")  # Main case: select tag

        if years_select:
            years = years_select.get("aria-label", "N/A").split()[0]  # Extract number from aria-label

        # Compile the extracted data
        kdrama_info = {
            # Other fields remain unchanged
            "Seasons": seasons,
            "Years": years,
            # Other fields remain unchanged
        }

        rating_span = detail_soup.find("span", class_="sc-d541859f-1 imUuxf")
        rating = rating_span.get_text() if rating_span else "N/A"

        num_ratings_div = detail_soup.find("div", class_="sc-d541859f-3 dwhNqC")
        num_ratings = num_ratings_div.get_text().replace(",", "") if num_ratings_div else "N/A"

        # Link to poster (scraping from og:image)
        poster_link = scrape_image_url(kdrama_link)
        
        video_tag = detail_soup.find('video', class_='jw-video jw-reset')
        video_link = video_tag['src'] if video_tag and 'src' in video_tag.attrs else "N/A"

        chip_links = detail_soup.find_all('a', class_='ipc-chip ipc-chip--on-baseAlt')
        genres = [chip.get_text(strip=True) for chip in chip_links]

        description_tag = detail_soup.find('span', {'data-testid': 'plot-l'})
        description = description_tag.get_text(strip=True) if description_tag else "N/A"

        actor_links = detail_soup.find_all('a', class_='ipc-metadata-list-item__list-content-item ipc-metadata-list-item__list-content-item--link')
        actor_names = list(dict.fromkeys([actor.get_text(strip=True) for actor in actor_links]))
        actor_names = actor_names[:3]

        # Streaming services
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

                # Include only allowed services
                if any(allowed_service in service_name for allowed_service in allowed_services):
                    # Parse the URL to remove query parameters for Netflix and Prime Video
                    if "Netflix" in service_name or "Prime Video" in service_name:
                        parsed_url = urlparse(service_link)
                        service_link = urlunparse(parsed_url._replace(query=""))

                    # Ensure the link is complete (add base URL if necessary)
                    if service_link.startswith("/"):
                        service_link = f"https://www.imdb.com{service_link}"

                    # Add the service with its link to the list
                    services.append(f"{service_name} ({service_link})")
                    
        # If no streaming services were found, set it to "N/A"
        if not services:
            services.append("N/A")

        # Compile the Kdrama information
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
            "Stars": ', '.join(actor_names),
            "Streaming Services": ', '.join(services)
        }

        # Append the Kdrama information to the data list
        kdrama_data.append(kdrama_info)

    if kdrama_data:
        df = pd.DataFrame(kdrama_data)
        df.to_csv('kdramas.csv', mode='a', index=False, encoding='utf-8', header=not os.path.exists('kdramas.csv'))
    else:
        print("No new K-dramas to add.")

finally:
    driver.quit()
