import mmap
from os import stat
import time
import re
from lxml import etree
from tqdm import tqdm


class DumpParser:
    def __init__(self, file_path):
        self.file_path = file_path
        self.file_size = stat(file_path).st_size
        self.total_lines = self.__count_lines()

        self.pages_count = 0
        self.redirect_pages_count = 0

        self.link_pattern = r'\[\[([^\n\|\]\[\<\>\{\}]{1,256})(?:\|[^\[\]]*)?\]\]'  # Regex for internal links

        self.raw_temp_data = {}  # Temporary storage for all pages

        self.titles_original_case = {}  # Dictionary lowercase title -> original title
        self.aliases = {}  # Dictionary alias -> original title
        self.aliases_counts = {}  # Dictionary Original title -> count of aliases
        self.nodes = {}  # Dictionary node -> ID
        self.reverse_nodes = {}  # ID -> node (for reverse lookup)
        self.edges = []  # List of (source_id, target_id) for edges

        self.__run()

    def get_file_size(self):
        return self.file_size

    def get_total_lines(self):
        return self.total_lines

    def get_pages_count(self):
        return self.pages_count

    def get_redirect_pages_count(self):
        return self.redirect_pages_count

    def get_articles_count(self):
        # Articles = Pages - Redirects (ns = 0)
        return self.pages_count - self.redirect_pages_count

    def get_titles_original_case(self):
        return self.titles_original_case

    def get_aliases_counts(self):
        return self.aliases_counts

    def get_nodes(self):
        return self.nodes

    def get_reverse_nodes(self):
        return self.reverse_nodes

    def get_edges(self):
        return self.edges

    def __run(self):
        print(f"Starting to parse {self.file_path}")
        start_time = time.time()

        self.__parse_xml()
        self.__build_data()

        # Free memory
        self.raw_temp_data.clear()

        print(f"Finished parsing in {time.time() - start_time:.2f} seconds")
        print(f"Total pages: {self.pages_count} including {self.redirect_pages_count} redirects")
        print(f"Total articles: {self.get_articles_count()}")

    def __count_lines(self, chunk_size=64 * 1024 * 1024):  # 64 MB
        with open(self.file_path, 'rb') as f:
            mmapped_file = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
            total_lines = 0
            while chunk := mmapped_file.read(chunk_size):
                total_lines += chunk.count(b'\n')
            mmapped_file.close()
        return total_lines

    def __parse_xml(self):
        context = etree.iterparse(self.file_path, events=("start", "end"))
        for event, elem in tqdm(context, total=self.total_lines, unit=" lines"):
            if event == "start" and elem.tag.split('}')[-1] == "page":
                self._process_page(elem)
            # Free memory
            elem.clear()

    def _process_page(self, elem):
        id = None
        ns = None
        title = None
        text = None
        redirect = None

        # Explore the children of the page element
        for child in elem:
            tag = child.tag.split('}')[-1]
            if tag == "ns":
                ns = child.text
                # Namespace = 0 (article)
                if ns != "0":
                    return
            elif tag == "id":
                id = child.text
            elif tag == "title":
                title = child.text
            elif tag == "redirect":
                redirect = child.attrib.get("title")
            elif tag == "revision":
                for rev_child in child:
                    rev_tag = rev_child.tag.split('}')[-1]
                    if rev_tag == "text":
                        text = rev_child.text

        if ns != "0" or not id or not title:
            return

        # convert id string to int
        id = int(id)

        self.pages_count += 1

        if redirect:
            title = title.lower()
            redirect = redirect.lower()
            self.redirect_pages_count += 1
            self.aliases[title] = redirect
            self.aliases_counts[redirect] = self.aliases_counts.get(redirect, 0) + 1
        else:
            self.titles_original_case[title.lower()] = title
            title = title.lower()
            # Extract internal links
            # Find all links to other articles
            links = re.findall(self.link_pattern, text) if text else []
            links = [link.lower() for link in links]
            self.raw_temp_data[title] = (id, links)

    def __build_data(self):
        # Add nodes and edges
        for title, (id, links) in self.raw_temp_data.items():
            if title not in self.nodes:
                self.nodes[title] = id
                self.reverse_nodes[id] = title

            source_id = id

            for link in links:
                # Resolve redirects
                resolved_link = self.aliases.get(link, link)
                if resolved_link not in self.nodes:
                    if not self.raw_temp_data.get(resolved_link):
                        # print(f"Link {resolved_link} not found - article probably does not exist yet/anymore")
                        continue
                    target_id = self.raw_temp_data.get(resolved_link)[0]
                    self.nodes[resolved_link] = target_id
                    self.reverse_nodes[target_id] = resolved_link
                else:
                    target_id = self.nodes[resolved_link]

                # # print if source_id or target_id is not a number
                # if not source_id.isnumeric() or not target_id.isnumeric():
                #     print(f"source_id: {source_id}, target_id: {target_id}")
                #     continue
                
                if source_id != target_id:  # Avoid self-loops
                    self.edges.append((source_id, target_id))
