import networkx as nx
import os
import random
import math
from pathlib import Path
import json


def get_grid_properties(G, n, m):
    """Calculate various grid graph properties for annotation"""
    nodes = G.number_of_nodes()
    edges = G.number_of_edges()

    # Grid-specific properties
    diameter = nx.diameter(G)
    radius = nx.radius(G)
    center = nx.center(G)

    # Degree statistics
    degrees = [G.degree(node) for node in G.nodes()]
    max_degree = max(degrees)
    avg_degree = sum(degrees) / len(degrees)
    min_degree = min(degrees)

    # Grid corner and edge nodes
    corner_nodes = 4  # Always 4 corners in a grid
    edge_nodes = 2 * (n - 2) + 2 * (m - 2)  # Nodes on the boundary but not corners
    interior_nodes = max(0, (n - 2) * (m - 2))  # Interior nodes

    # Mutual visibility calculation for grid graphs
    # For grid graphs, the mutual visibility number is 2 * min(n, m)
    mutual_visibility_number = 2 * min(n, m)

    return {
        "nodes": nodes,
        "edges": edges,
        "grid_dimensions": [n, m],
        "grid_width": n,
        "grid_height": m,
        "mutual_visibility_number": mutual_visibility_number,
        "diameter": diameter,
        "radius": radius,
        "center_size": len(center),
        "max_degree": max_degree,
        "min_degree": min_degree,
        "avg_degree": round(avg_degree, 3),
        "corner_nodes": corner_nodes,
        "edge_nodes": edge_nodes,
        "interior_nodes": interior_nodes,
        "graph_type": "grid",
    }


def generate_grid_graph(target_size, seed, instance=0):
    """
    Generate grid graph that is close to target_size nodes with varied dimensions.
    Grid is the Cartesian product of two paths: P_n × P_m
    where n > 3 and m > 3, and n * m ≈ target_size

    This function creates diverse grid dimensions rather than always choosing
    the most square-like grid, to provide variety in the dataset.
    """
    random.seed(seed)

    # Find all valid n, m combinations where n > 3, m > 3, and n * m is close to target_size
    valid_combinations = []
    max_dim = target_size  # Allow checking up to target_size for one dimension

    for n in range(4, max_dim + 1):
        for m in range(4, max_dim + 1):
            size = n * m

            # Only consider combinations that are reasonably close to target
            # Allow some flexibility: within 20% of target or at most 10 nodes different for small targets
            if target_size <= 20:
                tolerance = 10
            else:
                tolerance = max(int(target_size * 0.2), 10)

            if abs(size - target_size) <= tolerance:
                diff = abs(size - target_size)
                aspect_ratio = max(n, m) / min(n, m)  # How elongated the grid is
                valid_combinations.append((n, m, size, diff, aspect_ratio))

    if not valid_combinations:
        # Fallback: find the closest possible combination
        best_n, best_m = 4, 4
        best_diff = float("inf")

        for n in range(4, int(math.sqrt(target_size)) + 5):
            for m in range(4, int(math.sqrt(target_size)) + 5):
                size = n * m
                diff = abs(size - target_size)
                if diff < best_diff:
                    best_diff = diff
                    best_n, best_m = n, m

        valid_combinations = [
            (
                best_n,
                best_m,
                best_n * best_m,
                best_diff,
                max(best_n, best_m) / min(best_n, best_m),
            )
        ]

    # Sort combinations by different criteria to encourage variety
    # Use instance number to determine selection strategy
    strategy = instance % 4

    if strategy == 0:
        # Prefer combinations closest to target size
        valid_combinations.sort(key=lambda x: x[3])  # Sort by difference
    elif strategy == 1:
        # Prefer more square-like grids (aspect ratio close to 1)
        valid_combinations.sort(key=lambda x: x[4])  # Sort by aspect ratio
    elif strategy == 2:
        # Prefer more elongated grids (higher aspect ratio)
        valid_combinations.sort(key=lambda x: -x[4])  # Sort by negative aspect ratio
    else:
        # Random selection from valid combinations
        random.shuffle(valid_combinations)

    # Select from top candidates to add some randomness while following strategy
    top_candidates = valid_combinations[: min(3, len(valid_combinations))]
    selected = random.choice(top_candidates)

    n, m, actual_size, diff, aspect_ratio = selected

    # Create grid graph
    G = nx.grid_2d_graph(n, m)

    # Convert node labels to integers for consistency
    G = nx.convert_node_labels_to_integers(G)

    return G, n, m


def is_valid_grid(G, expected_size=None, expected_n=None, expected_m=None):
    """
    Comprehensive validation that a graph is a valid grid.

    Args:
        G: NetworkX graph
        expected_size: Optional expected number of nodes
        expected_n: Expected grid width
        expected_m: Expected grid height

    Returns:
        tuple: (is_valid, error_message)
    """
    if G.number_of_nodes() == 0:
        return False, "Graph has no nodes"

    # Check if it's connected
    if not nx.is_connected(G):
        return False, "Graph is not connected"

    # Check expected size if provided
    n_nodes = G.number_of_nodes()
    if expected_size is not None and n_nodes != expected_size:
        return False, f"Wrong size: {n_nodes} nodes (expected {expected_size})"

    # Check grid dimensions if provided
    if expected_n is not None and expected_m is not None:
        expected_nodes = expected_n * expected_m
        if n_nodes != expected_nodes:
            return (
                False,
                f"Wrong grid size: {n_nodes} nodes (expected {expected_nodes} for {expected_n}×{expected_m} grid)",
            )

    # Basic grid validation: check degree sequence
    degrees = [G.degree(node) for node in G.nodes()]
    max_degree = max(degrees)
    min_degree = min(degrees)

    # In a grid, max degree should be 4 (interior nodes) and min degree should be 2 (corner nodes)
    if max_degree > 4:
        return False, f"Invalid grid: maximum degree {max_degree} > 4"

    if min_degree < 2:
        return False, f"Invalid grid: minimum degree {min_degree} < 2"

    # Count nodes by degree
    degree_counts = {}
    for d in degrees:
        degree_counts[d] = degree_counts.get(d, 0) + 1

    # For a valid n×m grid:
    # - 4 corner nodes with degree 2
    # - 2*(n-2) + 2*(m-2) edge nodes with degree 3
    # - (n-2)*(m-2) interior nodes with degree 4

    if expected_n is not None and expected_m is not None:
        expected_corners = 4
        expected_edges = 2 * (expected_n - 2) + 2 * (expected_m - 2)
        expected_interior = max(0, (expected_n - 2) * (expected_m - 2))

        if degree_counts.get(2, 0) != expected_corners:
            return (
                False,
                f"Wrong number of corner nodes: {degree_counts.get(2, 0)} (expected {expected_corners})",
            )

        if expected_edges > 0 and degree_counts.get(3, 0) != expected_edges:
            return (
                False,
                f"Wrong number of edge nodes: {degree_counts.get(3, 0)} (expected {expected_edges})",
            )

        if expected_interior > 0 and degree_counts.get(4, 0) != expected_interior:
            return (
                False,
                f"Wrong number of interior nodes: {degree_counts.get(4, 0)} (expected {expected_interior})",
            )

    return True, "Valid grid"


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

        # Create grids subdirectory
        grids_dir = size_dir / "grids"
        grids_dir.mkdir(exist_ok=True)

    return project_root


def generate_grid_dataset():
    """Generate complete annotated grid dataset"""

    # Create folder structure and get project root
    project_root = create_folder_structure()

    # Dataset configuration
    sizes = [10, 100, 1000]

    # Grid graphs are only of one kind
    instances_per_type = {
        10: 15,
        100: 20,
        1000: 30,
    }

    all_dataset_info = {}

    print("Generating annotated grid dataset...")
    print("=" * 50)

    for size in sizes:
        print(f"\nGenerating grids of approximately size {size}...")

        dataset_info = []
        graph_id = 0

        instances = instances_per_type[size]

        for instance in range(instances):
            seed = size * 1000 + graph_id * 42 + instance  # Ensure reproducibility

            try:
                # Generate grid with varied dimensions
                G, n, m = generate_grid_graph(size, seed, instance)

                # Initial validation
                is_valid, error_msg = is_valid_grid(G, expected_n=n, expected_m=m)
                if not is_valid:
                    print(
                        f"    Warning: Generated invalid grid for size {size}, instance {instance}: {error_msg}"
                    )
                    continue

                # Relabel nodes to be consecutive integers starting from 0
                G = nx.convert_node_labels_to_integers(G)

                # Calculate properties
                properties = get_grid_properties(G, n, m)
                properties["instance"] = instance
                properties["graph_id"] = graph_id
                properties["seed"] = seed

                # Add graph-level attributes to the NetworkX graph
                for key, value in properties.items():
                    G.graph[key] = value

                # Add node attributes
                for node in G.nodes():
                    G.nodes[node]["degree"] = G.degree(node)
                    G.nodes[node]["eccentricity"] = nx.eccentricity(G, node)

                # Save as GML
                filename = (
                    project_root
                    / "datasets"
                    / f"n{size}"
                    / "grids"
                    / f"grid_{graph_id:03d}_{n}x{m}_{instance:02d}.gml"
                )
                nx.write_gml(G, filename)

                # Create relative filename for dataset_info.json
                relative_filename = f"grid_{graph_id:03d}_{n}x{m}_{instance:02d}.gml"

                # Add to dataset info
                dataset_info.append(
                    {"filename": relative_filename, "graph_id": graph_id, **properties}
                )

                graph_id += 1

            except Exception as e:
                print(f"    Error generating grid of size {size}: {e}")
                continue

        # Save dataset metadata for this size
        metadata_file = (
            project_root / "datasets" / f"n{size}" / "grids" / "dataset_info.json"
        )
        with open(metadata_file, "w") as f:
            json.dump(dataset_info, f, indent=2)

        all_dataset_info[f"n{size}"] = dataset_info

        # Create summary for this size
        create_size_summary(size, dataset_info, project_root)

        print(f"  Generated {len(dataset_info)} grids for size {size}")

    # Create overall summary
    create_overall_summary(all_dataset_info, project_root)

    print(f"\n" + "=" * 50)
    print("DATASET GENERATION COMPLETE!")
    print("=" * 50)

    total_grids = sum(len(info) for info in all_dataset_info.values())
    print(f"Total grids generated: {total_grids}")
    print(f"Saved in folder structure: ./datasets/n{{size}}/grids/")


def create_size_summary(size, dataset_info, project_root):
    """Create summary statistics for a specific size"""

    if not dataset_info:
        return

    summary = {
        "size": size,
        "total_graphs": len(dataset_info),
        "actual_sizes": {},
        "grid_dimensions": {},
        "mutual_visibility_stats": {},
        "degree_distribution": {},
    }

    # Actual size distribution
    actual_sizes = [item["nodes"] for item in dataset_info]
    for actual_size in set(actual_sizes):
        summary["actual_sizes"][actual_size] = actual_sizes.count(actual_size)

    # Grid dimension distribution
    dimensions = [
        f"{item['grid_width']}x{item['grid_height']}" for item in dataset_info
    ]
    for dim in set(dimensions):
        summary["grid_dimensions"][dim] = dimensions.count(dim)

    # Mutual visibility number statistics
    mv_numbers = [item["mutual_visibility_number"] for item in dataset_info]
    summary["mutual_visibility_stats"] = {
        "min_mv": min(mv_numbers),
        "max_mv": max(mv_numbers),
        "avg_mv": round(sum(mv_numbers) / len(mv_numbers), 2),
        "median_mv": sorted(mv_numbers)[len(mv_numbers) // 2],
    }

    # Degree distribution summary
    max_degrees = [item["max_degree"] for item in dataset_info]
    min_degrees = [item["min_degree"] for item in dataset_info]
    summary["degree_distribution"] = {
        "max_degree_range": f"{min(max_degrees)}-{max(max_degrees)}",
        "min_degree_range": f"{min(min_degrees)}-{max(min_degrees)}",
    }

    # Save summary
    summary_file = project_root / "datasets" / f"n{size}" / "grids" / "summary.json"
    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=2)

    # Print summary
    print(f"    Summary for n≈{size}:")
    print(f"      Total grids: {summary['total_graphs']}")
    print(f"      Actual size range: {min(actual_sizes)} - {max(actual_sizes)}")
    print(
        f"      MV number range: {summary['mutual_visibility_stats']['min_mv']} - {summary['mutual_visibility_stats']['max_mv']}"
    )
    print(f"      Average MV: {summary['mutual_visibility_stats']['avg_mv']}")


def create_overall_summary(all_dataset_info, project_root):
    """Create overall dataset summary"""

    overall_summary = {
        "dataset_sizes": list(all_dataset_info.keys()),
        "total_grids": sum(len(info) for info in all_dataset_info.values()),
        "grids_per_size": {size: len(info) for size, info in all_dataset_info.items()},
        "mutual_visibility_ranges": {},
        "size_ranges": {},
    }

    for size, dataset_info in all_dataset_info.items():
        if dataset_info:
            mv_numbers = [item["mutual_visibility_number"] for item in dataset_info]
            actual_sizes = [item["nodes"] for item in dataset_info]

            overall_summary["mutual_visibility_ranges"][size] = {
                "min": min(mv_numbers),
                "max": max(mv_numbers),
                "avg": round(sum(mv_numbers) / len(mv_numbers), 2),
            }

            overall_summary["size_ranges"][size] = {
                "min": min(actual_sizes),
                "max": max(actual_sizes),
                "avg": round(sum(actual_sizes) / len(actual_sizes), 2),
            }

    # Save overall summary
    with open(project_root / "datasets" / "overall_grid_summary.json", "w") as f:
        json.dump(overall_summary, f, indent=2)


def verify_dataset_integrity(project_root):
    """
    Verify the integrity of the generated grid dataset.

    Args:
        project_root: Path to the project root directory

    Returns:
        dict: Summary of verification results
    """
    sizes = [10, 100, 1000]
    verification_results = {}

    print("Verifying grid dataset integrity...")
    print("=" * 50)

    for size in sizes:
        print(f"\nVerifying grids of size ≈{size}...")

        # Load dataset info
        dataset_info_file = (
            project_root / "datasets" / f"n{size}" / "grids" / "dataset_info.json"
        )
        if not dataset_info_file.exists():
            print(f"  ERROR: dataset_info.json not found for size {size}")
            continue

        with open(dataset_info_file, "r") as f:
            dataset_info = json.load(f)

        results = {
            "total_files": len(dataset_info),
            "valid_grids": 0,
            "invalid_grids": 0,
            "missing_files": 0,
            "size_mismatches": 0,
            "connectivity_errors": 0,
            "errors": [],
        }

        for item in dataset_info:
            filename = item["filename"]
            expected_nodes = item["nodes"]
            expected_n = item["grid_width"]
            expected_m = item["grid_height"]

            # Check if file exists
            grid_file = project_root / "datasets" / f"n{size}" / "grids" / filename
            if not grid_file.exists():
                results["missing_files"] += 1
                results["errors"].append(f"Missing file: {filename}")
                continue

            try:
                # Load and verify grid
                G = nx.read_gml(grid_file)

                # Validate grid
                is_valid, error_msg = is_valid_grid(
                    G, expected_nodes, expected_n, expected_m
                )

                if is_valid:
                    results["valid_grids"] += 1
                else:
                    results["invalid_grids"] += 1
                    results["errors"].append(f"{filename}: {error_msg}")

                    if "Wrong size" in error_msg:
                        results["size_mismatches"] += 1
                    if "not connected" in error_msg:
                        results["connectivity_errors"] += 1

            except Exception as e:
                results["invalid_grids"] += 1
                results["errors"].append(f"{filename}: Error loading file - {str(e)}")

        verification_results[f"n{size}"] = results

        # Print summary for this size
        print(f"  Results for n≈{size}:")
        print(f"    Total files: {results['total_files']}")
        print(f"    Valid grids: {results['valid_grids']}")
        print(f"    Invalid grids: {results['invalid_grids']}")
        print(f"    Missing files: {results['missing_files']}")

        if results["errors"]:
            print(f"    Errors found: {len(results['errors'])}")
            for error in results["errors"][:5]:  # Show first 5 errors
                print(f"      - {error}")
            if len(results["errors"]) > 5:
                print(f"      ... and {len(results['errors']) - 5} more errors")

    print(f"\n" + "=" * 50)
    print("GRID DATASET VERIFICATION COMPLETE!")
    print("=" * 50)

    total_valid = sum(
        results["valid_grids"] for results in verification_results.values()
    )
    total_invalid = sum(
        results["invalid_grids"] for results in verification_results.values()
    )
    total_missing = sum(
        results["missing_files"] for results in verification_results.values()
    )

    print(f"Overall Results:")
    print(f"  Valid grids: {total_valid}")
    print(f"  Invalid grids: {total_invalid}")
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
        generate_grid_dataset()
