#!/usr/bin/env python3
"""
comapy summary 

Generates professional Markdown business intelligence reports from KBO JSON data.
Automatically processes files from web_researcher/output/kbo directory.
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import requests

class LLMClient:
    """Client for interacting with local Ollama models."""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.1:latest"):
        self.base_url = base_url
        self.model = model
        self.session = requests.Session()
        
    def generate_response(self, prompt: str, max_tokens: int = 2000) -> str:
        """Generate response from the LLM."""
        try:
            response = self.session.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "num_predict": max_tokens,
                        "temperature": 0.7
                    }
                },
                timeout=120
            )
            response.raise_for_status()
            return response.json().get("response", "").strip()
        except Exception as e:
            logging.error(f"Error generating LLM response: {e}")
            return f"Error generating response: {str(e)}"

class KBOReportGenerator:
    """Generates comprehensive business intelligence reports from KBO data."""
    
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
        
    def load_kbo_data(self, file_path: str) -> Dict[str, Any]:
        """Load KBO data from JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Error loading KBO data from {file_path}: {e}")
            return {}
    
    def _prepare_company_summary(self, kbo_data: Dict[str, Any]) -> str:
        """Prepare comprehensive company summary for LLM analysis."""
        summary_parts = []
        
        # Basic company information
        company_name = kbo_data.get("name", "Unknown")
        company_id = kbo_data.get("company_id", "Unknown")
        legal_form = kbo_data.get("legal_form", "Unknown")
        status = kbo_data.get("status", "Unknown")
        legal_status = kbo_data.get("legal_status", "Unknown")
        start_date = kbo_data.get("start_date", "Unknown")
        address = kbo_data.get("address_block", "Unknown")
        
        summary_parts.append(f"Company Name: {company_name}")
        summary_parts.append(f"Enterprise Number: {company_id}")
        summary_parts.append(f"Legal Form: {legal_form}")
        summary_parts.append(f"Status: {status}")
        summary_parts.append(f"Legal Status: {legal_status}")
        summary_parts.append(f"Start Date: {start_date}")
        summary_parts.append(f"Address: {address}")
        
        # Establishment information
        entity_type = kbo_data.get("entity_type", "Unknown")
        establishment_units = kbo_data.get("establishment_units", "Unknown")
        website = kbo_data.get("website", "Not available")
        email = kbo_data.get("email", "Not available")
        
        summary_parts.append(f"Entity Type: {entity_type}")
        summary_parts.append(f"Establishment Units: {establishment_units}")
        summary_parts.append(f"Website: {website}")
        summary_parts.append(f"Email: {email}")
        
        # Business activities
        btw_activities = kbo_data.get("btw_activities", [])
        if btw_activities:
            summary_parts.append("Business Activities:")
            for activity in btw_activities[:3]:  # Limit to first 3 activities
                code = activity.get("code", "N/A")
                desc = activity.get("desc", "N/A")
                summary_parts.append(f"  - {code}: {desc}")
        
        # Key people
        functions = kbo_data.get("functions", [])
        if functions:
            summary_parts.append(f"Key People ({len(functions)} total):")
            # Group by role for better analysis
            roles = {}
            for person in functions:
                role = person.get("role", "Unknown")
                name = person.get("name", "Unknown")
                since = person.get("since", "Unknown")
                if role not in roles:
                    roles[role] = []
                roles[role].append(f"{name} (since {since})")
            
            for role, people in roles.items():
                summary_parts.append(f"  {role}: {len(people)} people")
                for person in people[:2]:  # Limit to first 2 per role
                    summary_parts.append(f"    - {person}")
        
        # Financial information
        financial_data = kbo_data.get("financial_data", {})
        if financial_data:
            summary_parts.append("Financial Information:")
            capital = financial_data.get("capital", "Not available")
            fiscal_year_end = financial_data.get("fiscal_year_end", "Not available")
            annual_meeting = financial_data.get("annual_meeting", "Not available")
            summary_parts.append(f"  Capital: {capital}")
            summary_parts.append(f"  Fiscal Year End: {fiscal_year_end}")
            summary_parts.append(f"  Annual Meeting: {annual_meeting}")
        
        # Professional licenses
        licenses = kbo_data.get("licenses", [])
        if licenses:
            summary_parts.append(f"Professional Licenses ({len(licenses)} total):")
            for license_info in licenses[:3]:  # Limit to first 3
                if isinstance(license_info, str):
                    summary_parts.append(f"  - {license_info}")
        
        # Entity relationships
        entity_links = kbo_data.get("entity_links", [])
        if entity_links:
            summary_parts.append(f"Entity Relationships ({len(entity_links)} total):")
            for link in entity_links[:5]:  # Limit to first 5
                name = link.get("name", "Unknown")
                relationship = link.get("relationship", "Unknown")
                since = link.get("since", "Unknown")
                summary_parts.append(f"  - {name}: {relationship} (since {since})")
        
        # External links count
        external_links = kbo_data.get("external_links", [])
        if external_links:
            summary_parts.append(f"External Official Links: {len(external_links)} available")
        
        return "\n".join(summary_parts)

    def _create_comprehensive_report_prompt(self, company_summary: str) -> str:
        """Create a comprehensive analysis prompt for the LLM."""
        return f"""You are a senior business intelligence analyst specializing in corporate due diligence and risk assessment. Analyze the following Belgian company data from the official KBO (Crossroads Bank for Enterprises) registry and provide a comprehensive business intelligence report.

COMPANY DATA:
{company_summary}

ANALYSIS REQUIREMENTS:
Please provide a detailed analysis covering the following areas. Base your analysis STRICTLY on the provided data - do not make assumptions or add external information.

1. EXECUTIVE SUMMARY
- Provide a concise overview of the company's current status, primary business focus, and key characteristics
- Highlight the most significant findings from the available data
- Assess the company's overall profile and market position based on available information

2. COMPANY PROFILE ANALYSIS
- Analyze the legal structure, establishment history, and operational scale
- Evaluate the significance of the number of establishment units and entity type
- Assess the company's digital presence and communication channels

3. BUSINESS ACTIVITIES ASSESSMENT
- Analyze the registered NACE activities and business scope
- Evaluate business diversification or specialization based on activity codes
- Assess the primary business focus and sector positioning

4. CORPORATE GOVERNANCE EVALUATION
- Analyze the management structure and key personnel
- Evaluate board composition and management committee structure
- Assess governance complexity and leadership stability based on appointment dates
- Identify any notable patterns in management appointments or roles

5. FINANCIAL OVERVIEW
- Analyze the capital structure and financial positioning
- Evaluate the significance of the capital amount in context
- Assess financial reporting practices and fiscal year structure

6. PROFESSIONAL LICENSING & COMPLIANCE
- Analyze professional licenses and authorizations
- Evaluate regulatory compliance indicators
- Assess the scope of licensed activities and their business implications

7. CORPORATE RELATIONSHIPS ANALYSIS
- Analyze entity relationships and corporate connections
- Evaluate the nature and timing of corporate transactions (absorptions, mergers, etc.)
- Assess the corporate network and potential group structure
- Identify patterns in relationship types and their strategic implications

8. REGULATORY COMPLIANCE & TRANSPARENCY
- Evaluate transparency based on available external official links
- Assess regulatory compliance indicators from KBO status
- Analyze the completeness of public filings and disclosures

9. RISK ASSESSMENT
- Identify potential operational, financial, and compliance risks based on available data
- Evaluate information gaps that might require further investigation
- Assess the overall risk profile based on corporate structure and relationships

10. BUSINESS INTELLIGENCE INSIGHTS
- Provide strategic insights about the company's market position
- Evaluate competitive advantages or challenges based on structure and activities
- Assess growth indicators and business development patterns
- Identify key business intelligence findings for stakeholders

11. DATA QUALITY & COMPLETENESS ASSESSMENT
- Evaluate the completeness and quality of available information
- Identify any data gaps or inconsistencies
- Provide recommendations for additional information gathering if needed

IMPORTANT GUIDELINES:
- Base all analysis STRICTLY on the provided KBO data
- Do not make assumptions beyond what the data supports
- Clearly distinguish between facts and analytical interpretations
- Use professional business intelligence language
- Provide specific examples from the data to support your analysis
- If information is not available, state this clearly rather than speculating
- Focus on actionable insights for business intelligence purposes

Generate a comprehensive, professional analysis that would be suitable for due diligence, risk assessment, or business intelligence purposes."""

    def generate_summary_insights(self, kbo_data: Dict[str, Any]) -> str:
        """Generate comprehensive business intelligence insights using LLM."""
        company_summary = self._prepare_company_summary(kbo_data)
        prompt = self._create_comprehensive_report_prompt(company_summary)
        
        logging.info("Generating comprehensive business intelligence report...")
        llm_response = self.llm_client.generate_response(prompt, max_tokens=3000)
        
        # If LLM failed, provide a fallback analysis
        if llm_response.startswith("Error generating response"):
            logging.warning("LLM unavailable, generating fallback analysis...")
            return self._generate_fallback_analysis(kbo_data)
        
        return llm_response

    def generate_markdown_report(self, kbo_data: Dict[str, Any], insights: str) -> str:
        """Generate a comprehensive markdown report."""
        company_name = kbo_data.get("name", "Unknown Company")
        company_id = kbo_data.get("company_id", "Unknown")
        
        # Extract all data sections
        company_overview = self._extract_company_overview(kbo_data)
        registered_activities = self._extract_registered_activities(kbo_data)
        key_people = self._extract_key_people(kbo_data)
        financial_info = self._extract_financial_info(kbo_data)
        entity_links = self._extract_entity_links(kbo_data)
        licenses = self._extract_licenses(kbo_data)
        capacities = self._extract_capacities(kbo_data)
        external_links = self._extract_external_links(kbo_data)
        establishment_info = self._extract_establishment_info(kbo_data)
        official_sources = self._generate_official_sources(kbo_data)
        
        report = f"""# Business Intelligence Report: {company_name}

**Company ID:** {company_id}  
**Report Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

## Executive Summary

{insights}

---

## Company Overview

{company_overview}

---

## Establishment Information

{establishment_info}

---

## Registered Business Activities

{registered_activities}

---

## Key People & Management

{key_people}

---

## Professional Licenses & Authorizations

{licenses}

---

## Legal Capacities

{capacities}

---

## Financial Information

{financial_info}

---

## Entity Relationships

{entity_links}

---

## External Official Links

{external_links}

---

## Official Sources

{chr(10).join(f"- {source}" for source in official_sources)}

---

*This report is generated from official KBO (Crossroads Bank for Enterprises) data and provides comprehensive business intelligence based on publicly available information.*
"""
        
        return report

    def _extract_company_overview(self, kbo_data: Dict[str, Any]) -> str:
        """Extract company overview information from KBO data."""
        overview = {
            "company_name": kbo_data.get("name", "Not available"),
            "enterprise_number": kbo_data.get("company_id", "Not available"),
            "legal_form": kbo_data.get("legal_form", "Not available"),
            "status": kbo_data.get("status", "Not available"),
            "address": kbo_data.get("address_block", "Not available"),
            "website": kbo_data.get("website", "Not available"),
            "establishment_date": kbo_data.get("establishment_date", "Not available"),
            "vat_liable": kbo_data.get("vat_liable", "Not available")
        }
        
        formatted_overview = f"""
**Company Name:** {overview['company_name']}  
**Enterprise Number:** {overview['enterprise_number']}  
**Legal Form:** {overview['legal_form']}  
**Status:** {overview['status']}  
**Address:** {overview['address']}  
**Website:** {overview['website']}  
**Establishment Date:** {overview['establishment_date']}  
**VAT Liable:** {overview['vat_liable']}
        """.strip()
        
        return formatted_overview
    
    def _extract_registered_activities(self, kbo_data: Dict[str, Any]) -> str:
        """Extract registered activities from KBO data."""
        activities = kbo_data.get("btw_activities", [])
        
        if not activities:
            return "No registered activities available."
        
        formatted_activities = []
        for activity in activities:
            nace_code = activity.get("code", "N/A")
            description = activity.get("desc", "N/A")
            classification = activity.get("classification", "")
            
            activity_text = f"- **{nace_code}:** {description}"
            if classification and classification != "Not available":
                activity_text += f" _{classification}_"
            formatted_activities.append(activity_text)
        
        return "\n".join(formatted_activities)
    
    def _extract_key_people(self, kbo_data: Dict[str, Any]) -> str:
        """Extract key people from KBO data."""
        functions = kbo_data.get("functions", [])
        
        if not functions:
            return "No key personnel information available."
        
        formatted_people = []
        for person in functions:
            name = person.get("name", "N/A")
            role = person.get("role", "N/A")
            start_date = person.get("since", "N/A")
            end_date = person.get("end_date", "")
            
            person_text = f"""
### {name}
- **Role:** {role}
- **Start Date:** {start_date}"""
            
            if end_date and end_date != "Not available":
                person_text += f"\n- **End Date:** {end_date}"
            
            formatted_people.append(person_text)
        
        return "\n".join(formatted_people)
    
    def _extract_financial_info(self, kbo_data: Dict[str, Any]) -> str:
        """Extract financial information from KBO data."""
        financial_data = kbo_data.get("financial_data", {})
        
        formatted_financial = f"""
**Capital:** {financial_data.get('capital', 'Not available')}  
**Currency:** {financial_data.get('currency', 'Not available')}  
**Fiscal Year End:** {financial_data.get('fiscal_year_end', 'Not available')}  
**Annual Meeting:** {financial_data.get('annual_meeting', 'Not available')}  
**Last Deposit:** {financial_data.get('last_deposit', 'Not available')}
        """.strip()
        
        return formatted_financial
    
    def _extract_entity_links(self, kbo_data: Dict[str, Any]) -> str:
        """Extract entity links from KBO data with enhanced relationship details."""
        entity_links = kbo_data.get("entity_links", [])
        
        if not entity_links:
            return "No entity relationships available."
        
        formatted_links = []
        for link in entity_links:
            entity_name = link.get("name", "N/A")
            entity_number = link.get("number", "N/A")
            relationship = link.get("relationship", "N/A")
            since_date = link.get("since", "N/A")
            
            link_text = f"""
### {entity_name}
- **Entity Number:** {entity_number}
- **Relationship Type:** {relationship}
- **Since:** {since_date}"""
            
            formatted_links.append(link_text)
        
        return "\n".join(formatted_links)

    def _extract_licenses(self, kbo_data: Dict[str, Any]) -> str:
        """Extract professional licenses and authorizations."""
        licenses = kbo_data.get("licenses", [])
        
        if not licenses:
            return "No professional licenses registered."
        
        formatted_licenses = []
        for license_info in licenses:
            if isinstance(license_info, str):
                formatted_licenses.append(f"- {license_info}")
        
        return "\n".join(formatted_licenses) if formatted_licenses else "No professional licenses registered."

    def _extract_capacities(self, kbo_data: Dict[str, Any]) -> str:
        """Extract legal capacities and functions."""
        capacities = kbo_data.get("capacities", [])
        
        if not capacities:
            return "No legal capacities information available."
        
        formatted_capacities = []
        for capacity in capacities:
            if isinstance(capacity, str) and not capacity.startswith("There are"):
                formatted_capacities.append(f"- {capacity}")
        
        return "\n".join(formatted_capacities) if formatted_capacities else "No detailed legal capacities available."

    def _extract_external_links(self, kbo_data: Dict[str, Any]) -> str:
        """Extract external official links and resources."""
        external_links = kbo_data.get("external_links", [])
        
        if not external_links:
            return "No external official links available."
        
        formatted_links = []
        for link in external_links:
            label = link.get("label", "Unknown")
            url = link.get("url", "#")
            formatted_links.append(f"- **{label}:** {url}")
        
        return "\n".join(formatted_links)

    def _extract_establishment_info(self, kbo_data: Dict[str, Any]) -> str:
        """Extract establishment and operational information."""
        info_parts = []
        
        # Basic establishment info
        establishment_units = kbo_data.get("establishment_units", "N/A")
        entity_type = kbo_data.get("entity_type", "N/A")
        start_date = kbo_data.get("start_date", "N/A")
        
        info_parts.append(f"**Entity Type:** {entity_type}")
        info_parts.append(f"**Start Date:** {start_date}")
        info_parts.append(f"**Establishment Units:** {establishment_units}")
        
        # Contact information
        website = kbo_data.get("website")
        email = kbo_data.get("email")
        phone = kbo_data.get("phone")
        
        if website:
            info_parts.append(f"**Website:** {website}")
        if email:
            info_parts.append(f"**Email:** {email}")
        if phone:
            info_parts.append(f"**Phone:** {phone}")
        
        # VAT information
        vat_number = kbo_data.get("vat_number")
        if vat_number:
            info_parts.append(f"**VAT Number:** {vat_number}")
        
        return "\n".join(info_parts)

    def _generate_fallback_analysis(self, kbo_data: Dict[str, Any]) -> str:
        """Generate a fallback analysis when LLM is not available."""
        company_name = kbo_data.get("name", "Unknown Company")
        legal_form = kbo_data.get("legal_form", "Unknown")
        status = kbo_data.get("status", "Unknown")
        
        # Extract primary activity
        activities = kbo_data.get("btw_activities", [])
        primary_activity = "Unknown"
        if activities:
            primary_activity = activities[0].get("desc", "Unknown")
        
        # Count key people
        functions = kbo_data.get("functions", [])
        people_count = len(functions)
        
        # Extract capital info
        financial_data = kbo_data.get("financial_data", {})
        capital = financial_data.get("capital", "Not available")
        
        # Count entity links
        entity_links = kbo_data.get("entity_links", [])
        links_count = len(entity_links)
        
        fallback_analysis = f"""
## 1. EXECUTIVE SUMMARY
{company_name} is a {legal_form.lower()} registered in Belgium with enterprise number {kbo_data.get("company_id", "Unknown")}. The company is currently {status.lower()} and operates primarily in {primary_activity.lower()}.

## 2. COMPANY PROFILE
The company is legally established as a {legal_form} and maintains {status.lower()} status in the Belgian company registry. The registered address is {kbo_data.get("address_block", "Not available")}.

## 3. BUSINESS ACTIVITIES ANALYSIS
The company's primary registered activity is {primary_activity}. The company has {len(activities)} registered NACE activities, indicating {"a focused business scope" if len(activities) <= 3 else "a diversified business scope"}.

## 4. CORPORATE GOVERNANCE
The company has {people_count} registered {"person" if people_count == 1 else "people"} in key positions. {"Management structure appears minimal" if people_count <= 2 else "Management structure shows appropriate governance"}.

## 5. FINANCIAL OVERVIEW
{"Share capital information is not available" if capital == "Not available" else f"The company has registered capital of {capital}"}. Fiscal year end is {financial_data.get("fiscal_year_end", "not specified")}.

## 6. CORPORATE RELATIONSHIPS
The company has {links_count} registered entity {"relationship" if links_count == 1 else "relationships"}. {"This suggests an independent entity" if links_count == 0 else "This indicates corporate connections that may require further analysis"}.

## 7. REGULATORY COMPLIANCE
The company maintains active registration with the KBO registry and appears to be in compliance with basic regulatory requirements based on its {status.lower()} status.

## 8. RISK ASSESSMENT
Based on available data:
- Operational risks: {"Limited information available for assessment" if not activities else "Standard risks associated with " + primary_activity.lower()}
- Compliance considerations: Standard Belgian corporate compliance requirements apply
- Information gaps: {"Minimal financial data available" if capital == "Not available" else "Financial information partially available"}

## 9. BUSINESS INTELLIGENCE INSIGHTS
- Market positioning: Company operates in {primary_activity.lower()} sector
- Corporate structure: {legal_form} structure with {"simple" if links_count == 0 else "connected"} ownership
- Scale indicators: {"Small to medium enterprise based on available data" if people_count <= 5 else "Larger enterprise based on management structure"}

## 10. DATA QUALITY ASSESSMENT
- Information completeness: {"Basic" if capital == "Not available" else "Good"} level of data available
- Data reliability: Official KBO registry data - high reliability
- Recommendations: {"Consider obtaining additional financial filings" if capital == "Not available" else "Data appears comprehensive for basic analysis"}

Analysis based solely on KBO registry data. No external assumptions added.
        """.strip()
        
        return fallback_analysis

    def _generate_official_sources(self, kbo_data: Dict[str, Any]) -> List[str]:
        """Generate official source URLs using company ID."""
        company_id = kbo_data.get("company_id", "").replace(".", "")
        
        if not company_id:
            return ["Company ID not available - cannot generate official source URLs"]
        
        return [
            f"https://kbopub.economie.fgov.be/kbopub/zoeknummerform.html?nummer={company_id}",
            f"https://consult.cbso.nbb.be/consult-enterprise/{company_id}",
            f"https://www.ejustice.just.fgov.be/cgi_tsv/list.pl?btw={company_id}"
        ]

    def process_kbo_file(self, input_file: str, output_dir: str) -> bool:
        """Process a single KBO JSON file and generate report."""
        try:
            logging.info(f"Processing KBO file: {input_file}")
            
            # Load KBO data
            kbo_data = self.load_kbo_data(input_file)
            if not kbo_data:
                logging.error(f"Failed to load data from {input_file}")
                return False
            
            # Generate insights
            insights = self.generate_summary_insights(kbo_data)
            
            # Create output structure
            company_id = kbo_data.get("company_id", "unknown").replace(".", "_")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Generate reports
            report_data = {
                "company_data": kbo_data,
                "insights": insights,
                "generated_at": datetime.now().isoformat(),
                "source_file": input_file
            }
            
            markdown_report = self.generate_markdown_report(kbo_data, insights)
            
            # Save outputs
            os.makedirs(output_dir, exist_ok=True)
            
            # Save JSON report
            json_output = os.path.join(output_dir, f"kbo_report_{company_id}_{timestamp}.json")
            with open(json_output, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            
            # Save Markdown report
            md_output = os.path.join(output_dir, f"kbo_report_{company_id}_{timestamp}.md")
            with open(md_output, 'w', encoding='utf-8') as f:
                f.write(markdown_report)
            
            logging.info(f"Reports generated successfully:")
            logging.info(f"  JSON: {json_output}")
            logging.info(f"  Markdown: {md_output}")
            
            return True
            
        except Exception as e:
            logging.error(f"Error processing {input_file}: {e}")
            return False

    def process_kbo_directory(self, input_dir: str, output_dir: str) -> int:
        """Process all KBO JSON files in a directory."""
        processed_count = 0
        
        if not os.path.exists(input_dir):
            logging.error(f"Input directory does not exist: {input_dir}")
            return 0
        
        json_files = [f for f in os.listdir(input_dir) if f.endswith('.json')]
        
        if not json_files:
            logging.warning(f"No JSON files found in {input_dir}")
            return 0
        
        logging.info(f"Found {len(json_files)} JSON files to process")
        
        for json_file in json_files:
            input_file = os.path.join(input_dir, json_file)
            if self.process_kbo_file(input_file, output_dir):
                processed_count += 1
        
        logging.info(f"Successfully processed {processed_count}/{len(json_files)} files")
        return processed_count

def main():
    """Main function with automatic path detection."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Get script directory and set default paths
    script_dir = Path(__file__).parent
    default_input_dir = script_dir / "output" / "kbo"
    default_output_dir = script_dir / "output" / "reports"
    
    # Create directories if they don't exist
    default_input_dir.mkdir(parents=True, exist_ok=True)
    default_output_dir.mkdir(parents=True, exist_ok=True)
    
    input_path = str(default_input_dir)
    output_path = str(default_output_dir)
    
    logging.info("=== KBO Report Generator ===")
    logging.info(f"Input directory: {input_path}")
    logging.info(f"Output directory: {output_path}")
    
    # Initialize LLM client
    try:
        llm_client = LLMClient()
        logging.info("LLM client initialized successfully")
    except Exception as e:
        logging.error(f"Failed to initialize LLM client: {e}")
        return
    
    # Initialize report generator
    generator = KBOReportGenerator(llm_client)
    
    # Process files
    if os.path.isfile(input_path):
        # Single file processing
        success = generator.process_kbo_file(input_path, output_path)
        if success:
            logging.info("Report generation completed successfully")
        else:
            logging.error("Report generation failed")
    else:
        # Directory processing
        processed_count = generator.process_kbo_directory(input_path, output_path)
        if processed_count > 0:
            logging.info(f"Successfully generated reports for {processed_count} companies")
        else:
            logging.warning("No reports were generated")

if __name__ == "__main__":
    main()