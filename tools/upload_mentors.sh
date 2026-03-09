#!/usr/bin/env bash
set -euo pipefail

# --------------------------------------------
# WCC Backend Mentors Upload Script
# Loops through mentors_data.json and uploads
# each mentor to the backend API using curl.
# --------------------------------------------

# Default API configuration
API_BASE="${API_BASE:-http://localhost:8080/api}"
API_KEY="${API_KEY:-test}"

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
JSON_FILE="${SCRIPT_DIR}/mentors_data.json"

# Check if jq is installed
if ! command -v jq &> /dev/null; then
    echo "❌ Error: jq is required but not installed."
    echo "   Please install jq: https://stedolan.github.io/jq/download/"
    exit 1
fi

# Check if JSON file exists
if [ ! -f "$JSON_FILE" ]; then
    echo "❌ Error: JSON file not found: $JSON_FILE"
    echo "   Please run convert_mentors_to_json.py first."
    exit 1
fi

echo "🚀 Starting WCC backend mentors upload..."
echo "📁 Reading mentors from: $JSON_FILE"
echo "🌐 API Base URL: $API_BASE"
echo ""

# Get total number of mentors
TOTAL_MENTORS=$(jq '. | length' "$JSON_FILE")
echo "📊 Found $TOTAL_MENTORS mentors to upload"
echo ""

# Counter for tracking progress
SUCCESS_COUNT=0
FAILED_COUNT=0

# Loop through each mentor in the JSON file
for i in $(seq 0 $((TOTAL_MENTORS - 1))); do
    # Extract mentor data
    MENTOR_DATA=$(jq -c ".[$i]" "$JSON_FILE")
    MENTOR_NAME=$(echo "$MENTOR_DATA" | jq -r '.fullName')
    
    echo "➡️  [$((i + 1))/$TOTAL_MENTORS] Uploading mentor: $MENTOR_NAME"
    
    # Make the curl request
    HTTP_CODE=$(curl -s -w "%{http_code}" -o /tmp/curl_response.txt \
        -X POST "${API_BASE}/platform/v1/mentors" \
        -H "accept: */*" \
        -H "X-API-KEY: ${API_KEY}" \
        -H "Content-Type: application/json" \
        -d "$MENTOR_DATA")
    
    # Check response
    if [ "$HTTP_CODE" -ge 200 ] && [ "$HTTP_CODE" -lt 300 ]; then
        echo "✅  Successfully uploaded $MENTOR_NAME (HTTP $HTTP_CODE)"
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    else
        echo "❌  Failed to upload $MENTOR_NAME (HTTP $HTTP_CODE)"
        echo "    Response: $(cat /tmp/curl_response.txt)"
        FAILED_COUNT=$((FAILED_COUNT + 1))
    fi
    
    echo ""
    
    # Optional: Add a small delay to avoid overwhelming the server
    # sleep 0.1
done

# Clean up
rm -f /tmp/curl_response.txt

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📈 Upload Summary:"
echo "   ✅ Successful: $SUCCESS_COUNT"
echo "   ❌ Failed: $FAILED_COUNT"
echo "   📊 Total: $TOTAL_MENTORS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Exit with error code if any uploads failed
if [ "$FAILED_COUNT" -gt 0 ]; then
    exit 1
fi

echo ""
echo "🎉 All mentors uploaded successfully!"
