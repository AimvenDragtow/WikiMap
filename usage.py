from wikimap import WikiMap, WikiLanguage, WikiGraphFormat, WikiSanityCheckMode
from datetime import datetime
import matplotlib.pyplot as plt
import networkx as nx
from igraph import Graph, plot

# Recombine all pages, current versions only
# frwiki-20241101-pages-meta-current.xml.bz2
# https://dumps.wikimedia.org/frwiki/20241101/frwiki-20241101-pages-meta-current.xml.bz2


# Nom du fichier                                        Contenu                                         Taille relative     Usage principal
# frwiki-20241101-pages-meta-current.xml.bz2            Pages actuelles + métadonnées                   Moyenne             Étude des articles et métadonnées actuels
# frwiki-20241101-pages-articles.xml.bz2                Texte brut des articles                         Faible              Travail sur le contenu brut des articles
# frwiki-20241101-pages-meta-history1.xml-p1p1209.7z    Historique complet pour une sélection de pages  Très élevée         Analyse des révisions et de l’évolution


# wm = WikiMap("wikimap_fr_20241101.gexf")
# wm = WikiMap("https://dumps.wikimedia.org/frwiki/20241101/frwiki-20241101-pages-meta-current.xml.bz2")
# wm = WikiMap("frwiki/20241101/frwiki-20241101-pages-meta-current.xml.bz2")
# wm = WikiMap("fr/20241101/pages-meta-current.xml.bz2")
# wm = WikiMap(date=datetime(2020, 5, 17), language="en", with_history=False)

wm = WikiMap(date="latest", language=WikiLanguage.EN, with_history=False)

wm.load()

wm.parse()

# graph = wm.get_graph()

# Pour NetworkX
# print(f"Le graphe contient {graph.number_of_nodes()} nœuds et {graph.number_of_edges()} arêtes.")
# # save a picture of the node with title = "512" with adjacent nodes
# node = [x for x,y in graph.nodes(data=True) if y['title']=="512"][0]
# adjacent_nodes = list(graph.successors(node)) + list(graph.predecessors(node))
# # Create a subgraph with the node and its adjacent nodes
# subgraph_nodes = [node] + adjacent_nodes
# subgraph = graph.subgraph(subgraph_nodes)
# # Draw the subgraph
# pos = nx.spring_layout(subgraph)
# labels = {n: d['title'] for n, d in subgraph.nodes(data=True)}
# nx.draw(subgraph, pos, labels=labels, with_labels=True, node_color='lightblue', edge_color='gray', node_size=500, font_size=10)
# # Save the picture
# plt.savefig("image.png")
# plt.show()

# wm.graph.save("gexf", "wikimap_fr_20241101.gexf")
# wm.save("512", "png", "wikimap_fr_20241101.png")

# total_pages, total_links, missing_pages = wm.stats()

# wm.save_graph(WikiGraphFormat.GRAPHML, "./tmp/fr_test_save")
# wm.save_graph(WikiGraphFormat.GRAPHML, "./tmp/fr_test_save", True)
# wm.save_graph(WikiGraphFormat.CSV, "./tmp/fr_test_save", compression=True)
# wm.save_graph(WikiGraphFormat.CSV, "./tmp/fr_test_save")

wm.display("United States", 1)

wm.sanity_check(WikiSanityCheckMode.NODES_SELECTION, 0.001)

# wm.display_html("Άρης (πλανήτης)", 2, "wikimap_el_latest.html")
# wm.display("Άρης (πλανήτης)", 2)

# check Αθλητισμός
# Ντέιβιντ Σάνσον
# ou
# ντέιβιντ σάνσον