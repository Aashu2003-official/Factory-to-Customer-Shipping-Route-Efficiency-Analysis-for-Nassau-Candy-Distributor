from __future__ import annotations

import base64
from pathlib import Path

import pandas as pd
import streamlit as st

from src.config import APP_SUBTITLE, APP_TITLE, RAW_DATA_PATH
from src.data_pipeline import (
    aggregate_geographic_metrics,
    aggregate_region_metrics,
    aggregate_route_metrics,
    aggregate_ship_mode_metrics,
    build_kpis,
    calculate_delay_threshold,
    filter_orders,
    get_route_order_details,
    load_orders,
)
from src.visuals import (
    make_region_bottleneck_chart,
    make_route_leaderboard,
    make_route_scatter,
    make_route_timeline,
    make_ship_mode_bar,
    make_ship_mode_distribution,
    make_ship_mode_region_heatmap,
    make_us_state_choropleth,
)


st.set_page_config(page_title="Nassau Candy Route Efficiency", layout="wide")


@st.cache_data(show_spinner=False)
def load_project_data(data_path: str):
    return load_orders(data_path)


def format_currency(value: float) -> str:
    return f"${value:,.2f}"


orders, factory_reference, cleaning_summary = load_project_data(str(RAW_DATA_PATH))
default_threshold = calculate_delay_threshold(orders)
logo_path = Path(__file__).resolve().parent / "assets" / "nassau_candy_logo.svg"
logo_base64 = base64.b64encode(logo_path.read_bytes()).decode("utf-8")

header_left, header_center, header_right = st.columns([1, 2, 1])
with header_center:
    st.markdown(
        f"""
        <div style="text-align: center; padding: 0.25rem 0 0.75rem 0;">
            <a href="https://www.nassaucandy.com/" target="_blank">
                <img
                    src="data:image/svg+xml;base64,{logo_base64}"
                    alt="Nassau Candy"
                    style="max-width: 420px; width: 100%; height: auto;"
                />
            </a>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.title(APP_TITLE)
st.caption(APP_SUBTITLE)

if cleaning_summary["lead_time_warning"]:
    st.warning(
        "The source data contains a date anomaly: order dates run from "
        f"{cleaning_summary['order_date_min']} to {cleaning_summary['order_date_max']}, while ship dates run from "
        f"{cleaning_summary['ship_date_min']} to {cleaning_summary['ship_date_max']}. "
        "Use lead times primarily for relative route benchmarking unless the source dates are corrected."
    )

with st.sidebar:
    st.header("Filters")
    min_order_date = orders["order_date"].min().date()
    max_order_date = orders["order_date"].max().date()
    date_range = st.date_input(
        "Order date range",
        value=(min_order_date, max_order_date),
        min_value=min_order_date,
        max_value=max_order_date,
    )

    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date, end_date = min_order_date, max_order_date

    country_options = sorted(orders["country_region"].unique().tolist())
    selected_countries = st.multiselect("Country / region", country_options, default=country_options)

    region_pool = orders if not selected_countries else orders.loc[orders["country_region"].isin(selected_countries)]
    region_options = sorted(region_pool["region"].unique().tolist())
    selected_regions = st.multiselect("Customer region", region_options, default=region_options)

    state_pool = region_pool if not selected_regions else region_pool.loc[region_pool["region"].isin(selected_regions)]
    state_options = sorted(state_pool["state_province"].unique().tolist())
    selected_states = st.multiselect("State / province", state_options, default=state_options)

    ship_mode_options = sorted(orders["ship_mode"].unique().tolist())
    selected_ship_modes = st.multiselect("Ship mode", ship_mode_options, default=ship_mode_options)

    threshold = st.slider(
        "Delay threshold (days)",
        min_value=int(orders["shipping_lead_time_days"].min()),
        max_value=int(orders["shipping_lead_time_days"].max()),
        value=int(default_threshold),
        step=1,
    )

    with st.expander("Data quality summary", expanded=False):
        st.write(f"Raw rows: {cleaning_summary['raw_rows']:,}")
        st.write(f"Rows removed during cleaning: {cleaning_summary['removed_rows']:,}")
        st.write(f"Missing shipment records: {cleaning_summary['missing_ship_dates']:,}")
        st.write(f"Negative lead times removed: {cleaning_summary['negative_lead_times']:,}")
        st.write(f"Median lead time after cleaning: {cleaning_summary['median_lead_time_days']:,} days")


filtered_orders = filter_orders(
    orders,
    start_date=pd.Timestamp(start_date),
    end_date=pd.Timestamp(end_date),
    countries=selected_countries,
    regions=selected_regions,
    states=selected_states,
    ship_modes=selected_ship_modes,
)

if filtered_orders.empty:
    st.error("No shipments match the current filter combination. Expand the filters to continue.")
    st.stop()

kpis = build_kpis(filtered_orders, threshold)
state_routes = aggregate_route_metrics(filtered_orders, "state", threshold)
region_routes = aggregate_route_metrics(filtered_orders, "region", threshold)
geo_metrics = aggregate_geographic_metrics(filtered_orders, threshold)
region_metrics = aggregate_region_metrics(filtered_orders, threshold)
ship_mode_metrics = aggregate_ship_mode_metrics(filtered_orders, threshold)

metric_col_1, metric_col_2, metric_col_3, metric_col_4 = st.columns(4)
metric_col_1.metric("Shipments", f"{kpis['shipments']:,}")
metric_col_2.metric("Average lead time", f"{kpis['avg_lead_time_days']:,} days")
metric_col_3.metric("Delay frequency", f"{kpis['delay_frequency_pct']:.2f}%")
metric_col_4.metric("State routes", f"{kpis['state_route_count']:,}")

summary_col_1, summary_col_2, summary_col_3 = st.columns(3)
summary_col_1.metric("Filtered sales", format_currency(kpis["total_sales"]))
summary_col_2.metric("Gross profit", format_currency(kpis["gross_profit"]))
summary_col_3.metric("Countries served", f"{kpis['countries_served']:,}")

overview_tab, geography_tab, ship_mode_tab, drill_down_tab = st.tabs(
    ["Route Efficiency Overview", "Geographic Shipping Map", "Ship Mode Comparison", "Route Drill-Down"]
)

with overview_tab:
    st.subheader("Route Performance Leaderboard")
    route_level_label = st.radio(
        "Route level",
        options=["Factory -> State / Province", "Factory -> Region"],
        horizontal=True,
    )
    route_metrics = state_routes if route_level_label == "Factory -> State / Province" else region_routes

    leaderboard_left, leaderboard_right = st.columns(2)
    with leaderboard_left:
        st.plotly_chart(
            make_route_leaderboard(route_metrics, "Top 10 Most Efficient Routes", top_n=10, ascending=True),
            use_container_width=True,
        )
    with leaderboard_right:
        st.plotly_chart(
            make_route_leaderboard(route_metrics, "Bottom 10 Least Efficient Routes", top_n=10, ascending=False),
            use_container_width=True,
        )

    st.plotly_chart(
        make_route_scatter(route_metrics, "Route Bottleneck Matrix: Volume vs Lead Time"),
        use_container_width=True,
    )

    st.dataframe(
        route_metrics[
            [
                "route_name",
                "total_shipments",
                "average_lead_time_days",
                "lead_time_variability",
                "delay_frequency_pct",
                "route_efficiency_score",
                "total_sales",
                "gross_profit",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )

with geography_tab:
    st.subheader("Geographic Bottlenecks")
    us_geo_metrics = geo_metrics.loc[geo_metrics["country_region"].eq("United States")].copy()

    st.plotly_chart(
        make_us_state_choropleth(us_geo_metrics, "average_lead_time_days", "US Heatmap: Average Lead Time by State"),
        use_container_width=True,
    )
    st.plotly_chart(
        make_us_state_choropleth(us_geo_metrics, "bottleneck_score", "US Heatmap: Bottleneck Score by State"),
        use_container_width=True,
    )

    st.plotly_chart(
        make_region_bottleneck_chart(region_metrics, "Regional Bottleneck Comparison"),
        use_container_width=True,
    )

    st.dataframe(
        geo_metrics[
            [
                "country_region",
                "region",
                "state_province",
                "total_shipments",
                "average_lead_time_days",
                "delay_frequency_pct",
                "bottleneck_score",
                "route_efficiency_score",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )

with ship_mode_tab:
    st.subheader("Ship Mode Efficiency")
    ship_left, ship_right = st.columns(2)
    with ship_left:
        st.plotly_chart(
            make_ship_mode_bar(ship_mode_metrics, "Lead Time by Ship Mode"),
            use_container_width=True,
        )
    with ship_right:
        st.plotly_chart(
            make_ship_mode_region_heatmap(filtered_orders, "Ship Mode vs Region Heatmap"),
            use_container_width=True,
        )

    st.plotly_chart(
        make_ship_mode_distribution(filtered_orders, "Lead Time Distribution by Ship Mode"),
        use_container_width=True,
    )

    st.dataframe(ship_mode_metrics, use_container_width=True, hide_index=True)

with drill_down_tab:
    st.subheader("Route Drill-Down")
    drill_level_label = st.selectbox("Route detail level", ["State / Province", "Region"])
    drill_level = "state" if drill_level_label == "State / Province" else "region"
    destination_column = "state_province" if drill_level == "state" else "region"

    factory_options = sorted(filtered_orders["factory"].dropna().unique().tolist())
    selected_factory = st.selectbox("Factory", factory_options)
    destination_options = sorted(
        filtered_orders.loc[filtered_orders["factory"].eq(selected_factory), destination_column].dropna().unique().tolist()
    )
    selected_destination = st.selectbox("Destination", destination_options)

    route_orders = get_route_order_details(filtered_orders, selected_factory, selected_destination, drill_level)
    route_ship_mode_metrics = aggregate_ship_mode_metrics(route_orders, threshold)

    detail_col_1, detail_col_2, detail_col_3, detail_col_4 = st.columns(4)
    detail_col_1.metric("Orders on route", f"{len(route_orders):,}")
    detail_col_2.metric("Avg lead time", f"{route_orders['shipping_lead_time_days'].mean():.2f} days")
    detail_col_3.metric("Total sales", format_currency(route_orders["sales"].sum()))
    detail_col_4.metric("Gross profit", format_currency(route_orders["gross_profit"].sum()))

    st.plotly_chart(
        make_route_timeline(route_orders, f"Recent order-to-ship timeline for {selected_factory} -> {selected_destination}"),
        use_container_width=True,
    )

    drill_left, drill_right = st.columns(2)
    with drill_left:
        st.dataframe(
            route_ship_mode_metrics[
                [
                    "ship_mode",
                    "total_shipments",
                    "average_lead_time_days",
                    "lead_time_variability",
                    "delay_frequency_pct",
                    "average_order_value",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )
    with drill_right:
        st.dataframe(
            route_orders[
                [
                    "order_id",
                    "order_date",
                    "ship_date",
                    "ship_mode",
                    "customer_id",
                    "city",
                    "state_province",
                    "product_name",
                    "sales",
                    "shipping_lead_time_days",
                ]
            ].sort_values("order_date", ascending=False),
            use_container_width=True,
            hide_index=True,
        )

with st.expander("Factory reference data", expanded=False):
    st.dataframe(factory_reference, use_container_width=True, hide_index=True)

st.caption(
    f"Data source: {Path(RAW_DATA_PATH).name}. Default delay threshold set to the 75th percentile lead time ({default_threshold} days)."
)

