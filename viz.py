import os
import sqlite3
import pandas as pd
import streamlit as st

st.set_page_config(layout="wide")

# Connect to SQLite database
@st.cache_resource
def get_connection():
    return sqlite3.connect(os.path.expanduser('~/.continue/dev_data/devdata.sqlite'))

conn = get_connection()

# Fetch data from the database
@st.cache_data(ttl=600)
def fetch_data(query):
    return pd.read_sql_query(query, conn)

# query = "SELECT model, provider, tokens_generated, timestamp FROM tokens_generated ORDER BY timestamp DESC"
# Updated query to exclude qwen2.5-coder:1.5b model
query = """
SELECT model, tokens_generated, timestamp 
FROM tokens_generated 
WHERE model != 'qwen2.5-coder:1.5b'
AND timestamp >= date('now', '-12 months')
ORDER BY timestamp DESC 
"""
data = fetch_data(query)
# Group by model and sum tokens_generated
grouped_data = data.groupby('model')['tokens_generated'].sum().reset_index()

# Convert timestamp to datetime
data['timestamp'] = pd.to_datetime(data['timestamp'])

# Group by month and model, sum tokens
monthly_tokens = data.groupby([
    pd.Grouper(key='timestamp', freq='W'), 
    'model'
])['tokens_generated'].sum().reset_index()

# Display data in Streamlit app
st.title("SQLite Data Visualization with Streamlit")
st.write("Data from SQLite Database:")
st.dataframe(grouped_data)

# Bar chart visualization
# st.bar_chart(data.set_index('model')['tokens_generated'])

# Altair chart example
import altair as alt

chart = alt.Chart(grouped_data).mark_bar().encode(
    x='model',
    y='tokens_generated'
)
st.altair_chart(chart, use_container_width=True)

# Create time series line chart
ts_chart = alt.Chart(monthly_tokens).mark_line(point=True).encode(
    x=alt.X('timestamp:T', 
            title='Week', 
            timeUnit='yearweek',  # Group by year and week
            axis=alt.Axis(
                format='%Y Week %W',  # Custom formatting to show year and week number
                labelAngle=45  # Angle labels to prevent overlap
            )
    ),
    y=alt.Y('tokens_generated:Q', title='Tokens Generated'),
    color='model:N',
    tooltip=['model', 'timestamp', 'tokens_generated']
).properties(
    title='Weekly Tokens Generated by Model',
    height=500,
)
st.altair_chart(ts_chart, use_container_width=True)

# Optional: Display the monthly aggregated data
st.write("Weekly Tokens by Model:")
st.dataframe(monthly_tokens)