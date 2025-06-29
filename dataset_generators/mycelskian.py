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
        "nodes": 10,
        "instances": NUM_INSTANCES_PER_SET
    },
    "n100": {
        "nodes": 100,
        "instances": NUM_INSTANCES_PER_SET_N100
    }
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
            return None # For P1, P2, P3: not covered by general formula in paper
    
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
        # 1. Mycielskian of Paths (M(Pn))
        print(f"  Generating M(G) for base_type='path' (n={n_base})...")
        for i in range(num_instances):
            base_graph_name = "path"
            G_base = nx.path_graph(n_base) 
            mu_mycielskian_val = calculate_mu_mycielskian(base_graph_name, n_base)
            
            M_G = nx.mycielskian(G_base) 
            
            graph_id = f"mycielskian_{base_graph_name}_{n_base}_{i}"
            gml_filename = f"{graph_id}.gml"
            gml_path = os.path.join(mycielskian_dir, gml_filename)
            nx.write_gml(M_G, gml_path)

            metadata = {
                "filename": gml_filename,
                "graph_id": graph_id,
                "base_graph_type": base_graph_name,
                "base_graph_nodes": n_base,
                "nodes": M_G.number_of_nodes(), 
                "edges": M_G.number_of_edges(), 
                "mutual_visibility_number": mu_mycielskian_val,
                "size_category": size_cat,
                "instance": i,
                "seed": None 
            }
            dataset_info.append(metadata)
            overall_summary.append(metadata)
            graph_id_counter += 1

        # 2. Mycielskian of Stars (M(K_1,n-1)) - as universal vertex example
        if n_base >= 2: 
            print(f"  Generating M(G) for base_type='star_universal_vertex' (n={n_base} base graph)...")
            for i in range(num_instances):
                base_graph_name = "star_universal_vertex"
                G_base = nx.star_graph(n_base - 1) 
                mu_mycielskian_val = calculate_mu_mycielskian(base_graph_name, n_base)
                
                M_G = nx.mycielskian(G_base)
                
                graph_id = f"mycielskian_{base_graph_name}_{n_base}_{i}"
                gml_filename = f"{graph_id}.gml"
                gml_path = os.path.join(mycielskian_dir, gml_filename)
                nx.write_gml(M_G, gml_path)

                metadata = {
                    "filename": gml_filename,
                    "graph_id": graph_id,
                    "base_graph_type": base_graph_name,
                    "base_graph_nodes": n_base,
                    "nodes": M_G.number_of_nodes(),
                    "edges": M_G.number_of_edges(),
                    "mutual_visibility_number": mu_mycielskian_val,
                    "size_category": size_cat,
                    "instance": i,
                    "seed": None
                }
                dataset_info.append(metadata)
                overall_summary.append(metadata)
                graph_id_counter += 1

        # 3. Mycielskian of Cycles (M(Cn)) - Exact values available
        if n_base >= 3: # C3 is the smallest cycle
            print(f"  Generating M(G) for base_type='cycle' (n={n_base} base graph)...")
            for i in range(num_instances):
                base_graph_name = "cycle"
                G_base = nx.cycle_graph(n_base) 
                mu_mycielskian_val = calculate_mu_mycielskian(base_graph_name, n_base)
                
                M_G = nx.mycielskian(G_base)
                
                graph_id = f"mycielskian_{base_graph_name}_{n_base}_{i}"
                gml_filename = f"{graph_id}.gml"
                gml_path = os.path.join(mycielskian_dir, gml_filename)
                nx.write_gml(M_G, gml_path)

                metadata = {
                    "filename": gml_filename,
                    "graph_id": graph_id,
                    "base_graph_type": base_graph_name,
                    "base_graph_nodes": n_base,
                    "nodes": M_G.number_of_nodes(),
                    "edges": M_G.number_of_edges(),
                    "mutual_visibility_number": mu_mycielskian_val,
                    "size_category": size_cat,
                    "instance": i,
                    "seed": None 
                }
                dataset_info.append(metadata)
                overall_summary.append(metadata)
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
    