/**
 * RAG Documents API Client
 * ========================
 *
 * This module provides client-side API functions for the RAG document
 * processing pipeline. Handles document upload, processing, and Q&A.
 *
 * @module lib/api/rag-documents
 */

// =============================================================================
// Configuration
// =============================================================================

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

// =============================================================================
// Type Definitions
// =============================================================================

export interface RAGUploadResponse {
  success: boolean;
  message: string;
  document_name: string;
  document_id: string;
  chunk_count: number;
  error?: string;
  metadata?: {
    session_id: string;
    qdrant_collection: string;
    files_processed: number;
    total_chunks: number;
    failed_files: number;
  };
}

// Legacy type for backward compatibility
export interface RAGSessionInfo {
  found: boolean;
  session_id: string;
  stage: ProcessingStage;
  progress: number;
  message: string;
  error: string | null;
  files: Array<{
    filename: string;
    path: string;
    size: number;
    uploaded_at: string;
  }>;
  documents_processed: number;
  chat_history_count: number;
  created_at: string;
  updated_at: string;
}

export type ProcessingStage =
  | "idle"
  | "uploading"
  | "extracting"
  | "cleaning"
  | "chunking"
  | "embedding"
  | "storing"
  | "ready"
  | "error";

export interface RAGProcessResponse {
  success: boolean;
  session_id: string;
  documents_processed: number;
  chunks_created: number;
  embeddings_generated: number;
  message: string;
  error: string | null;
}

export interface RAGSourceInfo {
  filename: string;
  chunk_id: number;
  similarity_score: number;
  text_preview: string;
}

export interface RAGQueryResponse {
  success: boolean;
  answer: string;
  sources: RAGSourceInfo[];
  query_time_ms: number;
}

export interface RAGSessionListResponse {
  sessions: RAGSessionListItem[];
}

export interface RAGSessionListItem {
  session_id: string;
  collection_name: string;
  document_count: number;
  created_date: string | null;
}

export interface APIError {
  error: string;
  message: string;
  timestamp?: string;
}

// =============================================================================
// Helper Functions
// =============================================================================

/**
 * Handle API errors and throw appropriate error messages
 */
async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorData = await response.json().catch(() => null);
    const errorMessage =
      errorData?.detail?.message ||
      errorData?.detail?.error ||
      errorData?.message ||
      `HTTP Error: ${response.status}`;
    throw new Error(errorMessage);
  }
  return response.json();
}

// =============================================================================
// API Functions - Chat Endpoints
// =============================================================================

/**
 * Upload documents to a chat session using the new chat endpoint
 *
 * @param files - Array of files to upload
 * @param sessionId - Optional existing session ID (creates new if not provided)
 * @returns Upload response with session ID and metadata
 */
export async function uploadDocumentsToChat(
  files: File[],
  sessionId?: string
): Promise<RAGUploadResponse> {
  try {
    const formData = new FormData();
    files.forEach((file) => formData.append("files", file));

    if (sessionId) {
      formData.append("session_id", sessionId);
    }

    const response = await fetch(`${API_BASE_URL}/api/v1/chat/ingest`, {
      method: "POST",
      body: formData,
    });

    return handleResponse<RAGUploadResponse>(response);
  } catch (error) {
    if (error instanceof Error) {
      if (error.message === "Failed to fetch") {
        throw new Error(
          "Unable to connect to server. Please ensure backend is running."
        );
      }
      throw error;
    }
    throw new Error("An unexpected error occurred during upload");
  }
}

/**
 * Upload a single document (legacy, uses new chat endpoint)
 *
 * @param file - The file to upload
 * @param sessionId - Optional existing session ID
 * @returns Upload response with session ID
 */
export async function uploadDocument(
  file: File,
  sessionId?: string
): Promise<RAGUploadResponse> {
  const result = await uploadDocumentsToChat([file], sessionId);
  return result;
}

/**
 * Query documents in a chat session
 *
 * @param sessionId - Session ID to query
 * @param query - Question to ask
 * @returns Query response with answer and sources
 */
export async function queryDocuments(
  sessionId: string,
  query: string
): Promise<RAGQueryResponse> {
  try {
    const formData = new FormData();
    formData.append("session_id", sessionId);
    formData.append("query", query);

    const response = await fetch(`${API_BASE_URL}/api/v1/chat/query`, {
      method: "POST",
      body: formData,
    });

    return handleResponse<RAGQueryResponse>(response);
  } catch (error) {
    if (error instanceof Error) {
      if (error.message === "Failed to fetch") {
        throw new Error(
          "Unable to connect to server. Please ensure backend is running."
        );
      }
      throw error;
    }
    throw new Error("An unexpected error occurred during query");
  }
}

/**
 * List all chat sessions
 *
 * @returns List of all sessions with metadata
 */
export async function listSessions(): Promise<{ sessions: RAGSessionListItem[] }> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/chat/sessions`);
    const data = await handleResponse<{ sessions: RAGSessionListItem[] }>(response);
    return data;
  } catch (error) {
    if (error instanceof Error) {
      if (error.message === "Failed to fetch") {
        throw new Error(
          "Unable to connect to server. Please ensure backend is running."
        );
      }
      throw error;
    }
    throw new Error("An unexpected error occurred while listing sessions");
  }
}

/**
 * Rename a session
 *
 * @param sessionId - Session ID to rename
 * @param name - New name for the session
 * @returns Success status
 */
export async function renameSession(
  sessionId: string,
  name: string
): Promise<{ success: boolean; message: string; session_id: string; name: string }> {
  try {
    const formData = new FormData();
    formData.append("name", name);

    const response = await fetch(`${API_BASE_URL}/api/v1/chat/sessions/${encodeURIComponent(sessionId)}/name`, {
      method: "PUT",
      body: formData,
    });

    return handleResponse<{ success: boolean; message: string; session_id: string; name: string }>(response);
  } catch (error) {
    if (error instanceof Error) {
      if (error.message === "Failed to fetch") {
        throw new Error(
          "Unable to connect to server. Please ensure backend is running."
        );
      }
      throw error;
    }
    throw new Error("An unexpected error occurred while renaming session");
  }
}

/**
 * Delete a session
 *
 * @param sessionId - Session ID to delete
 * @returns Success status
 */
export async function deleteSession(
  sessionId: string
): Promise<{ success: boolean; message: string; session_id: string }> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/chat/sessions/${encodeURIComponent(sessionId)}`, {
      method: "DELETE",
    });

    return handleResponse<{ success: boolean; message: string; session_id: string }>(response);
  } catch (error) {
    if (error instanceof Error) {
      if (error.message === "Failed to fetch") {
        throw new Error(
          "Unable to connect to server. Please ensure backend is running."
        );
      }
      throw error;
    }
    throw new Error("An unexpected error occurred while deleting session");
  }
}

/**
 * Upload multiple documents using the new chat endpoint
 *
 * @param files - Array of files to upload
 * @param sessionId - Optional existing session ID
 * @param onProgress - Optional callback for upload progress
 * @returns Upload response with session ID
 */
export async function uploadDocuments(
  files: File[],
  sessionId?: string,
  onProgress?: (current: number, total: number, filename: string) => void
): Promise<{ sessionId: string; uploads: RAGUploadResponse[] }> {
  if (onProgress) {
    // For progress tracking, upload files one by one
    const uploads: RAGUploadResponse[] = [];
    let currentSessionId = sessionId;

    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      onProgress(i + 1, files.length, file.name);

      const result = await uploadDocumentsToChat([file], currentSessionId);
      uploads.push(result);

      // Use session ID from first upload for subsequent uploads
      if (!currentSessionId) {
        currentSessionId = result.metadata?.session_id;
      }
    }

    return {
      sessionId: currentSessionId || "",
      uploads,
    };
  } else {
    // Without progress tracking, upload all at once
    const result = await uploadDocumentsToChat(files, sessionId);
    const sessionIdToReturn = result.metadata?.session_id || sessionId || "";

    return {
      sessionId: sessionIdToReturn,
      uploads: [result],
    };
  }
}

// =============================================================================
// Legacy Functions (kept for backward compatibility)
// =============================================================================

/**
 * Start processing uploaded documents (legacy - no longer used)
 */
export async function processDocuments(
  sessionId: string
): Promise<RAGProcessResponse> {
  // Processing is now automatic with new chat endpoints
  // This function is kept for backward compatibility but does nothing
  return {
    success: true,
    session_id: sessionId,
    documents_processed: 0,
    chunks_created: 0,
    embeddings_generated: 0,
    message: "Processing is automatic with new endpoints",
    error: null,
  };
}

/**
 * Get current processing status (legacy - no longer used)
 */
export async function getProcessingStatus(
  sessionId: string
): Promise<RAGSessionInfo> {
  // Status is now automatic with new chat endpoints
  return {
    session_id: sessionId,
    found: true,
    stage: "ready",
    progress: 100,
    message: "Ready",
    error: null,
    files: [],
    documents_processed: 0,
    chat_history_count: 0,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };
}

/**
 * Poll processing status (legacy - no longer used)
 */
export async function pollProcessingStatus(
  sessionId: string,
  onStatusChange?: (status: RAGSessionInfo) => void,
  intervalMs: number = 1000
): Promise<RAGSessionInfo> {
  // Processing is now automatic
  return getProcessingStatus(sessionId);
}

// =============================================================================
// Stage Display Helpers
// =============================================================================

export const PROCESSING_STAGES: {
  key: ProcessingStage;
  label: string;
  description: string;
}[] = [
  { key: "extracting", label: "Extract", description: "Extracting text from documents" },
  { key: "cleaning", label: "Clean", description: "Cleaning and preprocessing" },
  { key: "chunking", label: "Chunk", description: "Splitting into chunks" },
  { key: "embedding", label: "Embed", description: "Generating embeddings" },
  { key: "storing", label: "Store", description: "Building vector store" },
  { key: "ready", label: "Ready", description: "Ready for questions" },
];

/**
 * Get the index of a processing stage
 */
export function getStageIndex(stage: ProcessingStage): number {
  const index = PROCESSING_STAGES.findIndex((s) => s.key === stage);
  return index >= 0 ? index : -1;
}

/**
 * Check if a stage is complete relative to the current stage
 */
export function isStageComplete(
  stage: ProcessingStage,
  currentStage: ProcessingStage
): boolean {
  const stageIndex = getStageIndex(stage);
  const currentIndex = getStageIndex(currentStage);
  return stageIndex >= 0 && currentIndex >= 0 && stageIndex < currentIndex;
}

/**
 * Check if a stage is the currently active stage
 */
export function isStageActive(
  stage: ProcessingStage,
  currentStage: ProcessingStage
): boolean {
  return stage === currentStage;
}
