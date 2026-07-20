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

class RAGService:
    def __init__(self, search_engine=None):
        if search_engine is None:
            embedding_service = EmbeddingService()
            vector_store = VectorStore()
            self.search_engine = SearchEngine(embedding_service, vector_store)
        else:
            self.search_engine = search_engine
        
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
        
        gemini_api_key = os.environ.get("GOOGLE_API_KEY")
        if not gemini_api_key:
            logging.warning("GOOGLE_API_KEY missing.")
            
        self.fallback_client = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=gemini_api_key,
            temperature=0.1,
            max_retries=2,
            timeout=30.0
        ) if gemini_api_key else None

    def generate_answer(self, query: str, chat_history: list = None, debug: bool = False, base_where: dict = None):
        t0 = time.time()
        
        # 1. Query Preprocessing
        clean_query = QueryAnalyzer.preprocess(query)
        
        # 2. Intent & Filters
        intent = QueryAnalyzer.detect_intent(clean_query)
        filters = QueryAnalyzer.extract_filters(clean_query)
        
        final_where = {"is_latest": 1}
        if base_where:
            final_where.update(base_where)
        if filters:
            final_where.update(filters)
            
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
            logging.warning(f"[LLM] Primary failed: {str(e)}")
            try:
                if not self.fallback_client:
                    raise ValueError("Fallback client not initialized.")
                logging.info("[LLM] Attempting Fallback (Gemini)")
                response = self.fallback_client.invoke(messages)
                response_content = response.content
                generated_by = "Gemini"
            except Exception as fallback_e:
                logging.error(f"[LLM] Fallback failed: {str(fallback_e)}")
                response_content = '{"answer": "System is currently unavailable.", "citations": [], "confidence_score": 0.0, "follow_up_questions": []}'
                generated_by = "Error"
                
        llm_latency = time.time() - t_llm_start
        
        # 9. Parsing JSON
        try:
            if isinstance(response_content, str):
                content = response_content.strip()
            else:
                content = str(response_content).strip()
                
            # Safely extract JSON
            match = re.search(r'\{.*\}', content, re.DOTALL)
            if match:
                parsed = json.loads(match.group())
            else:
                # Fallback if LLM forgets JSON format
                parsed = {
                    "answer": content,
                    "citations": [],
                    "confidence_score": 0.5,
                    "follow_up_questions": []
                }
        except Exception:
            parsed = {
                "answer": "Failed to parse LLM response.",
                "citations": [],
                "confidence_score": 0.0,
                "follow_up_questions": []
            }
            
        # 10. Observability
        total_latency = time.time() - t0
        logging.info(f"[RAG Trace] Latency - Total: {total_latency:.2f}s | Retrieval: {retrieval_latency:.2f}s | LLM: {llm_latency:.2f}s | Provider: {generated_by}")
        
        # Normalize output
        return {
            "answer": parsed.get("answer", ""),
            "citations": parsed.get("citations", []),
            "confidence_score": parsed.get("confidence_score", 0.0),
            "follow_up_questions": parsed.get("follow_up_questions", []),
            "provider": generated_by,
            "intent": intent
        }
