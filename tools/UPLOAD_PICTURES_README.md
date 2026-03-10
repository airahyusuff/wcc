# Upload Mentor Profile Pictures Script

This script uploads profile pictures for mentors from the `assets/images/mentors` directory to the WCC backend.

## Prerequisites

- `jq` must be installed (for bash script)
- Python 3 with `requests` library (for Python script)
- Images must exist in `assets/images/mentors/` directory
- A mentor IDs mapping file (see below)

## Creating the Mentor IDs Mapping File

Since the API requires mentor IDs, you need to create a mapping file that links mentor names to their IDs.

### Method 1: Auto-generate from Log (Recommended)

First, run the upload_and_accept_mentors script and save the output to a log file:

```bash
export API_KEY='your-api-key-here'
./tools/upload_and_accept_mentors.sh | tee tools/mentor_ids.log
```

Then generate the mapping file from the log:

```bash
./tools/generate_mentor_ids_mapping.sh
```

This automatically extracts mentor IDs from the log and creates `tools/mentor_ids_mapping.txt`.

### Method 2: Generate Template and Fill Manually

```bash
./tools/generate_mentor_ids_mapping.sh --template
```

This creates `tools/mentor_ids_mapping.txt` with mentor names and placeholder IDs. After running `upload_and_accept_mentors` script, manually fill in the IDs:

```
Rajani Rao|abc123-def456-789
Eleonora Belova|ghi789-jkl012-345
...
```

## Usage

### Bash Script

```bash
export API_KEY='your-api-key-here'
export MENTOR_IDS_FILE='tools/mentor_ids_mapping.txt'
./tools/upload_mentor_pictures.sh
```

### Python Script

```bash
export API_KEY='your-api-key-here'
export MENTOR_IDS_FILE='tools/mentor_ids_mapping.txt'
python3 tools/upload_mentor_pictures.py
```

### Dry Run (Test Without Uploading)

```bash
export API_KEY='test'
export MENTOR_IDS_FILE='tools/mentor_ids_mapping.txt'
DRY_RUN=true ./tools/upload_mentor_pictures.sh
```

## How It Works

For each mentor in the mapping file:

1. **Normalizes** the mentor name (e.g., "Rajani Rao" → "rajani_rao")
2. **Finds** the corresponding image file in `assets/images/mentors/`
   - Tries: `rajani_rao.jpeg`, `rajani_rao.jpg`, `rajani_rao.png`
3. **Uploads** via POST to `/platform/v1/resources/member-profile-picture?memberId={id}`
4. **Reports** success, failure, or if image file is missing

## Image File Naming Convention

Images should be named using the mentor's full name:
- Convert to lowercase
- Replace spaces with underscores
- Remove or replace special characters with underscores

Examples:
- "Rajani Rao" → `rajani_rao.jpeg`
- "Adriana Zencke Zimmermann" → `adriana_zencke_zimmermann.jpeg`
- "Ken Pemberton" → `ken_pemberton.jpeg`

Supported extensions: `.jpeg`, `.jpg`, `.png`

## Expected Output

```
🚀 Starting WCC backend mentor pictures upload...
📁 Images directory: ../assets/images/mentors
📋 Reading mentor IDs from: tools/mentor_ids_mapping.txt

➡️  Processing mentor: Rajani Rao (ID: abc123)
    📸 Found image: rajani_rao.jpeg
    ✅ Successfully uploaded picture for Rajani Rao (HTTP 200)

➡️  Processing mentor: Eleonora Belova (ID: def456)
    📸 Found image: eleonora_belova.jpeg
    ✅ Successfully uploaded picture for Eleonora Belova (HTTP 200)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📈 Upload Summary:
   ✅ Successfully uploaded: 35
   ❌ Failed: 0
   ⚠️  Skipped (no image): 0
   📊 Total processed: 35
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎉 Process completed! 35 pictures uploaded successfully!
```

## Environment Variables

- `API_KEY` (required): Your WCC backend API key
- `MENTOR_IDS_FILE` (required): Path to mentor IDs mapping file
- `API_BASE` (optional): API base URL (default: `https://wcc-backend-prod.fly.dev/api`)
- `DRY_RUN` (optional): Set to `true` for testing (default: `false`)

## Complete Workflow

1. **Create mentors** using `upload_and_accept_mentors` script
2. **Generate mapping file** from the log output
3. **Upload pictures** using this script

Example complete workflow:

```bash
# Step 1: Upload and accept mentors (save log)
export API_KEY='your-key-here'
./tools/upload_and_accept_mentors.sh | tee tools/mentor_ids.log

# Step 2: Generate mapping file from log
./tools/generate_mentor_ids_mapping.sh

# Step 3: Upload profile pictures
export MENTOR_IDS_FILE='tools/mentor_ids_mapping.txt'
./tools/upload_mentor_pictures.sh
```

## Troubleshooting

### "No MENTOR_IDS_FILE provided or file not found"

Make sure to set the `MENTOR_IDS_FILE` environment variable and that the file exists:

```bash
export MENTOR_IDS_FILE='tools/mentor_ids_mapping.txt'
ls -l $MENTOR_IDS_FILE  # Verify file exists
```

### "No image file found for: Mentor Name"

The image file naming doesn't match the expected pattern. Check:
1. Image exists in `assets/images/mentors/`
2. Image name matches normalized mentor name (lowercase, underscores)
3. Image has supported extension (.jpeg, .jpg, .png)

### "API_KEY environment variable is not set"

Set your API key before running:

```bash
export API_KEY='your-api-key-here'
```

## Security Note

⚠️ **NEVER commit the API key to the repository!** Always pass it via environment variable.

## Available Images

Current images in `assets/images/mentors/` (46 total):
- adeola_adekoyejo.jpeg
- adriana_zencke_zimmermann.jpeg
- airah_yusuff.jpeg
- ana_nogal.jpeg
- ... and 42 more

Run the script without MENTOR_IDS_FILE to see the full list.
