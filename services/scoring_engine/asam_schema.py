from enum import Enum, IntEnum

class Dimension(str, Enum):
    D1 = "D1_INTOXICATION"
    D2 = "D2_BIOMEDICAL"
    D3 = "D3_EMOTIONAL"
    D4 = "D4_READINESS"
    D5 = "D5_RELAPSE"
    D6 = "D6_ENVIRONMENT"

class Severity(IntEnum):
    NONE = 0
    MILD = 1
    MODERATE = 2
    SIGNIFICANT = 3
    SEVERE = 4
