"""Deterministic task decomposition with depth and DAG validation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import heapq
import json
import re
from typing import Mapping, Sequence


_ID_SANITIZER = re.compile(r"[^a-z0-9]+")
MAX_TASK_DEPTH = 2


class TaskGraphValidationCode(str, Enum):
    DEPTH_LIMIT_EXCEEDED = "DEPTH_LIMIT_EXCEEDED"
    MISSING_DEPENDENCY = "MISSING_DEPENDENCY"
    SELF_DEPENDENCY = "SELF_DEPENDENCY"
    DUPLICATE_NODE_ID = "DUPLICATE_NODE_ID"
    CYCLE_DETECTED = "CYCLE_DETECTED"


@dataclass(frozen=True, slots=True)
class TaskGraphValidationFailure:
    code: TaskGraphValidationCode
    message: str
    node_id: str | None = None
    detail: Mapping[str, object] | None = None

    def as_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {"code": self.code.value, "message": self.message}
        if self.node_id is not None:
            payload["node_id"] = self.node_id
        if self.detail is not None:
            payload["detail"] = dict(self.detail)
        return payload


class TaskGraphValidationError(ValueError):
    """Raised when decomposition input violates graph requirements."""

    def __init__(self, failure: TaskGraphValidationFailure) -> None:
        super().__init__(f"{failure.code.value}: {failure.message}")
        self.failure = failure


@dataclass(frozen=True, slots=True)
class TaskSpec:
    title: str
    node_id: str | None = None
    depends_on: tuple[str, ...] = ()
    subtasks: tuple["TaskSpec", ...] = ()
    constraint_keys: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class TaskNode:
    node_id: str
    title: str
    depth: int
    parent_id: str | None
    depends_on: tuple[str, ...]
    constraint_keys: tuple[str, ...]

    def as_payload(self) -> dict[str, object]:
        return {
            "node_id": self.node_id,
            "title": self.title,
            "depth": self.depth,
            "parent_id": self.parent_id,
            "depends_on": list(self.depends_on),
            "constraint_keys": list(self.constraint_keys),
        }


@dataclass(frozen=True, slots=True)
class TaskEdge:
    from_id: str
    to_id: str

    def as_payload(self) -> dict[str, str]:
        return {"from": self.from_id, "to": self.to_id}


@dataclass(frozen=True, slots=True)
class TaskGraph:
    nodes: tuple[TaskNode, ...]
    edges: tuple[TaskEdge, ...]

    def as_payload(self) -> dict[str, object]:
        return {
            "nodes": [node.as_payload() for node in self.nodes],
            "edges": [edge.as_payload() for edge in self.edges],
        }

    def to_json(self) -> str:
        return json.dumps(self.as_payload(), sort_keys=True, separators=(",", ":"))


TaskInput = TaskSpec | Mapping[str, object]


def build_task_graph(tasks: Sequence[TaskInput]) -> TaskGraph:
    """Build a deterministic dependency DAG from top-level tasks and subtasks."""
    normalized = _normalize_specs(tasks)
    node_rows: list[tuple[TaskNode, tuple[str, ...]]] = []
    seen_ids: set[str] = set()

    def _walk(
        specs: Sequence[TaskSpec],
        *,
        parent_id: str | None,
        depth: int,
    ) -> None:
        ordered_specs = _sort_specs(specs)
        for sibling_index, spec in enumerate(ordered_specs):
            node_id = _resolve_node_id(spec, parent_id=parent_id, sibling_index=sibling_index)
            if node_id in seen_ids:
                failure = TaskGraphValidationFailure(
                    code=TaskGraphValidationCode.DUPLICATE_NODE_ID,
                    message=f"Duplicate node id: {node_id}",
                    node_id=node_id,
                )
                raise TaskGraphValidationError(failure)
            if depth > MAX_TASK_DEPTH:
                failure = TaskGraphValidationFailure(
                    code=TaskGraphValidationCode.DEPTH_LIMIT_EXCEEDED,
                    message=f"Task depth {depth} exceeds max depth {MAX_TASK_DEPTH}.",
                    node_id=node_id,
                    detail={"depth": depth, "max_depth": MAX_TASK_DEPTH},
                )
                raise TaskGraphValidationError(failure)
            seen_ids.add(node_id)
            depends_on = tuple(sorted({_normalize_dependency(dep) for dep in spec.depends_on}))
            node_rows.append(
                (
                    TaskNode(
                        node_id=node_id,
                        title=spec.title.strip(),
                        depth=depth,
                        parent_id=parent_id,
                        depends_on=depends_on,
                        constraint_keys=tuple(sorted(spec.constraint_keys)),
                    ),
                    depends_on,
                )
            )
            if spec.subtasks:
                _walk(spec.subtasks, parent_id=node_id, depth=depth + 1)

    _walk(normalized, parent_id=None, depth=1)
    return _validate_and_sort(node_rows)


def _normalize_specs(tasks: Sequence[TaskInput]) -> tuple[TaskSpec, ...]:
    return tuple(_coerce_task_spec(task) for task in tasks)


def _coerce_task_spec(task: TaskInput) -> TaskSpec:
    if isinstance(task, TaskSpec):
        return task
    title = str(task.get("title", "")).strip()
    if title == "":
        raise TypeError("Task title is required and must be non-empty.")
    node_id = task.get("id")
    if node_id is not None:
        node_id = _normalize_dependency(str(node_id))
    depends_on = tuple(_normalize_dependency(str(dep)) for dep in task.get("depends_on", ()))
    constraint_keys = tuple(str(key).strip() for key in task.get("constraint_keys", ()) if str(key).strip())
    subtasks_raw = task.get("subtasks", ())
    if not isinstance(subtasks_raw, Sequence):
        raise TypeError("Task subtasks must be a sequence.")
    subtasks = tuple(_coerce_task_spec(subtask) for subtask in subtasks_raw)  # type: ignore[arg-type]
    return TaskSpec(
        title=title,
        node_id=node_id,
        depends_on=depends_on,
        subtasks=subtasks,
        constraint_keys=constraint_keys,
    )


def _sort_specs(specs: Sequence[TaskSpec]) -> tuple[TaskSpec, ...]:
    return tuple(
        sorted(
            specs,
            key=lambda spec: (
                spec.title.casefold(),
                spec.node_id or "",
                tuple(dep.casefold() for dep in spec.depends_on),
                tuple(key.casefold() for key in spec.constraint_keys),
            ),
        )
    )


def _resolve_node_id(spec: TaskSpec, *, parent_id: str | None, sibling_index: int) -> str:
    if spec.node_id is not None:
        return spec.node_id
    slug = _slugify(spec.title)
    local_id = f"{slug}-{sibling_index + 1:02d}"
    if parent_id is None:
        return local_id
    return f"{parent_id}.{local_id}"


def _normalize_dependency(raw: str) -> str:
    dependency = raw.strip()
    if dependency == "":
        raise TypeError("Dependency ids must be non-empty strings.")
    return dependency


def _slugify(raw: str) -> str:
    slug = _ID_SANITIZER.sub("-", raw.casefold()).strip("-")
    return slug or "task"


def _validate_and_sort(node_rows: Sequence[tuple[TaskNode, tuple[str, ...]]]) -> TaskGraph:
    node_by_id: dict[str, TaskNode] = {node.node_id: node for node, _ in node_rows}
    in_degree: dict[str, int] = {node.node_id: 0 for node, _ in node_rows}
    outgoing: dict[str, list[str]] = {node.node_id: [] for node, _ in node_rows}
    edges: set[tuple[str, str]] = set()

    for node, dependencies in node_rows:
        for dependency in dependencies:
            if dependency == node.node_id:
                failure = TaskGraphValidationFailure(
                    code=TaskGraphValidationCode.SELF_DEPENDENCY,
                    message=f"Task {node.node_id} depends on itself.",
                    node_id=node.node_id,
                )
                raise TaskGraphValidationError(failure)
            if dependency not in node_by_id:
                failure = TaskGraphValidationFailure(
                    code=TaskGraphValidationCode.MISSING_DEPENDENCY,
                    message=f"Task {node.node_id} references unknown dependency {dependency}.",
                    node_id=node.node_id,
                    detail={"dependency": dependency},
                )
                raise TaskGraphValidationError(failure)
            if (dependency, node.node_id) not in edges:
                edges.add((dependency, node.node_id))
                outgoing[dependency].append(node.node_id)
                in_degree[node.node_id] += 1

    for targets in outgoing.values():
        targets.sort()

    frontier: list[tuple[tuple[int, str, str], str]] = []
    for node_id, degree in in_degree.items():
        if degree == 0:
            node = node_by_id[node_id]
            heapq.heappush(frontier, ((_node_sort_key(node)), node_id))

    ordered_ids: list[str] = []
    while frontier:
        _, node_id = heapq.heappop(frontier)
        ordered_ids.append(node_id)
        for target_id in outgoing[node_id]:
            in_degree[target_id] -= 1
            if in_degree[target_id] == 0:
                node = node_by_id[target_id]
                heapq.heappush(frontier, ((_node_sort_key(node)), target_id))

    if len(ordered_ids) != len(node_rows):
        remaining = sorted(node_id for node_id, degree in in_degree.items() if degree > 0)
        failure = TaskGraphValidationFailure(
            code=TaskGraphValidationCode.CYCLE_DETECTED,
            message="Dependency cycle detected in task graph.",
            detail={"cycle_nodes": remaining},
        )
        raise TaskGraphValidationError(failure)

    ordered_nodes = tuple(node_by_id[node_id] for node_id in ordered_ids)
    ordered_edges = tuple(
        TaskEdge(from_id=source, to_id=target) for source, target in sorted(edges, key=lambda edge: (edge[0], edge[1]))
    )
    return TaskGraph(nodes=ordered_nodes, edges=ordered_edges)


def _node_sort_key(node: TaskNode) -> tuple[int, str, str]:
    return (node.depth, node.title.casefold(), node.node_id)


__all__ = [
    "MAX_TASK_DEPTH",
    "TaskEdge",
    "TaskGraph",
    "TaskGraphValidationCode",
    "TaskGraphValidationError",
    "TaskNode",
    "TaskSpec",
    "build_task_graph",
]

