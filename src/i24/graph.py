"""Evidence-only relationship graph; no beneficial ownership inference."""
import networkx as nx
from .audit import read

def build_graph(path,known_ids):
    g=nx.DiGraph();g.add_nodes_from(known_ids);invalid=[]
    for r in read(path):
        if r['from_entity_id'] not in known_ids or r['to_entity_id'] not in known_ids:
            invalid.append(r['relation_id']);continue
        g.add_edge(r['from_entity_id'],r['to_entity_id'],relationship=r['relation_type'],evidence=r['evidence_id'],source=r['source'])
    return g,invalid

def evidence_neighborhood(graph,node):
    if node not in graph:return []
    return sorted([{'related_id':n,'relation_type':graph.edges[node,n]['relationship'],'evidence':graph.edges[node,n]['evidence']} for n in graph.successors(node)],key=lambda d:d['related_id'])
