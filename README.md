# Construction Of A Greedy Algorithm And Its Empirical Analysis On The MV Problem

Research paper submitted to the conference SCORES 25, in the field of graph theory, tackling the mutual-visibility problem. Co-authored with Bor Pangeršič.

## Dataset Generation and Verification

This project includes a comprehensive dataset generation system for creating both tree and grid graph instances to test mutual visibility algorithms. The mutual visibility problem on trees is equivalent to finding the minimum number of leaves needed, while grid graphs provide a different structural challenge for algorithm development and empirical analysis.

### Dataset Structure

The generated dataset is organized as follows:

```text
datasets/
├── overall_summary.json          # Global tree dataset statistics
├── overall_grid_summary.json     # Global grid dataset statistics
├── n10/                         # Graphs with ~10 nodes
│   ├── trees/
│   │   ├── dataset_info.json   # Metadata for all trees in this size
│   │   ├── summary.json         # Statistical summary for trees
│   │   └── tree_*.gml          # Individual tree files in GML format
│   └── grids/
│       ├── dataset_info.json   # Metadata for all grids in this size
│       ├── summary.json         # Statistical summary for grids
│       └── grid_*.gml          # Individual grid files in GML format
├── n100/                       # Graphs with ~100 nodes
│   ├── trees/
│   └── grids/
└── n1000/                      # Graphs with ~1000 nodes
    ├── trees/
    └── grids/
```

### Graph Types Generated

The dataset includes two main categories of graphs:

#### Tree Graphs

Seven different types of trees, each with specific structural properties:

1. **Random Trees**: Generated using Prüfer sequences for unbiased random structures
2. **Star Trees**: One central node connected to all other nodes (n-1 leaves)
3. **Path Trees**: Linear chains of nodes (2 leaves, minimal mutual visibility)
4. **Balanced Trees**: Approximately balanced binary/k-ary trees
5. **Caterpillar Trees**: Path backbone with leaves attached to internal nodes
6. **Binary Trees**: Random binary tree structures
7. **Spider Trees**: Star-like structures with paths extending from the center

#### Grid Graphs

Grid graphs are Cartesian products of two paths (P_n × P_m) where:

- Both dimensions n > 3 and m > 3
- Generated to approximate target sizes (10, 100, 1000 nodes)
- Regular 2D lattice structures with well-defined geometric properties
- Examples: 4×4 (16 nodes), 10×10 (100 nodes), 28×36 (1008 nodes)

### Dataset Sizes and Instances

#### Trees
- **Small trees (n=10)**: 15 instances per type × 7 types = 105 total trees
- **Medium trees (n=100)**: 20 instances per type × 7 types = 140 total trees
- **Large trees (n=1000)**: 30 instances per type × 7 types = 210 total trees

**Total tree dataset**: 455 annotated tree instances

#### Grids
- **Small grids (n≈10-20)**: 15 instances = 15 total grids (variable dimensions like 4×4, 4×5, 5×4)
- **Medium grids (n≈100)**: 20 instances = 20 total grids (10×10, 100 nodes each)
- **Large grids (n≈1000)**: 30 instances = 30 total grids (28×36, 1008 nodes each)

**Total grid dataset**: 65 annotated grid instances (with varied dimensions)

**Combined dataset size**: 520 total graph instances

### Graph Properties and Annotations

Each graph instance includes comprehensive metadata:

#### Tree Properties

- `nodes`: Number of vertices
- `mutual_visibility_number`: Number of leaves (target value for MV problem)
- `leaves`: Number of leaf nodes (same as mutual_visibility_number for trees)
- `diameter`: Maximum shortest path distance between any two nodes
- `radius`: Minimum eccentricity among all nodes
- `center_size`: Number of nodes in the center of the tree
- `max_degree`: Maximum degree of any node
- `avg_degree`: Average degree across all nodes
- `internal_nodes`: Number of non-leaf nodes
- `tree_type`: Type of tree generation algorithm used
- `instance`: Instance number within the type
- `graph_id`: Unique identifier across the entire dataset
- `seed`: Random seed used for reproducible generation

#### Grid Properties

- `nodes`: Number of vertices
- `edges`: Number of edges
- `grid_dimensions`: Array [n, m] of grid dimensions
- `grid_width`: Width of the grid (n)
- `grid_height`: Height of the grid (m)
- `mutual_visibility_number`: Computed dominating set size (approximation)
- `diameter`: Maximum shortest path distance
- `radius`: Minimum eccentricity among all nodes
- `center_size`: Number of nodes in the center
- `max_degree`: Maximum degree (4 for interior nodes)
- `min_degree`: Minimum degree (2 for corner nodes)
- `avg_degree`: Average degree across all nodes
- `corner_nodes`: Number of corner nodes (always 4)
- `edge_nodes`: Number of boundary nodes (excluding corners)
- `interior_nodes`: Number of interior nodes
- `graph_type`: Always "grid"
- `instance`: Instance number
- `graph_id`: Unique identifier
- `seed`: Random seed used for reproducible generation

#### Node-level Properties

- `degree`: Degree of each node
- `is_leaf`: Boolean indicating if the node is a leaf (trees only)
- `eccentricity`: Maximum distance from this node to any other node

### Generation Process

#### Tree Generation (`dataset generators/trees.py`)

To generate a new tree dataset:

```bash
cd "dataset generators"
python trees.py
```

#### Grid Generation (`dataset generators/grids.py`)

To generate a new grid dataset:

```bash
cd "dataset generators"
python grids.py
```

The generation process includes:

1. **Folder Structure Creation**: Automatically creates the required directory hierarchy
2. **Type-specific Generation**: Uses specialized algorithms for each tree type
3. **Size Validation**: Ensures all trees have exactly the specified number of nodes
4. **Connectivity Verification**: Validates that all generated graphs are connected trees
5. **Property Calculation**: Computes all structural and metric properties
6. **File Export**: Saves trees in GML format with embedded metadata
7. **Summary Generation**: Creates statistical summaries at multiple levels

#### Quality Assurance

The generation process includes comprehensive validation:

- **Tree Structure Validation**: Ensures graphs are connected and acyclic
- **Edge Count Verification**: Confirms n-1 edges for n nodes
- **Size Consistency**: Validates exact node counts
- **Connectivity Checks**: Ensures all trees are connected
- **Leaf Count Validation**: Verifies minimum leaf requirements

### Dataset Verification

To verify the integrity of existing datasets:

#### Tree Dataset Verification

```bash
cd "dataset generators"
python trees.py --verify
```

#### Grid Dataset Verification

```bash
cd "dataset generators"
python grids.py --verify
```

The verification process checks:

- **File Existence**: Confirms all referenced files exist
- **Graph Validity**: Validates graph structure and connectivity
- **Size Consistency**: Verifies node counts match metadata
- **Property Accuracy**: Checks computed properties against actual graph structure
- **Grid Structure**: Validates proper grid topology and degree distribution (grids only)
- **Tree Structure**: Validates tree connectivity and acyclicity (trees only)

#### Verification Results

The verification system provides detailed reports including:

- Total files processed
- Number of valid vs. invalid trees
- Missing file detection
- Size mismatch identification
- Connectivity error reporting
- Overall success rate calculation

### File Formats

#### GML Format

Tree instances are stored in Graph Modeling Language (GML) format, which includes:

- Complete graph structure (nodes and edges)
- All computed properties as graph attributes
- Node-level annotations
- Human-readable format suitable for NetworkX

#### JSON Metadata

- `dataset_info.json`: Complete metadata for all trees in a size category
- `summary.json`: Statistical summaries per size
- `overall_summary.json`: Global dataset statistics

### Usage in Research

This dataset is designed for:

- **Algorithm Testing**: Standardized instances for mutual visibility algorithms on both trees and grids
- **Performance Analysis**: Diverse graph structures for comprehensive evaluation
- **Structural Comparison**: Trees vs. grids provide different algorithmic challenges
- **Reproducible Research**: Seeded generation ensures consistent results
- **Scalability Studies**: Multiple size categories for performance scaling analysis
- **Geometric Analysis**: Grid graphs enable study of spatial/geometric properties

### Dataset Statistics

Current dataset includes:

- **520 total graphs** across three size categories
  - **455 trees** across 7 different types with varying structural properties
  - **65 grids** with regular 2D lattice structures
- **100% validation success rate** for connectivity and structural properties
- **Comprehensive annotations** for algorithm development and analysis
- **Reproducible generation** using seeded random number generation

The dataset provides a robust foundation for empirical analysis of mutual visibility algorithms on both tree and grid graph structures.
