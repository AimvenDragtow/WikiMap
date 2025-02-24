# WikiMap

WikiMap est un package Python conçu pour extraire et analyser les données de Wikipedia, en construisant un graphe orienté où les sommets représentent les articles et les arêtes représentent les liens entre ces articles.

## Fonctionnalités

- **Téléchargement des dumps Wikimedia** : Récupération des données depuis [dumps.wikimedia.org](https://dumps.wikimedia.org/).
- **Traitement des données** : Extraction des articles et de leurs liens.
- **Construction de graphes** : Création d'un graphe orienté avec des outils performants comme `igraph`.
- **Persistance des graphes** : Sauvegarde et chargement des graphes dans différents formats.
- **Analyse et statistiques** : Calcul de métriques comme le PageRank, centralité, etc.
- **Visualisation des graphes** : Génération de visualisations interactives ou statiques.

## Installation

Vous pouvez installer **WikiMap** via `pip` une fois le package publié sur PyPI :

```bash
pip install wikimap
