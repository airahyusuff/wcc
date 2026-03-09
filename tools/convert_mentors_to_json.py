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
        return "London", {"countryCode": "GB", "countryName": "United Kingdom", "capital": "London"}
    
    # Common country mappings with capitals
    country_mappings = {
        "UK": {"countryCode": "GB", "countryName": "United Kingdom", "capital": "London"},
        "United Kingdom": {"countryCode": "GB", "countryName": "United Kingdom", "capital": "London"},
        "USA": {"countryCode": "US", "countryName": "United States", "capital": "Washington DC"},
        "United States": {"countryCode": "US", "countryName": "United States", "capital": "Washington DC"},
        "Germany": {"countryCode": "DE", "countryName": "Germany", "capital": "Berlin"},
        "Netherlands": {"countryCode": "NL", "countryName": "Netherlands", "capital": "Amsterdam"},
        "The Netherlands": {"countryCode": "NL", "countryName": "Netherlands", "capital": "Amsterdam"},
        "Spain": {"countryCode": "ES", "countryName": "Spain", "capital": "Madrid"},
        "France": {"countryCode": "FR", "countryName": "France", "capital": "Paris"},
        "Italy": {"countryCode": "IT", "countryName": "Italy", "capital": "Rome"},
        "Portugal": {"countryCode": "PT", "countryName": "Portugal", "capital": "Lisbon"},
        "Ireland": {"countryCode": "IE", "countryName": "Ireland", "capital": "Dublin"},
        "Poland": {"countryCode": "PL", "countryName": "Poland", "capital": "Warsaw"},
        "Canada": {"countryCode": "CA", "countryName": "Canada", "capital": "Ottawa"},
        "Australia": {"countryCode": "AU", "countryName": "Australia", "capital": "Canberra"},
        "New Zealand": {"countryCode": "NZ", "countryName": "New Zealand", "capital": "Wellington"},
        "India": {"countryCode": "IN", "countryName": "India", "capital": "New Delhi"},
        "Singapore": {"countryCode": "SG", "countryName": "Singapore", "capital": "Singapore"},
        "Sweden": {"countryCode": "SE", "countryName": "Sweden", "capital": "Stockholm"},
        "Denmark": {"countryCode": "DK", "countryName": "Denmark", "capital": "Copenhagen"},
        "Norway": {"countryCode": "NO", "countryName": "Norway", "capital": "Oslo"},
        "Finland": {"countryCode": "FI", "countryName": "Finland", "capital": "Helsinki"},
        "Belgium": {"countryCode": "BE", "countryName": "Belgium", "capital": "Brussels"},
        "Switzerland": {"countryCode": "CH", "countryName": "Switzerland", "capital": "Bern"},
        "Austria": {"countryCode": "AT", "countryName": "Austria", "capital": "Vienna"},
        "Brazil": {"countryCode": "BR", "countryName": "Brazil", "capital": "Brasília"},
        "Argentina": {"countryCode": "AR", "countryName": "Argentina", "capital": "Buenos Aires"},
        "Mexico": {"countryCode": "MX", "countryName": "Mexico", "capital": "Mexico City"},
        "Japan": {"countryCode": "JP", "countryName": "Japan", "capital": "Tokyo"},
        "South Korea": {"countryCode": "KR", "countryName": "South Korea", "capital": "Seoul"},
        "China": {"countryCode": "CN", "countryName": "China", "capital": "Beijing"},
        "Albania": {"countryCode": "AL", "countryName": "Albania", "capital": "Tirana"},
        "Turkey": {"countryCode": "TR", "countryName": "Turkey", "capital": "Ankara"},
        "Serbia": {"countryCode": "RS", "countryName": "Serbia", "capital": "Belgrade"},
        "Romania": {"countryCode": "RO", "countryName": "Romania", "capital": "Bucharest"},
        "Bulgaria": {"countryCode": "BG", "countryName": "Bulgaria", "capital": "Sofia"},
        "Jamaica": {"countryCode": "JM", "countryName": "Jamaica", "capital": "Kingston"},
        "Nigeria": {"countryCode": "NG", "countryName": "Nigeria", "capital": "Abuja"},
    }
    
    # Normalize slashes to commas for consistent parsing
    location_normalized = location_str.replace('/', ',').strip()
    
    # Try to parse location string
    parts = [p.strip() for p in location_normalized.split(',')]
    
    city = None
    country = {"countryCode": "GB", "countryName": "United Kingdom", "capital": "London"}  # Default
    country_found = False
    
    if len(parts) == 1:
        # Single part - could be city or country
        single_part = parts[0]
        
        # Check if it matches a country exactly
        for country_name, country_info in country_mappings.items():
            if country_name.lower() == single_part.lower():
                country = country_info
                city = country_info.get("capital")
                country_found = True
                break
        
        # If not a country, treat as city (keep default UK country)
        if not country_found:
            city = single_part
            
    elif len(parts) == 2:
        # Two parts - typically City, Country
        city_part = parts[0]
        country_part = parts[1].strip()
        
        # Check if first part is country (e.g., "Bulgaria, Sofia")
        first_is_country = False
        for country_name, country_info in country_mappings.items():
            if country_name.lower() == city_part.lower():
                # First part is country, second is city
                city = country_part
                country = country_info
                country_found = True
                first_is_country = True
                break
        
        # If first part wasn't country, check second part for country
        if not first_is_country:
            for country_name, country_info in country_mappings.items():
                if country_name.lower() in country_part.lower():
                    country = country_info
                    city = city_part
                    country_found = True
                    break
            
            # If still not found, use first part as city
            if not country_found:
                city = city_part
                
    elif len(parts) > 2:
        # Multiple commas - last part is country, rest is city
        country_part = parts[-1].strip()
        city = ', '.join(parts[:-1])  # Join all parts except last as city
        
        for country_name, country_info in country_mappings.items():
            if country_name.lower() in country_part.lower():
                country = country_info
                country_found = True
                break
    
    # If still no city, use capital as default
    if not city:
        city = country.get("capital", "London")
    
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
                result.append(normalized)
    
    # Assign proficiency levels based on position
    # EXPERT, ADVANCED, INTERMEDIATE, BEGINNER
    # If more than 4, last one uses BEGINNER
    proficiency_levels = ["EXPERT", "ADVANCED", "INTERMEDIATE", "BEGINNER"]
    
    languages_with_proficiency = []
    for i, lang in enumerate(result):
        if i < len(proficiency_levels):
            proficiency = proficiency_levels[i]
        else:
            # More than 4 items, use BEGINNER for the rest
            proficiency = "BEGINNER"
        
        languages_with_proficiency.append({
            "language": lang,
            "proficiencyLevel": proficiency
        })
    
    return languages_with_proficiency


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


def extract_position_role(position_str):
    """Extract role from position string (before comma)."""
    if not position_str:
        return ""
    
    # Split by comma and take the first part (the role)
    if ',' in position_str:
        return position_str.split(',')[0].strip()
    
    # If no comma, check if there's "at Company" pattern
    if ' at ' in position_str.lower():
        parts = position_str.split(' at ', 1)
        return parts[0].strip()
    
    # Otherwise return the entire string (role-only)
    return position_str.strip()


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
    area_list = skills_data.get('areas', [])
    
    # Assign proficiency levels: EXPERT, ADVANCED, INTERMEDIATE, BEGINNER
    # If more than 4, use BEGINNER for the rest
    proficiency_levels = ["EXPERT", "ADVANCED", "INTERMEDIATE", "BEGINNER"]
    
    for i, area in enumerate(area_list):
        normalized_area = normalize_technical_area(area)
        
        if i < len(proficiency_levels):
            proficiency = proficiency_levels[i]
        else:
            # More than 4 items, use BEGINNER for the rest
            proficiency = "BEGINNER"
        
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
    
    # Add long term mentorship info (without hours - hours in YAML is for adhoc)
    num_mentee = mentor.get('num_mentee', 0)
    mentor_type = mentor.get('type', 'long-term')
    
    if mentor_type in ['long-term', 'both'] and num_mentee > 0:
        mentee_section['longTerm'] = {
            "numMentee": num_mentee
            # hours field intentionally omitted - will be set later via spreadsheet
        }
    
    # adHoc array should be empty for now
    mentee_section['adHoc'] = []
    
    # Build the final JSON structure
    # Note: email left blank - will be imported later via spreadsheet
    # Gender-related fields default to false until confirmed
    json_mentor = {
        "fullName": mentor.get('name', ''),
        "position": extract_position_role(mentor.get('position', '')),
        "email": "",  # Left blank - will be imported via spreadsheet
        "slackDisplayName": f"@{mentor.get('name', '').split()[0]}",
        "country": country,
        "companyName": extract_company_name(mentor.get('position', '')),
        "memberTypes": ["MENTOR"],
        "images": [],
        "network": network,
        "isWomen": False,  # Default to false until confirmed
        "acceptMale": False,  # Default to false until confirmed
        "acceptPromotion": False,  # Default to false until confirmed
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
    
    # Add city - should always be present now
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
