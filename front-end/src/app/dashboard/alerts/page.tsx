/**
 * Company Search & VAT Validation Page
 * =====================================
 *
 * This page provides:
 * 1. EU VAT number validation via VIES service
 * 2. Detailed KBO data lookup for Belgian companies
 *
 * Features:
 * - Country code selection for all EU member states
 * - Real-time VAT validation with VIES
 * - One-click KBO data retrieval for Belgian companies
 * - Professional display of company information
 * - Clickable links to external sources (KBO, National Gazette, etc.)
 *
 * @author Yottanest Team
 */
"use client"

import { useState } from "react"
import {
  Search,
  Building2,
  CheckCircle,
  XCircle,
  MapPin,
  Loader2,
  ChevronDown,
  AlertCircle,
  Clock,
  FileCheck,
  RefreshCw,
  Globe,
  Phone,
  Mail,
  Calendar,
  Users,
  Briefcase,
  BadgeCheck,
  ExternalLink,
  Link2,
  DollarSign,
  FileText,
  ChevronRight,
  Sparkles,
  X,
  Bot,
} from "lucide-react"
import { PageHeader } from "@/components/layout/page-header"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

// Import the VAT validation API service
import {
  validateVAT,
  VATValidationResponse,
  fetchKBOData,
  KBODataResponse,
  generateCompanySummary,
  CompanySummaryResponse,
} from "@/lib/api/vat-validation"

// =============================================================================
// Helper Functions
// =============================================================================

/**
 * Parse markdown links [text](url) and return React elements
 * Handles mixed content with links and plain text
 */
function parseMarkdownLinks(text: string | null | undefined): React.ReactNode {
  if (!text) return "—"

  // Regex to match markdown links [text](url)
  const linkRegex = /\[([^\]]+)\]\(([^)]+)\)/g
  const parts: React.ReactNode[] = []
  let lastIndex = 0
  let match
  let keyIndex = 0

  while ((match = linkRegex.exec(text)) !== null) {
    // Add text before the link
    if (match.index > lastIndex) {
      parts.push(text.slice(lastIndex, match.index))
    }

    // Add the link
    const linkText = match[1]
    const linkUrl = match[2]
    parts.push(
      <a
        key={keyIndex++}
        href={linkUrl}
        target="_blank"
        rel="noopener noreferrer"
        className="text-primary-600 hover:text-primary-700 hover:underline font-medium"
      >
        {linkText}
      </a>
    )

    lastIndex = match.index + match[0].length
  }

  // Add remaining text after last link
  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex))
  }

  return parts.length > 0 ? parts : text
}

/**
 * Check if text contains "No data" or similar
 */
function hasNoData(text: string | null | undefined): boolean {
  if (!text) return true
  const lowerText = text.toLowerCase()
  return lowerText.includes("no data") || lowerText.includes("not available") || text === "—"
}

// =============================================================================
// Constants
// =============================================================================

/**
 * European VAT country codes
 * These are all the valid country codes for the EU VIES system
 */
const vatCountryCodes = [
  { code: "AT", name: "Austria" },
  { code: "BE", name: "Belgium" },
  { code: "BG", name: "Bulgaria" },
  { code: "HR", name: "Croatia" },
  { code: "CY", name: "Cyprus" },
  { code: "CZ", name: "Czech Republic" },
  { code: "DK", name: "Denmark" },
  { code: "EE", name: "Estonia" },
  { code: "FI", name: "Finland" },
  { code: "FR", name: "France" },
  { code: "DE", name: "Germany" },
  { code: "EL", name: "Greece" },
  { code: "HU", name: "Hungary" },
  { code: "IE", name: "Ireland" },
  { code: "IT", name: "Italy" },
  { code: "LV", name: "Latvia" },
  { code: "LT", name: "Lithuania" },
  { code: "LU", name: "Luxembourg" },
  { code: "MT", name: "Malta" },
  { code: "NL", name: "Netherlands" },
  { code: "PL", name: "Poland" },
  { code: "PT", name: "Portugal" },
  { code: "RO", name: "Romania" },
  { code: "SK", name: "Slovakia" },
  { code: "SI", name: "Slovenia" },
  { code: "ES", name: "Spain" },
  { code: "SE", name: "Sweden" },
  { code: "XI", name: "Northern Ireland" },
]

// =============================================================================
// Component
// =============================================================================

export default function CompanySearchPage() {
  // ---------------------------------------------------------------------------
  // State Management
  // ---------------------------------------------------------------------------

  // Form input states
  const [companyName, setCompanyName] = useState("")
  const [vatCountryCode, setVatCountryCode] = useState("")
  const [vatNumber, setVatNumber] = useState("")

  // UI states
  const [isSearching, setIsSearching] = useState(false)
  const [hasSearched, setHasSearched] = useState(false)

  // Validation and error states
  const [vatError, setVatError] = useState("")
  const [apiError, setApiError] = useState("")

  // API response state
  const [validationResult, setValidationResult] = useState<VATValidationResponse | null>(null)

  // KBO data states
  const [kboData, setKboData] = useState<KBODataResponse | null>(null)
  const [isLoadingKBO, setIsLoadingKBO] = useState(false)
  const [kboError, setKboError] = useState("")

  // Company summary states (AI-powered KYC/AML analysis)
  const [summaryData, setSummaryData] = useState<CompanySummaryResponse | null>(null)
  const [isLoadingSummary, setIsLoadingSummary] = useState(false)
  const [summaryError, setSummaryError] = useState("")
  const [showSummaryModal, setShowSummaryModal] = useState(false)

  // Computed value: full VAT number with country prefix
  const fullVatNumber = vatCountryCode && vatNumber ? `${vatCountryCode}${vatNumber}` : ""

  // Check if it's a Belgian VAT number (for showing "Get More Data" button)
  const isBelgianVAT = vatCountryCode === "BE"

  // ---------------------------------------------------------------------------
  // Event Handlers
  // ---------------------------------------------------------------------------

  /**
   * Handles the search form submission
   * Validates input and calls the backend API
   */
  const handleSearch = async () => {
    // Reset previous errors
    setVatError("")
    setApiError("")

    // Validate: VAT number is required
    if (!vatCountryCode) {
      setVatError("Please select a country code")
      return
    }

    if (!vatNumber.trim()) {
      setVatError("Please enter a VAT number")
      return
    }

    // Start loading state
    setIsSearching(true)
    setHasSearched(false)
    setValidationResult(null)

    try {
      // Call the backend API to validate the VAT number
      const result = await validateVAT({
        country_code: vatCountryCode,
        vat_number: vatNumber.trim(),
        company_name: companyName.trim() || undefined,
      })

      // Store the result
      setValidationResult(result)
      setHasSearched(true)
    } catch (error) {
      // Handle API errors
      const errorMessage = error instanceof Error
        ? error.message
        : "An unexpected error occurred. Please try again."

      setApiError(errorMessage)
      setHasSearched(true)
    } finally {
      // End loading state
      setIsSearching(false)
    }
  }

  /**
   * Handles Enter key press to submit the form
   */
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      handleSearch()
    }
  }

  /**
   * Resets the form to initial state
   */
  const handleReset = () => {
    setCompanyName("")
    setVatCountryCode("")
    setVatNumber("")
    setVatError("")
    setApiError("")
    setValidationResult(null)
    setHasSearched(false)
    // Reset KBO data
    setKboData(null)
    setKboError("")
    setIsLoadingKBO(false)
    // Reset company summary data
    setSummaryData(null)
    setSummaryError("")
    setIsLoadingSummary(false)
    setShowSummaryModal(false)
  }

  /**
   * Handles fetching additional KBO data for Belgian VAT numbers
   */
  const handleGetMoreData = async () => {
    if (!validationResult?.full_vat_number) return

    // Reset previous KBO data and errors
    setKboError("")
    setKboData(null)
    setIsLoadingKBO(true)

    try {
      const data = await fetchKBOData(validationResult.full_vat_number)
      setKboData(data)
    } catch (error) {
      const errorMessage = error instanceof Error
        ? error.message
        : "Failed to fetch KBO data. Please try again."
      setKboError(errorMessage)
    } finally {
      setIsLoadingKBO(false)
    }
  }

  /**
   * Handles generating AI-powered KYC/AML summary for the company
   * Requires KBO data to be fetched first
   */
  const handleGenerateSummary = async () => {
    if (!validationResult?.full_vat_number) return

    // Reset previous summary data and errors
    setSummaryError("")
    setSummaryData(null)
    setIsLoadingSummary(true)
    setShowSummaryModal(true)

    try {
      const data = await generateCompanySummary(validationResult.full_vat_number)
      setSummaryData(data)
    } catch (error) {
      const errorMessage = error instanceof Error
        ? error.message
        : "Failed to generate company summary. Please try again."
      setSummaryError(errorMessage)
    } finally {
      setIsLoadingSummary(false)
    }
  }

  /**
   * Gets the country name from country code
   */
  const getCountryName = (code: string): string => {
    const country = vatCountryCodes.find((c) => c.code === code)
    return country?.name || code
  }

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <PageHeader
        title="Company Search"
        description="Validate VAT numbers and retrieve company information from the EU VIES database"
      />

      {/* Search Form Card */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Search className="h-5 w-5" />
            Search Company by VAT Number
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* VAT Number Field - Required */}
            <div>
              <label className="block text-sm font-medium text-neutral-700 mb-2">
                VAT Number <span className="text-red-500">*</span>
              </label>
              <div className="flex">
                {/* Country Code Dropdown */}
                <div className="relative">
                  <select
                    value={vatCountryCode}
                    onChange={(e) => {
                      setVatCountryCode(e.target.value)
                      if (vatError) setVatError("")
                    }}
                    className="appearance-none h-10 pl-3 pr-8 border border-r-0 border-neutral-300 rounded-l-md bg-neutral-50 text-sm font-medium text-neutral-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 cursor-pointer"
                    aria-label="Select country code"
                  >
                    <option value="">Country</option>
                    {vatCountryCodes.map((country) => (
                      <option key={country.code} value={country.code}>
                        {country.code} - {country.name}
                      </option>
                    ))}
                  </select>
                  <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 h-4 w-4 text-neutral-400 pointer-events-none" />
                </div>

                {/* VAT Number Input */}
                <div className="relative flex-1">
                  <Input
                    placeholder="Enter VAT number..."
                    value={vatNumber}
                    onChange={(e) => {
                      setVatNumber(e.target.value)
                      if (vatError) setVatError("")
                    }}
                    onKeyDown={handleKeyPress}
                    className="rounded-l-none"
                    aria-label="VAT number"
                  />
                </div>
              </div>

              {/* Validation Error Message */}
              {vatError && (
                <p className="mt-1 text-sm text-red-500 flex items-center gap-1">
                  <AlertCircle className="h-4 w-4" />
                  {vatError}
                </p>
              )}

              {/* Full VAT Number Preview */}
              {fullVatNumber && !vatError && (
                <p className="mt-1 text-xs text-neutral-500">
                  Full VAT: <span className="font-medium font-mono">{fullVatNumber}</span>
                </p>
              )}
            </div>

            {/* Company Name Field - Optional */}
            <div>
              <label className="block text-sm font-medium text-neutral-700 mb-2">
                Company Name <span className="text-neutral-400">(Optional)</span>
              </label>
              <div className="relative">
                <Building2 className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-neutral-400" />
                <Input
                  placeholder="Enter company name for reference..."
                  value={companyName}
                  onChange={(e) => setCompanyName(e.target.value)}
                  onKeyDown={handleKeyPress}
                  className="pl-10"
                  aria-label="Company name (optional)"
                />
              </div>
              <p className="mt-1 text-xs text-neutral-400">
                Optional: Add company name for your reference
              </p>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="mt-4 flex justify-end gap-2">
            {/* Reset Button - Only show after search */}
            {hasSearched && (
              <Button
                variant="outline"
                onClick={handleReset}
                disabled={isSearching}
              >
                <RefreshCw className="mr-2 h-4 w-4" />
                New Search
              </Button>
            )}

            {/* Search Button */}
            <Button
              onClick={handleSearch}
              disabled={isSearching}
              className="min-w-[140px]"
            >
              {isSearching ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Validating...
                </>
              ) : (
                <>
                  <Search className="mr-2 h-4 w-4" />
                  Validate VAT
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Loading State */}
      {isSearching && (
        <div className="text-center py-12">
          <Loader2 className="h-12 w-12 text-primary-500 mx-auto mb-4 animate-spin" />
          <h3 className="text-lg font-medium text-neutral-900 mb-2">
            Validating VAT Number...
          </h3>
          <p className="text-neutral-500">
            Connecting to EU VIES database to verify company information
          </p>
        </div>
      )}

      {/* API Error State */}
      {apiError && !isSearching && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="p-6">
            <div className="flex items-start gap-4">
              <div className="shrink-0 w-12 h-12 rounded-full bg-red-100 flex items-center justify-center">
                <XCircle className="h-6 w-6 text-red-600" />
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-red-900 mb-1">
                  Validation Error
                </h3>
                <p className="text-red-700">
                  {apiError}
                </p>
                <p className="text-sm text-red-600 mt-2">
                  Please check your VAT number and try again. If the problem persists,
                  the VIES service may be temporarily unavailable.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Validation Results */}
      {validationResult && !isSearching && !apiError && (
        <div className="space-y-4">
          {/* Main Result Card */}
          <Card className={`border-2 ${validationResult.valid ? "border-green-200 bg-green-50/50" : "border-red-200 bg-red-50/50"}`}>
            <CardContent className="p-6">
              <div className="flex flex-col lg:flex-row lg:items-start gap-6">
                <div className={`shrink-0 w-16 h-16 rounded-full flex items-center justify-center ${validationResult.valid ? "bg-green-100" : "bg-red-100"}`}>
                  {validationResult.valid ? (
                    <CheckCircle className="h-8 w-8 text-green-600" />
                  ) : (
                    <XCircle className="h-8 w-8 text-red-600" />
                  )}
                </div>

                <div className="flex-1 space-y-4">
                  <div className="bg-white rounded-lg p-4 border border-neutral-200">
                    <div className="flex items-center gap-2 text-sm text-neutral-500 mb-1">
                      <FileCheck className="h-4 w-4" />
                      VAT Number
                    </div>
                    <p className="text-xl font-mono font-bold text-neutral-900">
                      {validationResult.full_vat_number}
                    </p>
                    <p className="text-sm text-neutral-500 mt-1">
                      Country: {getCountryName(validationResult.country_code)}
                    </p>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="bg-white rounded-lg p-4 border border-neutral-200">
                      <div className="flex items-center gap-2 text-sm text-neutral-500 mb-1">
                        <Building2 className="h-4 w-4" />
                        Company Name
                      </div>
                      <p className="text-lg font-semibold text-neutral-900">
                        {validationResult.company_name !== "Not available"
                          ? validationResult.company_name
                          : "—"}
                      </p>
                    </div>

                    <div className="bg-white rounded-lg p-4 border border-neutral-200">
                      <div className="flex items-center gap-2 text-sm text-neutral-500 mb-1">
                        <MapPin className="h-4 w-4" />
                        Location
                      </div>
                      <p className="text-lg font-semibold text-neutral-900">
                        {validationResult.address !== "Not available"
                          ? validationResult.address
                          : "—"}
                      </p>
                    </div>
                  </div>

                  {/* Get More Data Button - Only for Belgian VAT */}
                  {validationResult.valid && isBelgianVAT && !kboData && (
                    <Button
                      onClick={handleGetMoreData}
                      className="mt-4"
                      variant="outline"
                      disabled={isLoadingKBO}
                    >
                      {isLoadingKBO ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          Fetching KBO Data...
                        </>
                      ) : (
                        <>
                          <Search className="mr-2 h-4 w-4" />
                          Get More Data from KBO
                        </>
                      )}
                    </Button>
                  )}

                  {/* Non-Belgian VAT info */}
                  {validationResult.valid && !isBelgianVAT && (
                    <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg text-sm text-blue-700">
                      <AlertCircle className="inline h-4 w-4 mr-2" />
                      Additional company data from KBO is only available for Belgian (BE) VAT numbers.
                    </div>
                  )}

                  <div className="flex items-center gap-2 text-sm text-neutral-500 pt-2 border-t border-neutral-200">
                    <Clock className="h-4 w-4" />
                    Validated on: {new Date(validationResult.timestamp).toLocaleString()}
                  </div>

                  {validationResult.request_company_name && (
                    <div className="text-sm text-neutral-500 bg-neutral-100 rounded-lg p-3">
                      <span className="font-medium">Your reference:</span>{" "}
                      {validationResult.request_company_name}
                    </div>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* KBO Loading State */}
          {isLoadingKBO && (
            <div className="text-center py-8">
              <Loader2 className="h-10 w-10 text-primary-500 mx-auto mb-4 animate-spin" />
              <h3 className="text-lg font-medium text-neutral-900 mb-2">
                Fetching KBO Data...
              </h3>
              <p className="text-neutral-500">
                Scraping detailed company information from the Belgian KBO database
              </p>
            </div>
          )}

          {/* KBO Error State */}
          {kboError && !isLoadingKBO && (
            <Card className="border-red-200 bg-red-50">
              <CardContent className="p-6">
                <div className="flex items-start gap-4">
                  <div className="shrink-0 w-12 h-12 rounded-full bg-red-100 flex items-center justify-center">
                    <XCircle className="h-6 w-6 text-red-600" />
                  </div>
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-red-900 mb-1">
                      KBO Data Error
                    </h3>
                    <p className="text-red-700">{kboError}</p>
                    <Button
                      onClick={handleGetMoreData}
                      variant="outline"
                      className="mt-3"
                      size="sm"
                    >
                      <RefreshCw className="mr-2 h-4 w-4" />
                      Try Again
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* KBO Data Display */}
          {kboData && !isLoadingKBO && (
            <div className="space-y-4">
              {/* KBO Data Header */}
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-bold text-neutral-900 flex items-center gap-2">
                  <FileText className="h-5 w-5 text-primary-500" />
                  KBO Company Data
                </h2>
                <div className="flex items-center gap-3">
                  {/* AI Summary Button */}
                  <Button
                    onClick={handleGenerateSummary}
                    size="sm"
                    disabled={isLoadingSummary}
                    className="bg-primary-500 hover:bg-primary-600 text-white"
                  >
                    {isLoadingSummary ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Analyzing...
                      </>
                    ) : (
                      <>
                        <Sparkles className="mr-2 h-4 w-4" />
                        AI Summary
                      </>
                    )}
                  </Button>
                  {kboData.source_url && (
                    <a
                      href={kboData.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm text-primary-600 hover:text-primary-700 flex items-center gap-1"
                    >
                      View on KBO
                      <ExternalLink className="h-4 w-4" />
                    </a>
                  )}
                </div>
              </div>

              {/* Company Overview Card */}
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-lg flex items-center gap-2">
                    <Building2 className="h-5 w-5 text-primary-500" />
                    Company Overview
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {/* Company Name */}
                    <div className="bg-neutral-50 rounded-lg p-4">
                      <p className="text-xs font-medium text-neutral-500 uppercase tracking-wide mb-1">
                        Company Name
                      </p>
                      <p className="text-base font-semibold text-neutral-900">
                        {kboData.name || "—"}
                      </p>
                    </div>

                    {/* Enterprise Number */}
                    <div className="bg-neutral-50 rounded-lg p-4">
                      <p className="text-xs font-medium text-neutral-500 uppercase tracking-wide mb-1">
                        Enterprise Number
                      </p>
                      <p className="text-base font-mono font-semibold text-neutral-900">
                        {kboData.company_id || kboData.vat_formatted || "—"}
                      </p>
                    </div>

                    {/* Status */}
                    <div className="bg-neutral-50 rounded-lg p-4">
                      <p className="text-xs font-medium text-neutral-500 uppercase tracking-wide mb-1">
                        Status
                      </p>
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        kboData.status?.toLowerCase().includes("actief") || kboData.status?.toLowerCase().includes("active")
                          ? "bg-green-100 text-green-800"
                          : "bg-neutral-100 text-neutral-800"
                      }`}>
                        {kboData.status || "—"}
                      </span>
                    </div>

                    {/* Legal Status */}
                    <div className="bg-neutral-50 rounded-lg p-4">
                      <p className="text-xs font-medium text-neutral-500 uppercase tracking-wide mb-1">
                        Legal Status
                      </p>
                      <p className="text-base font-semibold text-neutral-900">
                        {kboData.legal_status || "—"}
                      </p>
                    </div>

                    {/* Legal Form */}
                    <div className="bg-neutral-50 rounded-lg p-4">
                      <p className="text-xs font-medium text-neutral-500 uppercase tracking-wide mb-1">
                        Legal Form
                      </p>
                      <p className="text-base font-semibold text-neutral-900">
                        {kboData.legal_form || "—"}
                      </p>
                    </div>

                    {/* Start Date */}
                    <div className="bg-neutral-50 rounded-lg p-4">
                      <p className="text-xs font-medium text-neutral-500 uppercase tracking-wide mb-1">
                        Start Date
                      </p>
                      <p className="text-base font-semibold text-neutral-900 flex items-center gap-2">
                        <Calendar className="h-4 w-4 text-neutral-400" />
                        {kboData.start_date || "—"}
                      </p>
                    </div>

                    {/* Entity Type */}
                    <div className="bg-neutral-50 rounded-lg p-4">
                      <p className="text-xs font-medium text-neutral-500 uppercase tracking-wide mb-1">
                        Entity Type
                      </p>
                      <p className="text-base font-semibold text-neutral-900">
                        {kboData.entity_type || "—"}
                      </p>
                    </div>

                    {/* Establishment Units */}
                    <div className="bg-neutral-50 rounded-lg p-4">
                      <p className="text-xs font-medium text-neutral-500 uppercase tracking-wide mb-1">
                        Establishment Units
                      </p>
                      <p className="text-base font-semibold text-neutral-900">
                        {kboData.establishment_units || "—"}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Contact Information Card */}
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-lg flex items-center gap-2">
                    <Phone className="h-5 w-5 text-primary-500" />
                    Contact Information
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Address */}
                    <div className="bg-neutral-50 rounded-lg p-4 md:col-span-2">
                      <p className="text-xs font-medium text-neutral-500 uppercase tracking-wide mb-1">
                        Registered Address
                      </p>
                      <p className="text-base font-semibold text-neutral-900 flex items-start gap-2">
                        <MapPin className="h-4 w-4 text-neutral-400 mt-1 shrink-0" />
                        {kboData.address_block || "—"}
                      </p>
                    </div>

                    {/* Phone */}
                    <div className="bg-neutral-50 rounded-lg p-4">
                      <p className="text-xs font-medium text-neutral-500 uppercase tracking-wide mb-1">
                        Phone
                      </p>
                      <p className="text-base font-semibold text-neutral-900 flex items-center gap-2">
                        <Phone className="h-4 w-4 text-neutral-400" />
                        {kboData.phone || "—"}
                      </p>
                    </div>

                    {/* Fax */}
                    <div className="bg-neutral-50 rounded-lg p-4">
                      <p className="text-xs font-medium text-neutral-500 uppercase tracking-wide mb-1">
                        Fax
                      </p>
                      <p className="text-base font-semibold text-neutral-900">
                        {kboData.fax || "—"}
                      </p>
                    </div>

                    {/* Email */}
                    <div className="bg-neutral-50 rounded-lg p-4">
                      <p className="text-xs font-medium text-neutral-500 uppercase tracking-wide mb-1">
                        Email
                      </p>
                      {kboData.email ? (
                        <a
                          href={`mailto:${kboData.email}`}
                          className="text-base font-semibold text-primary-600 hover:text-primary-700 flex items-center gap-2"
                        >
                          <Mail className="h-4 w-4" />
                          {kboData.email}
                        </a>
                      ) : (
                        <p className="text-base font-semibold text-neutral-900">—</p>
                      )}
                    </div>

                    {/* Website */}
                    <div className="bg-neutral-50 rounded-lg p-4">
                      <p className="text-xs font-medium text-neutral-500 uppercase tracking-wide mb-1">
                        Website
                      </p>
                      {kboData.website ? (
                        <a
                          href={kboData.website.startsWith("http") ? kboData.website : `https://${kboData.website}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-base font-semibold text-primary-600 hover:text-primary-700 flex items-center gap-2"
                        >
                          <Globe className="h-4 w-4" />
                          {kboData.website}
                        </a>
                      ) : (
                        <p className="text-base font-semibold text-neutral-900">—</p>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Financial Information Card */}
              {kboData.financial_data && (
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-lg flex items-center gap-2">
                      <DollarSign className="h-5 w-5 text-primary-500" />
                      Financial Information
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div className="bg-neutral-50 rounded-lg p-4">
                        <p className="text-xs font-medium text-neutral-500 uppercase tracking-wide mb-1">
                          Capital
                        </p>
                        <p className="text-base font-semibold text-neutral-900">
                          {kboData.financial_data.capital || "—"}
                        </p>
                      </div>
                      <div className="bg-neutral-50 rounded-lg p-4">
                        <p className="text-xs font-medium text-neutral-500 uppercase tracking-wide mb-1">
                          Annual Meeting
                        </p>
                        <p className="text-base font-semibold text-neutral-900">
                          {kboData.financial_data.annual_meeting || "—"}
                        </p>
                      </div>
                      <div className="bg-neutral-50 rounded-lg p-4">
                        <p className="text-xs font-medium text-neutral-500 uppercase tracking-wide mb-1">
                          Fiscal Year End
                        </p>
                        <p className="text-base font-semibold text-neutral-900">
                          {kboData.financial_data.fiscal_year_end || "—"}
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Functions/Directors Card */}
              {kboData.functions && kboData.functions.length > 0 && (
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-lg flex items-center gap-2">
                      <Users className="h-5 w-5 text-primary-500" />
                      Functions & Directors ({kboData.functions.length})
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="overflow-x-auto">
                      <table className="w-full">
                        <thead>
                          <tr className="border-b border-neutral-200 bg-neutral-50">
                            <th className="text-left py-3 px-4 text-xs font-medium text-neutral-500 uppercase tracking-wide">
                              Role
                            </th>
                            <th className="text-left py-3 px-4 text-xs font-medium text-neutral-500 uppercase tracking-wide">
                              Name / Entity
                            </th>
                            <th className="text-left py-3 px-4 text-xs font-medium text-neutral-500 uppercase tracking-wide">
                              Since
                            </th>
                          </tr>
                        </thead>
                        <tbody>
                          {kboData.functions.map((func, index) => (
                            <tr key={index} className="border-b border-neutral-100 last:border-0 hover:bg-neutral-50">
                              {typeof func === "string" ? (
                                <td colSpan={3} className="py-3 px-4 text-sm text-neutral-900">
                                  {parseMarkdownLinks(func)}
                                </td>
                              ) : (
                                <>
                                  <td className="py-3 px-4 text-sm font-medium text-neutral-900">
                                    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-50 text-blue-700 border border-blue-200">
                                      {func.role || "—"}
                                    </span>
                                  </td>
                                  <td className="py-3 px-4 text-sm text-neutral-700">
                                    {parseMarkdownLinks(func.name)}
                                  </td>
                                  <td className="py-3 px-4 text-sm text-neutral-500">
                                    {func.since || "—"}
                                  </td>
                                </>
                              )}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* BTW/VAT Activities Card */}
              {kboData.btw_activities && kboData.btw_activities.length > 0 && (
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-lg flex items-center gap-2">
                      <Briefcase className="h-5 w-5 text-primary-500" />
                      BTW/VAT Activities (NACE Codes)
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="overflow-x-auto">
                      <table className="w-full">
                        <thead>
                          <tr className="border-b border-neutral-200">
                            <th className="text-left py-3 px-4 text-xs font-medium text-neutral-500 uppercase tracking-wide">
                              Version
                            </th>
                            <th className="text-left py-3 px-4 text-xs font-medium text-neutral-500 uppercase tracking-wide">
                              Code
                            </th>
                            <th className="text-left py-3 px-4 text-xs font-medium text-neutral-500 uppercase tracking-wide">
                              Description
                            </th>
                            <th className="text-left py-3 px-4 text-xs font-medium text-neutral-500 uppercase tracking-wide">
                              Since
                            </th>
                          </tr>
                        </thead>
                        <tbody>
                          {kboData.btw_activities.map((activity, index) => (
                            <tr key={index} className="border-b border-neutral-100 last:border-0">
                              <td className="py-3 px-4 text-sm">
                                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                                  {activity.version || "—"}
                                </span>
                              </td>
                              <td className="py-3 px-4 text-sm font-mono font-medium text-neutral-900">
                                {activity.code || "—"}
                              </td>
                              <td className="py-3 px-4 text-sm text-neutral-700">
                                {activity.desc || "—"}
                              </td>
                              <td className="py-3 px-4 text-sm text-neutral-500">
                                {activity.since || "—"}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* RSZ/NSSO Activities Card */}
              {kboData.rsz_activities && kboData.rsz_activities.length > 0 && (
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-lg flex items-center gap-2">
                      <Briefcase className="h-5 w-5 text-primary-500" />
                      RSZ/NSSO Activities (NACE Codes)
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="overflow-x-auto">
                      <table className="w-full">
                        <thead>
                          <tr className="border-b border-neutral-200">
                            <th className="text-left py-3 px-4 text-xs font-medium text-neutral-500 uppercase tracking-wide">
                              Version
                            </th>
                            <th className="text-left py-3 px-4 text-xs font-medium text-neutral-500 uppercase tracking-wide">
                              Code
                            </th>
                            <th className="text-left py-3 px-4 text-xs font-medium text-neutral-500 uppercase tracking-wide">
                              Description
                            </th>
                            <th className="text-left py-3 px-4 text-xs font-medium text-neutral-500 uppercase tracking-wide">
                              Since
                            </th>
                          </tr>
                        </thead>
                        <tbody>
                          {kboData.rsz_activities.map((activity, index) => (
                            <tr key={index} className="border-b border-neutral-100 last:border-0">
                              <td className="py-3 px-4 text-sm">
                                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-800">
                                  {activity.version || "—"}
                                </span>
                              </td>
                              <td className="py-3 px-4 text-sm font-mono font-medium text-neutral-900">
                                {activity.code || "—"}
                              </td>
                              <td className="py-3 px-4 text-sm text-neutral-700">
                                {activity.desc || "—"}
                              </td>
                              <td className="py-3 px-4 text-sm text-neutral-500">
                                {activity.since || "—"}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Capacities & Licenses */}
              {((kboData.capacities && kboData.capacities.length > 0 && !kboData.capacities.every(c => hasNoData(c))) ||
                (kboData.licenses && kboData.licenses.length > 0 && !kboData.licenses.every(l => hasNoData(l)))) && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Capacities */}
                  {kboData.capacities && kboData.capacities.length > 0 && !kboData.capacities.every(c => hasNoData(c)) && (
                    <Card className="md:col-span-2">
                      <CardHeader className="pb-3">
                        <CardTitle className="text-lg flex items-center gap-2">
                          <BadgeCheck className="h-5 w-5 text-primary-500" />
                          Capacities & Qualifications
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-2">
                          {kboData.capacities
                            .filter(c => !hasNoData(c) && !c.includes("Show the legal functions") && !c.includes("Hide the legal functions"))
                            .map((capacity, index) => (
                            <div key={index} className="flex items-start gap-2 text-sm text-neutral-700 p-2 bg-neutral-50 rounded-lg">
                              <ChevronRight className="h-4 w-4 text-primary-500 mt-0.5 shrink-0" />
                              <span>{parseMarkdownLinks(capacity)}</span>
                            </div>
                          ))}
                        </div>
                      </CardContent>
                    </Card>
                  )}

                  {/* Licenses */}
                  {kboData.licenses && kboData.licenses.length > 0 && !kboData.licenses.every(l => hasNoData(l)) && (
                    <Card className="md:col-span-2">
                      <CardHeader className="pb-3">
                        <CardTitle className="text-lg flex items-center gap-2">
                          <FileCheck className="h-5 w-5 text-primary-500" />
                          Licenses & Authorizations
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-2">
                          {kboData.licenses.filter(l => !hasNoData(l)).map((license, index) => (
                            <div key={index} className="flex items-start gap-2 text-sm text-neutral-700 p-2 bg-neutral-50 rounded-lg">
                              <ChevronRight className="h-4 w-4 text-primary-500 mt-0.5 shrink-0" />
                              <span>{parseMarkdownLinks(license)}</span>
                            </div>
                          ))}
                        </div>
                      </CardContent>
                    </Card>
                  )}
                </div>
              )}

              {/* Entity Links Card */}
              {kboData.entity_links && kboData.entity_links.length > 0 && (
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-lg flex items-center gap-2">
                      <Link2 className="h-5 w-5 text-primary-500" />
                      Related Entities ({kboData.entity_links.length})
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="overflow-x-auto">
                      <table className="w-full">
                        <thead>
                          <tr className="border-b border-neutral-200 bg-neutral-50">
                            <th className="text-left py-3 px-4 text-xs font-medium text-neutral-500 uppercase tracking-wide">
                              Enterprise Number
                            </th>
                            <th className="text-left py-3 px-4 text-xs font-medium text-neutral-500 uppercase tracking-wide">
                              Name
                            </th>
                            <th className="text-left py-3 px-4 text-xs font-medium text-neutral-500 uppercase tracking-wide">
                              Relationship
                            </th>
                            <th className="text-left py-3 px-4 text-xs font-medium text-neutral-500 uppercase tracking-wide">
                              Since
                            </th>
                          </tr>
                        </thead>
                        <tbody>
                          {kboData.entity_links.map((link, index) => (
                            <tr key={index} className="border-b border-neutral-100 last:border-0 hover:bg-neutral-50">
                              <td className="py-3 px-4 text-sm font-mono font-medium">
                                {link.number ? (
                                  <a
                                    href={`https://kbopub.economie.fgov.be/kbopub/toonondernemingps.html?ondernemingsnummer=${link.number.replace(/\./g, '')}`}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-primary-600 hover:text-primary-700 hover:underline"
                                  >
                                    {link.number}
                                  </a>
                                ) : "—"}
                              </td>
                              <td className="py-3 px-4 text-sm font-medium text-neutral-900">
                                {link.name || "—"}
                              </td>
                              <td className="py-3 px-4 text-sm text-neutral-600">
                                {link.relationship || "—"}
                              </td>
                              <td className="py-3 px-4 text-sm text-neutral-500">
                                {link.since || "—"}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* External Links Card */}
              {kboData.external_links && kboData.external_links.length > 0 && (
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-lg flex items-center gap-2">
                      <ExternalLink className="h-5 w-5 text-primary-500" />
                      External References & Official Sources
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                      {kboData.external_links.map((link, index) => (
                        <div key={index}>
                          {link.url ? (
                            <a
                              href={link.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="flex items-center gap-3 p-3 bg-gradient-to-r from-neutral-50 to-neutral-100 hover:from-primary-50 hover:to-primary-100 border border-neutral-200 hover:border-primary-300 rounded-lg text-sm text-neutral-700 hover:text-primary-700 transition-all group"
                            >
                              <div className="shrink-0 w-8 h-8 rounded-full bg-white border border-neutral-200 group-hover:border-primary-300 flex items-center justify-center">
                                <ExternalLink className="h-4 w-4 text-neutral-400 group-hover:text-primary-500" />
                              </div>
                              <span className="font-medium truncate">{link.label || link.url}</span>
                            </a>
                          ) : (
                            <div className="flex items-center gap-3 p-3 bg-neutral-50 border border-neutral-200 rounded-lg text-sm text-neutral-700">
                              <div className="shrink-0 w-8 h-8 rounded-full bg-white border border-neutral-200 flex items-center justify-center">
                                <FileText className="h-4 w-4 text-neutral-400" />
                              </div>
                              <span className="font-medium">{link.label || "—"}</span>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Entrepreneurial Skills */}
              {kboData.entrepreneurial_skills &&
               kboData.entrepreneurial_skills.length > 0 &&
               !kboData.entrepreneurial_skills.every(s => hasNoData(s)) && (
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-lg flex items-center gap-2">
                      <BadgeCheck className="h-5 w-5 text-primary-500" />
                      Entrepreneurial Skills
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {kboData.entrepreneurial_skills.filter(s => !hasNoData(s)).map((skill, index) => (
                        <div key={index} className="flex items-start gap-2 text-sm text-neutral-700 p-2 bg-neutral-50 rounded-lg">
                          <ChevronRight className="h-4 w-4 text-primary-500 mt-0.5 shrink-0" />
                          <span>{parseMarkdownLinks(skill)}</span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          )}

          {/* AI Company Summary Modal */}
          {showSummaryModal && (
            <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-neutral-900/60 backdrop-blur-sm">
              <Card className="w-full max-w-3xl max-h-[85vh] overflow-hidden shadow-2xl border-0">
                {/* Header */}
                <div className="bg-primary-500 px-6 py-5 relative">
                  <button
                    onClick={() => setShowSummaryModal(false)}
                    className="absolute right-4 top-4 p-2 rounded-lg bg-white/10 hover:bg-white/20 transition-colors"
                    aria-label="Close modal"
                  >
                    <X className="h-4 w-4 text-white" />
                  </button>
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-white/20 flex items-center justify-center">
                      <Bot className="h-5 w-5 text-white" />
                    </div>
                    <div>
                      <h2 className="text-lg font-semibold text-white">
                        AI Company Analysis
                      </h2>
                      <p className="text-sm text-white/70">
                        KYC/AML Intelligence Report
                      </p>
                    </div>
                  </div>
                </div>

                {/* Content */}
                <div className="p-6 overflow-y-auto max-h-[calc(85vh-88px)] bg-neutral-50">
                  {/* Loading State */}
                  {isLoadingSummary && (
                    <div className="text-center py-16">
                      <div className="relative mx-auto w-20 h-20 mb-6">
                        <div className="absolute inset-0 rounded-full border-4 border-primary-100"></div>
                        <div className="absolute inset-0 rounded-full border-4 border-primary-500 border-t-transparent animate-spin"></div>
                        <div className="absolute inset-0 flex items-center justify-center">
                          <Sparkles className="h-7 w-7 text-primary-500" />
                        </div>
                      </div>
                      <h3 className="text-lg font-semibold text-neutral-900 mb-2">
                        Analyzing Company Data
                      </h3>
                      <p className="text-sm text-neutral-500 max-w-sm mx-auto">
                        Our AI is reviewing KBO data to generate a comprehensive KYC/AML summary
                      </p>
                    </div>
                  )}

                  {/* Error State */}
                  {summaryError && !isLoadingSummary && (
                    <div className="text-center py-12">
                      <div className="w-16 h-16 rounded-full bg-red-50 border border-red-200 flex items-center justify-center mx-auto mb-4">
                        <XCircle className="h-8 w-8 text-red-500" />
                      </div>
                      <h3 className="text-lg font-semibold text-neutral-900 mb-2">
                        Analysis Failed
                      </h3>
                      <p className="text-sm text-neutral-600 mb-6 max-w-sm mx-auto">
                        {summaryError}
                      </p>
                      <Button
                        onClick={handleGenerateSummary}
                        variant="outline"
                        size="sm"
                        className="border-primary-300 text-primary-700 hover:bg-primary-50"
                      >
                        <RefreshCw className="mr-2 h-4 w-4" />
                        Try Again
                      </Button>
                    </div>
                  )}

                  {/* Summary Content */}
                  {summaryData && !isLoadingSummary && !summaryError && (
                    <div className="space-y-5">
                      {/* Company Info Card */}
                      <div className="bg-white rounded-xl border border-neutral-200 p-5">
                        <div className="flex items-start gap-4">
                          <div className="w-14 h-14 rounded-xl bg-primary-50 border border-primary-100 flex items-center justify-center shrink-0">
                            <Building2 className="h-7 w-7 text-primary-600" />
                          </div>
                          <div className="flex-1 min-w-0">
                            <h3 className="text-lg font-semibold text-neutral-900 truncate">
                              {summaryData.company_name || kboData?.name || "Company"}
                            </h3>
                            <div className="flex items-center gap-3 mt-1">
                              <span className="text-sm text-neutral-500 font-mono bg-neutral-100 px-2 py-0.5 rounded">
                                {summaryData.vat_number}
                              </span>
                              {kboData?.status && (
                                <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                                  kboData.status.toLowerCase().includes("active") || kboData.status.toLowerCase().includes("actief")
                                    ? "bg-green-50 text-green-700 border border-green-200"
                                    : "bg-neutral-100 text-neutral-600 border border-neutral-200"
                                }`}>
                                  {kboData.status}
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* Summary Section */}
                      <div className="bg-white rounded-xl border border-neutral-200 overflow-hidden">
                        <div className="px-5 py-4 border-b border-neutral-100 bg-neutral-50/50">
                          <div className="flex items-center gap-2">
                            <div className="w-8 h-8 rounded-lg bg-primary-100 flex items-center justify-center">
                              <Sparkles className="h-4 w-4 text-primary-600" />
                            </div>
                            <div>
                              <h4 className="text-sm font-semibold text-neutral-900">
                                KYC/AML Summary
                              </h4>
                              <p className="text-xs text-neutral-500">
                                AI-generated compliance analysis
                              </p>
                            </div>
                          </div>
                        </div>
                        <div className="p-5">
                          <div className="text-sm text-neutral-700 leading-relaxed whitespace-pre-wrap">
                            {summaryData.summary}
                          </div>
                        </div>
                      </div>

                      {/* Metadata Footer */}
                      <div className="bg-white rounded-xl border border-neutral-200 px-5 py-3">
                        <div className="flex items-center justify-between text-xs">
                          <div className="flex items-center gap-4">
                            <span className="flex items-center gap-1.5 text-neutral-500">
                              <Bot className="h-3.5 w-3.5" />
                              <span className="font-medium text-neutral-700">{summaryData.model}</span>
                            </span>
                            <span className="w-px h-4 bg-neutral-200"></span>
                            <span className="flex items-center gap-1.5 text-neutral-500">
                              <Clock className="h-3.5 w-3.5" />
                              {new Date(summaryData.generated_at).toLocaleString()}
                            </span>
                          </div>
                          <div className="flex items-center gap-1.5 text-primary-600">
                            <CheckCircle className="h-3.5 w-3.5" />
                            <span className="font-medium">Analysis Complete</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </Card>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
