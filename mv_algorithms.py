import networkx as nx
import numpy as np
from collections import deque
import matplotlib.pyplot as plt
import random

def bfs_mv(G, P, v, t):
    """
    Procedure BFS_MV as described in Figure 3 of Di Stefano's paper.
    Calculates distances from a starting vertex v to all other vertices,
    and specifically to points in P.
    
    Parameters:
    - G (networkx.Graph): The connected graph.
    - P (set): A set of "points" (vertices) in the graph.
    - v (node): The starting vertex for BFS.
    - t (bool): If True, distances are calculated in G.
                If False, distances are calculated in G excluding other points in P (P \ {u,v}).
                
    Returns:
    - dict: DP (distance to points in P), where DP[p] is the distance from v to p.
    """
    
    D = {node: float('inf') for node in G.nodes()}
    DP = {p_node: float('inf') for p_node in P}

    D[v] = 0
    if v in P:
        DP[v] = 0

    Q = deque()
    Q.append(v)

    while Q:
        u = Q.popleft()

        for w in G.neighbors(u):
            if D[w] == float('inf'):
                D[w] = D[u] + 1
                if w in P:
                    DP[w] = D[w]
                if t or w not in P:
                    Q.append(w)
    
    return DP

def mv(G, P):
    """
    Procedure MV as described in Figure 4 of Di Stefano's paper.
    Checks if a given set P is a mutual-visibility set in graph G.
    
    Parameters:
    - G (networkx.Graph): The undirected graph.
    - P (set): The set of "points" (vertices) to check for mutual visibility.
    
    Returns:
    - bool: True if P is a mutual-visibility set, False otherwise.
    """
    
    if not P or len(P) == 1:
        return True

    first_point = next(iter(P)) 
    connected_component_of_first_point = None
    
    for component in nx.connected_components(G):
        if first_point in component:
            connected_component_of_first_point = component
            break
            
    if connected_component_of_first_point is None: 
        return False 
        
    for point in P:
        if point not in connected_component_of_first_point:
            return False 


    H = G.subgraph(connected_component_of_first_point)
    for p in P:
       
        distances_in_H = bfs_mv(H, P, p, True)
        distances_in_H_minus_p = bfs_mv(H, P, p, False)
        if distances_in_H != distances_in_H_minus_p:
            return False

    
    return True



def greedy_mutual_visibility(G):
    """
    Greedy algorithm to find a large mutual-visibility set.
    """
    S = set()
    V_sorted = sorted(G.nodes, key=lambda v: G.degree[v], reverse=True)
    for v in V_sorted:
        S_candidate = S | {v}
        if mv(G, S_candidate):
            S = S_candidate
    return S


def get_one_shortest_path_and_internal_vertices(graph, source, target):
    """
    Finds one shortest path between source and target and returns its internal vertices.
    Returns an empty list if source == target or no path exists.
    """
    if source == target:
        return []

    try:
        path = nx.shortest_path(graph, source, target)
    except nx.NetworkXNoPath:
        return [] 

    if len(path) <= 2:
        return []
    else:
        return path[1:-1]


import itertools

def build_mv_hypergraph(graph):
    H_hyperedges = []

    for u, v in itertools.combinations(graph.nodes, 2):
        internal_vertices = get_one_shortest_path_and_internal_vertices(graph, u, v)

        for x in internal_vertices:
            hyperedge = frozenset({u, v, x}) 
            H_hyperedges.append(hyperedge)

    return list(set(H_hyperedges))

def k_independent_set(nodes, hyperedges, k=1):
    """
    Simplified greedy deletion algorithm to find a k-independent set in a hypergraph.
    This version iteratively removes the node with the current highest degree
    until all remaining nodes have a degree less than 'k'.
    
    For the Mutual Visibility problem, k should be 1 (meaning degree < 1, i.e., degree 0).
    
    Parameters:
    - nodes (list): All vertices in the hypergraph (initial set).
    - hyperedges (list): List of frozensets, where each frozenset is a hyperedge.
    - k (int): The k-independence parameter. Nodes in the final set must have degree < k.
               (e.g., k=1 for a standard independent set).
               
    Returns:
    - set: The k-independent set found.
    """
    
    current_nodes = set(nodes) 
    remaining_hyperedges = list(hyperedges) 

    while True: 
        node_degrees = {node: 0 for node in current_nodes}
        for h_edge in remaining_hyperedges:
            for node in h_edge:
                if node in current_nodes: 
                    node_degrees[node] += 1
        
        max_degree_node = None
        max_degree = -1
        
        for node in current_nodes:
            current_node_degree = node_degrees[node]
            if current_node_degree > max_degree:
                max_degree = current_node_degree
                max_degree_node = node
        
        if max_degree < k:
            break 

        current_nodes.remove(max_degree_node)
        
        hyperedges_to_remove_in_this_iteration = []
        for h_edge in remaining_hyperedges:
            if max_degree_node in h_edge:
                hyperedges_to_remove_in_this_iteration.append(h_edge)
        
        for h_edge in hyperedges_to_remove_in_this_iteration:
            remaining_hyperedges.remove(h_edge)
            
    return current_nodes

def greedy_hypergraph_independent_set(nodes, hyperedges):
    """
    Greedy algorithm for hypergraph independent set.
    Selects min-degree node, adds to IS, removes node and all nodes from its *incident hyperedges*
    (as they are now "covered" by the selected node).
    """
    current_nodes = set(nodes)
    independent_set = set()
    
    remaining_hyperedges = list(hyperedges) 

    while current_nodes:
        
        node_degrees = {node: 0 for node in current_nodes}
        for h_edge in remaining_hyperedges:
            for node in h_edge:
                if node in current_nodes: 
                    node_degrees[node] += 1 

        min_degree_node = None
        min_degree = float('inf')
        for node in current_nodes:
            current_node_degree = node_degrees.get(node, 0) 
            if current_node_degree < min_degree:
                min_degree = current_node_degree
                min_degree_node = node
        
        if min_degree_node is None: 
            break

        independent_set.add(min_degree_node)
        
        nodes_to_remove_from_consideration = {min_degree_node}
        
        hyperedges_to_remove_in_this_iteration = []

        for h_edge in remaining_hyperedges:
            if min_degree_node in h_edge:
                nodes_to_remove_from_consideration.update(h_edge) 
                hyperedges_to_remove_in_this_iteration.append(h_edge)
        
        for node in nodes_to_remove_from_consideration:
            if node in current_nodes: 
                current_nodes.remove(node)
        
        for h_edge in hyperedges_to_remove_in_this_iteration:
            if h_edge in remaining_hyperedges: 
                remaining_hyperedges.remove(h_edge)

    return independent_set

def brute_force_mutual_visibility(G):
    """
    Brute force algorithm to find the largest mutual-visibility set.
    """
    nodes = list(G.nodes())
    n = len(nodes)
    max_mv_set = set()
    for r in range(n, -1, -1):
        for subset_nodes_tuple in itertools.combinations(nodes, r):
            current_subset = set(subset_nodes_tuple)
            
            if len(current_subset) <= len(max_mv_set):
                break 
            
            if mv(G, current_subset):
                max_mv_set = current_subset

    return max_mv_set


def _count_mv_violations(G, P):
    """
    Helper function for the GA fitness calculation.
    Counts the number of pairs in P that violate the mutual-visibility condition
    """
    if len(P) < 2:
        return 0

    P_nodes = list(P)

    # We're assuming G is connected
    violating_pairs = set()

    for p in P_nodes:
        distances_in_G = bfs_mv(G, P, p, True)
        distances_in_G_minus_p = bfs_mv(G, P, p, False)

        for q in P_nodes:
            if p == q:
                continue

            dist_normal = distances_in_G.get(q, float('inf'))
            dist_restricted = distances_in_G_minus_p.get(q, float('inf'))

            # If the normal distance is shorter, the path was blocked by another P-node.
            if dist_normal < dist_restricted:
                violating_pairs.add(frozenset({p, q}))

    return len(violating_pairs)


def ga_mutual_visibility(G, n_p=50, maxit=100, penalty_multiplier=10):
    """
    Finds a large mutual-visibility set in graph G using a Genetic Algorithm.
    The algorithm is adapted from the one for the General Position Problem. 

    Parameters:
    - G (networkx.Graph): The input graph.
    - n_p (int): The size of the population. 
    - maxit (int): The maximum number of iterations (generations). 
    - penalty_multiplier (int): The constant M for the fitness penalty. 
    
    Returns:
    - set: The largest valid mutual-visibility set found by the algorithm.
    """
    
    nodes = list(G.nodes())
    node_to_idx = {node: i for i, node in enumerate(nodes)}
    n = len(nodes)
    
  
    population = [np.random.randint(0, 2, n) for _ in range(n_p)]
    
    best_solution_ever = set()
    best_fitness_ever = -float('inf')

    fitness_cache = {}

    def get_fitness(chromosome_tuple):
        nonlocal best_solution_ever
        
        if chromosome_tuple in fitness_cache:
            return fitness_cache[chromosome_tuple]
        
        chromosome = np.array(chromosome_tuple)
        S = {nodes[i] for i, bit in enumerate(chromosome) if bit == 1}
        num_selected = len(S)
        num_violations = _count_mv_violations(G, S)
        
        fitness = num_selected - penalty_multiplier * num_violations
        fitness_cache[chromosome_tuple] = fitness

        if num_violations == 0 and num_selected > len(best_solution_ever):
            best_solution_ever = S
            
        return fitness

    for _ in range(maxit):
        pop_with_fitness = [(get_fitness(tuple(chromo)), chromo) for chromo in population]
        
        pop_with_fitness.sort(key=lambda x: x[0], reverse=True)
        population = [chromo for fitness, chromo in pop_with_fitness]

        next_gen_candidates = population[:n_p // 2]
        
        while len(next_gen_candidates) < n_p:
            parent1, parent2 = random.choices(population, k=2)
            
            offspring = np.logical_or(parent1, parent2).astype(int)
            
            idx1, idx2 = random.sample(range(n), 2)
            offspring[idx1], offspring[idx2] = offspring[idx2], offspring[idx1]
            
            next_gen_candidates.append(offspring)
            
        population = next_gen_candidates

    final_fitness = get_fitness(tuple(np.array([1 if n in best_solution_ever else 0 for n in nodes])))
    
    if not best_solution_ever:
        best_chromo_final = population[0]
        return {nodes[i] for i, bit in enumerate(best_chromo_final) if bit == 1}

    return best_solution_ever

def forward(G : nx.Graph, run_brute_force=True, draw_graph=False):
    print("Graph: ", G.nodes())
    
    greedy_mv_set = greedy_mutual_visibility(G)
    hypergraph_edges = build_mv_hypergraph(G)
    
    greedy_hypergraph_set = greedy_hypergraph_independent_set(G.nodes, hypergraph_edges)
    greedy_k_set = k_independent_set(G.nodes, hypergraph_edges)
    genetic_set = ga_mutual_visibility(G)


    brute_force_mv_set = set()
    if run_brute_force:
        brute_force_mv_set = brute_force_mutual_visibility(G) 
    else:
        print(" (Brute Force skipped for this graph size)")
    if not mv(G, greedy_mv_set):
        print("Greedy MV Set is not a mutual-visibility set")
    if not mv(G, greedy_hypergraph_set):
        print("Greedy Hypergraph Set is not a mutual-visibility set")
    if not mv(G, greedy_k_set):
        print("Greedy K Set is not a mutual-visibility set")
    if not mv(G, genetic_set):
        print("Genetic set is not a mutual-visibility set")

    print(f"Greedy MV Set: {greedy_mv_set}")
    print(f"Greedy Hypergraph Set: {greedy_hypergraph_set}")
    print(f"Greedy K Set: {greedy_k_set}")
    print(f"Genetic Set: {genetic_set}")
    print(f"Brute Force MV Set: {brute_force_mv_set}")

    # Plot the graph with MV set nodes colored red
    if draw_graph:
        plt.figure(figsize=(10, 8))
        
        # Create node color list: red for nodes in MV set, lightblue for others
        node_colors = []
        for node in G.nodes():
            if node in greedy_mv_set:
                node_colors.append('red')
            else:
                node_colors.append('lightblue')
        
        pos = nx.spring_layout(G)
        nx.draw(G, pos, with_labels=True, node_color=node_colors, edge_color='gray', 
                node_size=700, font_size=10, font_weight='bold')
        
        # Add legend
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor='red', label='Mutual Visibility Set'),
            Patch(facecolor='lightblue', label='Other Nodes')
        ]
        plt.legend(handles=legend_elements, loc='upper right')
        
        plt.title(f"{G.name if G.name else 'Graph'} - Mutual Visibility Set (Red Nodes)")
        plt.show(block=False)


def main():

    G_petersen = nx.petersen_graph()
    G_petersen.name = "Petersen Graph"

    forward(G_petersen, draw_graph=True)

    input("\nAll computations are finished. Press Enter to exit and close all plots...")

if __name__ == "__main__":
    main()

