import plotly.express as px
import plotly.graph_objects as go


# Teal & Cyan theme
BACKGROUND = "#0B1E23"
SIDEBAR = "#0F3A40"
CARD = "#134E4A"
PRIMARY = "#06B6D4"
ACCENT = "#67E8F9"
TEXT = "#E2E8F0"


def apply_dark_theme(fig):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=BACKGROUND,
        plot_bgcolor=BACKGROUND,
        font=dict(color=TEXT),
        colorway=[PRIMARY, ACCENT, "#14B8A6", "#F59E0B", "#A78BFA"],
        margin=dict(l=20, r=20, t=55, b=20),
    )
    return fig


def bar_chart(data, x, y, title, color=None):
    fig = px.bar(
        data,
        x=x,
        y=y,
        title=title,
        color=color,
        color_discrete_sequence=[PRIMARY, ACCENT, "#14B8A6"],
    )
    return apply_dark_theme(fig)


def line_chart(data, x, y, title, color=None):
    fig = px.line(
        data,
        x=x,
        y=y,
        title=title,
        color=color,
        markers=True,
        color_discrete_sequence=[PRIMARY, ACCENT, "#14B8A6"],
    )
    return apply_dark_theme(fig)


def comparison_bar(labels, values, title):
    fig = go.Figure(
        data=[
            go.Bar(
                x=labels,
                y=values,
                marker_color=[PRIMARY, ACCENT],
            )
        ]
    )
    fig.update_layout(title=title)
    return apply_dark_theme(fig)