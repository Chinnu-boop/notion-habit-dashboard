import requests
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="Habit Progress",
    layout="wide"
)

NOTION_TOKEN = st.secrets["NOTION_TOKEN"]
DATA_SOURCE_ID = st.secrets["NOTION_DATA_SOURCE_ID"]

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2026-03-11",
    "Content-Type": "application/json",
}


def get_notion_rows():
    url = f"https://api.notion.com/v1/data_sources/{DATA_SOURCE_ID}/query"

    rows = []
    payload = {"page_size": 100}

    while True:
        response = requests.post(url, headers=HEADERS, json=payload)
        response.raise_for_status()

        data = response.json()
        rows.extend(data["results"])

        if not data.get("has_more"):
            break

        payload["start_cursor"] = data["next_cursor"]

    return rows


def notion_to_dataframe(rows):
    records = []

    for row in rows:
        props = row["properties"]

        # Skip rows with no date
        date_prop = props.get("Date", {})
        date_data = date_prop.get("date")

        if not date_data or not date_data.get("start"):
            continue

        record = {
            "Date": pd.to_datetime(date_data["start"]).date()
        }

        # Automatically treat every checkbox property as a habit
        for name, prop in props.items():
            if prop.get("type") == "checkbox":
                record[name] = prop.get("checkbox", False)

        records.append(record)

    return pd.DataFrame(records)


rows = get_notion_rows()
df = notion_to_dataframe(rows)

if df.empty:
    st.info("No dated habit entries found.")
    st.stop()

habit_columns = [
    col for col in df.columns
    if col != "Date"
]

if not habit_columns:
    st.info("No checkbox habit properties found.")
    st.stop()

# Convert checkbox values to 1 / 0
for habit in habit_columns:
    df[habit] = df[habit].astype(int)

# Monday of each week
df["Week"] = pd.to_datetime(df["Date"]) - pd.to_timedelta(
    pd.to_datetime(df["Date"]).dt.weekday,
    unit="D"
)

# Wide -> long format
long_df = df.melt(
    id_vars=["Date", "Week"],
    value_vars=habit_columns,
    var_name="Habit",
    value_name="Completed"
)

# Weekly average = completion percentage
weekly = (
    long_df
    .groupby(["Week", "Habit"], as_index=False)
    .agg(
        Completion=("Completed", "mean"),
        Completed_Days=("Completed", "sum"),
        Total_Days=("Completed", "count")
    )
)

weekly["Completion"] *= 100

fig = px.line(
    weekly,
    x="Week",
    y="Completion",
    color="Habit",
    markers=True,
    custom_data=["Completed_Days", "Total_Days"]
)

fig.update_traces(
    hovertemplate=(
        "<b>%{fullData.name}</b><br>"
        "Week of %{x|%d %b %Y}<br>"
        "%{y:.0f}%<br>"
        "%{customdata[0]} of %{customdata[1]} days"
        "<extra></extra>"
    )
)

fig.update_yaxes(
    range=[0, 100],
    ticksuffix="%",
    title="Completion"
)

fig.update_xaxes(
    title=None
)

fig.update_layout(
    legend_title=None,
    hovermode="closest"
)

st.plotly_chart(
    fig,
    use_container_width=True
)
