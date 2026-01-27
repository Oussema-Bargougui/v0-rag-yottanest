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

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// =============================================================================
// Type Definitions
// =============================================================================

export interface RAGUploadResponse {
  session_id: string;
  filename: string;
  size: number;
  message: string;
}

export interface RAGProcessingStatus {
  session_id: string;
  found: boolean;
  stage: ProcessingStage;
  progress: number;
  message: string;
  error: string | null;
  files_count: number;
  documents_processed: number;
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
  query: string;
  chunks_used: number;
  model: string;
  error: string | null;
}

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
// API Functions
// =============================================================================

/**
 * Upload a document to the RAG system
 *
 * @param file - The file to upload
 * @param sessionId - Optional existing session ID (creates new if not provided)
 * @returns Upload response with session ID
 */
export async function uploadDocument(
  file: File,
  sessionId?: string
): Promise<RAGUploadResponse> {
  try {
    const formData = new FormData();
    formData.append("file", file);

    let url = `${API_BASE_URL}/api/rag/upload`;
    if (sessionId) {
      url += `?session_id=${encodeURIComponent(sessionId)}`;
    }

    const response = await fetch(url, {
      method: "POST",
      body: formData,
    });

    return handleResponse<RAGUploadResponse>(response);
  } catch (error) {
    if (error instanceof Error) {
      if (error.message === "Failed to fetch") {
        throw new Error(
          "Unable to connect to the server. Please ensure the backend is running."
        );
      }
      throw error;
    }
    throw new Error("An unexpected error occurred during upload");
  }
}

/**
 * Upload multiple documents to the RAG system
 *
 * @param files - Array of files to upload
 * @param sessionId - Optional existing session ID
 * @param onProgress - Optional callback for upload progress
 * @returns Array of upload responses
 */
export async function uploadDocuments(
  files: File[],
  sessionId?: string,
  onProgress?: (current: number, total: number, filename: string) => void
): Promise<{ sessionId: string; uploads: RAGUploadResponse[] }> {
  const uploads: RAGUploadResponse[] = [];
  let currentSessionId = sessionId;

  for (let i = 0; i < files.length; i++) {
    const file = files[i];
    onProgress?.(i + 1, files.length, file.name);

    const result = await uploadDocument(file, currentSessionId);
    uploads.push(result);

    // Use the session ID from the first upload for subsequent uploads
    if (!currentSessionId) {
      currentSessionId = result.session_id;
    }
  }

  return {
    sessionId: currentSessionId || "",
    uploads,
  };
}

/**
 * Start processing uploaded documents
 *
 * @param sessionId - Session ID containing uploaded documents
 * @returns Processing result
 */
export async function processDocuments(
  sessionId: string
): Promise<RAGProcessResponse> {
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/rag/process?session_id=${encodeURIComponent(sessionId)}`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      }
    );

    return handleResponse<RAGProcessResponse>(response);
  } catch (error) {
    if (error instanceof Error) {
      if (error.message === "Failed to fetch") {
        throw new Error(
          "Unable to connect to the server. Please ensure the backend is running."
        );
      }
      throw error;
    }
    throw new Error("An unexpected error occurred during processing");
  }
}

/**
 * Get the current processing status for a session
 *
 * @param sessionId - Session ID to check
 * @returns Processing status
 */
export async function getProcessingStatus(
  sessionId: string
): Promise<RAGProcessingStatus> {
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/rag/status/${encodeURIComponent(sessionId)}`
    );

    return handleResponse<RAGProcessingStatus>(response);
  } catch (error) {
    if (error instanceof Error) {
      if (error.message === "Failed to fetch") {
        throw new Error("Unable to connect to the server.");
      }
      throw error;
    }
    throw new Error("An unexpected error occurred");
  }
}

/**
 * Query processed documents and get an AI-generated answer
 *
 * @param sessionId - Session ID with processed documents
 * @param query - Question to ask
 * @param topK - Number of relevant chunks to retrieve (default: 5)
 * @returns Query response with answer and sources
 */
export async function queryDocuments(
  sessionId: string,
  query: string,
  topK: number = 5
): Promise<RAGQueryResponse> {
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/rag/query?session_id=${encodeURIComponent(sessionId)}`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query,
          top_k: topK,
        }),
      }
    );

    return handleResponse<RAGQueryResponse>(response);
  } catch (error) {
    if (error instanceof Error) {
      if (error.message === "Failed to fetch") {
        throw new Error(
          "Unable to connect to the server. Please ensure the backend and Ollama are running."
        );
      }
      throw error;
    }
    throw new Error("An unexpected error occurred during query");
  }
}

/**
 * Get comprehensive information about a session
 *
 * @param sessionId - Session ID to query
 * @returns Session information
 */
export async function getSessionInfo(
  sessionId: string
): Promise<RAGSessionInfo> {
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/rag/session/${encodeURIComponent(sessionId)}`
    );

    return handleResponse<RAGSessionInfo>(response);
  } catch (error) {
    if (error instanceof Error) {
      if (error.message === "Failed to fetch") {
        throw new Error("Unable to connect to the server.");
      }
      throw error;
    }
    throw new Error("An unexpected error occurred");
  }
}

/**
 * Delete a session and clean up its resources
 *
 * @param sessionId - Session ID to delete
 * @returns Success status
 */
export async function deleteSession(
  sessionId: string
): Promise<{ success: boolean; message: string }> {
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/rag/session/${encodeURIComponent(sessionId)}`,
      {
        method: "DELETE",
      }
    );

    return handleResponse<{ success: boolean; message: string }>(response);
  } catch (error) {
    if (error instanceof Error) {
      if (error.message === "Failed to fetch") {
        throw new Error("Unable to connect to the server.");
      }
      throw error;
    }
    throw new Error("An unexpected error occurred");
  }
}

/**
 * Poll processing status until complete or error
 *
 * @param sessionId - Session ID to poll
 * @param onStatusChange - Callback for status updates
 * @param intervalMs - Polling interval in milliseconds (default: 1000)
 * @returns Final processing status
 */
export async function pollProcessingStatus(
  sessionId: string,
  onStatusChange?: (status: RAGProcessingStatus) => void,
  intervalMs: number = 1000
): Promise<RAGProcessingStatus> {
  return new Promise((resolve, reject) => {
    const poll = async () => {
      try {
        const status = await getProcessingStatus(sessionId);
        onStatusChange?.(status);

        if (status.stage === "ready") {
          resolve(status);
        } else if (status.stage === "error") {
          reject(new Error(status.error || "Processing failed"));
        } else {
          setTimeout(poll, intervalMs);
        }
      } catch (error) {
        reject(error);
      }
    };

    poll();
  });
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
