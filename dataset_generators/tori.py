import networkx as nx
import os
import random
import math
from pathlib import Path
import json


def get_torus_properties(G, n, m):
    """Calculate various torus graph properties for annotation"""
    nodes = G.number_of_nodes()
    edges = G.number_of_edges()

    # Torus-specific properties
    diameter = nx.diameter(G)
    radius = nx.radius(G)
    # Skip center calculation due to type issues, use a default
    center_size = 1

    # Degree statistics
    degrees = [G.degree(node) for node in G.nodes()]
    max_degree = max(degrees)
    avg_degree = sum(degrees) / len(degrees)
    min_degree = min(degrees)

    # For torus graphs, all nodes have degree 4 (regular graph)
    assert (
        max_degree == min_degree == 4
    ), f"Torus should be 4-regular, got degrees {min_degree}-{max_degree}"

    # Mutual visibility upper bound for torus graphs
    # The exact mutual visibility number is not known, but mv <= 3 * min(m, n)
    mutual_visibility_upper_bound = 3 * min(n, m)

    if nodes > 1000:
        print(
            f"    Skipping average shortest path length calculation for M(G) n={nodes} (potentially slow)."
        )
    elif nodes > 0:
        try:
            mycielskian_avg_shortest_path_length = nx.average_shortest_path_length(G)
        except nx.NetworkXError:
            pass

    hypergraph_omega_sqrt_n_D_lower_bound_val = None
    if (
        mycielskian_avg_shortest_path_length is not None
        and mycielskian_avg_shortest_path_length > 0
    ):
        hypergraph_omega_sqrt_n_D_lower_bound_val = math.sqrt(
            nodes / mycielskian_avg_shortest_path_length
        )

    return {
        "nodes": nodes,
        "edges": edges,
        "torus_dimensions": [n, m],
        "torus_width": n,
        "torus_height": m,
        "mutual_visibility_upper_bound": mutual_visibility_upper_bound,
        "hypergraph_omega_sqrt_n_D_lower_bound_val": hypergraph_omega_sqrt_n_D_lower_bound_val,
        "diameter": diameter,
        "radius": radius,
        "center_size": center_size,
        "max_degree": max_degree,
        "min_degree": min_degree,
        "avg_degree": round(avg_degree, 3),
        "graph_type": "torus",
    }


def annotate_torus_nodes(G, properties):
    """Add node-level properties to a torus graph"""
    eccentricities = nx.eccentricity(G)

    for node in G.nodes():
        G.nodes[node]["degree"] = G.degree(node)
        G.nodes[node]["eccentricity"] = eccentricities[node]

    return G


def generate_torus_for_size(target_size, instance, seed):
    """
    Generate a torus graph with approximately target_size nodes.

    A torus is the Cartesian product of two cycles C_n × C_m where n, m >= 3.
    The resulting graph has n * m nodes and is 4-regular.

    Args:
        target_size: Target number of nodes
        instance: Instance number for variety
        seed: Random seed for reproducibility

    Returns:
        tuple: (NetworkX graph, n, m)
    """
    random.seed(seed)

    # Find valid (n, m) combinations where n, m >= 3 and n * m ≈ target_size
    valid_combinations = []
    tolerance = max(1, target_size * 0.2)  # Allow 20% tolerance

    # Search for valid combinations
    for n in range(3, int(math.sqrt(target_size * 2)) + 5):
        for m in range(3, target_size // n + 5):
            actual_size = n * m
            if abs(actual_size - target_size) <= tolerance:
                diff = abs(actual_size - target_size)
                aspect_ratio = max(n, m) / min(n, m)
                valid_combinations.append([n, m, actual_size, diff, aspect_ratio])

    if not valid_combinations:
        # Fallback: find closest possible size
        best_diff = float("inf")
        best_n, best_m = 3, 3

        for n in range(3, int(math.sqrt(target_size * 2)) + 10):
            for m in range(3, target_size // n + 10):
                actual_size = n * m
                diff = abs(actual_size - target_size)
                if diff < best_diff:
                    best_diff = diff
                    best_n, best_m = n, m

        valid_combinations = [
            [
                best_n,
                best_m,
                best_n * best_m,
                best_diff,
                max(best_n, best_m) / min(best_n, best_m),
            ]
        ]

    # Sort combinations by different criteria to encourage variety
    # Use instance number to determine selection strategy
    strategy = instance % 4

    if strategy == 0:
        # Prefer combinations closest to target size
        valid_combinations.sort(key=lambda x: x[3])  # Sort by difference
    elif strategy == 1:
        # Prefer more square-like tori (aspect ratio close to 1)
        valid_combinations.sort(key=lambda x: x[4])  # Sort by aspect ratio
    elif strategy == 2:
        # Prefer more elongated tori (higher aspect ratio)
        valid_combinations.sort(key=lambda x: -x[4])  # Sort by negative aspect ratio
    else:
        # Random selection from valid combinations
        random.shuffle(valid_combinations)

    # Select from top candidates to add some randomness while following strategy
    top_candidates = valid_combinations[: min(3, len(valid_combinations))]
    selected = random.choice(top_candidates)

    n, m, actual_size, diff, aspect_ratio = selected

    # Create torus graph (Cartesian product of two cycles)
    # NetworkX doesn't have a direct torus generator, so we create it manually
    G = create_torus_graph(n, m)

    return G, n, m


def create_torus_graph(n, m):
    """
    Create a torus graph as the Cartesian product of two cycles C_n × C_m.

    Args:
        n: Size of first cycle
        m: Size of second cycle

    Returns:
        NetworkX graph representing the torus
    """
    # Create empty graph
    G = nx.Graph()

    # Add nodes
    for i in range(n):
        for j in range(m):
            G.add_node(i * m + j)

    # Add edges
    for i in range(n):
        for j in range(m):
            current_node = i * m + j

            # Horizontal edges (cycle in the m direction)
            next_j = (j + 1) % m
            next_node_horizontal = i * m + next_j
            G.add_edge(current_node, next_node_horizontal)

            # Vertical edges (cycle in the n direction)
            next_i = (i + 1) % n
            next_node_vertical = next_i * m + j
            G.add_edge(current_node, next_node_vertical)

    return G


def is_valid_torus(G, expected_size=None, expected_n=None, expected_m=None):
    """
    Comprehensive validation that a graph is a valid torus.

    Args:
        G: NetworkX graph
        expected_size: Optional expected number of nodes
        expected_n: Expected torus width
        expected_m: Expected torus height

    Returns:
        tuple: (is_valid, error_message)
    """
    try:
        # Basic connectivity check
        if not nx.is_connected(G):
            return False, "Graph is not connected"

        # Check if it's a cycle (no trees allowed)
        if nx.is_tree(G):
            return False, "Graph is a tree, not a torus"

        # Size validation
        actual_size = G.number_of_nodes()
        if expected_size is not None and actual_size != expected_size:
            return False, f"Expected {expected_size} nodes, got {actual_size}"

        # Check if all nodes have degree 4 (torus should be 4-regular)
        degrees = [G.degree(node) for node in G.nodes()]
        if not all(deg == 4 for deg in degrees):
            return False, f"Torus should be 4-regular, got degrees: {set(degrees)}"

        # Check expected dimensions if provided
        if expected_n is not None and expected_m is not None:
            expected_edges = (
                2 * expected_n * expected_m
            )  # Each node has degree 4, so 2*n*m edges
            actual_edges = G.number_of_edges()
            if actual_edges != expected_edges:
                return (
                    False,
                    f"Expected {expected_edges} edges for {expected_n}×{expected_m} torus, got {actual_edges}",
                )

        # Verify torus structure by checking cycles
        # A torus should have specific cycle structure
        if expected_n is not None and expected_m is not None:
            # The number of nodes should match n * m
            if actual_size != expected_n * expected_m:
                return (
                    False,
                    f"Expected {expected_n * expected_m} nodes for {expected_n}×{expected_m} torus, got {actual_size}",
                )

        return True, "Valid torus"

    except Exception as e:
        return False, f"Validation error: {str(e)}"


def save_torus_to_gml(G, properties, filename, output_dir):
    """Save torus graph to GML format with metadata"""
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Add graph-level properties
    for key, value in properties.items():
        G.graph[key] = value

    # Save to GML format
    filepath = os.path.join(output_dir, filename)
    nx.write_gml(G, filepath)

    return filepath


def create_torus_dataset_info(torus_data, output_dir):
    """Create metadata file for the torus dataset"""
    dataset_info = []

    for data in torus_data:
        info = {
            "filename": data["filename"],
            "graph_id": data["graph_id"],
            **data["properties"],
        }
        dataset_info.append(info)

    # Save dataset info
    info_path = os.path.join(output_dir, "dataset_info.json")
    with open(info_path, "w") as f:
        json.dump(dataset_info, f, indent=2)

    return info_path


def create_torus_summary(torus_data, output_dir):
    """Create statistical summary of the torus dataset"""
    if not torus_data:
        return None

    # Extract numerical properties for statistics
    nodes = [data["properties"]["nodes"] for data in torus_data]
    edges = [data["properties"]["edges"] for data in torus_data]
    diameters = [data["properties"]["diameter"] for data in torus_data]
    radii = [data["properties"]["radius"] for data in torus_data]
    mv_bounds = [
        data["properties"]["mutual_visibility_upper_bound"] for data in torus_data
    ]

    def stats(values):
        return {
            "min": min(values),
            "max": max(values),
            "mean": round(sum(values) / len(values), 2),
            "count": len(values),
        }

    summary = {
        "dataset_info": {
            "total_tori": len(torus_data),
            "generation_date": "2025-06-27",
            "graph_type": "torus",
        },
        "size_distribution": {"nodes": stats(nodes), "edges": stats(edges)},
        "structural_properties": {
            "diameter": stats(diameters),
            "radius": stats(radii),
            "mutual_visibility_upper_bound": stats(mv_bounds),
        },
        "torus_dimensions": {
            "dimension_pairs": list(
                set(
                    (
                        data["properties"]["torus_width"],
                        data["properties"]["torus_height"],
                    )
                    for data in torus_data
                )
            )
        },
    }

    # Save summary
    summary_path = os.path.join(output_dir, "summary.json")
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    return summary_path


def generate_torus_dataset():
    """Generate complete torus dataset with multiple size categories"""
    print("🔄 Generating torus dataset...")

    # Define size categories and instance counts
    size_configs = [
        {"target": 10, "instances": 15, "label": "n10"},
        {"target": 100, "instances": 20, "label": "n100"},
    ]

    # Base directory for datasets
    datasets_dir = Path("../datasets")
    all_torus_data = []

    global_graph_id = 0

    for size_config in size_configs:
        target_size = size_config["target"]
        num_instances = size_config["instances"]
        size_label = size_config["label"]

        print(
            f"\n📊 Generating {num_instances} tori for size category {size_label} (target ~{target_size} nodes)"
        )

        # Create output directory
        output_dir = datasets_dir / size_label / "tori"
        output_dir.mkdir(parents=True, exist_ok=True)

        torus_data = []

        for instance in range(num_instances):
            # Use a deterministic seed based on size and instance
            seed = 10000 + target_size + instance * 43

            try:
                # Generate torus
                G, n, m = generate_torus_for_size(target_size, instance, seed)

                # Validate torus
                is_valid, error_msg = is_valid_torus(G, expected_n=n, expected_m=m)
                if not is_valid:
                    print(
                        f"❌ Generated invalid torus for instance {instance}: {error_msg}"
                    )
                    continue

                # Calculate properties
                properties = get_torus_properties(G, n, m)
                properties["instance"] = instance
                properties["graph_id"] = global_graph_id
                properties["seed"] = seed

                # Annotate nodes
                G = annotate_torus_nodes(G, properties)

                # Create filename
                filename = f"torus_{instance:03d}_{n}x{m}_{instance:02d}.gml"

                # Save torus
                filepath = save_torus_to_gml(G, properties, filename, output_dir)

                # Store data for metadata
                torus_data.append(
                    {
                        "filename": filename,
                        "filepath": filepath,
                        "graph_id": global_graph_id,
                        "properties": properties,
                    }
                )

                print(
                    f"  ✅ Generated torus {instance:03d}: {n}×{m} torus ({n*m} nodes) -> {filename}"
                )

                global_graph_id += 1

            except Exception as e:
                print(f"❌ Error generating torus {instance}: {str(e)}")
                continue

        # Create metadata files
        if torus_data:
            info_path = create_torus_dataset_info(torus_data, output_dir)
            summary_path = create_torus_summary(torus_data, output_dir)

            print(f"📋 Created metadata: {info_path}")
            print(f"📈 Created summary: {summary_path}")
            print(f"✅ Generated {len(torus_data)} valid tori for {size_label}")

            all_torus_data.extend(torus_data)
        else:
            print(f"❌ No valid tori generated for {size_label}")

    # Create overall summary
    if all_torus_data:
        print(f"🎉 Total dataset: {len(all_torus_data)} torus graphs generated!")

    return all_torus_data


def verify_torus_dataset():
    """Verify the integrity of existing torus datasets"""
    print("🔍 Verifying torus dataset...")

    datasets_dir = Path("../datasets")
    size_categories = ["n10", "n100"]

    total_files = 0
    valid_tori = 0
    errors = []

    for size_label in size_categories:
        torus_dir = datasets_dir / size_label / "tori"

        if not torus_dir.exists():
            errors.append(f"Directory {torus_dir} does not exist")
            continue

        print(f"\n📂 Verifying {size_label} tori...")

        # Check if dataset_info.json exists
        info_file = torus_dir / "dataset_info.json"
        if not info_file.exists():
            errors.append(f"Missing dataset_info.json in {torus_dir}")
            continue

        # Load metadata
        with open(info_file, "r") as f:
            dataset_info = json.load(f)

        for entry in dataset_info:
            filename = entry["filename"]
            expected_nodes = entry["nodes"]
            expected_n = entry["torus_width"]
            expected_m = entry["torus_height"]

            filepath = torus_dir / filename
            total_files += 1

            if not filepath.exists():
                errors.append(f"Missing file: {filepath}")
                continue

            try:
                # Load graph
                G = nx.read_gml(filepath)

                # Validate torus
                is_valid, error_msg = is_valid_torus(
                    G, expected_nodes, expected_n, expected_m
                )

                if is_valid:
                    valid_tori += 1
                    print(
                        f"  ✅ {filename}: Valid {expected_n}×{expected_m} torus ({expected_nodes} nodes)"
                    )
                else:
                    errors.append(f"{filename}: {error_msg}")
                    print(f"  ❌ {filename}: {error_msg}")

            except Exception as e:
                errors.append(f"{filename}: Failed to load - {str(e)}")
                print(f"  ❌ {filename}: Failed to load - {str(e)}")

    # Print summary
    print(f"\n📊 Verification Summary:")
    print(f"Total files checked: {total_files}")
    print(f"Valid tori: {valid_tori}")
    print(f"Errors: {len(errors)}")

    if errors:
        print(f"\n❌ Errors found:")
        for error in errors[:10]:  # Show first 10 errors
            print(f"  - {error}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more errors")
    else:
        print("✅ All tori are valid!")

    return valid_tori == total_files and len(errors) == 0


def main():
    """Main function to handle command line arguments"""
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="Generate and verify torus graph datasets for mutual visibility research"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify existing dataset integrity instead of generating new data",
    )

    args = parser.parse_args()

    if args.verify:
        success = verify_torus_dataset()
        sys.exit(0 if success else 1)
    else:
        torus_data = generate_torus_dataset()
        if torus_data:
            print(f"\n🎉 Successfully generated {len(torus_data)} torus graphs!")
        else:
            print("\n❌ Failed to generate torus dataset")
            sys.exit(1)


if __name__ == "__main__":
    main()
