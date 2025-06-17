# Copyright (c) 2025 Lucid. All rights reserved.
# MRSS (Media RSS) Feed Generator
# This script generates MRSS feeds for BrightSign® players by scanning a base folder
# and creating both a main feed and individual feeds for each subdirectory

import datetime
import os
import hashlib
import xml.etree.ElementTree as ET
from xml.dom import minidom
import argparse

# Supported video file extensions that will be included in the RSS feed
MEDIA_EXTENSIONS = ['.mp4', '.mov', '.avi', '.mkv']

# Base URL for the web server where media files are hosted
BASE_URL = 'http://raspberrypi.local/'

def get_md5(file_path):
    """
    Calculate MD5 hash of a file for cache-busting and unique identification.
    
    Args:
        file_path (str): Path to the file to hash
        
    Returns:
        str: MD5 hash digest as hexadecimal string
    """
    hash_md5 = hashlib.md5()
    with open(file_path, 'rb') as f:
        # Read file in chunks to handle large files efficiently
        for chunk in iter(lambda: f.read(4096), b''):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def prettify_xml(elem):
    """
    Convert XML element to a nicely formatted string with proper indentation.
    
    Args:
        elem: XML element to format
        
    Returns:
        str: Formatted XML string
    """
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="    ")

def generate_mrss_for_folder(folder_path, base_url, output_file, url_prefix=""):
    """
    Generate an MRSS feed for all video files in a specified folder.
    
    Args:
        folder_path (str): Path to the folder containing media files
        base_url (str): Base URL for the web server
        output_file (str): Path where the generated XML file should be saved
        url_prefix (str): Optional URL prefix for subdirectories (e.g., "subfolder/")
    """
    # Create the root RSS element with Media RSS namespace
    rss = ET.Element('rss', {
        'xmlns:media': 'http://search.yahoo.com/mrss/',
        'version': '2.0'
    })
    
    # Create the channel element (required for RSS feeds)
    channel = ET.SubElement(rss, 'channel')
    
    # Get folder name for the feed title
    folder_name = os.path.basename(folder_path.rstrip(os.sep))
    
    # Add standard RSS channel elements
    ET.SubElement(channel, 'title').text = f'MB Media{f" - {folder_name}" if url_prefix else ""}'
    ET.SubElement(channel, 'link').text = ''
    ET.SubElement(channel, 'description').text = f'MB{f" - {folder_name}" if url_prefix else ""}'
    ET.SubElement(channel, 'generator').text = 'Server RSS Generator'

    # Iterate through all files in the folder
    for filename in os.listdir(folder_path):
        # Skip hidden files (starting with .)
        if filename.startswith('.'):
            continue
            
        file_path = os.path.join(folder_path, filename)
        
        # Skip directories, only process files
        if not os.path.isfile(file_path):
            continue
            
        # Check if file has a supported video extension
        ext = os.path.splitext(filename)[1].lower()
        if ext not in MEDIA_EXTENSIONS:
            continue
            
        # Extract title from filename (remove extension)
        title = os.path.splitext(filename)[0]
        
        # Generate MD5 hash for cache-busting and unique identification
        md5_hash = get_md5(file_path)
        
        # Create the media URL with MD5 parameter for cache control
        link = f"{base_url}{url_prefix}{filename}?md5={md5_hash}"
        
        # Create RSS item for this media file
        item = ET.SubElement(channel, 'item')
        ET.SubElement(item, 'title').text = title
        ET.SubElement(item, 'pubDate').text = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        ET.SubElement(item, 'link').text = link
        ET.SubElement(item, 'description').text = link
        ET.SubElement(item, 'medium').text = 'video'
        ET.SubElement(item, 'guid').text = f"{title}-{md5_hash}"
        
        # Add Media RSS content element with video metadata
        ET.SubElement(item, 'media:content', {
            'url': link,
            'type': 'video/mp4',
            'medium': 'video'
        })
    
    # Format the XML and write to output file
    xml_str = prettify_xml(rss)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(xml_str)
    print(f"Generated {output_file}")

def main():
    """
    Main function that handles command line arguments and orchestrates RSS generation.
    Generates a main RSS feed for the root folder and individual feeds for each subdirectory.
    """
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(description='Generate MRSS feed for media files in a folder.')
    parser.add_argument('--folder', type=str, default='/var/www/html', 
                       help='Path to the folder containing media files')
    args = parser.parse_args()
    
    # Get folder path from arguments
    FOLDER_PATH = args.folder
    OUTPUT_FILE = os.path.join(FOLDER_PATH, 'mrss.xml')

    # Generate MRSS for the main folder (root level)
    generate_mrss_for_folder(FOLDER_PATH, BASE_URL, OUTPUT_FILE)

    # Generate MRSS for each subdirectory
    for filename in os.listdir(FOLDER_PATH):
        # Skip hidden files
        if filename.startswith('.'):
            continue
            
        file_path = os.path.join(FOLDER_PATH, filename)
        
        # Only process directories
        if os.path.isdir(file_path):
            subfolder = filename
            subfolder_path = file_path
            # Create output filename based on subfolder name
            subfolder_output_file = os.path.join(FOLDER_PATH, f"{subfolder}.xml")
            # Add subfolder prefix to URLs for proper path construction
            url_prefix = f"{subfolder}/"
            generate_mrss_for_folder(subfolder_path, BASE_URL, subfolder_output_file, url_prefix=url_prefix)

if __name__ == '__main__':
    main()
