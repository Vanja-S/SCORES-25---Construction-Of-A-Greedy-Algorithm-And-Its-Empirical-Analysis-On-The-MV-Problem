def test_comprehensive():
    print("\nComprehensive Testing of Mutual Visibility on Various Graphs:")
    
    # 1. Small Graphs
    print("\n1. Small Graphs:")
    # Path graph
    G_path = nx.path_graph(5)
    S_path = greedy_mutual_visibility(G_path)
    print(f"Path graph (5 nodes): mutual-visibility set: {S_path}")
    
    # Star graph
    G_star = nx.star_graph(4)
    S_star = greedy_mutual_visibility(G_star)
    print(f"Star graph (5 nodes): mutual-visibility set: {S_star}")
    
    # Wheel graph
    G_wheel = nx.wheel_graph(6)
    S_wheel = greedy_mutual_visibility(G_wheel)
    print(f"Wheel graph (6 nodes): mutual-visibility set: {S_wheel}")

    # 2. Medium Graphs
    print("\n2. Medium Graphs:")
    # Complete bipartite
    G_bipartite = nx.complete_bipartite_graph(4, 4)
    S_bipartite = greedy_mutual_visibility(G_bipartite)
    print(f"Complete bipartite (8 nodes): mutual-visibility set: {S_bipartite}")
    
    # Grid graph
    G_grid = nx.grid_2d_graph(4, 4)
    S_grid = greedy_mutual_visibility(G_grid)
    print(f"4x4 grid graph: mutual-visibility set: {S_grid}")
    
    # Random regular graph
    G_regular = nx.random_regular_graph(3, 10, seed=42)
    S_regular = greedy_mutual_visibility(G_regular)
    print(f"Random 3-regular graph (10 nodes): mutual-visibility set: {S_regular}")

    # 3. Large Graphs
    print("\n3. Large Graphs:")
    # Large cycle
    G_large_cycle = nx.cycle_graph(20)
    S_large_cycle = greedy_mutual_visibility(G_large_cycle)
    print(f"Large cycle (20 nodes): mutual-visibility set size: {len(S_large_cycle)}")
    
    # Large complete graph
    G_large_complete = nx.complete_graph(15)
    S_large_complete = greedy_mutual_visibility(G_large_complete)
    print(f"Large complete graph (15 nodes): mutual-visibility set size: {len(S_large_complete)}")
    
    # Large grid
    G_large_grid = nx.grid_2d_graph(5, 5)
    S_large_grid = greedy_mutual_visibility(G_large_grid)
    print(f"5x5 grid graph: mutual-visibility set size: {len(S_large_grid)}")

    # 4. Special Graphs
    print("\n4. Special Graphs:")
    # Petersen graph
    G_petersen = nx.petersen_graph()
    S_petersen = greedy_mutual_visibility(G_petersen)
    print(f"Petersen graph: mutual-visibility set: {S_petersen}")
    
    # Random graph with high density
    G_dense = nx.dense_gnm_random_graph(100, 400, seed=42)
    S_dense = greedy_mutual_visibility(G_dense)
    print(f"Dense random graph (12 nodes, 40 edges): mutual-visibility set size: {len(S_dense)}")
    
    # Random graph with low density
    G_sparse = nx.dense_gnm_random_graph(12, 15, seed=42)
    S_sparse = greedy_mutual_visibility(G_sparse)
    print(f"Sparse random graph (12 nodes, 15 edges): mutual-visibility set size: {len(S_sparse)}")

    # 5. Performance Test
    print("\n5. Performance Test:")
    # Very large cycle
    G_very_large = nx.cycle_graph(50)
    S_very_large = greedy_mutual_visibility(G_very_large)
    print(f"Very large cycle (50 nodes): mutual-visibility set size: {len(S_very_large)}")