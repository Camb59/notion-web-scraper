import os
import logging
import traceback
from typing import Dict
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

def identify_main_content(soup: BeautifulSoup) -> BeautifulSoup:
    """メインコンテンツと思われる要素を特定"""
    # よくあるメインコンテンツのセレクタやクラス名
    selectors = [
        'article',
        'main',
        '#main-content',
        '.main-content',
        '.post-content',
        '.article-content',
        '.entry-content',
        '.content'
    ]
    
    for selector in selectors:
        content = soup.select_one(selector)
        if content:
            return content
    
    # 最大のテキストコンテンツを持つdivを探す
    max_text_len = 0
    main_div = None
    for div in soup.find_all('div'):
        text_len = len(div.get_text())
        if text_len > max_text_len:
            max_text_len = text_len
            main_div = div
    
    return main_div

def clean_text(text: str) -> str:
    """テキストのクリーニング"""
    if not text:
        return ""
    # 余分な空白と改行を削除
    text = " ".join(text.split())
    return text

def extract_metadata(soup: BeautifulSoup, url: str) -> Dict[str, str]:
    """メタデータを抽出"""
    metadata = {}
    
    # タイトルの抽出
    title = soup.find('meta', {'property': 'og:title'})
    if not title:
        title = soup.find('title')
    metadata['title'] = title.get('content', '') if title and title.get('content') else title.string if title else ''

    # 説明文の抽出
    description = soup.find('meta', {'property': 'og:description'}) or soup.find('meta', {'name': 'description'})
    metadata['description'] = description.get('content', '') if description else ''

    # 著者の抽出
    author = soup.find('meta', {'name': 'author'}) or soup.find('meta', {'property': 'article:author'})
    metadata['author'] = author.get('content', '') if author else ''

    # 日付の抽出
    date = (
        soup.find('meta', {'property': 'article:published_time'}) or
        soup.find('meta', {'property': 'article:modified_time'}) or
        soup.find('time')
    )
    metadata['date'] = date.get('content', '') if date and date.get('content') else date.get('datetime', '') if date else ''

    # サイト名の抽出
    site_name = soup.find('meta', {'property': 'og:site_name'})
    metadata['site_name'] = site_name.get('content', '') if site_name else ''

    # ヘッダー画像の抽出
    header_image = soup.find('meta', {'property': 'og:image'})
    if header_image and header_image.get('content'):
        metadata['header_image'] = urljoin(url, header_image.get('content', ''))
    
    return metadata

def extract_main_content(soup: BeautifulSoup, url: str) -> str:
    # メインコンテンツを取得
    main_content = soup.find('div', {'itemprop': 'articleBody'})
    if not main_content:
        main_content = identify_main_content(soup)
    
    if not main_content:
        raise Exception("メインコンテンツが見つかりませんでした")

    # 関連記事セクションを検出して削除
    related_content = main_content.find(lambda tag: tag.name and 
        (
            '関連' in tag.get_text() or 
            'related' in tag.get_text().lower() or
            'おすすめ' in tag.get_text() or
            'recommend' in tag.get_text().lower()
        )
    )
    if related_content:
        # 関連記事セクションとその後のすべての要素を削除
        for sibling in related_content.find_all_next():
            sibling.decompose()
        related_content.decompose()

    # 不要な要素を削除
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
        response.encoding = response.apparent_encoding
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract metadata and content
        metadata = extract_metadata(soup, url)
        content = extract_main_content(soup, url)
        
        # データの検証とクリーニング
        cleaned_data = {
            'title': clean_text(metadata.get('title', '')),
            'content': content,  # HTMLコンテンツをそのまま保持
            'description': clean_text(metadata.get('description', '')),
            'author': clean_text(metadata.get('author', '')),
            'date': clean_text(metadata.get('date', '')),
            'header_image': metadata.get('header_image', ''),
            'site_name': clean_text(metadata.get('site_name', '')),
            'url': url
        }
        
        # エンコーディング問題の対処
        for key, value in cleaned_data.items():
            if isinstance(value, str):
                cleaned_data[key] = value.encode('utf-8', errors='replace').decode('utf-8')
        
        return cleaned_data
            
    except requests.RequestException as e:
        error_msg = f"Network error: {str(e)}"
        logging.error(error_msg)
        raise Exception(error_msg)
    except Exception as e:
        error_msg = f"Scraping error: {str(e)}"
        logging.error(f"Error in scrape_url: {error_msg}")
        logging.error(f"Traceback: {traceback.format_exc()}")
        raise Exception(error_msg)
