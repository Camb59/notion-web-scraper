import json
from flask import request, jsonify
from flask import render_template
from app import app, db
from models import ScrapedContent
from services.scraper import scrape_url
from services.translator import translate_text
from services.notion_client import create_notion_page

@app.route('/api/scrape', methods=['POST'])
def scrape_content():
    try:
        url = request.json.get('url')
        if not url:
            return jsonify({'error': 'URL is required'}), 400

        # Check cache
        existing_content = ScrapedContent.query.filter_by(url=url).first()
        if existing_content:
            return jsonify(existing_content.to_dict())

        # Scrape new content
        scraped_data = scrape_url(url)
        content = ScrapedContent(
            url=url,
            title=scraped_data['title'],
            content=scraped_data['content'],
            header_image=scraped_data.get('header_image')
        )
        db.session.add(content)
        db.session.commit()

        return jsonify(content.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/translate', methods=['POST'])
def translate_content():
    try:
        content_id = request.json.get('content_id')
        content = ScrapedContent.query.get(content_id)
        if not content:
            return jsonify({'error': 'Content not found'}), 404

        if not content.translated_title:
            content.translated_title = translate_text(content.title)
            content.translated_content = translate_text(content.content)
            db.session.commit()

        return jsonify(content.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/save-to-notion', methods=['POST'])
def save_to_notion():
    try:
        content_id = request.json.get('content_id')
        properties = request.json.get('properties', {})
        
        content = ScrapedContent.query.get(content_id)
        if not content:
            return jsonify({'error': 'Content not found'}), 404

        # Create Notion page
        page_id = create_notion_page(content, properties)
        content.notion_page_id = page_id
        db.session.commit()

        return jsonify({'success': True, 'notion_page_id': page_id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/')
def index():
    return render_template('index.html')
