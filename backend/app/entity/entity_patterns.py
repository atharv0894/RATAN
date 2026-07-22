import re

# --- Entity Patterns ---

PATTERNS = {
    "Equipment": [
        r'\b(?:Pump|Valve|Motor|Tank|Compressor|Heat Exchanger|Turbine|Generator|Boiler|Reactor)\s+[A-Z0-9-]+\b',
        r'\b[PVMTCHGBR]-\d{2,4}[A-Z]?\b' # Matches P-101, V-204, etc.
    ],
    "Role": [
        r'\b(?:Operator|Supervisor|Engineer|Officer|Inspector|Technician|Manager|Auditor|Reviewer|Director|Coordinator|Specialist|Staff|Administrator)\b'
    ],
    "Standard": [
        r'\b(?:ISO|API|ASME|OISD|OSHA|IEC|IEEE)(?:\s+\d{3,5}(?:-\d{4})?)?\b',
        r'\b(?:Policy|Guideline|Framework|Protocol|Regulation|Statute|Compliance)\b'
    ],
    "Parameter": [
        r'\b(?:Pressure|Temperature|Flow Rate|Voltage|Current|RPM|Torque|Speed|Humidity|Latency|Throughput|Capacity|Performance|Metric|Benchmark)\b'
    ],
    "Safety": [
        r'\b(?:PPE|Hazard|Lockout|Tagout|LOTO|Emergency|Permit|Warning|Caution|Danger|Risk|Mitigation|Incident|Accident|Evacuation)\b'
    ],
    "Organization": [
        r'\b(?:Department|Agency|Office|Committee|Board|Commission|Task Force|Unit|Division|Branch|Ministry)\b'
    ],
    "Concept": [
        r'\b(?:Audit|Review|Analysis|Evaluation|Assessment|Strategy|Architecture|System|Network|Infrastructure|Platform|Process|Workflow|Lifecycle)\b'
    ],
    "Tool": [
        r'\b(?:Software|Hardware|Application|Database|Server|Scanner|Computer|Program|Algorithm|Interface|Dashboard|Portal)\b'
    ],
    "Document": [
        r'\b(?:Report|Form|Manual|Handbook|Guide|Checklist|Log|Record|Ledger|Invoice|Bill|Receipt|Certificate|License)\b'
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
