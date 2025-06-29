import networkx as nx
import os
import json
import random

BASE_DIR = "datasets"
NUM_INSTANCES_PER_SET = 15 
NUM_INSTANCES_PER_SET_N100 = 15


GRAPH_SPECS = {
    "n10": {
        "nodes": 10,
        "p_values": [0.2, 0.4, 0.6, 0.8], 
        "instances": NUM_INSTANCES_PER_SET
    },
    "n100": {
        "nodes": 100,
        "p_values": [0.05, 0.1, 0.2, 0.4],
        "instances": NUM_INSTANCES_PER_SET_N100
    }
}

def generate_connected_erdos_renyi_dataset(base_dir, graph_specs):
    overall_summary = [] # To collect metadata for overall_summary.json
    
    for size_cat, specs in graph_specs.items():
        n = specs["nodes"]
        p_values = specs["p_values"]
        num_instances = specs["instances"]
        
        size_dir = os.path.join(base_dir, size_cat)
        erdos_renyi_dir = os.path.join(size_dir, "erdos_renyi") 
        
        os.makedirs(erdos_renyi_dir, exist_ok=True)
        
        dataset_info = [] # Metadata for dataset_info.json
        
        print(f"\nGenerating Erdős-Rényi graphs for n={n}...")

        instance_count = 0
        graph_id_counter = 0 # Unique ID for each generated graph instance

        for p_val in p_values:
            print(f"  Generating for p={p_val} ({num_instances} instances)...")
            for i in range(num_instances):
                graph_id = f"er_{n}_{str(p_val).replace('.', '')}_{i}" # Unique ID based on params
                
                # Generate until connected
                G = None
                is_connected = False
                attempts = 0
                max_attempts = 100 # Avoid infinite loops for very low p
                
                while not is_connected and attempts < max_attempts:
                    G_candidate = nx.erdos_renyi_graph(n, p_val, seed=random.randint(0, 1000000))
                    is_connected = nx.is_connected(G_candidate)
                    if is_connected:
                        G = G_candidate
                    attempts += 1
                
                if not is_connected:
                    print(f"Warning: Could not generate connected G({n},{p_val}) after {max_attempts} attempts. Skipping instance.")
                    continue

                if G is not None:
                    G = nx.relabel_nodes(G, {node: int(node) for node in G.nodes()})
                else:
                    continue

                num_nodes = G.number_of_nodes()
                num_edges = G.number_of_edges()
                diameter = nx.diameter(G)
                avg_degree = sum(dict(G.degree()).values()) / num_nodes
                max_degree = max(dict(G.degree()).values())

                # Diameter calculation (O(N*M) or higher, very slow for large N)
                if num_nodes <= 100: # Threshold can be adjusted based on available computation power
                    try:
                        current_diameter = nx.diameter(G)
                    except nx.NetworkXError: # Graph might be technically connected but paths not found or other issues
                        current_diameter = None
                else:
                    print(f"    Skipping diameter calculation for n={num_nodes} (potentially very slow).")

                # Girth calculation (also O(N*M) for sparse, can be higher for dense)
                if num_nodes <= 50: # Threshold can be adjusted
                    try:
                        current_girth = nx.girth(G)
                    except nx.NetworkXError: # Graph is acyclic (a tree) or issues finding cycles
                        current_girth = None
                else:
                    print(f"    Skipping girth calculation for n={num_nodes} (potentially very slow).")
                
                # --- General Upper and Lower Bounds for mu(G) ---
                # Based on Di Stefano et al. (2021), Lemma 2.4, Lemma 2.6, Remark 2.7
                
                # General Lower Bound: mu(G) >= Delta(G)
                general_lb_max_degree = max_degree
                
                # General Upper Bound: mu(G) <= n - d + 1
                general_ub_diameter_based = None
                if current_diameter is not None:
                    general_ub_diameter_based = num_nodes - current_diameter + 1
                    
                # General Upper Bound: mu(G) <= n - c + 3
                general_ub_girth_based = None
                if current_girth is not None:
                    general_ub_girth_based = num_nodes - current_girth + 3

                gml_filename = f"{graph_id}.gml"
                gml_path = os.path.join(erdos_renyi_dir, gml_filename)
                nx.write_gml(G, gml_path)

                metadata = {
                    "filename": gml_filename,
                    "graph_id": graph_id, 
                    "nodes": num_nodes,
                    "edges": num_edges,
                    "p_value": p_val,
                    "diameter": diameter,
                    "avg_degree": avg_degree,
                    "max_degree": max_degree,
                    "general_lb_max_degree": general_lb_max_degree,
                    "general_ub_diameter_based": general_ub_diameter_based,
                    "general_ub_girth_based": general_ub_girth_based,
                    "graph_type": "erdos_renyi",
                    "size_category": size_cat,
                    "instance": i,
                    "seed": G.graph.get('seed', None) 
                }
                dataset_info.append(metadata)
                overall_summary.append(metadata)
                graph_id_counter += 1
                instance_count += 1
        
        dataset_info_path = os.path.join(erdos_renyi_dir, "dataset_info.json")
        with open(dataset_info_path, 'w') as f:
            json.dump(dataset_info, f, indent=4)
        print(f"  Generated {instance_count} connected Erdős-Rényi graphs for n={n}.")

    overall_summary_path = os.path.join(base_dir, "summary.json")
    with open(overall_summary_path, 'w') as f:
        json.dump(overall_summary, f, indent=4)
    print(f"\nAll Erdős-Rényi graph generation complete. Total: {graph_id_counter} graphs.")


# --- Execute Generation ---
if __name__ == "__main__":
    # Ensure the base 'datasets' directory exists
    os.makedirs(BASE_DIR, exist_ok=True)
    
    # Run the generation
    generate_connected_erdos_renyi_dataset(BASE_DIR, GRAPH_SPECS)
    
    print("\nGeneration script finished. You can now run your experiment_runner.py.")