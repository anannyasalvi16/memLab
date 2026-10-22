from __future__ import annotations
import html
from typing import List
import plotly.graph_objects as go
from core.models import Block


def render_memory_bar_plotly(
    blocks: List[Block],
    total_memory: int,
    title: str = "",
    height: int = 130
) -> go.Figure:
    """
    Renders an interactive horizontal stacked memory bar using Plotly.
    - Allocated: Green (#10b981)
    - Free Holes: Grey (#e2e8f0)
    - Reserved: Slate (#64748b)
    """
    fig = go.Figure()

    for idx, b in enumerate(blocks):
        safe_owner = html.escape(str(b.owner)) if b.owner else ""
        if b.is_free:
            color = "#e2e8f0"
            border_color = "#94a3b8"
            label = f"Hole<br>{b.size}K"
            hover_text = f"<b>Free Hole</b><br>Start: {b.start} KB<br>End: {b.end} KB<br>Size: {b.size} KB"
            text_color = "#475569"
        elif b.owner == "OS_RESERVED":
            color = "#94a3b8"
            border_color = "#64748b"
            label = f"Reserved<br>{b.size}K"
            hover_text = f"<b>OS Reserved</b><br>Start: {b.start} KB<br>End: {b.end} KB<br>Size: {b.size} KB"
            text_color = "#ffffff"
        else:
            color = "#10b981"
            border_color = "#047857"
            label = f"<b>{safe_owner}</b><br>{b.size}K"
            hover_text = f"<b>Process: {safe_owner}</b><br>Start: {b.start} KB<br>End: {b.end} KB<br>Size: {b.size} KB"
            text_color = "#ffffff"

        fig.add_trace(go.Bar(
            y=["Memory"],
            x=[b.size],
            name=b.owner if b.owner else f"Hole_{idx}",
            orientation='h',
            text=label if b.size >= (total_memory * 0.08) else "",
            textposition="inside",
            insidetextanchor="middle",
            textfont=dict(color=text_color, size=11, family="Inter, sans-serif"),
            hoverinfo="text",
            hovertext=hover_text,
            marker=dict(
                color=color,
                line=dict(color=border_color, width=1.5)
            ),
            showlegend=False
        ))

    fig.update_layout(
        barmode='stack',
        height=height,
        margin=dict(l=10, r=10, t=30 if title else 10, b=25),
        title=dict(text=title, font=dict(size=13, color="#1e293b", family="Inter, sans-serif")),
        xaxis=dict(
            range=[0, total_memory],
            showgrid=True,
            gridcolor="#f1f5f9",
            zeroline=False,
            title=dict(text="Memory Address (KB)", font=dict(size=10, color="#64748b")),
            tickfont=dict(size=9, color="#64748b")
        ),
        yaxis=dict(
            showticklabels=False,
            showgrid=False
        ),
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
    )

    return fig


def render_memory_bar_html(blocks: List[Block], total_memory: int) -> str:
    """
    Renders a lightweight, ultra-crisp CSS memory bar suitable for side-by-side columns.
    """
    if total_memory <= 0:
        return ""

    segments_html = []
    for b in blocks:
        pct = (b.size / total_memory) * 100
        safe_owner = html.escape(str(b.owner)) if b.owner else ""
        if b.is_free:
            bg = "#f1f5f9"
            border = "1px dashed #94a3b8"
            color = "#475569"
            text = f"Hole {b.size}K"
        elif b.owner == "OS_RESERVED":
            bg = "#cbd5e1"
            border = "1px solid #64748b"
            color = "#1e293b"
            text = f"Res {b.size}K"
        else:
            bg = "#10b981"
            border = "1px solid #047857"
            color = "#ffffff"
            text = f"{safe_owner} ({b.size}K)"

        # Only show text if width is at least 10% to prevent overflow
        label = text if pct >= 10 else ""
        tooltip = f"{safe_owner or 'Free Hole'}: {b.start}-{b.end} KB ({b.size} KB)"

        segments_html.append(
            f'<div title="{tooltip}" style="width: {pct:.2f}%; background-color: {bg}; border: {border}; color: {color}; '
            f'display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: 500; '
            f'height: 48px; box-sizing: border-box; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; '
            f'border-radius: 3px; margin-right: 1px;">{label}</div>'
        )

    return f'''
    <div style="width: 100%; display: flex; background: #e2e8f0; padding: 2px; border-radius: 5px; border: 1px solid #cbd5e1; margin-bottom: 8px;">
        {''.join(segments_html)}
    </div>
    <div style="display: flex; justify-content: space-between; font-size: 10px; color: #64748b; font-family: monospace; margin-bottom: 6px;">
        <span>0 KB</span>
        <span>Total: {total_memory} KB</span>
    </div>
    '''
