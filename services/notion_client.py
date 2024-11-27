from notion_client import Client
import os
import logging
from typing import Dict, Any, Optional
import traceback
from datetime import datetime

notion = Client(auth=os.environ["NOTION_TOKEN"])

def get_database_properties() -> Dict[str, Any]:
    """
    Get all properties from the Notion database with improved error handling
    and standardized property mapping, excluding specific properties
    """
    try:
        database_id = os.environ.get("NOTION_DATABASE_ID")
        if not database_id:
            raise ValueError("NOTION_DATABASE_IDが設定されていません")
            
        # Fetch database metadata
        database = notion.databases.retrieve(database_id=database_id)
        
        # Property type mapping
        type_mapping = {
            "title": "text",
            "rich_text": "text",
            "select": "select",
            "multi_select": "multi_select",
            "date": "date",
            "url": "url",
            "checkbox": "checkbox",
            "number": "number",
            "email": "email",
            "phone_number": "phone",
            "files": "files"
        }
        
        # List of properties to exclude
        excluded_properties = {
            "AI キーワード",
            "AI 要約",
            "Cat１ego１２ry",
            "Content１Type１１０",
            "Parent item",
            "Sub-item",
            "作成日",
            "MainCategory",  # 追加
            "SubCategory"    # 追加
        }
        
        # Extract and format properties
        properties = {}
        for prop_name, prop_data in database["properties"].items():
            # Skip excluded properties
            if prop_name in excluded_properties:
                logging.debug(f"除外されたプロパティをスキップ: {prop_name}")
                continue
                
            prop_type = prop_data["type"]
            prop_info = {
                "id": prop_data["id"],
                "name": prop_name,
                "type": type_mapping.get(prop_type, prop_type)
            }
            
            # Add options for select and multi_select properties
            if prop_type in ["select", "multi_select"] and "options" in prop_data[prop_type]:
                if prop_name == "重要度":
                    prop_info["options"] = [
                        {"label": "★☆☆", "value": "★☆☆"},
                        {"label": "★★☆", "value": "★★☆"},
                        {"label": "★★★", "value": "★★★"}
                    ]
                else:
                    prop_info["options"] = [
                        {"label": option["name"], "value": option["name"]}
                        for option in prop_data[prop_type]["options"]
                    ]

            # Add relation properties
            if prop_type == "relation":
                prop_info["database_id"] = prop_data["relation"]["database_id"]
                try:
                    # データベースの全ページを取得
                    relation_database_id = prop_data["relation"]["database_id"]
                    pages = notion.databases.query(
                        database_id=relation_database_id,
                        page_size=100  # 最大100ページまで取得
                    ).get("results", [])
                    
                    # ページのタイトルを選択肢として追加
                    prop_info["options"] = []
                    for page in pages:
                        # タイトルプロパティを取得
                        properties = page.get("properties", {})
                        title = None
                        
                        # 全プロパティから最初のtitleタイプを探す
                        for prop in properties.values():
                            if prop["type"] == "title" and prop["title"]:
                                title = prop["title"][0]["plain_text"]
                                break
                        
                        if title:
                            prop_info["options"].append({
                                "label": title,
                                "value": page["id"]
                            })
                    
                    prop_info["type"] = "relation_select"
                    logging.info(f"Retrieved {len(prop_info['options'])} pages from relation database")
                except Exception as e:
                    logging.error(f"関連データベースのページ取得エラー: {str(e)}")
                    prop_info["options"] = []
                else:
                    # Fetch related database title for other databases
                    try:
                        related_db = notion.databases.retrieve(database_id=prop_info["database_id"])
                        prop_info["database_title"] = related_db["title"][0]["plain_text"]
                    except Exception as e:
                        logging.error(f"関連データベースの取得エラー: {str(e)}")
                        prop_info["database_title"] = "Unknown Database"
            
            properties[prop_name] = prop_info
            
        return {
            "status": "success",
            "data": properties
        }
    except ValueError as ve:
        error_msg = str(ve)
        logging.error(f"バリデーションエラー: {error_msg}")
        return {
            "status": "error",
            "error": error_msg,
            "type": "validation_error"
        }
    except Exception as e:
        error_msg = str(e)
        logging.error(f"Notionプロパティ取得エラー: {error_msg}")
        logging.error(f"トレースバック: {traceback.format_exc()}")
        return {
            "status": "error",
            "error": "Notionデータベースのプロパティ取得に失敗しました",
            "type": "system_error",
            "details": error_msg
        }

def create_notion_page(content: Any, properties: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new page in Notion with the given content and properties"""
    try:
        database_id = os.environ.get("NOTION_DATABASE_ID")
        if not database_id:
            raise ValueError("NOTION_DATABASE_IDが設定されていません")
        
        # Validate properties
        database_props = get_database_properties()
        if database_props["status"] == "error":
            raise ValueError(f"データベースプロパティの取得に失敗: {database_props['error']}")
        
        valid_props = database_props["data"]
        
        # Prepare automatic property mappings with enhanced error handling
        current_time = datetime.now().isoformat()
        auto_properties = {
            "titlename": {
                "title": [{"text": {"content": content.title or ""}}]
            },
            "日付": {
                "date": {"start": current_time}
            },
            "作成日時": {
                "created_time": current_time
            },
            "発言者": {
                "rich_text": [{"text": {"content": content.author or content.site_name or ""}}]
            },
            "URL": {
                "url": content.url
            }
        }
        
        # Prepare page content
        page_content = {
            "parent": {"database_id": database_id},
            "properties": {
                **auto_properties,
                "URL": {
                    "url": content.url
                },
                "Content": {
                    "rich_text": [{"text": {"content": content.content[:2000] if content.content else ""}}]
                }
            }
        }
        
        # Add custom properties with validation
        for prop_name, prop_value in properties.items():
            if prop_name in ["URL", "Content"] or prop_name in auto_properties:
                continue
                
            if prop_name not in valid_props:
                logging.warning(f"無効なプロパティをスキップ: {prop_name}")
                continue
                
            prop_type = valid_props[prop_name]["type"]
            try:
                if isinstance(prop_value, dict):
                    page_content["properties"][prop_name] = prop_value
                else:
                    # Default handling for string values
                    if prop_type == "rich_text":
                        page_content["properties"][prop_name] = {
                            "rich_text": [{"text": {"content": str(prop_value)}}]
                        }
                    elif prop_type == "select":
                        page_content["properties"][prop_name] = {
                            "select": {"name": str(prop_value)}
                        }
                    elif prop_type == "date":
                        page_content["properties"][prop_name] = {
                            "date": {"start": str(prop_value)}
                        }
                    elif prop_type == "relation_select":
                        page_content["properties"][prop_name] = {
                            "relation": [{"id": str(prop_value)}]
                        }
            except Exception as e:
                logging.error(f"プロパティのフォーマットエラー {prop_name}: {str(e)}")
                continue
        
        # Create page
        response = notion.pages.create(**page_content)
        return {
            "status": "success",
            "data": {
                "page_id": response["id"]
            }
        }
    except ValueError as ve:
        error_msg = str(ve)
        logging.error(f"バリデーションエラー: {error_msg}")
        return {
            "status": "error",
            "error": error_msg,
            "type": "validation_error"
        }
    except Exception as e:
        error_msg = str(e)
        logging.error(f"Notionページ作成エラー: {error_msg}")
        logging.error(f"トレースバック: {traceback.format_exc()}")
        return {
            "status": "error",
            "error": "Notionページの作成に失敗しました",
            "type": "system_error",
            "details": error_msg
        }
