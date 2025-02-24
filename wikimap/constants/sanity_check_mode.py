# sanity check modes enum
from enum import Enum

class WikiSanityCheckMode(Enum):
    NODES_SELECTION = 'nodes'
    EDGES_SELECTION = 'edges'
    NODES_EDGES_SELECTION = 'nodes_edges'