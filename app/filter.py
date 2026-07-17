from markupsafe import Markup
from urllib.parse import urlparse # Import Python's built-in URL parser at the top!
from datetime import datetime

import bleach
import markdown
import re

from app import app

@app.template_filter('markdown')
def markdown_filter(text):
    if not text:
        return ""
    
    # 1. Convert the raw Markdown into HTML
    raw_html = markdown.markdown(text)
    
    # 2. The VIP List: Exactly which HTML tags are allowed to exist
    allowed_tags = [
        'a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
        'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'br', 'img', 'hr'
    ]
    
    # 3. Allowed Attributes: Prevent malicious links or image sources
    allowed_attrs = {
        'a': ['href', 'title', 'target'],
        'img': ['src', 'alt', 'title']
    }
    
    # 4. Scrub the HTML clean with Bleach
    clean_html = bleach.clean(raw_html, tags=allowed_tags, attributes=allowed_attrs)
    
    # 5. Markup() tells Jinja the code is now perfectly safe to render!
    return Markup(clean_html)

@app.template_filter('parse_links')
def parse_links_filter(text):
    if not text:
        return []
        
    formatted_links = []
    
    # --- Phase 1: Process Markdown Links ---
    # Find all pairs of [Title](URL)
    markdown_links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', text)
    
    for title, raw_url in markdown_links:
        clean_url = raw_url.strip()
        
        # PROTOCOL FIX: If you typed a Markdown link without https://, add it automatically
        if not clean_url.startswith(('http://', 'https://')):
            clean_url = f"https://{clean_url}"
            
        formatted_links.append((title, clean_url))
        
    # --- Phase 2: Prepare Text for Raw Links ---
    # We must ERASE the markdown links from the text block before running the raw URL search.
    # Otherwise, the raw URL search will rip the links out of the Markdown brackets and duplicate them.
    text_without_markdown = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', ' ', text)
        
    # --- Phase 3: Process Raw Links ---
    url_pattern = r'\b(?:https?://|www\.)[^\s,]+|\b[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:/[^\s,]*)?'
    raw_urls = re.findall(url_pattern, text_without_markdown)
    
    for url in raw_urls:
        clean_url = url.rstrip('.,;!?').strip()
        
        # PROTOCOL FIX: If it's a naked domain like 'www.instagram.com', add https://
        if not clean_url.startswith(('http://', 'https://')):
            clean_url = f"https://{clean_url}"
            
        try:
            parsed = urlparse(clean_url)
            domain = parsed.netloc.replace('www.', '')
            title = domain if domain else clean_url
            formatted_links.append((title, clean_url))
        except:
            formatted_links.append(("Attached Resource", clean_url))
            
    return formatted_links

@app.template_filter('extract_images')
def extract_images_filter(text):
    if not text:
        return []
    # Regex hunts for ![alt text](image_url) and captures the alt and url
    return re.findall(r'!\[([^\]]*)\]\(([^)]+)\)', text)

@app.template_filter('remove_images')
def remove_images_filter(text):
    if not text:
        return ""
    # Replaces the markdown image string with an empty space, erasing it from the text
    return re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', '', text)

@app.template_filter('timeago')
def time_ago_filter(date_obj):
    """
    Takes a Python datetime object and returns a relative 'time ago' string.
    """
    # Safety check: if no date was provided, return nothing
    if not date_obj:
        return ""
    
    now = datetime.now()
    diff = now - date_obj
    seconds = diff.total_seconds()

    # Translate the seconds into readable chunks
    if seconds < 60:
        return "Just now"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif seconds < 86400:
        hours = int(seconds // 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif seconds < 604800: # 7 days
        days = int(seconds // 86400)
        return f"{days} day{'s' if days != 1 else ''} ago"
    else:
        # If it's older than a week, just show the actual date (e.g., "Jul 16, 2026")
        return date_obj.strftime("%b %d, %Y")