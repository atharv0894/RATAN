import re
from typing import Dict, Any, List

class QueryAnalyzer:
    """Handles query preprocessing, intent detection, metadata extraction, and query expansion."""
    
    @staticmethod
    def preprocess(query: str) -> str:
        # Normalize whitespace
        query = re.sub(r'\s+', ' ', query).strip()
        # Case normalization and unit normalization could go here if needed
        return query
        
    @staticmethod
    def detect_intent(query: str) -> str:
        lower_query = query.lower()
        if any(w in lower_query for w in ['how to', 'procedure', 'steps', 'process']):
            return 'Procedure'
        elif any(w in lower_query for w in ['troubleshoot', 'fix', 'error', 'broken', 'issue']):
            return 'Troubleshooting'
        elif any(w in lower_query for w in ['safe', 'ppe', 'hazard', 'warning']):
            return 'Safety'
        elif any(w in lower_query for w in ['compare', 'difference', 'vs']):
            return 'Comparison'
        elif any(w in lower_query for w in ['summarize', 'summary', 'overview']):
            return 'Summary'
        return 'General'
        
    @staticmethod
    def extract_filters(query: str) -> Dict[str, Any]:
        """Extracts naive metadata filters from query text."""
        filters = {}
        # Naive extraction - in production this could use a fast NER model or exact match dictionaries
        lower_query = query.lower()
        
        # Example dummy matches for industrial terminology
        if 'plant 1' in lower_query:
            filters['plant'] = 'Plant 1'
        if 'maintenance' in lower_query:
            filters['department'] = 'Maintenance'
            
        return filters
        
    @staticmethod
    def expand_query(query: str) -> List[str]:
        """Expand abbreviations or synonyms."""
        expansions = {
            "sop": "standard operating procedure",
            "ppe": "personal protective equipment",
            "hvac": "heating, ventilation, and air conditioning"
        }
        expanded = query
        for k, v in expansions.items():
            if re.search(r'\b' + k + r'\b', expanded, re.IGNORECASE):
                expanded = re.sub(r'\b' + k + r'\b', f"{k} ({v})", expanded, flags=re.IGNORECASE)
                
        return expanded
