import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import io

st.set_page_config(page_title="Mağaza Analitikası", page_icon="🛒", layout="wide")

def xeta(mesaj, ipucu=None):
    st.error(f"⚠️ {mesaj}")
    if ipucu:
        st.info(f"💡 {ipucu}")
    st.stop()

def fayl_oxu(fayl):
    ad = fayl.name.lower()
    try:
        if ad.endswith(".csv"):
            for enc in ["utf-8", "utf-8-sig", "cp1252", "latin-1", "cp1251"]:
                try:
                    fayl.seek(0)
                    return pd.read_csv(fayl, encoding=enc)
                except UnicodeDecodeError:
                    continue
            xeta("CSV faylı oxunmadı", "Faylı Excel formatında (.xlsx) saxlayıb yenidən yükləyin")
        elif ad.endswith((".xlsx", ".xls")):
            fayl.seek(0)
            return pd.read_excel(fayl)
        else:
            xeta("Yalnız .xlsx, .xls və .csv faylları qəbul edilir")
    except Exception as e:
        xeta(f"Fayl oxunmadı", "Faylın açıq olmadığına və zədəli olmadığına əmin olun")

def sutun_tipi_mueyyenles(df):
    """Hər sütunun tipini avtomatik müəyyənləşdir"""
    tarix_sutun = None
    mebler_sutun = None
    mehsul_sutun = None
    kateq_sutun = None

    tarix_sozler  = ["tarix","date","tarih","gun","vaxt","time","dt","created"]
    mebler_sozler = ["mebler","məbləğ","cemi","total","amount","qiymet","price","summa","gelir","revenue"]
    mehsul_sozler = ["mehsul","məhsul","product","mal","ad","name","item","tovар"]
    kateq_sozler  = ["kateq","category","nov","tip","qrup","group","sinif"]

    for sutun in df.columns:
        s = str(sutun).lower()

        # Ada görə yoxla
        if any(x in s for x in tarix_sozler) and tarix_sutun is None:
            tarix_sutun = sutun
            continue
        if any(x in s for x in mebler_sozler) and mebler_sutun is None:
            mebler_sutun = sutun
            continue
        if any(x in s for x in mehsul_sozler) and mehsul_sutun is None:
            mehsul_sutun = sutun
            continue
        if any(x in s for x in kateq_sozler) and kateq_sutun is None:
            kateq_sutun = sutun

    # Ada görə tapılmadısa — məzmuna görə yoxla
    for sutun in df.columns:
        numune = df[sutun].dropna().head(20)

        if tarix_sutun is None:
            cehd = pd.to_datetime(numune, errors="coerce", dayfirst=True)
            if cehd.notna().sum() >= len(numune) * 0.6:
                tarix_sutun = sutun

        if mebler_sutun is None:
            eded = pd.to_numeric(
                numune.astype(str).str.replace(",",".").str.replace(r"[^\d.]","",regex=True),
                errors="coerce"
            )
            if eded.notna().sum() >= len(numune) * 0.7 and eded.mean() > 0:
                mebler_sutun = sutun

        if mehsul_sutun is None:
            if df[sutun].dtype == object and df[sutun].nunique() < len(df) * 0.8:
                if sutun != tarix_sutun and sutun != kateq_sutun:
                    mehsul_sutun = sutun

    return tarix_sutun, mebler_sutun, mehsul_sutun, kateq_sutun

def temizle(df, tarix_s, mebler_s, mehsul_s, kateq_s):
    hesabat = []
    df = df.copy()
    df = df.dropna(how="all").dropna(axis=1, how="all")
    df.columns = df.columns.astype(str).str.strip()

    # Tarix
    try:
        df[tarix_s] = pd.to_datetime(df[tarix_s], dayfirst=True, errors="coerce")
        null_say = df[tarix_s].isna().sum()
        if null_say > 0:
            hesabat.append(f"⚠️ {null_say} oxunmayan tarix silindi")
        df = df.dropna(subset=[tarix_s])
        if len(df) == 0:
            xeta("Tarix sütununda oxuna bilən tarix yoxdur",
                 "Tarix formatı: 26/01/2024 və ya 2024-01-26 olmalıdır")
        hesabat.append("✅ Tarix sütunu təmizləndi")
    except:
        xeta("Tarix sütununda xəta", "Tarix sütununu düzgün seçin")

    # Məbləğ
    try:
        mebler_raw = df[mebler_s].astype(str)
        mebler_raw = mebler_raw.str.replace(r"[^\d,\.-]", "", regex=True)
        mebler_raw = mebler_raw.str.replace(r"\.(?=.*\.)", "", regex=True)
        mebler_raw = mebler_raw.str.replace(",", ".")
        df[mebler_s] = pd.to_numeric(mebler_raw, errors="coerce")
        null_say = df[mebler_s].isna().sum()
        if null_say > 0:
            hesabat.append(f"⚠️ {null_say} oxunmayan məbləğ silindi")
        df = df[df[mebler_s] > 0]
        if len(df) == 0:
            xeta("Məbləğ sütununda müsbət ədəd tapılmadı",
                 "Məbləğ sütununu düzgün seçin")
        hesabat.append("✅ Məbləğ sütunu təmizləndi")
    except:
        xeta("Məbləğ sütununda xəta", "Məbləğ sütununu düzgün seçin")

    # Məhsul
    if mehsul_s:
        try:
            df[mehsul_s] = df[mehsul_s].astype(str).str.strip().str.title()
            df[mehsul_s] = df[mehsul_s].replace("Nan", "Naməlum")
            hesabat.append("✅ Məhsul adları normallaşdırıldı")
        except:
            hesabat.append("⚠️ Məhsul sütunu tam təmizlənmədi")

    # Kateqoriya
    if kateq_s:
        try:
            df[kateq_s] = df[kateq_s].astype(str).str.strip().str.title()
            df[kateq_s] = df[kateq_s].replace("Nan", "Naməlum")
            hesabat.append("✅ Kateqoriya sütunu təmizləndi")
        except:
            hesabat.append("⚠️ Kateqoriya sütunu tam təmizlənmədi")

    evvel = len(df)
    df = df.drop_duplicates()
    if evvel != len(df):
        hesabat.append(f"🗑️ {evvel - len(df)} dublikat silindi")

    hesabat.append(f"📊 Nəticə: {len(df)} sətir hazırdır")
    return df, hesabat

def numune_fayl_yarat():
    df = pd.DataFrame({
        "Tarix":      ["26/01/2024","15/02/2024","10/03/2024"],
        "Mehsul":     ["Süd 1L","Çörək","Pendir"],
        "Kateqoriya": ["Süd məhsulları","Çörək","Süd məhsulları"],
        "Mebleg":     [2.40, 0.80, 7.20],
        "Miqdar":     [2, 1, 2],
    })
    buf = io.BytesIO()
    df.to_excel(buf, index=False)
    return buf.getvalue()

# ════════════════════════════════════════════════════════
st.title("🛒 Mağaza Satış Paneli")

st.sidebar.header("📂 Data yüklə")
st.sidebar.download_button(
    "📥 Nümunə Excel yüklə",
    data=numune_fayl_yarat(),
    file_name="numune_format.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

yuklenilen = st.sidebar.file_uploader(
    "Excel və ya CSV faylını seç",
    type=["xlsx","xls","csv"]
)

if yuklenilen is None:
    st.info("👈 Sol tərəfdən Excel faylını yükləyin")
    st.markdown("Faylınız hazır deyil? Sol tərəfdən **nümunə formatı** yükləyin.")
    st.stop()

df_raw = fayl_oxu(yuklenilen)

if df_raw is None or len(df_raw) == 0:
    xeta("Fayl boşdur", "Məlumat olan fayl seçin")
if len(df_raw.columns) < 2:
    xeta("Faylda yalnız 1 sütun var", "Ən azı tarix və məbləğ sütunları olmalıdır")

st.sidebar.success(f"✅ {len(df_raw)} sətir yükləndi")

# Avtomatik sütun aşkarlama
auto_tarix, auto_mebler, auto_mehsul, auto_kateq = sutun_tipi_mueyyenles(df_raw)

st.sidebar.header("🔧 Sütunları təsdiqlə")
st.sidebar.caption("Sistem avtomatik seçdi — yanlışsa düzəlt")

sutunlar = list(df_raw.columns)

def get_index(sutunlar, deger, offset=0):
    try:
        return sutunlar.index(deger) + offset if deger else 0
    except:
        return 0

tarix_s = st.sidebar.selectbox(
    "📅 Tarix sütunu", sutunlar,
    index=get_index(sutunlar, auto_tarix)
)
mebler_s = st.sidebar.selectbox(
    "💰 Məbləğ sütunu", sutunlar,
    index=get_index(sutunlar, auto_mebler)
)
mehsul_s = st.sidebar.selectbox(
    "🛍️ Məhsul sütunu", ["(yoxdur)"] + sutunlar,
    index=get_index(sutunlar, auto_mehsul, offset=1)
)
kateq_s = st.sidebar.selectbox(
    "📁 Kateqoriya sütunu", ["(yoxdur)"] + sutunlar,
    index=get_index(sutunlar, auto_kateq, offset=1)
)

mehsul_s = None if mehsul_s == "(yoxdur)" else mehsul_s
kateq_s  = None if kateq_s  == "(yoxdur)" else kateq_s

df, hesabat = temizle(df_raw.copy(), tarix_s, mebler_s, mehsul_s, kateq_s)

with st.sidebar.expander("🧹 Təmizlik hesabatı"):
    for x in hesabat:
        st.write(x)

# KPI
k1, k2, k3 = st.columns(3)
try:
    k1.metric("Ümumi gəlir", f"{df[mebler_s].sum():,.2f} AZN")
except:
    k1.metric("Ümumi gəlir", "—")
try:
    k2.metric("Əməliyyat sayı", f"{len(df):,}")
except:
    k2.metric("Əməliyyat sayı", "—")
try:
    k3.metric("Orta çek", f"{df[mebler_s].mean():.2f} AZN")
except:
    k3.metric("Orta çek", "—")

if mehsul_s:
    try:
        en_cox = df.groupby(mehsul_s)[mebler_s].sum().idxmax()
        st.sidebar.metric("🏆 Ən çox satan", en_cox)
    except:
        pass

st.divider()

g1, g2 = st.columns(2)

with g1:
    try:
        st.subheader("Günlük gəlir")
        gunluk = df.groupby(tarix_s)[mebler_s].sum().reset_index()
        fig1 = px.line(gunluk, x=tarix_s, y=mebler_s,
                       labels={tarix_s:"Tarix", mebler_s:"Gəlir (AZN)"})
        fig1.update_traces(line_color="#7F77DD", line_width=2)
        st.plotly_chart(fig1, use_container_width=True)
    except:
        st.warning("Günlük gəlir qrafiki göstərilmədi — tarix sütununu yoxlayın")

with g2:
    try:
        if kateq_s:
            st.subheader("Kateqoriya üzrə paylanma")
            cat = df.groupby(kateq_s)[mebler_s].sum().reset_index()
            fig2 = px.pie(cat, names=kateq_s, values=mebler_s, hole=0.4)
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.subheader("Aylıq gəlir")
            df["_ay"] = df[tarix_s].dt.to_period("M").astype(str)
            aylik = df.groupby("_ay")[mebler_s].sum().reset_index()
            fig2 = px.bar(aylik, x="_ay", y=mebler_s,
                          labels={"_ay":"Ay", mebler_s:"Gəlir (AZN)"})
            fig2.update_traces(marker_color="#1D9E75")
            st.plotly_chart(fig2, use_container_width=True)
    except:
        st.warning("Kateqoriya qrafiki göstərilmədi")

if mehsul_s:
    try:
        st.subheader("TOP 10 məhsul")
        top = (df.groupby(mehsul_s)[mebler_s]
                 .sum().sort_values(ascending=True).tail(10).reset_index())
        fig3 = px.bar(top, x=mebler_s, y=mehsul_s, orientation="h",
                      labels={mebler_s:"Gəlir (AZN)", mehsul_s:""})
        fig3.update_traces(marker_color="#378ADD")
        st.plotly_chart(fig3, use_container_width=True)
    except:
        st.warning("TOP 10 qrafiki göstərilmədi")

with st.expander("📋 Ətraflı data (ilk 100 sətir)"):
    try:
        st.dataframe(df.head(100), use_container_width=True)
    except:
        st.warning("Cədvəl göstərilmədi")