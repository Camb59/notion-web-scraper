from notion_client import Client
import os
import logging
from typing import Dict, Any, Optional
import traceback

notion = Client(auth=os.environ["NOTION_TOKEN"])

def get_database_properties() -> Dict[str, Any]:
    """
    Get all properties from the Notion database with improved error handling
    and standardized property mapping
    """
    try:
        database_id = os.environ.get("NOTION_DATABASE_ID")
        if not database_id:
            raise ValueError("NOTION_DATABASE_ID environment variable is not set")
            
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
        
        # Extract and format properties
        properties = {}
        for prop_name, prop_data in database["properties"].items():
            prop_type = prop_data["type"]
            prop_info = {
                "id": prop_data["id"],
                "name": prop_name,
                "type": type_mapping.get(prop_type, prop_type)
            }
            
            # Add options for select and multi_select properties
            if prop_type in ["select", "multi_select"] and "options" in prop_data[prop_type]:
                prop_info["options"] = [
                    {"label": option["name"], "value": option["name"]}
                    for option in prop_data[prop_type]["options"]
                ]
            
            properties[prop_name] = prop_info
            
        return {
            "status": "success",
            "data": properties
        }
    except ValueError as ve:
        error_msg = str(ve)
        logging.error(f"Validation error in get_database_properties: {error_msg}")
        return {
            "status": "error",
            "error": error_msg,
            "type": "validation_error"
        }
    except Exception as e:
        error_msg = str(e)
        logging.error(f"Error in get_database_properties: {error_msg}")
        logging.error(f"Traceback: {traceback.format_exc()}")
        return {
            "status": "error",
            "error": "Failed to fetch Notion database properties",
            "type": "system_error",
            "details": error_msg
        }

def create_notion_page(content: Any, properties: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new page in Notion with the given content and properties"""
    try:
        database_id = os.environ.get("NOTION_DATABASE_ID")
        if not database_id:
            raise ValueError("NOTION_DATABASE_ID environment variable is not set")
        
        # Validate properties
        database_props = get_database_properties()
        if database_props["status"] == "error":
            raise ValueError(f"Failed to get database properties: {database_props['error']}")
        
        valid_props = database_props["data"]
        
        # Prepare page content
        page_content = {
            "parent": {"database_id": database_id},
            "properties": {
                "Title": {
                    "title": [{"text": {"content": content.title}}]
                },
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
            if prop_name in ["Title", "URL", "Content"]:
                continue
                
            if prop_name not in valid_props:
                logging.warning(f"Skipping invalid property: {prop_name}")
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
            except Exception as e:
                logging.error(f"Error formatting property {prop_name}: {str(e)}")
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
        logging.error(f"Validation error in create_notion_page: {error_msg}")
        return {
            "status": "error",
            "error": error_msg,
            "type": "validation_error"
        }
    except Exception as e:
        error_msg = str(e)
        logging.error(f"Error in create_notion_page: {error_msg}")
        logging.error(f"Traceback: {traceback.format_exc()}")
        return {
            "status": "error",
            "error": "Failed to create Notion page",
            "type": "system_error",
            "details": error_msg
        }
