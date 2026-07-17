import re

# --- Entity Patterns ---

PATTERNS = {
    "Equipment": [
        r'\b(?:Pump|Valve|Motor|Tank|Compressor|Heat Exchanger|Turbine|Generator|Boiler|Reactor)\s+[A-Z0-9-]+\b',
        r'\b[PVMTCHGBR]-\d{2,4}[A-Z]?\b' # Matches P-101, V-204, etc.
    ],
    "Role": [
        r'\b(?:Operator|Supervisor|Maintenance Engineer|Quality Engineer|EHS Officer|Inspector|Technician|Manager)\b'
    ],
    "Standard": [
        r'\b(?:ISO|API|ASME|OISD|Factory Act|PESO|OSHA|IEC|IEEE)(?:\s+\d{3,5}(?:-\d{4})?)?\b'
    ],
    "Parameter": [
        r'\b(?:Pressure|Temperature|Flow Rate|Voltage|Current|RPM|Torque|Speed|Humidity)\b'
    ],
    "Metadata": [
        r'\b(?:Revision|Version)\s*(?:\d+(?:\.\d+)?|[A-Z])\b',
        r'\b(?:Issue Date|Effective Date):\s*\d{1,4}[-/.]\d{1,2}[-/.]\d{1,4}\b',
        r'\b(?:SOP Number|Document Number):\s*[A-Z0-9-]+\b'
    ],
    "Safety": [
        r'\b(?:PPE|Hazard|Lockout|Tagout|LOTO|Emergency|Permit|Warning|Caution|Danger)\b'
    ]
}

COMPILED_PATTERNS = {k: [re.compile(p, re.IGNORECASE) for p in v] for k, v in PATTERNS.items()}


# --- Classification Patterns ---

CLASSIFICATION_RULES = {
    "SOP": [r'\bstandard operating procedure\b', r'\bsop\b', r'\boperating procedure\b'],
    "Maintenance Manual": [r'\bmaintenance manual\b', r'\bmaintenance guide\b', r'\bservice manual\b'],
    "Inspection Report": [r'\binspection report\b', r'\binspection checklist\b'],
    "Incident Report": [r'\bincident report\b', r'\baccident report\b'],
    "Audit Report": [r'\baudit report\b', r'\baudit findings\b'],
    "Engineering Standard": [r'\bengineering standard\b', r'\bdesign standard\b'],
    "Training Material": [r'\btraining manual\b', r'\btraining material\b', r'\bcourse material\b']
}

COMPILED_CLASSIFICATIONS = {k: [re.compile(p, re.IGNORECASE) for p in v] for k, v in CLASSIFICATION_RULES.items()}
