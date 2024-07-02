from enum import Enum

class RawRoadAccidentCsvFileNames(str, Enum):
    caracteristiques = 'caracteristiques'
    lieux = 'lieux'
    usagers = 'usagers'
    vehicules = 'vehicules'
    

class ProcessingStatus(str, Enum):
    processing = 'PROCESSING'
    processed = 'PROCESSED'
    failed = 'FAILED'