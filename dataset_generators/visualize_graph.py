#!/usr/bin/env python3
"""
Graph Visualization Script

A simple script to load and visualize graphs from GML files.
Useful for examining the generated datasets (trees, grids, torus, Petersen graphs).

Usage:
    python visualize_graph.py <path_to_gml_file>
    python visualize_graph.py --help
"""

import argparse
import sys
from pathlib import Path
import matplotlib.pyplot as plt
import networkx as nx


def visualize_graph(
    gml_file,
    output_file=None,
    layout="spring",
    node_size=300,
    figsize=(10, 8),
    show_labels=True,
    save_only=False,
):
    """
    Load and visualize a graph from a GML file.

    Args:
        gml_file: Path to the GML file
        output_file: Optional path to save the visualization
        layout: Layout algorithm ("spring", "circular", "kamada_kawai", "planar", "shell")
        node_size: Size of the nodes
        figsize: Figure size tuple
        show_labels: Whether to show node labels
        save_only: If True, only save the image without displaying it
    """
    try:
        # Load the graph
        G = nx.read_gml(gml_file)
        print(
            f"📊 Loaded graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges"
        )

        # Determine graph type from filename for better visualization
        filename = Path(gml_file).name.lower()

        # Set up the figure
        plt.figure(figsize=figsize)

        # Choose layout based on graph type or user preference
        if layout == "auto":
            if "petersen" in filename:
                layout = "circular"
            elif "grid" in filename:
                layout = "kamada_kawai"
            elif "torus" in filename:
                layout = "spring"
            elif "tree" in filename:
                layout = "spring"
            else:
                layout = "spring"

        # Generate node positions
        if layout == "spring":
            pos = nx.spring_layout(G, k=1, iterations=50)
        elif layout == "circular":
            pos = nx.circular_layout(G)
        elif layout == "kamada_kawai":
            pos = nx.kamada_kawai_layout(G)
        elif layout == "planar":
            if nx.is_planar(G):
                pos = nx.planar_layout(G)
            else:
                print("⚠️ Graph is not planar, falling back to spring layout")
                pos = nx.spring_layout(G, k=1, iterations=50)
        elif layout == "shell":
            pos = nx.shell_layout(G)
        else:
            pos = nx.spring_layout(G, k=1, iterations=50)

        # Color nodes based on graph type
        if "petersen" in filename:
            # Color Petersen graphs with two cycles in different colors
            n_nodes = G.number_of_nodes()
            n = n_nodes // 2
            node_colors = [
                "lightblue" if i < n else "lightcoral" for i in range(n_nodes)
            ]
            title_suffix = "Generalized Petersen Graph"
        elif "grid" in filename:
            node_colors = "lightgreen"
            title_suffix = "Grid Graph"
        elif "torus" in filename:
            node_colors = "lightyellow"
            title_suffix = "Torus Graph"
        elif "tree" in filename:
            # Color tree nodes by degree
            degrees = dict(G.degree())
            max_degree = max(degrees.values()) if degrees else 1
            node_colors = [
                plt.cm.viridis(degrees[node] / max_degree) for node in G.nodes()
            ]
            title_suffix = "Tree Graph"
        else:
            node_colors = "lightblue"
            title_suffix = "Graph"

        # Draw the graph
        nx.draw(
            G,
            pos,
            node_color=node_colors,
            node_size=node_size,
            with_labels=show_labels,
            font_size=8,
            font_weight="bold",
            edge_color="gray",
            alpha=0.7,
        )

        # Add title with graph properties
        basic_properties = f"{G.number_of_nodes()} nodes, {G.number_of_edges()} edges"
        if nx.is_connected(G):
            diameter = nx.diameter(G)
            basic_properties += f", diameter: {diameter}"

        plt.title(
            f"{title_suffix}\n{Path(gml_file).name}\n{basic_properties}",
            fontsize=12,
            fontweight="bold",
        )

        # Adjust layout
        plt.tight_layout()

        # Save or show
        if output_file:
            plt.savefig(output_file, dpi=300, bbox_inches="tight")
            print(f"💾 Saved visualization to: {output_file}")

        if not save_only:
            plt.show()
        else:
            plt.close()

    except FileNotFoundError:
        print(f"❌ Error: File '{gml_file}' not found")
        return False
    except Exception as e:
        print(f"❌ Error loading or visualizing graph: {e}")
        return False

    return True


def visualize_multiple_graphs(
    gml_files, output_dir=None, layout="auto", grid_size=None
):
    """
    Visualize multiple graphs in a grid layout.

    Args:
        gml_files: List of GML file paths
        output_dir: Directory to save individual images
        layout: Layout algorithm to use
        grid_size: Tuple (rows, cols) for subplot grid, auto-calculated if None
    """
    n_graphs = len(gml_files)

    if grid_size is None:
        # Auto-calculate grid size
        cols = min(4, n_graphs)
        rows = (n_graphs + cols - 1) // cols
    else:
        rows, cols = grid_size

    fig, axes = plt.subplots(rows, cols, figsize=(cols * 4, rows * 4))
    if n_graphs == 1:
        axes = [axes]
    elif rows == 1:
        axes = [axes] if cols == 1 else axes
    else:
        axes = axes.flatten()

    for i, gml_file in enumerate(gml_files):
        if i >= len(axes):
            break

        try:
            G = nx.read_gml(gml_file)

            # Choose layout
            if layout == "auto":
                filename = Path(gml_file).name.lower()
                if "petersen" in filename:
                    pos = nx.circular_layout(G)
                elif "tree" in filename:
                    pos = nx.spring_layout(G, k=1, iterations=50)
                else:
                    pos = nx.spring_layout(G, k=0.5, iterations=30)
            else:
                pos = nx.spring_layout(G, k=0.5, iterations=30)

            # Draw on subplot
            ax = axes[i]
            nx.draw(
                G,
                pos,
                ax=ax,
                node_size=50,
                node_color="lightblue",
                with_labels=False,
                edge_color="gray",
                alpha=0.7,
            )

            ax.set_title(
                f"{Path(gml_file).name}\n{G.number_of_nodes()}n, {G.number_of_edges()}e",
                fontsize=8,
            )
            ax.set_aspect("equal")

        except Exception as e:
            print(f"⚠️ Error with {gml_file}: {e}")
            continue

    # Hide unused subplots
    for i in range(n_graphs, len(axes)):
        axes[i].set_visible(False)

    plt.tight_layout()

    if output_dir:
        output_path = Path(output_dir) / "multiple_graphs.png"
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        print(f"💾 Saved multiple graph visualization to: {output_path}")

    plt.show()


def main():
    parser = argparse.ArgumentParser(
        description="Visualize graphs from GML files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Visualize a single graph
  python visualize_graph.py datasets/n10/petersen/petersen_000_gp_5_1.gml
  
  # Save visualization to file
  python visualize_graph.py datasets/n10/trees/tree_000_random_00.gml -o tree_vis.png
  
  # Use circular layout for Petersen graphs
  python visualize_graph.py datasets/n10/petersen/petersen_001_gp_5_2.gml -l circular
  
  # Visualize multiple graphs
  python visualize_graph.py datasets/n10/petersen/*.gml -m
        """,
    )

    parser.add_argument(
        "gml_files", nargs="+", help="Path(s) to GML file(s) to visualize"
    )

    parser.add_argument(
        "-o",
        "--output",
        help="Output file to save the visualization (PNG, PDF, SVG supported)",
    )

    parser.add_argument(
        "-l",
        "--layout",
        choices=["spring", "circular", "kamada_kawai", "planar", "shell", "auto"],
        default="auto",
        help="Layout algorithm (default: auto)",
    )

    parser.add_argument(
        "-s",
        "--node-size",
        type=int,
        default=300,
        help="Size of the nodes (default: 300)",
    )

    parser.add_argument(
        "--figsize",
        nargs=2,
        type=int,
        default=[10, 8],
        help="Figure size in inches (width height, default: 10 8)",
    )

    parser.add_argument(
        "--no-labels", action="store_true", help="Don't show node labels"
    )

    parser.add_argument(
        "--save-only", action="store_true", help="Only save the image, don't display it"
    )

    parser.add_argument(
        "-m",
        "--multiple",
        action="store_true",
        help="Visualize multiple graphs in a grid layout",
    )

    parser.add_argument(
        "--grid-size",
        nargs=2,
        type=int,
        help="Grid size for multiple graphs (rows cols)",
    )

    args = parser.parse_args()

    # Expand glob patterns
    gml_files = []
    for pattern in args.gml_files:
        path = Path(pattern)
        if path.exists():
            gml_files.append(str(path))
        else:
            # Try glob expansion
            matches = list(Path(".").glob(pattern))
            if matches:
                gml_files.extend(str(m) for m in matches)
            else:
                print(f"⚠️ No files found matching: {pattern}")

    if not gml_files:
        print("❌ No valid GML files found")
        sys.exit(1)

    print(f"📁 Found {len(gml_files)} GML file(s)")

    # Visualize graphs
    if args.multiple and len(gml_files) > 1:
        visualize_multiple_graphs(
            gml_files,
            output_dir=Path(args.output).parent if args.output else None,
            layout=args.layout,
            grid_size=tuple(args.grid_size) if args.grid_size else None,
        )
    else:
        for gml_file in gml_files:
            success = visualize_graph(
                gml_file,
                output_file=args.output,
                layout=args.layout,
                node_size=args.node_size,
                figsize=tuple(args.figsize),
                show_labels=not args.no_labels,
                save_only=args.save_only,
            )

            if not success:
                print(f"❌ Failed to visualize: {gml_file}")


if __name__ == "__main__":
    main()
