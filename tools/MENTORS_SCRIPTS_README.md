# Mentors Data Conversion and Upload Scripts

This directory contains scripts to convert mentor data from YAML to JSON format and upload it to the WCC backend API.

## Files

- `convert_mentors_to_json.py` - Python script that converts `_data/mentors.yml` to JSON format compatible with wcc-backend API
- `mentors_data.json` - Generated JSON file containing all mentor data (created by running the conversion script)
- `upload_mentors.sh` - Bash script that loops through the JSON file and uploads each mentor via curl

## Requirements

### For conversion script:
- Python 3.x
- PyYAML (install via: `pip install pyyaml`)

### For upload script:
- Bash
- curl
- jq (JSON processor - install from https://stedolan.github.io/jq/download/)

## Usage

### Step 1: Convert YAML to JSON

Run the conversion script to generate `mentors_data.json`:

```bash
cd tools
python3 convert_mentors_to_json.py
```

This will:
- Read mentor data from `_data/mentors.yml`
- Convert each mentor to the JSON format expected by wcc-backend
- Write the results to `tools/mentors_data.json`
- Display a sample of the first converted mentor

### Step 2: Upload Mentors to Backend

Run the upload script to send all mentors to the API:

```bash
cd tools
./upload_mentors.sh
```

By default, the script connects to:
- API Base URL: `http://localhost:8080/api`
- API Key: `test`

You can override these with environment variables:

```bash
API_BASE="https://api.example.com/api" API_KEY="your-api-key" ./upload_mentors.sh
```

The script will:
- Read all mentors from `mentors_data.json`
- Loop through each mentor
- Send a POST request to `/platform/v1/mentors` for each one
- Display progress and summary statistics

## Data Mapping

The conversion script maps YAML fields to JSON fields as follows:

### Basic Information
- `name` → `fullName`
- `position` → `position`
- `location` → parsed into `city` and `country` (with countryCode)
- `bio` → `bio`
- `languages` → `spokenLanguages`

### Skills
- `skills.years` → `skills.yearsExperience`
- `skills.areas` → `skills.areas[]` (with technicalArea and proficiencyLevel)
- `skills.languages` → `skills.languages[]` (with language and proficiencyLevel)
- `skills.focus` → `skills.mentorshipFocus[]`

### Mentorship
- `num_mentee` + `hours` → `menteeSection.longTerm`
- `type` + `hours` → `menteeSection.adHoc[]`
- `skills.mentee` → `menteeSection.idealMentee`
- `skills.extra` → `menteeSection.additional`

### Network
- `network[]` → `network[]` (with type and link)

## Notes

- The conversion script skips mentors where `disabled: true`
- Email addresses are generated as `{name}@womencodingcommunity.com`
- Slack display names are generated as `@{firstName}`
- Default values are used for some fields (isWomen: true, acceptMale: true, etc.)
- Country codes are mapped from location strings using common country names
- Technical areas and programming languages are normalized to backend enum values

## JSON Format

The generated JSON follows the wcc-backend API schema. Here's an example structure:

```json
{
  "fullName": "Jane Doe",
  "position": "Senior Software Engineer",
  "email": "jane.doe@womencodingcommunity.com",
  "slackDisplayName": "@Jane",
  "country": {
    "countryCode": "GB",
    "countryName": "United Kingdom"
  },
  "city": "London",
  "companyName": "Tech Company",
  "memberTypes": ["MENTOR"],
  "images": [],
  "network": [
    {
      "type": "linkedin",
      "link": "https://www.linkedin.com/in/janedoe"
    }
  ],
  "isWomen": true,
  "acceptMale": true,
  "acceptPromotion": true,
  "pronouns": "she/her",
  "pronounCategory": "FEMININE",
  "skills": {
    "yearsExperience": 10,
    "areas": [
      {
        "technicalArea": "BACKEND",
        "proficiencyLevel": "EXPERT"
      }
    ],
    "languages": [
      {
        "language": "JAVA",
        "proficiencyLevel": "EXPERT"
      }
    ],
    "mentorshipFocus": [
      "Grow from beginner to mid-level"
    ]
  },
  "spokenLanguages": ["english"],
  "bio": "Bio text here...",
  "menteeSection": {
    "idealMentee": "Description of ideal mentee...",
    "additional": "Additional information...",
    "longTerm": {
      "numMentee": 2,
      "hours": 4
    },
    "adHoc": [
      {
        "month": "JUNE",
        "hours": 2
      }
    ]
  }
}
```

## Reference

The JSON format is based on the wcc-backend API specification:
https://github.com/airahyusuff/wcc-backend/blob/main/scripts/init-local-env.sh#L42-L103
