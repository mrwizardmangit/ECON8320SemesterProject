import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title='US Labor Market Dashboard',
    layout="wide"
)

@st.cache_data
def load_data():
    df = pd.read_csv('labor_market_data.csv')
    df['date'] = pd.to_datetime(df['date'])
    return df

try:
    df = load_data()
    # Labor Leverage Ratio (Quits / Layoffs)
    df['Leverage Ratio'] = df['Quits'] / df['Layoffs']
    
    # Real Wage Growth (YoY)
    df['Real Wage Growth'] = df['Real Wages'].pct_change(periods=12, fill_method=None) * 100
    
    # Job Openings Rate
    # Openings / (Employed + Openings)
    df['Job Openings Rate'] = (df['Job Openings'] / (df['Total Nonfarm Employment'] + df['Job Openings'])) * 100
except FileNotFoundError:
    st.error("Data file not found. Run data_collection.py first.")
    st.stop()

def get_latest_valid(df, col_name):
    # Drop NaNs
    valid_data = df[col_name].dropna()
    
    if valid_data.empty:
        return 0, 0  
        
    latest_val = valid_data.iloc[-1]
    
    # Get previous value
    if len(valid_data) > 1:
        prev_val = valid_data.iloc[-2]
    else:
        prev_val = latest_val
        
    return latest_val, prev_val

st.title("US Labor Market: Quality and Dynamism")
st.markdown("Measuring the quality of jobs and churn of the workforce.")

u3_curr, u3_prev = get_latest_valid(df, 'Unemployment Rate (U3)')
u6_curr, u6_prev = get_latest_valid(df, 'Underemployment Rate (U6)')
jobs_curr, jobs_prev = get_latest_valid(df, 'Total Nonfarm Employment')
quits_curr, quits_prev = get_latest_valid(df, 'Quits')

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Unemployment (U-3)", 
              f"{u3_curr}%", 
              f"{u3_curr - u3_prev:.1f}%",
              delta_color="inverse",
              help="The percentage of the labor force that is unemployed and actively looking for work."
    )
with col2:
    st.metric("Underemployment (U-6)", 
              f"{u6_curr}%", 
              f"{u6_curr - u6_prev:.1f}%",
              delta_color="inverse",
              help="Includes the unemployed, plus 'marginally attached' workers, plus those working part-time for economic reasons."
    )

with col3:
    st.metric("Total Jobs Added", 
              f"{jobs_curr:,.0f}", 
              f"{jobs_curr - jobs_prev:,.0f}",
              help="The net number of nonfarm jobs added or lost in the economy compared to the previous month (measured in thousands)."
    )

with col4:
    st.metric("Quits (Worker Confidence)", 
              f"{quits_curr:,.0f}", 
              f"{quits_curr - quits_prev:,.0f}",
              help="The total number of workers who quit their job during the month (measured in thousands). A high number of quits suggests workers are confident they can find a better job elsewhere."
    )

st.divider()

st.markdown("### Market Analysis")
tab1, tab2, tab3 = st.tabs(["Macroeconomic Overview", "Real Wage Analysis", "Beveridge Curve"])

# Tab 1

with tab1:
    st.markdown("#### Labor Turnover & Leverage")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.caption("Employment vs. Unemployment Rate")
        # Dual Axis: Jobs vs Unemployment
        fig_headline = go.Figure()
        fig_headline.add_trace(go.Scatter(x=df['date'], y=df['Total Nonfarm Employment'], name="Total Jobs (Left)", yaxis='y1'))
        fig_headline.add_trace(go.Scatter(x=df['date'], y=df['Unemployment Rate (U3)'], name="Unemployment Rate (Right)", yaxis='y2', line=dict(dash='dot', color='red')))
        
        fig_headline.update_layout(
            yaxis=dict(title="Total Jobs (Thousands)"),
            yaxis2=dict(title="Unemployment Rate (%)", overlaying='y', side='right'),
            legend=dict(orientation="h", y=1.1),
            margin=dict(l=0, r=0, t=0, b=0)
        )
        st.plotly_chart(fig_headline, width="stretch")
        
    with col2:
        st.caption("Labor Leverage Ratio (Quits / Layoffs)")
        # Leverage Ratio Chart
        fig_lev = px.line(df, x='date', y='Leverage Ratio', 
                          title=None)
        # Reference line at 1.0 
        fig_lev.add_hline(y=1.0, line_dash="dot", annotation_text="Neutral (1.0)", annotation_position="bottom right")
        
        fig_lev.update_layout(
            yaxis_title="Ratio",
            margin=dict(l=0, r=0, t=0, b=0)
        )
        st.plotly_chart(fig_lev, width="stretch")
        
    st.info("""
    The labor leverage ratio compares voluntary quits to involuntary layoffs. 
    * A rising ratio (>1.0) indicates high worker confidence and a tight labor market.
    * A falling ratio indicates the opposite.
    """)

# Tab 2

with tab2:
    st.markdown("#### Wage Growth vs. Inflation")
    
    col_w1, col_w2 = st.columns(2)
    
    with col_w1:
        st.caption("Real Average Hourly Earnings (Indexed to CPI)")
        fig_real = px.line(df, x='date', y='Real Wages')
        fig_real.update_layout(yaxis_title="Real Earnings ($)", margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig_real, width="stretch")
        
    with col_w2:
        st.caption("Year-over-Year % Change in Real Wages")
        # Color bars red if negative, green if positive
        df['Growth Color'] = df['Real Wage Growth'].apply(lambda x: 'Positive' if x >= 0 else 'Negative')
        fig_growth = px.bar(df, x='date', y='Real Wage Growth', color='Growth Color',
                            color_discrete_map={'Positive': 'green', 'Negative': 'red'})
        fig_growth.update_layout(showlegend=False, yaxis_title="YoY Growth (%)", margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig_growth, width="stretch")

    st.info("""
    The bar chart illustrates changes in purchasing power. 
    * Green bars indicate that nominal wage growth is outpacing inflation.
    * Red bars indicate that inflation is rising faster than wages.
    """)

# Tab 3

with tab3:
    st.markdown("#### Structural Labor Market Efficiency")
    
    col_b1, col_b2 = st.columns([2, 1])
    
    with col_b1:
        # Unemployment (x) vs Job Openings Rate (y)
        # Color by 'date' to show time progression
        fig_bev = px.scatter(df, x='Unemployment Rate (U3)', y='Job Openings Rate', 
                             color='date', 
                             title="Beveridge Curve (2020-Present)",
                             labels={'Unemployment Rate (U3)': 'Unemployment Rate (%)', 'Job Openings Rate': 'Job Openings Rate (%)'})
        # Connect the dots 
        fig_bev.update_traces(mode='lines+markers', marker=dict(size=8))
        fig_bev.update_layout(
            coloraxis_showscale=False, # Hides the color bar 
            showlegend=False,          # Hides the list of dates
            margin=dict(l=0, r=0, t=30, b=0)
        )

        st.plotly_chart(fig_bev, width="stretch")
        
    with col_b2:
        st.markdown("""
        The Beveridge Curve plots the unemployment rate against the job openings rate.
        * Movements along the curve represent the business cycle (recession and expansion).
        * Outward shifts of the curve (up and to the right) indicate a decline in matching efficiency (high vacancies and high unemployment).
        """)

