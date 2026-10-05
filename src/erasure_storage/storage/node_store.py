from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Set

from erasure_storage.coordinator.coordinator import FragmentRecord


@dataclass
class NodeState:
    node_id: int
    online: bool = True
    fragments: List[FragmentRecord] = field(default_factory=list)


class NodeStore:
    def __init__(self, node_count: int):
        self.node_count = node_count
        self.nodes: Dict[int, NodeState] = {node_id: NodeState(node_id=node_id) for node_id in range(node_count)}
        self.failed_nodes: Set[int] = set()

    def store_fragments(self, fragment_records: List[FragmentRecord]) -> None:
        for record in fragment_records:
            if record.node_id not in self.nodes:
                continue
            self.nodes[record.node_id].fragments.append(record)

    def fail_nodes(self, node_ids: List[int]) -> None:
        self.failed_nodes.update(node_ids)
        for node_id in node_ids:
            if node_id in self.nodes:
                self.nodes[node_id].online = False

    def recover_fragments(self, file_id: str) -> List[FragmentRecord]:
        recovered: List[FragmentRecord] = []
        for node in self.nodes.values():
            for fragment in node.fragments:
                if fragment.file_id == file_id and node.online:
                    recovered.append(fragment)
        return recovered
