from __future__ import annotations
import sys
from pathlib import Path

# Anchor repo root in sys.path for Streamlit Cloud and containerized runners
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import List, Dict, Any

from core.models import Block, AllocationMetrics
from core.allocator import MemoryAllocator
from core.scenarios import (
    run_worst_fit_scenario,
    run_all_strategies_for_preset,
    get_worst_fit_preset_blocks,
    PRESET_REQUESTS,
    SCENARIO_EXPLANATION,
    HONESTY_NOTE
)
from core.paging import (
    calculate_fixed_partitioning,
    calculate_paging_overhead,
    calculate_segmentation_overhead,
    get_comparison_matrix
)
from core.replacement import (
    simulate_replacement,
    simulate_fifo,
    simulate_lru,
    simulate_optimal,
    STANDARD_REF_STRING,
    BELADY_REF_STRING,
    run_belady_check
)
from core.benchmark import (
    run_benchmark_suite,
    get_worst_fit_counterexample
)
from components.visualizer import render_memory_bar_plotly, render_memory_bar_html
from components.metrics import display_metric_cards, apply_custom_styles

# Page configuration
st.set_page_config(
    page_title="MemLab — Memory Management Lab",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply minimal clean light styling
apply_custom_styles()

# ---------------------------------------------------------
# Sidebar Navigation & Information
# ---------------------------------------------------------
with st.sidebar:
    st.title("🧠 MemLab")
    st.caption("OS Memory Management Performance Lab")
    st.markdown("---")
    st.markdown("""
    **Module 4 Topics Covered:**
    1. Performance analysis of all memory management techniques.
    2. Design and proof of a scenario where **Worst-Fit** outperforms First, Best, and Next-fit.
    """)
    st.markdown("---")
    st.info("💡 **Tip:** Use the step sliders across tabs to replay memory states deterministically.")


# ---------------------------------------------------------
# App Tabs
# ---------------------------------------------------------
tab_alloc, tab_worst_fit, tab_techniques, tab_benchmark = st.tabs([
    "📐 Allocation Lab",
    "⭐ Worst-Fit Scenario",
    "📊 Techniques & Page Replacement",
    "🚀 Benchmark & Honesty"
])


# =========================================================
# TAB 1: ALLOCATION LAB (DYNAMIC PARTITIONING)
# =========================================================
with tab_alloc:
    st.header("Dynamic Partitioning Allocation Lab")
    st.write("Interactively allocate and free memory blocks, visualize real-time hole coalescing, and inspect event logs.")

    # Initialize session state for allocator
    if "allocator" not in st.session_state:
        st.session_state.allocator = MemoryAllocator(total_size=256, strategy="first_fit")

    # Top Control Bar
    ctrl_col1, ctrl_col2, ctrl_col3 = st.columns([2, 2, 2])
    with ctrl_col1:
        strategy_choice = st.selectbox(
            "Allocation Strategy",
            ["First-Fit", "Best-Fit", "Worst-Fit", "Next-Fit"],
            index=["first_fit", "best_fit", "worst_fit", "next_fit"].index(st.session_state.allocator.strategy)
            if st.session_state.allocator.strategy in ["first_fit", "best_fit", "worst_fit", "next_fit"] else 0,
            key="alloc_strategy_select"
        )
        strat_key = strategy_choice.lower().replace("-", "_")
        if strat_key != st.session_state.allocator.strategy:
            st.session_state.allocator.strategy = strat_key
            st.rerun()

    with ctrl_col2:
        new_total_mem = st.number_input(
            "Total Memory Size (KB)",
            min_value=64,
            max_value=2048,
            value=st.session_state.allocator.total_size,
            step=32,
            key="alloc_total_mem_input"
        )
        if new_total_mem != st.session_state.allocator.total_size:
            st.session_state.allocator = MemoryAllocator(total_size=new_total_mem, strategy=strat_key)
            st.session_state["alloc_step_slider"] = 1
            st.rerun()

    with ctrl_col3:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        if st.button("🔄 Reset Allocator", use_container_width=True, key="alloc_reset_btn"):
            st.session_state.allocator.reset()
            st.session_state["alloc_step_slider"] = 1
            st.rerun()

    st.markdown("---")

    # Allocation & Deallocation Operations
    op_col1, op_col2, op_col3 = st.columns([2, 2, 2])
    with op_col1:
        st.subheader("Allocate Memory")
        alloc_pid = st.text_input("Process ID", value=f"P{st.session_state.allocator.satisfied_count + 1}", key="alloc_pid_input")
        alloc_size = st.number_input("Request Size (KB)", min_value=1, max_value=st.session_state.allocator.total_size, value=40, step=10, key="alloc_size_input")
        if st.button("➕ Allocate Block", type="primary", use_container_width=True, key="alloc_submit_btn"):
            active_existing_pids = [b.owner for b in st.session_state.allocator.blocks if not b.is_free]
            if alloc_pid in active_existing_pids:
                st.warning(f"Process ID '{alloc_pid}' is already active in memory!")
            elif alloc_size > st.session_state.allocator.total_size:
                st.warning(f"Request size ({alloc_size} KB) exceeds total memory ({st.session_state.allocator.total_size} KB)!")
            st.session_state.allocator.allocate(size=alloc_size, pid=alloc_pid)
            st.session_state["alloc_step_slider"] = len(st.session_state.allocator.events)
            st.rerun()

    with op_col2:
        st.subheader("Free Memory")
        active_pids = sorted(list(set(b.owner for b in st.session_state.allocator.blocks if not b.is_free and b.owner != "OS_RESERVED")))
        if active_pids:
            free_pid = st.selectbox("Select Active Process to Free", active_pids, key="alloc_free_select")
            if st.button("🗑️ Free Block (Coalesce)", use_container_width=True, key="alloc_free_btn"):
                st.session_state.allocator.free(pid=free_pid)
                st.session_state["alloc_step_slider"] = len(st.session_state.allocator.events)
                st.rerun()
        else:
            st.info("No active user processes in memory to free.")

    with op_col3:
        st.subheader("Quick Presets")
        if st.button("⚡ Load Fragmented Pattern", use_container_width=True, key="alloc_preset_frag_btn"):
            st.session_state.allocator.reset()
            st.session_state.allocator.allocate(40, "P1")
            st.session_state.allocator.allocate(30, "P2")
            st.session_state.allocator.allocate(50, "P3")
            st.session_state.allocator.allocate(40, "P4")
            st.session_state.allocator.allocate(30, "P5")
            st.session_state.allocator.free("P2")
            st.session_state.allocator.free("P4")
            st.session_state["alloc_step_slider"] = len(st.session_state.allocator.events)
            st.rerun()

        if st.button("⚡ Fill Memory to Limit", use_container_width=True, key="alloc_preset_fill_btn"):
            st.session_state.allocator.reset()
            remaining = st.session_state.allocator.total_size
            idx = 1
            while remaining >= 30:
                chunk = min(50, remaining)
                st.session_state.allocator.allocate(chunk, f"P{idx}")
                remaining -= chunk
                idx += 1
            st.session_state["alloc_step_slider"] = len(st.session_state.allocator.events)
            st.rerun()

    st.markdown("---")

    # Step Replay Slider
    total_events = len(st.session_state.allocator.events)
    if "alloc_step_slider" in st.session_state:
        st.session_state["alloc_step_slider"] = min(max(1, st.session_state["alloc_step_slider"]), total_events)

    if total_events > 1:
        step_val = st.slider(
            "Replay Memory Event History (Step-by-Step)",
            min_value=1,
            max_value=total_events,
            value=min(max(1, st.session_state.get("alloc_step_slider", total_events)), total_events),
            key="alloc_step_slider",
            help="Drag to inspect memory layout and metrics at any previous operation."
        )
        step_idx = min(max(0, step_val - 1), total_events - 1)
    else:
        step_idx = 0

    current_event = st.session_state.allocator.events[step_idx]
    current_blocks = current_event.blocks
    current_metrics = current_event.metrics or st.session_state.allocator.metrics

    # Display Metrics
    display_metric_cards(current_metrics)

    # Event message badge
    status_color = "#166534" if current_event.success else "#991b1b"
    status_bg = "#dcfce7" if current_event.success else "#fee2e2"
    st.markdown(
        f"<div style='background-color: {status_bg}; color: {status_color}; padding: 8px 12px; border-radius: 6px; font-weight: 500; margin: 10px 0;'>"
        f"Step {current_event.step} ({current_event.action}): {current_event.message}"
        f"</div>",
        unsafe_allow_html=True
    )

    # Memory Visualizer Bar
    st.plotly_chart(
        render_memory_bar_plotly(current_blocks, st.session_state.allocator.total_size, title="Physical Memory Bar"),
        use_container_width=True,
        key="alloc_memory_bar_chart"
    )

    # Event Log Table
    with st.expander("📋 Detailed Event History Log", expanded=False):
        log_rows = []
        for ev in st.session_state.allocator.events:
            log_rows.append({
                "Step": ev.step,
                "Action": ev.action,
                "Process": ev.pid or "—",
                "Size (KB)": ev.size if ev.size is not None else "—",
                "Status": "✅ Success" if ev.success else "❌ Failed",
                "Details": ev.message
            })
        st.dataframe(pd.DataFrame(log_rows), use_container_width=True, hide_index=True)


# =========================================================
# TAB 2: WORST-FIT SCENARIO (QUESTION 2)
# =========================================================
with tab_worst_fit:
    st.header("⭐ Worst-Fit Superiority Scenario (Question 2)")
    st.markdown("""
    **Theoretical Question 2:** *Design a scenario showing that Worst-Fit may be a good algorithm for dynamic partitioning.*

    Below is the runnable scenario proving that **Worst-Fit succeeds on all 4 requests**, whereas **First-Fit, Best-Fit, and Next-Fit all fail the final request**.
    """)

    # Scenario parameters card
    st.markdown("""
    <div class="explanation-card">
        <b>Preset Configuration:</b><br>
        • Initial free holes: <b>100 KB</b> and <b>120 KB</b> (separated by an OS reserved block). Total free memory: <b>220 KB</b>.<br>
        • Sequence of allocation requests: <b>60 KB (P1)</b> &rarr; <b>50 KB (P2)</b> &rarr; <b>50 KB (P3)</b> &rarr; <b>50 KB (P4)</b>.<br>
        • Total requested memory: <b>210 KB</b> (less than total free memory of 220 KB).
    </div>
    """, unsafe_allow_html=True)

    # Run all strategies
    scenario_results = run_all_strategies_for_preset()

    # Step slider for scenario
    max_scenario_steps = 4  # 0: Init, 1: P1, 2: P2, 3: P3, 4: P4
    scenario_step = st.slider(
        "Interactive Step Slider",
        min_value=0,
        max_value=max_scenario_steps,
        value=max_scenario_steps,
        format="Step %d",
        key="wf_scenario_step_slider"
    )

    step_labels = [
        "Initial State: Holes [100 KB, 120 KB]",
        "Step 1: Request 60 KB (P1)",
        "Step 2: Request 50 KB (P2)",
        "Step 3: Request 50 KB (P3)",
        "Step 4: Request 50 KB (P4) — Critical Test!"
    ]
    st.caption(f"**Current Action:** {step_labels[scenario_step]}")

    # 4 Columns side-by-side
    col_ff, col_bf, col_wf, col_nf = st.columns(4)
    strategy_cols = [
        ("First-Fit", "first_fit", col_ff),
        ("Best-Fit", "best_fit", col_bf),
        ("Worst-Fit ⭐", "worst_fit", col_wf),
        ("Next-Fit", "next_fit", col_nf)
    ]

    for title, key, col in strategy_cols:
        alloc = scenario_results[key]
        event = alloc.events[scenario_step]
        blocks_at_step = event.blocks

        with col:
            st.subheader(title)
            # Status badge
            if scenario_step == 4:
                if key == "worst_fit":
                    st.markdown("<span class='badge-success'>✅ ALL 4 SATISFIED (100%)</span>", unsafe_allow_html=True)
                else:
                    st.markdown("<span class='badge-fail'>❌ P4 FAILED (75%)</span>", unsafe_allow_html=True)
            else:
                st.markdown("<span class='badge-success'>Processing...</span>", unsafe_allow_html=True)

            # Render HTML memory bar
            st.markdown(render_memory_bar_html(blocks_at_step, alloc.total_size), unsafe_allow_html=True)

            # Details at step
            free_holes = [b.size for b in blocks_at_step if b.is_free]
            st.markdown(f"**Remaining Holes:** `{free_holes}` KB")
            st.markdown(f"**Largest Hole:** `{max(free_holes, default=0)}` KB")
            st.markdown(f"**Step Status:** {event.message}")

    st.markdown("---")

    # Step-by-Step Decision Trace Table
    st.subheader("Step-by-Step Strategy Decision Matrix")
    matrix_rows = []
    req_labels = ["Init", "P1 (60 KB)", "P2 (50 KB)", "P3 (50 KB)", "P4 (50 KB)"]
    for s_idx in range(5):
        row = {"Step / Request": req_labels[s_idx]}
        for title, key, _ in strategy_cols:
            ev = scenario_results[key].events[s_idx]
            if ev.action == "INIT":
                row[title] = "Holes: [100, 120] KB"
            elif ev.success:
                row[title] = f"✅ Placed in {ev.size} KB (addr {ev.blocks_snapshot if hasattr(ev, 'blocks_snapshot') else ''})"
                # Find allocated block
                for b in ev.blocks:
                    if b.owner == ev.pid:
                        row[title] = f"✅ Placed @ {b.start} KB"
            else:
                row[title] = "❌ FAILED (No hole ≥ 50 KB)"
        matrix_rows.append(row)
    st.dataframe(pd.DataFrame(matrix_rows), use_container_width=True, hide_index=True)

    # Theoretical Explanations
    st.markdown(SCENARIO_EXPLANATION)
    st.markdown(HONESTY_NOTE)


# =========================================================
# TAB 3: TECHNIQUES COMPARISON (QUESTION 1)
# =========================================================
with tab_techniques:
    st.header("📊 Memory Management Techniques (Question 1)")
    st.markdown("""
    **Theoretical Question 1:** *Discuss the performance of all memory management techniques.*
    Compare Fixed Partitioning, Dynamic Partitioning, Simple Paging, Segmentation, and Virtual Memory Page Replacement.
    """)

    subtab_matrix, subtab_paging, subtab_replacement, subtab_belady = st.tabs([
        "📋 Comprehensive Comparison Matrix",
        "🧮 Partitioning & Paging Calculators",
        "📄 Page Replacement (FIFO, LRU, Optimal)",
        "⚠️ Belady's Anomaly Live Demo"
    ])

    # 1. Comparison Matrix
    with subtab_matrix:
        st.subheader("Architecture & Performance Scoring Matrix")
        matrix_data = get_comparison_matrix()
        st.dataframe(pd.DataFrame(matrix_data), use_container_width=True, hide_index=True)

        st.markdown("""
        ### Key Insights:
        - **Fixed Partitioning**: Simple and fast, but suffers from **internal fragmentation** and a rigid maximum process size.
        - **Dynamic Partitioning**: Eliminates internal fragmentation completely, but suffers from severe **external fragmentation**, often requiring expensive compaction.
        - **Paging**: Solves external fragmentation completely by allocating non-contiguous frames. Internal fragmentation is minimal (average 1/2 page per process in the final page).
        - **Segmentation**: Has **zero internal fragmentation** (segments match logical sizes exactly), but still suffers from **external fragmentation** due to variable segment lengths (often requiring compaction).
        """)

    # 2. Calculators
    with subtab_paging:
        st.subheader("Interactive Memory Overhead Calculators")
        calc_col1, calc_col2 = st.columns(2)

        with calc_col1:
            st.markdown("#### Simple Paging Overhead Calculator")
            proc_size = st.number_input("Process Size (KB)", min_value=1, max_value=65536, value=35, step=5, key="paging_proc_size")
            page_size = st.selectbox("Page Frame Size (KB)", [1, 2, 4, 8, 16], index=2, key="paging_page_size")
            entry_bytes = st.selectbox("Page Table Entry Size (bytes)", [4, 8], index=0, key="paging_entry_bytes")

            try:
                paging_res = calculate_paging_overhead(proc_size, page_size, entry_bytes)
                st.markdown(f"""
                - **Pages Required:** `{paging_res.num_pages}` pages
                - **Allocated Physical Memory:** `{paging_res.num_pages * page_size}` KB
                - **Last Page Internal Fragmentation:** `{paging_res.internal_frag_kb}` KB
                - **Page Table Memory Overhead:** `{paging_res.page_table_size_bytes}` bytes
                - **Overhead Percentage:** `{paging_res.overhead_percentage:.3f}%` of process space
                """)
            except ValueError as e:
                st.error(f"Paging error: {e}")

        with calc_col2:
            st.markdown("#### Fixed Partitioning Fragmentation Calculator")
            fixed_part_size = st.number_input("Partition Size (KB)", min_value=16, max_value=512, value=128, step=16, key="fixed_part_size")
            num_parts = st.number_input("Number of Partitions", min_value=1, max_value=32, value=4, step=1, key="fixed_num_parts")
            raw_reqs = st.text_input("Process Request Sizes (comma-separated KB)", value="50, 120, 140, 80", key="fixed_raw_reqs")

            try:
                req_list = [int(x.strip()) for x in raw_reqs.split(",") if x.strip()]
                if not req_list:
                    st.error("Please enter at least one request size.")
                elif any(r <= 0 for r in req_list):
                    st.error("Request sizes must be positive integers.")
                else:
                    fixed_res = calculate_fixed_partitioning(fixed_part_size, num_parts, req_list)
                    st.markdown(f"""
                    - **Total Internal Fragmentation:** `{fixed_res.total_internal_frag}` KB
                    - **Satisfied Requests:** `{fixed_res.satisfied_requests}` / `{len(req_list)}`
                    - **Failed Requests:** `{fixed_res.failed_requests}`
                    - **Memory Utilization:** `{fixed_res.utilization * 100:.1f}%`
                    """)
            except ValueError as e:
                st.error(f"Invalid input: {e}")

    # 3. Page Replacement
    with subtab_replacement:
        st.subheader("Virtual Memory Page Replacement Simulator")
        st.write("Compare FIFO, LRU, and Optimal algorithms on custom reference strings.")

        repl_col1, repl_col2 = st.columns([3, 1])
        with repl_col1:
            raw_ref = st.text_input(
                "Reference String (comma-separated page numbers)",
                value=", ".join(map(str, STANDARD_REF_STRING)),
                key="repl_raw_ref_input"
            )
        with repl_col2:
            frames_count = st.slider("Allocated Physical Frames", min_value=2, max_value=8, value=3, key="repl_frames_slider")

        tokens = [x.strip() for x in raw_ref.split(",") if x.strip()]
        if not tokens:
            st.error("Reference string is empty! Falling back to standard reference string.")
            ref_pages = STANDARD_REF_STRING
        else:
            try:
                parsed_pages = [int(x) for x in tokens]
                if any(p < 0 for p in parsed_pages):
                    st.error("Page numbers cannot be negative! Falling back to standard reference string.")
                    ref_pages = STANDARD_REF_STRING
                else:
                    ref_pages = parsed_pages
            except ValueError:
                st.error("Invalid reference string! Please enter comma-separated integers. Falling back to standard reference string.")
                ref_pages = STANDARD_REF_STRING

        # Simulate all 3 algorithms
        res_fifo = simulate_fifo(ref_pages, frames_count)
        res_lru = simulate_lru(ref_pages, frames_count)
        res_opt = simulate_optimal(ref_pages, frames_count)

        # Metrics display
        m_col1, m_col2, m_col3 = st.columns(3)
        with m_col1:
            st.metric("FIFO Faults", res_fifo.faults, delta=f"Hit Ratio: {res_fifo.hit_ratio * 100:.1f}%")
        with m_col2:
            st.metric("LRU Faults", res_lru.faults, delta=f"Hit Ratio: {res_lru.hit_ratio * 100:.1f}%")
        with m_col3:
            st.metric("Optimal Faults", res_opt.faults, delta=f"Hit Ratio: {res_opt.hit_ratio * 100:.1f}%")

        # Select algorithm to inspect frame grid
        selected_algo = st.radio("Inspect Step-by-Step Frame Matrix for:", ["FIFO", "LRU", "Optimal"], horizontal=True, key="repl_algo_radio")
        active_res = res_fifo if selected_algo == "FIFO" else (res_lru if selected_algo == "LRU" else res_opt)

        # Build Frame Matrix
        matrix_dict: Dict[str, List[Any]] = {"Step": [], "Page": [], "Event": []}
        for f in range(frames_count):
            matrix_dict[f"Frame {f}"] = []

        for stp in active_res.steps:
            matrix_dict["Step"].append(stp.step_index + 1)
            matrix_dict["Page"].append(stp.page)
            matrix_dict["Event"].append("❌ FAULT" if stp.is_fault else "✅ HIT")
            for f in range(frames_count):
                val = stp.frames[f] if f < len(stp.frames) and stp.frames[f] is not None else "—"
                matrix_dict[f"Frame {f}"].append(val)

        st.dataframe(pd.DataFrame(matrix_dict), use_container_width=True, hide_index=True)

    # 4. Belady's Anomaly
    with subtab_belady:
        st.subheader("⚠️ Belady's Anomaly Demonstration")
        st.markdown("""
        **Belady's Anomaly** is the counterintuitive phenomenon in First-In-First-Out (FIFO) page replacement
        where **increasing the number of page frames results in an increase in the number of page faults**.

        This violates the natural expectation that more memory should always yield better or equal performance.
        *(Stack-based algorithms like LRU and Optimal are immune to Belady's Anomaly).*
        """)

        belady_data = run_belady_check(max_frames=7)
        df_belady = pd.DataFrame(belady_data)

        st.dataframe(df_belady, use_container_width=True, hide_index=True)

        # Plotly Line Chart for Belady
        fig_belady = go.Figure()
        fig_belady.add_trace(go.Scatter(
            x=df_belady["frames"],
            y=df_belady["FIFO Faults"],
            mode="lines+markers+text",
            name="FIFO (Exhibits Anomaly)",
            text=df_belady["FIFO Faults"],
            textposition="top center",
            line=dict(color="#ef4444", width=3)
        ))
        fig_belady.add_trace(go.Scatter(
            x=df_belady["frames"],
            y=df_belady["LRU Faults"],
            mode="lines+markers",
            name="LRU (Monotonic)",
            line=dict(color="#3b82f6", width=2, dash="dash")
        ))
        fig_belady.add_trace(go.Scatter(
            x=df_belady["frames"],
            y=df_belady["Optimal Faults"],
            mode="lines+markers",
            name="Optimal (Monotonic)",
            line=dict(color="#10b981", width=2, dash="dot")
        ))

        # Add annotation for anomaly at 3 -> 4 frames
        fig_belady.add_annotation(
            x=4,
            y=10,
            text="⚠️ Anomaly: 9 -> 10 faults!",
            showarrow=True,
            arrowhead=2,
            arrowcolor="#ef4444",
            arrowsize=1.2,
            font=dict(color="#ef4444", size=12, family="Inter, sans-serif")
        )

        fig_belady.update_layout(
            title="Page Faults vs. Frame Allocation (Belady Reference String: 1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5)",
            xaxis_title="Number of Frames",
            yaxis_title="Total Page Faults",
            plot_bgcolor="#ffffff",
            paper_bgcolor="#ffffff",
            hovermode="x unified",
            height=400
        )
        st.plotly_chart(fig_belady, use_container_width=True, key="belady_plotly_chart")


# =========================================================
# TAB 4: BENCHMARK & HONESTY (EMPIRICAL WORKLOADS)
# =========================================================
with tab_benchmark:
    st.header("🚀 Random Workload Benchmark & Honesty Panel")
    st.markdown("""
    Evaluate allocation strategies across hundreds of randomized allocation and deallocation operations to measure
    **Failure Rate**, **External Fragmentation**, and **Memory Utilization**.
    """)

    bench_col1, bench_col2, bench_col3, bench_col4 = st.columns(4)
    with bench_col1:
        num_runs = st.slider("Benchmark Runs (Workloads)", min_value=5, max_value=50, value=20, step=5, key="bench_num_runs")
    with bench_col2:
        ops_per_run = st.slider("Operations per Workload", min_value=20, max_value=100, value=40, step=10, key="bench_ops_per_run")
    with bench_col3:
        bench_mem = st.number_input("Memory Size (KB)", min_value=200, max_value=2000, value=500, step=100, key="bench_mem")
    with bench_col4:
        bench_seed = st.number_input("Deterministic Random Seed", min_value=1, max_value=9999, value=100, key="bench_seed")

    if st.button("🔥 Run Monte Carlo Benchmark Suite", type="primary", use_container_width=True, key="bench_run_btn"):
        with st.spinner("Executing randomized workloads across all strategies..."):
            agg_results, raw_records = run_benchmark_suite(
                num_runs=num_runs,
                num_operations_per_run=ops_per_run,
                total_memory_kb=bench_mem,
                base_seed=bench_seed
            )
            st.session_state.bench_agg = agg_results
            st.session_state.bench_raw = raw_records

    # Display results if available
    if "bench_agg" in st.session_state:
        df_bench = pd.DataFrame([
            {
                "Strategy": r.strategy,
                "Avg Failure Rate": f"{r.avg_failure_rate * 100:.2f}%",
                "Avg External Frag.": f"{r.avg_external_fragmentation * 100:.2f}%",
                "Avg Utilization": f"{r.avg_utilization * 100:.2f}%",
                "Total Satisfied": r.total_satisfied,
                "Total Failed": r.total_failed,
            }
            for r in st.session_state.bench_agg
        ])

        st.subheader("Aggregated Performance Metrics")
        st.dataframe(df_bench, use_container_width=True, hide_index=True)

        # Plotly Comparison Charts
        plot_df = pd.DataFrame([
            {
                "Strategy": r.strategy,
                "Failure Rate (%)": r.avg_failure_rate * 100,
                "External Fragmentation (%)": r.avg_external_fragmentation * 100,
                "Utilization (%)": r.avg_utilization * 100
            }
            for r in st.session_state.bench_agg
        ])

        chart_col1, chart_col2 = st.columns(2)
        with chart_col1:
            fig_fail = px.bar(
                plot_df,
                x="Strategy",
                y="Failure Rate (%)",
                color="Strategy",
                color_discrete_sequence=["#3b82f6", "#10b981", "#ef4444", "#f59e0b"],
                title="Average Request Failure Rate (Lower is Better)",
                text_auto=".1f"
            )
            fig_fail.update_layout(plot_bgcolor="#ffffff", paper_bgcolor="#ffffff", showlegend=False)
            st.plotly_chart(fig_fail, use_container_width=True, key="bench_fail_chart")

        with chart_col2:
            fig_frag = px.bar(
                plot_df,
                x="Strategy",
                y="External Fragmentation (%)",
                color="Strategy",
                color_discrete_sequence=["#3b82f6", "#10b981", "#ef4444", "#f59e0b"],
                title="Average External Fragmentation Index (Lower is Better)",
                text_auto=".1f"
            )
            fig_frag.update_layout(plot_bgcolor="#ffffff", paper_bgcolor="#ffffff", showlegend=False)
            st.plotly_chart(fig_frag, use_container_width=True, key="bench_frag_chart")

    st.markdown("---")

    # Honesty Panel: Concrete Proof where Worst-Fit Fails
    st.subheader("Honesty Panel: Proof That Worst-Fit Does Not Always Win")
    st.markdown("""
    While Tab 2 proved that Worst-Fit wins under structured workloads that benefit from even hole division,
    Worst-Fit is rarely preferred because it shreds large holes; real kernels use buddy and slab allocators. Here is why:
    """)

    counter_res = get_worst_fit_counterexample()
    counter_rows = []
    for strat, data in counter_res["results"].items():
        counter_rows.append({
            "Strategy": strat.replace("_", " ").title(),
            "Failure Rate": f"{data['failure_rate'] * 100:.1f}%",
            "Failed Requests": data['failed'],
            "Satisfied Requests": data['satisfied'],
            "External Fragmentation": f"{data['external_fragmentation'] * 100:.1f}%",
            "Utilization": f"{data['utilization'] * 100:.1f}%"
        })

    st.dataframe(pd.DataFrame(counter_rows), use_container_width=True, hide_index=True)

    st.markdown("""
    <div class="explanation-card">
        <b>Why Worst-Fit Loses in Real Systems:</b>
        <ol>
            <li><b>Destruction of Large Holes:</b> Worst-Fit always attacks the largest free block in the system. As a result, memory quickly contains only medium and small fragments. When a process requesting a genuinely large contiguous block arrives, the request fails.</li>
            <li><b>Higher External Fragmentation:</b> Best-Fit and First-Fit preserve large untouched regions at the end of memory, maintaining lower long-term failure rates.</li>
            <li><b>Search Overhead:</b> Worst-Fit must traverse the entire list or maintain a sorted tree of holes on every allocation, adding kernel latency compared to First-Fit.</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)
