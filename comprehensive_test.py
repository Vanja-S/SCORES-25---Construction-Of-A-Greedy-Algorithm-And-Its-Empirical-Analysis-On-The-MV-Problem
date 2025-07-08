import networkx as nx
import os
import json
import time
import traceback
from mv_algorithms import (
    bfs_mv,
    mv,
    random_mv_sampling_size,
    get_one_shortest_path_and_internal_vertices,
    build_mv_hypergraph,
    ga_mutual_visibility,
    k_independent_set,
)


def run_dataset_experiments(dataset_base_path="datasets"):
    """
    Iterates through the GML dataset, runs mutual visibility algorithms,
    and collects performance metrics.

    Assumes the following functions are already defined and available:
    - bfs_mv
    - algorithm_mv
    - random_mv_sampling_size
    - get_one_shortest_path_and_internal_vertices
    - build_mv_hypergraph
    - caro_tuza_hypergraph_k_independent_set
    """
    results = []

    size_categories = ["n10", "n100"]  # Modify this list for category processing
    graph_types = [
        "trees",
        "grids",
        "tori",
        "petersen",
        "mycielskian",
        "complete",
        "erdos_renyi",
    ]

    for size_cat in size_categories:
        for graph_type in graph_types:
            type_dir = os.path.join(dataset_base_path, size_cat, graph_type)
            if not os.path.exists(type_dir):
                print(f"Directory not found: {type_dir}. Skipping.")
                continue

            print(f"\n--- Running experiments for {size_cat}/{graph_type} ---")

            # Load dataset_info.json if available, for ground truth MV numbers
            dataset_info_path = os.path.join(type_dir, "dataset_info.json")  #
            graphs_metadata = []
            if os.path.exists(dataset_info_path):
                with open(dataset_info_path, "r") as f:
                    graphs_metadata = json.load(f)  #
            else:
                print(
                    f"Warning: {dataset_info_path} not found. MV numbers will be N/A."
                )  #
            # Iterate through GML files
            for gml_file in os.listdir(type_dir):
                if gml_file.endswith(".gml"):  #
                    gml_path = os.path.join(type_dir, gml_file)  #

                    try:
                        G = nx.read_gml(gml_path)  #
                        G = nx.relabel_nodes(
                            G,
                            {
                                str(node): int(node)
                                for node in G.nodes()
                                if isinstance(node, str) and node.isdigit()
                            },
                        )

                        num_nodes = G.number_of_nodes()
                        num_edges = G.number_of_edges()

                        true_mv_num = G.graph.get("mutual_visibility_number", None)
                        if true_mv_num == "None":
                            true_mv_num = None
                        print(
                            f"  Processing {gml_file} (Nodes: {num_nodes}, Edges: {num_edges}, True MV: {true_mv_num if true_mv_num is not None else 'N/A'})"
                        )

                        # Retrieve the specific bounds from graph attributes as populated by generators
                        mutual_visibility_lower_bound_val = G.graph.get(
                            "mutual_visibility_lower_bound", None
                        )
                        mutual_visibility_upper_bound_val = G.graph.get(
                            "mutual_visibility_upper_bound", None
                        )

                        if true_mv_num is not None:
                            mutual_visibility_lower_bound_val = true_mv_num
                            mutual_visibility_upper_bound_val = true_mv_num

                        hypergraph_omega_sqrt_n_D_lower_bound_val = G.graph.get(
                            "hypergraph_omega_sqrt_n_D_lower_bound_val", None
                        )

                        # --- Run Algorithm 1: Random MV Sampling ---
                        start_time_direct = time.time()
                        mv_set_direct = random_mv_sampling_size(G)
                        runtime_direct = time.time() - start_time_direct
                        size_direct = len(mv_set_direct)

                        # --- Run Algorithm 2: Hypergraph-based (Caro & Tuza) ---
                        start_time_hyper = time.time()
                        mv_set_hyper = k_independent_set(
                            list(G.nodes()), build_mv_hypergraph(G), k=1
                        )  #
                        runtime_hyper = time.time() - start_time_hyper
                        size_hyper = len(mv_set_hyper)

                        # -- Run Algorithm 3: Genetic algorithm
                        start_time_ga = time.time()
                        mv_set_ga = ga_mutual_visibility(G)
                        runtime_ga = time.time() - start_time_ga
                        size_ga = len(mv_set_ga)

                        # Calculate approximation ratios if true_mv_num is known

                        ratio_direct = (
                            size_direct / true_mv_num
                            if true_mv_num is not None and true_mv_num > 0
                            else (
                                1.0 if true_mv_num == 0 and size_direct == 0 else None
                            )
                        )
                        ratio_hyper = (
                            size_hyper / true_mv_num
                            if true_mv_num is not None and true_mv_num > 0
                            else (1.0 if true_mv_num == 0 and size_hyper == 0 else None)
                        )
                        ratio_ga = (
                            size_ga / true_mv_num
                            if true_mv_num is not None and true_mv_num > 0
                            else (1.0 if true_mv_num == 0 and size_ga == 0 else None)
                        )

                        results.append(
                            {
                                "graph_id": gml_file,
                                "size_category": size_cat,
                                "graph_type": graph_type,
                                "num_nodes": num_nodes,
                                "num_edges": num_edges,
                                "true_mv_num": true_mv_num,
                                "random_mv_sampling_size": size_direct,
                                "random_mv_sampling_runtime": runtime_direct,
                                "random_mv_sampling_ratio": ratio_direct,
                                "hypergraph_algo_size": size_hyper,
                                "hypergraph_algo_runtime": runtime_hyper,
                                "hypergraph_algo_ratio": ratio_hyper,
                                "genetic_algo_size": size_ga,
                                "genetic_algo_runtime": runtime_ga,
                                "genetic_algo_ratio": ratio_ga,
                                "mutual_visibility_lower_bound": mutual_visibility_lower_bound_val,
                                "mutual_visibility_upper_bound": mutual_visibility_upper_bound_val,
                                "hypergraph_omega_sqrt_n_D_lower_bound": hypergraph_omega_sqrt_n_D_lower_bound_val,
                            }
                        )

                    except Exception as e:
                        print(f"Error processing {gml_file}: {e}")
                        traceback.print_exc()

    return results


if __name__ == "__main__":

    all_experiment_results = run_dataset_experiments()

    output_filename = "experiment_results.json"  #
    with open(output_filename, "w") as f:
        json.dump(all_experiment_results, f, indent=4)  #
    print(f"\nAll experiment results saved to {output_filename}")

    print("\n--- Experiment Summary (First 5 Results) ---")
    if all_experiment_results:
        for res in all_experiment_results[:5]:  #
            print(
                f"  Graph: {res['graph_id']}, Nodes: {res['num_nodes']}, Type: {res['graph_type']}"
            )
            direct_ratio = res["random_mv_sampling_ratio"]
            if direct_ratio is not None:
                direct_ratio_str = f"{direct_ratio:.2f}"
            else:
                direct_ratio_str = "N/A"
            print(
                f"    True MV: {res['true_mv_num']}, Random MV Sampling: {res['random_mv_sampling_size']} (Ratio: {direct_ratio_str})"
            )

            hypergraph_ratio = res["hypergraph_algo_ratio"]
            if hypergraph_ratio is not None:
                hypergraph_ratio_str = f"{hypergraph_ratio:.2f}"
            else:
                hypergraph_ratio_str = "N/A"
            print(
                f"    Hypergraph Algo: {res['hypergraph_algo_size']} (Ratio: {hypergraph_ratio_str})"
            )

            genetic_ratio = res["genetic_algo_ratio"]
            if genetic_ratio is not None:
                genetic_ratio_str = f"{genetic_ratio:.2f}"
            else:
                genetic_ratio_str = "N/A"
            print(
                f"    Genetic Algo: {res['genetic_algo_size']} (Ratio: {genetic_ratio_str})"
            )
    else:
        print("No results collected (check dataset path and file existence).")
