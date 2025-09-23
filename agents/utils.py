import re

def clean_section_title(section_title: str) -> str:
    """
    Cleans the section title by removing markdown characters and extra whitespace.
    This prepares it for use in search queries or as a section header.
    """
    # Remove markdown characters like *, #, numbers, and periods at the start of a line
    cleaned_title = re.sub(r'^[*\s\d\.\-]+', '', section_title).strip()
    return cleaned_title

