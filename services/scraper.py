import trafilatura
from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin
from typing import Dict, Optional
import time
from datetime import datetime

def extract_metadata(soup: BeautifulSoup, url: str) -> Dict[str, str]:
    """Extract metadata from the webpage with enhanced author and site name detection"""
    metadata = {
        'title': '',
        'description': '',
        'author': '',
        'date': '',
        'header_image': '',
        'site_name': '',
    }
    
    # Title extraction with fallbacks
    if soup.title:
        metadata['title'] = soup.title.string.strip() if soup.title.string else ''
    
    # Enhanced meta tags mapping with priority order
    meta_tags = {
        # High priority tags
        'article:author': 'author',
        'dc:creator': 'author',
        'author': 'author',
        'og:site_name': 'site_name',
        
        # Medium priority tags
        'og:title': 'title',
        'og:description': 'description',
        'og:image': 'header_image',
        'article:published_time': 'date',
        'description': 'description',
        
        # Additional author-related tags
        'twitter:creator': 'author',
        'article:publisher': 'site_name',
        'publisher': 'site_name',
    }
    
    # Additional author detection from schema.org metadata
    schema_tags = soup.find_all('script', type='application/ld+json')
    for tag in schema_tags:
        try:
            schema_data = json.loads(tag.string)
            if isinstance(schema_data, dict):
                if 'author' in schema_data and isinstance(schema_data['author'], dict):
                    if 'name' in schema_data['author'] and not metadata['author']:
                        metadata['author'] = schema_data['author']['name']
                if 'publisher' in schema_data and isinstance(schema_data['publisher'], dict):
                    if 'name' in schema_data['publisher'] and not metadata['site_name']:
                        metadata['site_name'] = schema_data['publisher']['name']
        except (json.JSONDecodeError, AttributeError):
            continue
    
    for tag in soup.find_all('meta'):
        property_name = tag.get('property', tag.get('name', ''))
        if property_name in meta_tags:
            content = tag.get('content', '')
            if content and not metadata[meta_tags[property_name]]:
                metadata[meta_tags[property_name]] = content

    # Ensure header image is absolute URL
    if metadata['header_image']:
        metadata['header_image'] = urljoin(url, metadata['header_image'])
    
    # Try to find publication date if not in meta tags
    if not metadata['date']:
        date_elements = soup.find_all(['time', 'span', 'div'], 
            class_=lambda x: x and any(date_word in x.lower() 
            for date_word in ['date', 'time', 'published', 'posted']))
        for element in date_elements:
            date_str = element.get('datetime', element.text)
            try:
                datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                metadata['date'] = date_str
                break
            except ValueError:
                continue

    return metadata

def scrape_url(url: str, max_retries: int = 3, retry_delay: int = 1) -> Dict[str, str]:
    """
    Scrape content from the given URL with improved extraction and error handling
    
    Args:
        url: The URL to scrape
        max_retries: Maximum number of retry attempts
        retry_delay: Delay between retries in seconds
    
    Returns:
        Dictionary containing extracted content and metadata
    
    Raises:
        Exception: If scraping fails after all retries
    """
    last_error = None
    
    for attempt in range(max_retries):
        try:
            # Configure trafilatura settings for better extraction
            config = trafilatura.extract.DEFAULT_CONFIG
            config.set('DEFAULT', 'MIN_EXTRACTED_SIZE', '100')
            config.set('DEFAULT', 'EXTRACTION_TIMEOUT', '30')
            config.set('DEFAULT', 'INCLUDE_TABLES', 'True')
            config.set('DEFAULT', 'INCLUDE_IMAGES', 'True')
            config.set('DEFAULT', 'INCLUDE_LINKS', 'True')
            
            # Download content
            downloaded = trafilatura.fetch_url(url)
            if not downloaded:
                raise Exception("Failed to download content")
            
            # Extract main content with trafilatura
            main_content = trafilatura.extract(
                downloaded,
                config=config,
                include_images=True,
                include_links=True,
                include_tables=True,
                output_format='html',
                with_metadata=True
            )
            
            if not main_content:
                raise Exception("No content could be extracted")
            
            # Parse with BeautifulSoup for additional metadata
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract metadata
            metadata = extract_metadata(soup, url)
            
            # Combine results
            return {
                'title': metadata['title'],
                'content': main_content,
                'description': metadata['description'],
                'author': metadata['author'],
                'date': metadata['date'],
                'header_image': metadata['header_image'],
                'site_name': metadata['site_name']
            }
            
        except Exception as e:
            last_error = str(e)
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            break
    
    raise Exception(f"Failed to scrape URL after {max_retries} attempts: {last_error}")
