from typing import Dict, Any
import os
from notion_client import Client

notion = Client(auth=os.environ.get("NOTION_TOKEN"))

def get_database_properties():
    """Get all properties from the Notion database"""
    try:
        database_id = os.environ.get("NOTION_DATABASE_ID")
        if not database_id:
            raise Exception("Notion database ID not found")
            
        # Fetch database metadata
        database = notion.databases.retrieve(database_id=database_id)
        
        # Extract and format properties
        properties = {}
        for prop_name, prop_data in database["properties"].items():
            prop_type = prop_data["type"]
            prop_info = {
                "id": prop_data["id"],
                "name": prop_name,
                "type": prop_type
            }
            
            # Add options for select and multi_select properties
            if prop_type in ["select", "multi_select"] and "options" in prop_data[prop_type]:
                prop_info["options"] = [
                    {"label": option["name"], "value": option["name"]}
                    for option in prop_data[prop_type]["options"]
                ]
            
            properties[prop_name] = prop_info
            
        return properties
    except Exception as e:
        raise Exception(f"Failed to fetch Notion database properties: {str(e)}")
def create_notion_page(content: Any, properties: Dict[str, Any]) -> str:
    """Create a new page in Notion with the given content and properties"""
    try:
        database_id = os.environ.get("NOTION_DATABASE_ID")
        
        # Prepare page content
        page_content = {
            "parent": {"database_id": database_id},
            "properties": {
                "Title": {
                    "title": [{"text": {"content": content.title}}]
                },
                "URL": {
                    "url": content.url
                }
            }
        }
        
        # Add custom properties
        for prop_name, prop_value in properties.items():
            if prop_name in ["Title", "URL"]:
                continue
            page_content["properties"][prop_name] = prop_value
        
        # Create page
        response = notion.pages.create(**page_content)
        return response["id"]
    except Exception as e:
        raise Exception(f"Failed to create Notion page: {str(e)}")
