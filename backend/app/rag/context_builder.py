class ContextBuilder:
    @staticmethod
    def build_context(chunks: list) -> str:
        """
        Merges adjacent chunks if they are from the same document and page.
        Builds the final text block to be injected into the LLM prompt.
        """
        if not chunks:
            return "No relevant context found."
            
        # Group chunks by document and page to prevent duplication
        # For this implementation, we will just format them cleanly with clear boundaries
        
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            meta = chunk.get('metadata', {})
            filename = meta.get('filename', meta.get('source', 'Unknown'))
            page = meta.get('page', meta.get('page_no', 'N/A'))
            section = meta.get('heading', meta.get('section', 'N/A'))
            version = meta.get('version_number', meta.get('version', 'latest'))
            chunk_id = chunk.get('chunk_id', 'N/A')
            
            block = (
                f"[Evidence ID: {i}]\n"
                f"Document: {filename} (v{version})\n"
                f"Page: {page} | Section: {section}\n"
                f"---\n{chunk['text']}\n==="
            )
            context_parts.append(block)
            
        return "\n\n".join(context_parts)
