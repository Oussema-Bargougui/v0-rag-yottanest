# Yottanest Project Architecture Documentation

## Overview

Yottanest is a comprehensive AML/KYC (Anti-Money Laundering/Know Your Customer) compliance platform that combines document processing, company validation, and AI-powered analysis. The system consists of a Python backend with FastAPI services and a Next.js frontend application.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND                                │
│                     (Next.js 14)                               │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   Dashboard     │  │  Document UI    │  │  Company Search │ │
│  │   Components    │  │  Components     │  │  Components     │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                │
                                │ HTTP/REST API
                                │
┌─────────────────────────────────────────────────────────────────┐
│                        BACKEND                                  │
│                    (FastAPI + Python)                            │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                WEB-RESEARCHER SERVICE                       │ │
│  │  ┌─────────────────┐  ┌─────────────────┐                 │ │
│  │  │  VAT Validation  │  │   RAG Service   │                 │ │
│  │  │     API         │  │   (Sessions)    │                 │ │
│  │  └─────────────────┘  └─────────────────┘                 │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                RAG-RESEARCHER SERVICE                      │ │
│  │  ┌─────────────────┐  ┌─────────────────┐                 │ │
│  │  │  RAG Pipeline   │  │   LLM Service   │                 │ │
│  │  │  Orchestrator   │  │  (Ollama/Llama) │                 │ │
│  │  └─────────────────┘  └─────────────────┘                 │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                │
                                │
                    ┌─────────────────────────┐
                    │   EXTERNAL SERVICES     │
                    │ ┌─────────┐ ┌─────────┐ │
                    │ │  Ollama │ │  EU VIES│ │
                    │ │ (LLM)   │ │ (VAT)   │ │
                    │ └─────────┘ └─────────┘ │
                    └─────────────────────────┘
```

## Backend Architecture

### 1. Web Researcher Service (`backend/web-researcher/`)

**Main Entry Point**: `main.py` - FastAPI application

#### Core Components:

##### VAT Validation API
- **Purpose**: Validate European VAT numbers using EU VIES service
- **Key Endpoints**:
  - `POST /api/vat/validate` - Validate VAT numbers
  - `GET /api/vat/kbo-data` - Fetch Belgian company data
  - `POST /api/vat/company-summary` - Generate AI-powered KYC summaries

##### RAG Service API
- **Purpose**: Document processing and Q&A capabilities
- **Key Endpoints**:
  - `POST /api/rag/upload` - Upload documents
  - `POST /api/rag/process` - Process documents through RAG pipeline
  - `GET /api/rag/status/{session_id}` - Check processing status
  - `POST /api/rag/query` - Query processed documents

#### Supporting Files:
- `rag_service.py` - Session management and RAG orchestration
- `vat_search.py` - KBO database scraping
- `company_summary.py` - AI-powered company analysis

### 2. RAG Researcher Service (`backend/rag_researcher/`)

**Main Entry Point**: `orchestrator.py` - RAG pipeline orchestrator

#### Core Pipeline Components:

##### Document Processing Pipeline
1. **Data Loader** (`data_loader.py`)
   - Loads documents from various formats (PDF, TXT, MD)
   - Handles file system operations
   - Extracts metadata

2. **PDF Extractor** (`pdf_extractor.py`)
   - Extracts text from PDF files
   - Handles OCR for scanned documents
   - Preserves document structure

3. **Text Cleaner** (`text_cleaner.py`)
   - Normalizes text content
   - Removes artifacts and noise
   - Prepares text for chunking

4. **Text Chunker** (`chunker.py`)
   - Splits documents into manageable chunks
   - Supports multiple chunking strategies
   - Maintains context overlap

5. **Text Embedder** (`embedder.py`)
   - Generates vector embeddings using Nomic/Ollama
   - Supports multiple embedding models
   - Handles batch processing

6. **Vector Store** (`vector_store.py`)
   - In-memory vector database
   - Similarity search capabilities
   - Persistent storage via pickle

7. **Retriever** (`retriever.py`)
   - Semantic search functionality
   - Hybrid search options
   - Result ranking and filtering

8. **LLM Answer Generator** (`llm_answer.py`)
   - Integrates with Ollama Llama 3.1
   - Context-aware answer generation
   - Source citation and formatting

## Frontend Architecture

### Technology Stack
- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS + Radix UI components
- **State Management**: Zustand
- **Data Fetching**: TanStack Query
- **Icons**: Lucide React

### Project Structure

```
front-end/src/
├── app/
│   ├── dashboard/
│   │   ├── page.tsx                 # Main dashboard
│   │   ├── documents/
│   │   │   ├── upload/              # Document upload interface
│   │   │   ├── chat/                # Q&A interface
│   │   │   ├── processing/          # Processing status
│   │   │   └── completed/           # Processed documents
│   │   └── ...                      # Other dashboard pages
│   ├── layout.tsx                   # Root layout
│   ├── page.tsx                     # Home page (redirects)
│   └── globals.css                  # Global styles
├── components/
│   ├── layout/                      # Layout components
│   │   ├── dashboard-layout.tsx     # Main dashboard layout
│   │   ├── sidebar.tsx              # Navigation sidebar
│   │   └── top-navbar.tsx          # Top navigation
│   ├── dashboard/                   # Dashboard-specific components
│   ├── documents/                   # Document-related components
│   └── ui/                         # Reusable UI components
├── lib/
│   ├── api/                         # API client functions
│   │   ├── vat-validation.ts        # VAT validation API
│   │   └── rag-documents.ts         # RAG documents API
│   ├── utils.ts                     # Utility functions
│   └── store/                       # State management
└── public/                          # Static assets
```

### Key Frontend Features

#### 1. Dashboard Layout
- **Responsive sidebar navigation** with collapsible sections
- **Top navigation bar** with user profile
- **Main content area** with proper routing

#### 2. Document Management
- **Upload Interface**: Drag-and-drop file upload with progress tracking
- **Processing Status**: Real-time updates on document processing pipeline
- **Chat Interface**: Q&A with uploaded documents using RAG
- **Document Preview**: PDF and text file preview capabilities

#### 3. Company Search & Validation
- **VAT Validation**: European VAT number validation
- **KBO Data Integration**: Belgian company information retrieval
- **AI Summaries**: KYC/AML compliance summaries using Llama 3.1

## Data Flow Architecture

### 1. Document Processing Flow

```
User Upload → Frontend → FastAPI → RAG Service → RAG Pipeline → Vector Store
     │              │         │            │             │              │
     │              │         │            │             │              │
     ▼              ▼         ▼            ▼             ▼              ▼
Upload File → API Call → Session → Text Extract → Embeddings → Store Vectors
```

#### Detailed Steps:
1. **Upload**: User selects files via Next.js interface
2. **API Call**: Frontend sends files to `/api/rag/upload`
3. **Session Creation**: RAG Service creates unique session
4. **Processing Pipeline**: Documents go through extraction → cleaning → chunking → embedding
5. **Vector Storage**: Embeddings stored in in-memory vector database
6. **Query Ready**: System ready for semantic search and Q&A

### 2. VAT Validation Flow

```
User Input → Frontend → FastAPI → EU VIES Service → Response
     │         │         │           │               │
     │         │         │           │               │
     ▼         ▼         ▼           ▼               ▼
VAT Form → API Call → SOAP Request → Validation → Company Data
```

#### Detailed Steps:
1. **Input**: User enters VAT number in frontend form
2. **Validation**: Frontend validates format before API call
3. **API Request**: FastAPI calls EU VIES SOAP service
4. **Response**: Validation results with company information
5. **Optional**: KBO data fetching for Belgian companies
6. **AI Analysis**: Optional Llama 3.1 summary generation

## Integration Points

### 1. Frontend ↔ Backend Communication

#### API Client Architecture
- **TypeScript Interfaces**: Strongly typed request/response models
- **Error Handling**: Comprehensive error catching and user-friendly messages
- **Authentication**: Session-based authentication (prepared for future implementation)
- **Environment Configuration**: Configurable API endpoints

#### Key API Integrations:
```typescript
// VAT Validation
await validateVAT({ country_code: 'BE', vat_number: '0403200393' })

// Document Upload
await uploadDocuments(files, sessionId)

// Document Query
await queryDocuments(sessionId, "What are the compliance requirements?")
```

### 2. Backend Service Communication

#### Web Researcher ↔ RAG Researcher
- **Shared Dependencies**: Common RAG modules imported from `rag_researcher`
- **Session Management**: In-memory session storage with cleanup
- **Pipeline Orchestration**: Coordinated document processing

#### External Services Integration
- **Ollama**: Local LLM service for embeddings and text generation
- **EU VIES**: SOAP-based VAT validation service
- **KBO Database**: Web scraping for Belgian company data

## Technology Dependencies

### Backend Dependencies

#### Core Framework
- **FastAPI 0.109.0+**: Modern async web framework
- **Uvicorn**: ASGI server for production deployment
- **Pydantic**: Data validation and serialization

#### RAG Pipeline
- **sentence-transformers**: Text embedding models
- **nomic**: Nomic embedding integration
- **groq**: Alternative LLM provider support
- **numpy/scipy**: Vector operations and similarity calculations

#### Document Processing
- **PyPDF2/PyMuPDF**: PDF text extraction
- **pdfplumber**: Advanced PDF processing
- **pytesseract**: OCR capabilities
- **Pillow**: Image processing

#### External Integrations
- **zeep**: SOAP client for EU VIES
- **requests**: HTTP client for web scraping
- **python-multipart**: File upload handling

### Frontend Dependencies

#### Core Framework
- **Next.js 14**: React framework with App Router
- **React 18**: UI library
- **TypeScript**: Type-safe JavaScript

#### UI Components
- **Radix UI**: Headless component library
- **Tailwind CSS**: Utility-first CSS framework
- **Lucide React**: Icon library
- **Framer Motion**: Animation library

#### Data Management
- **TanStack Query**: Server state management
- **Zustand**: Client state management
- **Axios/Fetch**: HTTP client utilities

## Deployment Architecture

### Development Environment
```
Frontend: http://localhost:3000 (Next.js dev server)
Backend:  http://localhost:8000 (FastAPI dev server)
Ollama:   http://localhost:11434 (Local LLM service)
```

### Production Considerations
1. **Frontend Deployment**: Static site generation or server-side deployment
2. **Backend Deployment**: Containerized FastAPI with proper ASGI server
3. **Database**: Vector database for production (Pinecone, Weaviate, etc.)
4. **LLM Service**: Managed LLM API or self-hosted Ollama cluster
5. **Load Balancing**: Multiple FastAPI instances behind load balancer
6. **Monitoring**: Logging, metrics, and health checks

## Security Considerations

### Current Implementation
1. **CORS Configuration**: Proper cross-origin resource sharing setup
2. **Input Validation**: Pydantic models for request validation
3. **File Upload Security**: File type and size restrictions
4. **Error Handling**: Safe error messages without information disclosure

### Future Enhancements
1. **Authentication**: JWT-based authentication system
2. **Authorization**: Role-based access control
3. **Rate Limiting**: API endpoint protection
4. **Data Encryption**: Sensitive data protection at rest
5. **Audit Logging**: Comprehensive activity tracking

## Performance Optimizations

### Backend Optimizations
1. **Async Processing**: Non-blocking I/O operations
2. **Batch Processing**: Efficient embedding generation
3. **Memory Management**: Vector store optimization
4. **Caching**: Response caching where appropriate

### Frontend Optimizations
1. **Code Splitting**: Route-based code division
2. **Image Optimization**: Next.js image optimization
3. **Lazy Loading**: Component lazy loading
4. **State Management**: Efficient state updates

## Migration to FastAPI

### Current State Assessment
The project already uses FastAPI for the web-researcher service, but the RAG researcher uses a standalone orchestrator. For a complete FastAPI migration:

### Migration Strategy

#### 1. Unify Backend Services
```python
# Current: Separate services
backend/web-researcher/main.py      # FastAPI service
backend/rag_researcher/orchestrator.py  # Standalone script

# Proposed: Unified FastAPI service
backend/main.py                     # Single FastAPI application
├── api/v1/
│   ├── vat_validation.py          # VAT endpoints
│   ├── rag_documents.py           # RAG endpoints
│   └── company_search.py          # Company search endpoints
├── core/
│   ├── config.py                  # Configuration management
│   ├── security.py                # Security utilities
│   └── dependencies.py            # FastAPI dependencies
├── services/
│   ├── rag_service.py             # RAG business logic
│   ├── vat_service.py             # VAT validation logic
│   └── llm_service.py             # LLM integration
└── models/
    ├── rag_models.py              # RAG Pydantic models
    └── vat_models.py              # VAT Pydantic models
```

#### 2. Database Integration
Replace in-memory storage with proper database:
- **PostgreSQL**: Structured data (sessions, users, entities)
- **Vector Database**: Chroma, Pinecone, or Weaviate for embeddings
- **Redis**: Session caching and temporary storage

#### 3. API Standardization
Implement consistent API patterns:
```python
# Standard API response model
class APIResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    timestamp: datetime

# Standard pagination
class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    size: int
    pages: int
```

#### 4. Authentication & Authorization
```python
from fastapi_users import FastAPIUsers
from fastapi_users.authentication import JWTAuthentication

# User management integration
jwt_authentication = JWTAuthentication(
    secret=SECRET, lifetime_seconds=3600, tokenUrl="auth/jwt/login"
)

fastapi_users = FastAPIUsers(
    user_db, [jwt_authentication], User, UserCreate, UserUpdate, UserDB
)
```

#### 5. Background Tasks
Replace manual threading with FastAPI background tasks:
```python
from fastapi import BackgroundTasks

@app.post("/api/rag/process")
async def process_documents_background(
    session_id: str,
    background_tasks: BackgroundTasks
):
    background_tasks.add_task(process_documents_task, session_id)
    return {"message": "Processing started"}
```

### Migration Benefits
1. **Unified Architecture**: Single entry point for all services
2. **Better Scalability**: Proper async/await patterns throughout
3. **Enhanced Security**: Integrated authentication and authorization
4. **Improved Monitoring**: Centralized logging and metrics
5. **Easier Deployment**: Single container deployment
6. **Better Testing**: Integrated testing with TestClient

## Conclusion

The Yottanest project demonstrates a sophisticated AML/KYC compliance platform with:

- **Modern Tech Stack**: Next.js frontend with FastAPI backend
- **AI Integration**: Local LLM capabilities with Ollama and Llama 3.1
- **Document Intelligence**: Comprehensive RAG pipeline for document Q&A
- **Regulatory Compliance**: VAT validation and company verification
- **Scalable Architecture**: Modular design ready for production deployment

The migration to a unified FastAPI backend would enhance the platform's maintainability, security, and scalability while preserving all existing functionality. The current architecture provides a solid foundation for implementing enterprise-grade compliance solutions.