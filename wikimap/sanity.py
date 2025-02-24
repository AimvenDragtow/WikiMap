import time
from constants.sanity_check_mode import WikiSanityCheckMode
from matplotlib import pyplot as plt
import numpy as np
import requests
from igraph import Graph

class WikiSanityChecker:
    def __init__(self, graph: Graph, string_language, mode: WikiSanityCheckMode, n: float, titles_original_case: dict):
        if n <= 0 or n > 1:
            raise ValueError("n should be between 0 and 1")
        self.graph = graph
        self.string_language = string_language
        self.mode = mode
        self.n = n
        self.titles_original_case = titles_original_case
        self.selectedNodes = set()

    def check(self):
        self.__selectNodes()
        start_time = time.time()
        self.graphMap = self.__getGraphNodesLinksCount()
        print(f"Graph map done in {time.time() - start_time} seconds")
        start_time = time.time()
        self.apiMap = self.__getAPINodesLinksCount()
        print(f"API map done in {time.time() - start_time} seconds")
        if len(self.graphMap) != len(self.apiMap):
            raise Exception("Graph and API nodes count mismatch")

    def save_analysis(self, path):
        if len(self.selectedNodes) != len(self.graphMap) or len(self.selectedNodes) != len(self.apiMap):
            raise Exception("Analysis not done yet")
        with open(path + ".csv", "w") as f:
            f.write("Node\tGraph\tAPI\n")
            for node in self.selectedNodes:
                f.write(f"{node.index}\t{self.graphMap[node]}\t{self.apiMap[node]}\n")
        
        # create and save a plot comparing the two maps with two curves (x = node, y = links count)
        listGraphMap = list(self.graphMap.values())
        listApiMap = list(self.apiMap.values())
        # sort the two lists by ascending order of graphMap
        listGraphMap, listApiMap = zip(*sorted(zip(listGraphMap, listApiMap)))
        plt.figure(figsize=(10, 6))
        plt.plot(listApiMap, label="According to API", linestyle="-", color="r")
        plt.plot(listGraphMap, label="According to WikiMap Graph", linestyle="--", color="b")
        plt.xlabel("Articles")
        plt.ylabel("Links count")
        plt.title("Data sanity check: Comparison of links count between WikiMap graph and Wikipedia API (outgoing degree)")
        plt.legend()
        plt.grid()
        plt.tight_layout()
        plt.savefig(path + ".png")
        plt.close()

    def __selectNodes(self):
        if (self.mode.value == WikiSanityCheckMode.NODES_SELECTION.value or self.mode.value == WikiSanityCheckMode.NODES_EDGES_SELECTION.value):
            # select randomly n% of the nodes with out degree as weight of randomness
            probabilities = [self.graph.degree(node, mode="out") for node in range(self.graph.vcount())]
            total = sum(probabilities)
            probabilities = [p / total for p in probabilities]  # normalize probabilities
            size = int(self.n * self.graph.vcount())
            nodes = np.random.choice(self.graph.vs, size=size, p=probabilities)
            # add to selected nodes to the set
            print(len(nodes))
            self.selectedNodes.update(nodes)
        if (self.mode.value == WikiSanityCheckMode.EDGES_SELECTION.value or self.mode.value == WikiSanityCheckMode.NODES_EDGES_SELECTION.value):
            # select randomly n% of the edges and get the nodes in source and target
            size = int(self.n * self.graph.ecount())
            edges = np.random.choice(self.graph.es, size=size)
            print(len(edges))
            for edge in edges:
                self.selectedNodes.add(edge.source)
                self.selectedNodes.add(edge.target)
        print(f"{len(self.selectedNodes)} nodes selected representing {self.n * 100}% of the graph")
        return self.selectedNodes

    def __getGraphNodesLinksCount(self) -> dict:
        m = {} # node -> links count
        for node in self.selectedNodes:
            m[node] = len(self.graph.neighbors(node, mode="out"))
        return m

    def __getAPINodesLinksCount(self) -> dict:
        m = {} # node -> links count 
        for node in self.selectedNodes:
            links = self.__getNodeLinksFromAPI(node)
            m[node] = len(links)
        return m

    def __getNodeLinksFromAPI(self, node) -> list[str]:
        # check links with wikipedia api continue_params = {}
        start_time = time.time()
        nb_requests = 0
        continue_params = {}  # Initialize continue_params
        all_links = []
        while True:
            nb_requests += 1
            response = requests.get(
                f"https://{self.string_language}.wikipedia.org/w/api.php",
                params={
                    "action": "query",
                    "format": "json",
                    "plnamespace": 0,
                    "titles": self.titles_original_case[node["title"]],
                    "prop": "links",
                    "pllimit": 500,
                    **continue_params
                }
            )
            if response.status_code != 200:
                raise Exception("Failed to get links from Wikipedia API")

            data = response.json()
            pages = data.get("query", {}).get("pages", {})
            for page_id, page_data in pages.items():
                links = page_data.get("links", [])
                all_links.extend(link["title"].lower() for link in links)

            if "continue" not in data:
                break
            continue_params = data["continue"]

        # print(f"API request done in {time.time() - start_time} seconds with {nb_requests} requests")
        return all_links
