# Usage Example: Mentors YAML to JSON Conversion and Upload

This document provides a step-by-step example of how to use the mentors conversion and upload scripts.

## Scenario

You have mentor data in `_data/mentors.yml` and want to:
1. Convert it to JSON format compatible with wcc-backend API
2. Upload all mentors to the backend API

## Step-by-Step Guide

### Prerequisites

Ensure you have the required tools installed:

```bash
# Check Python 3
python3 --version

# Check jq (JSON processor)
jq --version

# Install PyYAML if needed
pip install pyyaml
```

### Step 1: Convert YAML to JSON

Navigate to the tools directory and run the conversion script:

```bash
cd tools
python3 convert_mentors_to_json.py
```

**Expected Output:**
```
Reading mentors from: /home/runner/work/wcc/wcc/_data/mentors.yml
Found 46 mentors in YAML file
Converted 46 mentors to JSON format
Skipped 0 disabled mentors
JSON data written to: /home/runner/work/wcc/wcc/tools/mentors_data.json

Sample of first mentor:
{
  "fullName": "Rajani Rao",
  "position": "CTO/Principal Technologist, WInvest/AVEVA",
  "email": "rajani.rao@womencodingcommunity.com",
  ...
}
```

### Step 2: Verify the JSON (Optional)

Check the generated JSON file:

```bash
# Count mentors
jq '. | length' mentors_data.json

# View first mentor
jq '.[0]' mentors_data.json

# List all mentor names
jq '.[].fullName' mentors_data.json
```

### Step 3: Test Upload in Dry-Run Mode

Before making actual API calls, test the upload script:

```bash
DRY_RUN=true ./upload_mentors.sh
```

**Expected Output:**
```
🚀 Starting WCC backend mentors upload...
📁 Reading mentors from: /home/runner/work/wcc/wcc/tools/mentors_data.json
🌐 API Base URL: http://localhost:8080/api
🔍 DRY RUN MODE: No actual API calls will be made

📊 Found 46 mentors to upload

➡️  [1/46] Uploading mentor: Rajani Rao
    [DRY RUN] Would upload: Rajani Rao
    [DRY RUN] Data size: 2243 bytes
...
```

### Step 4: Upload to Backend

Once you've verified the data looks correct, upload to the backend:

```bash
# Upload to default local backend
./upload_mentors.sh

# OR specify custom API endpoint
API_BASE="https://api.example.com/api" API_KEY="your-api-key" ./upload_mentors.sh
```

**Expected Output (Success):**
```
🚀 Starting WCC backend mentors upload...
📁 Reading mentors from: /home/runner/work/wcc/wcc/tools/mentors_data.json
🌐 API Base URL: http://localhost:8080/api

📊 Found 46 mentors to upload

➡️  [1/46] Uploading mentor: Rajani Rao
✅  Successfully uploaded Rajani Rao (HTTP 201)

➡️  [2/46] Uploading mentor: Eleonora Belova
✅  Successfully uploaded Eleonora Belova (HTTP 201)

...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📈 Upload Summary:
   ✅ Successful: 46
   ❌ Failed: 0
   📊 Total: 46
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎉 All mentors uploaded successfully!
```

## Common Use Cases

### Re-convert After YAML Changes

If you update `_data/mentors.yml`, simply re-run the conversion:

```bash
python3 convert_mentors_to_json.py
```

This will regenerate `mentors_data.json` with the latest data.

### Upload to Different Environment

```bash
# Production
API_BASE="https://api.womencodingcommunity.com/api" \
API_KEY="prod-secret-key" \
./upload_mentors.sh

# Staging
API_BASE="https://staging-api.womencodingcommunity.com/api" \
API_KEY="staging-key" \
./upload_mentors.sh
```

### Debug a Single Mentor

Extract and inspect a specific mentor:

```bash
# Find mentor by name
jq '.[] | select(.fullName == "Rajani Rao")' mentors_data.json

# View all technical areas
jq '.[0].skills.areas' mentors_data.json

# Check all emails
jq '.[].email' mentors_data.json
```

## Troubleshooting

### Issue: "jq: command not found"

**Solution:** Install jq:
```bash
# macOS
brew install jq

# Ubuntu/Debian
sudo apt-get install jq

# Windows (via Chocolatey)
choco install jq
```

### Issue: "ModuleNotFoundError: No module named 'yaml'"

**Solution:** Install PyYAML:
```bash
pip install pyyaml
# or
pip3 install pyyaml
```

### Issue: Upload fails with HTTP 401

**Solution:** Check your API key:
```bash
API_KEY="correct-api-key" ./upload_mentors.sh
```

### Issue: Upload fails with HTTP 500

**Solution:** 
1. Check the backend server logs
2. Verify the JSON format matches the API schema
3. Try uploading a single mentor manually to identify the issue

## Tips

1. **Always test in dry-run mode first** to verify data correctness
2. **Keep the original YAML** as the source of truth
3. **Version control the scripts** but not necessarily the generated JSON
4. **Monitor upload progress** - the script shows detailed status for each mentor
5. **Handle errors gracefully** - the script continues even if some uploads fail

## Next Steps

- Check the backend API to verify all mentors were created
- Update mentor profiles as needed through the backend interface
- Set up automated workflows for periodic data sync

For more details, see [MENTORS_SCRIPTS_README.md](MENTORS_SCRIPTS_README.md).
