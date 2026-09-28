from __future__ import annotations

import random
from collections import defaultdict, deque
from typing import Callable, Iterable


class DiGraph:
    def __init__(self) -> None:
        self.nodes: set[str] = set()
        self.adj: dict[str, dict[str, float]] = defaultdict(dict)
        self.rev: dict[str, dict[str, float]] = defaultdict(dict)

    def add_node(self, node: str) -> None:
        self.nodes.add(node)

    def add_edge(self, src: str, dst: str, weight: float = 1.0) -> None:
        self.nodes.add(src)
        self.nodes.add(dst)
        self.adj[src][dst] = self.adj[src].get(dst, 0.0) + weight
        self.rev[dst][src] = self.rev[dst].get(src, 0.0) + weight

    def out_edges(self, node: str) -> dict[str, float]:
        return self.adj.get(node, {})

    def in_edges(self, node: str) -> dict[str, float]:
        return self.rev.get(node, {})

    def out_degree(self, node: str) -> int:
        return len(self.adj.get(node, {}))

    def in_degree(self, node: str) -> int:
        return len(self.rev.get(node, {}))

    def edges(self) -> Iterable[tuple[str, str, float]]:
        for src, targets in self.adj.items():
            for dst, weight in targets.items():
                yield src, dst, weight

    def undirected(self) -> dict[str, set[str]]:
        neighbors: dict[str, set[str]] = {node: set() for node in self.nodes}
        for src, dst, _ in self.edges():
            neighbors[src].add(dst)
            neighbors[dst].add(src)
        return neighbors

    def connected_components(self) -> list[set[str]]:
        neighbors = self.undirected()
        seen: set[str] = set()
        components: list[set[str]] = []
        for node in sorted(self.nodes):
            if node in seen:
                continue
            component: set[str] = set()
            queue = deque([node])
            seen.add(node)
            while queue:
                current = queue.popleft()
                component.add(current)
                for nxt in sorted(neighbors.get(current, ())):
                    if nxt not in seen:
                        seen.add(nxt)
                        queue.append(nxt)
            components.append(component)
        components.sort(key=len, reverse=True)
        return components

    def pagerank(self, damping: float = 0.85, iterations: int = 60, weight_key: bool = True) -> dict[str, float]:
        if not self.nodes:
            return {}
        n = len(self.nodes)
        rank = {node: 1.0 / n for node in self.nodes}
        total_out_weight: dict[str, float] = {}
        for src in self.nodes:
            total_out_weight[src] = sum(self.adj.get(src, {}).values()) or 0.0
        for _ in range(iterations):
            dangling = sum(rank[node] for node in self.nodes if total_out_weight.get(node, 0.0) == 0.0)
            nxt = {node: (1.0 - damping) / n + damping * dangling / n for node in self.nodes}
            for src in self.nodes:
                out = self.adj.get(src, {})
                total = total_out_weight.get(src, 0.0)
                if total <= 0:
                    continue
                share = damping * rank[src]
                for dst, weight in out.items():
                    nxt[dst] += share * (weight / total)
            rank = nxt
        return rank

    def betweenness(self) -> dict[str, float]:
        score = {node: 0.0 for node in self.nodes}
        undirected_edges = set()
        for src, dst, _ in self.edges():
            undirected_edges.add((src, dst) if src <= dst else (dst, src))
        neighbors: dict[str, list[str]] = defaultdict(list)
        for a, b in undirected_edges:
            neighbors[a].append(b)
            neighbors[b].append(a)
        for source in sorted(self.nodes):
            stack: list[str] = []
            preds: dict[str, list[str]] = defaultdict(list)
            sigma = {node: 0.0 for node in self.nodes}
            sigma[source] = 1.0
            dist = {node: -1 for node in self.nodes}
            dist[source] = 0
            queue = deque([source])
            while queue:
                current = queue.popleft()
                stack.append(current)
                for nxt in neighbors.get(current, []):
                    if dist[nxt] < 0:
                        dist[nxt] = dist[current] + 1
                        queue.append(nxt)
                    if dist[nxt] == dist[current] + 1:
                        sigma[nxt] += sigma[current]
                        preds[nxt].append(current)
            delta = {node: 0.0 for node in self.nodes}
            while stack:
                node = stack.pop()
                for pred in preds.get(node, []):
                    if sigma[node] > 0:
                        delta[pred] += (sigma[pred] / sigma[node]) * (1.0 + delta[node])
                if node != source:
                    score[node] += delta[node]
        if self.nodes:
            for node in score:
                score[node] /= 2.0
        return score

    def label_communities(self, seed: int = 7, rounds: int = 12) -> dict[str, int]:
        if not self.nodes:
            return {}
        rng = random.Random(seed)
        neighbors = self.undirected()
        labels = {node: idx for idx, node in enumerate(sorted(self.nodes))}
        nodes = sorted(self.nodes)
        for _ in range(rounds):
            changed = 0
            order = nodes[:]
            rng.shuffle(order)
            for node in order:
                counts: dict[int, int] = defaultdict(int)
                for nxt in neighbors.get(node, ()):
                    counts[labels[nxt]] += 1
                if not counts:
                    continue
                best = max(counts.values())
                candidates = sorted(label for label, count in counts.items() if count == best)
                new_label = candidates[0]
                if new_label != labels[node]:
                    labels[node] = new_label
                    changed += 1
            if changed == 0:
                break
        remap: dict[int, int] = {}
        out: dict[str, int] = {}
        for node in sorted(labels, key=lambda n: labels[n]):
            label = labels[node]
            if label not in remap:
                remap[label] = len(remap)
            out[node] = remap[label]
        return out

    def longest_chain(self, predicate: Callable[[str], bool]) -> list[str]:
        filtered = [node for node in self.nodes if predicate(node)]
        allowed = set(filtered)
        memo: dict[str, list[str]] = {}

        def dfs(node: str, visiting: frozenset[str]) -> list[str]:
            if node in memo:
                return memo[node]
            if node in visiting:
                return []
            best: list[str] = [node]
            for nxt in sorted(self.adj.get(node, [])):
                if nxt not in allowed:
                    continue
                candidate = dfs(nxt, visiting | {node})
                if len(candidate) + 1 > len(best):
                    best = [node] + candidate
            memo[node] = best
            return best

        best_chain: list[str] = []
        for node in sorted(allowed):
            chain = dfs(node, frozenset())
            if len(chain) > len(best_chain):
                best_chain = chain
        return best_chain


def money_flows(flows: Iterable[tuple[str, str, float]]) -> tuple[dict[str, float], dict[str, float]]:
    inflow: dict[str, float] = defaultdict(float)
    outflow: dict[str, float] = defaultdict(float)
    for src, dst, amount in flows:
        outflow[src] += amount
        inflow[dst] += amount
    return inflow, outflow


def hop_distance(graph: DiGraph, sources: set[str], max_hops: int = 8, reverse: bool = False) -> dict[str, int]:
    dist: dict[str, int] = {}
    queue: deque[tuple[str, int]] = deque()
    for node in sources:
        dist[node] = 0
        queue.append((node, 0))
    while queue:
        current, d = queue.popleft()
        if d >= max_hops:
            continue
        edges = graph.in_edges(current) if reverse else graph.out_edges(current)
        for nxt in edges:
            if nxt not in dist:
                dist[nxt] = d + 1
                queue.append((nxt, d + 1))
    return dist
