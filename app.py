from datetime import date
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Umut Besicilik - Çiftlik Yönetim Sistemi",
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
        columns=["Tarih", "Toplam_Kg"]
    )

if "expense_logs" not in st.session_state:
    st.session_state.expense_logs = pd.DataFrame(
        columns=["Tarih", "Gider_Turu", "Miktar", "Toplam_Tutar_TL"]
    )

if "milk_price" not in st.session_state:
    st.session_state.milk_price = 15.0  # Varsayılan süt kg fiyatı


# Yaş Hesaplama Fonksiyonu
def calculate_age(born):
    today = date.today()
    months = (today.year - born.year) * 12 + today.month - born.month
    years = months // 12
    rem_months = months % 12
    return f"{years} Yaşında ({rem_months} aylık)"


st.title("🐄 Umut Besicilik - Çiftlik Yönetim Paneli")
st.markdown("Babanın telefonundan tek tıkla süt, masraf ve kâr-zarar takibi.")

# -------------------------------------------------------------
# ANA SAYFA / ÜST BÖLÜM: AYLIK FİNANSAL DURUM VE KÂR/ZARAR ÖZETİ
# -------------------------------------------------------------
st.markdown("### 💵 Aylık Kâr / Zarar ve Finansal Durum")

col_f1, col_f2 = st.columns([2, 3])
with col_f1:
    price_input = st.text_input(
        "Güncel Süt Kg Fiyatı (TL)",
        value=str(st.session_state.milk_price),
        placeholder="Örn: 15.5",
    )
with col_f2:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Fiyatı Güncelle"):
        try:
            new_p = float(price_input.replace(",", "."))
            st.session_state.milk_price = new_p
            st.success(f"✅ Süt fiyatı {new_p} TL olarak güncellendi!")
            st.rerun()
        except ValueError:
            st.error("⚠️ Geçerli bir fiyat girin.")

current_price = st.session_state.milk_price
today = date.today()

# Aylık Hesaplamalar İçin Tarih Süzme
df_milk = st.session_state.milking_logs.copy()
df_exp = st.session_state.expense_logs.copy()

current_month_milk_income = 0.0
current_month_expense = 0.0

if not df_milk.empty:
    df_milk["Tarih"] = pd.to_datetime(df_milk["Tarih"])
    month_milk = df_milk[
        (df_milk["Tarih"].dt.year == today.year)
        & (df_milk["Tarih"].dt.month == today.month)
    ]
    total_kg_month = month_milk["Toplam_Kg"].sum()
    current_month_milk_income = total_kg_month * current_price

if not df_exp.empty:
    df_exp["Tarih"] = pd.to_datetime(df_exp["Tarih"])
    month_exp = df_exp[
        (df_exp["Tarih"].dt.year == today.year)
        & (df_exp["Tarih"].dt.month == today.month)
    ]
    current_month_expense = month_exp["Toplam_Tutar_TL"].sum()

net_profit = current_month_milk_income - current_month_expense

# Gösterge Kartları (2. Görseldeki Gibi Büyük Gösterge)[cite: 2]
col_k1, col_k2, col_k3 = st.columns(3)
with col_k1:
    st.metric(
        "Bu Ayki Süt Geliri",
        f"{current_month_milk_income:,.2f} TL",
        help=f"Kg fiyatı ({current_price} TL) üzerinden otomatik hesaplandı.",
    )
with col_k2:
    st.metric(
        "Bu Ayki Toplam Masraf",
        f"{current_month_expense:,.2f} TL",
        help="Bu ay yapılan toplam harcama.",
    )
with col_k3:
    st.metric(
        "Bu Ayki NET KÂR / ZARAR",
        f"{net_profit:,.2f} TL",
        delta=f"{net_profit:,.2f} TL",
    )

# Durum Değerlendirme Mesajı
if net_profit > 0:
    st.success(
        f"🟢 **DURUM HARİKA (ARTIDAYIZ):** Bu ay Umut Besicilik masraflar çıktıktan sonra **{net_profit:,.2f} TL** net kârda!"
    )
elif net_profit < 0:
    st.error(
        f"🔴 **DURUM EKSİDE (ZARAR / TOPLU ALIM):** Bu ay yapılan masraflar süt gelirini geçti. (Eğer toplu saman/yem alındıysa bu normaldir, uzun vadeli stok yapılmıştır.) Şu an **{abs(net_profit):,.2f} TL** fark var."
    )
else:
    st.info(
        "ℹ️ Bu ay henüz gelir veya gider dengesi başa baş (0 TL) seviyesinde."
    )

st.divider()

# -------------------------------------------------------------
# SEKMELER
# -------------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs(
    [
        "📥 Günlük Toplam Süt Girişi",
        "🛒 Masraf Girişi (Yem, Saman)",
        "🐄 İnekler ve Yaş Takibi",
        "📊 Detaylı Raporlar ve Özet",
    ]
)

with tab1:
    st.subheader("Bugünkü Toplam Süt Tartımını Kaydet (Kg)")
    st.markdown(
        "Bütün ineklerden sağlanan toplam sütü tek seferde buraya yazabilirsiniz[cite: 1, 2]."
    )

    with st.form("milking_form"):
        selected_date = st.date_input("Sağım Tarihi", value=date.today())
        total_milk_input = st.text_input(
            "Bugünkü Toplam Süt Miktarı (kg)",
            value="",
            placeholder="Örn: 120.5 veya 115",
        )

        submitted = st.form_submit_button("Toplam Süt Kaydını Ekle")

        if submitted:
            try:
                total_milk = (
                    float(total_milk_input.replace(",", "."))
                    if total_milk_input.strip()
                    else 0.0
                )

                new_row = pd.DataFrame(
                    {
                        "Tarih": [selected_date],
                        "Toplam_Kg": [total_milk],
                    }
                )
                st.session_state.milking_logs = pd.concat(
                    [st.session_state.milking_logs, new_row], ignore_index=True
                )
                st.success(
                    f"✅ Toplam süt kaydedildi: **{total_milk} kg** (Otomatik satıldı ve gelir eklendi!)"
                )
                st.rerun()
            except ValueError:
                st.error(
                    "⚠️ Lütfen kg alanına geçerli bir sayı yazın (Örn: 125.5)."
                )

    st.divider()
    st.subheader("📋 Son Süt Kayıtları ve Yanlış Giriş Silme")
    if not st.session_state.milking_logs.empty:
        st.markdown(
            "Kayıtlı son işlemleriniz aşağıdadır. Hatalı olanı listeden seçip silebilirsiniz:"
        )

        for idx, row in st.session_state.milking_logs.tail(5).iterrows():
            st.info(
                f"📅 **{pd.to_datetime(row['Tarih']).strftime('%d.%m.%Y')}** | "
                f"Toplam Sağım: **{row['Toplam_Kg']} kg**"
            )

        with st.form("delete_log_form"):
            row_to_delete = st.selectbox(
                "Silmek İstediğiniz Kaydı Seçin",
                options=st.session_state.milking_logs.index.tolist(),
                format_func=lambda x: f"Tarih: {st.session_state.milking_logs.loc[x, 'Tarih']} | Toplam: {st.session_state.milking_logs.loc[x, 'Toplam_Kg']} kg",
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
        "İster 2 haftalık, ister 1 yıllık olsun; aldığınız ürünü ve ödediğiniz toplam parayı buraya yazabilirsiniz."
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
                "Miktar / Adet", value="", placeholder="Örn: 50 veya 5"
            )
            exp_unit = st.selectbox(
                "Birim", ["Balya", "Çuval", "Kg", "Ton", "Adet"]
            )
        with col_e2:
            exp_total_price = st.text_input(
                "Ödenen Toplam Tutar (TL)",
                value="",
                placeholder="Örn: 25000",
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
                st.rerun()
            except ValueError:
                st.error(
                    "⚠️ Lütfen miktar ve tutar alanlarına geçerli sayılar yazın."
                )

    st.divider()
    st.subheader("📋 Yapılan Masraf Geçmişi ve Silme")
    if not st.session_state.expense_logs.empty:
        for idx, row in st.session_state.expense_logs.tail(5).iterrows():
            st.warning(
                f"📅 **{pd.to_datetime(row['Tarih']).strftime('%d.%m.%Y')}** | "
                f"🛒 **{row['Gider_Turu']}** ({row['Miktar']}) -> "
                f"Tutar: **{row['Toplam_Tutar_TL']:,.2f} TL**"
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
    st.subheader("İnek Listesi ve Otomatik Yaş Takibi")
    st.markdown(
        "Buradan ineklerinizi ekleyebilir, yaşlarını otomatik görebilir ya da silebilirsiniz."
    )

    if not st.session_state.cows.empty:
        for idx, row in st.session_state.cows.iterrows():
            yas_metni = calculate_age(row["Dogum_Tarihi"])
            st.info(
                f"🐄 **{row['Inek_ID']}** | Doğum Tarihi: {row['Dogum_Tarihi']} | Yaşı: **{yas_metni}**"
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
                st.warning("Lütfen bir inek adı yazın!")
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
                st.success(f"'{new_id}' sisteme eklendi!")
                st.rerun()

with tab4:
    st.subheader("📊 Büyük Kartlı Raporlar ve Çiftlik Analizi")
    st.markdown(
        "Babanın zorlanmadan, tek bakışta görebileceği büyük rakamlı kart özetleri[cite: 2]:"
    )

    # 1. Gider Türlerine Göre Büyük Kartlar[cite: 2]
    st.markdown("### 💸 Gider Türlerine Göre Toplam Harcamalar")
    if not st.session_state.expense_logs.empty:
        exp_summary = (
            st.session_state.expense_logs.groupby("Gider_Turu")[
                "Toplam_Tutar_TL"
            ]
            .sum()
            .reset_index()
        )

        cols = st.columns(min(len(exp_summary), 4) if len(exp_summary) > 0 else 1)
        for idx, row in exp_summary.iterrows():
            with cols[idx % len(cols)]:
                st.metric(
                    label=f"📌 {row['Gider_Turu']}",
                    value=f"{row['Toplam_Tutar_TL']:,.2f} TL",
                )
    else:
        st.info("Masraf dökümü için önce masraf kaydı girmelisin.")

    st.divider()

    # 2. Genel Süt ve Haftalık Karşılaştırma Analizi
    st.markdown("### 📈 Süt Verimi ve Haftalık Karşılaştırma")
    if not st.session_state.milking_logs.empty:
        df_logs_analysis = st.session_state.milking_logs.copy()
        df_logs_analysis["Tarih"] = pd.to_datetime(df_logs_analysis["Tarih"])
        today_ts = pd.Timestamp(date.today())

        week_ago = today_ts - pd.Timedelta(days=7)
        two_weeks_ago = today_ts - pd.Timedelta(days=14)

        this_w = df_logs_analysis[
            (df_logs_analysis["Tarih"] > week_ago)
            & (df_logs_analysis["Tarih"] <= today_ts)
        ]["Toplam_Kg"].sum()
        last_w = df_logs_analysis[
            (df_logs_analysis["Tarih"] > two_weeks_ago)
            & (df_logs_analysis["Tarih"] <= week_ago)
        ]["Toplam_Kg"].sum()

        col_r1, col_r2 = st.columns(2)
        with col_r1:
            st.metric("Son 7 Günde Toplam Süt", f"{this_w:.1f} kg")
        with col_r2:
            st.metric("Önceki 7 Günde Toplam Süt", f"{last_w:.1f} kg")

        fark = this_w - last_w
        if last_w > 0:
            if fark > 0:
                st.success(
                    f"🟢 Harika! Bu hafta geçen haftaya göre toplam **{fark:.1f} kg daha fazla** süt elde edildi."
                )
            elif fark < 0:
                st.warning(
                    f"⚠️ Dikkat: Bu hafta geçen haftaya göre toplam **{abs(fark):.1f} kg daha az** süt elde edildi."
                )
            else:
                st.info(
                    "ℹ️ Bu hafta ile geçen haftanın süt verimi aynı seviyede."
                )
    else:
        st.info("Süt analizi için önce süt kaydı girmelisin.")
