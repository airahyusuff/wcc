#!/usr/bin/env bash
set -euo pipefail

# --------------------------------------------
# Generate Mentor IDs Mapping Script
# Parses mentor_ids.log to create mentor_ids_mapping.txt
# --------------------------------------------

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
LOG_FILE="${MENTOR_IDS_LOG:-${SCRIPT_DIR}/mentor_ids.log}"
OUTPUT_FILE="${SCRIPT_DIR}/mentor_ids_mapping.txt"
JSON_FILE="${SCRIPT_DIR}/../mentor_json_outputs/longterm_or_both_mentors.json"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "🚀 Mentor IDs Mapping Generator"
echo ""

# Function to show usage
show_usage() {
    echo "Usage:"
    echo "  $0 [OPTIONS]"
    echo ""
    echo "This script generates mentor_ids_mapping.txt from mentor_ids.log"
    echo ""
    echo "Options:"
    echo "  --template    Generate a template file with FILL_IN_ID_HERE placeholders"
    echo "  --log FILE    Specify log file path (default: tools/mentor_ids.log)"
    echo "  --help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  # Generate from log file:"
    echo "  $0"
    echo ""
    echo "  # Generate template:"
    echo "  $0 --template"
    echo ""
    echo "  # Use custom log file:"
    echo "  MENTOR_IDS_LOG=/path/to/mentor_ids.log $0"
    echo ""
}

# Function to generate template
generate_template() {
    echo "📝 Generating template mapping file..."
    
    if [ ! -f "$JSON_FILE" ]; then
        echo -e "${RED}❌ Error: JSON file not found: $JSON_FILE${NC}"
        exit 1
    fi
    
    if ! command -v jq &> /dev/null; then
        echo -e "${RED}❌ Error: jq is required but not installed.${NC}"
        echo "   Please install jq: https://stedolan.github.io/jq/download/"
        exit 1
    fi
    
    # Create the template file
    {
        echo "# Mentor Name to ID Mapping Template"
        echo "# Format: Mentor Full Name|mentor_id"
        echo "# Please fill in the mentor IDs after running upload_and_accept_mentors script"
        echo ""
        jq -r '.[] | .fullName + "|FILL_IN_ID_HERE"' "$JSON_FILE"
    } > "$OUTPUT_FILE"
    
    MENTOR_COUNT=$(jq '. | length' "$JSON_FILE")
    echo -e "${GREEN}✅ Template file created: $OUTPUT_FILE${NC}"
    echo "   Total mentors: $MENTOR_COUNT"
    echo ""
    echo "Next steps:"
    echo "  1. Run the upload_and_accept_mentors script and save output:"
    echo "     ./tools/upload_and_accept_mentors.sh | tee tools/mentor_ids.log"
    echo "  2. Generate mapping from log:"
    echo "     ./tools/generate_mentor_ids_mapping.sh"
    echo "  3. Use the mapping file with upload_mentor_pictures script"
}

# Function to parse log file and generate mapping
generate_from_log() {
    echo "📋 Parsing mentor IDs from log file: $LOG_FILE"
    echo ""
    
    if [ ! -f "$LOG_FILE" ]; then
        echo -e "${YELLOW}⚠️  Warning: Log file not found: $LOG_FILE${NC}"
        echo ""
        echo "The log file should contain output from upload_and_accept_mentors script."
        echo ""
        echo "To generate the log file, run:"
        echo "  ./tools/upload_and_accept_mentors.sh | tee tools/mentor_ids.log"
        echo ""
        echo "Or generate a template instead:"
        echo "  $0 --template"
        echo ""
        exit 1
    fi
    
    # Create temporary file for extracted data
    TMP_FILE=$(mktemp)
    
    # Parse log file for lines like:
    # ✅ Created mentor: Rajani Rao (HTTP 201, ID: abc123-def456)
    # Extract: Rajani Rao|abc123-def456
    
    grep "✅ Created mentor:" "$LOG_FILE" | \
        sed -E 's/.*Created mentor: ([^(]+) \(HTTP [0-9]+, ID: ([^)]+)\)/\1|\2/' | \
        sed 's/ |/|/' > "$TMP_FILE"
    
    # Count entries found
    ENTRY_COUNT=$(wc -l < "$TMP_FILE")
    
    if [ "$ENTRY_COUNT" -eq 0 ]; then
        echo -e "${YELLOW}⚠️  No mentor IDs found in log file${NC}"
        echo ""
        echo "Expected format in log file:"
        echo "  ✅ Created mentor: Mentor Name (HTTP 201, ID: mentor-id-here)"
        echo ""
        echo "Please verify that:"
        echo "  1. The log file contains output from upload_and_accept_mentors script"
        echo "  2. Mentors were successfully created (look for ✅ Created mentor: lines)"
        echo ""
        rm -f "$TMP_FILE"
        exit 1
    fi
    
    # Create the mapping file
    {
        echo "# Mentor Name to ID Mapping"
        echo "# Format: Mentor Full Name|mentor_id"
        echo "# Generated from: $LOG_FILE"
        echo "# Generated at: $(date '+%Y-%m-%d %H:%M:%S')"
        echo ""
        cat "$TMP_FILE"
    } > "$OUTPUT_FILE"
    
    # Clean up
    rm -f "$TMP_FILE"
    
    echo -e "${GREEN}✅ Mapping file created: $OUTPUT_FILE${NC}"
    echo "   Entries found: $ENTRY_COUNT"
    echo ""
    
    # Show first few entries
    echo "First entries:"
    head -n 10 "$OUTPUT_FILE" | tail -n 5
    if [ "$ENTRY_COUNT" -gt 5 ]; then
        echo "..."
    fi
    echo ""
    
    echo "You can now use this mapping file:"
    echo "  export MENTOR_IDS_FILE='$OUTPUT_FILE'"
    echo "  ./tools/upload_mentor_pictures.sh"
}

# Parse command line arguments
GENERATE_TEMPLATE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --template)
            GENERATE_TEMPLATE=true
            shift
            ;;
        --log)
            LOG_FILE="$2"
            shift 2
            ;;
        --help|-h)
            show_usage
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo ""
            show_usage
            exit 1
            ;;
    esac
done

# Execute based on mode
if [ "$GENERATE_TEMPLATE" = true ]; then
    generate_template
else
    generate_from_log
fi
