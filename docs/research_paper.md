# Factory-to-Customer Shipping Route Efficiency Analysis for Nassau Candy Distributor

## 1. Introduction

Nassau Candy Distributor ships products from a distributed factory network to customers across multiple customer regions. In this environment, route efficiency affects customer experience, transportation cost, and the distributor's ability to scale. This project translates the provided shipment dataset into route-level performance intelligence through cleaning, feature engineering, route aggregation, bottleneck detection, and dashboard design.

## 2. Business Problem

The company currently lacks a route-centric view of shipping performance. Without clear visibility into efficient versus inefficient lanes, logistics decisions remain reactive. The analytical goal was to identify:

- Which factory-to-customer routes are consistently efficient
- Which routes are most delay-prone
- How performance changes across regions, states, and ship modes
- Where geographic bottlenecks are concentrated

## 3. Dataset Overview

- Source file: Nassau Candy Distributor.csv
- Records analyzed: 10,194
- Countries represented: United States (9,994 rows) and Canada (200 rows)
- Product count: 15 unique products
- Factories represented after product mapping: 5
- Order date range: 2024-01-02 to 2025-12-31
- Ship date range: 2026-06-30 to 2030-06-28
- Mean lead time: 1,320.84 days
- Delay benchmark used in the dashboard: 75th percentile lead time = 1,638 days

## 4. Data Cleaning and Validation

The cleaning layer applied the following rules:

1. Parsed `Order Date` and `Ship Date` using day-first date formatting.
2. Standardized categorical fields such as region, state/province, ship mode, and product name.
3. Converted sales, units, cost, and gross profit to numeric fields.
4. Derived factory location from the provided product-to-factory correlation.
5. Calculated shipping lead time as `Ship Date - Order Date`.
6. Removed records with missing dates, missing factory mappings, or negative lead times.

The dataset passed the structural validation checks: there were no missing ship dates, no negative lead times, and no unmapped products. However, a major analytical limitation remained: the ship-date range is far later than the order-date range, which produces unrealistically high absolute lead times. Because of that, the analysis focuses on comparative route efficiency rather than literal transit duration.

## 5. Feature Engineering

The project engineered the following fields:

- `shipping_lead_time_days`
- `factory`
- `route_to_state`
- `route_to_region`
- `is_us_destination`
- `order_month`
- `ship_month`
- `delay_flag` using a configurable lead-time threshold
- `route_efficiency_score` based on normalized inverse lead time

Each route was analyzed at two granularities:

- Factory -> State / Province
- Factory -> Region

## 6. Analytical Methodology

### 6.1 Route Aggregation

For each route, the analysis calculated:

- Total shipments
- Average lead time
- Lead-time variability
- Delay frequency
- Sales and gross profit contribution

### 6.2 Efficiency Benchmarking

Routes were ranked from fastest to slowest using average lead time. A normalized efficiency score converted route averages into a 0-100 scale for easier dashboard comparison.

### 6.3 Geographic Bottleneck Analysis

State and regional aggregates were evaluated using:

- Average lead time
- Shipment volume
- Delay frequency
- A composite bottleneck score combining lead time, volume, and delay rate

### 6.4 Ship Mode Analysis

Ship modes were compared on:

- Average lead time
- Lead-time spread
- Delay frequency
- Revenue contribution

## 7. Key Findings

### 7.1 Route network shape

- 196 factory-to-state routes were observed
- 20 factory-to-region routes were observed
- Lot's O' Nuts handled the highest shipment volume with 5,692 orders
- Wicked Choccy's followed with 4,152 orders

This indicates that most route exposure is concentrated in the chocolate network rather than the smaller "Other" and sugar product lanes.

### 7.2 Most efficient high-volume routes

Among routes with at least 50 shipments, the strongest performers were:

1. Lot's O' Nuts -> Virginia: 1,229.49 days
2. Wicked Choccy's -> Virginia: 1,238.88 days
3. Lot's O' Nuts -> Oregon: 1,245.19 days
4. Wicked Choccy's -> Michigan: 1,291.85 days
5. Lot's O' Nuts -> Massachusetts: 1,292.12 days

These lanes provide candidates for best-practice benchmarking once the source dates are validated.

### 7.3 Highest-risk high-volume routes

Among routes with at least 50 shipments, the weakest performers were:

1. Wicked Choccy's -> Indiana: 1,402.46 days
2. Wicked Choccy's -> Tennessee: 1,393.76 days
3. Lot's O' Nuts -> Tennessee: 1,390.96 days
4. Wicked Choccy's -> Washington: 1,375.72 days
5. Lot's O' Nuts -> Maryland: 1,370.67 days

These are the most likely candidates for operational review because poor performance overlaps with meaningful volume.

### 7.4 Geographic bottlenecks

At the region level, performance differences were modest but still directional:

- Gulf: 1,311.37 days
- Pacific: 1,322.19 days
- Atlantic: 1,322.75 days
- Interior: 1,323.09 days

The Gulf region emerged as the best-performing region in this dataset, while Interior was the weakest. At the state level, high-latency areas included West Virginia, North Dakota, Iowa, New Mexico, Tennessee, and Washington, though several of the worst states have very low shipment counts and should not be prioritized ahead of higher-volume lanes.

### 7.5 Ship mode behavior

Expected service-tier behavior was not present:

- Standard Class: 1,314.33 days average lead time
- Second Class: 1,323.85 days
- Same Day: 1,333.44 days
- First Class: 1,338.28 days

This inversion suggests either label quality issues, date quality issues, or both. The ship-mode findings are still useful as anomaly flags, but they should not be interpreted as evidence that premium shipping is slower in real operations.

## 8. Dashboard Design

The Streamlit dashboard includes four modules:

1. Route Efficiency Overview
2. Geographic Shipping Map
3. Ship Mode Comparison
4. Route Drill-Down

Interactive controls allow the user to filter by order date range, country/region, customer region, state/province, ship mode, and delay threshold. The interface is built for live analytics rather than static reporting, making it suitable for executive review and operational follow-up.

## 9. Recommendations

1. Correct and revalidate the shipment calendar fields before using this data for SLA management.
2. Investigate the Indiana and Tennessee lanes first, especially for Wicked Choccy's and Lot's O' Nuts.
3. Separate low-volume outliers from high-volume bottlenecks in decision-making to avoid chasing noise.
4. Track ship mode behavior after date correction to confirm whether service-tier prioritization is functioning properly.
5. Extend the dashboard with actual transportation cost, carrier, and warehouse handoff timestamps when available.

## 10. Conclusion

This project converts a raw shipment table into a practical route-efficiency monitoring system for Nassau Candy Distributor. Although the source dates create a limitation on absolute transit-time interpretation, the analysis still exposes relative route strengths, geographic bottlenecks, and service-mode anomalies. With corrected dates and continued dashboard use, Nassau Candy can move from reactive logistics management to a more targeted, evidence-driven operating model.
