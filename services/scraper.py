import trafilatura
from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin
from typing import Dict, Optional, Any
import time
import logging
import html
import re
import traceback
import json
from datetime import datetime

def clean_text(text: Optional[str]) -> str:
    """
    Clean and sanitize text content with improved handling
    
    Args:
        text: The text to clean
        
    Returns:
        str: The cleaned text
    """
    if not text:
        return ""
    
    try:
        # HTML entities decoding
        text = html.unescape(text)
        
        # Remove control characters except newlines and tabs
        text = "".join(char for char in text if ord(char) >= 32 or char in "\n\r\t")
        
        # Remove excessive whitespace while preserving newlines
        lines = text.split('\n')
        cleaned_lines = [re.sub(r'\s+', ' ', line).strip() for line in lines]
        text = '\n'.join(line for line in cleaned_lines if line)
        
        return text
    except Exception as e:
        logging.error(f"Error cleaning text: {str(e)}")
        return str(text) if text else ""

def extract_metadata(soup: BeautifulSoup, url: str) -> Dict[str, str]:
    """Extract metadata from webpage with enhanced error handling"""
    metadata = {
        'title': '',
        'description': '',
        'author': '',
        'date': '',
        'header_image': '',
        'site_name': ''
    }
    
    try:
        # Title extraction with fallbacks
        if soup.title:
            metadata['title'] = clean_text(soup.title.string)
        
        # Meta tags mapping
        meta_mapping = {
            'article:author': 'author',
            'author': 'author',
            'og:site_name': 'site_name',
            'og:title': 'title',
            'og:description': 'description',
            'og:image': 'header_image',
            'article:published_time': 'date',
            'description': 'description'
        }
        
        # Extract meta tags
        for tag in soup.find_all('meta'):
            property_name = tag.get('property', tag.get('name', ''))
            if property_name in meta_mapping:
                content = clean_text(tag.get('content', ''))
                if content and not metadata[meta_mapping[property_name]]:
                    metadata[meta_mapping[property_name]] = content
        
        # Ensure header image is absolute URL
        if metadata['header_image']:
            metadata['header_image'] = urljoin(url, metadata['header_image'])
        
        return metadata
    except Exception as e:
        logging.error(f"Error extracting metadata: {str(e)}")
        return metadata

def scrape_url(url: str, max_retries: int = 3, retry_delay: int = 1) -> Dict[str, str]:
    """
    Scrape content from URL with improved error handling and retries
    
    Args:
        url: The URL to scrape
        max_retries: Maximum number of retry attempts
        retry_delay: Delay between retries in seconds
        
    Returns:
        Dict containing scraped content
        
    Raises:
        Exception: If scraping fails after all retries
    """
    logging.info(f"Starting to scrape URL: {url}")
    last_error = None
    
    for attempt in range(max_retries):
        try:
            # Download content
            downloaded = trafilatura.fetch_url(url)
            if not downloaded:
                raise Exception("コンテンツのダウンロードに失敗しました")
            
            # Extract main content with safeguards
            main_content = trafilatura.extract(
                downloaded,
                include_images=True,
                include_links=True,
                include_tables=True,
                output_format='html',
                with_metadata=True,
                target_language='ja',
                url=url,  # Add URL for better link handling
                favor_precision=True,
                include_formatting=True
            )
            
            if not main_content:
                raise Exception("コンテンツの抽出に失敗しました")
            
            # Parse with BeautifulSoup for metadata
            soup = BeautifulSoup(downloaded, 'html.parser')
            metadata = extract_metadata(soup, url)
            
            # Clean and validate all data
            cleaned_data = {
                'title': clean_text(metadata.get('title', '')),
                'content': clean_text(main_content),
                'description': clean_text(metadata.get('description', '')),
                'author': clean_text(metadata.get('author', '')),
                'date': clean_text(metadata.get('date', '')),
                'header_image': metadata.get('header_image', ''),
                'site_name': clean_text(metadata.get('site_name', '')),
                'url': url
            }
            
            # Verify JSON serialization
            try:
                json.dumps(cleaned_data)
                return cleaned_data
            except (TypeError, ValueError) as e:
                logging.error(f"JSON serialization error: {str(e)}")
                # Convert all values to strings if serialization fails
                return {k: str(v) for k, v in cleaned_data.items()}
                
        except requests.RequestException as e:
            last_error = f"Network error: {str(e)}"
            logging.error(f"Network error on attempt {attempt + 1}: {str(e)}")
        except Exception as e:
            last_error = str(e)
            logging.error(f"Error in scrape_url (attempt {attempt + 1}): {str(e)}")
            logging.error(f"Traceback: {traceback.format_exc()}")
        
        if attempt < max_retries - 1:
            logging.info(f"Waiting {retry_delay} seconds before retry")
            time.sleep(retry_delay)
    
    error_msg = f"Failed to scrape URL after {max_retries} attempts: {last_error}"
    logging.error(error_msg)
    raise Exception(error_msg)