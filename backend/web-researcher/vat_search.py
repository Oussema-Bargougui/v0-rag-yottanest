#!/usr/bin/env python3
"""
KBO (Kruispuntbank van Ondernemingen) Scraper Tool.

This module provides functionality to scrape company information from the Belgian KBO public database.
It supports both full browser-based scraping (via crawl4ai) and basic HTML scraping (via requests).

For agent usage: Use `scrap_vat_kbo_data` as the canonical entrypoint after validating a VAT.
This ensures consistent naming and provides a clear integration point for automated workflows.
"""

import re  # Regular expressions for parsing markdown content
import json  # JSON serialization for output
import os  # Operating system interface for file operations
from typing import Dict, List, Optional  # Type hints for better code clarity
from pathlib import Path  # Object-oriented filesystem paths

# Try importing crawl4ai for browser-based scraping (optional dependency)
try:
    from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
    C4A_AVAILABLE = True  # Flag to track if crawl4ai is available
except ImportError:
    # If crawl4ai is not installed, set flag to False and create dummy classes
    AsyncWebCrawler = None
    BrowserConfig = None
    CrawlerRunConfig = None
    CacheMode = None
    C4A_AVAILABLE = False  # Will fallback to requests-based scraping

# Try importing requests for basic HTTP scraping (required dependency)
try:
    import requests  # HTTP library for making web requests
    REQUESTS_AVAILABLE = True  # Flag to track if requests is available
except ImportError:
    requests = None
    REQUESTS_AVAILABLE = False  # Both scrapers unavailable - will error

# Try importing asyncio for async operations (required for crawl4ai)
try:
    import asyncio  # Asynchronous I/O for crawl4ai operations
except ImportError:
    asyncio = None  # Will error if crawl4ai is used without asyncio

# Export public functions for external imports
__all__ = ["scrap_vat_kbo_data", "scrape_kbo_data"]

# ---------------------------
# Parsing
# ---------------------------

def _parse_kbo_from_html(html: str) -> Dict:
    """
    Parse KBO company data from raw HTML content.
    
    This function extracts company information directly from the HTML structure
    of the KBO website, handling the specific DOM elements and patterns used.
    
    Parameters
    ----------
    html : str
        Raw HTML content from the KBO website
    
    Returns
    -------
    dict
        Structured company data with all available fields
    """
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        
        # Initialize output structure
        out = {
            "company_id": None,
            "name": None,
            "status": None,
            "legal_status": None,
            "legal_form": None,
            "start_date": None,
            "address_block": None,
            "website": None,
            "phone": None,
            "fax": None,
            "email": None,
            "entity_type": None,
            "establishment_units": None,
            "functions": [],
            "entrepreneurial_skills": [],
            "capacities": [],
            "licenses": [],
            "btw_activities": [],
            "rsz_activities": [],
            "financial_data": {
                "capital": None,
                "annual_meeting": None,
                "fiscal_year_end": None
            },
            "entity_links": [],
            "external_links": []
        }
        
        # Extract company name from title or main heading
        title_tag = soup.find('title')
        if title_tag:
            title_text = title_tag.get_text().strip()
            # Extract company name from title pattern
            if ' - ' in title_text:
                out["name"] = title_text.split(' - ')[0].strip()

        # Look for main content tables
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    label = cells[0].get_text().strip().lower()
                    value = cells[1].get_text().strip()

                    # Map common fields
                    if 'naam' in label or 'name' in label:
                        if value and not out["name"]:
                            out["name"] = value
                    elif 'status' in label:
                        out["status"] = value
                    elif 'rechtsvorm' in label or 'legal form' in label:
                        out["legal_form"] = value
                    elif 'adres' in label or 'address' in label:
                        out["address_block"] = value
                    elif 'telefoon' in label or 'phone' in label:
                        out["phone"] = value
                    elif 'website' in label or 'url' in label:
                        out["website"] = value
                    elif 'email' in label:
                        out["email"] = value

        return out

    except Exception as e:
        # Return error structure if parsing fails
        return {
            "company_id": None,
            "name": None,
            "status": None,
            "legal_status": None,
            "legal_form": None,
            "start_date": None,
            "address_block": "Address not available",
            "website": None,
            "phone": None,
            "fax": None,
            "email": None,
            "entity_type": None,
            "establishment_units": None,
            "functions": [],
            "entrepreneurial_skills": [],
            "capacities": [],
            "licenses": [],
            "btw_activities": [],
            "rsz_activities": [],
            "financial_data": {
                "capital": None,
                "annual_meeting": None,
                "fiscal_year_end": None
            },
            "entity_links": [],
            "external_links": [],
            "error": f"Failed to parse HTML: {str(e)}"
        }


def _parse_kbo_from_markdown(md: str) -> Dict:
    """
    Parse KBO company data from markdown-formatted content.
    
    This function extracts structured company information from the markdown
    representation of a KBO webpage. It uses regular expressions to identify
    and extract various data fields including company details, activities,
    financial data, and relationships.
    
    Parameters
    ----------
    md : str
        Markdown-formatted content from the KBO website, typically obtained
        via crawl4ai's markdown conversion or HTML-to-markdown transformation.
    
    Returns
    -------
    dict
        A structured dictionary containing all extracted company information:
        - company_id: Belgian enterprise number (e.g., "0403.170.701")
        - name: Company name
        - status: Current status (e.g., "Actief")
        - legal_status: Legal status (e.g., "Normale toestand")
        - legal_form: Legal form (e.g., "Naamloze vennootschap")
        - start_date: Company start date
        - address_block: Full address
        - website: Company website URL
        - phone: Phone number
        - fax: Fax number
        - email: Email address
        - entity_type: Type of entity (e.g., "Rechtspersoon")
        - establishment_units: Number and link to establishment units
        - entrepreneurial_skills: List of entrepreneurial qualifications
        - capacities: List of company capacities (e.g., "Werkgever RSZ")
        - licenses: List of business licenses
        - btw_activities: List of VAT activities with version, code, description, and date
        - rsz_activities: List of RSZ activities with version, code, description, and date
        - financial_data: Dictionary with capital, annual meeting, and fiscal year end
        - entity_links: List of related entities with their relationships
        - external_links: List of external reference links
    
    Notes
    -----
    - All fields default to None or empty lists if not found in the markdown
    - The function is resilient to format variations in the KBO website
    - Regex patterns are designed to handle both Dutch and French content
    """
    try:
        # Initialize output dictionary with all expected fields
        out = {
            "company_id": None,  # Enterprise number
            "name": None,  # Company name
            "status": None,  # Active/inactive status
            "legal_status": None,  # Legal situation
            "legal_form": None,  # Company type
            "start_date": None,  # Foundation date
            "address_block": None,  # Full address
            "website": None,  # Company website
            "phone": None,  # Phone number
            "fax": None,  # Fax number
            "email": None,  # Email address
            "entity_type": None,  # Entity type
            "establishment_units": None,  # Number of units
            "functions": [],  # List of functions/function holders
            "entrepreneurial_skills": [],  # List of skills
            "capacities": [],  # List of capacities
            "licenses": [],  # List of licenses
            "btw_activities": [],  # VAT activities
            "rsz_activities": [],  # RSZ activities
            "financial_data": {  # Financial information
                "capital": None,
                "annual_meeting": None,
                "fiscal_year_end": None
            },
            "entity_links": [],  # Related entities
            "external_links": []  # External reference links
        }

        # Check if markdown content is valid
        if not md or not isinstance(md, str):
            print("[WARNING] Invalid or empty markdown content")
            return out

        # Helper function to clean extracted text
        def _clean(s):
            """Remove extra whitespace and clean up text."""
            if not s:  # Return empty string if None or empty
                return ""
            # Remove pipe characters and extra whitespace
            return re.sub(r"\s+", " ", s.replace("|", "").strip())

        # 1) Add right below _clean()
        def _strip_md_links(text: str) -> str:
            """
            Replace markdown links [label](url) with 'label' and remove orphan pieces like '](url)'.
            """
            if not text:
                return ""
            text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)   # [label](url) -> label
            text = re.sub(r"\]\([^)]+\)", "", text)                # orphan '](url)' -> ''
            return text

        # --- Core company information extraction ---
        # Extract enterprise number - support both Dutch and English, handle table format
        company_id_match = re.search(r"(Ondernemingsnummer|Enterprise number):\s*\|\s*([^\n|]+)", md, re.IGNORECASE)
        if company_id_match:
            out["company_id"] = _clean(company_id_match.group(2))

        # Extract company name - handle table format
        name_match = re.search(r"Name:\s*\|\s*([^\n|]+)", md, re.IGNORECASE)
        if name_match:
            out["name"] = _clean(name_match.group(1))

        # Extract status - handle table format
        status_match = re.search(r"Status:\s*\|\s*\*\*([^*]+)\*\*", md, re.IGNORECASE)
        if status_match:
            out["status"] = _clean(status_match.group(1))

        # Extract legal status - handle table format
        legal_status_match = re.search(r"Legal situation:\s*\|\s*\*\*([^*]+)\*\*", md, re.IGNORECASE)
        if legal_status_match:
            out["legal_status"] = _clean(legal_status_match.group(1))

        # Extract legal form - handle table format
        legal_form_match = re.search(r"Legal form:\s*\|\s*([^\n|]+)", md, re.IGNORECASE)
        if legal_form_match:
            out["legal_form"] = _clean(legal_form_match.group(1))

        # Extract start date - support both Dutch and English, handle table format
        start_date_match = re.search(r"(Begindatum|Start date):\s*\|\s*([^\n|]+)", md, re.IGNORECASE)
        if start_date_match:
            out["start_date"] = _clean(start_date_match.group(2))

        # Extract address - support both Dutch and English, handle table format and multi-line
        address_match = re.search(r"(Maatschappelijke zetel|Registered seat's address):\s*\|\s*([^|]+?)(?=\n[A-Za-z]+:|Since|\Z)", md, re.DOTALL | re.IGNORECASE)
        if address_match:
            out["address_block"] = _clean(address_match.group(2))

        # Extract website - handle table format
        website_match = re.search(r"Web Address:\s*\|\s*\|\s*\[([^\]]+)\]\([^)]+\)", md, re.IGNORECASE)
        if website_match:
            out["website"] = _clean(website_match.group(1))

        # Extract phone - handle table format
        phone_match = re.search(r"Phone number:\s*\|\s*([^\n|]+)", md, re.IGNORECASE)
        if phone_match and "No data included" not in phone_match.group(1):
            out["phone"] = _clean(phone_match.group(1))

        # Extract fax - handle table format
        fax_match = re.search(r"Fax:\s*\|\s*([^\n|]+)", md, re.IGNORECASE)
        if fax_match and "No data included" not in fax_match.group(1):
            out["fax"] = _clean(fax_match.group(1))

        # Extract email - handle table format
        email_match = re.search(r"Email address:\s*\|\s*\|\s*([^\s|]+)", md, re.IGNORECASE)
        if email_match:
            out["email"] = _clean(email_match.group(1))

        # Extract entity type - handle table format
        entity_type_match = re.search(r"Entity type:\s*\|\s*([^\n|]+)", md, re.IGNORECASE)
        if entity_type_match:
            out["entity_type"] = _clean(entity_type_match.group(1))

        # Extract establishment units - handle table format
        establishment_match = re.search(r"Number of establishment units.*?:\s*\|\s*\*\*(\d+)\*\*", md, re.IGNORECASE)
        if establishment_match:
            out["establishment_units"] = _clean(establishment_match.group(1))

        # --- Functions extraction ---
        # Extract directors and other functions from table format
        functions_section = re.search(r"## Functions.*?(?=##|$)", md, re.DOTALL | re.IGNORECASE)
        if functions_section:
            functions_text = functions_section.group(0)
            # Extract individual function entries from table format
            function_matches = re.findall(r"([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*Since\s+([^|\n]+)", functions_text, re.IGNORECASE)
            for role, name, since_date in function_matches:
                role_clean = _clean(role)
                name_clean = _clean(name)
                since_clean = _clean(since_date)
                
                # Skip header rows and empty entries
                if role_clean and name_clean and "---" not in role_clean and "---" not in name_clean:
                    out["functions"].append({
                        "role": role_clean,
                        "name": name_clean,
                        "since": since_clean
                    })
        
        # Fallback: Find the functions section (Functies) for non-table format
        if not out["functions"]:
            functions_section = re.search(r"Functies.*?\n(.*?)(?=\n\n[A-Z]|\n##|\Z)", md, re.DOTALL | re.IGNORECASE)
            if functions_section:
                functions = []  # Temporary list
                for line in functions_section.group(1).split("\n"):  # Process each line
                    cleaned = _clean(line)  # Clean the line
                    # Skip empty lines, headers, and separators
                    if cleaned and not cleaned.startswith("##") and not cleaned.startswith("---"):
                        functions.append(cleaned)  # Add to functions
                out["functions"] = functions  # Store in output

        # --- Company name extraction (robust, no links) ---
        name_val = None

        # Try the explicit "Naam:" line first (the visible legal name is on the next non-empty line)
        m_name_block = re.search(r"^\s*Naam:\s*\|?\s*(.*?)(?=\n[A-Z][^\n]*:\s*|\n\n|\Z)", md, flags=re.M | re.I | re.S)
        if m_name_block:
            # Examine lines after "Naam:"
            lines = [ln.strip() for ln in m_name_block.group(1).split("\n")]
            for ln in lines:
                if not ln:
                    continue
                # Skip language markers and junk like orphan link tails
                if re.match(r"^(Naam in het|Name in|Nom en|Sinds|Since|Depuis)\b", ln, flags=re.I):
                    continue
                if ln.startswith("]("):   # orphan tail of a markdown link
                    continue
                candidate = _strip_md_links(ln)
                # Cut off any trailing meta like "Naam in het Nederlands, sinds ..."
                candidate = re.split(r"\b(Naam in het|Name in|Nom en|Sinds|Since|Depuis)\b", candidate, maxsplit=1, flags=re.I)[0].strip()
                if candidate:
                    name_val = candidate
                    break

        # Fallback 1: the next line after "Naam in het Nederlands"
        if not name_val:
            m_nl = re.search(r"^Naam in het Nederlands[^\n]*\n([^\n]+)", md, flags=re.M | re.I)
            if m_nl:
                name_val = _strip_md_links(m_nl.group(1)).strip()

        # Fallback 2: Commerciële Naam
        if not name_val:
            m_trade = re.search(r"^\s*Commerci[eë]le Naam:\s*\|?\s*([^\n]+)", md, flags=re.M | re.I)
            if m_trade:
                name_val = _strip_md_links(m_trade.group(1)).strip()

        # Final cleanup and assign
        if name_val:
            name_val = name_val.replace("**", "").replace("_", "").replace("`", "").strip()
        out["name"] = name_val or out.get("name")


        # --- Entrepreneurial skills extraction ---
        # Find the entrepreneurial skills section and extract all skills
        # Support both Dutch and English section names
        skills_section = re.search(r"(Ondernemersvaardigheden|Entrepreneurial skill).*?\n(.*?)(?=\n\n[A-Z]|\n##|\Z)", md, re.DOTALL | re.IGNORECASE)
        if skills_section:
            skills = []  # Temporary list to avoid duplicates
            for line in skills_section.group(2).split("\n"):  # Process each line (group 2 because group 1 is the section name)
                cleaned = _clean(line)  # Clean the line
                # Skip empty lines, headers, and separators
                if cleaned and not cleaned.startswith("##") and not cleaned.startswith("---"):
                    skills.append(cleaned)  # Add to skills list
            out["entrepreneurial_skills"] = skills  # Store in output

        # --- Capacities extraction ---
        # Find the capacities section (Hoedanigheden/Functions)
        capacities_section = re.search(r"(Hoedanigheden|Functions).*?\n(.*?)(?=\n\n[A-Z]|\n##|\Z)", md, re.DOTALL | re.IGNORECASE)
        if capacities_section:
            capacities = []  # Temporary list
            for line in capacities_section.group(2).split("\n"):  # Process each line
                cleaned = _clean(line)  # Clean the line
                # Skip empty lines, headers, and separators
                if cleaned and not cleaned.startswith("##") and not cleaned.startswith("---"):
                    capacities.append(cleaned)  # Add to capacities
            out["capacities"] = capacities  # Store in output

        # --- Licenses extraction ---
        # Find the licenses section (Toelatingen/Authorisations)
        licenses_section = re.search(r"(Toelatingen|Authorisations).*?\n(.*?)(?=\n\n[A-Z]|\n##|\Z)", md, re.DOTALL | re.IGNORECASE)
        if licenses_section:
            licenses = []  # Temporary list
            for line in licenses_section.group(2).split("\n"):  # Process each line
                cleaned = _clean(line)  # Clean the line
                # Skip empty lines, headers, and separators
                if cleaned and not cleaned.startswith("##") and not cleaned.startswith("---"):
                    licenses.append(cleaned)  # Add to licenses
            out["licenses"] = licenses  # Store in output

        # --- BTW (VAT) activities extraction ---
        # Extract BTW/VAT 2025 activities (current version) - support both Dutch and English
        for m in re.findall(r"(Btw|VAT)\s*2025[:\s]*([0-9.]+)\s*[-–]\s*([^\n]+)", md, re.IGNORECASE):
            out["btw_activities"].append({
                "version": "BTW 2025",  # Version identifier
                "code": m[1],  # NACE code (group 1 is Btw/VAT, group 2 is code)
                "desc": _clean(m[2]),  # Activity description
                "since": "1 januari 2025"  # Default date for 2025 version
            })

        # Extract BTW/VAT 2008 activities (previous version)
        for m in re.findall(r"(Btw|VAT)\s*2008[:\s]*([0-9.]+)\s*[-–]\s*([^\n]+)", md, re.IGNORECASE):
            out["btw_activities"].append({
                "version": "BTW 2008",  # Version identifier
                "code": m[1],  # NACE code
                "desc": _clean(m[2]),  # Activity description
                "since": "1 januari 2008"  # Default date for 2008 version
            })

        # Extract BTW/VAT 2003 activities (oldest version)
        for m in re.findall(r"(Btw|VAT)\s*2003[:\s]*([0-9.]+)\s*[-–]\s*([^\n]+)", md, re.IGNORECASE):
            out["btw_activities"].append({
                "version": "BTW 2003",  # Version identifier
                "code": m[1],  # NACE code
                "desc": _clean(m[2]),  # Activity description
                "since": None  # No default date for 2003
            })

        # --- RSZ (Social Security) activities extraction ---
        # Extract RSZ/NSSO 2025 activities - support both Dutch and English
        for m in re.findall(r"(RSZ|NSSO)\s*2025[:\s]*([0-9.]+)\s*[-–]\s*([^\n]+)", md, re.IGNORECASE):
            out["rsz_activities"].append({
                "version": "RSZ 2025",  # Version identifier
                "code": m[1],  # NACE code
                "desc": _clean(m[2]),  # Activity description
                "since": "1 januari 2025"  # Default date for 2025
            })

        # Extract RSZ/NSSO 2008 activities
        for m in re.findall(r"(RSZ|NSSO)\s*2008[:\s]*([0-9.]+)\s*[-–]\s*([^\n]+)", md, re.IGNORECASE):
            out["rsz_activities"].append({
                "version": "RSZ 2008",  # Version identifier
                "code": m[1],  # NACE code
                "desc": _clean(m[2]),  # Activity description
                "since": None  # No default date
            })

        # Extract RSZ/NSSO 2003 activities
        for m in re.findall(r"(RSZ|NSSO)\s*2003[:\s]*([0-9.]+)\s*[-–]\s*([^\n]+)", md, re.IGNORECASE):
            out["rsz_activities"].append({
                "version": "RSZ 2003",  # Version identifier
                "code": m[1],  # NACE code
                "desc": _clean(m[2]),  # Activity description
                "since": None  # No default date
            })

        # --- Financial information extraction ---
        # Extract financial data from table format
        financial_section = re.search(r"## Financial information.*?(?=##|$)", md, re.DOTALL | re.IGNORECASE)
        if financial_section:
            financial_text = financial_section.group(0)
            
            # Extract capital
            capital_match = re.search(r"Capital\s*\|\s*([^\n|]+)", financial_text, re.IGNORECASE)
            if capital_match:
                out["financial_data"]["capital"] = _clean(capital_match.group(1))
            
            # Extract annual assembly
            assembly_match = re.search(r"Annual assembly\s*\|\s*([^\n|]+)", financial_text, re.IGNORECASE)
            if assembly_match:
                out["financial_data"]["annual_meeting"] = _clean(assembly_match.group(1))
            
            # Extract financial year end
            year_end_match = re.search(r"End date financial year\s*\|\s*([^\n|]+)", financial_text, re.IGNORECASE)
            if year_end_match:
                out["financial_data"]["fiscal_year_end"] = _clean(year_end_match.group(1))

        # --- Statistical tables extraction ---
        # Extract NACE codes tables
        nace_sections = re.findall(r"## Version of the Nacebel codes.*?(?=##|$)", md, re.DOTALL | re.IGNORECASE)
        for section in nace_sections:
            # Extract NACE code entries
            nace_matches = re.findall(r"(VAT|NSSO)\s*(\d{4})\s*\[?([0-9.]+)\]?\s*-\s*([^\n]+)", section, re.IGNORECASE)
            for match in nace_matches:
                activity_type, year, code, description = match
                if activity_type.upper() == "VAT":
                    out["btw_activities"].append({
                        "version": f"BTW {year}",
                        "code": _clean(code),
                        "desc": _clean(description),
                        "since": None
                    })
                elif activity_type.upper() == "NSSO":
                    out["rsz_activities"].append({
                        "version": f"RSZ {year}",
                        "code": _clean(code),
                        "desc": _clean(description),
                        "since": None
                    })

        # --- Authorizations extraction ---
        auth_section = re.search(r"## Authorisations.*?(?=##|$)", md, re.DOTALL | re.IGNORECASE)
        if auth_section:
            auth_text = auth_section.group(0)
            # Extract authorization entries
            auth_matches = re.findall(r"([^\n]+?)\s*Since\s+([^\n]+)", auth_text, re.IGNORECASE)
            for auth_name, since_date in auth_matches:
                auth_clean = _clean(auth_name)
                since_clean = _clean(since_date)
                if auth_clean and "Authorisations" not in auth_clean:
                    out["licenses"].append(f"{auth_clean} (since {since_clean})")

        # --- Entity links extraction (related companies) ---
        # Find the entity links section - support both Dutch and English
        entity_section = re.search(r"(Linken tussen entiteiten|Links between entities)\s*\n(.*?)(?=\n\n[A-Z]|\n(Externe links|External links)|\Z)", md, re.DOTALL | re.IGNORECASE)
        if entity_section:
            content = entity_section.group(2)  # Get section content (group 2 because group 1 is the section name)
            
            # Pattern 1: Markdown link format [NUMBER](url) (NAME) relationship sinds/since DATE
            pattern1 = r"\[?(\d{4}\.\d{3}\.\d{3})\]?\([^)]*\)\s*\(([^)]+)\)\s*(.*?)\s+(sinds|since)\s+(.+?)(?=\n|$)"
            for match in re.findall(pattern1, content):
                out["entity_links"].append({
                    "number": match[0],  # Company number
                    "name": match[1],  # Company name
                    "relationship": _clean(match[2]),  # Relationship type
                    "since": match[4]  # Date (group 4 because group 3 is sinds/since)
                })
            
            # Pattern 2: Plain text format NUMBER (NAME) relationship sinds/since DATE
            pattern2 = r"^(\d{4}\.\d{3}\.\d{3})\s*\(([^)]+)\)\s*(.*?)\s+(sinds|since)\s+(.+?)(?=\n|$)"
            for line in content.split("\n"):
                if not re.match(r"^\[", line):  # Skip markdown links already processed
                    match = re.search(pattern2, line)
                    if match:
                        out["entity_links"].append({
                            "number": match.group(1),  # Company number
                            "name": match.group(2),  # Company name
                            "relationship": _clean(match.group(3)),  # Relationship type
                            "since": match.group(5)  # Date
                        })
            
            # Pattern 3: "Deze entiteit/This entity" format with markdown link
            pattern3 = r"(Deze entiteit|This entity)\s+(.*?)\s+\[?(\d{4}\.\d{3}\.\d{3})\]?\([^)]*\)\s*\(([^)]+)\)\s+(sinds|since)\s+(.+?)(?=\n|$)"
            for match in re.findall(pattern3, content):
                out["entity_links"].append({
                    "number": match[2],  # Company number
                    "name": match[3],  # Company name
                    "relationship": f"{match[0]} {match[1]}",  # Full relationship text
                    "since": match[5]  # Date
                })
            
            # Pattern 4: "Deze entiteit/This entity" format without markdown link
            pattern4 = r"(Deze entiteit|This entity)\s+(.*?)\s+(\d{4}\.\d{3}\.\d{3})\s*\(([^)]+)\)\s+(sinds|since)\s+(.+?)(?=\n|$)"
            for line in content.split("\n"):
                if ("Deze entiteit" in line or "This entity" in line) and not re.search(r"\[\d{4}\.\d{3}\.\d{3}\]", line):
                    match = re.search(pattern4, line)
                    if match:
                        out["entity_links"].append({
                            "number": match.group(3),  # Company number
                            "name": match.group(4),  # Company name
                            "relationship": f"{match.group(1)} {match.group(2)}",  # Full relationship text
                            "since": match.group(6)  # Date
                        })
        
        # Fallback: If no entity links found, try simpler pattern
        if not out["entity_links"]:
            # Find all company numbers with dates
            all_entities = re.findall(r"(\d{4}\.\d{3}\.\d{3}).*?sinds\s+(\d+\s+\w+\s+\d{4})", md)
            for number, date in all_entities:
                # Skip the main company number
                if number != out.get("company_id"):
                    out["entity_links"].append({
                        "number": number,  # Company number
                        "name": "",  # Name not found
                        "relationship": "",  # Relationship not found
                        "since": date  # Date
                    })

        # --- External links extraction ---
        # Find the external links section - support both Dutch and English
        external_section = re.search(r"(Externe links|External links)\s*\n(.*?)(?=\n\(|\Z)", md, re.DOTALL | re.IGNORECASE)
        if external_section:
            # Find all markdown-formatted links [label](url)
            for label, url in re.findall(r"\[([^\]]+)\]\(([^)]+)\)", external_section.group(2)):
                out["external_links"].append({
                    "label": _clean(label),  # Link text
                    "url": url  # Link URL
                })
            
            # Also capture plain text links without markdown formatting
            for line in external_section.group(2).split("\n"):
                cleaned = _clean(line)
                # Add non-markdown lines that aren't headers or already have URLs
                if cleaned and not re.match(r"^(##|--|\[)", cleaned) and "http" not in cleaned:
                    out["external_links"].append({
                        "label": cleaned,  # Link text
                        "url": None  # No URL found
                    })

        return out  # Return the complete parsed data

    except Exception as e:
        print(f"[ERROR] Failed to parse KBO data: {str(e)}")
        # Return a minimal structure with error information
        return {
            "company_id": None,
            "name": "Data parsing error",
            "status": "Error",
            "legal_status": None,
            "legal_form": "Unknown",
            "start_date": None,
            "address_block": "Could not parse company data",
            "website": None,
            "phone": None,
            "fax": None,
            "email": None,
            "entity_type": None,
            "establishment_units": None,
            "functions": [],
            "entrepreneurial_skills": [],
            "capacities": [],
            "licenses": [],
            "btw_activities": [],
            "rsz_activities": [],
            "financial_data": {
                "capital": None,
                "annual_meeting": None,
                "fiscal_year_end": None
            },
            "entity_links": [],
            "external_links": [],
            "error": f"Failed to parse KBO data: {str(e)}"
        }

# ---------------------------
# Fetchers
# ---------------------------

async def _fetch_markdown_with_crawl4ai(url: str) -> str:
    """
    Fetch and convert webpage content to markdown using crawl4ai browser automation.
    
    This function uses a headless browser to load the webpage, execute JavaScript,
    and convert the rendered HTML to markdown format. This is necessary for pages
    that rely heavily on client-side rendering.
    
    Parameters
    ----------
    url : str
        The full URL of the KBO webpage to scrape.
    
    Returns
    -------
    str
        Markdown-formatted content of the webpage. Returns empty string if
        the fetch fails or no content is available.
    
    Raises
    ------
    RuntimeError
        If crawl4ai is not installed or if the crawl operation fails.
    
    Side Effects
    ------------
    - Makes a network request to the specified URL
    - Launches a headless browser instance (resource intensive)
    - May take several seconds to complete due to page rendering
    
    Notes
    -----
    - Requires crawl4ai to be installed (`pip install crawl4ai`)
    - Uses Playwright under the hood for browser automation
    - Bypasses cache to ensure fresh data
    - Waits for network idle before capturing content
    """
    # Check if crawl4ai is available
    if not C4A_AVAILABLE:
        raise RuntimeError("crawl4ai not installed/available")

    # Configure browser settings
    browser_conf = BrowserConfig(headless=True)  # Run browser in headless mode
    # Configure crawl settings
    run_conf = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,  # Always fetch fresh data
        page_timeout=60000,  # 60 second timeout
        word_count_threshold=1,  # Include all content
    )

    # Create crawler instance and fetch the page
    async with AsyncWebCrawler(config=browser_conf) as crawler:
        result = await crawler.arun(url=url, config=run_conf)  # Run the crawl

    # Check if crawl was successful
    if not getattr(result, "success", True):
        raise RuntimeError(getattr(result, "error_message", "Unknown crawl4ai error"))

    # Extract markdown content from result (try multiple attributes)
    md_obj = getattr(result, "markdown", None)
    if hasattr(md_obj, "fit_markdown") and md_obj.fit_markdown:
        return md_obj.fit_markdown  # Preferred: fitted markdown
    if hasattr(md_obj, "raw_markdown") and md_obj.raw_markdown:
        return md_obj.raw_markdown  # Alternative: raw markdown
    if isinstance(md_obj, str) and md_obj:
        return md_obj  # Direct string markdown
    # Fallback to HTML if no markdown available
    html = getattr(result, "html", "") or getattr(result, "raw_html", "")
    return html or ""  # Return HTML or empty string

def _fetch_html_with_requests(url: str) -> str:
    """
    Fetch webpage HTML content using the requests library.
    
    This is a simpler, faster alternative to browser-based scraping.
    It works well for static HTML pages but may miss JavaScript-rendered content.
    
    Parameters
    ----------
    url : str
        The full URL of the KBO webpage to scrape.
    
    Returns
    -------
    str
        Raw HTML content of the webpage.
    
    Raises
    ------
    requests.RequestException
        If the HTTP request fails (network error, timeout, etc.)
    requests.HTTPError
        If the server returns an error status code (4xx, 5xx)
    
    Side Effects
    ------------
    - Makes a network request to the specified URL
    - Much lighter than browser-based scraping
    
    Notes
    -----
    - Does not execute JavaScript
    - May not work for pages that require client-side rendering
    - Includes a user agent header to identify the scraper
    """
    # Set headers to identify the scraper
    headers = {"User-Agent": "Mozilla/5.0 (compatible; KBO-Scraper/1.0; +https://example.local)"}
    # Make HTTP GET request
    resp = requests.get(url, headers=headers, timeout=30)  # 30 second timeout
    resp.raise_for_status()  # Raise exception for bad status codes
    return resp.text  # Return HTML content

# ---------------------------
# Main Tool Function
# ---------------------------

def scrape_kbo_data(vat_number: str, engine: str = "crawl4ai") -> Dict:
    """
    Scrape KBO data for a given VAT number.

    Args:
        vat_number (str):
            Belgian VAT or enterprise number. Format is flexible.
        engine (str):
            "crawl4ai" (default) - uses Crawl4AI headless browser for full data.
            "requests" - uses basic HTTP requests (faster but may miss JS content).

    Returns:
        dict: Parsed company data with all available fields.
    """
    # Clean VAT number: remove spaces, dots, and "BE" prefix
    vat_clean = re.sub(r"[^0-9]", "", vat_number.upper().replace("BE", ""))
    # Ensure VAT has 10 digits (pad with zeros if needed)
    if len(vat_clean) < 10:
        vat_clean = vat_clean.zfill(10)  # Pad with leading zeros
    # Format as 0XXX.XXX.XXX for the URL
    vat_formatted = f"{vat_clean[:4]}.{vat_clean[4:7]}.{vat_clean[7:10]}"
    
    # Construct KBO URL with English language parameter
    url = f"https://kbopub.economie.fgov.be/kbopub/zoeknummerform.html?lang=en&nummer={vat_formatted}&actionLu=Search"
    print(f"[INFO] Fetching KBO data for {vat_formatted} from {url}")

    # Fetch content based on selected engine
    if engine == "crawl4ai":
        # Use browser-based scraping
        if not C4A_AVAILABLE:
            print("[WARNING] crawl4ai not available, falling back to requests")
            engine = "requests"  # Fallback to requests
        else:
            # Run async crawler
            if asyncio:
                # Get or create event loop
                try:
                    loop = asyncio.get_running_loop()  # Try to get existing loop
                    # If we're already in a loop, create a task
                    content = asyncio.create_task(_fetch_markdown_with_crawl4ai(url))
                except RuntimeError:
                    # No loop running, create a new one
                    content = asyncio.run(_fetch_markdown_with_crawl4ai(url))
            else:
                raise RuntimeError("asyncio not available for crawl4ai")
    
    # Use requests-based scraping
    if engine == "requests":
        if not REQUESTS_AVAILABLE:
            raise RuntimeError("requests library not available")
        content = _fetch_html_with_requests(url)  # Get HTML content

    # Parse the content based on engine type
    if engine == "requests":
        # HTML content from requests needs HTML parsing
        parsed = _parse_kbo_from_html(content)
    else:
        # Markdown content from crawl4ai
        parsed = _parse_kbo_from_markdown(content)
    
    # Add metadata
    parsed["vat_number"] = vat_number  # Original input
    parsed["vat_formatted"] = vat_formatted  # Formatted version
    parsed["source_url"] = url  # Source URL
    parsed["engine"] = engine  # Engine used
    
    return parsed  # Return complete data

def scrap_vat_kbo_data(vat_number: str, engine: str = "crawl4ai") -> Dict:
    """
    Agent-friendly entrypoint for scraping KBO data.
    
    This is a thin wrapper around `scrape_kbo_data` that provides a consistent
    naming convention for agent integration. It performs exactly the same
    operation as the underlying function.
    
    Parameters
    ----------
    vat_number : str
        Belgian VAT or enterprise number in any common format.
        Examples: "BE0403170701", "0403170701", "403170701"
    
    engine : str, optional
        Scraping engine to use:
        - "crawl4ai" (default): Full browser automation for JavaScript-heavy pages
        - "requests": Lightweight HTTP client for static content
    
    Returns
    -------
    dict
        Structured company data with the following schema:
        {
            "company_id": str|None,           # Enterprise number
            "name": str|None,                  # Company name
            "status": str|None,                # Active/inactive status
            "legal_status": str|None,          # Legal situation
            "legal_form": str|None,            # Company type
            "start_date": str|None,            # Foundation date
            "address_block": str|None,         # Full address
            "website": str|None,               # Company website
            "phone": str|None,                 # Phone number
            "fax": str|None,                   # Fax number
            "email": str|None,                 # Email address
            "entity_type": str|None,           # Entity classification
            "establishment_units": str|None,   # Number of units
            "functions": [str],                # List of functions/function holders
            "entrepreneurial_skills": [str],   # List of qualifications
            "capacities": [str],               # List of capacities
            "licenses": [str],                 # List of licenses
            "btw_activities": [                # VAT activities
                {
                    "version": str,            # Version (e.g., "BTW 2025")
                    "code": str,               # NACE code
                    "desc": str,               # Activity description
                    "since": str|None          # Start date
                }
            ],
            "rsz_activities": [                # RSZ activities
                {
                    "version": str,            # Version (e.g., "RSZ 2025")
                    "code": str,               # NACE code
                    "desc": str,               # Activity description
                    "since": str|None          # Start date
                }
            ],
            "financial_data": {                # Financial information
                "capital": str|None,           # Share capital
                "annual_meeting": str|None,    # Annual meeting month
                "fiscal_year_end": str|None    # Fiscal year end date
            },
            "entity_links": [                  # Related entities
                {
                    "number": str,             # Enterprise number
                    "name": str,               # Entity name
                    "relationship": str,       # Relationship type
                    "since": str               # Relationship date
                }
            ],
            "external_links": [                # External references
                {
                    "label": str,              # Link text
                    "url": str|None            # Link URL
                }
            ],
            "vat_number": str,                 # Original input
            "vat_formatted": str,              # Formatted VAT
            "source_url": str,                 # KBO URL
            "engine": str                      # Engine used
        }
    
    Side Effects
    ------------
    - Makes network request to KBO website
    - May launch headless browser if using crawl4ai
    - Prints status messages to console
    
    Notes
    -----
    - This is the recommended entry point for agent integration
    - Behavior is identical to `scrape_kbo_data`
    - Use after VAT validation to ensure valid input
    - crawl4ai engine recommended for complete data extraction
    - requests engine is faster but may miss dynamic content
    
    Examples
    --------
    >>> data = scrap_vat_kbo_data("BE0403170701")
    >>> print(data["name"])
    'ELECTRABEL'
    
    >>> data = scrap_vat_kbo_data("0403170701", engine="requests")
    >>> print(data["legal_form"])
    'Naamloze vennootschap'
    """
    # IMPORTANT: just delegate to the existing function without altering parameters
    return scrape_kbo_data(vat_number=vat_number, engine=engine)

# ---------------------------
# Demo / CLI
# ---------------------------

if __name__ == "__main__":
    import sys

    # Accept VAT number from command line argument
    if len(sys.argv) > 1:
        vat = sys.argv[1]
    else:
        # Default test VAT number
        vat = "0428750985"

    print(f"[INFO] Scraping KBO data for VAT: {vat}")

    # Call the main scraping function with crawl4ai engine
    result = scrape_kbo_data(vat, engine="crawl4ai")

    # Generate output filename with VAT number
    vat_clean = result.get('vat_formatted', vat).replace('.', '')
    json_file = f"output/kbo/kbo_{vat_clean}.json"

    # Create output directory if it doesn't exist
    Path(json_file).parent.mkdir(parents=True, exist_ok=True)

    # Save JSON data for programmatic access
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"[SUCCESS] JSON data saved to {json_file}")