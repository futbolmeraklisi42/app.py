from datetime import date
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Umut Besicilik - Süt Takip Sistemi", page_icon="🐄", layout="wide"
)

# 1. Başlangıç Verileri (Session State)
if "cows" not in st.session_state:
    st.session_state.cows = pd.DataFrame(
        {
            "Inek_ID": ["İnek 1 (Sarıkız)", "İnek 2 (Benekli)", "İnek 3 (Yıldız)", "İnek 4 (Kınalı)", "İnek 5 (Doru)", "İnek 6 (Papatya)", "İnek 7 (Zeytin)"],
            "Dogum_Tarihi": [
                date(2020, 3, 15),
                date(2019, 5, 10),
                date(2021, 2, 20),
                date(2018, 8, 12),
                date(2022, 1, 5),
                date(2020, 11, 25),
                date(2021, 6, 18),
            ],
            T_Kuru_Donem: [False, False, False, False, False, False, False],
        }
    )

if "milking_logs" not in st.session_state:
    # Örnek boş veya başlangıç kayıt tablosu
    st.session_state.milking_logs = pd.DataFrame(
        columns=["Tarih", "Inek", "Sabah_Litre", "Aksam_Litre", "Toplam_Litre"]
    )


# Yaş Hesaplama Fonksiyonu
def calculate_age(born):
    today = date.today()
    age = (
        today.year
        - born.year
        - ((today.month, today.day) < (born.month, born.day))
    )
    # Kaç yıl kaç ay olduğunu da hesaplayalım
    months = (today.year - born.year) * 12 + today.month - born.month
    years = months // 12
    rem_months = months % 12
    return f"{years} Yaşında ({rem_months} aylık)"


st.title("🐄 Umut Besicilik - Süt ve İnek Takip Paneli")
st.markdown("Babanın telefonundan rahatça kullanabileceği günlük sağım takip sistemi.")

# Sekmeler
tab1, tab2, tab3 = st.tabs(
    ["📥 Günlük Sağım Girişi", "🐄 İnekler ve Yaş Takibi", "📊 Raporlar ve Özet"]
)

with tab1:
    st.subheader("Bugünkü Süt Tartımını Kaydet")

    with st.form("milking_form"):
        selected_date = st.date_input("Sağım Tarihi", value=date.today())
        cow_name = st.selectbox(
            "İnek Seçin", st.session_state.cows["Inek_ID"].tolist()
        )

        col1, col2 = st.columns(2)
        with col1:
            morning_milk = st.number_input(
                "Sabah Sütü (Litre)", min_value=0.0, step=0.1, format="%.1f"
            )
        with col2:
            evening_milk = st.number_input(
                "Akşam Sütü (Litre)", min_value=0.0, step=0.1, format="%.1f"
            )

        submitted = st.form_submit_button("Kaydı Ekle")

        if submitted:
            total_milk = morning_milk + evening_milk
            new_row = pd.DataFrame(
                {
                    "Tarih": [selected_date],
                    "Inek": [cow_name],
                    "Sabah_Litre": [morning_milk],
                    "Aksam_Litre": [evening_milk],
                    "Toplam_Litre": [total_milk],
                }
            )
            st.session_state.milking_logs = pd.concat(
                [st.session_state.milking_logs, new_row], ignore_index=True
            )
            st.success(
                f"✅ {cow_name} için kayıt eklendi! Toplam: {total_milk} Litre"
            )

    st.divider()
    st.subheader("Son Yapılan Kayıtlar")
    if not st.session_state.milking_logs.empty:
        st.dataframe(
            st.session_state.milking_logs.sort_values(
                by="Tarih", ascending=False
            ),
            use_container_width=True,
        )
    else:
        st.info("Henüz kayıt girilmedi.")

with tab2:
    st.subheader("İnek Listesi ve Yaş Durumu")
    st.markdown(
        "İneklerin doğum tarihlerine göre güncel yaşları her gün otomatik hesaplanır."
    )

    # Yaşları tabloya ekleyelim
    display_df = st.session_state.cows.copy()
    display_df["Guncel_Yas"] = display_df["Dogum_Tarihi"].apply(calculate_age)

    st.dataframe(
        display_df[["Inek_ID", "Dogum_Tarihi", "Guncel_Yas"]],
        use_container_width=True,
    )

    with st.expander("Yeni İnek Ekle / Düzenle"):
        with st.form("new_cow_form"):
            new_id = st.text_input("İnek Adı / Numarası")
            new_birth = st.date_input(
                "Doğum Tarihi", value=date(2021, 1, 1)
            )
            add_cow_btn = st.form_submit_button("İneği Kaydet")

            if add_cow_btn and new_id:
                if new_id in st.session_state.cows["Inek_ID"].values:
                    st.warning("Bu isimde bir inek zaten var!")
                else:
                    new_cow_row = pd.DataFrame(
                        {
                            "Inek_ID": [new_id],
                            "Dogum_Tarihi": [new_birth],
                            "T_Kuru_Donem": [False],
                        }
                    )
                    st.session_state.cows = pd.concat(
                        [st.session_state.cows, new_cow_row], ignore_index=True
                    )
                    st.success(f"'{new_id}' sisteme eklendi!")
                    st.rerun()

with tab3:
    st.subheader("Genel Süt Verim Analizi")
    if not st.session_state.milking_logs.empty:
        df_logs = st.session_state.milking_logs
        total_sum = df_logs["Toplam_Litre"].sum()
        st.metric(
            label="Toplam Üretilen Süt (Sezon/Tüm Zamanlar)",
            value=f"{total_sum:.1f} Litre",
        )

        # İneklere göre dağılım
        cow_summary = (
            df_logs.groupby("Inek")["Toplam_Litre"].sum().reset_index()
        )
        st.bar_chart(cow_summary.set_index("Inek"))
    else:
        st.info("Grafik oluşturmak için önce günlük süt kaydı girmelisin.")
