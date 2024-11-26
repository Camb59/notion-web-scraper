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
    # メインコンテンツの検出を改善
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

    # 不要な要素を削除
    # Remove col-sm-8 class from articleBody elements
    for article_body in main_content.find_all('div', {'itemprop': 'articleBody'}):
        if article_body.get('class'):
            classes = article_body['class']
            if 'col-sm-8' in classes:
                classes.remove('col-sm-8')
            article_body['class'] = ' '.join(classes)
    for element in main_content.find_all(['script', 'style', 'iframe', 'nav', 'header', 'footer', 'aside']):
        element.decompose()

    # 画像の処理を改善
    for img in main_content.find_all('img'):
        if img.get('src'):
            img['src'] = urljoin(url, img['src'])
            img['loading'] = 'lazy'
            img['style'] = 'max-width: 100%; height: auto; display: block; margin: 0 auto;'
        if img.get('data-src'):  # 遅延読み込み対応
            img['src'] = urljoin(url, img['data-src'])

    # テーブルの処理を改善
    for table in main_content.find_all('table'):
        table['class'] = 'w-full border-collapse my-4'
        for cell in table.find_all(['td', 'th']):
            cell['class'] = 'border p-2'

    # トーク形式の処理を引用ブロックに変更
    for talk_div in main_content.find_all('div', class_='talk'):
        if talk_div:
            # テキスト部分を取得
            balloon_div = talk_div.find('div', class_='talk-balloonR')
            if balloon_div:
                text_div = balloon_div.find('div', class_='talk-text')
                if text_div:
                    # 新しい引用ブロックを作成
                    blockquote = soup.new_tag('blockquote')
                    blockquote['class'] = 'notion-quote'
                    blockquote.string = text_div.get_text()
                    # 元の吹き出しを引用ブロックで置き換え
                    talk_div.replace_with(blockquote)

    # スタイルを維持したまま返す
    return str(main_content)

def scrape_url(url: str) -> Dict[str, str]:
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # エンコーディングの処理を改善
        if response.encoding == 'ISO-8859-1':
            response.encoding = response.apparent_encoding
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # メタデータとコンテンツの抽出
        metadata = extract_metadata(soup, url)
        content = extract_main_content(soup, url)
        
        if not content:
            raise Exception("メインコンテンツを抽出できませんでした")
        
        # データの検証とクリーニング
        cleaned_data = {
            'title': clean_text(metadata.get('title', '')),
            'content': content,
            'description': clean_text(metadata.get('description', '')),
            'author': clean_text(metadata.get('author', '')),
            'date': clean_text(metadata.get('date', '')),
            'header_image': metadata.get('header_image', ''),
            'site_name': clean_text(metadata.get('site_name', '')),
            'url': url
        }
        
        return cleaned_data
            
    except requests.RequestException as e:
        raise Exception(f"ネットワークエラー: {str(e)}")
    except Exception as e:
        logging.error(f"Scraping error: {str(e)}")
        logging.error(f"Traceback: {traceback.format_exc()}")
        raise Exception(f"スクレイピングエラー: {str(e)}")
