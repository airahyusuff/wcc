#!/usr/bin/env python3
"""
WCC Backend Mentor Pictures Upload Script

Uploads profile pictures for mentors from assets/images/mentors directory
"""

import json
import os
import sys
import time
import re
from pathlib import Path
import requests


def normalize_name(name):
    """Convert mentor name to expected filename format"""
    # Convert to lowercase, replace spaces with underscores, remove special chars
    normalized = name.lower().replace(' ', '_')
    # Remove or replace special characters
    normalized = re.sub(r'[^a-z0-9_-]', '_', normalized)
    return normalized


def find_image_file(images_dir, mentor_name):
    """Find the image file for a given mentor name"""
    normalized = normalize_name(mentor_name)
    
    # Try different extensions
    for ext in ['.jpeg', '.jpg', '.png']:
        image_path = images_dir / f"{normalized}{ext}"
        if image_path.exists():
            return image_path
    
    return None


def detect_content_type(image_path):
    """Detect content type based on file extension"""
    suffix = image_path.suffix.lower()
    if suffix in ['.jpg', '.jpeg']:
        return 'image/jpeg'
    elif suffix == '.png':
        return 'image/png'
    else:
        return 'image/jpeg'  # default


def main():
    # Configuration from environment variables
    api_base = os.getenv('API_BASE', 'https://wcc-backend-prod.fly.dev/api')
    api_key = os.getenv('API_KEY', '')
    dry_run = os.getenv('DRY_RUN', 'false').lower() == 'true'
    mentor_ids_file = os.getenv('MENTOR_IDS_FILE', '')
    
    # Setup paths
    script_dir = Path(__file__).parent
    images_dir = script_dir / '..' / 'assets' / 'images' / 'mentors'
    json_file = script_dir / '..' / 'mentor_json_outputs' / 'longterm_or_both_mentors.json'
    
    # Validate API key
    if not api_key:
        print("❌ Error: API_KEY environment variable is not set.")
        print("   Please set it before running this script:")
        print("   export API_KEY='your-api-key-here'")
        sys.exit(1)
    
    # Validate images directory
    if not images_dir.exists():
        print(f"❌ Error: Images directory not found: {images_dir}")
        sys.exit(1)
    
    # Validate JSON file
    if not json_file.exists():
        print(f"❌ Error: JSON file not found: {json_file}")
        sys.exit(1)
    
    print("🚀 Starting WCC backend mentor pictures upload...")
    print(f"📁 Images directory: {images_dir}")
    print(f"📁 Mentors JSON: {json_file}")
    print(f"🌐 API Base URL: {api_base}")
    if dry_run:
        print("🔍 DRY RUN MODE: No actual API calls will be made")
    print()
    
    # Counters
    success_count = 0
    failed_count = 0
    skipped_count = 0
    
    uploaded_mentors = []
    failed_mentors = []
    skipped_mentors = []
    
    # Headers for API requests
    headers = {
        'accept': '*/*',
        'X-API-KEY': api_key
    }
    
    # Check if mentor IDs file is provided
    if mentor_ids_file and Path(mentor_ids_file).exists():
        print(f"📋 Reading mentor IDs from: {mentor_ids_file}")
        print()
        
        with open(mentor_ids_file, 'r') as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                
                # Parse line: mentor_name|mentor_id
                if '|' not in line:
                    print(f"⚠️  Skipping invalid line: {line}")
                    continue
                
                mentor_name, mentor_id = line.split('|', 1)
                mentor_name = mentor_name.strip()
                mentor_id = mentor_id.strip()
                
                print(f"➡️  Processing mentor: {mentor_name} (ID: {mentor_id})")
                
                # Find the image file
                image_file = find_image_file(images_dir, mentor_name)
                if image_file:
                    print(f"    📸 Found image: {image_file.name}")
                    
                    if dry_run:
                        print(f"    [DRY RUN] Would upload image for {mentor_name} (ID: {mentor_id})")
                        success_count += 1
                        uploaded_mentors.append(mentor_name)
                    else:
                        try:
                            # Prepare the file upload
                            content_type = detect_content_type(image_file)
                            
                            with open(image_file, 'rb') as img:
                                files = {
                                    'file': (image_file.name, img, content_type)
                                }
                                
                                # Upload the image
                                upload_url = f"{api_base}/platform/v1/resources/member-profile-picture?memberId={mentor_id}"
                                response = requests.post(upload_url, headers=headers, files=files)
                                
                                if response.status_code >= 200 and response.status_code < 300:
                                    print(f"    ✅ Successfully uploaded picture for {mentor_name} (HTTP {response.status_code})")
                                    success_count += 1
                                    uploaded_mentors.append(mentor_name)
                                else:
                                    print(f"    ❌ Failed to upload picture for {mentor_name} (HTTP {response.status_code})")
                                    print(f"    Response: {response.text[:200]}")
                                    failed_count += 1
                                    failed_mentors.append(mentor_name)
                        
                        except Exception as e:
                            print(f"    ❌ Error uploading picture for {mentor_name}: {str(e)}")
                            failed_count += 1
                            failed_mentors.append(mentor_name)
                else:
                    print(f"    ⚠️  No image file found for: {mentor_name}")
                    skipped_count += 1
                    skipped_mentors.append(mentor_name)
                
                print()
                
                # Small delay to avoid overwhelming the server
                if not dry_run:
                    time.sleep(0.3)
    else:
        print("⚠️  No MENTOR_IDS_FILE provided or file not found.")
        print()
        print("This script requires a file mapping mentor names to their IDs.")
        print("Please provide the file path using the MENTOR_IDS_FILE environment variable.")
        print()
        print("Expected format (one per line):")
        print("  Mentor Full Name|mentor_id_from_api")
        print()
        print("Example:")
        print("  Rajani Rao|abc123-def456")
        print("  Eleonora Belova|ghi789-jkl012")
        print()
        print("You can generate this file by:")
        print("  1. Running the upload_and_accept_mentors script first")
        print("  2. Capturing the mentor IDs from the API responses")
        print("  3. Creating a mapping file")
        print()
        print("Alternative: List all available image files to help with manual mapping")
        print()
        print(f"Available image files in {images_dir}:")
        image_files = sorted(images_dir.glob('*'))[:20]
        for img in image_files:
            print(f"  {img.name}")
        total_images = len(list(images_dir.glob('*')))
        if total_images > 20:
            print(f"... and {total_images - 20} more")
        print()
        sys.exit(1)
    
    # Print summary
    print("━" * 50)
    print("📈 Upload Summary:")
    print(f"   ✅ Successfully uploaded: {success_count}")
    print(f"   ❌ Failed: {failed_count}")
    print(f"   ⚠️  Skipped (no image): {skipped_count}")
    print(f"   📊 Total processed: {success_count + failed_count + skipped_count}")
    print("━" * 50)
    
    # Print failed mentors if any
    if failed_mentors:
        print()
        print("⚠️  Failed to upload pictures for the following mentors:")
        for mentor in failed_mentors:
            print(f"   - {mentor}")
    
    # Print skipped mentors if any
    if skipped_mentors:
        print()
        print("⚠️  No image files found for the following mentors:")
        for mentor in skipped_mentors:
            print(f"   - {mentor}")
    
    print()
    
    # Exit with appropriate code
    if success_count > 0:
        print(f"🎉 Process completed! {success_count} pictures uploaded successfully!")
        sys.exit(0)
    elif failed_count > 0:
        print("❌ All uploads failed!")
        sys.exit(1)
    else:
        print("⚠️  No pictures were uploaded.")
        sys.exit(1)


if __name__ == '__main__':
    main()
