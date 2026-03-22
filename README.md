# Nassau Candy Shipping Route Efficiency Analysis

This project delivers a complete VS Code-ready Streamlit analysis for Nassau Candy Distributor's factory-to-customer shipping performance. It combines route benchmarking, geographic bottleneck analysis, ship mode comparison, and route-level drill-down views in one dashboard.

The project uses the provided Nassau Candy shipment file and the factory/product correlation supplied in the brief. The raw dataset is already included at `data/raw/Nassau Candy Distributor.csv`.

## What is included

- `app.py`: Streamlit dashboard with overview, map, ship mode, and drill-down modules.
- `src/data_pipeline.py`: cleaning, feature engineering, KPI, and aggregation logic.
- `src/visuals.py`: Plotly visual builders.
- `docs/research_paper.md`: analytical write-up with findings and recommendations.
- `docs/executive_summary.md`: short stakeholder summary.

## Quick start

1. Open this folder in VS Code.
2. Create and activate a virtual environment.
3. Install dependencies:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

4. Launch the dashboard:

```powershell
streamlit run app.py
```

## Dashboard features

- Route efficiency leaderboard for factory-to-state and factory-to-region views
- US state heatmaps for lead time and bottleneck intensity
- Ship mode comparison with region heatmap and lead-time distribution
- Route drill-down with order-level timelines and shipment detail
- Interactive filters for date range, geography, ship mode, and delay threshold

## Data notes

- Source records: 10,194 shipments
- Coverage: 9,994 US shipments and 200 Canadian shipments
- Order dates: 2024-01-02 to 2025-12-31
- Ship dates: 2026-06-30 to 2030-06-28
- Mean lead time in the file: 1,320.84 days

The ship dates are much later than the order dates, so the dashboard treats lead time primarily as a comparative benchmarking metric. The app surfaces this warning directly so the user can interpret the results responsibly.

## Project structure

```text
.
|-- app.py
|-- requirements.txt
|-- data
|   |-- raw
|   |   `-- Nassau Candy Distributor.csv
|   `-- reference
|       |-- factories.csv
|       `-- product_factory_mapping.csv
|-- docs
|   |-- executive_summary.md
|   `-- research_paper.md
`-- src
    |-- __init__.py
    |-- config.py
    |-- data_pipeline.py
    `-- visuals.py
```
