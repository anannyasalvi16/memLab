from __future__ import annotations
import sys
from pathlib import Path

# Anchor repo root in sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
from core.models import AllocationMetrics


def display_metric_cards(metrics: AllocationMetrics):
    """Displays 4 neatly formatted metric cards in a row."""
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            label="Memory Utilization",
            value=f"{metrics.utilization * 100:.1f}%",
            delta=f"{metrics.allocated_memory} / {metrics.total_memory} KB"
        )
    with col2:
        st.metric(
            label="External Frag.",
            value=f"{metrics.external_fragmentation * 100:.1f}%",
            delta=f"Largest Hole: {metrics.largest_hole} KB",
            delta_color="inverse"
        )
    with col3:
        st.metric(
            label="Holes Count",
            value=metrics.num_holes,
            delta=f"Free: {metrics.free_memory} KB"
        )
    with col4:
        st.metric(
            label="Failure Rate",
            value=f"{metrics.failure_rate * 100:.1f}%",
            delta=f"{metrics.requests_failed} failed / {metrics.requests_satisfied + metrics.requests_failed} total",
            delta_color="inverse"
        )


def apply_custom_styles():
    """Applies minimal, modern light styling to Streamlit."""
    st.markdown("""
        <style>
        /* Modern minimal light theme styling */
        .block-container {
            padding-top: 2rem;
            padding-bottom: 3rem;
            max-width: 1200px;
        }
        div[data-testid="stMetricValue"] {
            font-size: 1.5rem !important;
            font-weight: 700;
            color: #0f172a;
        }
        div[data-testid="stMetricDelta"] {
            font-size: 0.8rem !important;
        }
        .element-container:has(iframe) {
            margin-top: 0.5rem;
            margin-bottom: 0.5rem;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 12px;
        }
        .stTabs [data-baseweb="tab"] {
            font-weight: 600;
            padding: 8px 16px;
            border-radius: 6px;
        }
        .stTabs [aria-selected="true"] {
            background-color: #f1f5f9;
        }
        .explanation-card {
            background-color: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 16px;
            margin-top: 12px;
            margin-bottom: 12px;
        }
        .badge-success {
            background-color: #dcfce7;
            color: #166534;
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
        }
        .badge-fail {
            background-color: #fee2e2;
            color: #991b1b;
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
        }
        </style>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    import runpy
    app_file = ROOT_DIR / "app.py"
    runpy.run_path(str(app_file), run_name="__main__")
