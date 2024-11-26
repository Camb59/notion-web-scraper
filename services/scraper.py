import trafilatura
from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin
from typing import Dict, Optional, Any
import time
from datetime import datetime
import json
import html
import logging
import re

def clean_text(text: str) -> str:
    """Clean and sanitize text content"""
    if not text:
        return ""
    
    # Decode HTML entities
    text = html.unescape(text)
    
    # Remove control characters
    text = "".join(char for char in text if ord(char) >= 32 or char in "\n\r\t")
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

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
        metadata['title'] = clean_text(soup.title.string) if soup.title.string else ''
    
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
    
    # Extract from meta tags
    for tag in soup.find_all('meta'):
        property_name = tag.get('property', tag.get('name', ''))
        if property_name in meta_tags:
            content = clean_text(tag.get('content', ''))
            if content and not metadata[meta_tags[property_name]]:
                metadata[meta_tags[property_name]] = content

    # Additional author detection from schema.org metadata
    schema_tags = soup.find_all('script', type='application/ld+json')
    for tag in schema_tags:
        try:
            # Clean and sanitize JSON string
            if not tag.string:
                continue
            
            json_str = clean_text(tag.string)
            
            # Remove any BOM or invalid starting characters
            while json_str and not json_str[0] in '{[':
                json_str = json_str[1:]
            
            # Handle empty or invalid JSON
            if not json_str:
                continue
            
            schema_data = json.loads(json_str)
            
            if isinstance(schema_data, dict):
                # Extract author information
                if 'author' in schema_data:
                    author_data = schema_data['author']
                    if isinstance(author_data, dict) and 'name' in author_data:
                        if not metadata['author']:
                            metadata['author'] = clean_text(author_data['name'])
                    elif isinstance(author_data, str):
                        if not metadata['author']:
                            metadata['author'] = clean_text(author_data)
                
                # Extract publisher information
                if 'publisher' in schema_data:
                    publisher_data = schema_data['publisher']
                    if isinstance(publisher_data, dict) and 'name' in publisher_data:
                        if not metadata['site_name']:
                            metadata['site_name'] = clean_text(publisher_data['name'])
                    elif isinstance(publisher_data, str):
                        if not metadata['site_name']:
                            metadata['site_name'] = clean_text(publisher_data)
                            
        except json.JSONDecodeError as e:
            logging.warning(f"Failed to parse JSON-LD: {str(e)}, content: {json_str[:100]}...")
            continue
        except Exception as e:
            logging.error(f"Unexpected error parsing JSON-LD: {str(e)}")
            continue

    # Ensure header image is absolute URL
    if metadata['header_image']:
        metadata['header_image'] = urljoin(url, metadata['header_image'])
    
    # Try to find publication date if not in meta tags
    if not metadata['date']:
        date_elements = soup.find_all(['time', 'span', 'div'], 
            class_=lambda x: x and any(date_word in x.lower() 
            for date_word in ['date', 'time', 'published', 'posted']))
        for element in date_elements:
            date_str = clean_text(element.get('datetime', element.text))
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
            
            # Download content with timeout
            downloaded = trafilatura.fetch_url(url, timeout=30)
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
            
            # Clean and sanitize all extracted content
            cleaned_data = {
                'title': clean_text(metadata['title']),
                'content': clean_text(main_content),
                'description': clean_text(metadata['description']),
                'author': clean_text(metadata['author']),
                'date': clean_text(metadata['date']),
                'header_image': metadata['header_image'].strip(),
                'site_name': clean_text(metadata['site_name']),
                'url': url
            }
            
            # Verify JSON serialization
            try:
                json.dumps(cleaned_data)
                return cleaned_data
            except (TypeError, ValueError) as e:
                logging.error(f"JSON serialization error: {str(e)}")
                # If serialization fails, ensure all values are strings
                return {k: str(v) for k, v in cleaned_data.items()}
            
        except requests.RequestException as e:
            last_error = f"Network error: {str(e)}"
            logging.error(last_error)
        except json.JSONDecodeError as e:
            last_error = f"JSON parsing error: {str(e)}"
            logging.error(last_error)
        except Exception as e:
            last_error = str(e)
            logging.error(f"Error in scrape_url: {last_error}")
            logging.error(f"Traceback: {traceback.format_exc()}")
        
        if attempt < max_retries - 1:
            time.sleep(retry_delay)
            continue
        break
    
    raise Exception(f"Failed to scrape URL after {max_retries} attempts: {last_error}")
