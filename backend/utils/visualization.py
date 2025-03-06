# backend/utils/visualization.py
import logging
import networkx as nx
import matplotlib.pyplot as plt
from typing import Any

logger = logging.getLogger(__name__)

def visualize_workflow(graph: Any, output_path: str = "workflow_graph.png"):
    """Generate workflow visualization with English labels"""
    try:
        plt.clf()  # Clear previous figure
        G = nx.DiGraph()
        
        # English node labels
        nodes = {
            "intent_detection_node": "Intent Detection",
            "info_collection_node": "Info Collection",
            "url_generation_node": "URL Generation",
            "general_response_node": "General Response",
            "END": "END"
        }
        
        # Edges remain the same
        edges = [
            ("info_collection_node", "intent_detection_node"),
            ("general_response_node", "intent_detection_node"),
            ("url_generation_node", "END"),
            ("intent_detection_node", "info_collection_node"),
            ("intent_detection_node", "url_generation_node"),
            ("intent_detection_node", "general_response_node")
        ]
        
        # Add nodes and edges
        G.add_nodes_from(nodes.keys())
        nx.set_node_attributes(G, {k: {"label": v} for k, v in nodes.items()})
        G.add_edges_from(edges)
        
        # Visualization settings optimized for English
        plt.figure(figsize=(18, 12))  # Wider canvas
        
        # Use spring layout with tuned parameters
        pos = nx.spring_layout(G, k=0.6, iterations=100, seed=42)
        
        nx.draw(
            G,
            pos,
            with_labels=True,
            labels={n: G.nodes[n]["label"] for n in G.nodes},
            node_size=8000,      # Larger nodes
            node_color="lightblue",
            font_size=10,        # Slightly smaller font for English
            font_weight="bold",
            edge_color="gray",
            arrowsize=25,
            width=2,
            connectionstyle="arc3,rad=0.2"
        )
        
        # Add title
        plt.title("Flight AI Workflow Diagram", fontsize=18, pad=20)
        
        # Save high-quality image
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        logger.info(f"Workflow diagram saved to {output_path}")
        
    except Exception as e:
        logger.error(f"Visualization failed: {str(e)}")
        raise