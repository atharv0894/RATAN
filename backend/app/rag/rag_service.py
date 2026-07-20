import os
import json
import re
import logging

# pyrefly: ignore [missing-import]
from langchain_google_genai import ChatGoogleGenerativeAI
# pyrefly: ignore [missing-import]
from langchain_groq import ChatGroq
# pyrefly: ignore [missing-import]
from langchain_core.messages import SystemMessage, HumanMessage
from app.rag.retrieval_service import RetrievalService
from app.rag.prompt_builder import PromptBuilder

class RAGService:
    def __init__(self, retrieval_service=None):
        self.retrieval_service = retrieval_service or RetrievalService()
        # Primary LLM: Groq
        groq_api_key = os.environ.get("GROQ_API_KEY")
        if not groq_api_key:
            raise ValueError("GROQ_API_KEY environment variable is missing or empty.")
            
        self.primary_client = ChatGroq(
            model="openai/gpt-oss-120b",
            temperature=0,
            api_key=groq_api_key,
            max_retries=5
        )
        
        # Fallback LLM: Gemini
        gemini_api_key = os.environ.get("GOOGLE_API_KEY")
        if not gemini_api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is missing or empty.")
            
        self.fallback_client = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=gemini_api_key,
            temperature=0.1,
            max_retries=1
        )
    def _decompose_query(self, query: str) -> list[str]:
        prompt = f"""Decompose the following complex query into a list of 2 to 4 simple, focused sub-queries for a search engine. 
Only output a valid JSON list of strings. Do not add any other text.
Query: {query}"""
        try:
            messages = [HumanMessage(content=prompt)]
            response = self.fallback_client.invoke(messages)
            if isinstance(response.content, str):
                content = response.content.strip()
            elif isinstance(response.content, list):
                content = "".join([part.get("text", "") if isinstance(part, dict) else str(part) for part in response.content]).strip()
            else:
                content = str(response.content).strip()
            match = re.search(r'\[.*\]', content, re.DOTALL)
            if match:
                parsed = json.loads(match.group())
                if isinstance(parsed, list) and all(isinstance(x, str) for x in parsed):
                    return parsed
            return [query]
        except Exception:
            # Deterministic fallback
            return [query]

    def generate_answer(self, query: str, debug: bool = False, where: dict = None):
        sub_queries = self._decompose_query(query)
        if query not in sub_queries:
            sub_queries.insert(0, query)
            
        all_retrieved = []
        seen_chunks = set()
        
        # Force searching only the latest versions of documents
        final_where = {"is_latest": 1}
        if where:
            final_where.update(where)
        
        if debug:
            logging.info("\n[RETRIEVAL DEBUG]")
            logging.info(f"Original Query: {query}")
            for i, sq in enumerate(sub_queries):
                if sq != query:
                    logging.info(f"Sub-query {i}: {sq}")
                    
        for sq in sub_queries:
            chunks = self.retrieval_service.retrieve(sq, top_k=6, fetch_k=20, lambda_mult=0.6, where=final_where)
            for chunk in chunks:
                chunk_id = chunk.get('chunk_id')
                if chunk_id not in seen_chunks:
                    seen_chunks.add(chunk_id)
                    all_retrieved.append(chunk)
                    
        # Rerank with MMR using original query
        query_embedding = self.retrieval_service.embedding_service.generate_embeddings([query])[0]
        embeddings = [self.retrieval_service.embedding_service.generate_embeddings([c['text']])[0] for c in all_retrieved]
        
        final_chunks = self.retrieval_service.mmr(
            query_embedding, all_retrieved, embeddings, k=8, lambda_mult=0.5
        )
        
        if debug:
            for rank, chunk in enumerate(final_chunks, 1):
                meta = chunk['metadata']
                logging.info(f"Rank {rank} | Chunk ID: {chunk['chunk_id']} | Source: {meta.get('source')} | Page: {meta.get('page_no')} | Score: {chunk['distance']:.4f}")
                
        prompt = PromptBuilder.build_rag_prompt(query, final_chunks)
        
        try:
            messages = [
                SystemMessage(content=PromptBuilder.get_system_prompt()),
                HumanMessage(content=prompt)
            ]
            
            # Primary attempt
            generated_by = "Groq / openai/gpt-oss-120b"
            logging.info("[LLM TRACE] CALL GPT-OSS (Groq)")
            if debug:
                logging.info(f"Primary LLM: {generated_by}")
                
            try:
                response = self.primary_client.invoke(messages)
                logging.info("[LLM TRACE] GPT SUCCESS")
            except Exception as e:
                error_str = str(e).lower()
                logging.warning(f"[LLM TRACE] GPT FAILED with error: {error_str}")
                is_fallback_condition = any(keyword in error_str for keyword in [
                    "429", "resource_exhausted", "rate limit", "quota", 
                    "unavailable", "503", "502", "500", "too many requests"
                ])
                
                if is_fallback_condition:
                    generated_by = "Gemini / gemini-2.5-flash"
                    logging.warning("[LLM TRACE] Fallback Started")
                    logging.info("[LLM TRACE] Gemini Called")
                    if debug:
                        logging.warning("Primary provider unavailable or quota limited.")
                        logging.info(f"Using fallback LLM: {generated_by}")
                    try:
                        response = self.fallback_client.invoke(messages)
                        logging.info("[LLM TRACE] Gemini Success")
                    except Exception as fallback_e:
                        logging.error(f"[LLM TRACE] Gemini Failed: {fallback_e}")
                        raise fallback_e
                else:
                    raise e
            
            if isinstance(response.content, str):
                content = response.content.strip()
            elif isinstance(response.content, list):
                content = "".join([part.get("text", "") if isinstance(part, dict) else str(part) for part in response.content]).strip()
            else:
                content = str(response.content).strip()
            
            # Safely parse JSON
            match = re.search(r'\{.*\}', content, re.DOTALL)
            if match:
                parsed = json.loads(match.group())
                answer_text = parsed.get("answer", content)
                used_ids = parsed.get("used_evidence_ids", [])
                
                # Filter final citations based on used_evidence_ids
                used_citations = []
                for chunk in final_chunks:
                    if chunk['chunk_id'] in used_ids:
                        used_citations.append(chunk)
                        
                final_citations = used_citations if used_citations else []
            else:
                answer_text = content
                final_citations = []
                
        except Exception as e:
            answer_text = f"Error generating answer: {str(e)}"
            final_citations = []
            generated_by = "Error"
            
        return {
            "answer": answer_text,
            "citations": final_citations,
            "provider": generated_by
        }
