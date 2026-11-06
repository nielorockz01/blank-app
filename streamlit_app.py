import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# Page configuration
st.set_page_config(
    page_title="Sales Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .metric-card {
        background-color: #ffffff;
        border: 1px solid #e9ecef;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        text-align: center;
    }
    .metric-value {
        font-size: 24px;
        font-weight: bold;
        color: #1e3a8a;
    }
    .metric-label {
        font-size: 14px;
        color: #6c757d;
    }
    </style>
""", unsafe_allow_html=True)

# Helper function to generate mock data if CSV is not provided/uploaded
@st.cache_data
def load_data(uploaded_file):
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
    else:
        # Generate synthetic sales data representing fact_sales structure
        np.random.seed(42)
        dates = pd.date_range(start="2023-01-01", end="2023-12-31", freq="D")
        categories = ['Electronics', 'Fashion', 'Home & Living', 'Beauty', 'Groceries']
        products = [f"Product {chr(65+i)}" for i in range(20)]
        cities = ['Manila', 'Quezon City', 'Davao City', 'Cebu City', 'Caloocan', 'Zamboanga City']
        regions = ['NCR', 'NCR', 'Mindanao', 'Visayas', 'NCR', 'Mindanao']
        city_region_map = dict(zip(cities, regions))

        data = []
        customer_ids = [f"CUST-{1000 + i}" for i in range(150)]
        
        for _ in range(2000):
            date = np.random.choice(dates)
            cust_id = np.random.choice(customer_ids)
            city = np.random.choice(cities)
            prod = np.random.choice(products)
            cat = np.random.choice(categories)
            qty = np.random.randint(1, 5)
            price = np.random.uniform(100, 5000)
            revenue = qty * price
            
            data.append({
                'order_id': f"ORD-{np.random.randint(10000, 99999)}",
                'order_date': date,
                'customer_id': cust_id,
                'product_name': prod,
                'category': cat,
                'city': city,
                'region': city_region_map[city],
                'quantity': qty,
                'unit_price': price,
                'revenue': revenue
            })
        df = pd.DataFrame(data)
    
    # Standardize Column Names and Data Types
    df.columns = [c.lower().strip() for c in df.columns]
    
    # Smart Column Mapping
    date_col = next((c for c in df.columns if 'date' in c), 'order_date')
    revenue_col = next((c for c in df.columns if 'rev' in c or 'amount' in c or 'total' in c or 'sales' in c), 'revenue')
    customer_col = next((c for c in df.columns if 'cust' in c or 'user' in c), 'customer_id')
    product_col = next((c for c in df.columns if 'prod' in c or 'item' in c), 'product_name')
    category_col = next((c for c in df.columns if 'cat' in c), 'category')
    city_col = next((c for c in df.columns if 'city' in c or 'location' in c), 'city')
    region_col = next((c for c in df.columns if 'region' in c or 'state' in c), 'region')
    order_col = next((c for c in df.columns if 'order' in c or 'id' in c), 'order_id')

    df[date_col] = pd.to_datetime(df[date_col])
    df['year_month'] = df[date_col].dt.to_period('M').astype(str)
    
    return df, {
        'date': date_col,
        'revenue': revenue_col,
        'customer': customer_col,
        'product': product_col,
        'category': category_col,
        'city': city_col,
        'region': region_col,
        'order': order_col
    }

# Sidebar - Data Upload & Filters
st.sidebar.title("⚙️ Dashboard Controls")
uploaded_file = st.sidebar.file_uploader("Upload `fact_sales.csv`", type=["csv"])

df, cols = load_data(uploaded_file)

if uploaded_file is None:
    st.sidebar.info("💡 Currently displaying demo data. Upload your `fact_sales.csv` to analyze your own dataset.")

# Sidebar Filters
st.sidebar.subheader("Filters")
if cols['region'] in df.columns:
    selected_region = st.sidebar.multiselect("Select Region", options=df[cols['region']].unique(), default=df[cols['region']].unique())
    df = df[df[cols['region']].isin(selected_region)]

if cols['category'] in df.columns:
    selected_cat = st.sidebar.multiselect("Select Category", options=df[cols['category']].unique(), default=df[cols['category']].unique())
    df = df[df[cols['category']].isin(selected_cat)]

# Primary KPI Calculations
total_revenue = df[cols['revenue']].sum()
total_orders = df[cols['order']].nunique()
aov = total_revenue / total_orders if total_orders > 0 else 0

# Repeat vs. New Customers Calculation
customer_order_counts = df.groupby(cols['customer'])[cols['order']].nunique()
repeat_customers = (customer_order_counts > 1).sum()
new_customers = (customer_order_counts == 1).sum()
total_unique_customers = customer_order_counts.count()
repeat_rate = (repeat_customers / total_unique_customers * 100) if total_unique_customers > 0 else 0

# Header
st.title("📈 Sales Performance Dashboard")
st.markdown("---")

# Row 1: Key Metrics Cards
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

with kpi1:
    st.metric("Total Revenue", f"₱{total_revenue:,.2f}")

with kpi2:
    st.metric("Total Orders", f"{total_orders:,}")

with kpi3:
    st.metric("Average Order Value (AOV)", f"₱{aov:,.2f}")

with kpi4:
    st.metric("Repeat Customer Rate", f"{repeat_rate:.1f}%", f"{repeat_customers:,} repeat / {new_customers:,} new")

st.markdown("---")

# Row 2: Trends and Customer Segmentation
col_trend, col_cust = st.columns([2, 1])

with col_trend:
    st.subheader("🗓️ Monthly Revenue Trend")
    monthly_rev = df.groupby('year_month')[cols['revenue']].sum().reset_index()
    fig_line = px.line(
        monthly_rev, 
        x='year_month', 
        y=cols['revenue'],
        labels={'year_month': 'Month', cols['revenue']: 'Revenue (₱)'},
        markers=True,
        color_discrete_sequence=['#1e3a8a']
    )
    fig_line.update_traces(line=dict(width=3))
    fig_line.update_layout(hovermode="x unified", yaxis_tickprefix="₱")
    st.plotly_chart(fig_line, use_container_width=True)

with col_cust:
    st.subheader("👥 Repeat vs New Customers")
    cust_df = pd.DataFrame({
        'Customer Type': ['New Customer', 'Repeat Customer'],
        'Count': [new_customers, repeat_customers]
    })
    fig_pie = px.pie(
        cust_df, 
        names='Customer Type', 
        values='Count', 
        hole=0.4,
        color_discrete_sequence=['#93c5fd', '#1d4ed8']
    )
    st.plotly_chart(fig_pie, use_container_width=True)

st.markdown("---")

# Row 3: Product & Category Breakdown
col_prod, col_cat = st.columns(2)

with col_prod:
    st.subheader("🏆 Top 10 Products by Revenue")
    top_products = df.groupby(cols['product'])[cols['revenue']].sum().reset_index()
    top_products = top_products.sort_values(by=cols['revenue'], ascending=True).tail(10)
    
    fig_top_prod = px.bar(
        top_products,
        x=cols['revenue'],
        y=cols['product'],
        orientation='h',
        text_auto='.2s',
        labels={cols['revenue']: 'Revenue (₱)', cols['product']: 'Product'},
        color_discrete_sequence=['#2563eb']
    )
    fig_top_prod.update_layout(xaxis_tickprefix="₱")
    st.plotly_chart(fig_top_prod, use_container_width=True)

with col_cat:
    st.subheader("📦 Revenue by Category")
    cat_rev = df.groupby(cols['category'])[cols['revenue']].sum().reset_index().sort_values(by=cols['revenue'], ascending=False)
    
    fig_cat = px.bar(
        cat_rev,
        x=cols['category'],
        y=cols['revenue'],
        text_auto='.2s',
        labels={cols['category']: 'Category', cols['revenue']: 'Revenue (₱)'},
        color=cols['revenue'],
        color_continuous_scale='Blues'
    )
    fig_cat.update_layout(yaxis_tickprefix="₱", coloraxis_showscale=False)
    st.plotly_chart(fig_cat, use_container_width=True)

st.markdown("---")

# Row 4: Regional Distribution & Spend Histogram
col_city, col_dist = st.columns(2)

with col_city:
    st.subheader("🌆 Revenue by Region / City")
    city_rev = df.groupby([cols['region'], cols['city']])[cols['revenue']].sum().reset_index().sort_values(by=cols['revenue'], ascending=False)
    
    fig_city = px.bar(
        city_rev,
        x=cols['city'],
        y=cols['revenue'],
        color=cols['region'] if cols['region'] in df.columns else None,
        labels={cols['city']: 'City', cols['revenue']: 'Revenue (₱)'},
        text_auto='.2s'
    )
    fig_city.update_layout(yaxis_tickprefix="₱")
    st.plotly_chart(fig_city, use_container_width=True)

with col_dist:
    st.subheader("💰 Customer Spend Distribution")
    cust_spend = df.groupby(cols['customer'])[cols['revenue']].sum().reset_index()
    
    fig_hist = px.histogram(
        cust_spend,
        x=cols['revenue'],
        nbins=20,
        labels={cols['revenue']: 'Total Customer Spend (₱)', 'count': 'Number of Customers'},
        color_discrete_sequence=['#3b82f6']
    )
    fig_hist.update_layout(xaxis_tickprefix="₱", yaxis_title="Customer Count")
    st.plotly_chart(fig_hist, use_container_width=True)

st.markdown("---")
# Raw Data Section
with st.expander("🔍 View Processed Data"):
    st.dataframe(df, use_container_width=True)
