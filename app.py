import streamlit as st
import pandas as pd

st.set_page_config(page_title="Order Search", layout="wide")
st.title("🔎 Order Search by Customer Name")

@st.cache_data
def load_data(path="orders.csv"):
    df = pd.read_csv(path)
    df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
    # helpful derived column
    df["order_value"] = df["quantity"] * df["unit_price"]
    return df

df = load_data()

st.sidebar.header("Search")
query = st.sidebar.text_input("Customer name", placeholder="e.g., Neha or Aarav")
status_filter = st.sidebar.multiselect("Status (optional)", sorted(df["status"].unique()))
city_filter = st.sidebar.multiselect("City (optional)", sorted(df["city"].unique()))

filtered = df.copy()

# Name search (partial + case-insensitive)
if query.strip():
    filtered = filtered[filtered["customer_name"].str.contains(query, case=False, na=False)]

# Optional filters
if status_filter:
    filtered = filtered[filtered["status"].isin(status_filter)]
if city_filter:
    filtered = filtered[filtered["city"].isin(city_filter)]

# Summary
col1, col2, col3 = st.columns(3)
col1.metric("Matching orders", len(filtered))
col2.metric("Unique customers", filtered["customer_name"].nunique() if len(filtered) else 0)
col3.metric("Total value", f"₹{filtered['order_value'].sum():,.0f}" if len(filtered) else "₹0")

st.subheader("Results")
st.dataframe(
    filtered.sort_values(["order_date", "order_id"], ascending=[False, False]),
    use_container_width=True
)

# Optional: download filtered results
st.download_button(
    "Download results as CSV",
    data=filtered.to_csv(index=False).encode("utf-8"),
    file_name="filtered_orders.csv",
    mime="text/csv",
    disabled=len(filtered) == 0,
)


