import networkx as nx
import os
import random
import math
from pathlib import Path
import json


def count_leaves(G):
    """Count the number of leaf nodes (degree 1) in a tree"""
    return sum(1 for node in G.nodes() if G.degree(node) == 1)


def get_tree_properties(G):
    """Calculate various tree properties for annotation"""
    n = G.number_of_nodes()
    leaves = count_leaves(G)

    # Tree metrics
    diameter = nx.diameter(G)
    radius = nx.radius(G)
    center = nx.center(G)

    # Degree statistics
    degrees = [G.degree(node) for node in G.nodes()]
    max_degree = max(degrees)
    avg_degree = sum(degrees) / len(degrees)

    return {
        "nodes": n,
        "mutual_visibility_number": leaves,  # This is your target variable
        "leaves": leaves,  # Same as mutual visibility for trees
        "diameter": diameter,
        "radius": radius,
        "center_size": len(center),
        "max_degree": max_degree,
        "avg_degree": round(avg_degree, 3),
        "internal_nodes": n - leaves,
        "tree_type": None,  # Will be set by generator
    }


def generate_random_tree(n, seed):
    """Generate random tree using Prüfer sequence"""
    G = nx.random_tree(n, seed=seed)
    return G


def generate_star_tree(n, seed):
    """Generate star tree (1 center, n-1 leaves)"""
    G = nx.star_graph(n - 1)  # star_graph creates n nodes
    return G


def generate_path_tree(n, seed):
    """Generate path tree (2 leaves, all others degree 2)"""
    G = nx.path_graph(n)
    return G


def generate_balanced_tree(n, seed):
    """Generate approximately balanced tree"""
    if n <= 2:
        return nx.path_graph(n)

    # Try to create a balanced tree close to size n
    for r in range(2, min(n, 8)):  # branching factor
        for h in range(1, 15):  # height
            nodes_in_tree = sum(r**i for i in range(h + 1))
            if nodes_in_tree >= n:
                G = nx.balanced_tree(r, h)
                # Trim to exact size if needed
                if G.number_of_nodes() > n:
                    # Remove leaf nodes to get to size n
                    nodes_to_remove = []
                    current_size = G.number_of_nodes()

                    # Get leaves and remove some
                    leaves = [node for node in G.nodes() if G.degree(node) == 1]
                    random.seed(seed)
                    random.shuffle(leaves)

                    for leaf in leaves:
                        if current_size > n:
                            nodes_to_remove.append(leaf)
                            current_size -= 1
                        else:
                            break

                    G.remove_nodes_from(nodes_to_remove)

                return nx.convert_node_labels_to_integers(G)

    # Fallback to random tree
    return generate_random_tree(n, seed)


def generate_caterpillar_tree(n, seed):
    """Generate caterpillar tree (path with leaves attached)"""
    if n <= 2:
        return nx.path_graph(n)

    random.seed(seed)

    # Create backbone path
    backbone_length = max(2, min(n // 2, int(math.sqrt(n))))
    G = nx.path_graph(backbone_length)

    # Add leaves to backbone nodes
    next_node = backbone_length
    remaining_nodes = n - backbone_length

    # Distribute remaining nodes as leaves
    backbone_nodes = list(range(1, backbone_length - 1))  # Skip endpoints
    random.shuffle(backbone_nodes)

    for node in backbone_nodes:
        if remaining_nodes > 0:
            # Add 1-3 leaves to this backbone node
            leaves_to_add = min(remaining_nodes, random.randint(1, 3))
            for _ in range(leaves_to_add):
                G.add_edge(node, next_node)
                next_node += 1
                remaining_nodes -= 1

    # Add any remaining nodes randomly
    while remaining_nodes > 0:
        attach_to = random.choice(list(G.nodes()))
        G.add_edge(attach_to, next_node)
        next_node += 1
        remaining_nodes -= 1

    return G


def generate_binary_tree(n, seed):
    """Generate random binary tree"""
    if n == 1:
        G = nx.Graph()
        G.add_node(0)
        return G

    random.seed(seed)
    G = nx.Graph()
    G.add_node(0)

    for i in range(1, n):
        # Find a node with degree < 2 to attach to
        candidates = [node for node in G.nodes() if G.degree(node) < 2]
        if candidates:
            parent = random.choice(candidates)
        else:
            # If no candidates with degree < 2, pick one with degree 2
            candidates = [node for node in G.nodes() if G.degree(node) == 2]
            if candidates:
                parent = random.choice(candidates)
            else:
                parent = random.choice(list(G.nodes()))

        G.add_edge(parent, i)

    return G


def generate_spider_tree(n, seed):
    """Generate spider tree (star with paths extending from center)"""
    if n <= 3:
        return nx.star_graph(n - 1)

    random.seed(seed)
    G = nx.Graph()
    G.add_node(0)  # Center

    # Determine number of legs
    num_legs = random.randint(3, min(8, n - 1))
    remaining_nodes = n - 1

    # Create legs of random lengths
    next_node = 1
    for leg in range(num_legs):
        if remaining_nodes <= 0:
            break

        # Determine leg length
        if leg == num_legs - 1:  # Last leg gets all remaining nodes
            leg_length = remaining_nodes
        else:
            max_leg_length = max(1, remaining_nodes - (num_legs - leg - 1))
            leg_length = random.randint(1, max_leg_length)

        # Create the leg
        prev_node = 0  # Start from center
        for i in range(leg_length):
            G.add_edge(prev_node, next_node)
            prev_node = next_node
            next_node += 1
            remaining_nodes -= 1

    return G


def create_folder_structure():
    """Create the required folder structure"""
    sizes = [10, 100, 1000]

    # Get the project root directory (parent of current script directory)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    # Create main datasets directory
    datasets_dir = project_root / "datasets"
    datasets_dir.mkdir(exist_ok=True)

    for size in sizes:
        size_dir = datasets_dir / f"n{size}"
        size_dir.mkdir(exist_ok=True)

        # Create trees subdirectory
        trees_dir = size_dir / "trees"
        trees_dir.mkdir(exist_ok=True)

    return project_root


def generate_tree_dataset():
    """Generate complete annotated tree dataset"""

    # Create folder structure and get project root
    project_root = create_folder_structure()

    # Dataset configuration
    sizes = [10, 100, 1000]
    tree_generators = [
        ("random", generate_random_tree),
        ("star", generate_star_tree),
        ("path", generate_path_tree),
        ("balanced", generate_balanced_tree),
        ("caterpillar", generate_caterpillar_tree),
        ("binary", generate_binary_tree),
        ("spider", generate_spider_tree),
    ]

    # Adjust number of instances based on size
    instances_per_type = {
        10: 15,
        100: 20,
        1000: 30,
    }

    all_dataset_info = {}

    print("Generating annotated tree dataset...")
    print("=" * 50)

    for size in sizes:
        print(f"\nGenerating trees of size {size}...")

        dataset_info = []
        graph_id = 0

        for tree_type, generator_func in tree_generators:
            print(f"  Generating {tree_type} trees...")

            instances = instances_per_type[size]

            for instance in range(instances):
                seed = size * 1000 + graph_id * 42 + instance  # Ensure reproducibility

                try:
                    # Generate tree
                    G = generator_func(size, seed)

                    # Initial validation
                    is_valid, error_msg = is_valid_tree(G)
                    if not is_valid:
                        print(
                            f"    Warning: Generated invalid tree for {tree_type}_{size}_{instance}: {error_msg}"
                        )
                        continue

                    # Adjust size if needed (for balanced trees that might be too big)
                    while G.number_of_nodes() > size:
                        # Remove a leaf
                        leaves = [n for n in G.nodes() if G.degree(n) == 1]
                        if leaves:
                            G.remove_node(random.choice(leaves))
                        else:
                            break

                    # Add nodes if too small (shouldn't happen often)
                    while G.number_of_nodes() < size:
                        # Add leaf to random node
                        attach_to = random.choice(list(G.nodes()))
                        new_node = max(G.nodes()) + 1 if G.nodes() else 0
                        G.add_edge(attach_to, new_node)

                    # Final validation after size adjustments
                    is_valid, error_msg = is_valid_tree(G, expected_size=size)
                    if not is_valid:
                        print(
                            f"    Warning: Tree became invalid after size adjustment for {tree_type}_{size}_{instance}: {error_msg}"
                        )
                        continue

                    # Relabel nodes to be consecutive integers starting from 0
                    G = nx.convert_node_labels_to_integers(G)

                    # Calculate properties
                    properties = get_tree_properties(G)
                    properties["tree_type"] = tree_type
                    properties["instance"] = instance
                    properties["graph_id"] = graph_id
                    properties["seed"] = seed

                    # Add graph-level attributes to the NetworkX graph
                    for key, value in properties.items():
                        G.graph[key] = value

                    # Add node attributes
                    for node in G.nodes():
                        G.nodes[node]["degree"] = G.degree(node)
                        G.nodes[node]["is_leaf"] = G.degree(node) == 1
                        G.nodes[node]["eccentricity"] = nx.eccentricity(G, node)

                    # Save as GML
                    filename = (
                        project_root
                        / "datasets"
                        / f"n{size}"
                        / "trees"
                        / f"tree_{graph_id:03d}_{tree_type}_{instance:02d}.gml"
                    )
                    nx.write_gml(G, filename)

                    # Create relative filename for dataset_info.json
                    relative_filename = (
                        f"tree_{graph_id:03d}_{tree_type}_{instance:02d}.gml"
                    )

                    # Add to dataset info
                    dataset_info.append(
                        {
                            "filename": relative_filename,
                            "graph_id": graph_id,
                            **properties,
                        }
                    )

                    graph_id += 1

                except Exception as e:
                    print(f"    Error generating {tree_type} tree of size {size}: {e}")
                    continue

        # Save dataset metadata for this size
        metadata_file = (
            project_root / "datasets" / f"n{size}" / "trees" / "dataset_info.json"
        )
        with open(metadata_file, "w") as f:
            json.dump(dataset_info, f, indent=2)

        all_dataset_info[f"n{size}"] = dataset_info

        # Create summary for this size
        create_size_summary(size, dataset_info, project_root)

        print(f"  Generated {len(dataset_info)} trees for size {size}")

    # Create overall summary
    create_overall_summary(all_dataset_info, project_root)

    print(f"\n" + "=" * 50)
    print("DATASET GENERATION COMPLETE!")
    print("=" * 50)

    total_trees = sum(len(info) for info in all_dataset_info.values())
    print(f"Total trees generated: {total_trees}")
    print(f"Saved in folder structure: ./datasets/n{{size}}/trees/")


def create_size_summary(size, dataset_info, project_root):
    """Create summary statistics for a specific size"""

    summary = {
        "size": size,
        "total_graphs": len(dataset_info),
        "type_distribution": {},
        "mutual_visibility_stats": {},
        "leaf_distribution": {},
    }

    # Type distribution
    types = [item["tree_type"] for item in dataset_info]
    for tree_type in set(types):
        summary["type_distribution"][tree_type] = types.count(tree_type)

    # Mutual visibility number statistics
    mv_numbers = [item["mutual_visibility_number"] for item in dataset_info]
    summary["mutual_visibility_stats"] = {
        "min_leaves": min(mv_numbers),
        "max_leaves": max(mv_numbers),
        "avg_leaves": round(sum(mv_numbers) / len(mv_numbers), 2),
        "median_leaves": sorted(mv_numbers)[len(mv_numbers) // 2],
    }

    # Leaf count distribution
    for leaves in set(mv_numbers):
        summary["leaf_distribution"][leaves] = mv_numbers.count(leaves)

    # Save summary
    summary_file = project_root / "datasets" / f"n{size}" / "trees" / "summary.json"
    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=2)

    # Print summary
    print(f"    Summary for n={size}:")
    print(f"      Total trees: {summary['total_graphs']}")
    print(
        f"      Leaf count range: {summary['mutual_visibility_stats']['min_leaves']} - {summary['mutual_visibility_stats']['max_leaves']}"
    )
    print(f"      Average leaves: {summary['mutual_visibility_stats']['avg_leaves']}")


def create_overall_summary(all_dataset_info, project_root):
    """Create overall dataset summary"""

    overall_summary = {
        "dataset_sizes": list(all_dataset_info.keys()),
        "total_trees": sum(len(info) for info in all_dataset_info.values()),
        "trees_per_size": {size: len(info) for size, info in all_dataset_info.items()},
        "mutual_visibility_ranges": {},
    }

    for size, dataset_info in all_dataset_info.items():
        mv_numbers = [item["mutual_visibility_number"] for item in dataset_info]
        overall_summary["mutual_visibility_ranges"][size] = {
            "min": min(mv_numbers),
            "max": max(mv_numbers),
            "avg": round(sum(mv_numbers) / len(mv_numbers), 2),
        }

    # Save overall summary
    with open(project_root / "datasets" / "overall_tree_summary.json", "w") as f:
        json.dump(overall_summary, f, indent=2)


def is_valid_tree(G, expected_size=None):
    """
    Comprehensive validation that a graph is a valid tree.

    Args:
        G: NetworkX graph
        expected_size: Optional expected number of nodes

    Returns:
        tuple: (is_valid, error_message)
    """
    if G.number_of_nodes() == 0:
        return False, "Graph has no nodes"

    # Check if it's a tree (connected and acyclic)
    if not nx.is_tree(G):
        if not nx.is_connected(G):
            return False, "Graph is not connected"
        else:
            return False, "Graph has cycles (not acyclic)"

    # Check edge count (trees have n-1 edges)
    n_nodes = G.number_of_nodes()
    n_edges = G.number_of_edges()
    if n_edges != n_nodes - 1:
        return (
            False,
            f"Wrong edge count: {n_edges} edges for {n_nodes} nodes (expected {n_nodes-1})",
        )

    # Check expected size if provided
    if expected_size is not None and n_nodes != expected_size:
        return False, f"Wrong size: {n_nodes} nodes (expected {expected_size})"

    # Additional sanity checks
    if n_nodes > 1:
        # Tree with more than 1 node should have at least 2 leaves
        leaves = [n for n in G.nodes() if G.degree(n) == 1]
        if len(leaves) < 2:
            return False, f"Tree has only {len(leaves)} leaves (expected at least 2)"

    return True, "Valid tree"


def verify_dataset_integrity(project_root):
    """
    Verify the integrity of the generated dataset by checking all trees.

    Args:
        project_root: Path to the project root directory

    Returns:
        dict: Summary of verification results
    """
    sizes = [10, 100, 1000]
    verification_results = {}

    print("Verifying dataset integrity...")
    print("=" * 50)

    for size in sizes:
        print(f"\nVerifying trees of size {size}...")

        # Load dataset info
        dataset_info_file = (
            project_root / "datasets" / f"n{size}" / "trees" / "dataset_info.json"
        )
        if not dataset_info_file.exists():
            print(f"  ERROR: dataset_info.json not found for size {size}")
            continue

        with open(dataset_info_file, "r") as f:
            dataset_info = json.load(f)

        results = {
            "total_files": len(dataset_info),
            "valid_trees": 0,
            "invalid_trees": 0,
            "missing_files": 0,
            "size_mismatches": 0,
            "connectivity_errors": 0,
            "errors": [],
        }

        for item in dataset_info:
            filename = item["filename"]
            expected_size = item["nodes"]

            # Check if file exists
            tree_file = project_root / "datasets" / f"n{size}" / "trees" / filename
            if not tree_file.exists():
                results["missing_files"] += 1
                results["errors"].append(f"Missing file: {filename}")
                continue

            try:
                # Load and verify tree
                G = nx.read_gml(tree_file)

                # Validate tree
                is_valid, error_msg = is_valid_tree(G, expected_size)

                if is_valid:
                    results["valid_trees"] += 1
                else:
                    results["invalid_trees"] += 1
                    results["errors"].append(f"{filename}: {error_msg}")

                    if "Wrong size" in error_msg:
                        results["size_mismatches"] += 1
                    if "not connected" in error_msg:
                        results["connectivity_errors"] += 1

            except Exception as e:
                results["invalid_trees"] += 1
                results["errors"].append(f"{filename}: Error loading file - {str(e)}")

        verification_results[f"n{size}"] = results

        # Print summary for this size
        print(f"  Results for n={size}:")
        print(f"    Total files: {results['total_files']}")
        print(f"    Valid trees: {results['valid_trees']}")
        print(f"    Invalid trees: {results['invalid_trees']}")
        print(f"    Missing files: {results['missing_files']}")

        if results["errors"]:
            print(f"    Errors found: {len(results['errors'])}")
            for error in results["errors"][:5]:  # Show first 5 errors
                print(f"      - {error}")
            if len(results["errors"]) > 5:
                print(f"      ... and {len(results['errors']) - 5} more errors")

    print(f"\n" + "=" * 50)
    print("DATASET VERIFICATION COMPLETE!")
    print("=" * 50)

    total_valid = sum(
        results["valid_trees"] for results in verification_results.values()
    )
    total_invalid = sum(
        results["invalid_trees"] for results in verification_results.values()
    )
    total_missing = sum(
        results["missing_files"] for results in verification_results.values()
    )

    print(f"Overall Results:")
    print(f"  Valid trees: {total_valid}")
    print(f"  Invalid trees: {total_invalid}")
    print(f"  Missing files: {total_missing}")
    print(
        f"  Success rate: {total_valid/(total_valid+total_invalid)*100:.1f}%"
        if (total_valid + total_invalid) > 0
        else "N/A"
    )

    return verification_results


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--verify":
        # Verify existing dataset
        script_dir = Path(__file__).parent
        project_root = script_dir.parent
        verify_dataset_integrity(project_root)
    else:
        # Generate new dataset
        generate_tree_dataset()
