import networkx as nx
import os
import json
import random

# --- Configuration ---
BASE_DIR = "datasets"
NUM_INSTANCES_PER_SET = 15 # As per your n10 dataset structure
NUM_INSTANCES_PER_SET_N100 = 20 # As per your n100 dataset structure

COMPLETE_GRAPH_SPECS = {
    "n10": {
        "nodes": 10,
        "instances": NUM_INSTANCES_PER_SET
    },
    "n100": {
        "nodes": 100,
        "instances": NUM_INSTANCES_PER_SET_N100
    }
}

# --- Generation Function ---
def generate_complete_graph_dataset(base_dir, graph_specs):
    overall_summary = [] # To collect metadata for overall_complete_summary.json
    
    for size_cat, specs in graph_specs.items():
        n = specs["nodes"]
        num_instances = specs["instances"]
        
        # Define directory paths
        size_dir = os.path.join(base_dir, size_cat)
        complete_dir = os.path.join(size_dir, "complete") # New directory for Complete graphs
        
        os.makedirs(complete_dir, exist_ok=True) # Create directory if it doesn't exist
        
        dataset_info = [] # Metadata for dataset_info.json within this size category
        
        print(f"\nGenerating Complete graphs for n={n}...")

        instance_counter = 0 # Counts successfully generated instances in this category
        
        for i in range(num_instances):
            graph_id = f"complete_{n}_{i}" # Unique ID based on params
            
            G = nx.complete_graph(n) # Generates K_n
            
            # Ensure node labels are integers for consistency with your existing code
            G = nx.relabel_nodes(G, {node: int(node) for node in G.nodes()})

            # --- Calculate Graph Properties and Exact mu(G) ---
            num_nodes = G.number_of_nodes()
            num_edges = G.number_of_edges()
            
            # Exact mu(G) for Complete Graphs: |V| [source: 887, Table 1]
            mutual_visibility_number = num_nodes 
            
            # Other properties (can be computationally intensive for larger graphs, but K_n is simple)
            diameter = 1 if num_nodes > 1 else 0 # Diameter of K_n is 1 (or 0 for K_1)
            avg_degree = (num_nodes - 1) # All nodes have degree n-1
            max_degree = (num_nodes - 1)
            
            # Girth is 3 for n >= 3, None for n < 3
            girth = 3 if num_nodes >= 3 else None 

            # Save graph to GML file
            gml_filename = f"{graph_id}.gml"
            gml_path = os.path.join(complete_dir, gml_filename)
            nx.write_gml(G, gml_path)

            # Collect all metadata for this instance
            metadata = {
                "filename": gml_filename,
                "graph_id": graph_id,
                "nodes": num_nodes,
                "edges": num_edges,
                "mutual_visibility_number": mutual_visibility_number,
                "diameter": diameter,
                "girth": girth,
                "avg_degree": avg_degree,
                "max_degree": max_degree,
                "graph_type": "complete",
                "size_category": size_cat,
                "instance": i,
                "seed": None # Complete graphs are deterministic, no random seed
            }
            dataset_info.append(metadata)
            overall_summary.append(metadata) # Add to overall summary list
            instance_counter += 1
        
        # Save dataset_info.json for this size category's Complete graphs
        dataset_info_path = os.path.join(complete_dir, "dataset_info.json")
        with open(dataset_info_path, 'w') as f:
            json.dump(dataset_info, f, indent=4)
        print(f"  Generated {instance_counter} Complete graphs for n={n}.")

    # Save a final overall summary JSON for all Complete graphs generated
    overall_summary_path = os.path.join(base_dir, "overall_complete_summary.json")
    with open(overall_summary_path, 'w') as f:
        json.dump(overall_summary, f, indent=4)
    print(f"\nAll Complete graph generation complete. Total unique graphs generated: {len(overall_summary)}.")


# --- Execution ---
if __name__ == "__main__":
    # Ensure the base 'datasets' directory exists before starting generation
    os.makedirs(BASE_DIR, exist_ok=True)
    
    # Run the generation
    generate_complete_graph_dataset(BASE_DIR, COMPLETE_GRAPH_SPECS)
    
    print("\nGeneration script finished. Remember to run your experiment_runner.py on the updated datasets.")