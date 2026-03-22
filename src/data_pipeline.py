from __future__ import annotations

from typing import Any, Dict, Iterable, Literal, Optional, Tuple

import pandas as pd

from src.config import (
    FACTORY_REFERENCE_PATH,
    LEAD_TIME_WARNING_DAYS,
    PRODUCT_FACTORY_REFERENCE_PATH,
    RAW_DATA_PATH,
    US_STATE_ABBREVIATIONS,
)


COLUMN_RENAMES = {
    "Row ID": "row_id",
    "Order ID": "order_id",
    "Order Date": "order_date",
    "Ship Date": "ship_date",
    "Ship Mode": "ship_mode",
    "Customer ID": "customer_id",
    "Country/Region": "country_region",
    "City": "city",
    "State/Province": "state_province",
    "Postal Code": "postal_code",
    "Division": "division",
    "Region": "region",
    "Product ID": "product_id",
    "Product Name": "product_name",
    "Sales": "sales",
    "Units": "units",
    "Gross Profit": "gross_profit",
    "Cost": "cost",
}

STRING_COLUMNS = [
    "order_id",
    "ship_mode",
    "customer_id",
    "country_region",
    "city",
    "state_province",
    "postal_code",
    "division",
    "region",
    "product_id",
    "product_name",
]

NUMERIC_COLUMNS = ["sales", "units", "gross_profit", "cost"]


def load_orders(data_path: str = str(RAW_DATA_PATH)) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    orders = pd.read_csv(data_path, parse_dates=["Order Date", "Ship Date"], dayfirst=True)
    orders = orders.rename(columns=COLUMN_RENAMES)

    for column in STRING_COLUMNS:
        orders[column] = orders[column].fillna("Unknown").astype(str).str.strip()

    for column in NUMERIC_COLUMNS:
        orders[column] = pd.to_numeric(orders[column], errors="coerce")

    factories = pd.read_csv(FACTORY_REFERENCE_PATH)
    product_factory = pd.read_csv(PRODUCT_FACTORY_REFERENCE_PATH)
    factory_lookup = product_factory.set_index("Product Name")["Factory"]

    orders["factory"] = orders["product_name"].map(factory_lookup)
    orders["shipping_lead_time_days"] = (orders["ship_date"] - orders["order_date"]).dt.days
    orders["route_to_state"] = orders["factory"].fillna("Unknown Factory") + " -> " + orders["state_province"]
    orders["route_to_region"] = orders["factory"].fillna("Unknown Factory") + " -> " + orders["region"]
    orders["is_us_destination"] = orders["country_region"].eq("United States")
    orders["order_month"] = orders["order_date"].dt.to_period("M").astype(str)
    orders["ship_month"] = orders["ship_date"].dt.to_period("M").astype(str)

    raw_rows = len(orders)
    valid_mask = (
        orders["order_date"].notna()
        & orders["ship_date"].notna()
        & orders["shipping_lead_time_days"].notna()
        & orders["shipping_lead_time_days"].ge(0)
        & orders["factory"].notna()
    )
    clean_orders = orders.loc[valid_mask].copy()

    summary = {
        "raw_rows": raw_rows,
        "clean_rows": int(len(clean_orders)),
        "removed_rows": int(raw_rows - len(clean_orders)),
        "missing_ship_dates": int(orders["ship_date"].isna().sum()),
        "missing_factory_mappings": int(orders["factory"].isna().sum()),
        "negative_lead_times": int((orders["shipping_lead_time_days"] < 0).fillna(False).sum()),
        "order_date_min": clean_orders["order_date"].min().date().isoformat(),
        "order_date_max": clean_orders["order_date"].max().date().isoformat(),
        "ship_date_min": clean_orders["ship_date"].min().date().isoformat(),
        "ship_date_max": clean_orders["ship_date"].max().date().isoformat(),
        "average_lead_time_days": round(float(clean_orders["shipping_lead_time_days"].mean()), 2),
        "median_lead_time_days": round(float(clean_orders["shipping_lead_time_days"].median()), 2),
        "lead_time_warning": bool(clean_orders["shipping_lead_time_days"].median() > LEAD_TIME_WARNING_DAYS),
    }

    return clean_orders, factories, summary


def calculate_delay_threshold(df: pd.DataFrame, quantile: float = 0.75) -> int:
    if df.empty:
        return 0
    return int(df["shipping_lead_time_days"].quantile(quantile))


def filter_orders(
    df: pd.DataFrame,
    start_date: Optional[pd.Timestamp] = None,
    end_date: Optional[pd.Timestamp] = None,
    countries: Optional[Iterable[str]] = None,
    regions: Optional[Iterable[str]] = None,
    states: Optional[Iterable[str]] = None,
    ship_modes: Optional[Iterable[str]] = None,
) -> pd.DataFrame:
    filtered = df.copy()

    if start_date is not None:
        filtered = filtered.loc[filtered["order_date"] >= pd.Timestamp(start_date)]
    if end_date is not None:
        filtered = filtered.loc[filtered["order_date"] <= pd.Timestamp(end_date)]

    if countries:
        filtered = filtered.loc[filtered["country_region"].isin(list(countries))]
    if regions:
        filtered = filtered.loc[filtered["region"].isin(list(regions))]
    if states:
        filtered = filtered.loc[filtered["state_province"].isin(list(states))]
    if ship_modes:
        filtered = filtered.loc[filtered["ship_mode"].isin(list(ship_modes))]

    return filtered.copy()


def with_delay_flag(df: pd.DataFrame, threshold: int) -> pd.DataFrame:
    flagged = df.copy()
    flagged["is_delayed"] = flagged["shipping_lead_time_days"] > threshold
    return flagged


def _normalize_efficiency_score(series: pd.Series) -> pd.Series:
    if series.empty:
        return series
    max_value = series.max()
    min_value = series.min()
    if max_value == min_value:
        return pd.Series([100.0] * len(series), index=series.index)
    return ((max_value - series) / (max_value - min_value) * 100).round(2)


def aggregate_route_metrics(
    df: pd.DataFrame,
    level: Literal["state", "region"] = "state",
    threshold: Optional[int] = None,
) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    delay_threshold = threshold if threshold is not None else calculate_delay_threshold(df)
    enriched = with_delay_flag(df, delay_threshold)
    destination_column = "state_province" if level == "state" else "region"

    routes = (
        enriched.groupby(["factory", destination_column], as_index=False)
        .agg(
            total_shipments=("order_id", "count"),
            average_lead_time_days=("shipping_lead_time_days", "mean"),
            lead_time_variability=("shipping_lead_time_days", "std"),
            delay_frequency_pct=("is_delayed", "mean"),
            total_sales=("sales", "sum"),
            total_units=("units", "sum"),
            gross_profit=("gross_profit", "sum"),
            average_order_value=("sales", "mean"),
            country_count=("country_region", "nunique"),
        )
        .rename(columns={destination_column: "destination"})
    )

    routes["lead_time_variability"] = routes["lead_time_variability"].fillna(0)
    routes["delay_frequency_pct"] = (routes["delay_frequency_pct"] * 100).round(2)
    routes["average_lead_time_days"] = routes["average_lead_time_days"].round(2)
    routes["lead_time_variability"] = routes["lead_time_variability"].round(2)
    routes["total_sales"] = routes["total_sales"].round(2)
    routes["gross_profit"] = routes["gross_profit"].round(2)
    routes["average_order_value"] = routes["average_order_value"].round(2)
    routes["route_name"] = routes["factory"] + " -> " + routes["destination"]
    routes["route_efficiency_score"] = _normalize_efficiency_score(routes["average_lead_time_days"])
    routes["rank_fastest"] = routes["average_lead_time_days"].rank(method="dense", ascending=True).astype(int)
    routes["rank_slowest"] = routes["average_lead_time_days"].rank(method="dense", ascending=False).astype(int)
    routes["route_level"] = level

    return routes.sort_values(["average_lead_time_days", "lead_time_variability", "total_shipments"]).reset_index(drop=True)


def aggregate_geographic_metrics(df: pd.DataFrame, threshold: Optional[int] = None) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    delay_threshold = threshold if threshold is not None else calculate_delay_threshold(df)
    enriched = with_delay_flag(df, delay_threshold)

    geography = (
        enriched.groupby(["country_region", "region", "state_province"], as_index=False)
        .agg(
            total_shipments=("order_id", "count"),
            average_lead_time_days=("shipping_lead_time_days", "mean"),
            lead_time_variability=("shipping_lead_time_days", "std"),
            delay_frequency_pct=("is_delayed", "mean"),
            total_sales=("sales", "sum"),
            gross_profit=("gross_profit", "sum"),
        )
    )

    geography["lead_time_variability"] = geography["lead_time_variability"].fillna(0)
    geography["delay_frequency_pct"] = (geography["delay_frequency_pct"] * 100).round(2)
    geography["average_lead_time_days"] = geography["average_lead_time_days"].round(2)
    geography["lead_time_variability"] = geography["lead_time_variability"].round(2)
    geography["state_code"] = geography["state_province"].map(US_STATE_ABBREVIATIONS)
    geography["route_efficiency_score"] = _normalize_efficiency_score(geography["average_lead_time_days"])
    geography["bottleneck_score"] = (
        geography["average_lead_time_days"] * geography["total_shipments"] * (1 + geography["delay_frequency_pct"] / 100)
    ).round(2)

    return geography.sort_values(["bottleneck_score", "average_lead_time_days"], ascending=[False, False]).reset_index(drop=True)


def aggregate_region_metrics(df: pd.DataFrame, threshold: Optional[int] = None) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    delay_threshold = threshold if threshold is not None else calculate_delay_threshold(df)
    enriched = with_delay_flag(df, delay_threshold)

    region_metrics = (
        enriched.groupby("region", as_index=False)
        .agg(
            total_shipments=("order_id", "count"),
            average_lead_time_days=("shipping_lead_time_days", "mean"),
            lead_time_variability=("shipping_lead_time_days", "std"),
            delay_frequency_pct=("is_delayed", "mean"),
            total_sales=("sales", "sum"),
        )
    )

    region_metrics["lead_time_variability"] = region_metrics["lead_time_variability"].fillna(0)
    region_metrics["average_lead_time_days"] = region_metrics["average_lead_time_days"].round(2)
    region_metrics["lead_time_variability"] = region_metrics["lead_time_variability"].round(2)
    region_metrics["delay_frequency_pct"] = (region_metrics["delay_frequency_pct"] * 100).round(2)
    region_metrics["bottleneck_score"] = (
        region_metrics["average_lead_time_days"] * region_metrics["total_shipments"] * (1 + region_metrics["delay_frequency_pct"] / 100)
    ).round(2)

    return region_metrics.sort_values("bottleneck_score", ascending=False).reset_index(drop=True)


def aggregate_ship_mode_metrics(df: pd.DataFrame, threshold: Optional[int] = None) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    delay_threshold = threshold if threshold is not None else calculate_delay_threshold(df)
    enriched = with_delay_flag(df, delay_threshold)

    ship_modes = (
        enriched.groupby("ship_mode", as_index=False)
        .agg(
            total_shipments=("order_id", "count"),
            average_lead_time_days=("shipping_lead_time_days", "mean"),
            lead_time_variability=("shipping_lead_time_days", "std"),
            delay_frequency_pct=("is_delayed", "mean"),
            average_order_value=("sales", "mean"),
            total_sales=("sales", "sum"),
            gross_profit=("gross_profit", "sum"),
        )
    )

    ship_modes["lead_time_variability"] = ship_modes["lead_time_variability"].fillna(0)
    ship_modes["average_lead_time_days"] = ship_modes["average_lead_time_days"].round(2)
    ship_modes["lead_time_variability"] = ship_modes["lead_time_variability"].round(2)
    ship_modes["delay_frequency_pct"] = (ship_modes["delay_frequency_pct"] * 100).round(2)
    ship_modes["average_order_value"] = ship_modes["average_order_value"].round(2)
    ship_modes["total_sales"] = ship_modes["total_sales"].round(2)
    ship_modes["gross_profit"] = ship_modes["gross_profit"].round(2)

    return ship_modes.sort_values("average_lead_time_days").reset_index(drop=True)


def build_kpis(df: pd.DataFrame, threshold: Optional[int] = None) -> Dict[str, Any]:
    if df.empty:
        return {}

    delay_threshold = threshold if threshold is not None else calculate_delay_threshold(df)
    enriched = with_delay_flag(df, delay_threshold)
    state_route_count = int(enriched[["factory", "state_province"]].drop_duplicates().shape[0])
    route_metrics = aggregate_route_metrics(enriched, "state", delay_threshold)
    top_route = route_metrics.iloc[0]["route_name"] if not route_metrics.empty else "N/A"

    return {
        "shipments": int(len(enriched)),
        "avg_lead_time_days": round(float(enriched["shipping_lead_time_days"].mean()), 2),
        "delay_frequency_pct": round(float(enriched["is_delayed"].mean() * 100), 2),
        "state_route_count": state_route_count,
        "top_route": top_route,
        "total_sales": round(float(enriched["sales"].sum()), 2),
        "gross_profit": round(float(enriched["gross_profit"].sum()), 2),
        "countries_served": int(enriched["country_region"].nunique()),
    }


def get_route_order_details(
    df: pd.DataFrame,
    factory: str,
    destination: str,
    level: Literal["state", "region"] = "state",
) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    column = "state_province" if level == "state" else "region"
    route_orders = df.loc[(df["factory"] == factory) & (df[column] == destination)].copy()
    return route_orders.sort_values(["order_date", "ship_date", "order_id"]).reset_index(drop=True)
