import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import io

st.set_page_config(page_title="Mağaza Analitikası", page_icon="🛒", layout="wide")

# ── Xəta göstərici ──────────────────────────────────────
def xeta(mesaj, ipucu=None):
    st.error(f"⚠️ {mesaj}")
    if ipucu:
        st.info(f"💡 {ipucu}")
    st.stop()

# ── Fayl oxuma ───────────────────────────────────────────
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
        xeta(f"Fayl oxunmadı: {type(e).__name__}", "Faylın açıq olmadığına və zədəli olmadığına əmin olun")

# ── Data təmizləmə ───────────────────────────────────────
def temizle(df, tarix_s, mebler_s, mehsul_s, kateq_s):
    hesabat = []
    df = df.copy()

    # Tamamilə boş sətir/sütunları sil
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
            xeta("Tarix sütununda heç bir oxuna bilən tarix yoxdur",
                 "Tarix formatı: 26/01/2024 və ya 2024-01-26 olmalıdır")
        hesabat.append("✅ Tarix sütunu təmizləndi")
    except Exception as e:
        xeta(f"Tarix sütununda xəta: {type(e).__name__}",
             "Tarix sütununu düzgün seçdiyinizdən əmin olun")

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
            xeta("Məbləğ sütununda heç bir müsbət ədəd tapılmadı",
                 "Məbləğ sütununun düzgün seçildiyindən əmin olun")
        hesabat.append("✅ Məbləğ sütunu təmizləndi")
    except Exception as e:
        xeta(f"Məbləğ sütununda xəta: {type(e).__name__}",
             "Məbləğ sütununda yalnız ədədlər olmalıdır")

    # Məhsul adı
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

    # Dublikatlar
    evvel = len(df)
    df = df.drop_duplicates()
    sonra = len(df)
    if evvel != sonra:
        hesabat.append(f"🗑️ {evvel - sonra} dublikat silindi")

    hesabat.append(f"📊 Nəticə: {len(df)} sətir hazırdır")
    return df, hesabat

# ── Nümunə fayl ─────────────────────────────────────────
def numune_fayl_yarat():
    df = pd.DataFrame({
        "Tarix":       ["26/01/2024","15/02/2024","10/03/2024"],
        "Mehsul":      ["Süd 1L","Çörək","Pendir"],
        "Kateqoriya":  ["Süd məhsulları","Çörək","Süd məhsulları"],
        "Mebleg":      [2.40, 0.80, 7.20],
        "Miqdar":      [2, 1, 2],
    })
    buf = io.BytesIO()
    df.to_excel(buf, index=False)
    return buf.getvalue()

# ════════════════════════════════════════════════════════
st.title("🛒 Mağaza Satış Paneli")

# ── Sidebar ──────────────────────────────────────────────
st.sidebar.header("📂 Data yüklə")

st.sidebar.download_button(
    "📥 Nümunə Excel yüklə",
    data=numune_fayl_yarat(),
    file_name="numune_format.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

yuklenilen = st.sidebar.file_uploader(
    "Excel və ya CSV faylını seç",
    type=["xlsx", "xls", "csv"]
)

if yuklenilen is None:
    st.info("👈 Sol tərəfdən Excel faylını yükləyin")
    st.markdown("**Faylınız hazır deyil?** Sol tərəfdən nümunə formatı yükləyin.")
    st.stop()

# Faylı oxu
df_raw = fayl_oxu(yuklenilen)

if df_raw is None or len(df_raw) == 0:
    xeta("Fayl boşdur", "Məlumat olan fayl seçin")

if len(df_raw.columns) < 2:
    xeta("Faylda yalnız 1 sütun var", "Ən azı tarix və məbləğ sütunları olmalıdır")

st.sidebar.success(f"✅ {len(df_raw)} sətir yükləndi")

# ── Sütun seçimi ─────────────────────────────────────────
st.sidebar.header("🔧 Sütunları seç")
sutunlar = list(df_raw.columns)

def auto_index(sutunlar, açar_sozler, offset=0):
    for i, s in enumerate(sutunlar):
        if any(x in str(s).lower() for x in açar_sozler):
            return i + offset
    return 0

tarix_s = st.sidebar.selectbox(
    "📅 Tarix sütunu", sutunlar,
    index=auto_index(sutunlar, ["tarix","date","tarih","gun","vaxt","time","dt"])
)
mebler_s = st.sidebar.selectbox(
    "💰 Məbləğ sütunu", sutunlar,
    index=auto_index(sutunlar, ["mebler","məbləğ","cemi","total","amount","qiymet","price","summa"])
)
mehsul_s = st.sidebar.selectbox(
    "🛍️ Məhsul sütunu", ["(yoxdur)"] + sutunlar,
    index=auto_index(sutunlar, ["mehsul","məhsul","product","mal","ad","name","item"], offset=1)
)
kateq_s = st.sidebar.selectbox(
    "📁 Kateqoriya sütunu", ["(yoxdur)"] + sutunlar,
    index=auto_index(sutunlar, ["kateq","category","nov","tip","qrup","group"], offset=1)
)

mehsul_s = None if mehsul_s == "(yoxdur)" else mehsul_s
kateq_s  = None if kateq_s  == "(yoxdur)" else kateq_s

# ── Təmizlə ──────────────────────────────────────────────
df, hesabat = temizle(df_raw.copy(), tarix_s, mebler_s, mehsul_s, kateq_s)

with st.sidebar.expander("🧹 Təmizlik hesabatı"):
    for x in hesabat:
        st.write(x)

# ── KPI kartları ─────────────────────────────────────────
k1, k2, k3 = st.columns(3)
k1.metric("Ümumi gəlir",   f"{df[mebler_s].sum():,.2f} AZN")
k2.metric("Əməliyyat sayı", f"{len(df):,}")
k3.metric("Orta çek",       f"{df[mebler_s].mean():.2f} AZN")

if mehsul_s:
    try:
        en_cox = df.groupby(mehsul_s)[mebler_s].sum().idxmax()
        st.sidebar.metric("🏆 Ən çox satan", en_cox)
    except:
        pass

st.divider()

# ── Qrafiklər ────────────────────────────────────────────
g1, g2 = st.columns(2)

with g1:
    try:
        st.subheader("Günlük gəlir")
        gunluk = df.groupby(tarix_s)[mebler_s].sum().reset_index()
        fig1 = px.line(gunluk, x=tarix_s, y=mebler_s,
                       labels={tarix_s: "Tarix", mebler_s: "Gəlir (AZN)"})
        fig1.update_traces(line_color="#7F77DD", line_width=2)
        st.plotly_chart(fig1, use_container_width=True)
    except Exception as e:
        st.warning(f"Günlük gəlir qrafiki göstərilmədi: {type(e).__name__}")

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
                          labels={"_ay": "Ay", mebler_s: "Gəlir (AZN)"})
            fig2.update_traces(marker_color="#1D9E75")
            st.plotly_chart(fig2, use_container_width=True)
    except Exception as e:
        st.warning(f"Kateqoriya qrafiki göstərilmədi: {type(e).__name__}")

if mehsul_s:
    try:
        st.subheader("TOP 10 məhsul")
        top = (df.groupby(mehsul_s)[mebler_s]
                 .sum().sort_values(ascending=True).tail(10).reset_index())
        fig3 = px.bar(top, x=mebler_s, y=mehsul_s, orientation="h",
                      labels={mebler_s: "Gəlir (AZN)", mehsul_s: ""})
        fig3.update_traces(marker_color="#378ADD")
        st.plotly_chart(fig3, use_container_width=True)
    except Exception as e:
        st.warning(f"TOP 10 qrafiki göstərilmədi: {type(e).__name__}")

with st.expander("📋 Ham data (ilk 100 sətir)"):
    try:
        st.dataframe(df.head(100), use_container_width=True)
    except:
        st.warning("Cədvəl göstərilmədi")