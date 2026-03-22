# Executive Summary

## Objective

This project converts Nassau Candy Distributor's shipment history into route-level logistics intelligence so leadership can identify efficient factory-to-customer lanes, isolate recurring delay patterns, and target operational bottlenecks with evidence rather than reaction.

## Scope

- 10,194 shipment records analyzed
- 5 factories mapped from the provided product-to-factory correlation
- 196 factory-to-state routes and 20 factory-to-region routes evaluated
- Coverage includes 9,994 US shipments and 200 Canadian shipments

## Headline findings

1. The dataset is operationally rich but contains a major date anomaly. Order dates span 2024-01-02 through 2025-12-31, while ship dates span 2026-06-30 through 2030-06-28. As a result, the lead-time values are best used for comparative benchmarking, not literal service-level measurement.
2. Even with the date anomaly, route comparisons are still informative. High-volume efficient lanes include Lot's O' Nuts -> Virginia at 1,229.49 days, Wicked Choccy's -> Virginia at 1,238.88 days, and Lot's O' Nuts -> Oregon at 1,245.19 days.
3. The most concerning high-volume routes are concentrated in a few state lanes. Wicked Choccy's -> Indiana averages 1,402.46 days, Wicked Choccy's -> Tennessee averages 1,393.76 days, and Lot's O' Nuts -> Tennessee averages 1,390.96 days.
4. Region-level performance is relatively close, but Gulf is the strongest region at 1,311.37 days average lead time, while Interior is the weakest at 1,323.09 days.
5. Ship mode results do not follow the expected operational hierarchy. Standard Class averages 1,314.33 days, Second Class 1,323.85 days, Same Day 1,333.44 days, and First Class 1,338.28 days. This suggests the underlying dates or service labels should be validated before drawing policy conclusions.

## Recommended actions

1. Validate the shipment calendar fields with the source system before using this dataset for SLA or budgeting decisions.
2. Prioritize route reviews for Indiana, Tennessee, Washington, Maryland, and Wisconsin lanes where volume and poor performance overlap.
3. Keep Canadian provinces separate from the US heatmap and route targeting process.
4. Use the Streamlit dashboard as the operational front end for continuous monitoring once the date issue is corrected.

## Deliverable value

The final dashboard gives stakeholders an interactive way to filter by date, geography, and ship mode, compare efficient versus inefficient routes, and drill into route-specific order timelines. That creates a strong foundation for future logistics optimization, service-level monitoring, and route redesign.
