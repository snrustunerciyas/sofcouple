# ========== GEREKLİ KÜTÜPHANELER ==========
import streamlit as st
import os
import json
import random
import string
import pandas as pd
import matplotlib.pyplot as plt
import io
from fpdf import FPDF
from math import pi
from sorular import sorular

# ========== TEMA ==========
st.set_page_config(page_title="Project Velvet", page_icon="🧩", layout="centered")
st.title("🧩 Project Velvet")
st.caption("Partner Eşleştirme & Öneri Sistemi")

# ========== YARDIMCI FONKSİYONLAR ==========
def rastgele_oturum_kodu(uzunluk=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=uzunluk))

def renk_kodla(v):
    if v < 3.5:
        return 'background-color: #ffcccc'  # kırmızı
    elif v < 5:
        return 'background-color: #fff3cd'  # sarı
    else:
        return 'background-color: #d4edda'  # yeşil

def radar_chart(df):
    categories = list(df["Kategori"])
    values = list(df["Ortalama"])
    N = len(categories)
    values += values[:1]
    angles = [n / float(N) * 2 * pi for n in range(N)] + [0]
    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    ax.set_theta_offset(pi / 2)
    ax.set_theta_direction(-1)
    plt.xticks(angles[:-1], categories)
    ax.plot(angles, values, linewidth=1, linestyle='solid')
    ax.fill(angles, values, alpha=0.3)
    st.pyplot(fig)

def pdf_olustur(kategori_df, detay_df):
    pdf = FPDF()
    pdf.add_page()
    font_path = os.path.join("fonts", "DejaVuSans.ttf")
    pdf.add_font('DejaVu', '', font_path, uni=True)
    pdf.set_font('DejaVu', '', 12)
    pdf.cell(200, 10, txt="Project Velvet - Rapor", ln=True, align='C')
    pdf.ln(10)
    pdf.cell(200, 10, txt="Kategori Ortalamaları", ln=True)
    for _, row in kategori_df.sort_values(by="Ortalama", ascending=False).iterrows():
        pdf.cell(200, 8, txt=f"{row['Kategori']}: {row['Ortalama']}", ln=True)
    pdf.ln(5)
    pdf.cell(200, 10, txt="Detaylı Soru Ortalamaları", ln=True)
    for _, row in detay_df.sort_values(by="Ortalama", ascending=False).iterrows():
        pdf.multi_cell(0, 8, txt=f"{row['Soru']} ({row['Kategori']}) → {row['Ortalama']}")
    buffer = io.BytesIO()
    pdf_bytes = pdf.output(dest='S').encode('latin1')
    buffer.write(pdf_bytes)
    buffer.seek(0)
    return buffer

# ========== ÖNERİ SİSTEMİ ==========
def onerileri_getir(detay_df):
    detay_yesil = detay_df[(detay_df["Ortalama"] >= 5) & (detay_df["Ortalama"] <= 7)].sort_values(by="Ortalama", ascending=False).to_dict(orient="records")
    detay_sari = detay_df[(detay_df["Ortalama"] >= 3.5) & (detay_df["Ortalama"] < 5)].sort_values(by="Ortalama", ascending=False).to_dict(orient="records")
    
    oneriler = []
    if detay_yesil:
        oneriler.append(("Kuvvetli Öneri", random.choice(detay_yesil)))
    if detay_sari:
        oneriler.append(("Denemeye Değer", random.choice(detay_sari)))
    return oneriler


# ========== OTURUM GİRİŞİ ==========
st.header("📝 Anket Katılımı")
col1, col2, col3 = st.columns(3)
with col1:
    rol_sec = st.radio("Rolünüzü seçin:", ["Partner1 (Oturum oluştur)", "Partner2 (Oturuma katıl)"])
with col2:
    isim = st.text_input("İsminizi girin:")
with col3:
    yas = st.number_input("Yaşınız:", min_value=18, max_value=100, step=1)
cinsiyet = st.radio("Cinsiyetiniz:", ["Kadın", "Erkek", "Diğer", "Belirtmek istemiyorum"], horizontal=True)

if rol_sec == "Partner1 (Oturum oluştur)":
    if "session_id" not in st.session_state:
        st.session_state["session_id"] = rastgele_oturum_kodu()
    session_id = st.text_input("Otomatik oluşturulan oturum kodu:", value=st.session_state["session_id"], disabled=True)
    st.info("🔑 Bu kodu partnerinizle paylaşın.")
    partner_rol = "partner1"
else:
    session_id = st.text_input("Partnerinizin verdiği oturum kodunu girin:")
    st.session_state["session_id"] = session_id
    partner_rol = "partner2"

# ========== ANKET CEVAPLARI ==========
if isim and session_id:
    cevap_objesi = {
        "isim": isim,
        "yas": yas,
        "cinsiyet": cinsiyet,
        "cevaplar": [],
        "toplam_skor": 0
    }
    cevaplar = []
    toplam_skor = 0
    st.markdown("---")
    st.subheader("📋 Anket Soruları")
    for s in sorular:
        secenekler_keys = list(s["secenekler"].keys())
        default_cevap = secenekler_keys.index("Nötr") if "Nötr" in secenekler_keys else 0
        with st.expander(s["soru"]):
            secim = st.radio("Cevabınızı seçin:", secenekler_keys, key=s["id"], index=default_cevap)
            puan = s["secenekler"][secim]
            cevaplar.append({"soru_id": s["id"], "kategori": s["kategori"], "cevap": secim, "puan": puan})
            cevap_objesi["cevaplar"].append({"soru_id": s["id"], "kategori": s["kategori"], "cevap": secim, "puan": puan})
            cevap_objesi["toplam_skor"] += puan
            toplam_skor += puan

    if st.button("✅ Anketi Bitir ve Kaydet"):
        os.makedirs("sessions", exist_ok=True)
        dosya_adi = f"sessions/{session_id}.json"
        if os.path.exists(dosya_adi):
            with open(dosya_adi, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = {}
        data[partner_rol] = cevap_objesi
        with open(dosya_adi, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        st.success("✅ Anket tamamlandı ve cevaplar kaydedildi.")

# ========== ANALİZ VE ÖNERİLER ==========
if "session_id" in st.session_state:
    dosya_adi = f"sessions/{st.session_state['session_id']}.json"
    if os.path.exists(dosya_adi):
        with open(dosya_adi, "r", encoding="utf-8") as f:
            data = json.load(f)
        if "partner1" in data and "partner2" in data:
            tum_cevaplar = data["partner1"]["cevaplar"] + data["partner2"]["cevaplar"]
            kategori_df = pd.DataFrame(tum_cevaplar).groupby("kategori")["puan"].mean().reset_index()
            kategori_df.rename(columns={"puan": "Ortalama", "kategori": "Kategori"}, inplace=True)
            kategori_df = kategori_df.sort_values(by="Ortalama", ascending=False).reset_index(drop=True)
            kategori_df.index += 1
            kategori_df.insert(0, "#", kategori_df.index)

            soru_ortalamalari = []
            for soru in sorular:
                ilgili = [c for c in tum_cevaplar if c["soru_id"] == soru["id"]]
                if len(ilgili) == 2:
                    ort = round(sum([c["puan"] for c in ilgili]) / 2, 2)
                    soru_ortalamalari.append({
                        "#": len(soru_ortalamalari)+1,
                        "Soru": soru["soru"],
                        "Kategori": soru["kategori"],
                        "Ortalama": ort
                    })
            detay_df = pd.DataFrame(soru_ortalamalari)

            st.markdown("---")
            st.subheader("📊 Radar Grafiği")
            radar_chart(kategori_df)

            st.subheader("📋 Kategori Ortalamaları")
            st.dataframe(kategori_df.style.applymap(renk_kodla, subset=["Ortalama"]))

            st.subheader("📋 Detaylı Sorular")
            st.dataframe(detay_df.style.applymap(renk_kodla, subset=["Ortalama"]))

            st.download_button("⬇️ PDF Raporu İndir", data=pdf_olustur(kategori_df, detay_df), file_name="rapor.pdf")

            if "oneriler" not in st.session_state:
                st.session_state["oneriler"] = []

            if st.button("🎲 Rastgele Öneri Göster"):
                st.session_state["oneriler"] = onerileri_getir(detay_df)

            for baslik, o in st.session_state["oneriler"]:
                st.success(f"**{baslik}**: {o['Soru']} _(Ortalama: {o['Ortalama']})_")
        else:
            st.info("👥 Rastgele öneri alabilmek için iki partnerin de oturumu tamamlamış olması gerekir.")
