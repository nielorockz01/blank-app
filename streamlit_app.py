import streamlit as st
import pandas as pd
import numpy as np

# Page Configuration
st.set_page_config(
    page_title="Sales Performance & Customer Insight",
    page_icon="📊",
    layout="wide"
)

# Load and Cache Data
@st.cache_data
def load_data():
    df = pd.read_csv("fact_sales.csv")
    df['order_datetime'] = pd.to_datetime(df['order_datetime'])
    df['year_month'] = df['order_datetime'].dt.to_period('M').astype(str)
    return df

df = load_data()

# Dashboard Header
st.title("📊 Sales Performance and Customer Insight Dashboard")
st.markdown("Comprehensive analytics tracking revenue, orders, product performance, regional distribution, and customer purchasing behavior in **Philippine Peso (₱)** using native Streamlit charts.")

# ================= Sidebar Filters =================
st.sidebar.header("🔍 Filter Controls")

min_date = df['order_datetime'].min().date()
max_date = df['order_datetime'].max().date()

date_range = st.sidebar.date_input(
    "Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

regions = ["All"] + sorted(df['region_name'].unique().tolist())
selected_region = st.sidebar.selectbox("Region", regions)

categories = ["All"] + sorted(df['category'].unique().tolist())
selected_category = st.sidebar.selectbox("Category", categories)

# Apply Filter Logic
filtered_df = df.copy()
if len(date_range) == 2:
    start_date, end_date = date_range
    filtered_df = filtered_df[
        (filtered_df['order_datetime'].dt.date >= start_date) & 
        (filtered_df['order_datetime'].dt.date <= end_date)
    ]

if selected_region != "All":
    filtered_df = filtered_df[filtered_df['region_name'] == selected_region]

if selected_category != "All":
    filtered_df = filtered_df[filtered_df['category'] == selected_category]

if filtered_df.empty:
    st.warning("No data available for the selected filter criteria.")
else:
    # ================= KPI Calculations =================
    total_revenue = filtered_df['total_revenue'].sum()
    total_orders = filtered_df['order_id'].nunique()
    aov = total_revenue / total_orders if total_orders > 0 else 0
    total_customers = filtered_df['customer_id'].nunique()

    cust_order_counts = filtered_df.groupby('customer_id')['order_id'].nunique()
    repeat_customers = (cust_order_counts > 1).sum()
    new_customers = (cust_order_counts == 1).sum()

    # Top KPI Metric Cards
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Revenue", f"₱{total_revenue:,.2f}")
    col2.metric("Total Orders", f"{total_orders:,}")
    col3.metric("Avg Order Value (AOV)", f"₱{aov:,.2f}")
    col4.metric("Active Customers", f"{total_customers:,}")
    col5.metric("Repeat / New Cust", f"{repeat_customers:,} / {new_customers:,}")

    st.markdown("---")

    # ================= Row 1: Monthly Revenue Trend & Revenue by Category =================
    r1_col1, r1_col2 = st.columns(2)

    with r1_col1:
        st.subheader("📈 Monthly Revenue Trend")
        monthly_rev = filtered_df.groupby('year_month')['total_revenue'].sum().reset_index()
        monthly_rev = monthly_rev.set_index('year_month')
        st.line_chart(monthly_rev)

    with r1_col2:
        st.subheader("🏷️ Revenue by Category")
        cat_rev = filtered_df.groupby('category')['total_revenue'].sum().reset_index()
        cat_rev = cat_rev.set_index('category')
        st.bar_chart(cat_rev)

    # ================= Row 2: Top 10 Products & Revenue by City =================
    r2_col1, r2_col2 = st.columns(2)

    with r2_col1:
        st.subheader("🏆 Top 10 Products by Revenue")
        top_products = filtered_df.groupby('product_name')['total_revenue'].sum().reset_index()
        top_products = top_products.sort_values(by='total_revenue', ascending=False).head(10)
        top_products = top_products.set_index('product_name')
        st.bar_chart(top_products)

    with r2_col2:
        st.subheader("🏙️ Revenue by City (Top 15)")
        city_rev = filtered_df.groupby('city')['total_revenue'].sum().reset_index()
        city_rev = city_rev.sort_values(by='total_revenue', ascending=False).head(15)
        city_rev = city_rev.set_index('city')
        st.bar_chart(city_rev)

    # ================= Row 3: Customer Spend Distribution & Repeat vs New =================
    r3_col1, r3_col2 = st.columns(2)

    with r3_col1:
        st.subheader("👥 Customer Spend Distribution Histogram")
        cust_spend = filtered_df.groupby('customer_id')['total_revenue'].sum().reset_index()
        counts, bin_edges = np.histogram(cust_spend['total_revenue'], bins=20)
        bin_labels = [f"₱{int(bin_edges[i]):,} - ₱{int(bin_edges[i+1]):,}" for i in range(len(bin_edges)-1)]
        hist_df = pd.DataFrame({"Customer Count": counts}, index=bin_labels)
        st.bar_chart(hist_df)

    with r3_col2:
        st.subheader("🔄 Repeat vs. New Customer Revenue")
        customer_orders = filtered_df.groupby('customer_id').agg(
            total_orders=('order_id', 'nunique'),
            customer_revenue=('total_revenue', 'sum')
        ).reset_index()
        
        customer_orders['customer_type'] = customer_orders['total_orders'].apply(lambda x: 'Repeat Customer' if x > 1 else 'New Customer')
        cust_type_rev = customer_orders.groupby('customer_type')['customer_revenue'].sum().reset_index()
        cust_type_rev = cust_type_rev.set_index('customer_type')
        st.bar_chart(cust_type_rev)
