import pandas as pd
import streamlit as st
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))) # adding parent dirs to python path
from IsYatirim import IsYatirimScraper
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))) # adding parent dirs to python path
from use_case_hisse_analiz_python import HisseAnaliz
from KAPScraper import KAPHelper, KAP
import plotly.graph_objects as go
from datetime import date, timedelta

@st.cache_data(show_spinner=False)
def get_price_df(ticker:str, start_date:str, end_date:str):

    price_df = IsYatirimScraper().get_is_yatirim_price_data(ticker=ticker, start_date=start_date, end_date=end_date)
    return price_df[["TARIH", "GUN ICI EN DUSUK", "GUN ICI EN YUKSEK", "HISSE KODU", "KAPANIS FIYATI (TL)", "DOLAR KURU (TL)", "DOLAR BAZLI FIYAT (USD)"]]

@st.cache_data(show_spinner=False)
def get_hisse_analiz(firma_kodu:str, price_df:pd.DataFrame):
    ha = HisseAnaliz(firma_kodu=firma_kodu)

    return {
        "son_guncelleme":ha.last_update(),
        "firma_bilgileri":ha.get_company_info(),
        "firma_bilanco":ha.get_balance_sheet_summary(),
        "firma_gelir_ceyreklik":ha.get_sum(time_type="quarterly"),
        "firma_gelir_kumulatif":ha.get_sum(time_type="cumulative"),
        "firma_kaynaklar":ha.get_sources(),
        "temel_oranlar":ha.fundamental_ratios(),
        "teknik_oranlar":ha.indicators(price_df=price_df)
    }

@st.cache_data
def get_firmalar():
    kap = KAPHelper()
    return kap.firma_listesi()

@st.cache_data(show_spinner=False)
def get_bist50():
    kap = KAPHelper()
    return kap.endeksler()["BIST 50"]

def foo(num:str):
    """
    Format specifier: 3500000000.00 -> 3.500.000.000.00
    """
    mod = num.index(".") % 3 
    if mod == 0:
        n = f'{num[0:3]}'
    elif mod == 1:
        n = f'{num[0:2]}'
    elif mod == 2:
        n = f'{num[0:1]}'
    for i in range(len(n), num.index("."), 3):
        n += f".{num[i:i+3]}"
    return n + ",00"

def firma_bilgiler(hisse_analiz, ticker):

    st.text(f'{get_firmalar()[ticker][0]} ({hisse_analiz["firma_bilgileri"]["company_name"]})')
    fiyat, son_guncelleme, _ = st.columns(3)
    with fiyat:
        st.metric(label="Son Fiyat", value=f'{hisse_analiz["firma_bilgileri"]["current_price"]} ₺', delta=f'{hisse_analiz["firma_bilgileri"]["daily_price_change"]} %')
    with son_guncelleme:
        st.text(f'Son Güncelleme:\n{hisse_analiz["son_guncelleme"]}')

    st.text("Şirket Detayları")
    st.text(f'Sektörler:\t\t\t{hisse_analiz["firma_bilgileri"]["sector_industry"]}')
    st.text(f'Piyasa Değeri:\t\t\t{round(hisse_analiz["firma_bilgileri"]["market_value"]/1_000_000_000, 2)} Milyar ₺')
    st.text(f'İşletme Sermayesi:\t\t{round(hisse_analiz["firma_bilgileri"]["working_capital"]/1_000_000_000, 2)} Milyar ₺')
    st.text(f'Toplam Hisse Adedi:\t\t{foo(num=hisse_analiz["firma_bilgileri"]["number_of_shares"])}')
    st.text(f'Dolaşımdaki Hisse Adedi:\t{hisse_analiz["firma_bilgileri"]["outstanding_shares"]}')
    st.text(f'Fiili Dolaşım Oranı:\t\t{hisse_analiz["firma_bilgileri"]["outstanding_shares%"]} %')

def price_graph(price_df, ticker):
    """
    Creates dual-y-axis line chart where the first y axis is Fiyat (TL) and the second is Fiyat (USD)
    """
    # Create dual-axis line chart
    fig = go.Figure()
    # Add the first line (Fiyat (TL)) Y1 to the left Y-axis
    fig.add_trace(go.Scatter(x=price_df["TARIH"], y=price_df["KAPANIS FIYATI (TL)"], mode='lines', name='FİYAT (TL)', line_color="#0080FF"))
    # Add the second line (Fiyat (USD)) Y2 to the right Y-axis
    fig.add_trace(go.Scatter(x=price_df["TARIH"], y=price_df["DOLAR BAZLI FIYAT (USD)"], mode='lines', name='FİYAT (USD)', yaxis='y2', line_color="#cc6600"))
    # Update layout to create the dual-axis effect
    fig.update_layout(
        title=f'{ticker} Fiyat Grafiği',
        xaxis_title='Tarih',
        yaxis_title='Fiyat (TL)',
        yaxis2=dict(
            title='Fiyat (USD)',
            overlaying='y',
            side='right',
        ),
        xaxis=dict(
            rangeslider=dict(visible=False),
            type='date',
        ),
    )
    fig.update_xaxes(
        ticks="outside",
        ticklabelmode="period",
        ticklen=10,
        rangeselector=dict(
            buttons=list([
                dict(count=1, label="1 AY", step="month", stepmode="backward"),
                dict(count=6, label="6 AY", step="month", stepmode="backward"),
                dict(count=1, label="YBK", step="year", stepmode="todate"),
                dict(count=1, label="1 YIL", step="year", stepmode="backward"),
                dict(step="all", label="HEPSİ")
            ]),
        ),
    )
    st.plotly_chart(fig, use_container_width=True)


def df_design(df:pd.DataFrame, tablo_tipi) -> pd.DataFrame:
    """
    Son ceyrek ve bir onceki senenin ayni ceyregi icin kumulatif kiyas yapan df'nin dizayni
    """
    # Son ceyrek ve bir onceki senenin ayni ceyregi -> 09/2023 | 09/2022
    df = df.iloc[:, :3].copy()
    # Kolonlarin data tipi her ihtimale karsi int64'e cevrilir ve 1.000'e bolunur.

    for col in df.columns[1:]:
        df[col] = df[col].astype("float64")
        df[col] = df[col].divide(1000.0) # / 1000 TL

    # Degisim orani bulunur
    df.loc[:, "%"] = float
    df.loc[:, "%"] = round(100 * (df.iloc[:,1] / df.iloc[:,2] - 1).astype("float64"), 2)
    # Aciklama kolonunun ismi dinamik olarak degistirilir
    df.rename(columns={"ACIKLAMA": f"Özet {tablo_tipi} Tablosu (1.000 TRY)"}, inplace=True)
    # % kolonuna ait degerlerin yanina % isareti konulur
    df.loc[:, df.columns[-1]] = df.loc[:, df.columns[-1]].astype(str)
    df.loc[:, df.columns[-1]] = df.loc[:, df.columns[-1]].apply(lambda x: f"{x} %")

    return df

def df_design_style(df, tablo_tipi) -> pd.DataFrame.style :
    """
    df_design() fonksiyonundan gelen dataframe'e ait stilleri duzenler.
    """
    # Biraz revizyon
    df = df.style\
        .format(precision=0, thousands=".", decimal=",")
    
    # Gelir tablosunun degisim orani kolonu (%) degerine gore renklendirilir 
    if tablo_tipi=="Gelir":
        df = df.map(
            lambda x: 'color: red' if float(x.split()[0]) < 0 else 'color: green', subset=[df.columns[-1]]
            )
    # Bilancoda bulunan borclar bir onceki doneme/seneye gore arttiysa bu olumsuz bir durumdur; yani % pozitif ise bu kirmizi renk ile gosterilmesi gerekirken
    # eger ki borclar azaldiysa bu durum olumludur, yani % negatif ise bu yesil renk ile gosterilmesi gerekir
    elif tablo_tipi=="Bilanço":
        df = df\
            .map(lambda x: 'color: red' if float(x.split()[0]) < 0 else 'color: green', subset=pd.IndexSlice[:3, df.columns[-1]])\
            .map(lambda x: 'color: green' if float(x.split()[0]) < 0 else 'color: red', subset=pd.IndexSlice[3:, df.columns[-1]])
    else:
        st.error("Hatali tablo tipi")

    return df

def bilanco_gr(gr_df, ceyrek=5):

    """
    Son 5 ceyrege (default) ait Donen Varliklar + Duran Varliklar = Toplam Varliklar
    esitligini saglayacak sekilde Stacked-Histogram Bar grafigini getirir.
    gr_df -> grafik bilgilerini iceren dataframe
    """
    gr_df = gr_df.iloc[:2, 0:ceyrek+1].reset_index(drop=True) # 0:6 -> son 5 ceyrek
    gr_df.loc[2, "ACIKLAMA"] = "Toplam Varlıklar"
    gr_df.iloc[2, 1:] = gr_df.iloc[0, 1:] + gr_df.iloc[1, 1:] # Duran varliklar + Donen varliklar
    
    # Veriler DataFrame'den alindigi icin guncel degerler solda kaliyordu, [::-1] ile tersini alarak guncel degerleri saga dogru olacak sekilde aldim
    ceyrekler = gr_df.columns[1:][::-1]
    donen_varl = gr_df.iloc[0,1:][::-1]
    duran_varl = gr_df.iloc[1,1:][::-1]
    traces = [
        go.Bar(x=ceyrekler, y=duran_varl, name="Duran Varlıklar"),
        go.Bar(x=ceyrekler, y=donen_varl, name="Dönen Varlıklar"),
    ]

    layout = go.Layout(
        barmode="stack",
        title="VARLIKLAR",
        xaxis=dict(title="Çeyrekler"),
        yaxis=dict(title="Toplam Varlıklar (₺)"),
    )

    fig = go.Figure(data=traces, layout=layout)
    return fig

def kaynak_gr(df, ceyrek=5):

    """
    Son 5 ceyrege (default) ait Donen Varliklar + Duran Varliklar = Toplam Varliklar
    esitligini saglayacak sekilde Stacked-Histogram Bar grafigini getirir.
    gr_df -> grafik bilgilerini iceren dataframe
    """
    df = df.iloc[:, 0:ceyrek+1].reset_index(drop=True) # 0:6 -> son 5 ceyrek
    df.loc[3, "ACIKLAMA"] = "Toplam"
    df.iloc[3, 1:] = df.iloc[:,1:].sum()
    percentages = df.iloc[:, 1:].div(df.iloc[3, 1:]).astype("float64").round(2) * 100
    
    ceyrekler = df.columns[1:][::-1]
    data = {
        "Kısa Vadeli Yükümlülükler": df.iloc[0,1:][::-1],
        "Uzun Vadeli Yükümlülükler": df.iloc[1,1:][::-1],
        "Özkaynaklar": df.iloc[2,1:][::-1]
    }

    percentages = {
        "Kısa Vadeli Yükümlülükler": percentages.iloc[0][::-1],
        "Uzun Vadeli Yükümlülükler": percentages.iloc[1][::-1],
        "Özkaynaklar": percentages.iloc[2][::-1]    
    }
    
    traces = [
        go.Bar(
            x=ceyrekler, 
            y=value, 
            name=key, 
            text=percentages[key].apply(lambda x: f"{x:.0f}%"), 
            textposition="inside", 
            insidetextanchor="middle"
            ) \
                for key,value in data.items()
    ]

    layout = go.Layout(
        barmode="stack",
        title="KAYNAKLAR",
        xaxis=dict(title="Çeyrekler"),
        yaxis=dict(title="Toplam Kaynaklar (₺)"),
    )

    fig = go.Figure(data=traces, layout=layout)
    return fig


def gelir_gr(df, ceyrek=5):

    df = df.iloc[:, :ceyrek+1]
    ceyrekler = df.columns[1:][::-1]
    data = {
        "Satışlar": df.iloc[0, 1:][::-1],
        "Net Kar": df.iloc[3, 1:][::-1],
        "FAVÖK": df.iloc[4, 1:][::-1]
    }
    traces = [
        go.Bar(x=ceyrekler, y=value, name=key) for key,value in data.items()
    ]
    layout = go.Layout(
        # barmode="overlay",
        title="GELİRLER",
        xaxis=dict(title="Çeyrekler"),
        yaxis=dict(title="Mlyr TL")
    )

    fig = go.Figure(data=traces, layout=layout)
    return fig


def rasyolar(hisse_analiz):
    """
    Ilgili firma ile ilgili temel oranlarini ceker
    """
    # teknik gostergeler
    sma = ", ".join([str(round(sma, 2)) + " ₺" for sma in hisse_analiz['teknik_oranlar']['simple_moving_average']])
    ema = ", ".join([str(round(ema, 2)) + " ₺" for ema in hisse_analiz['teknik_oranlar']['exponential_moving_average']])
    rsi = round(hisse_analiz['teknik_oranlar']["relative_strength_index"], 2)
    momentum = hisse_analiz["teknik_oranlar"]["momentum"]
    min_max = hisse_analiz["teknik_oranlar"]["min_max"]

    # temel gostergeler
    fk = hisse_analiz['temel_oranlar']["fk"]                    # fiyat/kazanc
    pd_dd = hisse_analiz["temel_oranlar"]["pd/dd"]              # piyasa degeri / defter degeri
    eps = hisse_analiz["temel_oranlar"]["eps"].iloc[0, 1:5].sum()       # hisse basi kazanc
    roe = hisse_analiz["temel_oranlar"]["roe"].iloc[-1, 1]                  # ozsermaye karliligi
    roa = hisse_analiz["temel_oranlar"]["roa"].iloc[-1, 1]                  # aktif karlilik
    dte = hisse_analiz["temel_oranlar"]["debt_to_equity"].iloc[-1, 1]       # borc/ozsermaye orani
    
    st.text("Teknik Oranlar")
    st.divider()
    st.text(f"Basit Hareketli Ortalama (10, 50, 200):\t\t {sma}")
    st.text(f"Üstel Hareketli Ortalama (10, 50, 200):\t\t {ema}")
    st.text(f"1 Yıllık Fiyat Aralığı (Min.-Max.):\t\t {min_max[0]} ₺ - {min_max[1]} ₺")
    st.text(f"Relatif Güç Endeksi (RSI) (14):\t\t\t {rsi}")
    st.text(f"Momentum (10):\t\t\t\t\t {momentum}")
    st.divider()

    st.text("Temel Oranlar")
    st.divider()
    st.text(f"Fiyat/Kazanç:\t\t\t\t\t {fk}")
    st.text(f"Piyasa Değeri / Defter Değeri:\t\t\t {pd_dd}")
    st.text(f"Hisse başına kazanç:\t\t\t\t {round(eps, 2)} ₺")
    st.text(f"Özsermaye karlılığı:\t\t\t\t {round(roe, 2)} %")
    st.text(f"Aktif karlılık:\t\t\t\t\t {round(roa, 2)} %")
    st.text(f"Borç/Özsermaye:\t\t\t\t\t {round(dte, 2)} %")

def get_kap_bildirimler(ticker):
    bildirimler = KAP(firma_kodu=ticker).bildirimler()
    s = ""
    for bildirim in bildirimler[:28]:
        s += f'{bildirim["yayin_tarihi"]} - <a href={bildirim["disclosureLink"]}>{bildirim["disclosureLink"]}</a> - {bildirim["baslik"]}\n'
    # CSS
    s = f"""<div style='font-family: "Source Code Pro", monospace; font-size: 14px; white-space: pre-line;'>{s}</div>"""
    return s

st.set_page_config(layout="wide")

# is_yatirim = IsYatirimScraper()
def get_input_hisse_analiz():
    liste_disi = ["AKBNK", "KRDMD", "GARAN", "HALKB", "ISCTR", "YKBNK"]
    firma_listesi = [i for i in get_bist50() if i not in liste_disi]
    x, _ = st.columns((1,2))
    with x:
        ticker = st.selectbox(label="Hisse", options=firma_listesi, label_visibility="hidden", placeholder="Görüntülemek istediğiniz hisseyi seçiniz...", index=None)
    start_date = (date.today() - timedelta(weeks=2*52)).strftime("%d-%m-%Y")
    end_date = date.today().strftime("%d-%m-%Y")
    return ticker, start_date, end_date

def callback():
    st.session_state.button_clicked = True

def main():
    # if "button_clicked" not in st.session_state:
    #     st.session_state.button_clicked = False


    ticker, start_date, end_date = get_input_hisse_analiz()
    if st.button("Hesapla 📊"): #", on_click=callback) or st.session_state.button_clicked:

        if not ticker:
            st.warning("Lütfen hisse senedi seçiniz.")
            st.stop()
        
        with st.spinner("Veriler indiriliyor..."):
            price_df = get_price_df(ticker=ticker, start_date=start_date, end_date=end_date)
            hisse_analiz = get_hisse_analiz(firma_kodu=ticker, price_df=price_df)
        _, firma_bilgileri, grafik, _ = st.columns((.5,4,5,.5))
        
        with firma_bilgileri:
            firma_bilgiler(hisse_analiz=hisse_analiz, ticker=ticker)

        with grafik:
            price_graph(price_df=price_df, ticker=ticker)

        _, bilanco, gelir_tablosu, _ = st.columns((.5,4.5,4.5,.5))
        with bilanco:
            bilanco_df = df_design(df=hisse_analiz["firma_bilanco"], tablo_tipi="Bilanço")
            bilanco_df = df_design_style(df=bilanco_df, tablo_tipi="Bilanço")
            st.dataframe(data=bilanco_df, hide_index=True, use_container_width=True) 

        with gelir_tablosu:
            gelir_tablosu_df = df_design(df=hisse_analiz["firma_gelir_kumulatif"], tablo_tipi="Gelir")
            gelir_tablosu_df = df_design_style(df=gelir_tablosu_df, tablo_tipi="Gelir")
            st.dataframe(gelir_tablosu_df, use_container_width=True, hide_index=True)

        _, bilanco_gr_col, kaynaklar_gr_col, gelirler_gr_col, _ = st.columns((.5,3,3,3,.5))

        # bilanco grafik
        with bilanco_gr_col:
            fig = bilanco_gr(gr_df=hisse_analiz["firma_bilanco"])
            st.plotly_chart(figure_or_data=fig, use_container_width=True)

        # kaynaklar grafik
        with kaynaklar_gr_col:
            fig = kaynak_gr(df=hisse_analiz["firma_kaynaklar"])
            st.plotly_chart(figure_or_data=fig, use_container_width=True)

        # gelir ve karlilik grafik
        with gelirler_gr_col:
            fig = gelir_gr(df=hisse_analiz["firma_gelir_ceyreklik"])
            st.plotly_chart(figure_or_data=fig)

        _, rasyolar_col, son_kap_haberleri, _ = st.columns((.5,5,5,.5))
        
        # oranlar
        with rasyolar_col:
            rasyolar(hisse_analiz=hisse_analiz)
            
        # kap bildirimleri
        with son_kap_haberleri:
            st.text("Son KAP Haberleri") # === kap sayfalarina href eklenecek
            st.divider()
            st.markdown(get_kap_bildirimler(ticker=ticker), unsafe_allow_html=True)


if __name__ == "__main__":
    main()