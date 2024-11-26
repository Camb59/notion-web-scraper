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
import traceback

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
    logging.info(f"Extracting metadata from {url}")
    
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
        logging.debug(f"Extracted title: {metadata['title']}")
    
    # Enhanced meta tags mapping with priority order
    meta_tags = {
        'article:author': 'author',
        'dc:creator': 'author',
        'author': 'author',
        'og:site_name': 'site_name',
        'og:title': 'title',
        'og:description': 'description',
        'og:image': 'header_image',
        'article:published_time': 'date',
        'description': 'description',
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
                logging.debug(f"Found meta tag {property_name}: {content}")

    # Additional author detection from schema.org metadata
    schema_tags = soup.find_all('script', type='application/ld+json')
    for tag in schema_tags:
        try:
            if not tag.string:
                continue
            
            json_str = clean_text(tag.string)
            
            # Remove any BOM or invalid starting characters
            while json_str and not json_str[0] in '{[':
                json_str = json_str[1:]
                logging.debug("Removed invalid starting character from JSON")
            
            if not json_str:
                continue
            
            schema_data = json.loads(json_str)
            logging.debug("Successfully parsed JSON-LD data")
            
            if isinstance(schema_data, dict):
                # Extract author information
                if 'author' in schema_data:
                    author_data = schema_data['author']
                    if isinstance(author_data, dict) and 'name' in author_data:
                        if not metadata['author']:
                            metadata['author'] = clean_text(author_data['name'])
                            logging.debug(f"Found author in JSON-LD: {metadata['author']}")
                    elif isinstance(author_data, str):
                        if not metadata['author']:
                            metadata['author'] = clean_text(author_data)
                            logging.debug(f"Found author string in JSON-LD: {metadata['author']}")
                
                # Extract publisher information
                if 'publisher' in schema_data:
                    publisher_data = schema_data['publisher']
                    if isinstance(publisher_data, dict) and 'name' in publisher_data:
                        if not metadata['site_name']:
                            metadata['site_name'] = clean_text(publisher_data['name'])
                            logging.debug(f"Found publisher in JSON-LD: {metadata['site_name']}")
                    elif isinstance(publisher_data, str):
                        if not metadata['site_name']:
                            metadata['site_name'] = clean_text(publisher_data)
                            logging.debug(f"Found publisher string in JSON-LD: {metadata['site_name']}")
                            
        except json.JSONDecodeError as e:
            logging.warning(f"Failed to parse JSON-LD: {str(e)}, content: {json_str[:100]}...")
            continue
        except Exception as e:
            logging.error(f"Unexpected error parsing JSON-LD: {str(e)}")
            logging.error(traceback.format_exc())
            continue

    # Ensure header image is absolute URL
    if metadata['header_image']:
        metadata['header_image'] = urljoin(url, metadata['header_image'])
        logging.debug(f"Converted header image to absolute URL: {metadata['header_image']}")
    
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
                logging.debug(f"Found date in HTML: {date_str}")
                break
            except ValueError:
                continue

    logging.info("Metadata extraction completed")
    return metadata

def scrape_url(url: str, max_retries: int = 3, retry_delay: int = 1) -> Dict[str, str]:
    """
    Scrape content from the given URL with improved extraction and error handling
    """
    logging.info(f"Starting to scrape URL: {url}")
    last_error = None
    
    for attempt in range(max_retries):
        try:
            logging.info(f"Attempt {attempt + 1} of {max_retries}")
            
            # Download content with timeout
            logging.debug("Fetching URL content")
            downloaded = trafilatura.fetch_url(url, timeout=30)
            if not downloaded:
                raise Exception("Failed to download content")
            
            # Extract main content with trafilatura
            logging.debug("Extracting content using trafilatura")
            main_content = trafilatura.extract(
                downloaded,
                include_images=True,
                include_links=True,
                include_tables=True,
                output_format='html',
                with_metadata=True
            )
            
            if not main_content:
                raise Exception("No content could be extracted")
            
            # Parse with BeautifulSoup for additional metadata
            logging.debug("Making request for metadata extraction")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract metadata
            metadata = extract_metadata(soup, url)
            
            # Clean and sanitize all extracted content
            logging.debug("Cleaning and sanitizing extracted content")
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
                logging.debug("Verifying JSON serialization")
                json.dumps(cleaned_data)
                logging.info("Successfully scraped and processed URL")
                return cleaned_data
            except (TypeError, ValueError) as e:
                logging.error(f"JSON serialization error: {str(e)}")
                logging.debug("Attempting to convert all values to strings")
                # If serialization fails, ensure all values are strings
                return {k: str(v) for k, v in cleaned_data.items()}
            
        except requests.RequestException as e:
            last_error = f"Network error: {str(e)}"
            logging.error(f"Network error on attempt {attempt + 1}: {str(e)}")
        except json.JSONDecodeError as e:
            last_error = f"JSON parsing error: {str(e)}"
            logging.error(f"JSON parsing error on attempt {attempt + 1}: {str(e)}")
        except Exception as e:
            last_error = str(e)
            logging.error(f"Error in scrape_url (attempt {attempt + 1}): {last_error}")
            logging.error(f"Traceback: {traceback.format_exc()}")
        
        if attempt < max_retries - 1:
            logging.info(f"Waiting {retry_delay} seconds before retry")
            time.sleep(retry_delay)
            continue
        break
    
    error_msg = f"Failed to scrape URL after {max_retries} attempts: {last_error}"
    logging.error(error_msg)
    raise Exception(error_msg)
