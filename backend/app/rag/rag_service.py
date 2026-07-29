import os
import json
import re
import time
import logging

# pyrefly: ignore [missing-import]
from langchain_google_genai import ChatGoogleGenerativeAI
# pyrefly: ignore [missing-import]
from langchain_groq import ChatGroq
# pyrefly: ignore [missing-import]
from langchain_core.messages import SystemMessage, HumanMessage

from app.rag.search.engine import SearchEngine
from app.rag.vector_store import VectorStore
from app.rag.embedding_service import EmbeddingService
from app.rag.prompt_builder import PromptBuilder
from app.rag.query_analyzer import QueryAnalyzer
from app.rag.reranker import Reranker
from app.rag.context_builder import ContextBuilder
from app.rag.retrieval_service import RetrievalService

class RAGService:
    def __init__(self, search_engine=None):
        embedding_service = EmbeddingService()
        vector_store = VectorStore()
        if search_engine is None:
            self.search_engine = SearchEngine(embedding_service, vector_store)
        else:
            self.search_engine = search_engine
        
        self.retrieval_service = RetrievalService(embedding_service, vector_store)
        
        groq_api_key = os.environ.get("GROQ_API_KEY")
        if not groq_api_key:
            logging.warning("GROQ_API_KEY missing.")
            
        self.primary_client = ChatGroq(
            model="openai/gpt-oss-120b",
            temperature=0,
            api_key=groq_api_key,
            max_retries=3,
            timeout=30.0
        ) if groq_api_key else None
        


    def generate_answer(self, query: str, chat_history: list = None, debug: bool = False, base_where: dict = None):
        t0 = time.time()
        
        # 1. Query Preprocessing
        clean_query = QueryAnalyzer.preprocess(query)
        
        # 2. Intent & Filters
        intent = QueryAnalyzer.detect_intent(clean_query)
        filters = QueryAnalyzer.extract_filters(clean_query)
        
        # Only apply is_latest for enterprise documents.
        # Personal documents are never versioned so this field does not exist.
        is_personal = base_where and "namespace" in base_where
        final_where = {} if is_personal else {"is_latest": 1}
        if filters:
            final_where.update(filters)
        if base_where:
            final_where.update(base_where)
            
        # 3. Query Expansion
        expanded_query = QueryAnalyzer.expand_query(clean_query)
        
        if debug:
            logging.info(f"Intent: {intent} | Filters: {filters} | Expanded: {expanded_query}")
            
        # 4. Retrieval (MMR built-in to retrieval_service)
        # Using expanded query for retrieval
        t_retrieval_start = time.time()
        retrieved_chunks = self.retrieval_service.retrieve(
            expanded_query, 
            top_k=10, 
            fetch_k=30, 
            lambda_mult=0.6, 
            where=final_where
        )
        retrieval_latency = time.time() - t_retrieval_start
        
        # 5. Reranking
        ranked_chunks = Reranker.rerank(clean_query, retrieved_chunks)
        top_chunks = ranked_chunks[:5] # Keep top 5 for LLM context
        
        if not top_chunks:
            return {
                "answer": "I couldn't find sufficient evidence.",
                "citations": [],
                "confidence_score": 0.0,
                "follow_up_questions": [],
                "provider": "None",
                "intent": intent
            }
            
        # Calculate server-side confidence
        distances = [c.get("distance", 1.0) for c in top_chunks]
        avg_distance = sum(distances) / len(distances) if distances else 1.0
        # Lower distance is better in most vector stores. Let's invert it for a 0-1 confidence score.
        confidence = max(0.0, min(1.0, 1.0 - (avg_distance / 2.0)))
        
        # Build server-side citations mapping
        citations = []
        for i, chunk in enumerate(top_chunks, 1):
            meta = chunk.get('metadata', {})
            citations.append({
                "evidence_id": i,
                "document_id": meta.get('document_id', 'Unknown'),
                "document_name": meta.get('filename', meta.get('source', 'Unknown')),
                "version": meta.get('version_number', 1),
                "page": meta.get('page', meta.get('page_no', 'N/A')),
                "section": meta.get('heading', meta.get('section', 'N/A')),
                "chunk_id": chunk.get('chunk_id', 'N/A'),
                "similarity_score": 1.0 - chunk.get('distance', 1.0)
            })
        
        # 6. Context Building
        context_str = ContextBuilder.build_context(top_chunks)
        
        # 7. Prompt Building
        prompt = PromptBuilder.build_rag_prompt(clean_query, context_str, chat_history)
        messages = [
            SystemMessage(content=PromptBuilder.get_system_prompt()),
            HumanMessage(content=prompt)
        ]
        
        # 8. LLM Orchestration
        t_llm_start = time.time()
        response_content = ""
        generated_by = "None"
        
        try:
            if not self.primary_client:
                raise ValueError("Primary client not initialized.")
            logging.info("[LLM] Attempting Primary (Groq)")
            response = self.primary_client.invoke(messages)
            response_content = response.content
            generated_by = "Groq"
        except Exception as e:
            logging.error(f"[LLM] Primary failed: {str(e)}")
            response_content = '{"answer": "System is currently unavailable.", "citations": [], "confidence_score": 0.0, "follow_up_questions": []}'
            generated_by = "Error"
                
        llm_latency = time.time() - t_llm_start
        
        # 9. Parsing JSON
        try:
            if isinstance(response_content, str):
                content = response_content.strip()
            else:
                content = str(response_content).strip()
        except Exception:
            content = "Failed to parse LLM response."
            
        # 10. Observability
        total_latency = time.time() - t0
        logging.info(f"[RAG Trace] Latency - Total: {total_latency:.2f}s | Retrieval: {retrieval_latency:.2f}s | LLM: {llm_latency:.2f}s | Provider: {generated_by}")
        
        # Normalize output
        return {
            "answer": content,
            "citations": citations,
            "confidence_score": confidence,
            "follow_up_questions": [],
            "provider": generated_by,
            "intent": intent
        }

    async def generate_answer_stream(self, query: str, chat_history: list = None, base_where: dict = None, trace_id: str = "unknown"):
        import asyncio
        from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
        
        t0 = time.time()
        
        yield f'data: {json.dumps({"type": "status", "message": "Analyzing query..."})}\n\n'
        
        # 1. Query Preprocessing
        clean_query = QueryAnalyzer.preprocess(query)
        intent = QueryAnalyzer.detect_intent(clean_query)
        filters = QueryAnalyzer.extract_filters(clean_query)
        
        is_personal = base_where and "namespace" in base_where
        final_where = {} if is_personal else {"is_latest": 1}
        if filters: final_where.update(filters)
        if base_where: final_where.update(base_where)
            
        expanded_query = QueryAnalyzer.expand_query(clean_query)
        
        yield f'data: {json.dumps({"type": "status", "message": "Searching documents..."})}\n\n'
        
        # Retrieval with 15s timeout
        t_retrieval = time.time()
        max_retries = 3
        retrieved_chunks = []
        for attempt in range(max_retries):
            try:
                # Run the sync retrieval in a thread pool to avoid blocking the async event loop
                retrieved_chunks = await asyncio.wait_for(
                    asyncio.to_thread(
                        self.retrieval_service.retrieve, expanded_query, top_k=10, fetch_k=30, lambda_mult=0.6, where=final_where
                    ),
                    timeout=15.0
                )
                break
            except asyncio.TimeoutError:
                logging.error(f"[Trace: {trace_id}] Retrieval timed out after 15s")
                yield f'data: {json.dumps({"type": "error", "message": "Document search timed out."})}\n\n'
                return
            except Exception as e:
                logging.error(f"[Trace: {trace_id}] Retrieval failed on attempt {attempt+1}: {e}", exc_info=True)
                if attempt == max_retries - 1:
                    yield f'data: {json.dumps({"type": "error", "message": "Failed to search documents."})}\n\n'
                    return
                await asyncio.sleep(2 ** attempt)
            
        retrieval_latency = time.time() - t_retrieval
        
        ranked_chunks = Reranker.rerank(clean_query, retrieved_chunks)
        top_chunks = ranked_chunks[:5]
        
        if not top_chunks:
            yield f'data: {json.dumps({"type": "chunk", "text": "I couldn\'t find sufficient evidence in your documents to answer this."})}\n\n'
            yield f'data: {json.dumps({"type": "done", "citations": [], "confidence": 0.0, "provider": "None", "latency_ms": int((time.time()-t0)*1000)})}\n\n'
            return
            
        distances = [c.get("distance", 1.0) for c in top_chunks]
        avg_distance = sum(distances) / len(distances) if distances else 1.0
        confidence = max(0.0, min(1.0, 1.0 - (avg_distance / 2.0)))
        
        citations = []
        for i, chunk in enumerate(top_chunks, 1):
            meta = chunk.get('metadata', {})
            citations.append({
                "evidence_id": i,
                "document_id": meta.get('document_id', 'Unknown'),
                "document_name": meta.get('filename', meta.get('source', 'Unknown')),
                "version": meta.get('version_number', 1),
                "page": meta.get('page', meta.get('page_no', 'N/A')),
                "section": meta.get('heading', meta.get('section', 'N/A')),
                "chunk_id": chunk.get('chunk_id', 'N/A'),
                "similarity_score": 1.0 - chunk.get('distance', 1.0)
            })
            
        context_str = ContextBuilder.build_context(top_chunks)
        prompt = PromptBuilder.build_rag_prompt(clean_query, context_str, chat_history)
        messages = [
            SystemMessage(content=PromptBuilder.get_system_prompt()),
            HumanMessage(content=prompt)
        ]
        
        yield f'data: {json.dumps({"type": "status", "message": "Generating answer..."})}\n\n'
        
        t_llm = time.time()
        generated_by = "Groq"
        full_response = ""
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if not self.primary_client:
                    raise ValueError("LLM client not initialized")
                
                gen = self.primary_client.astream(messages)
                while True:
                    try:
                        chunk = await asyncio.wait_for(gen.__anext__(), timeout=60.0)
                        content = chunk.content
                        if content:
                            full_response += content
                            yield f'data: {json.dumps({"type": "chunk", "text": content})}\n\n'
                    except StopAsyncIteration:
                        break
                        
                # If we finish successfully without exception, break the retry loop
                break
            except asyncio.TimeoutError:
                logging.error(f"[Trace: {trace_id}] LLM generation timed out after 60s")
                yield f'data: {json.dumps({"type": "error", "message": "LLM generation timed out."})}\n\n'
                return
            except Exception as e:
                logging.error(f"[Trace: {trace_id}] LLM generation failed on attempt {attempt+1}: {e}", exc_info=True)
                if attempt == max_retries - 1:
                    yield f'data: {json.dumps({"type": "error", "message": "Failed to generate answer after retries."})}\n\n'
                    return
                # Wait before retry
                await asyncio.sleep(2 ** attempt)
            
        llm_latency = time.time() - t_llm
        total_latency = time.time() - t0
        
        logging.info(f"[Trace: {trace_id}] Latency - Total: {total_latency:.2f}s | Retrieval: {retrieval_latency:.2f}s | LLM: {llm_latency:.2f}s | Provider: {generated_by}")
        
        # Send final citations and completion event
        yield f'data: {json.dumps({"type": "done", "citations": citations, "confidence": confidence, "provider": generated_by, "latency_ms": int(total_latency*1000), "full_answer": full_response})}\n\n'

