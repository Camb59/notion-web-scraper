from datetime import datetime
from app import db

class ScrapedContent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(2048), nullable=False)
    title = db.Column(db.String(512))
    content = db.Column(db.Text)
    description = db.Column(db.Text)
    author = db.Column(db.String(256))
    publish_date = db.Column(db.String(64))
    site_name = db.Column(db.String(256))
    translated_title = db.Column(db.String(512))
    translated_content = db.Column(db.Text)
    translated_description = db.Column(db.Text)
    header_image = db.Column(db.String(2048))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    notion_page_id = db.Column(db.String(256))

    def to_dict(self):
        return {
            'id': self.id,
            'url': self.url,
            'title': self.title,
            'content': self.content,
            'description': self.description,
            'author': self.author,
            'publish_date': self.publish_date,
            'site_name': self.site_name,
            'translated_title': self.translated_title,
            'translated_content': self.translated_content,
            'translated_description': self.translated_description,
            'header_image': self.header_image,
            'created_at': self.created_at.isoformat(),
            'notion_page_id': self.notion_page_id
        }
