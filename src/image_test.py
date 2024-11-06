import requests
from bs4 import BeautifulSoup

# Set the URL of the IMDb page to scrape
url = "https://www.imdb.com/title/tt27668559/"

# Set the headers with a user agent
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
}

# Send a GET request to the IMDb page
response = requests.get(url, headers=headers)

# Check if the request was successful
if response.status_code == 200:
    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Find the <meta> tag with property "og:image"
    og_image = soup.find('meta', property='og:image')
    
    # Get the content attribute value (the image URL)
    if og_image and 'content' in og_image.attrs:
        image_url = og_image['content']
        print("Image URL:", image_url)
    else:
        print("Image URL not found.")
else:
    print("Failed to retrieve the page. Status code:", response.status_code)
