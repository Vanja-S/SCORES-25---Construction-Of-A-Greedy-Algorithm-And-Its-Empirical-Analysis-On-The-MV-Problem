import networkx as nx
import os
import json
import random
import math 

# --- Configuration ---
BASE_DIR = "datasets"
NUM_INSTANCES_PER_SET = 15 
NUM_INSTANCES_PER_SET_N100 = 15 

MYCIELSKIAN_GRAPH_SPECS = {
    "n10": {
        "nodes": 10, # Base graph size n_base
        "instances": NUM_INSTANCES_PER_SET
    },
    "n100": {
        "nodes": 100, # Base graph size n_base
        "instances": NUM_INSTANCES_PER_SET_N100
    },
}

# --- Function to calculate exact mu(M(G)) based on Roy et al. (2024) ---
def calculate_mu_mycielskian(base_graph_type, n_base_graph):
    """
    Calculates the exact mu(M(G)) based on formulas from Roy et al. (2024).
    
    Parameters:
    - base_graph_type (str): Type of the base graph ('path', 'star_universal_vertex', 'cycle').
    - n_base_graph (int): Number of nodes in the base graph G.
    
    Returns:
    - int: The exact mu(M(G)) if formula exists, None otherwise.
    """
    if base_graph_type == 'path':
        # Theorem 5.1: mu(M(Pn)) = n + floor((n+1)/4) for n >= 5
        # Special case mu(M(P4)) = 6 (as given in paper p.14)
        if n_base_graph == 4:
            return 6
        elif n_base_graph >= 5:
            return n_base_graph + math.floor((n_base_graph + 1) / 4)
        else: 
            return None 
    
    elif base_graph_type == 'star_universal_vertex':
        # Proposition 5.3: If G has a universal vertex, mu(M(G)) = 2*n(G) - 1
        if n_base_graph >= 2: 
            return 2 * n_base_graph - 1
        else: 
            return None 
            
    elif base_graph_type == 'cycle':
        # Theorem 5.2: mu(M(Cn)) = n + floor(n/4) for n >= 8
        # For 4 <= n <= 7, mu(M(Cn)) = n + 2
        if n_base_graph >= 8:
            return n_base_graph + math.floor(n_base_graph / 4)
        elif 4 <= n_base_graph <= 7:
            return n_base_graph + 2
        else: 
            return None 
    
    return None

# --- Main Generation Loop ---
def generate_mycielskian_dataset(base_dir, mycielskian_specs):
    overall_summary = [] 
    
    for size_cat, specs in mycielskian_specs.items():
        n_base = specs["nodes"] # Number of nodes for the *base* graph G
        num_instances = specs["instances"]
        
        mycielskian_dir = os.path.join(base_dir, size_cat, "mycielskian")
        os.makedirs(mycielskian_dir, exist_ok=True)
        
        dataset_info = [] 
        
        print(f"\nGenerating Mycielskian graphs for n={n_base} base graphs...")

        graph_id_counter = 0 

        # --- Base Graph Types for Mycielskian ---
        base_graph_types_to_generate = [
            "path", 
            "star_universal_vertex", 
            "cycle"
        ]

        for base_graph_name in base_graph_types_to_generate:
            print(f"  Generating M(G) for base_type='{base_graph_name}' (n={n_base})...")
            
            for i in range(num_instances):
                G_base = None
                if base_graph_name == "path":
                    G_base = nx.path_graph(n_base)
                elif base_graph_name == "star_universal_vertex":
                    if n_base >= 2: 
                        G_base = nx.star_graph(n_base - 1)
                    else:
                        print(f"    Skipping star_universal_vertex for n_base={n_base} (too small).")
                        continue
                elif base_graph_name == "cycle":
                    if n_base >= 3: 
                        G_base = nx.cycle_graph(n_base)
                    else:
                        print(f"    Skipping cycle for n_base={n_base} (too small).")
                        continue
                
                if G_base is None:
                    continue

                mu_mycielskian_val = calculate_mu_mycielskian(base_graph_name, n_base)
                
                M_G = nx.mycielskian(G_base) 
                
                # Ensure nodes are integers for consistency with algorithms
                M_G = nx.relabel_nodes(M_G, {node: int(node) for node in M_G.nodes()})

                # --- Calculate ALL Graph Properties for M(G) and General Bounds ---
                num_nodes_mycielskian = M_G.number_of_nodes()
                num_edges_mycielskian = M_G.number_of_edges()
                
                avg_degree_mycielskian = sum(dict(M_G.degree()).values()) / num_nodes_mycielskian if num_nodes_mycielskian > 0 else 0
                max_degree_mycielskian = max(dict(M_G.degree()).values()) if num_nodes_mycielskian > 0 else 0

                mycielskian_diameter = None
                mycielskian_girth = None
                mycielskian_avg_shortest_path_length = None 
                
                # Threshold for expensive calculations (M(G) has 2N+1 nodes)
                if num_nodes_mycielskian <= 500: 
                    try: 
                        mycielskian_diameter = nx.diameter(M_G)
                    except nx.NetworkXError: 
                        pass 
                    try: 
                        mycielskian_girth = nx.girth(M_G)
                    except nx.NetworkXError: 
                        pass
                    try: 
                        mycielskian_avg_shortest_path_length = nx.average_shortest_path_length(M_G)
                    except nx.NetworkXError: 
                        pass
                else:
                    print(f"    Skipping detailed property calculations for M(G) n={num_nodes_mycielskian}.")

                # General Bounds for mu(G) (from Di Stefano et al. (2021))
                general_lb_max_degree_myc = max_degree_mycielskian
                
                general_ub_diameter_myc = num_nodes_mycielskian - mycielskian_diameter + 1 if mycielskian_diameter is not None else None
                    
                general_ub_girth_myc = None
                if mycielskian_girth is not None:
                    general_ub_girth_myc = num_nodes_mycielskian - mycielskian_girth + 3

                # --- Hypergraph Omega(sqrt(n/D)) Lower Bound ---
                hypergraph_omega_sqrt_n_D_lower_bound_val = None
                if mycielskian_avg_shortest_path_length is not None and mycielskian_avg_shortest_path_length > 0:
                    hypergraph_omega_sqrt_n_D_lower_bound_val = math.sqrt(num_nodes_mycielskian / mycielskian_avg_shortest_path_length)

                # --- Final Bounds (for metadata added to G.graph and then to GML) ---
                # These are set to mu_mycielskian_val if known, otherwise None.
                mutual_visibility_lower_bound = mu_mycielskian_val 
                mutual_visibility_upper_bound = mu_mycielskian_val 
                
                # --- Assign all properties directly to the graph object's attributes (M_G.graph) ---
                M_G.graph['filename'] = f"{graph_id_counter:03d}_mycielskian_{base_graph_name}_{n_base}_{i}.gml" 
                M_G.graph['graph_id'] = f"mycielskian_{base_graph_name}_{n_base}_{i}"
                M_G.graph['base_graph_type'] = base_graph_name
                M_G.graph['base_graph_nodes'] = n_base
                M_G.graph['nodes'] = num_nodes_mycielskian
                M_G.graph['edges'] = num_edges_mycielskian
                M_G.graph['mutual_visibility_number'] = mu_mycielskian_val
                M_G.graph['mutual_visibility_lower_bound'] = mutual_visibility_lower_bound
                M_G.graph['mutual_visibility_upper_bound'] = mutual_visibility_upper_bound
                M_G.graph['diameter'] = mycielskian_diameter
                M_G.graph['girth'] = mycielskian_girth
                M_G.graph['avg_degree'] = avg_degree_mycielskian
                M_G.graph['max_degree'] = max_degree_mycielskian
                M_G.graph['avg_shortest_path_length'] = mycielskian_avg_shortest_path_length
                M_G.graph['general_lb_max_degree'] = general_lb_max_degree_myc
                M_G.graph['general_ub_diameter_based'] = general_ub_diameter_myc
                M_G.graph['general_ub_girth_based'] = general_ub_girth_myc
                M_G.graph['hypergraph_omega_sqrt_n_D_lower_bound_val'] = hypergraph_omega_sqrt_n_D_lower_bound_val 
                M_G.graph['graph_type'] = "mycielskian"
                M_G.graph['size_category'] = size_cat
                M_G.graph['instance'] = i
                M_G.graph['seed'] = random.randint(0, 1000000) 
                
                # --- Convert None values to "None" string for GML export ---
                # NetworkX GML writer sometimes complains about None values.
                for key, value in list(M_G.graph.items()): # Iterate over a copy of items
                    if value is None:
                        M_G.graph[key] = "None" 

                # Save graph (now with all properties in M_G.graph)
                gml_filename = M_G.graph['filename']
                gml_path = os.path.join(mycielskian_dir, gml_filename)
                nx.write_gml(M_G, gml_path)

                # Collect metadata for dataset_info.json (copy M_G.graph for flat structure)
                # It's better to store the actual Python None in JSON for data analysis
                # So, create a separate dict for JSON if you modified for GML writing.
                json_metadata = {k: v if v != "None" else None for k,v in M_G.graph.items()}
                dataset_info.append(json_metadata)
                overall_summary.append(json_metadata)
                graph_id_counter += 1
            
        dataset_info_path = os.path.join(mycielskian_dir, "dataset_info.json")
        with open(dataset_info_path, 'w') as f:
            json.dump(dataset_info, f, indent=4)
        print(f"  Generated {len(dataset_info)} Mycielskian graphs for n={n_base} base graphs.")

    overall_summary_path = os.path.join(base_dir, "overall_mycielskian_summary.json")
    with open(overall_summary_path, 'w') as f:
        json.dump(overall_summary, f, indent=4)
    print(f"\nAll Mycielskian graph generation complete. Total unique graphs generated: {len(overall_summary)}.")

# --- Execution ---
if __name__ == "__main__":
    os.makedirs(BASE_DIR, exist_ok=True)
    
    generate_mycielskian_dataset(BASE_DIR, MYCIELSKIAN_GRAPH_SPECS)
    
    print("\nMycielskian generation script finished. Remember to run your experiment_runner.py on the updated datasets.")