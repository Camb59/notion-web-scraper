import os
import logging
import traceback
from flask import jsonify, request, render_template
from app import app, db
from models import ScrapedContent
from services.scraper import scrape_url
from services.translator import translate_text

@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')

@app.route('/api/scrape', methods=['POST'])
def scrape():
    """Scrape content from the given URL with improved error handling"""
    try:
        # Validate request
        if not request.is_json:
            return jsonify({
                "status": "error",
                "message": "Content-Type must be application/json",
                "type": "validation_error"
            }), 400

        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({
                "status": "error",
                "message": "URL is required",
                "type": "validation_error"
            }), 400

        url = data['url']
        
        # Scrape URL with proper error handling
        try:
            scraped_data = scrape_url(url)
        except Exception as scrape_error:
            return jsonify({
                "status": "error",
                "message": "Failed to scrape URL",
                "type": "scraping_error",
                "details": str(scrape_error)
            }), 500

        # Save to database with validation
        try:
            content = ScrapedContent(
                url=url,
                title=scraped_data.get('title', ''),
                content=scraped_data.get('content', ''),
                description=scraped_data.get('description', ''),
                author=scraped_data.get('author', ''),
                publish_date=scraped_data.get('date', ''),
                site_name=scraped_data.get('site_name', ''),
                header_image=scraped_data.get('header_image', '')
            )
            db.session.add(content)
            db.session.commit()
        except Exception as db_error:
            db.session.rollback()
            return jsonify({
                "status": "error",
                "message": "Database error",
                "type": "database_error",
                "details": str(db_error)
            }), 500

        # Return standardized successful response
        return jsonify({
            "status": "success",
            "data": content.to_dict()
        })

    except Exception as e:
        logging.error(f"Error in scrape: {str(e)}")
        logging.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({
            "status": "error",
            "message": "Internal server error",
            "type": "system_error",
            "details": str(e)
        }), 500

@app.route('/api/translate', methods=['POST'])
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

@app.route('/api/notion/properties', methods=['GET'])
def get_notion_properties():
    """Get all properties from the Notion database"""
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

@app.route('/api/save-to-notion', methods=['POST'])
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
