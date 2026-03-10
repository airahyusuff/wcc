#!/usr/bin/env python3
"""
WCC Backend Mentors Upload & Accept Script

Loops through longterm_or_both_mentors.json, uploads each mentor,
and accepts them using the backend API.
"""

import json
import os
import sys
import time
import requests
from pathlib import Path


def main():
    # Configuration from environment variables
    api_base = os.getenv('API_BASE', 'https://wcc-backend-prod.fly.dev/api')
    api_key = os.getenv('API_KEY', '')
    dry_run = os.getenv('DRY_RUN', 'false').lower() == 'true'
    verbose = os.getenv('VERBOSE', 'false').lower() == 'true'
    
    # Setup paths
    script_dir = Path(__file__).parent
    json_file = script_dir / '..' / 'mentor_json_outputs' / 'longterm_or_both_mentors.json'
    
    # Validate API key
    if not api_key:
        print("❌ Error: API_KEY environment variable is not set.")
        print("   Please set it before running this script:")
        print("   export API_KEY='your-api-key-here'")
        sys.exit(1)
    
    # Validate JSON file exists
    if not json_file.exists():
        print(f"❌ Error: JSON file not found: {json_file}")
        sys.exit(1)
    
    # Load mentors data
    with open(json_file, 'r') as f:
        mentors = json.load(f)
    
    print("🚀 Starting WCC backend mentors upload & accept process...")
    print(f"📁 Reading mentors from: {json_file}")
    print(f"🌐 API Base URL: {api_base}")
    if dry_run:
        print("🔍 DRY RUN MODE: No actual API calls will be made")
    print()
    
    total_mentors = len(mentors)
    print(f"📊 Found {total_mentors} mentors to upload")
    print()
    
    # Counters
    success_count = 0
    failed_count = 0
    accepted_count = 0
    accept_failed_count = 0
    
    created_ids = []
    failed_mentors = []
    
    # Headers for API requests
    headers = {
        'accept': '*/*',
        'X-API-KEY': api_key,
        'Content-Type': 'application/json'
    }
    
    # Process each mentor
    for i, mentor in enumerate(mentors, 1):
        mentor_name = mentor.get('fullName', 'Unknown')
        print(f"➡️  [{i}/{total_mentors}] Processing mentor: {mentor_name}")
        
        if dry_run:
            print(f"    [DRY RUN] Would upload: {mentor_name}")
            print(f"    [DRY RUN] Data size: {len(json.dumps(mentor))} bytes")
            print(f"    [DRY RUN] Would accept mentor after creation")
            success_count += 1
            accepted_count += 1
        else:
            try:
                # Step 1: Create mentor (POST)
                create_url = f"{api_base}/platform/v1/mentors"
                response = requests.post(create_url, headers=headers, json=mentor)
                
                if response.status_code >= 200 and response.status_code < 300:
                    try:
                        response_data = response.json()
                        mentor_id = response_data.get('id')
                        
                        if mentor_id:
                            print(f"    ✅ Created mentor: {mentor_name} (HTTP {response.status_code}, ID: {mentor_id})")
                            success_count += 1
                            created_ids.append(mentor_id)
                            
                            # Step 2: Accept mentor (PATCH)
                            print(f"    ⏳ Accepting mentor ID: {mentor_id}")
                            accept_url = f"{api_base}/platform/v1/mentors/{mentor_id}/accept"
                            accept_response = requests.patch(accept_url, headers=headers)
                            
                            if accept_response.status_code >= 200 and accept_response.status_code < 300:
                                print(f"    ✅ Accepted mentor: {mentor_name} (HTTP {accept_response.status_code})")
                                accepted_count += 1
                            else:
                                print(f"    ⚠️  Failed to accept {mentor_name} (HTTP {accept_response.status_code})")
                                print(f"    Response: {accept_response.text[:200]}")
                                accept_failed_count += 1
                        else:
                            print(f"    ⚠️  Created but couldn't extract ID for: {mentor_name}")
                            print(f"    Response: {response.text[:200]}")
                            accept_failed_count += 1
                    except json.JSONDecodeError:
                        print(f"    ⚠️  Created but response is not valid JSON for: {mentor_name}")
                        accept_failed_count += 1
                else:
                    print(f"    ❌ Failed to create {mentor_name} (HTTP {response.status_code})")
                    print(f"    Response: {response.text[:200]}")
                    failed_count += 1
                    failed_mentors.append(mentor_name)
                    
            except requests.exceptions.RequestException as e:
                print(f"    ❌ Network error for {mentor_name}: {str(e)}")
                failed_count += 1
                failed_mentors.append(mentor_name)
        
        print()
        
        # Small delay to avoid overwhelming the server
        if not dry_run:
            time.sleep(0.5)
    
    # Print summary
    print("━" * 50)
    print("📈 Upload & Accept Summary:")
    print(f"   ✅ Successfully created: {success_count}")
    print(f"   ✅ Successfully accepted: {accepted_count}")
    print(f"   ⚠️  Accept failed: {accept_failed_count}")
    print(f"   ❌ Creation failed: {failed_count}")
    print(f"   📊 Total mentors: {total_mentors}")
    print("━" * 50)
    
    # Print failed mentors if any
    if failed_mentors:
        print()
        print("⚠️  Failed to create the following mentors:")
        for mentor in failed_mentors:
            print(f"   - {mentor}")
    
    # Print created IDs in verbose mode
    if verbose and created_ids:
        print()
        print("📋 Created Mentor IDs:")
        for mentor_id in created_ids:
            print(f"   - {mentor_id}")
    
    print()
    
    # Exit with appropriate code
    if success_count > 0 and accepted_count > 0:
        print(f"🎉 Process completed! {accepted_count} mentors uploaded and accepted successfully!")
        sys.exit(0)
    elif failed_count == total_mentors:
        print("❌ All mentor uploads failed!")
        sys.exit(1)
    else:
        print("⚠️  Process completed with some failures.")
        sys.exit(1)


if __name__ == '__main__':
    main()
