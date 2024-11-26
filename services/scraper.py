import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from typing import Dict, Optional, Any
import logging
import html
import re
import traceback
import json
from datetime import datetime

def clean_text(text: Optional[str]) -> str:
    if not text:
        return ""
    
    try:
        # Decode HTML entities
        text = html.unescape(text)
        
        # Remove control characters
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')
        
        # Normalize whitespace while preserving meaningful line breaks
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

def extract_main_content(soup: BeautifulSoup, url: str) -> str:
    # メインコンテンツコンテナを検索
    for container in [
        soup.find('main'),
        soup.find('article'),
        soup.find(class_=lambda x: x and ('content' in x or 'article' in x)),
        soup.find(id=lambda x: x and ('content' in x or 'article' in x))
    ]:
        if container:
            # 不要な要素を削除
            for element in container.find_all(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                element.decompose()
            
            # 画像要素のsrcを絶対URLに変換
            for img in container.find_all('img'):
                if img.get('src'):
                    img['src'] = urljoin(url, img['src'])
                    
            # 見出し、段落、リスト等の構造を維持
            return str(container)
    
    # フォールバック：記事らしき部分を抽出
    content_area = soup.new_tag('div')
    for element in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'img', 'ul', 'ol', 'blockquote']):
        if element.name == 'img' and element.get('src'):
            element['src'] = urljoin(url, element['src'])
        content_area.append(element)
    
    return str(content_area)

def scrape_url(url: str) -> Dict[str, str]:
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        response.encoding = response.apparent_encoding
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract metadata
        metadata = extract_metadata(soup, url)
        
        # Extract main content with improved parsing
        content = extract_main_content(soup, url)
        
        # Clean and validate all data
        cleaned_data = {
            'title': clean_text(metadata.get('title', '')),
            'content': clean_text(content),
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
        error_msg = f"Network error: {str(e)}"
        logging.error(error_msg)
        raise Exception(error_msg)
    except Exception as e:
        error_msg = f"Scraping error: {str(e)}"
        logging.error(f"Error in scrape_url: {error_msg}")
        logging.error(f"Traceback: {traceback.format_exc()}")
        raise Exception(error_msg)
