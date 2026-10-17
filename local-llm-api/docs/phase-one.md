# Phase 1 — Local LLM Lab Foundation

## 1. Objective

Establish a local AI development environment that serves as the foundation for learning, experimenting with, evaluating, and eventually building production-oriented LLM applications.

The goal is to develop a single project incrementally, with each phase introducing new AI capabilities while preserving the existing foundation.

## 2. Planned Scope

Phase 1 focuses on establishing the core capabilities required for future AI application development.

- Local Large Language Model (LLM) inference.
- API-based access to the LLM.
- Basic conversational interactions.
- Conversation and request tracking.
- Performance benchmarking and evaluation.
- Persistent storage for application data.
- Vector database foundation for future Retrieval-Augmented Generation (RAG).
- Basic document management for future knowledge-based AI applications.

## 3. Achievements

### LLM Integration
- Established the foundation for running an LLM locally using Ollama.
- Enabled application-level interaction with the local model.
- Selected Qwen 3.5 4B as the initial model for experimentation.

### Chat Capabilities
- Established separate endpoints for conversations without memory and conversations using supplied message history.
- Defined structured request and response formats.
- Established the foundation for extending chat functionality in later phases.

### Observability and Evaluation
- Established persistent tracking of LLM requests.
- Planned recording of request status, execution timings, token metrics, and errors.
- Added a foundation for benchmark runs to compare model performance.

### Persistent Data Storage
- Established MySQL as the relational storage layer.
- Defined the initial data model for conversations, LLM requests, and benchmark runs.
- Established the foundation for tracking application activity and evaluating AI behavior over time.

### Vector Database and Document Management
- Selected ChromaDB as the initial vector database.
- Established the foundation for persistent document storage.
- Planned basic document CRUD capabilities: create, retrieve, list, update, and delete.
- Prepared the project for future semantic search and RAG capabilities.

### API Foundation
- Established FastAPI as the application API layer.
- Organized the application around separate functional modules.
- Established a health-check endpoint and cross-origin configuration for frontend integration.

## 4. Current Project Capabilities

| Capability | Status |
|---|---|
| Local LLM integration | Foundation established |
| Chat without memory | Implemented |
| Chat with supplied history | Implemented |
| MySQL data model | Established |
| LLM request tracking | Implemented in application logic |
| Benchmarking endpoint | Implemented in application logic |
| ChromaDB persistence | Foundation established |
| Document CRUD API | Implemented in code; runtime verification pending |
| Semantic search | Not started |
| Document chunking | Not started |
| RAG-based question answering | Not started |
| Automated evaluation framework | Not started |
| Production deployment | Not started |

*Note: Implementation status does not necessarily mean every endpoint has been tested end-to-end. Items requiring runtime verification should be confirmed before being considered complete.*

## 5. Phase 1 Completion Criteria

Phase 1 will be considered complete when:

- The API starts reliably without import or configuration errors.
- The local LLM responds successfully through the API.
- Chat requests and their execution results are recorded correctly.
- Benchmark runs can be executed and retrieved.
- Document operations work against persistent ChromaDB storage.
- Data remains available after restarting the application.
- The core endpoints are tested through the API documentation or an API client.

## 6. Out of Scope for Phase 1

The following capabilities are intentionally deferred:

- Retrieval-Augmented Generation (RAG).
- Semantic similarity search.
- Document ingestion pipelines and automatic chunking.
- Ollama-based embedding generation.
- Agentic AI and tool calling.
- Fine-tuning and model training.
- Production-grade authentication, scaling, and deployment.

These are future extensions rather than requirements for the initial foundation.

## 7. Next Phase

**Phase 2 — Embeddings, Semantic Search, and Basic RAG**

The next phase will extend the existing document management foundation into a searchable knowledge system.

Planned outcomes:

1. Understand embeddings and vector representations.
2. Generate embeddings for documents.
3. Store and retrieve document vectors.
4. Implement semantic similarity search.
5. Retrieve relevant context for a user query.
6. Send the retrieved context to the local LLM.
7. Build the first end-to-end RAG question-answering workflow.

## 8. Project Direction

The long-term objective is to evolve this single project into a practical AI engineering laboratory covering:

- LLM integration and inference.
- Model performance measurement.
- Embeddings and vector databases.
- RAG pipelines.
- AI agents and tool use.
- Evaluation, monitoring, and reliability.
- Deployment of AI-powered applications.

Each phase will build on the previous phase, producing a progressively more capable and demonstrable AI engineering project.
