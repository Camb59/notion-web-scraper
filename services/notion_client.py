from typing import Dict, Any
import os
from notion_client import Client

notion = Client(auth=os.environ.get("NOTION_TOKEN"))

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
