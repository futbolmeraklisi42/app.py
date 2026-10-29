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
            "Inek_ID": [
                "İnek 1 (Sarıkız)",
                "İnek 2 (Benekli)",
                "İnek 3 (Yıldız)",
                "İnek 4 (Kınalı)",
                "İnek 5 (Doru)",
                "İnek 6 (Papatya)",
                "İnek 7 (Zeytin)",
            ],
            "Dogum_Tarihi": [
                date(2020, 3, 15),
                date(2019, 5, 10),
                date(2021, 2, 20),
                date(2018, 8, 12),
                date(2022, 1, 5),
                date(2020, 11, 25),
                date(2021, 6, 18),
            ],
            "T_Kuru_Donem": [
                False,
                False,
                False,
                False,
                False,
                False,
                False,
            ],
        }
    )

if "milking_logs" not in st.session_state:
    st.session_state.milking_logs = pd.DataFrame(
        columns=["Tarih", "Inek", "Sabah_Kg", "Aksam_Kg", "Toplam_Kg"]
    )


# Yaş Hesaplama Fonksiyonu
def calculate_age(born):
    today = date.today()
    months = (today.year - born.year) * 12 + today.month - born.month
    years = months // 12
    rem_months = months % 12
    return f"{years} Yaşında ({rem_months} aylık)"


st.title("🐄 Umut Besicilik - Süt ve İnek Takip Paneli")
st.markdown("Babanın telefonundan rahatça kullanabileceği günlük sağım sistemi.")

# Sekmeler
tab1, tab2, tab3 = st.tabs(
    [
        "📥 Günlük Sağım Girişi & Düzeltme",
        "🐄 İnekler ve Yaş Takibi",
        "📊 Raporlar ve Özet",
    ]
)

with tab1:
    st.subheader("Bugünkü Süt Tartımını Kaydet (Kilogram - kg)")

    if st.session_state.cows.empty:
        st.warning(
            "⚠️ Önce 'İnekler ve Yaş Takibi' sekmesinden en az bir inek eklemelisin!"
        )
    else:
        with st.form("milking_form"):
            selected_date = st.date_input("Sağım Tarihi", value=date.today())
            cow_name = st.selectbox(
                "İnek Seçin", st.session_state.cows["Inek_ID"].tolist()
            )

            col1, col2 = st.columns(2)
            with col1:
                morning_input = st.text_input(
                    "Sabah Sütü (Kilogram - kg)",
                    value="",
                    placeholder="Örn: 12.5 veya 12",
                )
            with col2:
                evening_input = st.text_input(
                    "Akşam Sütü (Kilogram - kg)",
                    value="",
                    placeholder="Örn: 10 veya 10.5",
                )

            submitted = st.form_submit_button("Kaydı Ekle")

            if submitted:
                try:
                    morning_milk = (
                        float(morning_input.replace(",", "."))
                        if morning_input.strip()
                        else 0.0
                    )
                    evening_milk = (
                        float(evening_input.replace(",", "."))
                        if evening_input.strip()
                        else 0.0
                    )
                    total_milk = morning_milk + evening_milk

                    new_row = pd.DataFrame(
                        {
                            "Tarih": [selected_date],
                            "Inek": [cow_name],
                            "Sabah_Kg": [morning_milk],
                            "Aksam_Kg": [evening_milk],
                            "Toplam_Kg": [total_milk],
                        }
                    )
                    st.session_state.milking_logs = pd.concat(
                        [st.session_state.milking_logs, new_row],
                        ignore_index=True,
                    )
                    st.success(
                        f"✅ {cow_name} için kayıt eklendi! Toplam: {total_milk} kg"
                    )
                except ValueError:
                    st.error(
                        "⚠️ Lütfen kg alanına geçerli bir sayı yazın (Örn: 12.5 veya 12)."
                    )

    st.divider()
    st.subheader("📋 Son Yapılan Kayıtlar ve Yanlış Giriş Düzeltme / Silme")
    if not st.session_state.milking_logs.empty:
        st.markdown(
            "Eğer yanlış bir kilo girdiysen, aşağıdan o kaydı seçip silebilir ve yeniden doğru şekilde girebilirsin."
        )

        # Tabloyu gösterelim
        display_logs = st.session_state.milking_logs.copy()
        display_logs["Kayıt_ID"] = display_logs.index
        st.dataframe(
            display_logs.sort_values(by="Tarih", ascending=False),
            use_container_width=True,
            hide_index=True,
        )

        # Kayıt Silme Formu
        with st.form("delete_log_form"):
            row_to_delete = st.selectbox(
                "Silmek İstediğiniz Kaydı Seçin",
                options=st.session_state.milking_logs.index.tolist(),
                format_func=lambda x: f"Tarih: {st.session_state.milking_logs.loc[x, 'Tarih']} | İnek: {st.session_state.milking_logs.loc[x, 'Inek']} | Sabah: {st.session_state.milking_logs.loc[x, 'Sabah_Kg']} kg | Akşam: {st.session_state.milking_logs.loc[x, 'Aksam_Kg']} kg",
            )
            delete_log_btn = st.form_submit_button("Seçilen Hatalı Kaydı Sil")

            if delete_log_btn:
                st.session_state.milking_logs = (
                    st.session_state.milking_logs.drop(row_to_delete)
                    .reset_index(drop=True)
                )
                st.success("🗑️ Seçilen hatalı kayıt silindi!")
                st.rerun()
    else:
        st.info("Henüz kayıt girilmedi.")

with tab2:
    st.subheader("İnek Listesi ve Yaş Durumu")
    st.markdown(
        "Sistemdeki kayıtlı inekleri buradan yönetebilir, yenilerini ekleyebilir veya listeden silebilirsin."
    )

    if not st.session_state.cows.empty:
        display_df = st.session_state.cows.copy()
        display_df["Guncel_Yas"] = display_df["Dogum_Tarihi"].apply(
            calculate_age
        )

        st.dataframe(
            display_df[["Inek_ID", "Dogum_Tarihi", "Guncel_Yas"]],
            use_container_width=True,
        )

        # İnek Silme Bölümü
        st.markdown("---")
        st.subheader("🗑️ İnek Sil")
        with st.form("delete_cow_form"):
            cow_to_delete = st.selectbox(
                "Silmek istediğiniz ineği seçin",
                st.session_state.cows["Inek_ID"].tolist(),
            )
            delete_btn = st.form_submit_button("Seçilen İneği Sil")

            if delete_btn:
                st.session_state.cows = st.session_state.cows[
                    st.session_state.cows["Inek_ID"] != cow_to_delete
                ].reset_index(drop=True)
                st.success(f"'{cow_to_delete}' sistemden silindi!")
                st.rerun()
    else:
        st.info("Sistemde kayıtlı hiç inek yok.")

    st.markdown("---")
    st.subheader("➕ Yeni İnek Ekle")
    with st.form("new_cow_form"):
        new_id = st.text_input(
            "İnek Adı / Numarası", placeholder="Örn: İnek 8 veya Kınalı"
        )
        new_birth = st.date_input("Doğum Tarihi", value=date(2021, 1, 1))
        add_cow_btn = st.form_submit_button("İneği Kaydet")

        if add_cow_btn:
            if not new_id.strip():
                st.warning("Lütfen bir inek adı veya numarası yazın!")
            elif new_id in st.session_state.cows["Inek_ID"].values:
                st.warning("Bu isimde bir inek zaten var!")
            else:
                new_cow_row = pd.DataFrame(
                    {
                        "Inek_ID": [new_id.strip()],
                        "Dogum_Tarihi": [new_birth],
                        "T_Kuru_Donem": [False],
                    }
                )
                st.session_state.cows = pd.concat(
                    [st.session_state.cows, new_cow_row], ignore_index=True
                )
                st.success(f"'{new_id}' sisteme başarıyla eklendi!")
                st.rerun()

with tab3:
    st.subheader("📊 Özet Raporlar ve Akıllı Analiz")

    if not st.session_state.milking_logs.empty:
        df_logs = st.session_state.milking_logs.copy()
        df_logs["Tarih"] = pd.to_datetime(df_logs["Tarih"])
        today_ts = pd.Timestamp(date.today())

        # 1. Bugünün Durumu
        st.markdown("### 📅 Bugünün Süt Özeti")
        today_logs = df_logs[df_logs["Tarih"] == today_ts]
        if not today_logs.empty:
            today_total = today_logs["Toplam_Kg"].sum()
            st.metric("Bugün Toplam Alınan Süt", f"{today_total:.1f} kg")
            st.markdown("**Bugün İneklere Göre Alınan Sütler:**")
            for _, row in today_logs.iterrows():
                st.write(
                    f"- **{row['Inek']}**: Sabah `{row['Sabah_Kg']} kg` | Akşam `{row['Aksam_Kg']} kg` | Toplam: **{row['Toplam_Kg']} kg**"
                )
        else:
            st.info("Bugün için henüz süt kaydı girilmedi.")

        st.divider()

        # 2. Haftalık Karşılaştırma Analizi
        st.markdown("### 📈 Haftalık Karşılaştırma ve Analiz")
        week_ago = today_ts - pd.Timedelta(days=7)
        two_weeks_ago = today_ts - pd.Timedelta(days=14)

        this_week_df = df_logs[
            (df_logs["Tarih"] > week_ago) & (df_logs["Tarih"] <= today_ts)
        ]
        last_week_df = df_logs[
            (df_logs["Tarih"] > two_weeks_ago) & (df_logs["Tarih"] <= week_ago)
        ]

        this_week_total = this_week_df["Toplam_Kg"].sum()
        last_week_total = last_week_df["Toplam_Kg"].sum()

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Son 7 Günlük Toplam Süt", f"{this_week_total:.1f} kg")
        with col2:
            st.metric(
                "Önceki 7 Günlük Toplam Süt", f"{last_week_total:.1f} kg"
            )

        st.markdown("#### 💡 Babaya Özel Özet Yorum:")
        if not last_week_df.empty and not this_week_df.empty:
            diff = this_week_total - last_week_total
            if diff > 0:
                st.success(
                    f"🟢 Harika! Bu hafta geçen haftaya göre **{diff:.1f} kg daha fazla** süt alındı."
                )
            elif diff < 0:
                st.warning(
                    f"⚠️ Dikkat: Bu hafta geçen haftaya göre **{abs(diff):.1f} kg daha az** süt alındı."
                )
            else:
                st.info(
                    "ℹ️ Bu hafta ile geçen haftanın süt verimi tam olarak aynı seviyede."
                )
        else:
            st.info(
                "Geçen hafta ile kıyaslama yapabilmek için son 2 haftaya ait düzenli kayıtlar gerekiyor."
            )

        st.divider()

        # 3. İnek İnek Tüm Zamanlar Dökümü
        st.markdown("### 🐄 İnek Bazında Toplam Süt Miktarları")
        cow_summary = (
            df_logs.groupby("Inek")[["Sabah_Kg", "Aksam_Kg", "Toplam_Kg"]]
            .sum()
            .reset_index()
        )
        cow_summary.columns = [
            "İnek Adı",
            "Toplam Sabah (kg)",
            "Toplam Akşam (kg)",
            "Genel Toplam (kg)",
        ]
        st.dataframe(cow_summary, use_container_width=True, hide_index=True)

    else:
        st.info("Raporları ve analizleri görebilmek için önce süt kaydı girmelisin.")
