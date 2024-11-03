from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import time

# Initialize selenium webdriver with service
driver_path = "C:\chromedriver.exe"
service = Service(driver_path)
driver = webdriver.Chrome(service=service)

# URL of the IMDb search page for Kdramas
url = "https://www.imdb.com/search/title/?title_type=tv_series&release_date=2016-01-01,2024-12-31&user_rating=6.5,10&num_votes=500,&interests=in0000209&sort=user_rating,desc"
driver.get(url)
time.sleep(1)  # Wait for the page to load

# Parse the search results page
soup = BeautifulSoup(driver.page_source, "html.parser")

# Extract links to individual Kdrama pages
kdrama_links = []
for link_tag in soup.find_all("a", class_="ipc-title-link-wrapper"):
    href = link_tag.get("href")
    if href and "/title/" in href:
        full_url = f"https://www.imdb.com{href}"
        kdrama_links.append(full_url)
    # if len(kdrama_links) >= 3:  # Limit to 3 Kdramas
    #     break

# Store results in a list
kdrama_data = []

# Loop through each Kdrama link to extract details
for kdrama_link in kdrama_links:
    driver.get(kdrama_link)
    time.sleep(1)  # Wait 1 second for page to load

    # Parse Kdrama detail page
    detail_soup = BeautifulSoup(driver.page_source, "html.parser")

    # Find name of Kdrama
    name_span = detail_soup.find("span", class_="hero__primary-text")
    name = name_span.get_text(strip=True) if name_span else "N/A"

    # Find original title
    original_title_div = detail_soup.find("div", class_="sc-ec65ba05-1 fUCCIx")
    original_title = original_title_div.get_text(strip=True).replace("Original title:", "").strip() if original_title_div else "N/A"

    # Find show type, date, age rating, time of episode
    details_ul = detail_soup.find("ul", class_="ipc-inline-list ipc-inline-list--show-dividers sc-ec65ba05-2 joVhBE baseAlt")
    
    if details_ul:
        details_items = details_ul.find_all("li", class_="ipc-inline-list__item")
        
        show_type = details_items[0].get_text(strip=True) if len(details_items) > 0 else "N/A"
        release_year = details_items[1].get_text(strip=True) if len(details_items) > 1 else "N/A"
        age_rating = details_items[2].get_text(strip=True) if len(details_items) > 2 else "N/A"
        duration = details_items[3].get_text(strip=True) if len(details_items) > 3 else "N/A"
    else:
        show_type = release_year = age_rating = duration = "N/A"
        
    # Rating
    rating_span = detail_soup.find("span", class_="sc-d541859f-1 imUuxf")
    rating = rating_span.get_text() if rating_span else "N/A"
        
    # Number of ratings
    num_ratings_div = detail_soup.find("div", class_="sc-d541859f-3 dwhNqC")
    num_ratings = num_ratings_div.get_text() if num_ratings_div else "N/A"
        
    # Link to poster
    poster_link_tag = detail_soup.find('a', class_='ipc-lockup-overlay ipc-focusable')
    poster_link = 'https://www.imdb.com' + poster_link_tag['href'] if poster_link_tag and 'href' in poster_link_tag.attrs else "N/A"
        
    # Link to trailer video
    video_tag = detail_soup.find('video', class_='jw-video jw-reset')
    video_link = video_tag['src'] if video_tag and 'src' in video_tag.attrs else "N/A"
    
    # Genre
    chip_links = detail_soup.find_all('a', class_='ipc-chip ipc-chip--on-baseAlt')
    genres = [chip.get_text(strip=True) for chip in chip_links]
    
    # Description
    description_tag = detail_soup.find('span', {'data-testid': 'plot-l'})
    description = description_tag.get_text(strip=True) if description_tag else "N/A"

    # Stars (limit to 3 names)
    actor_links = detail_soup.find_all('a', class_='ipc-metadata-list-item__list-content-item ipc-metadata-list-item__list-content-item--link')
    actor_names = list(dict.fromkeys([actor.get_text(strip=True) for actor in actor_links]))  # Remove duplicates using dict
    actor_names = actor_names[:3]  # Limit to 3 stars

    # Streaming services (only include Netflix, Prime Video, and Roku Channel)
    streaming_services = detail_soup.find_all('div', class_='ipc-slate-card')
    services = []
    allowed_services = ["Netflix", "Prime Video", "Roku Channel"]
    
    for service in streaming_services:
        streaming_link_tag = service.find('a', class_='ipc-lockup-overlay')
        if streaming_link_tag:
            service_name = streaming_link_tag.get('aria-label', 'N/A')
            service_link = streaming_link_tag['href'] if 'href' in streaming_link_tag.attrs else 'N/A'
            # Only include allowed services
            if any(allowed_service in service_name for allowed_service in allowed_services):
                services.append((service_name, service_link))

    # Add data to list
    kdrama_data.append({
        "Link": kdrama_link,
        "Name": name,
        "Original Title": original_title,
        "Show Type": show_type,
        "Release Year": release_year,
        "Age Rating": age_rating,
        "Duration": duration,
        "Rating": rating,
        "Number of Ratings": num_ratings,
        "Poster Link": poster_link,
        "Trailer Link": video_link,
        "Genres": genres,
        "Description": description,
        "Stars": actor_names,
        "Streaming Services": services if services else [],
    })

# Print the scraped data
for kdrama in kdrama_data:
    print(f"Kdrama URL: {kdrama['Link']}")
    print(f"Name: {kdrama['Name']}")
    print(f"Original Title: {kdrama['Original Title']}")
    print(f"Show Type: {kdrama['Show Type']}")
    print(f"Release Year: {kdrama['Release Year']}")
    print(f"Age Rating: {kdrama['Age Rating']}")
    print(f"Duration: {kdrama['Duration']}")
    print(f"Rating: {kdrama['Rating']}")
    print(f"Number of Ratings: {kdrama['Number of Ratings']}")
    print(f"Poster Link: {kdrama['Poster Link']}")
    print(f"Trailer Link: {kdrama['Trailer Link']}")
    print(f"Genres: {kdrama['Genres']}")
    print(f"Description: {kdrama['Description']}")
    print(f"Stars: {kdrama['Stars']}")
    
    if kdrama['Streaming Services']:
        print("Streaming Services:")
        for service_name, service_link in kdrama['Streaming Services']:
            print(f"  - {service_name}: {service_link}")
    else:
        print("Streaming Services: None available")
    
    print("=" * 80)

# Close the browser
driver.quit()
