"""Finite two-route transition graph and independent BFS oracle."""

from __future__ import annotations

from collections import deque

from pydantic import model_validator

from rci.claims.models import FrozenModel


class RouteEdge(FrozenModel):
    source: str
    target: str

    @model_validator(mode="after")
    def validate_edge(self) -> RouteEdge:
        if not self.source or not self.target:
            raise ValueError("route edge endpoints are required")
        return self


class RouteGraph(FrozenModel):
    id: str
    revision: str
    nodes: tuple[str, ...]
    edges: tuple[RouteEdge, ...]
    start: str
    goal: str
    closed_world: bool = True

    @model_validator(mode="after")
    def validate_graph(self) -> RouteGraph:
        node_set = set(self.nodes)
        if len(node_set) != len(self.nodes):
            raise ValueError("route graph nodes must be unique")
        if self.start not in node_set or self.goal not in node_set:
            raise ValueError("route start and goal must be declared nodes")
        if any(edge.source not in node_set or edge.target not in node_set for edge in self.edges):
            raise ValueError("route edges must connect declared nodes")
        edge_keys = [(edge.source, edge.target) for edge in self.edges]
        if len(set(edge_keys)) != len(edge_keys):
            raise ValueError("route graph edges must be unique")
        return self


class RouteDemonstration(FrozenModel):
    graph: RouteGraph
    proposed_prerequisite: str
    routes: tuple[tuple[str, ...], ...]
    maximal_executions: tuple[tuple[str, ...], ...]
    bypass_route: tuple[str, ...] | None
    may_reach: bool
    must_reach: bool
    must_pass_prerequisite: bool
    control_promoted: bool = False

    @property
    def expected_findings_hold(self) -> bool:
        return (
            self.may_reach
            and not self.must_reach
            and not self.must_pass_prerequisite
            and not self.control_promoted
            and self.bypass_route is not None
            and self.proposed_prerequisite not in self.bypass_route
        )


def reference_route_graph() -> RouteGraph:
    return RouteGraph(
        id="two-route-transition-graph",
        revision="1",
        nodes=("bypass", "dead_end", "gate", "start", "target"),
        edges=(
            RouteEdge(source="bypass", target="dead_end"),
            RouteEdge(source="bypass", target="target"),
            RouteEdge(source="gate", target="target"),
            RouteEdge(source="start", target="bypass"),
            RouteEdge(source="start", target="gate"),
        ),
        start="start",
        goal="target",
    )


def enumerate_simple_routes(graph: RouteGraph) -> tuple[tuple[str, ...], ...]:
    adjacency: dict[str, list[str]] = {node: [] for node in graph.nodes}
    for edge in graph.edges:
        adjacency[edge.source].append(edge.target)
    for successors in adjacency.values():
        successors.sort()
    queue: deque[tuple[str, ...]] = deque(((graph.start,),))
    routes: list[tuple[str, ...]] = []
    while queue:
        path = queue.popleft()
        tail = path[-1]
        if tail == graph.goal:
            routes.append(path)
            continue
        for successor in adjacency[tail]:
            if successor not in path:
                queue.append((*path, successor))
    return tuple(routes)


def enumerate_maximal_executions(graph: RouteGraph) -> tuple[tuple[str, ...], ...]:
    """Enumerate every finite maximal acyclic execution, including failed branches."""

    adjacency: dict[str, list[str]] = {node: [] for node in graph.nodes}
    for edge in graph.edges:
        adjacency[edge.source].append(edge.target)
    for successors in adjacency.values():
        successors.sort()
    queue: deque[tuple[str, ...]] = deque(((graph.start,),))
    maximal: list[tuple[str, ...]] = []
    while queue:
        path = queue.popleft()
        successors = [node for node in adjacency[path[-1]] if node not in path]
        if not successors:
            maximal.append(path)
            continue
        queue.extend((*path, successor) for successor in successors)
    return tuple(maximal)


def route_demonstration() -> RouteDemonstration:
    graph = reference_route_graph()
    prerequisite = "gate"
    routes = enumerate_simple_routes(graph)
    maximal_executions = enumerate_maximal_executions(graph)
    bypass = next((route for route in routes if prerequisite not in route), None)
    return RouteDemonstration(
        graph=graph,
        proposed_prerequisite=prerequisite,
        routes=routes,
        maximal_executions=maximal_executions,
        bypass_route=bypass,
        may_reach=bool(routes),
        must_reach=bool(maximal_executions)
        and all(execution[-1] == graph.goal for execution in maximal_executions),
        must_pass_prerequisite=bool(routes) and all(prerequisite in route for route in routes),
    )
