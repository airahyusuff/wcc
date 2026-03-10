# Upload and Accept Mentors Script

This script uploads mentors from `longterm_or_both_mentors.json` to the WCC backend and automatically accepts them.

## Prerequisites

- `jq` must be installed (for JSON parsing)
- The JSON file must exist at `../mentor_json_outputs/longterm_or_both_mentors.json`
- API key must be available

## Usage

### Dry Run (Recommended First)

Test the script without making actual API calls:

```bash
export API_KEY='your-api-key-here'
DRY_RUN=true ./upload_and_accept_mentors.sh
```

### Production Run

Upload and accept mentors to production:

```bash
export API_KEY='your-production-api-key'
./upload_and_accept_mentors.sh
```

### Using a Different API Base URL

To use a different backend (e.g., staging or local):

```bash
export API_KEY='your-api-key'
export API_BASE='http://localhost:8080/api'
./upload_and_accept_mentors.sh
```

## What the Script Does

For each mentor in the JSON file:

1. **POST** to `/platform/v1/mentors` - Creates the mentor
2. Extracts the `id` from the successful response
3. **PATCH** to `/platform/v1/mentors/{id}/accept` - Accepts the mentor

## Output

The script provides detailed progress information:

- Current mentor being processed (X/Total)
- Success/failure status for each mentor
- Final summary with counts:
  - Successfully created
  - Successfully accepted
  - Accept failures
  - Creation failures

## Error Handling

- If mentor creation fails, the script logs the error and continues
- If mentor acceptance fails, the script logs the error and continues
- The script returns a non-zero exit code if any operations fail
- Failed mentors are listed at the end of the run

## Environment Variables

- `API_KEY` (required): Your WCC backend API key
- `API_BASE` (optional): API base URL (default: `https://wcc-backend-prod.fly.dev/api`)
- `DRY_RUN` (optional): Set to `true` for testing without API calls (default: `false`)
- `VERBOSE` (optional): Set to `true` to see all created mentor IDs (default: `false`)

## Security Note

⚠️ **NEVER commit the API key to the repository!** Always pass it via environment variable.

## Example Output

```
🚀 Starting WCC backend mentors upload & accept process...
📁 Reading mentors from: ../mentor_json_outputs/longterm_or_both_mentors.json
🌐 API Base URL: https://wcc-backend-prod.fly.dev/api

📊 Found 35 mentors to upload

➡️  [1/35] Processing mentor: Rajani Rao
    ✅ Created mentor: Rajani Rao (HTTP 201, ID: abc123)
    ⏳ Accepting mentor ID: abc123
    ✅ Accepted mentor: Rajani Rao (HTTP 200)

...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📈 Upload & Accept Summary:
   ✅ Successfully created: 35
   ✅ Successfully accepted: 35
   ⚠️  Accept failed: 0
   ❌ Creation failed: 0
   📊 Total mentors: 35
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎉 Process completed! 35 mentors uploaded and accepted successfully!
```

## Troubleshooting

### "jq is required but not installed"

Install jq:
- macOS: `brew install jq`
- Ubuntu/Debian: `sudo apt-get install jq`
- See: https://stedolan.github.io/jq/download/

### "API_KEY environment variable is not set"

Make sure to export the API key before running:
```bash
export API_KEY='your-api-key-here'
```

### "JSON file not found"

Ensure you're running the script from the `tools/` directory and that `mentor_json_outputs/longterm_or_both_mentors.json` exists.
