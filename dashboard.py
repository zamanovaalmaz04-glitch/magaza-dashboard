import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3

st.set_page_config(page_title="Mağaza Analitikası", page_icon="🛒", layout="wide")

@st.cache_data
def load_data():
    conn = sqlite3.connect("magaza.db")
    df = pd.read_sql("SELECT * FROM satislar", conn)
    conn.close()
    df["tarix"] = pd.to_datetime(df["tarix"])
    return df

df = load_data()

st.title("🛒 Mağaza Satış Paneli")

k1, k2, k3, k4 = st.columns(4)
k1.metric("Ümumi gəlir", f"{df['umumi_mebler'].sum():,.0f} AZN")
k2.metric("Əməliyyat sayı", f"{len(df):,}")
k3.metric("Orta çek", f"{df['umumi_mebler'].mean():.2f} AZN")
k4.metric("Ən çox satan", df.groupby("mehsul_adi")["miqdar"].sum().idxmax())

st.divider()

g1, g2 = st.columns(2)

with g1:
    st.subheader("Günlük gəlir")
    gunluk = df.groupby("tarix")["umumi_mebler"].sum().reset_index()
    fig1 = px.line(gunluk, x="tarix", y="umumi_mebler",
                   labels={"tarix": "Tarix", "umumi_mebler": "Gəlir (AZN)"})
    fig1.update_traces(line_color="#7F77DD", line_width=2)
    st.plotly_chart(fig1, use_container_width=True)

with g2:
    st.subheader("Kateqoriya üzrə paylanma")
    cat = df.groupby("kateqoriya")["umumi_mebler"].sum().reset_index()
    fig2 = px.pie(cat, names="kateqoriya", values="umumi_mebler", hole=0.4)
    st.plotly_chart(fig2, use_container_width=True)

g3, g4 = st.columns(2)

with g3:
    st.subheader("TOP 10 məhsul")
    top = df.groupby("mehsul_adi")["umumi_mebler"].sum().sort_values(ascending=True).tail(10).reset_index()
    fig3 = px.bar(top, x="umumi_mebler", y="mehsul_adi", orientation="h",
                  labels={"umumi_mebler": "Gəlir (AZN)", "mehsul_adi": ""})
    fig3.update_traces(marker_color="#1D9E75")
    st.plotly_chart(fig3, use_container_width=True)

with g4:
    st.subheader("Həftə günü üzrə satış")
    gun_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    gun_labels = {"Monday":"B.ertəsi","Tuesday":"Ç.axşamı","Wednesday":"Çərşənbə",
                  "Thursday":"C.axşamı","Friday":"Cümə","Saturday":"Şənbə","Sunday":"Bazar"}
    gun_df = df.groupby("hefte_gunu")["umumi_mebler"].sum().reindex(gun_order).reset_index()
    gun_df["hefte_gunu"] = gun_df["hefte_gunu"].map(gun_labels)
    fig4 = px.bar(gun_df, x="hefte_gunu", y="umumi_mebler",
                  labels={"hefte_gunu": "", "umumi_mebler": "Gəlir (AZN)"})
    fig4.update_traces(marker_color="#378ADD")
    st.plotly_chart(fig4, use_container_width=True)