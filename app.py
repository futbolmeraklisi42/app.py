from datetime import date
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Umut Besicilik - Süt ve Gider Takip Sistemi",
    page_icon="🐄",
    layout="wide",
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

if "expense_logs" not in st.session_state:
    st.session_state.expense_logs = pd.DataFrame(
        columns=["Tarih", "Gider_Turu", "Miktar", "Birim", "Toplam_Tutar_TL"]
    )

if "milk_price" not in st.session_state:
    st.session_state.milk_price = 15.0  # Varsayılan örnek süt kg fiyatı


# Yaş Hesaplama Fonksiyonu
def calculate_age(born):
    today = date.today()
    months = (today.year - born.year) * 12 + today.month - born.month
    years = months // 12
    rem_months = months % 12
    return f"{years} Yaşında ({rem_months} aylık)"


st.title("🐄 Umut Besicilik - Süt ve Masraf Takip Paneli")
st.markdown(
    "Babanın telefonundan rahatça kullanabileceği günlük çiftlik yönetim sistemi."
)

# Üst kısımda Fiyat Ayarı
with st.container():
    st.markdown("### 💰 Süt Satış Fiyatı Ayarı")
    col_p1, col_p2 = st.columns([2, 3])
    with col_p1:
        price_input = st.text_input(
            "Güncel Süt Kilogram Fiyatı (TL)",
            value=str(st.session_state.milk_price),
            placeholder="Örn: 15.5",
        )
    with col_p2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Fiyatı Güncelle"):
            try:
                new_p = float(price_input.replace(",", "."))
                st.session_state.milk_price = new_p
                st.success(
                    f"✅ Süt kg fiyatı başarıyla {new_p} TL olarak güncellendi!"
                )
            except ValueError:
                st.error("⚠️ Lütfen geçerli bir fiyat yazın.")

st.divider()

# Sekmeler
tab1, tab2, tab3, tab4 = st.tabs(
    [
        "📥 Günlük Süt Girişi",
        "🛒 Masraf Girişi (Yem, Saman vb.)",
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
                    "Sabah Sütü (kg)", value="", placeholder="Örn: 12.5"
                )
            with col2:
                evening_input = st.text_input(
                    "Akşam Sütü (kg)", value="", placeholder="Örn: 10"
                )

            submitted = st.form_submit_button("Süt Kaydını Ekle")

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
                        f"✅ {cow_name} için süt eklendi! Toplam: {total_milk} kg"
                    )
                except ValueError:
                    st.error(
                        "⚠️ Lütfen kg alanına geçerli bir sayı yazın (Örn: 12.5 veya 12)."
                    )

    st.divider()
    st.subheader("📋 Son Süt Kayıtları ve Hatalı Giriş Silme")
    if not st.session_state.milking_logs.empty:
        display_logs = st.session_state.milking_logs.copy()
        st.dataframe(
            display_logs.sort_values(by="Tarih", ascending=False),
            use_container_width=True,
            hide_index=True,
        )

        with st.form("delete_log_form"):
            row_to_delete = st.selectbox(
                "Silmek İstediğiniz Süt Kaydını Seçin",
                options=st.session_state.milking_logs.index.tolist(),
                format_func=lambda x: f"Tarih: {st.session_state.milking_logs.loc[x, 'Tarih']} | İnek: {st.session_state.milking_logs.loc[x, 'Inek']} | Toplam: {st.session_state.milking_logs.loc[x, 'Toplam_Kg']} kg",
            )
            delete_log_btn = st.form_submit_button(
                "Seçilen Hatalı Süt Kaydını Sil"
            )

            if delete_log_btn:
                st.session_state.milking_logs = (
                    st.session_state.milking_logs.drop(row_to_delete)
                    .reset_index(drop=True)
                )
                st.success("🗑️ Seçilen süt kaydı silindi!")
                st.rerun()
    else:
        st.info("Henüz süt kaydı girilmedi.")

with tab2:
    st.subheader("🛒 Yem, Saman ve Diğer Giderleri Kaydet")
    st.markdown(
        "Babam marketten/tüccardan yem, saman, arpa vb. aldığında buraya işleyebilir."
    )

    with st.form("expense_form"):
        exp_date = st.date_input("Alışveriş Tarihi", value=date.today())
        exp_type = st.selectbox(
            "Gider Türü",
            [
                "Saman",
                "Kesif Yem",
                "Arpa",
                "Yonca",
                "Veteriner / İlaç",
                "Diğer",
            ],
        )

        col_e1, col_e2 = st.columns(2)
        with col_e1:
            exp_amount = st.text_input(
                "Miktar / Adet", value="", placeholder="Örn: 5 veya 50"
            )
            exp_unit = st.selectbox("Birim", ["Balya", "Çuval", "Kg", "Adet"])
        with col_e2:
            exp_total_price = st.text_input(
                "Ödenen Toplam Tutar (TL)",
                value="",
                placeholder="Örn: 2500",
            )

        exp_submitted = st.form_submit_button("Masrafı Kaydet")

        if exp_submitted:
            try:
                amount_val = (
                    float(exp_amount.replace(",", "."))
                    if exp_amount.strip()
                    else 0.0
                )
                total_price_val = (
                    float(exp_total_price.replace(",", "."))
                    if exp_total_price.strip()
                    else 0.0
                )

                new_exp = pd.DataFrame(
                    {
                        "Tarih": [exp_date],
                        "Gider_Turu": [exp_type],
                        "Miktar": [f"{amount_val} {exp_unit}"],
                        "Toplam_Tutar_TL": [total_price_val],
                    }
                )
                st.session_state.expense_logs = pd.concat(
                    [st.session_state.expense_logs, new_exp], ignore_index=True
                )
                st.success(
                    f"✅ {exp_type} masrafı eklendi! Toplam: {total_price_val:,.2f} TL"
                )
            except ValueError:
                st.error(
                    "⚠️ Lütfen miktar ve tutar alanlarına geçerli sayılar yazın."
                )

    st.divider()
    st.subheader("📋 Yapılan Masraf Geçmişi ve Silme")
    if not st.session_state.expense_logs.empty:
        st.dataframe(
            st.session_state.expense_logs.sort_values(
                by="Tarih", ascending=False
            ),
            use_container_width=True,
            hide_index=True,
        )

        with st.form("delete_expense_form"):
            exp_to_delete = st.selectbox(
                "Silmek İstediğiniz Masrafı Seçin",
                options=st.session_state.expense_logs.index.tolist(),
                format_func=lambda x: f"Tarih: {st.session_state.expense_logs.loc[x, 'Tarih']} | Tür: {st.session_state.expense_logs.loc[x, 'Gider_Turu']} | Tutar: {st.session_state.expense_logs.loc[x, 'Toplam_Tutar_TL']} TL",
            )
            delete_exp_btn = st.form_submit_button(
                "Seçilen Hatalı Masrafı Sil"
            )

            if delete_exp_btn:
                st.session_state.expense_logs = (
                    st.session_state.expense_logs.drop(exp_to_delete)
                    .reset_index(drop=True)
                )
                st.success("🗑️ Seçilen masraf kaydı silindi!")
                st.rerun()
    else:
        st.info("Henüz masraf girilmedi.")

with tab3:
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

with tab4:
    st.subheader("📊 Özet Raporlar, Satış Geliri ve Masraf Analizi")

    today_ts = pd.Timestamp(date.today())
    current_price = st.session_state.milk_price

    # 1. Bugünün Durumu
    st.markdown("### 📅 Bugünün Süt ve Satış Özeti")
    if not st.session_state.milking_logs.empty:
        df_logs = st.session_state.milking_logs.copy()
        df_logs["Tarih"] = pd.to_datetime(df_logs["Tarih"])
        today_logs = df_logs[df_logs["Tarih"] == today_ts]

        if not today_logs.empty:
            today_total_kg = today_logs["Toplam_Kg"].sum()
            today_total_money = today_total_kg * current_price

            col_m1, col_m2 = st.columns(2)
            with col_m1:
                st.metric("Bugün Toplam Alınan Süt", f"{today_total_kg:.1f} kg")
            with col_m2:
                st.metric(
                    "Bugünkü Otomatik Satış Geliri",
                    f"{today_total_money:,.2f} TL",
                )
        else:
            st.info("Bugün için henüz süt kaydı girilmedi.")
    else:
        st.info("Henüz süt kaydı girilmedi.")

    st.divider()

    # 2. Genel Toplam Giderler Özeti
    st.markdown("### 💸 Toplam Masraflar Özeti (Yem, Saman vb.)")
    if not st.session_state.expense_logs.empty:
        df_exp = st.session_state.expense_logs.copy()
        total_expense = df_exp["Toplam_Tutar_TL"].sum()
        st.metric(
            label="Yapılan Toplam Masraf",
            value=f"{total_expense:,.2f} TL",
        )

        st.markdown("**Gider Türlerine Göre Dağılım:**")
        exp_summary = (
            df_exp.groupby("Gider_Turu")["Toplam_Tutar_TL"]
            .sum()
            .reset_index()
        )
        exp_summary.columns = ["Gider Türü", "Toplam Harcanan (TL)"]
        st.dataframe(exp_summary, use_container_width=True, hide_index=True)
    else:
        st.info("Henüz masraf kaydı girilmedi.")

    st.divider()

    # 3. İnek Bazında Süt Dökümü
    st.markdown("### 🐄 İnek Bazında Toplam Süt Miktarları")
    if not st.session_state.milking_logs.empty:
        df_logs = st.session_state.milking_logs.copy()
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
        st.info("İnek bazlı döküm için önce süt kaydı girmelisin.")
