import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Sales Performance & Customer Insight",
    page_icon="📊",
    layout="wide"
)

@st.cache_data
def load_data():
    df = pd.read_csv("fact_sales.csv")
    df['order_datetime'] = pd.to_datetime(df['order_datetime'])
    df['year_month'] = df['order_datetime'].dt.to_period('M').astype(str)
    return df

df = load_data()

st.title("📊 Sales Performance and Customer Insight Dashboard")
st.markdown("Comprehensive analytics dashboard tracking Philippine Peso (₱) revenue, orders, product performance, and customer behavior.")

# Sidebar Filters
st.sidebar.header("Filter Controls")

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

# Apply Filters
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
    st.warning("No data available for the selected filters.")
else:
    # KPI Calculations
    total_revenue = filtered_df['total_revenue'].sum()
    total_orders = filtered_df['order_id'].nunique()
    aov = total_revenue / total_orders if total_orders > 0 else 0
    total_customers = filtered_df['customer_id'].nunique()

    # Repeat vs New Customer calculation based on customer order frequency in filtered or overall dataset
    cust_order_counts = filtered_df.groupby('customer_id')['order_id'].nunique()
    repeat_customers = (cust_order_counts > 1).sum()
    new_customers = (cust_order_counts == 1).sum()

    # Top KPIs Row
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Revenue", f"₱{total_revenue:,.2f}")
    col2.metric("Total Orders", f"{total_orders:,}")
    col3.metric("Avg Order Value (AOV)", f"₱{aov:,.2f}")
    col4.metric("Active Customers", f"{total_customers:,}")
    col5.metric("Repeat / New Cust", f"{repeat_customers:,} / {new_customers:,}")

    st.markdown("---")

    # Row 1: Monthly Revenue Trend & Revenue by Category
    row1_col1, row1_col2 = st.columns(2)

    with row1_col1:
        st.subheader("📈 Monthly Revenue Trend")
        monthly_rev = filtered_df.groupby('year_month')['total_revenue'].sum().reset_index()
        fig_monthly = px.line(
            monthly_rev, 
            x='year_month', 
            y='total_revenue',
            markers=True,
            labels={'year_month': 'Month', 'total_revenue': 'Revenue (₱)'},
            template='plotly_white'
        )
        fig_monthly.update_traces(line=dict(color='#1f77b4', width=3))
        st.plotly_chart(fig_monthly, use_container_width=True)

    with row1_col2:
        st.subheader("🏷️ Revenue by Category")
        cat_rev = filtered_df.groupby('category')['total_revenue'].sum().reset_index().sort_values(by='total_revenue', ascending=True)
        fig_cat = px.bar(
            cat_rev,
            x='total_revenue',
            y='category',
            orientation='h',
            labels={'total_revenue': 'Revenue (₱)', 'category': 'Category'},
            template='plotly_white',
            color='total_revenue',
            color_continuous_scale='Blues'
        )
        st.plotly_chart(fig_cat, use_container_width=True)

    # Row 2: Top 10 Products & Revenue by City
    row2_col1, row2_col2 = st.columns(2)

    with row2_col1:
        st.subheader("🏆 Top 10 Products by Revenue")
        top_products = filtered_df.groupby(['product_id', 'product_name'])['total_revenue'].sum().reset_index()
        top_products = top_products.sort_values(by='total_revenue', ascending=False).head(10).sort_values(by='total_revenue', ascending=True)
        fig_prod = px.bar(
            top_products,
            x='total_revenue',
            y='product_name',
            orientation='h',
            labels={'total_revenue': 'Revenue (₱)', 'product_name': 'Product'},
            template='plotly_white',
            color='total_revenue',
            color_continuous_scale='Viridis'
        )
        st.plotly_chart(fig_prod, use_container_width=True)

    with row2_col2:
        st.subheader("🏙️ Revenue by City (Top 15)")
        city_rev = filtered_df.groupby('city')['total_revenue'].sum().reset_index()
        city_rev = city_rev.sort_values(by='total_revenue', ascending=False).head(15).sort_values(by='total_revenue', ascending=True)
        fig_city = px.bar(
            city_rev,
            x='total_revenue',
            y='city',
            orientation='h',
            labels={'total_revenue': 'Revenue (₱)', 'city': 'City'},
            template='plotly_white',
            color='total_revenue',
            color_continuous_scale='Teal'
        )
        st.plotly_chart(fig_city, use_container_width=True)

    # Row 3: Customer Spend Distribution & Repeat vs New Customer
    row3_col1, row3_col2 = st.columns(2)

    with row3_col1:
        st.subheader("👥 Customer Spend Distribution")
        cust_spend = filtered_df.groupby('customer_id')['total_revenue'].sum().reset_index()
        fig_hist = px.histogram(
            cust_spend,
            x='total_revenue',
            nbins=30,
            labels={'total_revenue': 'Total Spend per Customer (₱)'},
            template='plotly_white',
            color_discrete_sequence=['#2ca02c']
        )
        st.plotly_chart(fig_hist, use_container_width=True)

    with row3_col2:
        st.subheader("🔄 Repeat vs. New Customer Revenue Share")
        # Classify customer order status per customer in filtered set
        customer_orders = filtered_df.groupby('customer_id').agg(
            first_order_date=('order_datetime', 'min'),
            total_orders=('order_id', 'nunique'),
            customer_revenue=('total_revenue', 'sum')
        ).reset_index()
        
        # Let's categorize based on total orders in this dataset view
        customer_orders['customer_type'] = customer_orders['total_orders'].apply(lambda x: 'Repeat Customer' if x > 1 else 'New Customer')
        cust_type_rev = customer_orders.groupby('customer_type')['customer_revenue'].sum().reset_index()

        fig_pie = px.pie(
            cust_type_rev,
            names='customer_type',
            values='customer_revenue',
            hole=0.4,
            template='plotly_white',
            color_discrete_sequence=['#ff7f0e', '#1f77b4']
        )
        st.plotly_chart(fig_pie, use_container_width=True)
