#!/usr/bin/env bash
set -euo pipefail

# --------------------------------------------
# WCC Backend Mentors Upload & Accept Script
# Loops through longterm_or_both_mentors.json,
# uploads each mentor, and accepts them.
# --------------------------------------------

# Default API configuration
API_BASE="${API_BASE:-https://wcc-backend-prod.fly.dev/api}"
API_KEY="${API_KEY:-}"
DRY_RUN="${DRY_RUN:-false}"

# Get the script directory and set JSON file path
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
JSON_FILE="${SCRIPT_DIR}/../mentor_json_outputs/longterm_or_both_mentors.json"

# Create temporary files for curl responses
TMP_RESPONSE=$(mktemp)
TMP_ACCEPT_RESPONSE=$(mktemp)

# Cleanup function
cleanup() {
    rm -f "$TMP_RESPONSE" "$TMP_ACCEPT_RESPONSE"
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

# Check if JSON file exists
if [ ! -f "$JSON_FILE" ]; then
    echo "❌ Error: JSON file not found: $JSON_FILE"
    exit 1
fi

echo "🚀 Starting WCC backend mentors upload & accept process..."
echo "📁 Reading mentors from: $JSON_FILE"
echo "🌐 API Base URL: $API_BASE"
if [ "$DRY_RUN" = "true" ]; then
    echo "🔍 DRY RUN MODE: No actual API calls will be made"
fi
echo ""

# Get total number of mentors
TOTAL_MENTORS=$(jq '. | length' "$JSON_FILE")
echo "📊 Found $TOTAL_MENTORS mentors to upload"
echo ""

# Counters for tracking progress
SUCCESS_COUNT=0
FAILED_COUNT=0
ACCEPTED_COUNT=0
ACCEPT_FAILED_COUNT=0

# Arrays to store results
declare -a CREATED_IDS
declare -a FAILED_MENTORS

# Loop through each mentor in the JSON file
for i in $(seq 0 $((TOTAL_MENTORS - 1))); do
    # Extract mentor data
    MENTOR_DATA=$(jq -c ".[$i]" "$JSON_FILE")
    MENTOR_NAME=$(echo "$MENTOR_DATA" | jq -r '.fullName')
    
    echo "➡️  [$((i + 1))/$TOTAL_MENTORS] Processing mentor: $MENTOR_NAME"
    
    if [ "$DRY_RUN" = "true" ]; then
        echo "    [DRY RUN] Would upload: $MENTOR_NAME"
        echo "    [DRY RUN] Data size: ${#MENTOR_DATA} bytes"
        echo "    [DRY RUN] Would accept mentor after creation"
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
        ACCEPTED_COUNT=$((ACCEPTED_COUNT + 1))
    else
        # Step 1: Upload the mentor (POST)
        HTTP_CODE=$(curl -s -w "%{http_code}" -o "$TMP_RESPONSE" \
            -X POST "${API_BASE}/platform/v1/mentors" \
            -H "accept: */*" \
            -H "X-API-KEY: ${API_KEY}" \
            -H "Content-Type: application/json" \
            -d "$MENTOR_DATA")
        
        # Check response for mentor creation
        if [ "$HTTP_CODE" -ge 200 ] && [ "$HTTP_CODE" -lt 300 ]; then
            # Extract the mentor ID from the response
            MENTOR_ID=$(jq -r '.id' "$TMP_RESPONSE" 2>/dev/null || echo "")
            
            if [ -n "$MENTOR_ID" ] && [ "$MENTOR_ID" != "null" ]; then
                echo "    ✅ Created mentor: $MENTOR_NAME (HTTP $HTTP_CODE, ID: $MENTOR_ID)"
                SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
                CREATED_IDS+=("$MENTOR_ID")
                
                # Step 2: Accept the mentor (PATCH)
                echo "    ⏳ Accepting mentor ID: $MENTOR_ID"
                ACCEPT_HTTP_CODE=$(curl -s -w "%{http_code}" -o "$TMP_ACCEPT_RESPONSE" \
                    -X PATCH "${API_BASE}/platform/v1/mentors/${MENTOR_ID}/accept" \
                    -H "accept: */*" \
                    -H "X-API-KEY: ${API_KEY}")
                
                # Check acceptance response
                if [ "$ACCEPT_HTTP_CODE" -ge 200 ] && [ "$ACCEPT_HTTP_CODE" -lt 300 ]; then
                    echo "    ✅ Accepted mentor: $MENTOR_NAME (HTTP $ACCEPT_HTTP_CODE)"
                    ACCEPTED_COUNT=$((ACCEPTED_COUNT + 1))
                else
                    echo "    ⚠️  Failed to accept $MENTOR_NAME (HTTP $ACCEPT_HTTP_CODE)"
                    echo "    Response: $(cat "$TMP_ACCEPT_RESPONSE")"
                    ACCEPT_FAILED_COUNT=$((ACCEPT_FAILED_COUNT + 1))
                fi
            else
                echo "    ⚠️  Created but couldn't extract ID for: $MENTOR_NAME"
                echo "    Response: $(cat "$TMP_RESPONSE")"
                ACCEPT_FAILED_COUNT=$((ACCEPT_FAILED_COUNT + 1))
            fi
        else
            echo "    ❌ Failed to create $MENTOR_NAME (HTTP $HTTP_CODE)"
            echo "    Response: $(cat "$TMP_RESPONSE")"
            FAILED_COUNT=$((FAILED_COUNT + 1))
            FAILED_MENTORS+=("$MENTOR_NAME")
        fi
    fi
    
    echo ""
    
    # Optional: Add a small delay to avoid overwhelming the server
    sleep 0.5
done

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📈 Upload & Accept Summary:"
echo "   ✅ Successfully created: $SUCCESS_COUNT"
echo "   ✅ Successfully accepted: $ACCEPTED_COUNT"
echo "   ⚠️  Accept failed: $ACCEPT_FAILED_COUNT"
echo "   ❌ Creation failed: $FAILED_COUNT"
echo "   📊 Total mentors: $TOTAL_MENTORS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Print failed mentors if any
if [ "$FAILED_COUNT" -gt 0 ]; then
    echo ""
    echo "⚠️  Failed to create the following mentors:"
    for mentor in "${FAILED_MENTORS[@]}"; do
        echo "   - $mentor"
    done
fi

# Print created IDs if in verbose mode
if [ "${VERBOSE:-false}" = "true" ] && [ ${#CREATED_IDS[@]} -gt 0 ]; then
    echo ""
    echo "📋 Created Mentor IDs:"
    for id in "${CREATED_IDS[@]}"; do
        echo "   - $id"
    done
fi

echo ""

# Exit with success if at least some mentors were successfully processed
if [ "$SUCCESS_COUNT" -gt 0 ] && [ "$ACCEPTED_COUNT" -gt 0 ]; then
    echo "🎉 Process completed! $ACCEPTED_COUNT mentors uploaded and accepted successfully!"
    exit 0
elif [ "$FAILED_COUNT" -eq "$TOTAL_MENTORS" ]; then
    echo "❌ All mentor uploads failed!"
    exit 1
else
    echo "⚠️  Process completed with some failures."
    exit 1
fi
