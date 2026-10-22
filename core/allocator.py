from __future__ import annotations
from typing import List, Optional, Tuple, Dict, Any
from core.models import Block, AllocationMetrics, AllocationEvent


class MemoryAllocator:
    """
    Simulates dynamic memory partitioning with First-Fit, Best-Fit,
    Worst-Fit, and Next-Fit allocation strategies, hole merging on free,
    and step-by-step event recording.
    """

    def __init__(self, total_size: int, strategy: str = "first_fit", record_events: bool = True):
        self.total_size = total_size
        self.strategy = strategy.lower().replace("-", "_")
        self.record_events = record_events
        self.blocks: List[Block] = [Block(start=0, size=total_size, owner=None)]
        self.last_alloc_address: int = 0
        self.events: List[AllocationEvent] = []
        self.step_counter: int = 0
        self.satisfied_count: int = 0
        self.failed_count: int = 0

        self._record_event(
            action="INIT",
            pid=None,
            size=None,
            success=True,
            message=f"Initialized {total_size} KB memory with strategy {self.strategy.replace('_', ' ').title()}"
        )

    @classmethod
    def from_blocks(cls, blocks: List[Block], strategy: str = "first_fit", record_events: bool = True) -> MemoryAllocator:
        """Initialize allocator with a predefined block layout."""
        total_size = sum(b.size for b in blocks)
        allocator = cls.__new__(cls)
        allocator.total_size = total_size
        allocator.strategy = strategy.lower().replace("-", "_")
        allocator.record_events = record_events
        allocator.blocks = [b.clone() for b in blocks]
        allocator.last_alloc_address = 0
        allocator.events = []
        allocator.step_counter = 0
        allocator.satisfied_count = 0
        allocator.failed_count = 0

        allocator._record_event(
            action="INIT",
            pid=None,
            size=None,
            success=True,
            message=f"Initialized custom block layout ({total_size} KB) with strategy {allocator.strategy.replace('_', ' ').title()}"
        )
        return allocator

    @property
    def metrics(self) -> AllocationMetrics:
        allocated = sum(b.size for b in self.blocks if not b.is_free)
        free_blocks = [b for b in self.blocks if b.is_free]
        total_free = sum(b.size for b in free_blocks)
        largest_hole = max((b.size for b in free_blocks), default=0)
        num_holes = len(free_blocks)

        utilization = allocated / self.total_size if self.total_size > 0 else 0.0
        ext_frag = (1.0 - (largest_hole / total_free)) if total_free > 0 else 0.0
        total_requests = self.satisfied_count + self.failed_count
        failure_rate = (self.failed_count / total_requests) if total_requests > 0 else 0.0

        return AllocationMetrics(
            total_memory=self.total_size,
            allocated_memory=allocated,
            free_memory=total_free,
            utilization=round(utilization, 4),
            external_fragmentation=round(ext_frag, 4),
            largest_hole=largest_hole,
            num_holes=num_holes,
            requests_satisfied=self.satisfied_count,
            requests_failed=self.failed_count,
            failure_rate=round(failure_rate, 4)
        )

    def _record_event(
        self,
        action: str,
        pid: Optional[str],
        size: Optional[int],
        success: bool,
        message: str
    ) -> AllocationEvent:
        self.step_counter += 1
        if not self.record_events:
            return AllocationEvent(
                step=self.step_counter,
                action=action,
                pid=pid,
                size=size,
                strategy=self.strategy,
                success=success,
                message=message,
                blocks=[],
                metrics=None
            )
        snapshot = [b.clone() for b in self.blocks]
        event = AllocationEvent(
            step=self.step_counter,
            action=action,
            pid=pid,
            size=size,
            strategy=self.strategy,
            success=success,
            message=message,
            blocks=snapshot,
            metrics=self.metrics
        )
        self.events.append(event)
        return event

    def _find_hole_index(self, size: int) -> Optional[int]:
        """Find the index in self.blocks of the hole to allocate into."""
        candidate_indices = [
            i for i, b in enumerate(self.blocks)
            if b.is_free and b.size >= size
        ]

        if not candidate_indices:
            return None

        if self.strategy in ("first", "first_fit"):
            return candidate_indices[0]

        elif self.strategy in ("best", "best_fit"):
            # Smallest hole that satisfies size
            return min(candidate_indices, key=lambda i: self.blocks[i].size)

        elif self.strategy in ("worst", "worst_fit"):
            # Largest hole that satisfies size
            return max(candidate_indices, key=lambda i: self.blocks[i].size)

        elif self.strategy in ("next", "next_fit"):
            # Scan starting from last_alloc_address circularly
            # First partition candidates into [>= last_alloc_address] and [< last_alloc_address]
            after = [i for i in candidate_indices if self.blocks[i].start >= self.last_alloc_address]
            before = [i for i in candidate_indices if self.blocks[i].start < self.last_alloc_address]
            ordered = after + before
            return ordered[0] if ordered else None

        else:
            raise ValueError(f"Unknown allocation strategy: {self.strategy}")

    def allocate(self, size: int, pid: str) -> Optional[Block]:
        """
        Allocate memory of given size to process pid.
        Splits chosen hole if size < hole.size.
        """
        if size <= 0:
            self.failed_count += 1
            self._record_event(
                action="FAIL",
                pid=pid,
                size=size,
                success=False,
                message=f"Allocation rejected: invalid size {size} KB requested for {pid}"
            )
            return None

        if size > self.total_size:
            self.failed_count += 1
            self._record_event(
                action="FAIL",
                pid=pid,
                size=size,
                success=False,
                message=f"Allocation failed: request {size} KB exceeds total memory ({self.total_size} KB)"
            )
            return None

        if any(not b.is_free and b.owner == pid for b in self.blocks):
            self.failed_count += 1
            self._record_event(
                action="FAIL",
                pid=pid,
                size=size,
                success=False,
                message=f"Allocation rejected: duplicate process ID '{pid}' already active in memory"
            )
            return None

        hole_idx = self._find_hole_index(size)
        if hole_idx is None:
            self.failed_count += 1
            self._record_event(
                action="FAIL",
                pid=pid,
                size=size,
                success=False,
                message=f"Allocation failed: no suitable hole found for {pid} ({size} KB)"
            )
            return None

        hole = self.blocks[hole_idx]
        allocated_block = Block(start=hole.start, size=size, owner=pid)

        if hole.size == size:
            # Exact fit: replace hole with allocated block
            self.blocks[hole_idx] = allocated_block
        else:
            # Split hole: allocated block followed by remaining hole
            remainder_hole = Block(
                start=hole.start + size,
                size=hole.size - size,
                owner=None
            )
            self.blocks[hole_idx] = allocated_block
            self.blocks.insert(hole_idx + 1, remainder_hole)

        self.last_alloc_address = allocated_block.end
        self.satisfied_count += 1

        self._record_event(
            action="ALLOCATE",
            pid=pid,
            size=size,
            success=True,
            message=f"Allocated {size} KB at address {allocated_block.start} to {pid}"
        )
        return allocated_block

    def free(self, pid: str) -> bool:
        """
        Free all blocks owned by pid and coalesce adjacent holes.
        """
        found = False
        for b in self.blocks:
            if b.owner == pid:
                b.owner = None
                found = True

        if not found:
            self._record_event(
                action="FREE",
                pid=pid,
                size=None,
                success=False,
                message=f"Free failed: process {pid} not found"
            )
            return False

        self._merge_adjacent_holes()
        self._record_event(
            action="FREE",
            pid=pid,
            size=None,
            success=True,
            message=f"Freed memory for {pid} and merged adjacent holes"
        )
        return True

    def _merge_adjacent_holes(self) -> None:
        """Merge consecutive free holes in-place."""
        if not self.blocks:
            return

        merged: List[Block] = []
        for block in self.blocks:
            if not merged:
                merged.append(block.clone())
                continue

            last = merged[-1]
            if last.is_free and block.is_free:
                # Merge into previous hole
                last.size += block.size
            else:
                merged.append(block.clone())

        self.blocks = merged

        # Next-Fit pointer adjustment: snap to merged hole's start, reset to 0 if no hole at/after it
        if self.last_alloc_address >= self.total_size:
            self.last_alloc_address = 0
        else:
            # Check if pointer falls inside a free hole
            for b in self.blocks:
                if b.is_free and b.start <= self.last_alloc_address < b.end:
                    self.last_alloc_address = b.start
                    break
            # If no hole exists at or after last_alloc_address, reset to 0
            has_hole_ahead = any(b.is_free and b.start >= self.last_alloc_address for b in self.blocks)
            if not has_hole_ahead:
                self.last_alloc_address = 0

    def reset(self) -> None:
        """Reset allocator back to initial state."""
        self.blocks = [Block(start=0, size=self.total_size, owner=None)]
        self.last_alloc_address = 0
        self.events = []
        self.step_counter = 0
        self.satisfied_count = 0
        self.failed_count = 0
        self._record_event(
            action="INIT",
            pid=None,
            size=None,
            success=True,
            message=f"Reset allocator to single {self.total_size} KB hole"
        )
