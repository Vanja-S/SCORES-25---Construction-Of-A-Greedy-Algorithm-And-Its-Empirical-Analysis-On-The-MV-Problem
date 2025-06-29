import networkx as nx
import os
import random
import math
from pathlib import Path
import json


def create_generalized_petersen_graph(n, k):
    """
    Create a generalized Petersen graph GP(n, k).

    Args:
        n: Number of vertices in each cycle (outer and inner)
        k: Step size for inner cycle connections

    Returns:
        NetworkX graph representing GP(n, k)
    """
    if k >= n or k <= 0:
        raise ValueError(f"Invalid parameters: k={k} must be in range 1 <= k < n={n}")

    # Create empty graph
    G = nx.Graph()

    # Add vertices: 0 to n-1 (outer cycle), n to 2n-1 (inner cycle)
    G.add_nodes_from(range(2 * n))

    # Add outer cycle edges: (i, i+1 mod n)
    for i in range(n):
        G.add_edge(i, (i + 1) % n)

    # Add inner cycle edges: (n+i, n+(i+k) mod n)
    for i in range(n):
        G.add_edge(n + i, n + ((i + k) % n))

    # Add spoke edges: (i, n+i)
    for i in range(n):
        G.add_edge(i, n + i)

    return G


def get_valid_k_values(n):
    """
    Get valid k values for GP(n, k) that produce interesting, non-isomorphic graphs.

    Args:
        n: The n parameter for GP(n, k)

    Returns:
        List of valid k values
    """
    import math

    valid_k = []
    for k in range(1, n // 2 + 1):
        # Include all k values up to n//2 for variety
        # We could add gcd(n,k) == 1 constraint for more restrictions, but
        # we want variety in our dataset
        valid_k.append(k)

    return valid_k


def get_petersen_properties(G, n, k):
    """Calculate properties of a generalized Petersen graph for annotation, including general bounds."""
    num_nodes = G.number_of_nodes()
    num_edges = G.number_of_edges()

    # Basic graph properties
    is_connected = nx.is_connected(G)
    is_regular = all(dict(G.degree())[v] == 3 for v in G.nodes())

    # --- Computationally intensive properties with safeguards ---
    diameter = float("inf")
    radius = float("inf")
    center_size = 0
    avg_shortest_path_length = None  # For hypergraph Omega bound

    if (
        num_nodes <= 100
    ):  # Threshold for calculations like diameter, radius, center, ASPL
        if is_connected:
            try:
                diameter = nx.diameter(G)
                radius = nx.radius(G)
                center_size = len(nx.center(G))
                avg_shortest_path_length = nx.average_shortest_path_length(G)
            except nx.NetworkXError:
                pass  # Already initialized to inf/None if error

    # Degree statistics
    degrees = dict(G.degree())
    max_degree = max(degrees.values()) if degrees else 0
    min_degree = min(degrees.values()) if degrees else 0
    avg_degree = sum(degrees.values()) / len(degrees) if degrees else 0

    # Planarity
    is_planar = nx.is_planar(G)

    # Girth of GP(n,k) - typically 5 for k=1, 5 or 6 for k>1, depends on specifics
    girth = None
    if num_nodes <= 50:  # Threshold for girth calculation
        try:
            girth = nx.girth(G)
        except nx.NetworkXError:
            pass  # Graph might be acyclic (girth undefined)

    # --- NEW FIELD: Hypergraph Omega(sqrt(n/D)) Lower Bound ---
    hypergraph_omega_sqrt_n_D_lower_bound_val = None
    if avg_shortest_path_length is not None and avg_shortest_path_length > 0:
        hypergraph_omega_sqrt_n_D_lower_bound_val = math.sqrt(
            num_nodes / avg_shortest_path_length
        )

    properties = {
        "nodes": num_nodes,
        "edges": num_edges,
        "petersen_n": n,
        "petersen_k": k,
        "is_connected": is_connected,
        "is_3_regular": is_regular,
        "diameter": diameter,
        "radius": radius,
        "center_size": center_size,
        "max_degree": max_degree,
        "min_degree": min_degree,
        "avg_degree": avg_degree,
        "girth": girth,
        "is_planar": is_planar,
        "clustering_coefficient": nx.average_clustering(
            G
        ),  # Add remaining properties from original user code
        "density": nx.density(G),
        "avg_shortest_path_length": avg_shortest_path_length,  # Include ASPL value
        "hypergraph_omega_sqrt_n_D_lower_bound_val": hypergraph_omega_sqrt_n_D_lower_bound_val,  # The new bound
    }

    # These properties were in original user code, keeping for consistency (though not always needed for GP)
    # automorphism_group_size and has_hamiltonian_cycle are very expensive, omitted for performance
    # properties["automorphism_group_size"] = "not_computed"
    # properties["has_hamiltonian_cycle"] = "not_computed"

    return properties


def get_target_n_values(target_size, tolerance=0.1):
    """
    Get n values where 2n is within tolerance of target_size.

    Args:
        target_size: Target number of nodes (approximately)
        tolerance: Allowable deviation (0.1 = 10%)

    Returns:
        List of valid n values
    """
    min_size = target_size * (1 - tolerance)
    max_size = target_size * (1 + tolerance)

    valid_n = []
    # Convert to integers for range()
    for n in range(3, int(max_size // 2) + 2):  # Start from n=3 for interesting graphs
        total_nodes = 2 * n
        if min_size <= total_nodes <= max_size:
            valid_n.append(n)

    return valid_n


def generate_petersen_dataset():
    """Generate the complete dataset of generalized Petersen graphs"""

    print("🔄 Generating generalized Petersen graph dataset...")

    # Get script directory and create output structure
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    datasets_dir = project_root / "datasets"

    # Target sizes with some variation
    size_configs = [
        {
            "name": "n10",
            "target": 10,
            "tolerance": 0.15,
        },  # Allow 15% variation for small graphs
        {"name": "n100", "target": 100, "tolerance": 0.1},
    ]

    all_petersen_data = []
    size_summaries = {}

    for size_config in size_configs:
        size_name = size_config["name"]
        target_size = size_config["target"]
        tolerance = size_config["tolerance"]

        print(
            f"\n📊 Generating Petersen graphs for {size_name} (target: ~{target_size} nodes)..."
        )

        # Create output directory
        size_dir = datasets_dir / size_name / "petersen"
        size_dir.mkdir(parents=True, exist_ok=True)

        # Get valid n values for this size (n in GP(n,k) represents outer cycle size)
        valid_n_values = get_target_n_values(target_size, tolerance)

        if not valid_n_values:
            print(f"  ⚠️  No valid n values found for target size {target_size}")
            continue

        petersen_data = []
        graph_count = 0
        max_graphs_per_size = 100  # Safety limit to prevent excessive generation

        print(f"  Valid n values: {valid_n_values}")

        for n_petersen in valid_n_values:
            if graph_count >= max_graphs_per_size:
                print(
                    f"  ⚠️  Reached maximum graphs limit ({max_graphs_per_size}) for {size_name}"
                )
                break

            valid_k_values = get_valid_k_values(n_petersen)
            print(f"  🔧 Processing n={n_petersen}, k values: {valid_k_values}")

            for k_petersen in valid_k_values:
                if graph_count >= max_graphs_per_size:
                    break

                try:
                    # Create the graph
                    G = create_generalized_petersen_graph(n_petersen, k_petersen)

                    # Calculate properties
                    properties = get_petersen_properties(G, n_petersen, k_petersen)

                    # --- Assign all properties directly to the graph object's attributes (G.graph) ---
                    # For Petersen graphs, mu(G) is generally unknown (N/A)
                    properties["mutual_visibility_number"] = None
                    properties["mutual_visibility_lower_bound"] = None
                    properties["mutual_visibility_upper_bound"] = None

                    # Set additional graph_level attributes before writing GML
                    properties["graph_type"] = "petersen"
                    properties["size_category"] = size_name
                    properties["instance"] = graph_count
                    properties["seed"] = (
                        10000 + graph_count
                    )  # For consistency with other scripts
                    properties["filename"] = (
                        f"petersen_{graph_count:03d}_gp_{n_petersen}_{k_petersen}.gml"
                    )
                    properties["graph_id"] = graph_count

                    for key, value in properties.items():
                        # Convert None values to "None" string for GML export
                        if value is None:
                            G.graph[key] = "None"
                        else:
                            G.graph[key] = value

                    # Write graph to file
                    filepath = size_dir / properties["filename"]
                    nx.write_gml(G, filepath)

                    # Store metadata in unified flat array format (like other scripts)
                    # For JSON, convert "None" string back to Python None
                    json_info = {
                        k: v if v != "None" else None for k, v in properties.items()
                    }
                    petersen_data.append(json_info)

                    print(
                        f"    ✅ Generated graph {graph_count:03d}: GP({n_petersen},{k_petersen}) ({2*n_petersen} nodes) -> {properties['filename']}"
                    )
                    graph_count += 1

                except Exception as e:
                    print(
                        f"    ❌ Failed to generate GP({n_petersen},{k_petersen}): {e}"
                    )
                    continue

        if petersen_data:
            # Calculate summary statistics
            node_counts = [g["nodes"] for g in petersen_data]
            diameters = [
                g["diameter"] for g in petersen_data if g["diameter"] != float("inf")
            ]

            summary = {
                "size_category": size_name,
                "target_size": target_size,
                "total_graphs": len(petersen_data),
                "node_count_range": {
                    "min": min(node_counts),
                    "max": max(node_counts),
                    "avg": sum(node_counts) / len(node_counts) if node_counts else 0,
                },
                "diameter_range": {
                    "min": min(diameters) if diameters else 0,
                    "max": max(diameters) if diameters else 0,
                    "avg": sum(diameters) / len(diameters) if diameters else 0,
                },
            }

            # Save dataset info in unified flat array format (like other scripts)
            info_file = size_dir / "dataset_info.json"
            with open(info_file, "w") as f:
                json.dump(petersen_data, f, indent=2)

            # Save summary
            summary_file = size_dir / "summary.json"
            with open(summary_file, "w") as f:
                json.dump(summary, f, indent=2)

            size_summaries[size_name] = summary
            all_petersen_data.extend(petersen_data)

            print(f"    Summary for {size_name}:")
            print(f"      Total graphs: {len(petersen_data)}")
            print(f"      Node count range: {min(node_counts)} - {max(node_counts)}")
            print(f"      Average nodes: {sum(node_counts) / len(node_counts):.1f}")

            print(f"📋 Created metadata: {info_file}")
            print(f"📈 Created summary for {size_name}")
            print(
                f"✅ Generated {len(petersen_data)} Petersen graphs for size {size_name}"
            )
        else:
            print(f"  ❌ No graphs generated for {size_name}")

    # Create overall summary
    if all_petersen_data:
        print(
            f"🎉 Total dataset: {len(all_petersen_data)} generalized Petersen graphs generated!"
        )

        return all_petersen_data

    return []


def validate_petersen_graph(G, n, k):
    """
    Validate that a graph is a correctly generated GP(n, k).

    Args:
        G: NetworkX graph
        n: Expected n parameter
        k: Expected k parameter

    Returns:
        tuple: (is_valid, error_message)
    """
    if G.number_of_nodes() != 2 * n:
        return False, f"Expected {2*n} nodes, got {G.number_of_nodes()}"

    if G.number_of_edges() != 3 * n:
        return False, f"Expected {3*n} edges, got {G.number_of_edges()}"

    # Check if all vertices have degree 3
    degrees = dict(G.degree())
    for v in G.nodes():
        if degrees[v] != 3:
            return False, f"Vertex {v} has degree {degrees[v]}, expected 3"

    # Check connectivity
    if not nx.is_connected(G):
        return False, "Graph is not connected"

    # Check outer cycle
    for i in range(n):
        if not G.has_edge(i, (i + 1) % n):
            return False, f"Missing outer cycle edge: {i} - {(i + 1) % n}"

    # Check inner cycle
    for i in range(n):
        inner_v1 = n + i
        inner_v2 = n + ((i + k) % n)
        if not G.has_edge(inner_v1, inner_v2):
            return False, f"Missing inner cycle edge: {inner_v1} - {inner_v2}"

    # Check spokes
    for i in range(n):
        if not G.has_edge(i, n + i):
            return False, f"Missing spoke edge: {i} - {n + i}"

    return True, "Valid generalized Petersen graph"


def verify_petersen_dataset():
    """Verify the integrity of generated Petersen graph dataset"""

    print("🔍 Verifying generalized Petersen graph dataset integrity...")

    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    datasets_dir = project_root / "datasets"

    sizes = ["n10", "n100", "n1000"]
    total_valid = 0
    total_invalid = 0
    total_missing = 0

    verification_results = []

    for size in sizes:
        print(f"\n📊 Verifying {size} Petersen graphs...")

        size_dir = datasets_dir / size / "petersen"
        info_file = size_dir / "dataset_info.json"

        if not info_file.exists():
            print(f"  ❌ No dataset info found for {size}")
            continue

        # Load dataset info
        with open(info_file, "r") as f:
            dataset_info = json.load(f)

        size_valid = 0
        size_invalid = 0
        size_missing = 0

        for graph_info in dataset_info.get("graphs", []):
            filename = graph_info["filename"]
            filepath = size_dir / filename
            n = graph_info["parameters"]["n"]
            k = graph_info["parameters"]["k"]

            if not filepath.exists():
                print(f"    ❌ Missing file: {filename}")
                size_missing += 1
                continue

            try:
                # Load and validate graph
                G = nx.read_gml(filepath)
                is_valid, error_msg = validate_petersen_graph(G, n, k)

                if is_valid:
                    print(f"    ✅ Valid: {filename} (GP({n},{k}))")
                    size_valid += 1
                else:
                    print(f"    ❌ Invalid: {filename} - {error_msg}")
                    size_invalid += 1

            except Exception as e:
                print(f"    ❌ Error loading {filename}: {e}")
                size_invalid += 1

        total_valid += size_valid
        total_invalid += size_invalid
        total_missing += size_missing

        print(f"  Results for {size}:")
        print(f"    ✅ Valid: {size_valid}")
        print(f"    ❌ Invalid: {size_invalid}")
        print(f"    📁 Missing: {size_missing}")

        verification_results.append(
            {
                "size": size,
                "valid": size_valid,
                "invalid": size_invalid,
                "missing": size_missing,
            }
        )

    print(f"\n📊 Overall Verification Results:")
    print(f"  ✅ Valid graphs: {total_valid}")
    print(f"  ❌ Invalid graphs: {total_invalid}")
    print(f"  📁 Missing files: {total_missing}")

    if total_invalid == 0 and total_missing == 0:
        print("🎉 All Petersen graphs are valid!")
    else:
        print("⚠️  Some issues found in dataset")

    return total_valid == (total_valid + total_invalid) and total_missing == 0


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="Generate and verify generalized Petersen graph datasets for mutual visibility research"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify existing dataset integrity instead of generating new data",
    )

    args = parser.parse_args()

    if args.verify:
        # Verify existing dataset
        success = verify_petersen_dataset()
        sys.exit(0 if success else 1)
    else:
        # Generate new dataset
        petersen_data = generate_petersen_dataset()
        if petersen_data:
            print(
                f"\n🎉 Successfully generated {len(petersen_data)} generalized Petersen graphs!"
            )
        else:
            print("\n❌ Failed to generate Petersen dataset")
            sys.exit(1)
