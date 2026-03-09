#!/usr/bin/env python3
"""
Script to convert mentors.yml to JSON format compatible with wcc-backend API.
This script reads the _data/mentors.yml file and converts it to the JSON format
expected by the wcc-backend POST /platform/v1/mentors endpoint.
"""

import yaml
import json
import re
import os
from pathlib import Path


def parse_location(location_str):
    """Parse location string into city and country."""
    if not location_str:
        return None, {"countryCode": "GB", "countryName": "United Kingdom"}
    
    # Common country mappings
    country_mappings = {
        "UK": {"countryCode": "GB", "countryName": "United Kingdom"},
        "United Kingdom": {"countryCode": "GB", "countryName": "United Kingdom"},
        "USA": {"countryCode": "US", "countryName": "United States"},
        "United States": {"countryCode": "US", "countryName": "United States"},
        "Germany": {"countryCode": "DE", "countryName": "Germany"},
        "Netherlands": {"countryCode": "NL", "countryName": "Netherlands"},
        "The Netherlands": {"countryCode": "NL", "countryName": "Netherlands"},
        "Spain": {"countryCode": "ES", "countryName": "Spain"},
        "France": {"countryCode": "FR", "countryName": "France"},
        "Italy": {"countryCode": "IT", "countryName": "Italy"},
        "Portugal": {"countryCode": "PT", "countryName": "Portugal"},
        "Ireland": {"countryCode": "IE", "countryName": "Ireland"},
        "Poland": {"countryCode": "PL", "countryName": "Poland"},
        "Canada": {"countryCode": "CA", "countryName": "Canada"},
        "Australia": {"countryCode": "AU", "countryName": "Australia"},
        "New Zealand": {"countryCode": "NZ", "countryName": "New Zealand"},
        "India": {"countryCode": "IN", "countryName": "India"},
        "Singapore": {"countryCode": "SG", "countryName": "Singapore"},
        "Sweden": {"countryCode": "SE", "countryName": "Sweden"},
        "Denmark": {"countryCode": "DK", "countryName": "Denmark"},
        "Norway": {"countryCode": "NO", "countryName": "Norway"},
        "Finland": {"countryCode": "FI", "countryName": "Finland"},
        "Belgium": {"countryCode": "BE", "countryName": "Belgium"},
        "Switzerland": {"countryCode": "CH", "countryName": "Switzerland"},
        "Austria": {"countryCode": "AT", "countryName": "Austria"},
        "Brazil": {"countryCode": "BR", "countryName": "Brazil"},
        "Argentina": {"countryCode": "AR", "countryName": "Argentina"},
        "Mexico": {"countryCode": "MX", "countryName": "Mexico"},
        "Japan": {"countryCode": "JP", "countryName": "Japan"},
        "South Korea": {"countryCode": "KR", "countryName": "South Korea"},
        "China": {"countryCode": "CN", "countryName": "China"},
    }
    
    # Try to parse location string (format: "City, Country" or just "Country")
    parts = [p.strip() for p in location_str.split(',')]
    
    city = None
    country = {"countryCode": "GB", "countryName": "United Kingdom"}  # Default
    
    if len(parts) == 1:
        # Just country or just city
        for country_name, country_info in country_mappings.items():
            if country_name.lower() in parts[0].lower():
                country = country_info
                break
    elif len(parts) >= 2:
        # City, Country format
        city = parts[0]
        country_part = parts[-1].strip()
        
        for country_name, country_info in country_mappings.items():
            if country_name.lower() in country_part.lower():
                country = country_info
                break
    
    return city, country


def normalize_technical_area(area):
    """Normalize technical area to backend enum values."""
    area_mappings = {
        "backend developer": "BACKEND",
        "backend": "BACKEND",
        "frontend developer": "FRONTEND",
        "frontend": "FRONTEND",
        "fullstack developer": "FULLSTACK",
        "fullstack": "FULLSTACK",
        "full stack": "FULLSTACK",
        "mobile developer": "MOBILE",
        "mobile": "MOBILE",
        "devops": "DEVOPS",
        "dev ops": "DEVOPS",
        "data engineering": "DATA_ENGINEERING",
        "data engineer": "DATA_ENGINEERING",
        "machine learning": "MACHINE_LEARNING",
        "ml": "MACHINE_LEARNING",
        "ai": "MACHINE_LEARNING",
        "distributed systems": "DISTRIBUTED_SYSTEMS",
        "quality assurance": "QUALITY_ASSURANCE",
        "qa": "QUALITY_ASSURANCE",
        "testing": "QUALITY_ASSURANCE",
        "engineering management": "ENGINEERING_MANAGEMENT",
        "management": "ENGINEERING_MANAGEMENT",
        "project management": "PROJECT_MANAGEMENT",
        "security": "SECURITY",
        "cybersecurity": "SECURITY",
        "cloud": "CLOUD",
        "database": "DATABASE",
    }
    
    area_lower = area.lower().strip()
    return area_mappings.get(area_lower, "BACKEND")  # Default to BACKEND


def normalize_language(lang):
    """Normalize programming language to backend enum values."""
    lang_mappings = {
        "java": "JAVA",
        "python": "PYTHON",
        "javascript": "JAVASCRIPT",
        "js": "JAVASCRIPT",
        "typescript": "TYPESCRIPT",
        "ts": "TYPESCRIPT",
        "c++": "C_PLUS_PLUS",
        "cpp": "C_PLUS_PLUS",
        "c#": "C_SHARP",
        "csharp": "C_SHARP",
        "c": "C",
        "go": "GO",
        "golang": "GO",
        "rust": "RUST",
        "ruby": "RUBY",
        "php": "PHP",
        "swift": "SWIFT",
        "kotlin": "KOTLIN",
        "scala": "SCALA",
        "r": "R",
        "matlab": "MATLAB",
        "sql": "SQL",
        "html": "HTML",
        "css": "CSS",
    }
    
    lang_lower = lang.lower().strip()
    return lang_mappings.get(lang_lower, None)


def parse_languages(languages_str):
    """Parse languages string into list of language objects."""
    if not languages_str or languages_str == '':
        return []
    
    # Split by common delimiters
    langs = re.split(r'[,;/]', languages_str)
    
    result = []
    for lang in langs:
        lang = lang.strip()
        if lang:
            normalized = normalize_language(lang)
            if normalized:
                # Default proficiency based on position in list (first = EXPERT, others = ADVANCED)
                proficiency = "ADVANCED"
                if len(result) == 0:
                    proficiency = "EXPERT"
                
                result.append({
                    "language": normalized,
                    "proficiencyLevel": proficiency
                })
    
    return result


def parse_spoken_languages(languages_str):
    """Parse spoken languages string into list."""
    if not languages_str:
        return ["english"]
    
    # Split by common delimiters
    langs = re.split(r'[,;/&]', languages_str.lower())
    
    result = []
    for lang in langs:
        lang = lang.strip()
        if lang and lang not in ['and']:
            result.append(lang)
    
    return result if result else ["english"]


def generate_email(name):
    """Generate a sanitized email address from name."""
    import unicodedata
    
    # Normalize unicode characters (e.g., Turkish characters)
    normalized = unicodedata.normalize('NFKD', name)
    # Remove diacritics
    ascii_name = ''.join(c for c in normalized if not unicodedata.combining(c))
    # Convert to lowercase and normalize whitespace
    cleaned = ' '.join(ascii_name.lower().split())
    # Replace spaces with dots
    email_local = cleaned.replace(' ', '.')
    
    return f"{email_local}@womencodingcommunity.com"


def extract_company_name(position_str):
    """Extract company name from position string."""
    if not position_str:
        return ""
    
    # Try to parse "Role, Company" format
    if ',' in position_str:
        parts = position_str.split(',')
        # Return the last part as it's usually the company
        return parts[-1].strip()
    
    # If no comma, check if there's "at Company" pattern
    if ' at ' in position_str.lower():
        parts = position_str.split(' at ', 1)
        return parts[-1].strip()
    
    # Otherwise return empty string (role-only, no company)
    return ""


def convert_mentor_to_json(mentor):
    """Convert a mentor from YAML format to JSON format."""
    
    # Skip disabled mentors
    if mentor.get('disabled', False):
        return None
    
    # Parse location
    city, country = parse_location(mentor.get('location', ''))
    
    # Get network information
    network = []
    for net_item in mentor.get('network', []):
        for net_type, link in net_item.items():
            network.append({
                "type": net_type,
                "link": link
            })
    
    # Parse skills
    skills_data = mentor.get('skills', {})
    years_exp = skills_data.get('years', 0)
    
    # Parse technical areas
    areas = []
    for area in skills_data.get('areas', []):
        normalized_area = normalize_technical_area(area)
        # Assign proficiency based on years of experience
        if years_exp >= 10:
            proficiency = "EXPERT"
        elif years_exp >= 5:
            proficiency = "ADVANCED"
        else:
            proficiency = "INTERMEDIATE"
        
        areas.append({
            "technicalArea": normalized_area,
            "proficiencyLevel": proficiency
        })
    
    # Parse programming languages
    prog_languages = parse_languages(skills_data.get('languages', ''))
    
    # Parse mentorship focus
    mentorship_focus = skills_data.get('focus', [])
    
    # Build mentee section
    mentee_section = {
        "idealMentee": skills_data.get('mentee', '').strip(),
        "additional": skills_data.get('extra', '').strip(),
    }
    
    # Add long term mentorship info
    num_mentee = mentor.get('num_mentee', 0)
    hours = mentor.get('hours', 0)
    mentor_type = mentor.get('type', 'long-term')
    
    if mentor_type in ['long-term', 'both'] and num_mentee > 0:
        mentee_section['longTerm'] = {
            "numMentee": num_mentee,
            "hours": hours
        }
    
    # Add ad-hoc availability
    availability = mentor.get('availability', [])
    if (mentor_type in ['ad-hoc', 'both'] or availability) and hours > 0:
        # Convert availability to adHoc format
        # Note: The original YAML doesn't have month-specific availability
        # so we'll create a placeholder
        mentee_section['adHoc'] = [
            {"month": "JUNE", "hours": hours},
        ]
    
    # Build the final JSON structure
    # Note: email is a placeholder as actual emails are not in the YAML source
    # Gender-related fields use defaults appropriate for Women Coding Community
    # which specifically supports women in tech (adjust if source data provides these fields)
    json_mentor = {
        "fullName": mentor.get('name', ''),
        "position": mentor.get('position', ''),
        "email": generate_email(mentor.get('name', 'unknown')),
        "slackDisplayName": f"@{mentor.get('name', '').split()[0]}",
        "country": country,
        "companyName": extract_company_name(mentor.get('position', '')),
        "memberTypes": ["MENTOR"],
        "images": [],
        "network": network,
        "isWomen": True,  # Default for WCC which supports women in tech
        "acceptMale": True,
        "acceptPromotion": True,
        "pronouns": "she/her",
        "pronounCategory": "FEMININE",
        "skills": {
            "yearsExperience": years_exp,
            "areas": areas,
            "languages": prog_languages,
            "mentorshipFocus": mentorship_focus
        },
        "spokenLanguages": parse_spoken_languages(mentor.get('languages', '')),
        "bio": mentor.get('bio', '').strip(),
        "menteeSection": mentee_section
    }
    
    # Add city if available
    if city:
        json_mentor['city'] = city
    
    return json_mentor


def main():
    """Main function to convert mentors.yml to JSON."""
    # Get the repository root directory
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    
    # Input and output paths
    input_file = repo_root / '_data' / 'mentors.yml'
    output_file = repo_root / 'tools' / 'mentors_data.json'
    
    print(f"Reading mentors from: {input_file}")
    
    # Load YAML data
    with open(input_file, 'r', encoding='utf-8') as f:
        mentors = yaml.safe_load(f)
    
    print(f"Found {len(mentors)} mentors in YAML file")
    
    # Convert each mentor
    json_mentors = []
    skipped = 0
    for mentor in mentors:
        converted = convert_mentor_to_json(mentor)
        if converted:
            json_mentors.append(converted)
        else:
            skipped += 1
    
    print(f"Converted {len(json_mentors)} mentors to JSON format")
    print(f"Skipped {skipped} disabled mentors")
    
    # Write to JSON file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(json_mentors, f, indent=2, ensure_ascii=False)
    
    print(f"JSON data written to: {output_file}")
    print(f"\nSample of first mentor:")
    print(json.dumps(json_mentors[0], indent=2))


if __name__ == '__main__':
    main()
