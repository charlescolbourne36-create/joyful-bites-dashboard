"""
JOYFUL BITES CUSTOMER DASHBOARD
Project Resonance - Module 1: Data Visualization

A professional dashboard for exploring customer segments and behavioral patterns
across the Joyful Bites customer base.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from datetime import datetime, timedelta

# Page configuration
st.set_page_config(
    page_title="Joyful Bites Customer Intelligence",
    page_icon="🍗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #D32F2F;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border-left: 4px solid #D32F2F;
        margin-bottom: 1rem;
    }
    .segment-card {
        background-color: #fff;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border: 2px solid #e0e0e0;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .persona-name {
        font-size: 1.5rem;
        font-weight: 600;
        color: #D32F2F;
    }
    .persona-tagline {
        font-size: 1rem;
        color: #666;
        font-style: italic;
    }
    .stat-value {
        font-size: 2rem;
        font-weight: 700;
        color: #D32F2F;
    }
    .stat-label {
        font-size: 0.9rem;
        color: #666;
        text-transform: uppercase;
    }
    .insight-box {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 0.25rem;
    }
</style>
""", unsafe_allow_html=True)

# Data loading function
@st.cache_data
def load_data():
    """Load customer dataset"""
    try:
        df = pd.read_csv('joyful_bites_customers_5000.csv')
        # Parse JSON fields
        df['top_menu_items_list'] = df['top_menu_items'].apply(lambda x: json.loads(x) if pd.notna(x) else [])
        df['num_menu_items'] = df['top_menu_items_list'].apply(len)
        return df
    except FileNotFoundError:
        st.error("Dataset not found. Please ensure 'joyful_bites_customers_5000.csv' is in the same directory.")
        return None

# Segment color mapping
SEGMENT_COLORS = {
    'Busy Brenda': '#E57373',
    'Hungry Hiro': '#64B5F6',
    'Urban Uro': '#81C784'
}

# Persona metadata
PERSONA_META = {
    'Busy Brenda': {
        'tagline': 'The Family Nurturer',
        'age_range': '30-45 years',
        'icon': '👨‍👩‍👧‍👦',
        'description': 'Time-strapped parents managing family meals, prioritizing convenience and kid-friendly options.'
    },
    'Hungry Hiro': {
        'tagline': 'The Value-Seeking Student/Gen Z',
        'age_range': '16-25 years',
        'icon': '🎓',
        'description': 'Budget-conscious students and young professionals seeking maximum value and social currency.'
    },
    'Urban Uro': {
        'tagline': 'The Nostalgic Professional',
        'age_range': '25-35 years',
        'icon': '💼',
        'description': 'Urban professionals valuing authentic Filipino taste, reliability, and convenience.'
    }
}

def format_currency(value):
    """Format value as Philippine Peso"""
    return f"₱{value:,.2f}"

def format_number(value):
    """Format number with thousands separator"""
    return f"{value:,.0f}"

def create_segment_overview(df):
    """Create segment overview visualizations"""
    
    st.markdown('<div class="main-header">Customer Intelligence Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Real-time insights across 5,399 Joyful Bites customers</div>', unsafe_allow_html=True)
    
    # Top-level KPIs
    col1, col2, col3, col4 = st.columns(4)
    
    total_customers = len(df)
    total_revenue = df['total_spent'].sum()
    total_orders = df['total_orders'].sum()
    avg_ltv = df['lifetime_value'].mean()
    
    with col1:
        st.metric(
            label="Total Customers",
            value=format_number(total_customers),
            delta=None
        )
    
    with col2:
        st.metric(
            label="Total Revenue",
            value=format_currency(total_revenue),
            delta=None
        )
    
    with col3:
        st.metric(
            label="Total Orders",
            value=format_number(total_orders),
            delta=None
        )
    
    with col4:
        st.metric(
            label="Avg Customer LTV",
            value=format_currency(avg_ltv),
            delta=None
        )
    
    st.markdown("---")
    
    # Segment distribution
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📊 Segment Distribution")
        
        segment_counts = df['segment'].value_counts()
        
        fig = go.Figure(data=[go.Pie(
            labels=segment_counts.index,
            values=segment_counts.values,
            hole=0.4,
            marker=dict(colors=[SEGMENT_COLORS[seg] for seg in segment_counts.index]),
            textposition='inside',
            textinfo='label+percent',
            hovertemplate='<b>%{label}</b><br>Customers: %{value}<br>Percentage: %{percent}<extra></extra>'
        )])
        
        fig.update_layout(
            height=400,
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("💰 Revenue Contribution by Segment")
        
        segment_revenue = df.groupby('segment')['total_spent'].sum().sort_values(ascending=False)
        
        fig = go.Figure(data=[go.Bar(
            x=segment_revenue.values,
            y=segment_revenue.index,
            orientation='h',
            marker=dict(color=[SEGMENT_COLORS[seg] for seg in segment_revenue.index]),
            text=[format_currency(val) for val in segment_revenue.values],
            textposition='outside',
            hovertemplate='<b>%{y}</b><br>Revenue: ₱%{x:,.2f}<extra></extra>'
        )])
        
        fig.update_layout(
            height=400,
            xaxis_title="Total Revenue (PHP)",
            yaxis_title="",
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)

def create_segment_comparison(df):
    """Create detailed segment comparison"""
    
    st.subheader("📈 Segment Performance Comparison")
    
    # Key metrics by segment
    segment_stats = df.groupby('segment').agg({
        'customer_id': 'count',
        'avg_order_value': 'mean',
        'visit_frequency_month': 'mean',
        'lifetime_value': 'mean',
        'party_size_avg': 'mean',
        'total_orders': 'sum',
        'total_spent': 'sum',
        'tenure_months': 'mean'
    }).round(2)
    
    segment_stats.columns = [
        'Customer Count',
        'Avg Order Value',
        'Visit Frequency/Month',
        'Lifetime Value',
        'Avg Party Size',
        'Total Orders',
        'Total Revenue',
        'Avg Tenure (Months)'
    ]
    
    # Create comparison metrics
    metrics = ['Avg Order Value', 'Visit Frequency/Month', 'Lifetime Value', 'Avg Party Size']
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Average Order Value comparison
        fig = go.Figure()
        
        for segment in segment_stats.index:
            fig.add_trace(go.Bar(
                name=segment,
                x=[segment],
                y=[segment_stats.loc[segment, 'Avg Order Value']],
                marker_color=SEGMENT_COLORS[segment],
                text=[format_currency(segment_stats.loc[segment, 'Avg Order Value'])],
                textposition='outside',
                hovertemplate=f'<b>{segment}</b><br>₱%{{y:,.2f}}<extra></extra>'
            ))
        
        fig.update_layout(
            title="Average Order Value by Segment",
            yaxis_title="PHP",
            showlegend=False,
            height=350,
            margin=dict(l=50, r=50, t=50, b=50)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Visit Frequency comparison
        fig = go.Figure()
        
        for segment in segment_stats.index:
            fig.add_trace(go.Bar(
                name=segment,
                x=[segment],
                y=[segment_stats.loc[segment, 'Visit Frequency/Month']],
                marker_color=SEGMENT_COLORS[segment],
                text=[f"{segment_stats.loc[segment, 'Visit Frequency/Month']:.1f}x"],
                textposition='outside',
                hovertemplate=f'<b>{segment}</b><br>%{{y:.1f}} visits/month<extra></extra>'
            ))
        
        fig.update_layout(
            title="Visit Frequency by Segment",
            yaxis_title="Visits per Month",
            showlegend=False,
            height=350,
            margin=dict(l=50, r=50, t=50, b=50)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Lifetime Value comparison
        fig = go.Figure()
        
        for segment in segment_stats.index:
            fig.add_trace(go.Bar(
                name=segment,
                x=[segment],
                y=[segment_stats.loc[segment, 'Lifetime Value']],
                marker_color=SEGMENT_COLORS[segment],
                text=[format_currency(segment_stats.loc[segment, 'Lifetime Value'])],
                textposition='outside',
                hovertemplate=f'<b>{segment}</b><br>₱%{{y:,.2f}}<extra></extra>'
            ))
        
        fig.update_layout(
            title="Customer Lifetime Value by Segment",
            yaxis_title="PHP",
            showlegend=False,
            height=350
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Party Size comparison
        fig = go.Figure()
        
        for segment in segment_stats.index:
            fig.add_trace(go.Bar(
                name=segment,
                x=[segment],
                y=[segment_stats.loc[segment, 'Avg Party Size']],
                marker_color=SEGMENT_COLORS[segment],
                text=[f"{segment_stats.loc[segment, 'Avg Party Size']:.1f}"],
                textposition='outside',
                hovertemplate=f'<b>{segment}</b><br>%{{y:.1f}} people<extra></extra>'
            ))
        
        fig.update_layout(
            title="Average Party Size by Segment",
            yaxis_title="People",
            showlegend=False,
            height=350
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Detailed comparison table
    st.subheader("📋 Detailed Metrics Table")
    
    # Format the table for display
    display_stats = segment_stats.copy()
    display_stats['Customer Count'] = display_stats['Customer Count'].apply(lambda x: format_number(x))
    display_stats['Avg Order Value'] = display_stats['Avg Order Value'].apply(lambda x: format_currency(x))
    display_stats['Lifetime Value'] = display_stats['Lifetime Value'].apply(lambda x: format_currency(x))
    display_stats['Total Revenue'] = display_stats['Total Revenue'].apply(lambda x: format_currency(x))
    display_stats['Total Orders'] = display_stats['Total Orders'].apply(lambda x: format_number(x))
    
    st.dataframe(display_stats, use_container_width=True)

def create_persona_deep_dive(df, persona_name):
    """Create detailed persona analysis"""
    
    persona_df = df[df['segment'] == persona_name]
    meta = PERSONA_META[persona_name]
    
    # Persona header
    st.markdown(f"""
    <div class="segment-card">
        <div style="display: flex; align-items: center; gap: 1rem;">
            <div style="font-size: 3rem;">{meta['icon']}</div>
            <div>
                <div class="persona-name">{persona_name}</div>
                <div class="persona-tagline">{meta['tagline']}</div>
            </div>
        </div>
        <p style="margin-top: 1rem; color: #666;">{meta['description']}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Key metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            label="Customers",
            value=format_number(len(persona_df)),
            delta=f"{len(persona_df)/len(df)*100:.1f}% of base"
        )
    
    with col2:
        st.metric(
            label="Avg Order Value",
            value=format_currency(persona_df['avg_order_value'].mean())
        )
    
    with col3:
        st.metric(
            label="Visit Frequency",
            value=f"{persona_df['visit_frequency_month'].mean():.1f}x/mo"
        )
    
    with col4:
        st.metric(
            label="Lifetime Value",
            value=format_currency(persona_df['lifetime_value'].mean())
        )
    
    with col5:
        st.metric(
            label="Avg Party Size",
            value=f"{persona_df['party_size_avg'].mean():.1f}"
        )
    
    st.markdown("---")
    
    # Behavioral patterns
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📱 Preferred Order Channels")
        
        channel_dist = persona_df['preferred_channel'].value_counts()
        
        fig = go.Figure(data=[go.Bar(
            x=channel_dist.index,
            y=channel_dist.values,
            marker_color=SEGMENT_COLORS[persona_name],
            text=channel_dist.values,
            textposition='outside',
            hovertemplate='<b>%{x}</b><br>Customers: %{y}<extra></extra>'
        )])
        
        fig.update_layout(
            yaxis_title="Number of Customers",
            xaxis_title="",
            height=350,
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("🕐 Primary Order Times")
        
        time_dist = persona_df['primary_order_time'].value_counts()
        
        fig = go.Figure(data=[go.Bar(
            x=time_dist.values,
            y=time_dist.index,
            orientation='h',
            marker_color=SEGMENT_COLORS[persona_name],
            text=time_dist.values,
            textposition='outside',
            hovertemplate='<b>%{y}</b><br>Customers: %{x}<extra></extra>'
        )])
        
        fig.update_layout(
            xaxis_title="Number of Customers",
            yaxis_title="",
            height=350,
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💳 Payment Methods")
        
        payment_dist = persona_df['preferred_payment'].value_counts()
        
        # Create color palette based on segment
        base_color = SEGMENT_COLORS[persona_name]
        
        fig = go.Figure(data=[go.Pie(
            labels=payment_dist.index,
            values=payment_dist.values,
            hole=0.3,
            textposition='inside',
            textinfo='label+percent',
            marker=dict(
                colors=['#E57373', '#81C784', '#64B5F6'][:len(payment_dist)]
            )
        )])
        
        fig.update_layout(
            height=350,
            showlegend=True,
            margin=dict(l=20, r=20, t=30, b=20)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("🎯 Engagement Metrics")
        
        promo_users = (persona_df['uses_promos'] == True).sum()
        loyalty_enrolled = (persona_df['loyalty_enrolled'] == True).sum()
        loyalty_active = (persona_df['loyalty_active'] == True).sum()
        
        engagement_data = {
            'Metric': ['Uses Promos', 'Loyalty Enrolled', 'Loyalty Active'],
            'Customers': [promo_users, loyalty_enrolled, loyalty_active],
            'Percentage': [
                promo_users/len(persona_df)*100,
                loyalty_enrolled/len(persona_df)*100,
                loyalty_active/len(persona_df)*100
            ]
        }
        
        fig = go.Figure(data=[go.Bar(
            x=engagement_data['Metric'],
            y=engagement_data['Percentage'],
            marker_color=SEGMENT_COLORS[persona_name],
            text=[f"{p:.0f}%" for p in engagement_data['Percentage']],
            textposition='outside',
            hovertemplate='<b>%{x}</b><br>%{y:.1f}%<extra></extra>'
        )])
        
        fig.update_layout(
            yaxis_title="Percentage (%)",
            yaxis_range=[0, 100],
            height=350,
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Top menu items
    st.subheader("🍗 Popular Menu Items")
    
    all_items = []
    for items_list in persona_df['top_menu_items_list']:
        all_items.extend(items_list)
    
    if all_items:
        item_counts = pd.Series(all_items).value_counts().head(10)
        
        fig = go.Figure(data=[go.Bar(
            x=item_counts.values,
            y=item_counts.index,
            orientation='h',
            marker_color=SEGMENT_COLORS[persona_name],
            text=item_counts.values,
            textposition='outside',
            hovertemplate='<b>%{y}</b><br>Ordered by %{x} customers<extra></extra>'
        )])
        
        fig.update_layout(
            xaxis_title="Number of Customers",
            yaxis_title="",
            height=400,
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No menu item data available for this segment")
    
    # Demographics
    st.subheader("👥 Demographics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**Age Distribution**")
        age_bins = [0, 20, 25, 30, 35, 40, 45, 100]
        age_labels = ['16-20', '21-25', '26-30', '31-35', '36-40', '41-45', '46+']
        persona_df['age_group'] = pd.cut(persona_df['age'], bins=age_bins, labels=age_labels)
        age_dist = persona_df['age_group'].value_counts().sort_index()
        
        fig = go.Figure(data=[go.Bar(
            x=age_dist.index,
            y=age_dist.values,
            marker_color=SEGMENT_COLORS[persona_name],
            hovertemplate='<b>%{x} years</b><br>Customers: %{y}<extra></extra>'
        )])
        
        fig.update_layout(height=300, showlegend=False, xaxis_title="Age Group", yaxis_title="Customers")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("**City Distribution (Top 10)**")
        city_dist = persona_df['city'].value_counts().head(10)
        
        fig = go.Figure(data=[go.Bar(
            x=city_dist.values,
            y=city_dist.index,
            orientation='h',
            marker_color=SEGMENT_COLORS[persona_name],
            hovertemplate='<b>%{y}</b><br>Customers: %{x}<extra></extra>'
        )])
        
        fig.update_layout(height=300, showlegend=False, xaxis_title="Customers", yaxis_title="")
        st.plotly_chart(fig, use_container_width=True)
    
    with col3:
        st.markdown("**Occupation Distribution**")
        occupation_dist = persona_df['occupation'].value_counts().head(5)
        
        fig = go.Figure(data=[go.Pie(
            labels=occupation_dist.index,
            values=occupation_dist.values,
            hole=0.3,
            marker=dict(
                colors=['#E57373', '#81C784', '#64B5F6', '#FFB74D', '#BA68C8'][:len(occupation_dist)]
            )
        )])
        
        fig.update_layout(
            height=300,
            showlegend=True,
            margin=dict(l=20, r=20, t=30, b=20)
        )
        st.plotly_chart(fig, use_container_width=True)

def create_behavioral_insights(df):
    """Create behavioral insights and patterns"""
    
    st.subheader("🔍 Behavioral Insights & Patterns")
    
    # Order value distribution
    st.markdown("### Order Value Distribution by Segment")
    
    fig = go.Figure()
    
    for segment in df['segment'].unique():
        segment_df = df[df['segment'] == segment]
        fig.add_trace(go.Box(
            y=segment_df['avg_order_value'],
            name=segment,
            marker_color=SEGMENT_COLORS[segment],
            boxmean='sd'
        ))
    
    fig.update_layout(
        yaxis_title="Average Order Value (PHP)",
        height=400,
        showlegend=True
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Correlation heatmap
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Visit Frequency vs Lifetime Value")
        
        fig = px.scatter(
            df,
            x='visit_frequency_month',
            y='lifetime_value',
            color='segment',
            color_discrete_map=SEGMENT_COLORS,
            trendline='ols',
            labels={
                'visit_frequency_month': 'Visit Frequency (per month)',
                'lifetime_value': 'Lifetime Value (PHP)',
                'segment': 'Segment'
            },
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### Tenure vs Total Spent")
        
        fig = px.scatter(
            df,
            x='tenure_months',
            y='total_spent',
            color='segment',
            color_discrete_map=SEGMENT_COLORS,
            trendline='ols',
            labels={
                'tenure_months': 'Tenure (months)',
                'total_spent': 'Total Spent (PHP)',
                'segment': 'Segment'
            },
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Key insights
    st.markdown("### 💡 Key Insights")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        brenda_df = df[df['segment'] == 'Busy Brenda']
        brenda_weekend_pct = (brenda_df['primary_order_time'].str.contains('Weekend')).sum() / len(brenda_df) * 100
        
        st.markdown(f"""
        <div class="insight-box">
            <strong>👨‍👩‍👧‍👦 Busy Brenda Insight</strong><br>
            {brenda_weekend_pct:.0f}% of Brenda segment orders during weekend lunch, indicating strong family dining tradition.
            Average party size of {brenda_df['party_size_avg'].mean():.1f} confirms family-focused behavior.
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        hiro_df = df[df['segment'] == 'Hungry Hiro']
        hiro_promo_pct = (hiro_df['uses_promos'] == True).sum() / len(hiro_df) * 100
        
        st.markdown(f"""
        <div class="insight-box">
            <strong>🎓 Hungry Hiro Insight</strong><br>
            {hiro_promo_pct:.0f}% of Hiro segment uses promos regularly. Highest visit frequency at {hiro_df['visit_frequency_month'].mean():.1f}x/month
            despite lowest AOV of {format_currency(hiro_df['avg_order_value'].mean())}.
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        uro_df = df[df['segment'] == 'Urban Uro']
        uro_delivery_pct = (uro_df['preferred_channel'] == 'Delivery').sum() / len(uro_df) * 100
        
        st.markdown(f"""
        <div class="insight-box">
            <strong>💼 Urban Uro Insight</strong><br>
            {uro_delivery_pct:.0f}% prefer delivery channel. Highest LTV at {format_currency(uro_df['lifetime_value'].mean())} 
            with longest tenure of {uro_df['tenure_months'].mean():.1f} months - most loyal segment.
        </div>
        """, unsafe_allow_html=True)

def main():
    """Main application"""
    
    # Load data
    df = load_data()
    
    if df is None:
        st.stop()
    
    # Sidebar navigation
    st.sidebar.image("https://via.placeholder.com/200x80/D32F2F/FFFFFF?text=JOYFUL+BITES", use_container_width=True)
    st.sidebar.title("Navigation")
    
    page = st.sidebar.radio(
        "Select View",
        ["📊 Overview", "📈 Segment Comparison", "👨‍👩‍👧‍👦 Busy Brenda", "🎓 Hungry Hiro", "💼 Urban Uro", "🔍 Behavioral Insights"]
    )
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### About")
    st.sidebar.info(
        "This dashboard provides real-time insights into the Joyful Bites customer base, "
        "segmented into three behavioral personas for targeted marketing strategies."
    )
    
    st.sidebar.markdown("### Data Summary")
    st.sidebar.metric("Total Customers", format_number(len(df)))
    st.sidebar.metric("Total Revenue", format_currency(df['total_spent'].sum()))
    st.sidebar.metric("Data Last Updated", datetime.now().strftime("%Y-%m-%d"))
    
    # Route to appropriate page
    if page == "📊 Overview":
        create_segment_overview(df)
        
    elif page == "📈 Segment Comparison":
        create_segment_comparison(df)
        
    elif page == "👨‍👩‍👧‍👦 Busy Brenda":
        create_persona_deep_dive(df, "Busy Brenda")
        
    elif page == "🎓 Hungry Hiro":
        create_persona_deep_dive(df, "Hungry Hiro")
        
    elif page == "💼 Urban Uro":
        create_persona_deep_dive(df, "Urban Uro")
        
    elif page == "🔍 Behavioral Insights":
        create_behavioral_insights(df)

if __name__ == "__main__":
    main()
