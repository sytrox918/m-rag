import networkx as nx
from storage.postgres import get_db, ContentUnitModel
from typing import List, Dict

class GraphService:
    def __init__(self):
        pass

    def build_graph(self) -> nx.DiGraph:
        """
        Builds a directed Knowledge Graph from the Postgres database.
        Edges flow from Prerequisite -> Topic
        """
        db = next(get_db())
        G = nx.DiGraph()
        try:
            units = db.query(ContentUnitModel).all()
            
            for unit in units:
                if not unit.topics:
                    continue
                    
                # Add nodes for all topics in this unit
                for topic in unit.topics:
                    topic = topic.strip().lower()
                    if not G.has_node(topic):
                        G.add_node(topic, type="topic", sources=[])
                    G.nodes[topic]['sources'].append({
                        "unit_id": unit.id,
                        "source_type": unit.source_type,
                        "document_name": unit.document_name
                    })
                
                # If there are prerequisites, link them to the topics
                if unit.prerequisites:
                    for prereq in unit.prerequisites:
                        prereq = prereq.strip().lower()
                        if not G.has_node(prereq):
                            G.add_node(prereq, type="prerequisite", sources=[])
                            
                        # Add edges from Prerequisite -> Topic
                        for topic in unit.topics:
                            topic = topic.strip().lower()
                            G.add_edge(prereq, topic, weight=1)
            return G
        finally:
            db.close()

    def get_learning_path(self, target_concept: str) -> Dict:
        """
        Calculates the topological order of prerequisites needed to understand the target concept.
        """
        G = self.build_graph()
        target = target_concept.strip().lower()
        
        # If the exact concept doesn't exist, try to find a partial match
        if target not in G:
            matches = [node for node in G.nodes() if target in node]
            if matches:
                target = matches[0] # Take best match
            else:
                return {"error": f"Concept '{target_concept}' not found in the knowledge graph."}
        
        # Get all ancestors (prerequisites) of the target concept
        try:
            ancestors = nx.ancestors(G, target)
            # Create a subgraph of just the target and its ancestors
            subgraph = G.subgraph(list(ancestors) + [target])
            
            # Sort them topologically so you learn the base prerequisites first!
            learning_order = list(nx.topological_sort(subgraph))
            
            path_details = []
            for node in learning_order:
                sources = G.nodes[node].get('sources', [])
                path_details.append({
                    "concept": node,
                    "recommended_sources": sources[:2] # Top 2 sources to learn this concept
                })
                
            return {
                "target_concept": target,
                "path": path_details
            }
        except nx.NetworkXUnfeasible:
            # Graph has a cycle (circular dependency)
            return {"error": "Circular dependency detected in prerequisites."}

    def generate_visual_graph(self, target_concept: str = None) -> str:
        """
        Generates a pyvis HTML string for the graph.
        """
        from pyvis.network import Network
        G = self.build_graph()
        
        if target_concept:
            target = target_concept.strip().lower()
            matches = [node for node in G.nodes() if target in node]
            if matches:
                target = matches[0]
                ancestors = nx.ancestors(G, target)
                G = G.subgraph(list(ancestors) + [target])
        
        # Build pyvis network
        net = Network(height="500px", width="100%", bgcolor="#222222", font_color="white", directed=True)
        
        # Color nodes based on type
        for node_id, data in G.nodes(data=True):
            color = "#00d2ff" if data.get('type') == 'topic' else "#ff0055"
            net.add_node(node_id, label=node_id.title(), color=color, shape="dot", size=20)
            
        for source, target in G.edges():
            net.add_edge(source, target, color="#666666")
            
        net.repulsion(node_distance=150, spring_length=100)
        
        import tempfile
        import os
        with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp:
            net.save_graph(tmp.name)
            with open(tmp.name, 'r', encoding='utf-8') as f:
                html_data = f.read()
        try:
            os.unlink(tmp.name)
        except:
            pass
            
        return html_data

graph_service = GraphService()
