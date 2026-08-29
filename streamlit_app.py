import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="Habit Progress",
    layout="wide"
)

data = pd.DataFrame({
    "Week": [
        "17–23 Aug", "17–23 Aug", "17–23 Aug",
        "24–30 Aug", "24–30 Aug", "24–30 Aug"
    ],
    "Habit": [
        "AM Skin Care", "PM Skin Care", "Exercise",
        "AM Skin Care", "PM Skin Care", "Exercise"
    ],
    "Completion": [
        75, 60, 40,
        85, 80, 65
    ]
})

fig = px.line(
    data,
    x="Week",
    y="Completion",
    color="Habit",
    markers=True
)

fig.update_yaxes(
    range=[0, 100],
    ticksuffix="%"
)

fig.update_layout(
    xaxis_title=None,
    yaxis_title="Completion",
    legend_title=None
)

st.plotly_chart(fig, use_container_width=True)
