import requests
from bs4 import BeautifulSoup
import re

url = "https://www.imdb.com/search/title/?title_type=tv_series&release_date=2016-01-01,2024-12-31&user_rating=6.5,&num_votes=500,&interests=in0000209&sort=user_rating,desc"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36"
}

response = requests.get(url, headers=headers)
html_text = response.text
soup = BeautifulSoup(html_text, "html.parser")

#list containing all KDramas
kdrama_list = []

#loop through each list in IMDb
for item in soup.find_all("li", class_="ipc-metadata-list-summary-item"):
    # Extract title
    title_element = item.find("h3", class_="ipc-title__text")
    title = title_element.get_text(strip=True) if title_element else None
    
    #remove leading number
    if title:
        title = re.sub(r"^\d+\.\s*", "", title)
    
    #year and age
    metadata_items = item.find("div", class_="sc-5bc66c50-5 hVarDB dli-title-metadata")
    
    if metadata_items:
        #find all span elements containing year and age
        year_age_spans = metadata_items.find_all("span", class_="dli-title-metadata-item")
        
        #extract year and age safely
        year = year_age_spans[0].get_text(strip=True) if len(year_age_spans) > 0 else None
        age = year_age_spans[1].get_text(strip=True) if len(year_age_spans) > 1 else None
    else:
        year = None
        age = None
    
    #IMDb rating
    imdb_rating_element = item.find("span", class_="ipc-rating-star--rating")
    imdb_rating = imdb_rating_element.get_text(strip=True) if imdb_rating_element else None
    
    #description
    description_element = item.find("div", class_="ipc-html-content-inner-div")
    description = description_element.get_text(strip=True) if description_element else None
    
    kdrama_info = {
        "title": title,
        "year": year,
        "age": age,
        "IMDb_rating": imdb_rating,
        "description": description,        
    }
    
    kdrama_list.append(kdrama_info)

for kdrama in kdrama_list:
    print(kdrama)