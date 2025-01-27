import os
import logging
import traceback
from flask import jsonify, request, render_template, Blueprint
from models import ScrapedContent, db
from services.scraper import scrape_url
from services.translator import translate_text

bp = Blueprint('main', __name__)

def register_routes(app):
    app.register_blueprint(bp)

@bp.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')

@bp.route('/api/scrape', methods=['POST'])
def scrape():
    try:
        if not request.is_json:
            return jsonify({
                "status": "error",
                "message": "Content-Type must be application/json"
            }), 400

        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({
                "status": "error",
                "message": "URLが必要です"
            }), 400

        url = data['url']
        scraped_data = scrape_url(url)
        
        if not scraped_data or not scraped_data.get('content'):
            return jsonify({
                "status": "error",
                "message": "コンテンツの抽出に失敗しました"
            }), 500

        # データベースへの保存処理
        content = ScrapedContent()
        content.url = url
        content.title = scraped_data.get('title', '')
        content.content = scraped_data.get('content', '')
        content.description = scraped_data.get('description', '')
        content.author = scraped_data.get('author', '')
        content.publish_date = scraped_data.get('date', '')
        content.site_name = scraped_data.get('site_name', '')
        content.header_image = scraped_data.get('header_image', '')
        
        db.session.add(content)
        db.session.commit()

        return jsonify({
            "status": "success",
            "data": {
                "id": content.id,
                "title": content.title,
                "content": content.content,
                "url": content.url
            }
        })

    except Exception as e:
        logging.error(f"Error in scrape: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"URLの抽出に失敗しました: {str(e)}"
        }), 500

@bp.route('/api/translate', methods=['POST'])
def translate():
    """Translate the scraped content"""
    try:
        data = request.get_json()
        if not data or 'content_id' not in data:
            return jsonify({"error": "Content ID is required"}), 400

        content = ScrapedContent.query.get(data['content_id'])
        if not content:
            return jsonify({"error": "Content not found"}), 404

        # Translate title and content
        translated_title = translate_text(content.title)
        translated_content = translate_text(content.content)
        translated_description = translate_text(content.description) if content.description else None

        # Update database
        content.translated_title = translated_title
        content.translated_content = translated_content
        content.translated_description = translated_description
        db.session.commit()

        return jsonify({
            "translated_title": translated_title,
            "translated_content": translated_content,
            "translated_description": translated_description
        })

    except Exception as e:
        logging.error(f"Error in translate: {str(e)}")
        logging.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500

@bp.route('/api/notion/properties', methods=['GET'])
def get_notion_properties():
    """Get all properties from the Notion database"""
    try:
        from services.notion_client import get_database_properties
        result = get_database_properties()
        
        if result["status"] == "error":
            error_code = 400 if result["type"] == "validation_error" else 500
            return jsonify({
                "status": "error",
                "message": result["error"],
                "type": result["type"],
                "details": result.get("details")
            }), error_code
        
        return jsonify({
            "status": "success",
            "data": result["data"]
        })
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@bp.route('/api/save-to-notion', methods=['POST'])
def save_to_notion():
    """Save content to Notion with selected properties"""
    try:
        data = request.get_json()
        if not data or 'content_id' not in data or 'properties' not in data:
            return jsonify({
                "status": "error",
                "message": "Missing required fields",
                "type": "validation_error"
            }), 400

        # Get content from database
        content = ScrapedContent.query.get(data['content_id'])
        if not content:
            return jsonify({
                "status": "error",
                "message": "Content not found",
                "type": "validation_error"
            }), 404

        # Save to Notion
        from services.notion_client import create_notion_page
        result = create_notion_page(content, data['properties'])

        if result["status"] == "error":
            error_code = 400 if result["type"] == "validation_error" else 500
            return jsonify({
                "status": "error",
                "message": result["error"],
                "type": result["type"],
                "details": result.get("details")
            }), error_code

        # Update notion_page_id in database
        content.notion_page_id = result["data"]["page_id"]
        db.session.commit()

        return jsonify({
            "status": "success",
            "data": result["data"]
        })

    except Exception as e:
        logging.error(f"Error in save_to_notion: {str(e)}")
        logging.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({
            "status": "error",
            "message": "Failed to save to Notion",
            "type": "system_error",
            "details": str(e)
        }), 500
