"""
Дашборд сквозной аналитики LeadFlow.

Показывает воронку лидов и разбивку по каналам/UTM-меткам поверх той же
базы данных, куда пишет бэкенд. Запуск: streamlit run dashboard/app.py
"""

import os

import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import create_engine

# По умолчанию читаем из того же SQLite-файла, куда пишет бэкенд
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./leadflow.db")

st.set_page_config(page_title="LeadFlow — аналитика", layout="wide")
st.title("Сквозная аналитика лидов")


@st.cache_data(ttl=60)
def load_leads() -> pd.DataFrame:
    engine = create_engine(DATABASE_URL)
    return pd.read_sql("SELECT * FROM leads", engine)


try:
    df = load_leads()
except Exception as exc:
    st.error(f"Не удалось подключиться к базе данных: {exc}")
    st.info("Убедись, что бэкенд хотя бы раз запускался — тогда файл leadflow.db уже создан.")
    st.stop()

if df.empty:
    st.info("Пока нет данных. Заполните квиз на лендинге или напишите боту.")
    st.stop()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Всего лидов", len(df))
col2.metric("Синхронизировано с Bitrix24", (df["sync_status"] == "synced").sum())
col3.metric("Повторных обращений", df["repeat_contacts"].sum())
col4.metric("Ошибок синхронизации", (df["sync_status"] == "failed").sum())

st.divider()

left, right = st.columns(2)

with left:
    st.subheader("Лиды по источникам")
    by_source = df["utm_source"].fillna("не указан").value_counts().reset_index()
    by_source.columns = ["Источник", "Количество"]
    fig = px.bar(by_source, x="Источник", y="Количество")
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("Воронка по каналам (форма vs бот)")
    by_channel = df["source"].value_counts().reset_index()
    by_channel.columns = ["Канал", "Количество"]
    fig2 = px.pie(by_channel, names="Канал", values="Количество")
    st.plotly_chart(fig2, use_container_width=True)

st.subheader("Динамика лидов по дням")
df["date"] = pd.to_datetime(df["created_at"]).dt.date
by_day = df.groupby("date").size().reset_index(name="Лиды")
fig3 = px.line(by_day, x="date", y="Лиды", markers=True)
st.plotly_chart(fig3, use_container_width=True)

st.subheader("Последние лиды")
st.dataframe(
    df[["created_at", "name", "source", "utm_source", "project_type", "sync_status"]]
    .sort_values("created_at", ascending=False)
    .head(20),
    use_container_width=True,
)
