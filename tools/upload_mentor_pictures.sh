#!/usr/bin/env bash
set -euo pipefail

# --------------------------------------------
# WCC Backend Mentor Pictures Upload Script
# Uploads profile pictures for mentors from
# assets/images/mentors directory
# --------------------------------------------

# Default API configuration
API_BASE="${API_BASE:-https://wcc-backend-prod.fly.dev/api}"
API_KEY="${API_KEY:-}"
DRY_RUN="${DRY_RUN:-false}"
MENTOR_IDS_FILE="${MENTOR_IDS_FILE:-}"

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
IMAGES_DIR="${SCRIPT_DIR}/../assets/images/mentors"
JSON_FILE="${SCRIPT_DIR}/../mentor_json_outputs/longterm_or_both_mentors.json"

# Create temporary file for curl responses
TMP_RESPONSE=$(mktemp)

# Cleanup function
cleanup() {
    rm -f "$TMP_RESPONSE"
}
trap cleanup EXIT

# Check if jq is installed
if ! command -v jq &> /dev/null; then
    echo "❌ Error: jq is required but not installed."
    echo "   Please install jq: https://stedolan.github.io/jq/download/"
    exit 1
fi

# Check if API_KEY is set
if [ -z "$API_KEY" ]; then
    echo "❌ Error: API_KEY environment variable is not set."
    echo "   Please set it before running this script:"
    echo "   export API_KEY='your-api-key-here'"
    exit 1
fi

# Check if images directory exists
if [ ! -d "$IMAGES_DIR" ]; then
    echo "❌ Error: Images directory not found: $IMAGES_DIR"
    exit 1
fi

# Check if JSON file exists
if [ ! -f "$JSON_FILE" ]; then
    echo "❌ Error: JSON file not found: $JSON_FILE"
    exit 1
fi

echo "🚀 Starting WCC backend mentor pictures upload..."
echo "📁 Images directory: $IMAGES_DIR"
echo "📁 Mentors JSON: $JSON_FILE"
echo "🌐 API Base URL: $API_BASE"
if [ "$DRY_RUN" = "true" ]; then
    echo "🔍 DRY RUN MODE: No actual API calls will be made"
fi
echo ""

# Function to normalize a name to filename format
# Produce candidate basenames for a mentor name (preserve unicode, ascii fallback)
normalize_name_candidates() {
    local name="$1"
    local lower underscored ascii

    lower=$(echo "$name" | tr '[:upper:]' '[:lower:]')
    underscored=$(echo "$lower" | tr ' ' '_')
    echo "$underscored"

    ascii=$(echo "$underscored" | sed 's/[^a-z0-9_-]/_/g')
    if [ "$ascii" != "$underscored" ]; then
        echo "$ascii"
    fi
}

# Try each candidate basename with common extensions
find_image_file() {
    local mentor_name="$1"
    local cand
    while IFS= read -r cand; do
        if [ -f "${IMAGES_DIR}/${cand}.jpeg" ]; then
            echo "${IMAGES_DIR}/${cand}.jpeg"
            return 0
        fi
        if [ -f "${IMAGES_DIR}/${cand}.jpg" ]; then
            echo "${IMAGES_DIR}/${cand}.jpg"
            return 0
        fi
        if [ -f "${IMAGES_DIR}/${cand}.png" ]; then
            echo "${IMAGES_DIR}/${cand}.png"
            return 0
        fi
    done < <(normalize_name_candidates "$mentor_name")
    return 1
}

# Counters
SUCCESS_COUNT=0
FAILED_COUNT=0
SKIPPED_COUNT=0

# Arrays to store results
declare -a UPLOADED_MENTORS
declare -a FAILED_MENTORS
declare -a SKIPPED_MENTORS

# If MENTOR_IDS_FILE is provided, read mentor IDs from file
# Expected format: mentor_name|mentor_id (one per line)
if [ -n "$MENTOR_IDS_FILE" ] && [ -f "$MENTOR_IDS_FILE" ]; then
    echo "📋 Reading mentor IDs from: $MENTOR_IDS_FILE"
    echo ""
    
    while IFS='|' read -r mentor_name mentor_id; do
        # Skip empty lines and comments
        [[ -z "$mentor_name" || "$mentor_name" =~ ^# ]] && continue
        
        echo "➡️  Processing mentor: $mentor_name (ID: $mentor_id)"
        
        # Find the image file
        if image_file=$(find_image_file "$mentor_name"); then
            echo "    📸 Found image: $(basename "$image_file")"
            
            if [ "$DRY_RUN" = "true" ]; then
                echo "    [DRY RUN] Would upload image for $mentor_name (ID: $mentor_id)"
                SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
                UPLOADED_MENTORS+=("$mentor_name")
            else
                # Detect content type
                content_type="image/jpeg"
                if [[ "$image_file" == *.png ]]; then
                    content_type="image/png"
                fi
                
                # Upload the image
                HTTP_CODE=$(curl -s -w "%{http_code}" -o "$TMP_RESPONSE" \
                    -X POST "${API_BASE}/platform/v1/resources/member-profile-picture?memberId=${mentor_id}" \
                    -H "accept: */*" \
                    -H "X-API-KEY: ${API_KEY}" \
                    -F "file=@${image_file};type=${content_type}")
                
                # Check response
                if [ "$HTTP_CODE" -ge 200 ] && [ "$HTTP_CODE" -lt 300 ]; then
                    echo "    ✅ Successfully uploaded picture for $mentor_name (HTTP $HTTP_CODE)"
                    SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
                    UPLOADED_MENTORS+=("$mentor_name")
                else
                    echo "    ❌ Failed to upload picture for $mentor_name (HTTP $HTTP_CODE)"
                    echo "    Response: $(cat "$TMP_RESPONSE")"
                    FAILED_COUNT=$((FAILED_COUNT + 1))
                    FAILED_MENTORS+=("$mentor_name")
                fi
            fi
        else
            echo "    ⚠️  No image file found for: $mentor_name"
            SKIPPED_COUNT=$((SKIPPED_COUNT + 1))
            SKIPPED_MENTORS+=("$mentor_name")
        fi
        
        echo ""
        
        # Small delay to avoid overwhelming the server
        [ "$DRY_RUN" != "true" ] && sleep 0.3
    done < "$MENTOR_IDS_FILE"
else
    echo "⚠️  No MENTOR_IDS_FILE provided or file not found."
    echo ""
    echo "This script requires a file mapping mentor names to their IDs."
    echo "Please provide the file path using the MENTOR_IDS_FILE environment variable."
    echo ""
    echo "Expected format (one per line):"
    echo "  Mentor Full Name|mentor_id_from_api"
    echo ""
    echo "Example:"
    echo "  Rajani Rao|abc123-def456"
    echo "  Eleonora Belova|ghi789-jkl012"
    echo ""
    echo "You can generate this file by:"
    echo "  1. Running the upload_and_accept_mentors script first"
    echo "  2. Capturing the mentor IDs from the API responses"
    echo "  3. Creating a mapping file"
    echo ""
    echo "Alternative: List all available image files to help with manual mapping"
    echo ""
    echo "Available image files in ${IMAGES_DIR}:"
    ls -1 "$IMAGES_DIR" | head -20
    [ $(ls -1 "$IMAGES_DIR" | wc -l) -gt 20 ] && echo "... and $(($(ls -1 "$IMAGES_DIR" | wc -l) - 20)) more"
    echo ""
    exit 1
fi

# Print summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📈 Upload Summary:"
echo "   ✅ Successfully uploaded: $SUCCESS_COUNT"
echo "   ❌ Failed: $FAILED_COUNT"
echo "   ⚠️  Skipped (no image): $SKIPPED_COUNT"
echo "   📊 Total processed: $((SUCCESS_COUNT + FAILED_COUNT + SKIPPED_COUNT))"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Print failed mentors if any
if [ "$FAILED_COUNT" -gt 0 ]; then
    echo ""
    echo "⚠️  Failed to upload pictures for the following mentors:"
    for mentor in "${FAILED_MENTORS[@]}"; do
        echo "   - $mentor"
    done
fi

# Print skipped mentors if any
if [ "$SKIPPED_COUNT" -gt 0 ]; then
    echo ""
    echo "⚠️  No image files found for the following mentors:"
    for mentor in "${SKIPPED_MENTORS[@]}"; do
        echo "   - $mentor"
    done
fi

echo ""

# Exit with appropriate code
if [ "$SUCCESS_COUNT" -gt 0 ]; then
    echo "🎉 Process completed! $SUCCESS_COUNT pictures uploaded successfully!"
    exit 0
elif [ "$FAILED_COUNT" -gt 0 ]; then
    echo "❌ All uploads failed!"
    exit 1
else
    echo "⚠️  No pictures were uploaded."
    exit 1
fi
