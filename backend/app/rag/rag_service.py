import os
# pyrefly: ignore [missing-import]
from groq import Groq
from app.rag.retrieval_service import RetrievalService

class RAGService:
    def __init__(self, retrieval_service=None):
        self.retrieval_service = retrieval_service or RetrievalService()
        self.client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        self.model = "llama-3.1-8b-instant" # Updated to supported Groq model
        
    def generate_answer(self, query: str):
        # 1. Retrieve relevant document chunks
        relevant_chunks = self.retrieval_service.retrieve(query, top_k=5)
        
        # 2. Build LLM context
        context_parts = []
        for chunk in relevant_chunks:
            source = chunk.get('metadata', {}).get('source', 'Unknown Document')
            page = chunk.get('metadata', {}).get('page_no', 'N/A')
            context_parts.append(f"Source: {source} (Page {page})\nText: {chunk['text']}")
            
        context_str = "\n\n".join(context_parts)
        
        # 3. Build Prompt
        prompt = f"""You are an industrial knowledge AI assistant (RATAN).
Use the following pieces of retrieved context to answer the question. 
If you don't know the answer, just say that you don't know. 
Do not hallucinate or make up information. Use citations where possible based on the source metadata.

Context:
{context_str}

Question:
{query}

Answer:"""

        # 4. Generate response
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful industrial AI assistant that answers operational questions accurately based on provided documentation context."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model=self.model,
                temperature=0.1
            )
            answer = chat_completion.choices[0].message.content
        except Exception as e:
            answer = f"Error generating answer: {str(e)}"
        
        return {
            "answer": answer,
            "citations": relevant_chunks
        }
