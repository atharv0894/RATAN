import re
import hashlib

class Chunker:
    def __init__(self, max_chars: int = 1500, overlap_chars: int = 200):
        self.max_chars = max_chars
        self.overlap_chars = overlap_chars

    def chunk_page_with_metadata(self, page, base_metadata: dict) -> list[dict]:
        """
        Splits a ParsedPage into chunks, preserving tables and section boundaries.
        """
        text = page.text
        if not text and not page.tables:
            return []
            
        chunks_info = []
        # Match headings like "1. Purpose" or "10. Quality Checks"
        section_pattern = re.compile(r'^(\d+\.\s+[A-Z].*)$')
        
        lines = text.split('\n')
        
        sections = []
        current_section_title = base_metadata.get('section', "General")
        current_section_lines = []
        
        for line in lines:
            match = section_pattern.match(line.strip())
            if match:
                if current_section_lines:
                    sections.append((current_section_title, "\n".join(current_section_lines)))
                current_section_title = match.group(1).strip()
                current_section_lines = [line]
            else:
                current_section_lines.append(line)
                
        if current_section_lines:
            sections.append((current_section_title, "\n".join(current_section_lines)))
            
        # Add tables as separate chunks to avoid splitting them
        if hasattr(page, 'tables') and page.tables:
            for table_idx, table in enumerate(page.tables):
                table_text = f"Table {table_idx + 1}:\n" + str(table.get('data', ''))
                sections.append((current_section_title + " (Table)", table_text))
            
        chunk_idx = 0
        for sec_title, sec_text in sections:
            start = 0
            while start < len(sec_text):
                end = min(start + self.max_chars, len(sec_text))
                
                if end < len(sec_text):
                    # Try to break at a newline
                    last_newline = sec_text.rfind('\n', start, end)
                    if last_newline != -1 and last_newline > start + (self.max_chars // 2):
                        end = last_newline
                    else:
                        # Try to break at a period
                        last_period = sec_text.rfind('. ', start, end)
                        if last_period != -1 and last_period > start + (self.max_chars // 2):
                            end = last_period + 1
                            
                chunk_str = sec_text[start:end].strip()
                if chunk_str:
                    source = base_metadata.get('source', 'unknown')
                    page = base_metadata.get('page_no', 0)
                    
                    # deterministic hash for dedup
                    content_hash = hashlib.sha256(chunk_str.lower().encode('utf-8')).hexdigest()
                    chunk_id = f"{source}_{page}_{content_hash}"
                    
                    meta = base_metadata.copy()
                    meta['section'] = sec_title
                    meta['chunk_id'] = chunk_id
                    
                    chunks_info.append({
                        "text": chunk_str,
                        "metadata": meta,
                        "chunk_id": chunk_id
                    })
                    chunk_idx += 1
                    
                start = end - self.overlap_chars
                if start <= 0 or end == len(sec_text):
                    if end == len(sec_text):
                        break
                        
        return chunks_info
