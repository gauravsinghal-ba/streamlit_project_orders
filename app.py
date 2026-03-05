import streamlit as st
import pandas as pd

st.set_page_config(page_title="Order Search", layout="wide")
st.title("🔎 Order Search by Customer Name")

@st.cache_data
def load_data(path="orders.csv"):
    df = pd.read_csv(path)

    # Defensive conversions (prevents common CSV issues)
    if "order_date" in df.columns:
        df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")

    for c in ["quantity", "unit_price"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    if set(["quantity", "unit_price"]).issubset(df.columns):
        df["order_value"] = df["quantity"].fillna(0) * df["unit_price"].fillna(0)
    else:
        df["order_value"] = 0

    return df

df = load_data()

# -------- Sidebar filters --------
st.sidebar.header("Search & Filters")

query = st.sidebar.text_input("Customer name", placeholder="e.g., Neha or Aarav")

status_options = sorted(df["status"].dropna().unique()) if "status" in df.columns else []
city_options = sorted(df["city"].dropna().unique()) if "city" in df.columns else []

status_filter = st.sidebar.multiselect("Status (optional)", status_options)
city_filter = st.sidebar.multiselect("City (optional)", city_options)

# Date filter (optional, only if order_date exists)
if "order_date" in df.columns and df["order_date"].notna().any():
    min_date = df["order_date"].min().date()
    max_date = df["order_date"].max().date()
    date_range = st.sidebar.date_input("Order date range", (min_date, max_date))
else:
    date_range = None

# -------- Apply filters --------
filtered = df.copy()

# Name search (partial + case-insensitive)
if "customer_name" in filtered.columns and query.strip():
    name_series = filtered["customer_name"].astype(str)
    filtered = filtered[name_series.str.contains(query, case=False, na=False)]

if status_filter and "status" in filtered.columns:
    filtered = filtered[filtered["status"].isin(status_filter)]

if city_filter and "city" in filtered.columns:
    filtered = filtered[filtered["city"].isin(city_filter)]

if date_range and "order_date" in filtered.columns:
    start, end = date_range
    filtered = filtered[
        (filtered["order_date"].dt.date >= start) & (filtered["order_date"].dt.date <= end)
    ]

# -------- Summary metrics --------
col1, col2, col3, col4 = st.columns(4)
col1.metric("Matching orders", len(filtered))
col2.metric("Unique customers", int(filtered["customer_name"].nunique()) if "customer_name" in filtered.columns and len(filtered) else 0)
col3.metric("Total value", f"₹{filtered['order_value'].sum():,.0f}" if len(filtered) else "₹0")
col4.metric("Avg order value", f"₹{filtered['order_value'].mean():,.0f}" if len(filtered) else "₹0")

st.divider()

# -------- Charts --------
st.subheader("Charts")

c1, c2 = st.columns(2)

# 1) Revenue/Order Value trend over time
with c1:
    st.markdown("**Order Value Over Time**")
    if "order_date" in filtered.columns and filtered["order_date"].notna().any():
        trend = (
            filtered.dropna(subset=["order_date"])
            .groupby(pd.Grouper(key="order_date", freq="D"))["order_value"]
            .sum()
            .reset_index()
            .sort_values("order_date")
        )
        if len(trend):
            st.line_chart(trend.set_index("order_date")["order_value"])
        else:
            st.info("Not enough valid dates to plot a trend.")
    else:
        st.info("`order_date` missing or empty in data.")

# 2) Status breakdown
with c2:
    st.markdown("**Orders by Status**")
    if "status" in filtered.columns and len(filtered):
        status_counts = filtered["status"].fillna("Unknown").value_counts().reset_index()
        status_counts.columns = ["status", "count"]
        st.bar_chart(status_counts.set_index("status")["count"])
    else:
        st.info("`status` missing or no rows after filters.")

c3, c4 = st.columns(2)

# 3) Top cities by total order value
with c3:
    st.markdown("**Top Cities by Total Value**")
    if "city" in filtered.columns and len(filtered):
        city_value = (
            filtered["city"].fillna("Unknown")
            .to_frame()
            .join(filtered["order_value"])
            .groupby("city")["order_value"]
            .sum()
            .sort_values(ascending=False)
            .head(10)
        )
        st.bar_chart(city_value)
    else:
        st.info("`city` missing or no rows after filters.")

# 4) Distribution of order values
with c4:
    st.markdown("**Order Value Distribution**")
    if len(filtered) and "order_value" in filtered.columns:
        vals = pd.to_numeric(filtered["order_value"], errors="coerce").fillna(0)

        bins = pd.cut(vals, bins=10)
        hist = bins.value_counts().sort_index()

        hist_df = hist.reset_index()
        hist_df.columns = ["bucket", "count"]
        hist_df["bucket"] = hist_df["bucket"].astype(str)  # <-- key fix

        st.bar_chart(hist_df, x="bucket", y="count")
    else:
        st.info("No values to plot.")

st.divider()

# -------- Results table --------
st.subheader("Results")
sort_cols = [c for c in ["order_date", "order_id"] if c in filtered.columns]
if sort_cols:
    filtered_view = filtered.sort_values(sort_cols, ascending=[False] * len(sort_cols))
else:
    filtered_view = filtered

st.dataframe(filtered_view, use_container_width=True)

# -------- Download --------
st.download_button(
    "Download results as CSV",
    data=filtered.to_csv(index=False).encode("utf-8"),
    file_name="filtered_orders.csv",
    mime="text/csv",
    disabled=len(filtered) == 0,
)
