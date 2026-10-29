from datetime import date
import pandas as pd
import sqlite3
import streamlit as st

st.set_page_config(
    page_title="Umut Besicilik - Çiftlik Yönetim Sistemi",
    page_icon="🐄",
    layout="wide",
)

# -------------------------------------------------------------
# 1. VERİTABANI BAĞLANTISI VE TABLOLARIN OLUŞTURULMASi
# -------------------------------------------------------------
DB_NAME = "umut_besicilik.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # İnekler Tablosu
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS cows (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            inek_id TEXT UNIQUE,
            dogum_tarihi TEXT,
            t_kuru_donem INTEGER
        )
    """
    )
    # Süt Kayıtları Tablosu
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS milking_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tarih TEXT,
            toplam_kg REAL
        )
    """
    )
    # Masraf Kayıtları Tablosu
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS expense_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tarih TEXT,
            gider_turu TEXT,
            miktar TEXT,
            toplam_tutar_tl REAL
        )
    """
    )
    # Ayarlar Tablosu (Süt Fiyatı İçin)
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """
    )
    conn.commit()
    conn.close()


init_db()


# Başlangıç verileri yoksa inekleri ekleyelim
def load_default_cows():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql("SELECT * FROM cows", conn)
    if df.empty:
        default_cows = [
            ("İnek 1 (Sarıkız)", "2020-03-15", 0),
            ("İnek 2 (Benekli)", "2019-05-10", 0),
            ("İnek 3 (Yıldız)", "2021-02-20", 0),
            ("İnek 4 (Kınalı)", "2018-08-12", 0),
            ("İnek 5 (Doru)", "2022-01-05", 0),
            ("İnek 6 (Papatya)", "2020-11-25", 0),
            ("İnek 7 (Zeytin)", "2021-06-18", 0),
        ]
        c = conn.cursor()
        c.executemany(
            "INSERT OR IGNORE INTO cows (inek_id, dogum_tarihi, t_kuru_donem)"
            " VALUES (?, ?, ?)",
            default_cows,
        )
        conn.commit()
    conn.close()


load_default_cows()


# Süt Fiyatını Al / Güncelle
def get_milk_price():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key = 'milk_price'")
    row = c.fetchone()
    conn.close()
    if row:
        return float(row[0])
    else:
        # Varsayılan fiyat ekle
        set_milk_price(15.0)
        return 15.0


def set_milk_price(price):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        "INSERT OR REPLACE INTO settings (key, value) VALUES ('milk_price',"
        " ?)",
        (str(price),),
    )
    conn.commit()
    conn.close()


# Yaş Hesaplama Fonksiyonu
def calculate_age(born_str):
    try:
        born = date.fromisoformat(born_str)
        today = date.today()
        months = (today.year - born.year) * 12 + today.month - born.month
        years = months // 12
        rem_months = months % 12
        return f"{years} Yaşında ({rem_months} aylık)"
    except:
        return "Bilinmiyor"


st.title("🐄 Umut Besicilik - Çiftlik Yönetim Paneli")
st.markdown(
    "Babanın telefonundan tek tıkla süt, masraf ve kâr-zarar takibi (Veriler"
    " veritabanında güvenle saklanır)."
)

# -------------------------------------------------------------
# ANA SAYFA / ÜST BÖLÜM: AYLIK FİNANSAL DURUM VE KÂR/ZARAR ÖZETİ
# -------------------------------------------------------------
st.markdown("### 💵 Aylık Kâr / Zarar ve Finansal Durum")

current_price = get_milk_price()

col_f1, col_f2 = st.columns([2, 3])
with col_f1:
    price_input = st.text_input(
        "Güncel Süt Kg Fiyatı (TL)",
        value=str(current_price),
        placeholder="Örn: 15.5",
    )
with col_f2:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Fiyatı Güncelle"):
        try:
            new_p = float(price_input.replace(",", "."))
            set_milk_price(new_p)
            st.success(f"✅ Süt fiyatı {new_p} TL olarak güncellendi!")
            st.rerun()
        except ValueError:
            st.error("⚠️ Geçerli bir fiyat girin.")

current_price = get_milk_price()
today = date.today()

# Veritabanından verileri çek
conn = sqlite3.connect(DB_NAME)
df_milk = pd.read_sql("SELECT * FROM milking_logs", conn)
df_exp = pd.read_sql("SELECT * FROM expense_logs", conn)
df_cows = pd.read_sql("SELECT * FROM cows", conn)
conn.close()

current_month_milk_income = 0.0
current_month_expense = 0.0

if not df_milk.empty:
    df_milk["tarih"] = pd.to_datetime(df_milk["tarih"])
    month_milk = df_milk[
        (df_milk["tarih"].dt.year == today.year)
        & (df_milk["tarih"].dt.month == today.month)
    ]
    total_kg_month = month_milk["toplam_kg"].sum()
    current_month_milk_income = total_kg_month * current_price

if not df_exp.empty:
    df_exp["tarih"] = pd.to_datetime(df_exp["tarih"])
    month_exp = df_exp[
        (df_exp["tarih"].dt.year == today.year)
        & (df_exp["tarih"].dt.month == today.month)
    ]
    current_month_expense = month_exp["toplam_tutar_tl"].sum()

net_profit = current_month_milk_income - current_month_expense

# Gösterge Kartları
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
        f"🟢 **DURUM HARİKA (ARTIDAYIZ):** Bu ay Umut Besicilik masraflar"
        f" çıktıktan sonra **{net_profit:,.2f} TL** net kârda!"
    )
elif net_profit < 0:
    st.error(
        f"🔴 **DURUM EKSİDE (ZARAR / TOPLU ALIM):** Bu ay yapılan masraflar süt"
        f" gelirini geçti. (Eğer toplu saman/yem alındıysa bu normaldir, uzun"
        f" vadeli stok yapılmıştır.) Şu an **{abs(net_profit):,.2f} TL** fark"
        " var."
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
        "Bütün ineklerden sağlanan toplam sütü tek seferde buraya"
        f" yazabilirsiniz[cite: 1, 2]."
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

                conn = sqlite3.connect(DB_NAME)
                c = conn.cursor()
                c.execute(
                    "INSERT INTO milking_logs (tarih, toplam_kg) VALUES (?, ?)",
                    (str(selected_date), total_milk),
                )
                conn.commit()
                conn.close()

                st.success(
                    f"✅ Toplam süt kaydedildi: **{total_milk} kg** (Veritabanına"
                    " yedeklendi!)"
                )
                st.rerun()
            except ValueError:
                st.error(
                    "⚠️ Lütfen kg alanına geçerli bir sayı yazın (Örn: 125.5)."
                )

    st.divider()
    st.subheader("📋 Son Süt Kayıtları ve Yanlış Giriş Silme")
    if not df_milk.empty:
        st.markdown(
            "Kayıtlı son işlemleriniz aşağıdadır. Hatalı olanı listeden seçip"
            " silebilirsiniz:"
        )

        for idx, row in df_milk.tail(5).iterrows():
            st.info(
                f"📅 **{pd.to_datetime(row['tarih']).strftime('%d.%m.%Y')}** |"
                f" Toplam Sağım: **{row['toplam_kg']} kg**"
            )

        with st.form("delete_log_form"):
            row_to_delete = st.selectbox(
                "Silmek İstediğiniz Kaydı Seçin",
                options=df_milk["id"].tolist(),
                format_func=lambda x: f"Tarih: {df_milk.loc[df_milk['id'] == x, 'tarih'].values[0]} | Toplam: {df_milk.loc[df_milk['id'] == x, 'toplam_kg'].values[0]} kg",
            )
            delete_log_btn = st.form_submit_button(
                "Seçilen Hatalı Süt Kaydını Sil"
            )

            if delete_log_btn:
                conn = sqlite3.connect(DB_NAME)
                c = conn.cursor()
                c.execute(
                    "DELETE FROM milking_logs WHERE id = ?", (row_to_delete,)
                )
                conn.commit()
                conn.close()
                st.success("🗑️ Seçilen süt kaydı silindi!")
                st.rerun()
    else:
        st.info("Henüz süt kaydı girilmedi.")

with tab2:
    st.subheader("🛒 Yem, Saman ve Diğer Giderleri Kaydet")
    st.markdown(
        "İster 2 haftalık, ister 1 yıllık olsun; aldığınız ürünü ve ödediğiniz"
        " toplam parayı buraya yazabilirsiniz."
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
                miktar_str = f"{amount_val} {exp_unit}"

                conn = sqlite3.connect(DB_NAME)
                c = conn.cursor()
                c.execute(
                    "INSERT INTO expense_logs (tarih, gider_turu, miktar,"
                    " toplam_tutar_tl) VALUES (?, ?, ?, ?)",
                    (str(exp_date), exp_type, miktar_str, total_price_val),
                )
                conn.commit()
                conn.close()

                st.success(
                    f"✅ {exp_type} masrafı eklendi ve veritabanına kaydedildi!"
                    f" Toplam: {total_price_val:,.2f} TL"
                )
                st.rerun()
            except ValueError:
                st.error(
                    "⚠️ Lütfen miktar ve tutar alanlarına geçerli sayılar"
                    " yazın."
                )

    st.divider()
    st.subheader("📋 Yapılan Masraf Geçmişi ve Silme")
    if not df_exp.empty:
        for idx, row in df_exp.tail(5).iterrows():
            st.warning(
                f"📅 **{pd.to_datetime(row['tarih']).strftime('%d.%m.%Y')}** |"
                f" 🛒 **{row['gider_turu']}** ({row['miktar']}) -> Tutar:"
                f" **{row['toplam_tutar_tl']:,.2f} TL**"
            )

        with st.form("delete_expense_form"):
            exp_to_delete = st.selectbox(
                "Silmek İstediğiniz Masrafı Seçin",
                options=df_exp["id"].tolist(),
                format_func=lambda x: f"Tarih: {df_exp.loc[df_exp['id'] == x, 'tarih'].values[0]} | Tür: {df_exp.loc[df_exp['id'] == x, 'gider_turu'].values[0]} | Tutar: {df_exp.loc[df_exp['id'] == x, 'toplam_tutar_tl'].values[0]} TL",
            )
            delete_exp_btn = st.form_submit_button(
                "Seçilen Hatalı Masrafı Sil"
            )

            if delete_exp_btn:
                conn = sqlite3.connect(DB_NAME)
                c = conn.cursor()
                c.execute("DELETE FROM expense_logs WHERE id = ?", (exp_to_delete,))
                conn.commit()
                conn.close()
                st.success("🗑️ Seçilen masraf kaydı silindi!")
                st.rerun()
    else:
        st.info("Henüz masraf girilmedi.")

with tab3:
    st.subheader("İnek Listesi ve Otomatik Yaş Takibi")
    st.markdown(
        "Buradan ineklerinizi ekleyebilir, yaşlarını otomatik görebilir ya da"
        " silebilirsiniz."
    )

    if not df_cows.empty:
        for idx, row in df_cows.iterrows():
            yas_metni = calculate_age(row["dogum_tarihi"])
            st.info(
                f"🐄 **{row['inek_id']}** | Doğum Tarihi:"
                f" {row['dogum_tarihi']} | Yaşı: **{yas_metni}**"
            )

        st.markdown("---")
        st.subheader("🗑️ İnek Sil")
        with st.form("delete_cow_form"):
            cow_to_delete = st.selectbox(
                "Silmek istediğiniz ineği seçin",
                df_cows["inek_id"].tolist(),
            )
            delete_btn = st.form_submit_button("Seçilen İneği Sil")

            if delete_btn:
                conn = sqlite3.connect(DB_NAME)
                c = conn.cursor()
                c.execute("DELETE FROM cows WHERE inek_id = ?", (cow_to_delete,))
                conn.commit()
                conn.close()
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
            elif new_id in df_cows["inek_id"].values:
                st.warning("Bu isimde bir inek zaten var!")
            else:
                conn = sqlite3.connect(DB_NAME)
                c = conn.cursor()
                c.execute(
                    "INSERT INTO cows (inek_id, dogum_tarihi, t_kuru_donem)"
                    " VALUES (?, ?, 0)",
                    (new_id.strip(), str(new_birth)),
                )
                conn.commit()
                conn.close()
                st.success(f"'{new_id}' sisteme eklendi ve yedeklendi!")
                st.rerun()

with tab4:
    st.subheader("📊 Büyük Kartlı Raporlar ve Çiftlik Analizi")
    st.markdown(
        "Babanın zorlanmadan, tek bakışta görebileceği büyük rakamlı kart"
        f" özetleri[cite: 2]:"
    )

    # 1. Gider Türlerine Göre Büyük Kartlar[cite: 2]
    st.markdown("### 💸 Gider Türlerine Göre Toplam Harcamalar")
    if not df_exp.empty:
        exp_summary = (
            df_exp.groupby("gider_turu")["toplam_tutar_tl"].sum().reset_index()
        )

        cols = st.columns(min(len(exp_summary), 4) if len(exp_summary) > 0 else 1)
        for idx, row in exp_summary.iterrows():
            with cols[idx % len(cols)]:
                st.metric(
                    label=f"📌 {row['gider_turu']}",
                    value=f"{row['toplam_tutar_tl']:,.2f} TL",
                )
    else:
        st.info("Masraf dökümü için önce masraf kaydı girmelisin.")

    st.divider()

    # 2. Genel Süt ve Haftalık Karşılaştırma Analizi
    st.markdown("### 📈 Süt Verimi ve Haftalık Karşılaştırma")
    if not df_milk.empty:
        df_logs_analysis = df_milk.copy()
        df_logs_analysis["tarih"] = pd.to_datetime(df_logs_analysis["tarih"])
        today_ts = pd.Timestamp(date.today())

        week_ago = today_ts - pd.Timedelta(days=7)
        two_weeks_ago = today_ts - pd.Timedelta(days=14)

        this_w = df_logs_analysis[
            (df_logs_analysis["tarih"] > week_ago)
            & (df_logs_analysis["tarih"] <= today_ts)
        ]["toplam_kg"].sum()
        last_w = df_logs_analysis[
            (df_logs_analysis["tarih"] > two_weeks_ago)
            & (df_logs_analysis["tarih"] <= week_ago)
        ]["toplam_kg"].sum()

        col_r1, col_r2 = st.columns(2)
        with col_r1:
            st.metric("Son 7 Günde Toplam Süt", f"{this_w:.1f} kg")
        with col_r2:
            st.metric("Önceki 7 Günde Toplam Süt", f"{last_w:.1f} kg")

        fark = this_w - last_w
        if last_w > 0:
            if fark > 0:
                st.success(
                    f"🟢 Harika! Bu hafta geçen haftaya göre toplam"
                    f" **{fark:.1f} kg daha fazla** süt elde edildi."
                )
            elif fark < 0:
                st.warning(
                    f"⚠️ Dikkat: Bu hafta geçen haftaya göre toplam"
                    f" **{abs(fark):.1f} kg daha az** süt elde edildi."
                )
            else:
                st.info(
                    "ℹ️ Bu hafta ile geçen haftanın süt verimi aynı seviyede."
                )
    else:
        st.info("Süt analizi için önce süt kaydı girmelisin.")
