from dataclasses import dataclass

@dataclass
class Correction:
    error_type: str
    unique_id: str
    variable: str
    correct_value: int
    explanation: str
    corrected_by: str
    timestamp: str
