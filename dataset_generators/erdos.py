import networkx as nx
import os
import json
import random
import math

# --- Configuration ---
BASE_DIR = "datasets"
NUM_INSTANCES_PER_SET = 15
NUM_INSTANCES_PER_SET_N100 = 15

GRAPH_SPECS = {
    "n10": {
        "nodes": 10,
        "p_values": [0.2, 0.4, 0.6, 0.8],
        "instances": NUM_INSTANCES_PER_SET,
    },
    "n100": {
        "nodes": 100,
        "p_values": [0.05, 0.1, 0.2, 0.4],
        "instances": NUM_INSTANCES_PER_SET_N100,
    },
}


# --- Generation Function ---
def generate_connected_erdos_renyi_dataset(base_dir, graph_specs):

    for size_cat, specs in graph_specs.items():
        n = specs["nodes"]
        p_values = specs["p_values"]
        num_instances = specs["instances"]

        size_dir = os.path.join(base_dir, size_cat)
        erdos_renyi_dir = os.path.join(size_dir, "erdos_renyi")

        os.makedirs(erdos_renyi_dir, exist_ok=True)

        dataset_info = []

        print(f"\nGenerating Erdős-Rényi graphs for n={n}...")

        instance_count = 0

        for p_val in p_values:
            print(f"  Generating for p={p_val} ({num_instances} instances)...")
            for i in range(num_instances):
                graph_id = f"er_{n}_{str(p_val).replace('.', '')}_{i}"

                G = None
                is_connected = False
                attempts = 0
                max_attempts = 200  # Increased attempts for larger N/lower P to ensure connectivity

                while not is_connected and attempts < max_attempts:
                    G_candidate = nx.erdos_renyi_graph(
                        n, p_val, seed=random.randint(0, 1000000)
                    )
                    is_connected = nx.is_connected(G_candidate)
                    if is_connected:
                        G = G_candidate
                    attempts += 1

                if not is_connected:
                    print(
                        f"    Warning: Could not generate connected G({n},{p_val}) after {max_attempts} attempts. Skipping instance {i}."
                    )
                    continue

                # Ensure node labels are integers for consistency
                # nx.erdos_renyi_graph generates integer nodes (0 to n-1) by default, but this is a good safeguard.
                G = nx.relabel_nodes(G, {node: int(node) for node in G.nodes()})

                # --- Calculate Graph Properties and General Bounds ---
                num_nodes = G.number_of_nodes()
                num_edges = G.number_of_edges()

                # Basic Properties
                avg_degree = (
                    sum(dict(G.degree()).values()) / num_nodes if num_nodes > 0 else 0
                )
                max_degree = max(dict(G.degree()).values()) if num_nodes > 0 else 0

                # Bounds-related properties (can be computationally intensive for large graphs)
                current_diameter = None
                current_girth = None
                current_avg_shortest_path_length = None  # For Omega(sqrt(n/D)) bound

                # Diameter calculation (O(N*M) or higher, very slow for large N)
                if (
                    num_nodes <= 1000
                ):  # Threshold can be adjusted based on available computation power
                    try:
                        current_diameter = nx.diameter(G)
                    except (
                        nx.NetworkXError
                    ):  # Graph might be technically connected but paths not found or other issues
                        current_diameter = None
                else:
                    print(
                        f"    Skipping diameter calculation for n={num_nodes} (potentially very slow)."
                    )

                # Girth calculation (also O(N*M) for sparse, can be higher for dense)
                if num_nodes <= 50:  # Threshold can be adjusted
                    try:
                        current_girth = nx.girth(G)
                    except (
                        nx.NetworkXError
                    ):  # Graph is acyclic (a tree) or issues finding cycles for sparse graphs
                        current_girth = None
                else:
                    print(
                        f"    Skipping girth calculation for n={num_nodes} (potentially very slow)."
                    )

                # Average Shortest Path Length (needed for hypergraph Omega bound)
                # Also computationally intensive for large N
                if num_nodes <= 1000:  # Apply same threshold as diameter
                    try:
                        current_avg_shortest_path_length = (
                            nx.average_shortest_path_length(G)
                        )
                    except (
                        nx.NetworkXError
                    ):  # Graph might be disconnected or paths not found
                        current_avg_shortest_path_length = None
                else:
                    print(
                        f"    Skipping average shortest path length calculation for n={num_nodes} (potentially very slow)."
                    )

                # --- General Upper and Lower Bounds for mu(G) ---
                # Based on Di Stefano et al. (2021), Lemma 2.4, Lemma 2.6, Remark 2.7

                # For ER graphs, mu(G) is generally unknown (N/A)
                true_mu_num = None

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

                # --- Hypergraph Omega(sqrt(n/D)) Lower Bound ---
                # The theoretical lower bound for the hypergraph-based approximation method
                hypergraph_omega_sqrt_n_D_lower_bound_val = None
                if (
                    current_avg_shortest_path_length is not None
                    and current_avg_shortest_path_length > 0
                ):
                    hypergraph_omega_sqrt_n_D_lower_bound_val = math.sqrt(
                        num_nodes / current_avg_shortest_path_length
                    )

                # --- Final Bounds (for metadata) ---
                # For ER graphs, these are also None as exact mu(G) is unknown
                mutual_visibility_lower_bound = None
                mutual_visibility_upper_bound = None

                # --- Assign all properties directly to the graph object's attributes (G.graph) ---
                # This ensures the GML file itself contains all the annotations.
                G.graph["filename"] = f"{graph_id}.gml"
                G.graph["graph_id"] = graph_id
                G.graph["nodes"] = num_nodes
                G.graph["edges"] = num_edges
                G.graph["p_value"] = p_val  # Specific to ER graphs
                G.graph["diameter"] = current_diameter
                G.graph["girth"] = current_girth
                G.graph["avg_degree"] = avg_degree
                G.graph["max_degree"] = max_degree
                G.graph["avg_shortest_path_length"] = current_avg_shortest_path_length
                G.graph["mutual_visibility_number"] = true_mu_num  # N/A for ER
                G.graph["mutual_visibility_lower_bound"] = (
                    mutual_visibility_lower_bound  # N/A for ER
                )
                G.graph["mutual_visibility_upper_bound"] = (
                    mutual_visibility_upper_bound  # N/A for ER
                )
                G.graph["general_lb_max_degree"] = general_lb_max_degree
                G.graph["general_ub_diameter_based"] = general_ub_diameter_based
                G.graph["general_ub_girth_based"] = general_ub_girth_based
                G.graph["hypergraph_omega_sqrt_n_D_lower_bound_val"] = (
                    hypergraph_omega_sqrt_n_D_lower_bound_val
                )
                G.graph["graph_type"] = "erdos_renyi"
                G.graph["size_category"] = size_cat
                G.graph["instance"] = i
                G.graph["seed"] = G.graph.get(
                    "seed", None
                )  # Get seed from NetworkX internal, or None

                # Convert None values to "None" string for GML export (NetworkX GML writer sometimes complains)
                for key, value in list(G.graph.items()):
                    if value is None:
                        G.graph[key] = "None"

                # Save graph to GML file
                gml_path = os.path.join(erdos_renyi_dir, G.graph["filename"])
                nx.write_gml(G, gml_path)

                # Collect metadata for dataset_info.json (copy of G.graph's values for flat structure)
                # Convert "None" string back to Python None for JSON if needed for analysis.
                json_metadata_for_file = {
                    k: v if v != "None" else None for k, v in G.graph.items()
                }
                dataset_info.append(json_metadata_for_file)
                instance_count += 1

        # Save dataset_info.json for this size category's ER graphs
        dataset_info_path = os.path.join(erdos_renyi_dir, "dataset_info.json")
        with open(dataset_info_path, "w") as f:
            json.dump(dataset_info, f, indent=4)
        print(f"  Generated {instance_count} connected Erdős-Rényi graphs for n={n}.")

    print(f"\nAll Erdős-Rényi graph generation complete.")


# --- Execution ---
if __name__ == "__main__":
    os.makedirs(BASE_DIR, exist_ok=True)

    generate_connected_erdos_renyi_dataset(BASE_DIR, GRAPH_SPECS)

    print(
        "\nGeneration script finished. Remember to run your experiment_runner.py on the updated datasets."
    )
