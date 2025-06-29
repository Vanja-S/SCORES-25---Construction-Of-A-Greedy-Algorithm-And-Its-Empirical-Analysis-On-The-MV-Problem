import networkx as nx
import os
import json
import random # For seed, though K_n is deterministic
import math

# --- Configuration ---
BASE_DIR = "datasets"
NUM_INSTANCES_PER_SET = 15 # For n10 graphs
NUM_INSTANCES_PER_SET_N100 = 15 # For n100 graphs

COMPLETE_GRAPH_SPECS = {
    "n10": {
        "nodes": 10,
        "instances": NUM_INSTANCES_PER_SET
    },
    "n100": {
        "nodes": 100,
        "instances": NUM_INSTANCES_PER_SET_N100
    },
}

# --- Generation Function ---
def generate_complete_graph_dataset(base_dir, complete_specs):
    overall_summary = []
    
    for size_cat, specs in complete_specs.items():
        n = specs["nodes"] # Number of nodes for the complete graph
        num_instances = specs["instances"]
        
        complete_graph_dir = os.path.join(base_dir, size_cat, "complete") # New directory for complete graphs
        os.makedirs(complete_graph_dir, exist_ok=True)
        
        dataset_info = [] # Metadata for dataset_info.json in this directory
        
        print(f"\nGenerating Complete graphs for n={n}...")

        instance_counter = 0 # Counts successfully generated instances

        for i in range(num_instances):
            graph_id = f"complete_{n}_{i}" # Unique ID string
            
            G = nx.complete_graph(n) # Generate the complete graph
            
            # Ensure node labels are integers for consistency
            G = nx.relabel_nodes(G, {node: int(node) for node in G.nodes()})

            # --- Calculate Graph Properties and Exact mu(G) ---
            num_nodes = G.number_of_nodes()
            num_edges = G.number_of_edges()
            
            # Basic Properties
            avg_degree = num_nodes - 1 if num_nodes > 0 else 0
            max_degree = num_nodes - 1 if num_nodes > 0 else 0

            # Properties for bounds
            current_diameter = 1 if num_nodes > 1 else 0 # Diameter of K_n is 1 (for n > 1)
            current_girth = 3 if num_nodes >= 3 else None # Girth of K_n is 3 (for n >= 3, undefined for K1, K2)
            
            # Average Shortest Path Length (needed for hypergraph Omega bound)
            avg_shortest_path_length = None
            if num_nodes > 1: # Undefined for single node, or if graph is not strongly connected for directed
                try:
                    avg_shortest_path_length = nx.average_shortest_path_length(G)
                except nx.NetworkXError: # Can happen if graph not connected (not for K_n)
                    avg_shortest_path_length = None

            # --- Exact MV number for Complete Graphs ---
            true_mu_num = num_nodes # mu(Kn) = n

            # --- General Bounds for mu(G) ---
            # Based on Di Stefano et al. (2021), Lemma 2.4, Lemma 2.6, Remark 2.7
            
            # General Lower Bound: mu(G) >= Delta(G)
            general_lb_max_degree = max_degree
            
            # General Upper Bound: mu(G) <= n - d + 1
            general_ub_diameter_based = num_nodes - current_diameter + 1
                
            # General Upper Bound: mu(G) <= n - c + 3
            general_ub_girth_based = None
            if current_girth is not None:
                general_ub_girth_based = num_nodes - current_girth + 3

            # --- Hypergraph Omega(sqrt(n/D)) Lower Bound ---
            hypergraph_omega_sqrt_n_D_lower_bound_val = None
            if avg_shortest_path_length is not None and avg_shortest_path_length > 0:
                hypergraph_omega_sqrt_n_D_lower_bound_val = math.sqrt(num_nodes / avg_shortest_path_length)

            # --- Final Bounds (for metadata) ---
            # If exact value is known, upper/lower bounds are the exact value.
            mutual_visibility_lower_bound = true_mu_num
            mutual_visibility_upper_bound = true_mu_num

            # --- Create metadata dictionary ---
            metadata = {
                "filename": f"complete_{n}_{i}.gml", # Filename for GML
                "graph_id": graph_id, # String ID for K_n graphs
                "nodes": num_nodes,
                "edges": num_edges,
                "diameter": current_diameter,
                "girth": current_girth,
                "avg_degree": avg_degree,
                "max_degree": max_degree,
                "avg_shortest_path_length": avg_shortest_path_length,
                "mutual_visibility_number": true_mu_num, # Exact MV number
                "mutual_visibility_lower_bound": mutual_visibility_lower_bound, # Set to exact if known
                "mutual_visibility_upper_bound": mutual_visibility_upper_bound, # Set to exact if known
                "general_lb_max_degree": general_lb_max_degree,
                "general_ub_diameter_based": general_ub_diameter_based,
                "general_ub_girth_based": general_ub_girth_based,
                "hypergraph_omega_sqrt_n_D_lower_bound_val": hypergraph_omega_sqrt_n_D_lower_bound_val,
                "graph_type": "complete",
                "size_category": size_cat,
                "instance": i,
                "seed": None # Complete graphs are deterministic, no random seed
            }
            
            # --- IMPORTANT FIX: Add all metadata to G.graph before writing GML ---
            # nx.write_gml writes attributes from G.graph, so they must be present here.
            for key, value in metadata.items():
                # GML writer can complain about None, so convert to string "None"
                if value is None:
                    G.graph[key] = "None"
                else:
                    G.graph[key] = value

            # Save graph to GML file
            gml_path = os.path.join(complete_graph_dir, metadata["filename"])
            nx.write_gml(G, gml_path)

            # Collect metadata for dataset_info.json (copy of G.graph's values for flat structure)
            # Convert "None" string back to Python None for JSON if needed for analysis.
            json_metadata_for_file = {k: v if v != "None" else None for k,v in G.graph.items()}
            dataset_info.append(json_metadata_for_file)
            overall_summary.append(json_metadata_for_file) 
            instance_counter += 1
        
        # Save dataset_info.json for this size category's K_n graphs
        dataset_info_path = os.path.join(complete_graph_dir, "dataset_info.json")
        with open(dataset_info_path, 'w') as f:
            json.dump(dataset_info, f, indent=4)
        print(f"  Generated {instance_counter} Complete graphs for n={n}.")

    # Save a final overall summary JSON for all K_n graphs generated
    overall_summary_path = os.path.join(base_dir, "overall_complete_summary.json")
    with open(overall_summary_path, 'w') as f:
        json.dump(overall_summary, f, indent=4)
    print(f"\nAll Complete graph generation complete. Total unique graphs generated: {len(overall_summary)}.")


# --- Execution ---
if __name__ == "__main__":
    os.makedirs(BASE_DIR, exist_ok=True)
    
    generate_complete_graph_dataset(BASE_DIR, COMPLETE_GRAPH_SPECS)
    
    print("\nComplete graph generation script finished. Remember to run your experiment_runner.py on the updated datasets.")