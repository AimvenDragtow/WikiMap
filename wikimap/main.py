import json
from os import path, makedirs, remove
from datetime import datetime
import random
import tarfile
import time
from constants.sanity_check_mode import WikiSanityCheckMode
from igraph import Graph, plot
from matplotlib import pyplot as plt
import dash_cytoscape as cyto
from dash import html, Dash
import requests
import gzip

from sanity import WikiSanityChecker

from .constants.language import WikiLanguage
from .constants.graph_format import WikiGraphFormat
from .dump_downloader import DumpDownloader
from .parser import DumpParser


class WikiMap:

    def __init__(self, date: datetime | str = "latest", language: WikiLanguage = WikiLanguage.EN, with_history: bool = False, directory: str = None):
        if date == "latest":
            self.string_date = "latest"
        elif isinstance(date, datetime):
            self.string_date = date.strftime("%Y%m%d")
        else:
            raise Exception("Invalid date format")
        self.string_language = language.value

        self.date = date
        self.language = language
        self.with_history = with_history
        self.directory = directory if directory else f"data/{self.string_language}/{self.string_date}"
        self.dump_name = f"{self.string_language}wiki-{self.string_date}-pages-articles.xml"
        self.url = f"https://dumps.wikimedia.org/{self.string_language}wiki/{self.string_date}/{self.dump_name}.bz2"
        # Cap to 3 threads beacause of dumps.wikimedia.org rate limiting
        self.dd = DumpDownloader(self.url, num_threads=3)

    def load(self):
        # check if the dump exists online
        if not self.exists():
            raise Exception("Invalid dump parameters")

        # check if the dump is already downloaded
        if not self.is_downloaded():
            # create directory if it does not exist recursively
            makedirs(self.directory, exist_ok=True)
            # self.dd.singleThreadDownload(self.directory + "/" + self.dump_name)
            self.dd.download(self.directory + "/" + self.dump_name + ".bz2")

        # check if the dump is already extracted
        if not self.is_extracted():
            self.dd.extract(self.directory + "/" + self.dump_name + ".bz2")

        print("Dump loaded successfully")

    def parse(self):
        # process the dump xml file
        parser = DumpParser(path.join(self.directory, self.dump_name))

        # Get the original nodes and edges
        self.titles_original_case = parser.get_titles_original_case()  # {low_case_title: original_title}
        self.aliases_counts = parser.get_aliases_counts()  # {original_title: count}
        reverse_nodes = parser.get_reverse_nodes()  # {original_id: title}
        edges = parser.get_edges()  # [(source_id, target_id)]

        # Remap node IDs to a continuous range
        id_mapping = {original_id: new_id for new_id, original_id in enumerate(sorted(reverse_nodes.keys()))}

        # Remap edges
        remapped_edges = [(id_mapping[source], id_mapping[target]) for source, target in edges]

        # Add vertices (including isolated ones)
        titles = [reverse_nodes[original_id] for original_id in sorted(reverse_nodes.keys())]
        original_ids = sorted(reverse_nodes.keys())

        self.graph = Graph(directed=True)

        self.graph.add_vertices(len(original_ids))  # Add all nodes
        self.graph.vs["title"] = titles  # Add titles as a vertex attribute
        # Add original IDs as a vertex attribute
        self.graph.vs["original_id"] = original_ids

        # Add edges
        self.graph.add_edges(remapped_edges)

        print(f"Graph contains {self.graph.vcount()} nodes and {self.graph.ecount()} edges.")

    def get_graph(self):
        return self.graph

    def save_graph(self, format: WikiGraphFormat, output_path, compression=False):
        start_time = time.time()
        print(f"Saving graph to {output_path} in {format} format{' with compression' if compression else ''}...")
        # Switch case
        match format:
            case WikiGraphFormat.CSV:
                # 2 csv files: nodes.csv and edges.csv
                # edges.csv
                # self.graph.write_edgelist(output_path + ".edges.csv")
                with open(output_path + ".edges.csv", "w", encoding="utf-8") as f:
                    f.write("source\ttarget\n")
                    for e in self.graph.es:
                        f.write(f"{e.source}\t{e.target}\n")
                    f.close()
                # nodes.csv
                with open(output_path + ".nodes.csv", "w", encoding="utf-8") as f:
                    f.write("id\toriginal_id\ttitle\tnumber_of_out_edges\tnumber_of_in_edges\tnumber_of_edges\tnumber_of_aliases(redirect)\n")
                    for v in self.graph.vs:
                        f.write(f"{v.index}\t{v['original_id']}\t{v['title']}\t{str(v.outdegree())}\t{str(v.indegree())}\t{str(v.degree())}\t{str(self.aliases_counts.get(v['title'], 0))}\n")
                    f.close()
                if compression:
                    # compress the csv files in one gzip file and delete the original files
                    # with open(output_path + ".graph.gz", "wb") as f_out:
                    #     with gzip.open(output_path + ".edges.csv", "rb") as f_in:
                    #         f_out.writelines(f_in)
                    #     with gzip.open(output_path + ".nodes.csv", "rb") as f_in:
                    #         f_out.writelines(f_in)
                    with tarfile.open(output_path + ".graph.tgz", "w:gz") as tar:
                        tar.add(output_path + ".edges.csv")
                        tar.add(output_path + ".nodes.csv")
                    # delete the original files
                    remove(output_path + ".edges.csv")
                    remove(output_path + ".nodes.csv")
            # case WikiGraphFormat.GEXF:
            #     self.graph.write_gexf(output_path)
            case WikiGraphFormat.GRAPHML:
                if compression:
                    self.graph.write_graphmlz(output_path + ".graphml.gz")
                else:
                    self.graph.write_graphml(output_path + ".graphml")
            case WikiGraphFormat.PARQUET:
                self.graph.write_pajek(output_path + ".txt")
            case _:  # default case
                raise Exception("Invalid format")
        print(f"Graph saved successfully in {time.time() - start_time:.2f} seconds.")
              

    def save(self, node_title, format, output_path):
        if format == "png" or format == "png":
            subgraph = self.__get_subgraph(node_title, 1)
            layout = subgraph.layout("fr")
            visual_style = {}
            visual_style["vertex_label"] = subgraph.vs["title"]
            visual_style["vertex_color"] = "lightblue"
            visual_style["edge_color"] = "gray"
            visual_style["vertex_size"] = 20
            visual_style["layout"] = layout
            visual_style["bbox"] = (300, 300)
            visual_style["margin"] = 20

            fig, ax = plt.subplots()
            plot(subgraph, ax, **visual_style)
            plt.savefig(output_path)
        else:
            raise Exception("Invalid format")

    def display(self, node_title: str, depth: int):
        node_title = node_title.lower()
        subgraph = self.__get_subgraph(node_title, depth)

        # Draw the subgraph
        layout = subgraph.layout("fr")
        visual_style = {}
        visual_style["vertex_label"] = subgraph.vs["title"]
        visual_style["vertex_color"] = ["red" if v["title"].lower() == node_title else "lightblue" for v in subgraph.vs]
        visual_style["edge_color"] = "gray"
        visual_style["vertex_size"] = 20
        visual_style["layout"] = layout
        visual_style["bbox"] = (300, 300)
        visual_style["margin"] = 20

        fig, ax = plt.subplots()
        plot(subgraph, ax, **visual_style)
        plt.show()

    def display_html(self, node_title: str, depth: int, output_path: str):
        node_title = node_title.lower()
        subgraph = self.__get_subgraph(node_title, depth)

        nodes = [
            {"data": {"id": str(v.index), "label": v["title"]}, "classes": "ego" if v["title"].lower() == node_title else ""}
            for v in subgraph.vs
        ]
        edges = [
            {"data": {"source": str(e.source), "target": str(e.target)}}
            for e in subgraph.es
        ]
        elements = nodes + edges

        # Define the layout and stylesheet for Cytoscape
        stylesheet = [
            {
                'selector': 'node',
                'style': {
                    'label': 'data(label)',
                    'background-color': 'lightblue',
                    'color': 'black',
                    'text-valign': 'center',
                    'text-halign': 'center',
                    'font-size': '12px'
                }
            },
            {
                'selector': 'node.ego',
                'style': {
                    'background-color': 'red'
                }
            },
            {
                'selector': 'edge',
                'style': {
                    'line-color': 'gray',
                    'width': 2
                }
            }
        ]

        layout = {
            'name': 'breadthfirst',
            'directed': True,
            'padding': 10
        }

        # HTML structure for the Cytoscape component
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Graph Visualization</title>
            <script src="https://cdn.jsdelivr.net/npm/cytoscape@3.22.0/dist/cytoscape.min.js"></script>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 0;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    background-color: #f0f0f0;
                }}
                #cy {{
                    width: 80%;
                    height: 80%;
                    border: 1px solid #ccc;
                    border-radius: 8px;
                    background-color: white;
                }}
            </style>
        </head>
        <body>
            <div id="cy"></div>

            <script>
                var cy = cytoscape({{
                    container: document.getElementById('cy'),
                    elements: {json.dumps(elements)},
                    layout: {json.dumps(layout)},
                    style: {json.dumps(stylesheet)},
                }});
            </script>
        </body>
        </html>
        """

        # Save the HTML content to the specified output path
        with open(output_path, 'w') as f:
            f.write(html_content)

    def sanity_check(self, mode: WikiSanityCheckMode = WikiSanityCheckMode.NODES_SELECTION, n: float = 0.5):
        if n <= 0 or n > 1:
            raise ValueError("n should be between 0 and 1")
        # Check if the graph is directed
        if not self.graph.is_directed():
            raise Exception("The graph is not directed.")
        sc = WikiSanityChecker(self.graph, self.string_language, mode, n, self.titles_original_case)
        sc.check()
        sc.save_analysis("sanity_check")

    def exists(self):
        # check if the dump exists online
        # https://dumps.wikimedia.org/elwiki/latest/elwiki-latest-pages-articles.xml.bz2
        # doing head request on the URL "https://dumps.wikimedia.org/"" + language + "wiki/"" + date + "/" + language + "wiki-" + date + "-pages-articles.xml.bz2"
        response = requests.head(self.url)
        # if the status code is 200, then the dump exists
        return response.status_code == 200

    def is_downloaded(self):
        # check if the dump is already downloaded
        # check if the file exists in the directory
        file_path = path.join(self.directory, self.dump_name + ".bz2")
        return path.exists(file_path) and path.getsize(file_path) > 0

    def is_extracted(self):
        # check if the dump is already extracted
        # check if the file exists in the directory
        file_path = path.join(self.directory, self.dump_name)
        return path.exists(file_path) and path.getsize(file_path) > 0

    def __get_subgraph(self, node_title: str, depth: int = 1, mode: str = "all") -> Graph:
        node_title = node_title.lower()
        node = self.graph.vs.find(title=node_title)
        if node is None:
            print(f"Node with title {node_title} not found.")
            return None

        # Use a set to keep track of visited nodes
        visited = set()
        current_level = {node.index}

        for _ in range(depth + 1):
            next_level = set()
            for node_index in current_level:
                neighbors = self.graph.neighbors(node_index, mode=mode)
                for neighbor in neighbors:
                    if neighbor not in visited:
                        next_level.add(neighbor)
            visited.update(current_level)
            current_level = next_level

        # Create a subgraph containing all the nodes visited (including neighbors up to the specified depth)
        subgraph_nodes = list(visited)
        print(f"Number of nodes in the subgraph: {len(subgraph_nodes)} (Depth: {depth})")

        # Return the subgraph
        return self.graph.subgraph(subgraph_nodes)