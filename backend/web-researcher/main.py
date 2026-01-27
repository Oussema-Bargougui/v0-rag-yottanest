"""
VAT Validation & KBO Data REST API Server
==========================================

This module provides a FastAPI-based REST API for:
1. Validating European VAT numbers using the EU VIES service
2. Fetching detailed company data from the Belgian KBO database

Endpoints:
    POST /api/vat/validate  - Validate a VAT number via EU VIES
    GET  /api/vat/kbo-data  - Fetch detailed KBO data for Belgian companies
    GET  /api/health        - Health check endpoint

Dependencies:
    - zeep: For SOAP communication with EU VIES
    - crawl4ai: For web scraping KBO data (via subprocess)

Author: Yottanest Team
Version: 1.0.0
"""

from fastapi import FastAPI, HTTPException, Query, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import re
import subprocess
import json
import os
from pathlib import Path

from zeep import Client
from zeep.exceptions import Fault, TransportError

# Import RAG service
from rag_service import get_rag_service, ProcessingStage

# =============================================================================
# FastAPI Application Configuration
# =============================================================================

app = FastAPI(
    title="Yottanest VAT Validation API",
    description="REST API for validating European VAT numbers using EU VIES service",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# -----------------------------------------------------------------------------
# CORS Configuration
# Allow requests from the frontend application
# -----------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",      # Next.js development server
        "http://127.0.0.1:3000",      # Alternative localhost
        "http://localhost:3001",      # Alternative port
    ],
    allow_credentials=True,
    allow_methods=["*"],              # Allow all HTTP methods
    allow_headers=["*"],              # Allow all headers
)

# =============================================================================
# Pydantic Models (Request/Response Schemas)
# =============================================================================

class VATValidationRequest(BaseModel):
    """
    Request model for VAT validation.

    Attributes:
        country_code: Two-letter EU country code (e.g., 'BE', 'FR', 'DE')
        vat_number: The VAT number without the country prefix
        company_name: Optional company name for additional context
    """
    country_code: str = Field(
        ...,
        min_length=2,
        max_length=2,
        description="Two-letter EU country code (e.g., BE, FR, DE)"
    )
    vat_number: str = Field(
        ...,
        min_length=1,
        description="VAT number without country prefix"
    )
    company_name: Optional[str] = Field(
        None,
        description="Optional company name for reference"
    )


class VATValidationResponse(BaseModel):
    """
    Response model for VAT validation results.

    Attributes:
        valid: Whether the VAT number is valid
        country_code: The validated country code
        vat_number: The validated VAT number
        full_vat_number: Complete VAT number with country prefix
        company_name: Registered company name from VIES
        address: Registered company address from VIES
        request_company_name: Company name provided in the request (if any)
        timestamp: Timestamp of the validation
        error: Error message if validation failed
    """
    valid: bool
    country_code: str
    vat_number: str
    full_vat_number: str
    company_name: str
    address: str
    request_company_name: Optional[str] = None
    timestamp: str
    error: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    timestamp: str
    service: str


# -----------------------------------------------------------------------------
# KBO Data Response Models
# -----------------------------------------------------------------------------

class BTWActivity(BaseModel):
    """BTW/VAT activity model."""
    version: Optional[str] = None
    code: Optional[str] = None
    desc: Optional[str] = None
    since: Optional[str] = None


class RSZActivity(BaseModel):
    """RSZ/NSSO activity model."""
    version: Optional[str] = None
    code: Optional[str] = None
    desc: Optional[str] = None
    since: Optional[str] = None


class FinancialData(BaseModel):
    """Financial information model."""
    capital: Optional[str] = None
    annual_meeting: Optional[str] = None
    fiscal_year_end: Optional[str] = None


class EntityLink(BaseModel):
    """Related entity link model."""
    number: Optional[str] = None
    name: Optional[str] = None
    relationship: Optional[str] = None
    since: Optional[str] = None


class ExternalLink(BaseModel):
    """External reference link model."""
    label: Optional[str] = None
    url: Optional[str] = None


class FunctionHolder(BaseModel):
    """Function/role holder model."""
    role: Optional[str] = None
    name: Optional[str] = None
    since: Optional[str] = None


class KBODataResponse(BaseModel):
    """
    Response model for KBO company data scraped from Belgian KBO database.
    """
    company_id: Optional[str] = None
    name: Optional[str] = None
    status: Optional[str] = None
    legal_status: Optional[str] = None
    legal_form: Optional[str] = None
    start_date: Optional[str] = None
    address_block: Optional[str] = None
    website: Optional[str] = None
    phone: Optional[str] = None
    fax: Optional[str] = None
    email: Optional[str] = None
    entity_type: Optional[str] = None
    establishment_units: Optional[str] = None
    functions: List[Any] = []
    entrepreneurial_skills: List[str] = []
    capacities: List[str] = []
    licenses: List[str] = []
    btw_activities: List[BTWActivity] = []
    rsz_activities: List[RSZActivity] = []
    financial_data: Optional[FinancialData] = None
    entity_links: List[EntityLink] = []
    external_links: List[ExternalLink] = []
    vat_number: Optional[str] = None
    vat_formatted: Optional[str] = None
    source_url: Optional[str] = None
    engine: Optional[str] = None
    error: Optional[str] = None


# =============================================================================
# Helper Functions
# =============================================================================

def clean_vat_number(vat_number: str) -> str:
    """
    Clean and normalize a VAT number by removing spaces, dots, and hyphens.

    Args:
        vat_number: Raw VAT number string

    Returns:
        Cleaned VAT number string
    """
    return re.sub(r'[\s\.\-]', '', vat_number)


def format_address(address: str) -> str:
    """
    Format the address string for better readability.
    Replaces newlines with commas and cleans up whitespace.

    Args:
        address: Raw address string from VIES

    Returns:
        Formatted address string
    """
    if not address or address == "Not available":
        return "Not available"

    # Replace multiple newlines/spaces with single comma-space
    formatted = re.sub(r'\n+', ', ', address.strip())
    formatted = re.sub(r'\s+', ' ', formatted)
    return formatted


# =============================================================================
# API Endpoints
# =============================================================================

@app.get("/api/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """
    Health check endpoint to verify the API is running.

    Returns:
        HealthResponse with status and timestamp
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        service="vat-validation-api"
    )


@app.post("/api/vat/validate", response_model=VATValidationResponse, tags=["VAT Validation"])
async def validate_vat(request: VATValidationRequest):
    """
    Validate a European VAT number using the EU VIES service.

    This endpoint connects to the official EU VAT Information Exchange System (VIES)
    to verify VAT numbers and retrieve registered company information.

    Args:
        request: VATValidationRequest containing country_code and vat_number

    Returns:
        VATValidationResponse with validation results and company information

    Raises:
        HTTPException: If the VIES service is unavailable or an error occurs
    """
    try:
        # Normalize input data
        country_code = request.country_code.upper().strip()
        vat_number = clean_vat_number(request.vat_number)

        # Validate country code format
        valid_country_codes = [
            "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR",
            "DE", "EL", "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL",
            "PL", "PT", "RO", "SK", "SI", "ES", "SE", "XI"
        ]

        if country_code not in valid_country_codes:
            return VATValidationResponse(
                valid=False,
                country_code=country_code,
                vat_number=vat_number,
                full_vat_number=f"{country_code}{vat_number}",
                company_name="Not available",
                address="Not available",
                request_company_name=request.company_name,
                timestamp=datetime.now().isoformat(),
                error=f"Invalid country code: {country_code}"
            )

        # Connect to EU VIES SOAP service
        wsdl_url = "https://ec.europa.eu/taxation_customs/vies/checkVatService.wsdl"
        client = Client(wsdl_url)

        # Call the VIES checkVat service
        response = client.service.checkVat(
            countryCode=country_code,
            vatNumber=vat_number
        )

        # Extract and format the response data
        company_name = response.name if response.name else "Not available"
        address = format_address(response.address) if response.address else "Not available"

        return VATValidationResponse(
            valid=bool(response.valid),
            country_code=response.countryCode,
            vat_number=response.vatNumber,
            full_vat_number=f"{response.countryCode}{response.vatNumber}",
            company_name=company_name,
            address=address,
            request_company_name=request.company_name,
            timestamp=datetime.now().isoformat(),
            error=None
        )

    except Fault as e:
        # SOAP Fault - usually means invalid VAT format or service error
        error_message = str(e)

        # Handle specific VIES error codes
        if "INVALID_INPUT" in error_message:
            error_message = "Invalid VAT number format for the specified country"
        elif "SERVICE_UNAVAILABLE" in error_message:
            error_message = "VIES service is temporarily unavailable. Please try again later."
        elif "MS_UNAVAILABLE" in error_message:
            error_message = "The member state's VAT database is temporarily unavailable"
        elif "TIMEOUT" in error_message:
            error_message = "Request timed out. Please try again."

        return VATValidationResponse(
            valid=False,
            country_code=request.country_code.upper(),
            vat_number=clean_vat_number(request.vat_number),
            full_vat_number=f"{request.country_code.upper()}{clean_vat_number(request.vat_number)}",
            company_name="Not available",
            address="Not available",
            request_company_name=request.company_name,
            timestamp=datetime.now().isoformat(),
            error=error_message
        )

    except TransportError as e:
        # Network/connection error
        raise HTTPException(
            status_code=503,
            detail={
                "error": "Unable to connect to VIES service",
                "message": "The EU VAT validation service is currently unreachable. Please try again later.",
                "timestamp": datetime.now().isoformat()
            }
        )

    except Exception as e:
        # Unexpected error
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )


@app.get("/api/vat/kbo-data", response_model=KBODataResponse, tags=["VAT Validation"])
async def get_kbo_data(
    vat_number: str = Query(..., description="Full VAT number including country prefix (e.g., BE0403170701)")
):
    """
    Fetch detailed company information from the Belgian KBO database.

    This endpoint scrapes the KBO (Kruispuntbank van Ondernemingen) public database
    to retrieve comprehensive company information including:
    - Basic company details (name, status, legal form)
    - Contact information (address, phone, email, website)
    - Business activities (BTW/VAT and RSZ/NSSO codes)
    - Financial information (capital, fiscal year)
    - Related entities and external links

    Note: This endpoint only works for Belgian (BE) VAT numbers.

    Args:
        vat_number: Full VAT number with country prefix (e.g., BE0403170701)

    Returns:
        KBODataResponse with comprehensive company information from KBO database

    Raises:
        HTTPException: If the VAT number is invalid or scraping fails
    """
    try:
        # Validate that it's a Belgian VAT number
        vat_upper = vat_number.upper().strip()

        # Remove spaces, dots, and hyphens
        vat_clean = re.sub(r'[\s\.\-]', '', vat_upper)

        # Check for BE prefix
        if not vat_clean.startswith("BE"):
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Invalid country code",
                    "message": "KBO data is only available for Belgian (BE) VAT numbers",
                    "timestamp": datetime.now().isoformat()
                }
            )

        # Extract the number part (remove BE prefix)
        vat_digits = vat_clean[2:]

        # Validate format (should be 10 digits)
        if not vat_digits.isdigit():
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Invalid VAT format",
                    "message": "VAT number should contain only digits after the country code",
                    "timestamp": datetime.now().isoformat()
                }
            )

        # Format VAT number for filename (remove dots)
        vat_for_filename = vat_digits.replace(".", "")
        if len(vat_for_filename) < 10:
            vat_for_filename = vat_for_filename.zfill(10)

        # Get the directory where this script is located
        script_dir = Path(__file__).parent.absolute()
        output_dir = script_dir / "output" / "kbo"
        json_file = output_dir / f"kbo_{vat_for_filename}.json"

        # Create output directory if it doesn't exist
        output_dir.mkdir(parents=True, exist_ok=True)

        # Run the vat_search.py script as a subprocess
        vat_search_script = script_dir / "vat_search.py"

        try:
            # Set environment variables to fix Windows encoding issues
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            env["PYTHONLEGACYWINDOWSSTDIO"] = "0"

            # Run the script with the VAT number
            # Use encoding="utf-8" to handle Unicode characters properly on Windows
            process = subprocess.run(
                ["python", str(vat_search_script), vat_digits],
                cwd=str(script_dir),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",  # Replace invalid characters instead of failing
                timeout=120,  # 2 minute timeout
                env=env
            )

            # Log script output for debugging (only if there's meaningful output)
            if process.stdout and process.stdout.strip():
                print(f"[INFO] Script output: {process.stdout.strip()}")
            if process.stderr and process.stderr.strip():
                print(f"[WARNING] Script stderr: {process.stderr.strip()}")

            # Check if the script ran successfully
            if process.returncode != 0:
                print(f"[ERROR] Script failed with return code: {process.returncode}")
                # Continue anyway, maybe the JSON file was still created

        except subprocess.TimeoutExpired:
            raise HTTPException(
                status_code=504,
                detail={
                    "error": "Timeout",
                    "message": "KBO scraping took too long. Please try again.",
                    "timestamp": datetime.now().isoformat()
                }
            )
        except Exception as e:
            print(f"[ERROR] Failed to run script: {str(e)}")

        # Read the JSON file
        if not json_file.exists():
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "File not found",
                    "message": f"KBO data file was not created. The scraper may have failed.",
                    "timestamp": datetime.now().isoformat()
                }
            )

        with open(json_file, "r", encoding="utf-8") as f:
            result = json.load(f)

        # Transform the result to match our response model
        # Handle functions which can be either strings or dicts
        functions = result.get("functions", [])

        # Handle BTW activities
        btw_activities = []
        for activity in result.get("btw_activities", []):
            if isinstance(activity, dict):
                btw_activities.append(BTWActivity(**activity))

        # Handle RSZ activities
        rsz_activities = []
        for activity in result.get("rsz_activities", []):
            if isinstance(activity, dict):
                rsz_activities.append(RSZActivity(**activity))

        # Handle financial data
        financial_data = None
        if result.get("financial_data"):
            financial_data = FinancialData(**result["financial_data"])

        # Handle entity links
        entity_links = []
        for link in result.get("entity_links", []):
            if isinstance(link, dict):
                entity_links.append(EntityLink(**link))

        # Handle external links
        external_links = []
        for link in result.get("external_links", []):
            if isinstance(link, dict):
                external_links.append(ExternalLink(**link))

        return KBODataResponse(
            company_id=result.get("company_id"),
            name=result.get("name"),
            status=result.get("status"),
            legal_status=result.get("legal_status"),
            legal_form=result.get("legal_form"),
            start_date=result.get("start_date"),
            address_block=result.get("address_block"),
            website=result.get("website"),
            phone=result.get("phone"),
            fax=result.get("fax"),
            email=result.get("email"),
            entity_type=result.get("entity_type"),
            establishment_units=result.get("establishment_units"),
            functions=functions,
            entrepreneurial_skills=result.get("entrepreneurial_skills", []),
            capacities=result.get("capacities", []),
            licenses=result.get("licenses", []),
            btw_activities=btw_activities,
            rsz_activities=rsz_activities,
            financial_data=financial_data,
            entity_links=entity_links,
            external_links=external_links,
            vat_number=result.get("vat_number"),
            vat_formatted=result.get("vat_formatted"),
            source_url=result.get("source_url"),
            engine=result.get("engine"),
            error=result.get("error")
        )

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise

    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=500,
            detail={
                "error": "KBO scraping failed",
                "message": f"Failed to retrieve KBO data: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
        )


# =============================================================================
# Company Summary Endpoint (AI-Powered KYC/AML Analysis)
# =============================================================================

class CompanySummaryResponse(BaseModel):
    """Response model for AI-generated company summary."""
    vat_number: str
    company_name: Optional[str] = None
    summary: str
    generated_at: str
    model: str = "llama3.1"
    error: Optional[str] = None


def _generate_kyc_summary_prompt(kbo_data: Dict[str, Any]) -> str:
    """
    Generate a simplified prompt for KYC/AML company summary.

    This prompt is designed to get a concise, actionable summary
    for compliance analysts reviewing a company.
    """
    # Extract key information
    company_name = kbo_data.get("name", "Unknown")
    company_id = kbo_data.get("company_id", "Unknown")
    legal_form = kbo_data.get("legal_form", "Unknown")
    status = kbo_data.get("status", "Unknown")
    legal_status = kbo_data.get("legal_status", "Unknown")
    start_date = kbo_data.get("start_date", "Unknown")
    address = kbo_data.get("address_block", "Unknown")
    entity_type = kbo_data.get("entity_type", "Unknown")
    establishment_units = kbo_data.get("establishment_units", "0")

    # Business activities
    activities = kbo_data.get("btw_activities", [])
    activities_text = "None registered"
    if activities:
        activities_text = ", ".join([
            f"{a.get('code', 'N/A')}: {a.get('desc', 'N/A')}"
            for a in activities[:3]
        ])

    # Key people count
    functions = kbo_data.get("functions", [])
    people_count = len(functions)

    # Directors list
    directors = [f.get("name", "Unknown") for f in functions if "Director" in str(f.get("role", ""))][:5]
    directors_text = ", ".join(directors) if directors else "Not available"

    # Financial info
    financial = kbo_data.get("financial_data", {})
    capital = financial.get("capital", "Not disclosed")

    # Entity links
    entity_links = kbo_data.get("entity_links", [])
    links_count = len(entity_links)

    prompt = f"""You are a KYC/AML compliance analyst. Based on the following Belgian company data from the official KBO registry, provide a brief compliance summary.

COMPANY DATA:
- Name: {company_name}
- Enterprise Number: {company_id}
- Legal Form: {legal_form}
- Status: {status}
- Legal Status: {legal_status}
- Start Date: {start_date}
- Address: {address}
- Entity Type: {entity_type}
- Establishment Units: {establishment_units}
- Business Activities: {activities_text}
- Key People Count: {people_count}
- Directors: {directors_text}
- Registered Capital: {capital}
- Corporate Relationships: {links_count}

PROVIDE A BRIEF SUMMARY (3-4 paragraphs) COVERING:

1. **Company Overview**: What is this company? What do they do? How long have they been operating?

2. **KYC Assessment**: Key points for Know Your Customer compliance - legal structure, ownership indicators, business legitimacy signals.

3. **AML Considerations**: Any red flags or points requiring further investigation? Missing information that should be obtained?

4. **Recommendation**: Overall risk level (Low/Medium/High) and next steps for due diligence.

Keep the summary concise and actionable. Focus on facts from the data provided. If information is missing, clearly state what additional documentation should be requested."""

    return prompt


def _call_ollama(prompt: str, model: str = "llama3.1:latest") -> str:
    """
    Call local Ollama API to generate response.

    Args:
        prompt: The prompt to send to the model
        model: Ollama model name (default: llama3.1:latest)

    Returns:
        Generated text response or error message
    """
    import requests as req

    try:
        response = req.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": 1000,
                    "temperature": 0.7
                }
            },
            timeout=120
        )
        response.raise_for_status()
        return response.json().get("response", "").strip()
    except req.exceptions.ConnectionError:
        return "Error: Cannot connect to Ollama. Please ensure Ollama is running (ollama serve)."
    except req.exceptions.Timeout:
        return "Error: Request to Ollama timed out. The model may be loading or overloaded."
    except Exception as e:
        return f"Error: {str(e)}"


@app.post("/api/vat/company-summary", response_model=CompanySummaryResponse, tags=["Company Analysis"])
async def generate_company_summary(
    vat_number: str = Query(..., description="Full VAT number including country prefix (e.g., BE0403170701)")
):
    """
    Generate an AI-powered KYC/AML summary for a Belgian company.

    This endpoint:
    1. Reads the KBO data from the previously scraped JSON file
    2. Sends key company information to local Llama 3.1 model
    3. Returns a concise compliance-focused summary

    Prerequisites:
    - The company must have been previously scraped via /api/vat/kbo-data
    - Ollama must be running locally with llama3.1 model installed

    Args:
        vat_number: Full VAT number with country prefix (e.g., BE0403170701)

    Returns:
        CompanySummaryResponse with AI-generated KYC/AML summary
    """
    try:
        # Clean VAT number
        vat_clean = re.sub(r"[^0-9]", "", vat_number.upper().replace("BE", ""))
        if len(vat_clean) < 10:
            vat_clean = vat_clean.zfill(10)

        # Get the directory where this script is located
        script_dir = Path(__file__).parent.absolute()
        json_file = script_dir / "output" / "kbo" / f"kbo_{vat_clean}.json"

        # Check if KBO data file exists
        if not json_file.exists():
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "KBO data not found",
                    "message": "Please fetch KBO data first using /api/vat/kbo-data endpoint",
                    "timestamp": datetime.now().isoformat()
                }
            )

        # Load KBO data
        with open(json_file, "r", encoding="utf-8") as f:
            kbo_data = json.load(f)

        # Generate prompt
        prompt = _generate_kyc_summary_prompt(kbo_data)

        # Call Ollama
        print(f"[INFO] Generating company summary for {vat_number}...")
        summary = _call_ollama(prompt)

        # Check for errors
        error = None
        if summary.startswith("Error:"):
            error = summary
            summary = "Unable to generate AI summary. Please ensure Ollama is running with llama3.1 model."

        return CompanySummaryResponse(
            vat_number=vat_number,
            company_name=kbo_data.get("name"),
            summary=summary,
            generated_at=datetime.now().isoformat(),
            model="llama3.1",
            error=error
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Summary generation failed",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )


# =============================================================================
# RAG Document Processing Endpoints
# =============================================================================

# -----------------------------------------------------------------------------
# RAG Pydantic Models
# -----------------------------------------------------------------------------

class RAGSessionResponse(BaseModel):
    """Response model for session creation."""
    session_id: str
    message: str
    created_at: str


class RAGUploadResponse(BaseModel):
    """Response model for file upload."""
    session_id: str
    filename: str
    size: int
    message: str


class RAGProcessingStatus(BaseModel):
    """Response model for processing status."""
    session_id: str
    found: bool
    stage: str
    progress: int
    message: str
    error: Optional[str] = None
    files_count: int = 0
    documents_processed: int = 0


class RAGQueryRequest(BaseModel):
    """Request model for document query."""
    query: str = Field(..., min_length=1, description="Question to ask about the documents")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of relevant chunks to retrieve")


class RAGSourceInfo(BaseModel):
    """Source information for a retrieved chunk."""
    filename: str
    chunk_id: int
    similarity_score: float
    text_preview: str


class RAGQueryResponse(BaseModel):
    """Response model for document query."""
    success: bool
    answer: str
    sources: List[RAGSourceInfo] = []
    query: str
    chunks_used: int = 0
    model: str = "llama3.1"
    error: Optional[str] = None


class RAGProcessResponse(BaseModel):
    """Response model for document processing."""
    success: bool
    session_id: str
    documents_processed: int = 0
    chunks_created: int = 0
    embeddings_generated: int = 0
    message: str = ""
    error: Optional[str] = None


# -----------------------------------------------------------------------------
# RAG Endpoints
# -----------------------------------------------------------------------------

@app.post("/api/rag/upload", response_model=RAGUploadResponse, tags=["RAG Documents"])
async def upload_document(
    file: UploadFile = File(..., description="PDF or text file to upload"),
    session_id: Optional[str] = Query(None, description="Existing session ID (creates new if not provided)")
):
    """
    Upload a document for RAG processing.

    Upload PDF or text files to be processed and indexed for question answering.
    If no session_id is provided, a new session will be created.

    Supported file types: PDF, TXT, MD
    """
    try:
        rag_service = get_rag_service()

        # Create new session if needed
        if not session_id:
            session_id = rag_service.create_session()

        # Validate session exists
        session = rag_service.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=404,
                detail={"error": "Session not found", "session_id": session_id}
            )

        # Validate file type
        filename = file.filename or "unknown"
        extension = Path(filename).suffix.lower()

        if extension not in ['.pdf', '.txt', '.md', '.text']:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Unsupported file type",
                    "message": f"File type '{extension}' is not supported. Please upload PDF, TXT, or MD files.",
                    "supported_types": [".pdf", ".txt", ".md"]
                }
            )

        # Read file content
        content = await file.read()

        if len(content) == 0:
            raise HTTPException(
                status_code=400,
                detail={"error": "Empty file", "message": "The uploaded file is empty."}
            )

        # Save file to session
        file_info = rag_service.save_uploaded_file(session_id, filename, content)

        return RAGUploadResponse(
            session_id=session_id,
            filename=filename,
            size=len(content),
            message=f"File '{filename}' uploaded successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "Upload failed", "message": str(e)}
        )


@app.post("/api/rag/process", response_model=RAGProcessResponse, tags=["RAG Documents"])
async def process_documents(
    session_id: str = Query(..., description="Session ID containing uploaded documents")
):
    """
    Process uploaded documents through the RAG pipeline.

    This endpoint triggers the document processing pipeline:
    1. Extract text from PDFs
    2. Clean and preprocess text
    3. Split into chunks
    4. Generate embeddings
    5. Build vector store
    """
    try:
        rag_service = get_rag_service()

        # Validate session exists
        session = rag_service.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=404,
                detail={"error": "Session not found", "session_id": session_id}
            )

        if not session.uploaded_files:
            raise HTTPException(
                status_code=400,
                detail={"error": "No files uploaded", "message": "Please upload documents before processing."}
            )

        # Process documents
        result = rag_service.process_documents(session_id)

        return RAGProcessResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "Processing failed", "message": str(e)}
        )


@app.get("/api/rag/status/{session_id}", response_model=RAGProcessingStatus, tags=["RAG Documents"])
async def get_processing_status(session_id: str):
    """
    Get the current processing status for a session.

    Processing stages: idle, uploading, extracting, cleaning, chunking, embedding, storing, ready, error
    """
    rag_service = get_rag_service()
    status = rag_service.get_processing_status(session_id)

    return RAGProcessingStatus(
        session_id=session_id,
        found=status.get("found", False),
        stage=status.get("stage", "unknown"),
        progress=status.get("progress", 0),
        message=status.get("message", ""),
        error=status.get("error"),
        files_count=status.get("files_count", 0),
        documents_processed=status.get("documents_processed", 0)
    )


@app.post("/api/rag/query", response_model=RAGQueryResponse, tags=["RAG Documents"])
async def query_documents(
    session_id: str = Query(..., description="Session ID with processed documents"),
    request: RAGQueryRequest = None
):
    """
    Query processed documents and get an AI-generated answer.

    Ask questions about the uploaded documents. The system will:
    1. Find relevant document chunks using semantic search
    2. Generate an answer using Llama 3.1 based on the context
    3. Return the answer with source citations
    """
    try:
        rag_service = get_rag_service()

        # Validate session exists and is ready
        session = rag_service.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=404,
                detail={"error": "Session not found", "session_id": session_id}
            )

        if session.stage != ProcessingStage.READY:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Documents not ready",
                    "message": f"Current stage: {session.stage.value}. Please process documents first.",
                    "stage": session.stage.value
                }
            )

        # Query documents
        result = rag_service.query_documents(
            session_id=session_id,
            query=request.query,
            top_k=request.top_k
        )

        # Convert sources to response model
        sources = []
        for source in result.get("sources", []):
            sources.append(RAGSourceInfo(
                filename=source.get("filename", "Unknown"),
                chunk_id=source.get("chunk_id", 0),
                similarity_score=source.get("similarity_score", 0),
                text_preview=source.get("text_preview", "")
            ))

        return RAGQueryResponse(
            success=result.get("success", False),
            answer=result.get("answer", ""),
            sources=sources,
            query=request.query,
            chunks_used=result.get("chunks_used", 0),
            model=result.get("model", "llama3.1"),
            error=result.get("error")
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "Query failed", "message": str(e)}
        )


@app.delete("/api/rag/session/{session_id}", tags=["RAG Documents"])
async def delete_session(session_id: str):
    """Delete a RAG session and clean up its resources."""
    rag_service = get_rag_service()

    if rag_service.delete_session(session_id):
        return {"success": True, "message": f"Session {session_id} deleted successfully"}
    else:
        raise HTTPException(
            status_code=404,
            detail={"error": "Session not found", "session_id": session_id}
        )


@app.get("/api/rag/session/{session_id}", tags=["RAG Documents"])
async def get_session_info(session_id: str):
    """Get comprehensive information about a session."""
    rag_service = get_rag_service()
    info = rag_service.get_session_info(session_id)

    if not info.get("found", False):
        raise HTTPException(
            status_code=404,
            detail={"error": "Session not found", "session_id": session_id}
        )

    return info


# =============================================================================
# Application Entry Point
# =============================================================================

if __name__ == "__main__":
    import uvicorn

    # Run the FastAPI server
    # Access API docs at: http://localhost:8000/api/docs
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Enable auto-reload during development
        log_level="info"
    )
