from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


@dataclass
class Block:
    start: int
    size: int
    owner: Optional[str] = None  # None indicates a free hole

    @property
    def is_free(self) -> bool:
        return self.owner is None

    @property
    def end(self) -> int:
        return self.start + self.size

    def clone(self) -> Block:
        return Block(start=self.start, size=self.size, owner=self.owner)


@dataclass
class AllocationMetrics:
    total_memory: int
    allocated_memory: int
    free_memory: int
    utilization: float
    external_fragmentation: float
    largest_hole: int
    num_holes: int
    requests_satisfied: int
    requests_failed: int
    failure_rate: float


@dataclass
class AllocationEvent:
    step: int
    action: str  # 'ALLOCATE', 'FREE', 'INIT', 'FAIL'
    pid: Optional[str]
    size: Optional[int]
    strategy: str
    success: bool
    message: str
    blocks: List[Block] = field(default_factory=list)
    metrics: Optional[AllocationMetrics] = None
