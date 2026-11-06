import streamlit as st
import pandas as pd

# Set page configuration
st.set_page_config(
    page_title="Sales Performance and Customer Insight",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_data
def load_data():
    df = pd.read_csv('fact_sales.csv')
    # Calculate revenue incorporating discounts
    df['revenue'] = df['quantity'] * df['unit_price_at_purchase'] * (1 - df['discount_pct'])
    df['order_datetime'] = pd.to_datetime(df['order_datetime'])
    df['year_month'] = df['order_datetime'].dt.to_period('M').astype(str)
    return df

df = load_data()

# Sidebar Filters
st.sidebar.title("🔍 Filters")

min_date = df['order_datetime'].min().date()
max_date = df['order_datetime'].max().date()

date_range = st.sidebar.date_input("Date Range", [min_date, max_date], min_value=min_date, max_value=max_date)
if len(date_range) == 2:
    start_date, end_date = date_range
    filtered_df = df[(df['order_datetime'].dt.date >= start_date) & (df['order_datetime'].dt.date <= end_date)]
else:
    filtered_df = df.copy()

categories = ['All'] + sorted(list(filtered_df['category'].dropna().unique()))
selected_category = st.sidebar.selectbox("Category", categories)
if selected_category != 'All':
    filtered_df = filtered_df[filtered_df['category'] == selected_category]

statuses = ['All'] + sorted(list(filtered_df['order_status'].dropna().unique()))
selected_status = st.sidebar.selectbox("Order Status", statuses)
if selected_status != 'All':
    filtered_df = filtered_df[filtered_df['order_status'] == selected_status]

# Header
st.title("🇵🇭 Fact Sales Executive Dashboard")
st.caption("Native Streamlit Implementation | All values in Philippine Peso (₱)")
st.divider()

# Core KPI Computations
total_revenue = filtered_df['revenue'].sum()
total_orders = filtered_df['order_id'].nunique()
aov = total_revenue / total_orders if total_orders > 0 else 0.0

# Customer Repeat Analysis
customer_order_counts = filtered_df.groupby('customer_id')['order_id'].nunique()
repeat_customers = (customer_order_counts > 1).sum()
new_customers = (customer_order_counts == 1).sum()
total_customers = customer_order_counts.nunique()
repeat_rate = (repeat_customers / total_customers * 100) if total_customers > 0 else 0.0

customer_revenue = filtered_df.groupby('customer_id').agg(
    total_spend=('revenue', 'sum'),
    order_count=('order_id', 'nunique')
).reset_index()
customer_revenue['customer_type'] = customer_revenue['order_count'].apply(lambda x: 'Repeat' if x > 1 else 'New')

repeat_rev = customer_revenue[customer_revenue['customer_type'] == 'Repeat']['total_spend'].sum()
new_rev = customer_revenue[customer_revenue['customer_type'] == 'New']['total_spend'].sum()

# Top Aggregations
top_category = filtered_df.groupby('category')['revenue'].sum().idxmax() if not filtered_df.empty else "N/A"
top_city = filtered_df.groupby('city')['revenue'].sum().idxmax() if not filtered_df.empty else "N/A"

# Row 1: Primary KPIs
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Total Revenue", f"₱{total_revenue:,.2f}")
kpi2.metric("Total Orders", f"{total_orders:,}")
kpi3.metric("Average Order Value (AOV)", f"₱{aov:,.2f}")
kpi4.metric("Top Category / City", f"{top_category}", delta=top_city, delta_color="normal")

# Row 2: Customer Breakdown KPIs
kpi5, kpi6, kpi7 = st.columns(3)
kpi5.metric("Repeat vs. New Customers", f"{repeat_customers:,} / {new_customers:,}", f"{repeat_rate:.1f}% Repeat Rate")
kpi6.metric("Repeat Customer Revenue", f"₱{repeat_rev:,.2f}", f"{(repeat_rev/total_revenue*100 if total_revenue>0 else 0):.1f}% of Total")
kpi7.metric("New Customer Revenue", f"₱{new_rev:,.2f}", f"{(new_rev/total_revenue*100 if total_revenue>0 else 0):.1f}% of Total")

st.divider()

# 1. Monthly Revenue Line Chart (Native Streamlit st.line_chart)
st.subheader("📈 Monthly Revenue Trend")
monthly_rev = filtered_df.groupby('year_month')['revenue'].sum().reset_index()
monthly_chart_data = monthly_rev.set_index('year_month')['revenue']
st.line_chart(monthly_chart_data, y_label="Revenue (₱)", x_label="Month")

# Row 3: Product and Category Charts (Native Streamlit st.bar_chart)
col1, col2 = st.columns(2)

with col1:
    st.subheader("🏆 Top 10 Products by Revenue")
    top_products = filtered_df.groupby('product_name')['revenue'].sum().reset_index().sort_values(by='revenue', ascending=False).head(10)
    top_prod_chart = top_products.set_index('product_name')['revenue']
    st.bar_chart(top_prod_chart, x_label="Product Name", y_label="Revenue (₱)")

with col2:
    st.subheader("📦 Revenue by Category")
    cat_rev = filtered_df.groupby('category')['revenue'].sum().reset_index().sort_values(by='revenue', ascending=False)
    cat_chart = cat_rev.set_index('category')['revenue']
    st.bar_chart(cat_chart, x_label="Category", y_label="Revenue (₱)")

# Row 4: City Chart & Customer Spend Distribution
col3, col4 = st.columns(2)

with col3:
    st.subheader("🏙️ Top 10 Revenue by Region City")
    city_rev = filtered_df.groupby('city')['revenue'].sum().reset_index().sort_values(by='revenue', ascending=False).head(10)
    city_chart = city_rev.set_index('city')['revenue']
    st.bar_chart(city_chart, x_label="City", y_label="Revenue (₱)")

with col4:
    st.subheader("👥 Customer Spend Distribution Histogram")
    # Native Streamlit histogram representation using pd.cut binning displayed via st.bar_chart
    spend_bins = pd.cut(customer_revenue['total_spend'], bins=15)
    spend_dist = spend_bins.value_counts().sort_index().reset_index()
    spend_dist.columns = ['Spend Range (₱)', 'Customer Count']
    spend_dist['Spend Range (₱)'] = spend_dist['Spend Range (₱)'].astype(str)
    hist_chart = spend_dist.set_index('Spend Range (₱)')['Customer Count']
    st.bar_chart(hist_chart, x_label="Spend Range (₱)", y_label="Customer Count")
