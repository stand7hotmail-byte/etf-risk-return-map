# -*- coding: utf-8 -*-
"""
Script to build static blog pages from Markdown files with front matter.
"""
import json
import logging
import os
import shutil
from datetime import datetime
from pathlib import Path

import markdown
import yaml
from jinja2 import Environment, FileSystemLoader

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Configuration ---
CONTENT_DIR = Path("content/blog")
TEMPLATES_DIR = Path("templates/blog")
OUTPUT_DIR = Path("static/blog") # Static output for FastAPI serving
JINJA_ENV = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))

# Add a strftime filter for Jinja2
def strftime_filter(value, format="%Y-%m-%d"):
    if isinstance(value, datetime):
        return value.strftime(format)
    return value
JINJA_ENV.filters['strftime'] = strftime_filter


def parse_markdown_with_frontmatter(filepath: Path) -> dict:
    """
    Parses a Markdown file with YAML front matter.

    Args:
        filepath: The path to the Markdown file.

    Returns:
        A dictionary containing front matter metadata and the rendered HTML content.
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    parts = content.split('---', 2)
    if len(parts) < 3:
        raise ValueError(f"Markdown file {filepath} is missing front matter.")

    metadata = yaml.safe_load(parts[1])
    markdown_content = parts[2]
    
    html_content = markdown.markdown(markdown_content)
    
    # Ensure date is a datetime object
    if 'date' in metadata and isinstance(metadata['date'], datetime):
        pass # Already a datetime object from yaml.safe_load
    elif 'date' in metadata and isinstance(metadata['date'], str):
        try:
            metadata['date'] = datetime.strptime(metadata['date'], "%Y-%m-%d")
        except ValueError:
            logger.warning(f"Invalid date format in {filepath}. Expected YYYY-MM-DD. Using current date.")
            metadata['date'] = datetime.now()
    else:
        metadata['date'] = datetime.now() # Default if no date is provided
        
    return {**metadata, 'content': html_content, 'filepath': filepath}


def build_blog():
    """
    Builds static HTML blog pages from Markdown sources.
    Generates an index page and individual post pages.
    """
    logger.info("Starting blog build process...")

    # Clear previous output
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
        logger.info(f"Cleared existing output directory: {OUTPUT_DIR}")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    posts_metadata = []
    
    # Process individual blog posts
    for md_file in CONTENT_DIR.glob("*.md"):
        try:
            post_data = parse_markdown_with_frontmatter(md_file)
            posts_metadata.append(post_data)

            # Render individual post page
            post_template = JINJA_ENV.get_template('post.html')
            output_html = post_template.render(post=post_data)
            
            output_path = OUTPUT_DIR / f"{post_data['slug']}.html"
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(output_html)
            logger.info(f"Generated post: {output_path}")

        except Exception as e:
            logger.error(f"Error processing {md_file}: {e}")
            
    # Sort posts by date for the index page (newest first)
    posts_metadata.sort(key=lambda x: x.get('date', datetime.min), reverse=True)
    
    # Render blog index page
    index_template = JINJA_ENV.get_template('index.html')
    output_html = index_template.render(posts=posts_metadata, title="すべての記事")
    
    index_output_path = OUTPUT_DIR / "index.html"
    with open(index_output_path, 'w', encoding='utf-8') as f:
        f.write(output_html)
    logger.info(f"Generated blog index: {index_output_path}")
    
    logger.info("Blog build process completed.")


if __name__ == "__main__":
    build_blog()
