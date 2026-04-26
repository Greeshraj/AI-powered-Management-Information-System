# from fastapi import FastAPI, UploadFile, File, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# import pandas as pd
# import io
# from typing import Any

# app = FastAPI(title="Business Analytics API", version="1.0.0")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# REQUIRED_COLUMNS = {"Date", "Region", "Product", "Revenue", "Cost", "Marketing"}


# def validate_dataframe(df: pd.DataFrame) -> None:
#     missing = REQUIRED_COLUMNS - set(df.columns)
#     if missing:
#         raise HTTPException(
#             status_code=422,
#             detail=f"Missing required columns: {', '.join(sorted(missing))}"
#         )


# def parse_dataframe(contents: bytes) -> pd.DataFrame:
#     try:
#         df = pd.read_csv(io.BytesIO(contents))
#     except Exception as e:
#         raise HTTPException(status_code=400, detail=f"Could not parse CSV: {str(e)}")

#     validate_dataframe(df)

#     try:
#         df["Date"] = pd.to_datetime(df["Date"])
#     except Exception:
#         raise HTTPException(status_code=422, detail="Date column could not be parsed as datetime.")

#     for col in ["Revenue", "Cost", "Marketing"]:
#         if not pd.api.types.is_numeric_dtype(df[col]):
#             try:
#                 df[col] = pd.to_numeric(df[col].str.replace(",", ""), errors="raise")
#             except Exception:
#                 raise HTTPException(status_code=422, detail=f"Column '{col}' must contain numeric values.")

#     return df


# def analyze(df: pd.DataFrame) -> dict[str, Any]:
#     total_revenue = df["Revenue"].sum()
#     total_cost = df["Cost"].sum()
#     total_profit = total_revenue - total_cost
#     total_marketing = df["Marketing"].sum()
#     profit_margin = (total_profit / total_revenue * 100) if total_revenue else 0
#     roi = ((total_profit - total_marketing) / total_marketing * 100) if total_marketing else 0

#     top_region = df.groupby("Region")["Revenue"].sum().idxmax()
#     top_product = df.groupby("Product")["Revenue"].sum().idxmax()

#     df["Month"] = df["Date"].dt.to_period("M")
#     monthly = df.groupby("Month")["Revenue"].sum()
#     monthly_revenue = {str(period): round(value, 2) for period, value in monthly.items()}

#     insights = [
#         f"Total Revenue: ${total_revenue:,.2f}",
#         f"Total Cost: ${total_cost:,.2f}",
#         f"Total Profit: ${total_profit:,.2f}",
#         f"Profit Margin: {profit_margin:.1f}%",
#         f"Marketing Spend: ${total_marketing:,.2f}",
#         f"Marketing ROI: {roi:.1f}%",
#         f"Top Region by Revenue: {top_region}",
#         f"Top Product by Revenue: {top_product}",
#         f"Date Range: {df['Date'].min().strftime('%b %d, %Y')} → {df['Date'].max().strftime('%b %d, %Y')}",
#         f"Total Records Analyzed: {len(df):,}",
#     ]

#     return {"insights": insights, "monthly_revenue": monthly_revenue}


# @app.post("/upload")
# async def upload_csv(file: UploadFile = File(...)) -> dict[str, Any]:
#     if not file.filename.endswith(".csv"):
#         raise HTTPException(status_code=400, detail="Only CSV files are accepted.")

#     contents = await file.read()
#     if len(contents) == 0:
#         raise HTTPException(status_code=400, detail="Uploaded file is empty.")

#     df = parse_dataframe(contents)
#     return analyze(df)


# @app.get("/health")
# def health() -> dict[str, str]:
#     return {"status": "ok"}

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np
import io
from typing import Any

app = FastAPI(title="Business Analytics API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

REQUIRED_COLUMNS = {"Date", "Region", "Product", "Revenue", "Cost", "Marketing"}
Z_THRESHOLD = 2.0  # flag if |z-score| >= this value


# ── Validation & Parsing ────────────────────────────────────────────────────

def validate_dataframe(df: pd.DataFrame) -> None:
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise HTTPException(
            status_code=422,
            detail=f"Missing required columns: {', '.join(sorted(missing))}"
        )


def parse_dataframe(contents: bytes) -> pd.DataFrame:
    try:
        df = pd.read_csv(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not parse CSV: {str(e)}")

    validate_dataframe(df)

    try:
        df["Date"] = pd.to_datetime(df["Date"])
    except Exception:
        raise HTTPException(status_code=422, detail="Date column could not be parsed as datetime.")

    for col in ["Revenue", "Cost", "Marketing"]:
        if not pd.api.types.is_numeric_dtype(df[col]):
            try:
                df[col] = pd.to_numeric(df[col].str.replace(",", ""), errors="raise")
            except Exception:
                raise HTTPException(
                    status_code=422,
                    detail=f"Column '{col}' must contain numeric values."
                )

    return df


# ── Core Analysis ───────────────────────────────────────────────────────────

def run_analysis(df: pd.DataFrame) -> dict[str, Any]:
    total_revenue   = df["Revenue"].sum()
    total_cost      = df["Cost"].sum()
    total_profit    = total_revenue - total_cost
    total_marketing = df["Marketing"].sum()
    profit_margin   = (total_profit / total_revenue * 100) if total_revenue else 0
    roi             = ((total_profit - total_marketing) / total_marketing * 100) if total_marketing else 0

    top_region  = df.groupby("Region")["Revenue"].sum().idxmax()
    top_product = df.groupby("Product")["Revenue"].sum().idxmax()

    df["Month"] = df["Date"].dt.to_period("M")
    monthly = df.groupby("Month")["Revenue"].sum()
    monthly_revenue = {str(p): round(v, 2) for p, v in monthly.items()}

    insights = [
        f"Total Revenue: ${total_revenue:,.2f}",
        f"Total Cost: ${total_cost:,.2f}",
        f"Total Profit: ${total_profit:,.2f}",
        f"Profit Margin: {profit_margin:.1f}%",
        f"Marketing Spend: ${total_marketing:,.2f}",
        f"Marketing ROI: {roi:.1f}%",
        f"Top Region by Revenue: {top_region}",
        f"Top Product by Revenue: {top_product}",
        f"Date Range: {df['Date'].min().strftime('%b %d, %Y')} → {df['Date'].max().strftime('%b %d, %Y')}",
        f"Total Records Analyzed: {len(df):,}",
    ]

    return {"insights": insights, "monthly_revenue": monthly_revenue}


# ── Anomaly Detection ───────────────────────────────────────────────────────

def _z_scores(series: pd.Series) -> pd.Series:
    """Return z-scores; return zeros if std is 0 (constant series)."""
    std = series.std()
    if std == 0:
        return pd.Series(0.0, index=series.index)
    return (series - series.mean()) / std


def detect_anomalies(df: pd.DataFrame) -> list[dict]:
    anomalies: list[dict] = []
    df = df.copy()
    df["Month"] = df["Date"].dt.to_period("M")

    # ── Monthly revenue anomalies ──────────────────────────────────────────
    monthly_rev = df.groupby("Month")["Revenue"].sum().reset_index()
    monthly_rev["z"] = _z_scores(monthly_rev["Revenue"])

    for _, row in monthly_rev.iterrows():
        z = row["z"]
        if abs(z) >= Z_THRESHOLD:
            direction = "drop" if z < 0 else "spike"
            label = "Revenue Drop" if z < 0 else "Revenue Spike"
            anomalies.append({
                "type": label,
                "severity": "high" if abs(z) >= 3 else "medium",
                "period": str(row["Month"]),
                "region": "All Regions",
                "value": round(row["Revenue"], 2),
                "z_score": round(z, 2),
                "description": (
                    f"Revenue {direction} in {row['Month']}: "
                    f"${row['Revenue']:,.0f} (z={z:.2f}), "
                    f"significantly {'below' if z < 0 else 'above'} the monthly average."
                ),
            })

    # ── Per-region revenue anomalies ───────────────────────────────────────
    for region, grp in df.groupby("Region"):
        region_monthly = grp.groupby("Month")["Revenue"].sum().reset_index()
        if len(region_monthly) < 2:
            continue
        region_monthly["z"] = _z_scores(region_monthly["Revenue"])
        for _, row in region_monthly.iterrows():
            z = row["z"]
            if abs(z) >= Z_THRESHOLD:
                direction = "drop" if z < 0 else "spike"
                label = "Revenue Drop" if z < 0 else "Revenue Spike"
                anomalies.append({
                    "type": label,
                    "severity": "high" if abs(z) >= 3 else "medium",
                    "period": str(row["Month"]),
                    "region": region,
                    "value": round(row["Revenue"], 2),
                    "z_score": round(z, 2),
                    "description": (
                        f"{region} revenue {direction} in {row['Month']}: "
                        f"${row['Revenue']:,.0f} (z={z:.2f}) compared to that region's average."
                    ),
                })

    # ── Marketing spend anomalies ──────────────────────────────────────────
    monthly_mkt = df.groupby("Month")["Marketing"].sum().reset_index()
    monthly_mkt["z"] = _z_scores(monthly_mkt["Marketing"])

    for _, row in monthly_mkt.iterrows():
        z = row["z"]
        if z >= Z_THRESHOLD:          # only flag unusual spikes (over-spend)
            anomalies.append({
                "type": "Marketing Spike",
                "severity": "high" if z >= 3 else "medium",
                "period": str(row["Month"]),
                "region": "All Regions",
                "value": round(row["Marketing"], 2),
                "z_score": round(z, 2),
                "description": (
                    f"Unusually high marketing spend in {row['Month']}: "
                    f"${row['Marketing']:,.0f} (z={z:.2f}). "
                    "Review campaign ROI for this period."
                ),
            })

    return anomalies


# ── Recommendation Engine ───────────────────────────────────────────────────

def generate_recommendations(df: pd.DataFrame) -> list[dict]:
    recs: list[dict] = []
    df = df.copy()
    df["Month"]  = df["Date"].dt.to_period("M")
    df["Profit"] = df["Revenue"] - df["Cost"]

    # Global efficiency ratio
    global_avg_rev = df["Revenue"].mean()
    global_avg_mkt = df["Marketing"].mean()

    # ── 1. Per-region trend analysis ───────────────────────────────────────
    region_stats = (
        df.groupby("Region")
        .agg(total_revenue=("Revenue", "sum"),
             total_marketing=("Marketing", "sum"),
             avg_revenue=("Revenue", "mean"),
             avg_marketing=("Marketing", "mean"),
             total_profit=("Profit", "sum"))
        .reset_index()
    )

    overall_avg_revenue    = region_stats["avg_revenue"].mean()
    overall_avg_marketing  = region_stats["avg_marketing"].mean()

    for _, r in region_stats.iterrows():
        rev_ratio = r["avg_revenue"]  / overall_avg_revenue   if overall_avg_revenue   else 0
        mkt_ratio = r["avg_marketing"] / overall_avg_marketing if overall_avg_marketing else 0
        mkt_eff   = r["total_revenue"] / r["total_marketing"]  if r["total_marketing"]  else 0

        # Under-performing region (revenue well below average)
        if rev_ratio < 0.75:
            recs.append({
                "type": "Region Strategy",
                "priority": "high",
                "region": r["Region"],
                "title": f"Underperforming Region: {r['Region']}",
                "description": (
                    f"{r['Region']} generates only {rev_ratio:.0%} of the average regional revenue. "
                    "Consider focused promotions, revised pricing, or product-mix adjustments."
                ),
                "action": "Focus promotions or pricing strategy in this region",
            })

        # Low marketing → low revenue: needs more investment
        if mkt_ratio < 0.85 and rev_ratio < 0.85:
            recs.append({
                "type": "Marketing Investment",
                "priority": "high",
                "region": r["Region"],
                "title": f"Increase Marketing: {r['Region']}",
                "description": (
                    f"Both revenue and marketing spend are below average in {r['Region']} "
                    f"({rev_ratio:.0%} and {mkt_ratio:.0%} of average). "
                    "Increasing marketing investment may unlock growth."
                ),
                "action": "Increase marketing budget in this region",
            })

        # High marketing → low revenue: inefficient campaigns
        elif mkt_ratio > 1.15 and rev_ratio < 1.0:
            recs.append({
                "type": "Campaign Efficiency",
                "priority": "medium",
                "region": r["Region"],
                "title": f"Inefficient Marketing: {r['Region']}",
                "description": (
                    f"{r['Region']} spends {mkt_ratio:.0%} of the average on marketing "
                    f"but achieves only {rev_ratio:.0%} of average revenue (ROI: ${mkt_eff:.1f}/$ spent). "
                    "Audit and optimise campaign targeting."
                ),
                "action": "Marketing inefficient — optimize campaigns",
            })

        # Strong performer: positive reinforcement
        if rev_ratio > 1.3:
            recs.append({
                "type": "Scale Success",
                "priority": "low",
                "region": r["Region"],
                "title": f"Scale Winning Strategy: {r['Region']}",
                "description": (
                    f"{r['Region']} outperforms the average by {(rev_ratio - 1):.0%}. "
                    "Replicate its product mix, pricing, or campaigns in other regions."
                ),
                "action": "Replicate this region's strategy elsewhere",
            })

    # ── 2. Monthly trend: consecutive decline ──────────────────────────────
    monthly_rev = (
        df.groupby("Month")["Revenue"].sum()
        .reset_index()
        .sort_values("Month")
    )
    if len(monthly_rev) >= 3:
        values = monthly_rev["Revenue"].tolist()
        periods = monthly_rev["Month"].tolist()
        for i in range(2, len(values)):
            if values[i] < values[i - 1] < values[i - 2]:
                recs.append({
                    "type": "Revenue Trend",
                    "priority": "high",
                    "region": "All Regions",
                    "title": "3-Month Revenue Decline",
                    "description": (
                        f"Revenue has fallen for three consecutive months ending {periods[i]}. "
                        "Investigate demand shifts, competitive pressure, or seasonal factors."
                    ),
                    "action": "Investigate root cause and activate retention campaigns",
                })
                break  # report once

    # ── 3. Overall marketing efficiency ───────────────────────────────────
    total_rev = df["Revenue"].sum()
    total_mkt = df["Marketing"].sum()
    if total_mkt > 0:
        global_mkt_eff = total_rev / total_mkt
        if global_mkt_eff < 3.0:
            recs.append({
                "type": "Campaign Efficiency",
                "priority": "medium",
                "region": "All Regions",
                "title": "Low Overall Marketing ROI",
                "description": (
                    f"Every $1 spent on marketing yields only ${global_mkt_eff:.2f} in revenue globally. "
                    "Review channel mix, audience targeting, and creative assets."
                ),
                "action": "Audit global marketing strategy",
            })

    # Deduplicate by (title, region)
    seen: set[tuple] = set()
    unique_recs = []
    for r in recs:
        key = (r["title"], r["region"])
        if key not in seen:
            seen.add(key)
            unique_recs.append(r)

    # Sort: high → medium → low
    priority_order = {"high": 0, "medium": 1, "low": 2}
    unique_recs.sort(key=lambda x: priority_order.get(x["priority"], 9))

    return unique_recs


# ── API Endpoints ───────────────────────────────────────────────────────────

@app.post("/upload")
async def upload_csv(file: UploadFile = File(...)) -> dict[str, Any]:
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted.")

    contents = await file.read()
    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    df = parse_dataframe(contents)

    result = run_analysis(df)
    result["anomalies"]       = detect_anomalies(df)
    result["recommendations"] = generate_recommendations(df)

    return result


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": "2.0.0"}