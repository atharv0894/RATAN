# RAG Pipeline Architecture

RATAN features an industrial-grade Retrieval-Augmented Generation (RAG) pipeline designed for both broad enterprise document retrieval and strictly isolated personal queries.

## Pipeline Architecture

```mermaid
flowchart TD
    Query[User Query] --> Intent[Intent Detection & Query Analysis]
    
    subgraph "Retrieval"
        Intent --> Expand[Query Expansion]
        Expand --> Embed[Embedding Generation (FastEmbed)]
        Embed --> VectorDB[(Qdrant Vector DB)]
        VectorDB -->|Metadata Filters| Filtered[Filtered Results]
    end
    
    subgraph "Reranking & Context"
        Filtered --> MMR[Maximal Marginal Relevance]
        MMR --> ContextBuilder[Context Builder]
    end
    
    subgraph "Generation"
        ContextBuilder --> Prompt[Prompt Assembly]
        Prompt --> LLM[LLM Primary: Groq]
        LLM -.->|Fallback| LLMF[LLM Fallback: Gemini]
    end
    
    LLM --> JSON[JSON Parser]
    JSON --> Response[Structured RAG Response]
    
    Response --> Citations[Citations & Confidence]
```

## 1. Document Ingestion
1. **Parsing**: PDF, TXT, CSV, and Markdown files are parsed to extract raw text.
2. **Chunking**: Text is chunked using recursive character splitting (chunk size ~1000 tokens, overlap ~200) to maintain semantic context.
3. **Metadata Extraction**: Chunks are enriched with metadata:
   - `organization_id` (Enterprise)
   - `namespace` (`personal/{user_id}`) (Personal)
   - `document_id`
   - `page_no`
4. **Embedding**: Chunks are embedded using `BAAI/bge-small-en-v1.5` via the `fastembed` library. This model is chosen for its efficiency and low memory footprint (133MB), allowing it to run entirely locally without external API costs.
5. **Storage**: Embeddings and metadata are pushed to **Qdrant**.

## 2. Query Processing
1. **Intent Detection**: The query is analyzed to determine if it is conversational, analytical, or a direct search.
2. **Expansion**: Technical synonyms and alternative phrasing are generated to improve recall.

## 3. Retrieval
The pipeline performs a vector similarity search (Cosine Distance) in Qdrant. 
- **Strict Isolation**: The query is *hard-filtered* at the database level by the user's `organization_id` or `namespace`. Data bleed across tenants is structurally impossible.
- **MMR**: Maximal Marginal Relevance is applied to ensure diversity in the retrieved chunks, preventing the context window from being flooded with repetitive information.

## 4. Generation
The retrieved chunks are formatted into a structured prompt alongside the user's query and chat history.
- **Primary LLM**: Groq (`gpt-oss-120b` or Llama 3) for ultra-low latency generation.
- **Fallback LLM**: Google Gemini (`gemini-2.5-flash`) triggers automatically if Groq is unavailable or rate-limited.
- **Structured Output**: The LLM is instructed to output strict JSON containing the `answer`, `citations` (mapped back to the source document and page number), `confidence_score`, and `follow_up_questions`.
