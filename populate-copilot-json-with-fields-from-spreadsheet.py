# Needs:
# - base JSON file from Copilot agent coding AND 
# spreadsheet (Excel file with "WCC: All Approved Mentors" sheet) to run.
# Outputs updated JSON file with fields from spreadsheet.

import json
import pandas as pd
import argparse


def yes_no_to_bool(value, default=True):
    if isinstance(value, str):
        v = value.strip().lower()
        if v == "yes":
            return True
        if v == "no":
            return False
    return default


def normalize_pronoun_category(pronouns: str):
    if not pronouns:
        return "FEMININE"

    p = pronouns.lower()

    if "she" in p and "her" in p:
        return "FEMININE"
    if "he" in p and "him" in p:
        return "MASCULINE"

    return "OTHER"


def ensure_slack_prefix(name):
    if not isinstance(name, str) or not name.strip():
        return name

    name = name.strip()

    if not name.startswith("@"):
        name = "@" + name

    return name


def detect_column(columns, keyword):
    for c in columns:
        if keyword in c.lower():
            return c
    return None


def main(json_file, spreadsheet, output_file):

    with open(json_file) as f:
        mentors = json.load(f)

    xls = pd.ExcelFile(spreadsheet)

    # find sheet containing approved mentors
    sheet = [s for s in xls.sheet_names if "approved" in s.lower()][0]

    df = pd.read_excel(spreadsheet, sheet_name=sheet)
    df.columns = [c.strip() for c in df.columns]

    email_col = detect_column(df.columns, "email")
    slack_col = detect_column(df.columns, "slack")
    pronouns_col = detect_column(df.columns, "pronoun")
    women_col = detect_column(df.columns, "identify as a woman")
    accept_male_col = detect_column(df.columns, "open to mentoring")
    promo_col = detect_column(df.columns, "highlight")
    name_col = detect_column(df.columns, "name")

    lookup = {
        str(row[name_col]).strip().lower(): row
        for _, row in df.iterrows()
    }

    updated = 0

    for mentor in mentors:

        name = str(mentor.get("fullName", "")).strip().lower()

        if name in lookup:

            row = lookup[name]

            pronouns = row.get(pronouns_col)

            if pd.isna(pronouns) or not str(pronouns).strip():
                pronouns = "she/her"

            mentor["email"] = row.get(email_col)
            mentor["slackDisplayName"] = ensure_slack_prefix(row.get(slack_col))
            mentor["pronouns"] = pronouns
            mentor["pronounCategory"] = normalize_pronoun_category(pronouns)

            mentor["isWomen"] = yes_no_to_bool(row.get(women_col), True)
            mentor["acceptMale"] = yes_no_to_bool(row.get(accept_male_col), True)
            mentor["acceptPromotion"] = yes_no_to_bool(row.get(promo_col), True)

            updated += 1

        # enforce defaults
        mentor["isWomen"] = mentor.get("isWomen", True)
        mentor["acceptMale"] = mentor.get("acceptMale", True)
        mentor["acceptPromotion"] = mentor.get("acceptPromotion", True)

        if not mentor.get("pronouns"):
            mentor["pronouns"] = "she/her"
            mentor["pronounCategory"] = "FEMININE"

        # ensure slack prefix if present
        mentor["slackDisplayName"] = ensure_slack_prefix(
            mentor.get("slackDisplayName")
        )

        # add hours field
        mentee_section = mentor.get("menteeSection", {})
        long_term = mentee_section.get("longTerm")

        if isinstance(long_term, dict) and "numMentee" in long_term:
            try:
                long_term["hours"] = int(long_term["numMentee"]) * 2
            except Exception:
                pass

    with open(output_file, "w") as f:
        json.dump(mentors, f, indent=2)

    print(f"{updated} mentors updated")
    print(f"Output written to {output_file}")


if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument("json")
    parser.add_argument("spreadsheet")
    parser.add_argument("output")

    args = parser.parse_args()

    main(args.json, args.spreadsheet, args.output)
