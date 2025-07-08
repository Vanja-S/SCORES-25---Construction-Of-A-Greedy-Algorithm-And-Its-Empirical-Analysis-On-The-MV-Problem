# Construction Of A Greedy Algorithm And Its Empirical Analysis On The MV Problem

Research paper submitted to the conference SCORES 25, in the field of graph theory, tackling the mutual-visibility problem. Co-authored with Bor Pangeršič.

## Dataset

This project includes graph datasets for testing mutual visibility algorithms across multiple graph families and sizes.

### Dataset Structure

```text
datasets/
├── n10/                         # Graphs with ~10 nodes
│   ├── trees/                   # Tree graphs (77 instances)
│   ├── complete/                # Complete graphs (15 instances)
│   ├── erdos_renyi/             # Erdős–Rényi random graphs (60 instances)
│   ├── grids/                   # Grid graphs (15 instances)
│   ├── mycielskian/             # Mycielskian graphs (5 instances)
│   └── petersen/                # Petersen-like graphs (5 instances)
├── n100/                        # Graphs with ~100 nodes
│   ├── trees/                   # Tree graphs (102 instances)
│   ├── complete/                # Complete graphs (15 instances)
│   ├── erdos_renyi/             # Erdős–Rényi random graphs (60 instances)
│   ├── grids/                   # Grid graphs (15 instances)
│   ├── mycielskian/             # Mycielskian graphs (5 instances)
│   └── petersen/                # Petersen-like graphs (5 instances)
└── n1000/                       # Graphs with ~1000 nodes
    ├── trees/                   # Tree graphs
    ├── erdos_renyi/             # Erdős–Rényi random graphs
    ├── grids/                   # Grid graphs
    └── petersen/                # Petersen-like graphs
```

### Graph Types

- **Trees**: 7 types (random, star, path, balanced, caterpillar, binary, spider)
  - Star and path trees: 1 instance per size (isomorphic)
  - Other types: 15-20 instances per size
- **Complete Graphs**: Cliques K_n
- **Erdős–Rényi Graphs**: Random graphs with varying edge probabilities
- **Grid Graphs**: 2D lattice structures P_n × P_m
- **Mycielskian Graphs**: Triangle-free graphs with high chromatic number
- **Petersen Graphs**: Generalized Petersen graph family

### Generation

Generate datasets using:

```bash
cd dataset_generators
python trees.py        # Tree graphs
python complete_graphs.py  # Complete graphs
python erdos.py        # Erdős–Rényi graphs
python grids.py        # Grid graphs
python mycelskian.py   # Mycielskian graphs
python petersen.py     # Petersen graphs
```

### Verification

Verify dataset integrity:

```bash
cd dataset_generators
python <generator>.py --verify
```

### File Format

- **Graphs**: GML format with embedded metadata
- **Metadata**: JSON files with graph properties and statistics

## Testing The Algoritms

All the algorithms described in the paper are available in the `mv_algorithms.py` script. To test them against the dataset, run;

```bash
python comprehensive_test.py
```

Which will output the `experiment_results.json`. If the JSON already exists, the analysis can be done in the `analysis.ipynb` file.
