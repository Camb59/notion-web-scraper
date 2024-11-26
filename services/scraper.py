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
    # メインコンテンツの特定
    main_content = None
    for selector in [
        'article', 'main', 
        '[role="main"]', 
        '#main-content', 
        '.main-content',
        '.post-content',
        '.entry-content'
    ]:
        main_content = soup.select_one(selector)
        if main_content:
            break

    if not main_content:
        main_content = soup.find('div', class_=lambda x: x and any(
            word in str(x).lower() for word in ['content', 'article', 'entry', 'post']
        ))

    if not main_content:
        main_content = soup

    # 不要な要素の削除
    for element in main_content.find_all(['script', 'style', 'iframe', 'nav', 'header', 'footer', 'aside']):
        element.decompose()

    # 画像の処理
    for img in main_content.find_all('img'):
        if img.get('src'):
            img['src'] = urljoin(url, img['src'])
            # 元のクラスを保持しつつ、新しいクラスを追加
            current_classes = img.get('class', [])
            if isinstance(current_classes, list):
                current_classes = ' '.join(current_classes)
            new_classes = f"{current_classes} max-w-full h-auto".strip()
            img['class'] = new_classes

    # テーブルの処理
    for table in main_content.find_all('table'):
        current_classes = table.get('class', [])
        if isinstance(current_classes, list):
            current_classes = ' '.join(current_classes)
        new_classes = f"{current_classes} w-full border-collapse".strip()
        table['class'] = new_classes
        
        for cell in table.find_all(['td', 'th']):
            current_classes = cell.get('class', [])
            if isinstance(current_classes, list):
                current_classes = ' '.join(current_classes)
            new_classes = f"{current_classes} border p-2".strip()
            cell['class'] = new_classes

    # HTMLの構造を維持したまま返す
    return str(main_content)

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
