from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def _empty_figure(title: str) -> go.Figure:
    figure = go.Figure()
    figure.update_layout(
        title=title,
        template="plotly_white",
        xaxis={"visible": False},
        yaxis={"visible": False},
        annotations=[
            {
                "text": "No data available for the current filters.",
                "xref": "paper",
                "yref": "paper",
                "x": 0.5,
                "y": 0.5,
                "showarrow": False,
            }
        ],
        margin={"l": 20, "r": 20, "t": 50, "b": 20},
    )
    return figure


def make_route_leaderboard(route_metrics: pd.DataFrame, title: str, top_n: int = 10, ascending: bool = True) -> go.Figure:
    if route_metrics.empty:
        return _empty_figure(title)

    chart_data = route_metrics.sort_values(
        ["average_lead_time_days", "lead_time_variability", "total_shipments"],
        ascending=[ascending, True, False],
    ).head(top_n)
    chart_data = chart_data.sort_values("average_lead_time_days", ascending=False)

    figure = px.bar(
        chart_data,
        x="average_lead_time_days",
        y="route_name",
        orientation="h",
        color="route_efficiency_score",
        color_continuous_scale="RdYlGn",
        hover_data={
            "total_shipments": True,
            "delay_frequency_pct": True,
            "lead_time_variability": True,
            "route_efficiency_score": True,
            "average_lead_time_days": ":.2f",
        },
        labels={
            "average_lead_time_days": "Average lead time (days)",
            "route_name": "Route",
            "route_efficiency_score": "Efficiency score",
        },
        title=title,
    )
    figure.update_layout(template="plotly_white", coloraxis_showscale=False, margin={"l": 20, "r": 20, "t": 60, "b": 20})
    return figure


def make_route_scatter(route_metrics: pd.DataFrame, title: str) -> go.Figure:
    if route_metrics.empty:
        return _empty_figure(title)

    figure = px.scatter(
        route_metrics,
        x="total_shipments",
        y="average_lead_time_days",
        size="gross_profit",
        color="delay_frequency_pct",
        hover_name="route_name",
        hover_data={
            "lead_time_variability": True,
            "route_efficiency_score": True,
            "total_sales": True,
            "gross_profit": True,
        },
        color_continuous_scale="YlOrRd",
        labels={
            "total_shipments": "Shipment volume",
            "average_lead_time_days": "Average lead time (days)",
            "delay_frequency_pct": "Delay frequency (%)",
        },
        title=title,
    )
    figure.update_layout(template="plotly_white", margin={"l": 20, "r": 20, "t": 60, "b": 20})
    return figure


def make_us_state_choropleth(geo_metrics: pd.DataFrame, color_column: str, title: str) -> go.Figure:
    chart_data = geo_metrics.dropna(subset=["state_code"]).copy()
    if chart_data.empty:
        return _empty_figure(title)

    figure = px.choropleth(
        chart_data,
        locations="state_code",
        locationmode="USA-states",
        scope="usa",
        color=color_column,
        hover_name="state_province",
        hover_data={
            "average_lead_time_days": True,
            "total_shipments": True,
            "delay_frequency_pct": True,
            "bottleneck_score": True,
            "state_code": False,
        },
        color_continuous_scale="YlOrRd",
        title=title,
    )
    figure.update_layout(template="plotly_white", height=760, margin={"l": 20, "r": 20, "t": 60, "b": 20})
    figure.update_geos(fitbounds="locations", visible=False)
    return figure


def make_region_bottleneck_chart(region_metrics: pd.DataFrame, title: str) -> go.Figure:
    if region_metrics.empty:
        return _empty_figure(title)

    figure = px.bar(
        region_metrics.sort_values("bottleneck_score", ascending=False),
        x="region",
        y="bottleneck_score",
        color="average_lead_time_days",
        color_continuous_scale="YlOrRd",
        hover_data={
            "total_shipments": True,
            "delay_frequency_pct": True,
            "lead_time_variability": True,
        },
        labels={"bottleneck_score": "Bottleneck score", "region": "Customer region"},
        title=title,
    )
    figure.update_layout(template="plotly_white", coloraxis_showscale=False, margin={"l": 20, "r": 20, "t": 60, "b": 20})
    return figure


def make_ship_mode_bar(ship_mode_metrics: pd.DataFrame, title: str) -> go.Figure:
    if ship_mode_metrics.empty:
        return _empty_figure(title)

    figure = px.bar(
        ship_mode_metrics,
        x="ship_mode",
        y="average_lead_time_days",
        color="delay_frequency_pct",
        color_continuous_scale="YlOrRd",
        hover_data={
            "total_shipments": True,
            "lead_time_variability": True,
            "average_order_value": True,
            "total_sales": True,
        },
        labels={
            "ship_mode": "Ship mode",
            "average_lead_time_days": "Average lead time (days)",
            "delay_frequency_pct": "Delay frequency (%)",
        },
        title=title,
    )
    figure.update_layout(template="plotly_white", margin={"l": 20, "r": 20, "t": 60, "b": 20})
    return figure


def make_ship_mode_region_heatmap(orders: pd.DataFrame, title: str) -> go.Figure:
    if orders.empty:
        return _empty_figure(title)

    figure = px.density_heatmap(
        orders,
        x="region",
        y="ship_mode",
        z="shipping_lead_time_days",
        histfunc="avg",
        color_continuous_scale="YlOrRd",
        labels={"region": "Customer region", "ship_mode": "Ship mode", "color": "Average lead time"},
        title=title,
    )
    figure.update_layout(template="plotly_white", margin={"l": 20, "r": 20, "t": 60, "b": 20})
    return figure


def make_ship_mode_distribution(orders: pd.DataFrame, title: str) -> go.Figure:
    if orders.empty:
        return _empty_figure(title)

    figure = px.box(
        orders,
        x="ship_mode",
        y="shipping_lead_time_days",
        color="ship_mode",
        points=False,
        labels={"ship_mode": "Ship mode", "shipping_lead_time_days": "Lead time (days)"},
        title=title,
    )
    figure.update_layout(template="plotly_white", showlegend=False, margin={"l": 20, "r": 20, "t": 60, "b": 20})
    return figure


def make_route_timeline(route_orders: pd.DataFrame, title: str, max_orders: int = 75) -> go.Figure:
    if route_orders.empty:
        return _empty_figure(title)

    timeline_data = route_orders.sort_values("order_date", ascending=False).head(max_orders).copy()
    timeline_data = timeline_data.sort_values("order_date")

    figure = px.timeline(
        timeline_data,
        x_start="order_date",
        x_end="ship_date",
        y="order_id",
        color="ship_mode",
        hover_data={
            "city": True,
            "state_province": True,
            "product_name": True,
            "shipping_lead_time_days": True,
            "sales": True,
        },
        title=title,
    )
    figure.update_yaxes(autorange="reversed")
    figure.update_layout(template="plotly_white", margin={"l": 20, "r": 20, "t": 60, "b": 20})
    return figure
