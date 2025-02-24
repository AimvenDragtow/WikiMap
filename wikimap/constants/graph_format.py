# graph formats enum
from enum import Enum

class WikiGraphFormat(Enum):
    CSV = 'csv'
    # GEXF = 'gexf'
    GRAPHML = 'graphml'
    PARQUET = 'parquet'