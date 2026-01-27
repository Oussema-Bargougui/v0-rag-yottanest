/**
 * VAT Validation & KBO Data API Service
 * ======================================
 *
 * This module provides functions to interact with the VAT validation backend API.
 * It handles:
 * 1. VAT validation via EU VIES (VAT Information Exchange System)
 * 2. Fetching detailed company data from Belgian KBO database
 *
 * Functions:
 * - validateVAT()   - Validate a European VAT number
 * - fetchKBOData()  - Get detailed Belgian company information
 * - checkAPIHealth() - Verify backend API availability
 *
 * @module lib/api/vat-validation
 * @author Yottanest Team
 */

// =============================================================================
// Configuration
// =============================================================================

/**
 * Backend API base URL
 * In production, this should come from environment variables
 */
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// =============================================================================
// Types & Interfaces
// =============================================================================

/**
 * Request payload for VAT validation
 */
export interface VATValidationRequest {
  /** Two-letter EU country code (e.g., 'BE', 'FR', 'DE') */
  country_code: string;
  /** VAT number without the country prefix */
  vat_number: string;
  /** Optional company name for reference */
  company_name?: string;
}

/**
 * Response from VAT validation API
 */
export interface VATValidationResponse {
  /** Whether the VAT number is valid and registered */
  valid: boolean;
  /** The validated country code */
  country_code: string;
  /** The validated VAT number (without prefix) */
  vat_number: string;
  /** Complete VAT number with country prefix */
  full_vat_number: string;
  /** Registered company name from VIES */
  company_name: string;
  /** Registered company address from VIES */
  address: string;
  /** Company name provided in the request (if any) */
  request_company_name?: string;
  /** ISO timestamp of the validation */
  timestamp: string;
  /** Error message if validation failed */
  error?: string;
}

/**
 * API error response structure
 */
export interface APIError {
  /** Error type or code */
  error: string;
  /** Human-readable error message */
  message: string;
  /** ISO timestamp of the error */
  timestamp: string;
}

// =============================================================================
// KBO Data Types
// =============================================================================

/**
 * BTW/VAT activity information
 */
export interface BTWActivity {
  version: string | null;
  code: string | null;
  desc: string | null;
  since: string | null;
}

/**
 * RSZ/NSSO activity information
 */
export interface RSZActivity {
  version: string | null;
  code: string | null;
  desc: string | null;
  since: string | null;
}

/**
 * Financial information from KBO
 */
export interface FinancialData {
  capital: string | null;
  annual_meeting: string | null;
  fiscal_year_end: string | null;
}

/**
 * Related entity link
 */
export interface EntityLink {
  number: string | null;
  name: string | null;
  relationship: string | null;
  since: string | null;
}

/**
 * External reference link
 */
export interface ExternalLink {
  label: string | null;
  url: string | null;
}

/**
 * Function/role holder in the company
 */
export interface FunctionHolder {
  role: string;
  name: string;
  since: string;
}

/**
 * Complete KBO data response structure
 */
export interface KBODataResponse {
  company_id: string | null;
  name: string | null;
  status: string | null;
  legal_status: string | null;
  legal_form: string | null;
  start_date: string | null;
  address_block: string | null;
  website: string | null;
  phone: string | null;
  fax: string | null;
  email: string | null;
  entity_type: string | null;
  establishment_units: string | null;
  functions: (string | FunctionHolder)[];
  entrepreneurial_skills: string[];
  capacities: string[];
  licenses: string[];
  btw_activities: BTWActivity[];
  rsz_activities: RSZActivity[];
  financial_data: FinancialData | null;
  entity_links: EntityLink[];
  external_links: ExternalLink[];
  vat_number: string | null;
  vat_formatted: string | null;
  source_url: string | null;
  engine: string | null;
  error: string | null;
}

/**
 * AI-generated company summary response
 */
export interface CompanySummaryResponse {
  /** The VAT number that was analyzed */
  vat_number: string;
  /** Company name from KBO data */
  company_name: string | null;
  /** AI-generated KYC/AML summary text */
  summary: string;
  /** Timestamp when summary was generated */
  generated_at: string;
  /** LLM model used for generation */
  model: string;
  /** Error message if generation failed */
  error: string | null;
}

// =============================================================================
// API Functions
// =============================================================================

/**
 * Validates a European VAT number using the backend API.
 *
 * This function sends a request to our FastAPI backend, which in turn
 * queries the EU VIES service to validate the VAT number and retrieve
 * company information.
 *
 * @param request - The VAT validation request containing country code and VAT number
 * @returns Promise resolving to the validation response with company details
 * @throws Error if the API request fails or returns an error
 *
 * @example
 * ```typescript
 * const result = await validateVAT({
 *   country_code: 'BE',
 *   vat_number: '0403200393',
 *   company_name: 'Example Company' // optional
 * });
 *
 * if (result.valid) {
 *   console.log(`Company: ${result.company_name}`);
 *   console.log(`Address: ${result.address}`);
 * }
 * ```
 */
export async function validateVAT(
  request: VATValidationRequest
): Promise<VATValidationResponse> {
  try {
    // Build the API endpoint URL
    const endpoint = `${API_BASE_URL}/api/vat/validate`;

    // Make the POST request to the backend
    const response = await fetch(endpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify({
        country_code: request.country_code.toUpperCase(),
        vat_number: request.vat_number.trim(),
        company_name: request.company_name?.trim() || null,
      }),
    });

    // Handle HTTP error responses
    if (!response.ok) {
      const errorData = await response.json().catch(() => null);

      // Extract error message from response
      const errorMessage =
        errorData?.detail?.message ||
        errorData?.detail ||
        errorData?.message ||
        `HTTP Error: ${response.status}`;

      throw new Error(errorMessage);
    }

    // Parse and return the successful response
    const data: VATValidationResponse = await response.json();
    return data;
  } catch (error) {
    // Re-throw with more context if needed
    if (error instanceof Error) {
      // Check for network errors
      if (error.message === "Failed to fetch") {
        throw new Error(
          "Unable to connect to the validation service. Please check if the backend server is running."
        );
      }
      throw error;
    }

    // Unknown error type
    throw new Error("An unexpected error occurred during VAT validation");
  }
}

/**
 * Fetches detailed company information from the Belgian KBO database.
 *
 * This function calls the backend API which scrapes the KBO public database
 * to retrieve comprehensive company information including business activities,
 * financial data, and related entities.
 *
 * Note: This only works for Belgian (BE) VAT numbers.
 *
 * @param vatNumber - The full VAT number including country prefix (e.g., 'BE0403170701')
 * @returns Promise resolving to the KBO data response with company details
 * @throws Error if the API request fails or returns an error
 *
 * @example
 * ```typescript
 * const kboData = await fetchKBOData('BE0403170701');
 * console.log(`Company: ${kboData.name}`);
 * console.log(`Legal Form: ${kboData.legal_form}`);
 * ```
 */
export async function fetchKBOData(vatNumber: string): Promise<KBODataResponse> {
  try {
    // Build the API endpoint URL with query parameter
    const endpoint = `${API_BASE_URL}/api/vat/kbo-data?vat_number=${encodeURIComponent(vatNumber)}`;

    // Make the GET request to the backend
    const response = await fetch(endpoint, {
      method: "GET",
      headers: {
        Accept: "application/json",
      },
    });

    // Handle HTTP error responses
    if (!response.ok) {
      const errorData = await response.json().catch(() => null);

      // Extract error message from response
      const errorMessage =
        errorData?.detail?.message ||
        errorData?.detail ||
        errorData?.message ||
        `HTTP Error: ${response.status}`;

      throw new Error(errorMessage);
    }

    // Parse and return the successful response
    const data: KBODataResponse = await response.json();
    return data;
  } catch (error) {
    // Re-throw with more context if needed
    if (error instanceof Error) {
      // Check for network errors
      if (error.message === "Failed to fetch") {
        throw new Error(
          "Unable to connect to the KBO data service. Please check if the backend server is running."
        );
      }
      throw error;
    }

    // Unknown error type
    throw new Error("An unexpected error occurred while fetching KBO data");
  }
}

/**
 * Generates an AI-powered KYC/AML summary for a Belgian company.
 *
 * This function calls the backend API which uses a local Llama 3.1 model
 * to generate a compliance-focused summary based on KBO data.
 *
 * Prerequisites:
 * - The company must have been previously fetched via fetchKBOData()
 * - Ollama must be running locally with llama3.1 model
 *
 * @param vatNumber - The full VAT number including country prefix (e.g., 'BE0403170701')
 * @returns Promise resolving to the AI-generated summary response
 * @throws Error if the API request fails or KBO data wasn't fetched first
 *
 * @example
 * ```typescript
 * // First fetch KBO data
 * await fetchKBOData('BE0403170701');
 *
 * // Then generate summary
 * const summary = await generateCompanySummary('BE0403170701');
 * console.log(summary.summary);
 * ```
 */
export async function generateCompanySummary(
  vatNumber: string
): Promise<CompanySummaryResponse> {
  try {
    // Build the API endpoint URL
    const endpoint = `${API_BASE_URL}/api/vat/company-summary?vat_number=${encodeURIComponent(vatNumber)}`;

    // Make the POST request to the backend
    const response = await fetch(endpoint, {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
    });

    // Handle HTTP error responses
    if (!response.ok) {
      const errorData = await response.json().catch(() => null);

      // Extract error message from response
      const errorMessage =
        errorData?.detail?.message ||
        errorData?.detail ||
        errorData?.message ||
        `HTTP Error: ${response.status}`;

      throw new Error(errorMessage);
    }

    // Parse and return the successful response
    const data: CompanySummaryResponse = await response.json();
    return data;
  } catch (error) {
    // Re-throw with more context if needed
    if (error instanceof Error) {
      if (error.message === "Failed to fetch") {
        throw new Error(
          "Unable to connect to the summary service. Please check if the backend server is running."
        );
      }
      throw error;
    }

    throw new Error("An unexpected error occurred while generating summary");
  }
}

/**
 * Checks if the backend API is healthy and available.
 *
 * @returns Promise resolving to true if the API is healthy, false otherwise
 *
 * @example
 * ```typescript
 * const isHealthy = await checkAPIHealth();
 * if (!isHealthy) {
 *   console.warn('Backend API is not available');
 * }
 * ```
 */
export async function checkAPIHealth(): Promise<boolean> {
  try {
    const endpoint = `${API_BASE_URL}/api/health`;

    const response = await fetch(endpoint, {
      method: "GET",
      headers: {
        Accept: "application/json",
      },
    });

    if (!response.ok) {
      return false;
    }

    const data = await response.json();
    return data.status === "healthy";
  } catch {
    return false;
  }
}

// =============================================================================
// Utility Functions
// =============================================================================

/**
 * Formats a VAT validation response for display purposes.
 *
 * @param response - The VAT validation response
 * @returns Formatted display object
 */
export function formatVATResponse(response: VATValidationResponse) {
  return {
    isValid: response.valid,
    fullVatNumber: response.full_vat_number,
    companyName: response.company_name,
    location: response.address,
    validatedAt: new Date(response.timestamp).toLocaleString(),
    hasError: !!response.error,
    errorMessage: response.error,
  };
}
