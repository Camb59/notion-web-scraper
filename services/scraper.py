import trafilatura
from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin

def scrape_url(url: str) -> dict:
    """Scrape content from the given URL"""
    try:
        # Download and extract main content
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            raise Exception("Failed to download content")

        main_content = trafilatura.extract(downloaded, include_images=True)
        
        # Parse with BeautifulSoup for additional metadata
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Get title
        title = soup.title.string if soup.title else ''
        
        # Try to find header image
        header_image = None
        og_image = soup.find('meta', property='og:image')
        if og_image:
            header_image = urljoin(url, og_image.get('content', ''))
        
        return {
            'title': title,
            'content': main_content,
            'header_image': header_image
        }
    except Exception as e:
        raise Exception(f"Failed to scrape URL: {str(e)}")
