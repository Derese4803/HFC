from dataclasses import dataclass
from datetime import datetime

@dataclass
class Correction:
    unique_id: str
    variable: str
    original_value: str
    corrected_value: str
    explanation: str
    corrected_by: str
    timestamp: str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
