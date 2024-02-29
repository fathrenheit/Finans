import sys, os
from ReturnCalculator import ReturnCalculator
from datetime import date, timedelta
import streamlit as st
import plotly.graph_objects as go
import pandas as pd

st.set_page_config(layout="wide", page_title="Financial Dashboard", page_icon=":money_with_wings:")
pd.set_option('display.colheader_justify', 'center')


@st.cache_data(show_spinner=False)
def get_data(hisse_kodu, tarih_baslangic, tarih_son, hesaplama_tipi, div_reinvest, tutar):
    try:
        rc = ReturnCalculator(ticker=hisse_kodu, period1=tarih_baslangic, period2=tarih_son)
        rf = rc.df_maker(hesaplama_tipi=hesaplama_tipi, div_reinvest=div_reinvest, tutar=tutar)
        rp = rc.report(hesaplama_tipi=hesaplama_tipi, div_reinvest=div_reinvest, tutar=tutar)
        return rf, rp
    except RuntimeError as e:
        st.error(e)
        st.stop()

@st.cache_data(show_spinner=False)
def get_bist50():
    from KAPScraper import KAPHelper
    return KAPHelper.endeksler()["BIST 50"]


def price_graph(price_df, ticker, col1, col2, graph_name, hesaplama_tipi, div_re):
    """
    Creates dual-y-axis line chart where the first y axis is Fiyat (TL) and the second is Fiyat (USD)
    """
    if hesaplama_tipi == "duzenli":
        hesaplama_tipi = "Her ay düzenli yatırım"
    else:
        hesaplama_tipi = "Tek seferlik yatırım"
    
    if div_re:
        tem = "Temettülerle hisse alımı yapıldı"
        alternatif = "Temettülerin portföyde saklandı"

    else:
        tem = "Temettülerin portföyde saklandı"
        alternatif = "Temettülerle hisse alımı yapıldı"

    # Create dual-axis line chart
    fig = go.Figure()
    # Add the first line (Fiyat (TL)) Y1 to the left Y-axis
    fig.add_trace(go.Scatter(x=price_df["TARIH"], y=price_df[col1], mode='lines', name=f'SEÇİLEN:           {tem}ğı durumda toplam portföy ({graph_name})', line=dict(color="royalblue", width=3))) # #0080FF
    # Add the second line (Fiyat (USD)) Y2 to the right Y-axis
    fig.add_trace(go.Scatter(x=price_df["TARIH"], y=price_df[col2], mode='lines', name=f'ALTERNATİF:    {alternatif}ğı durumda toplam portföy ({graph_name})  ', line=dict(color="salmon", width=1.5, dash="dash")))#cc6600"
    # Update layout to create the dual-axis effect
    fig.update_layout(
        title=f'{ticker} Hissesi {hesaplama_tipi.title()} Sonuç Grafiği',
        xaxis_title='Tarih',
        yaxis_title=f'Portföy Değeri ({graph_name})',
        legend=dict(
            orientation="v",
            xanchor="center",
            # yanchor="auto",
            x=.75,
            y=1.27,
        )

    )
    fig.update_xaxes(
        ticks="outside",
        ticklabelmode="period",
        ticklen=10,
    )
    st.plotly_chart(fig, use_container_width=True)

def get_input():
    firma_listesi = get_bist50()
    ticker = st.selectbox(label="hisse kodu", options=firma_listesi, label_visibility="hidden", placeholder="Getiri hesabı yapmak istediğiniz hisseyi seçiniz?")
    st_date, end_date = st.columns(2)
    with st_date:

        mins_st = date(2015, 1, 1)
        start_date = st.date_input("Başlangıç tarihi seçiniz:", value=date.today() - timedelta(weeks=52), max_value= date.today() - timedelta(weeks=1), min_value=mins_st, format="DD/MM/YYYY")
        
    with end_date:
        end_date = st.date_input("Bitiş tarihi seçiniz:", max_value=date.today(), format="DD/MM/YYYY")

    if end_date < start_date :
        st.error(f"Hatalı tarih aralığı seçtiniz. Başlangıç tarihi ({start_date.strftime('%d-%m-%Y')}), bitiş tarihinden ({end_date.strftime('%d-%m-%Y')}) daha büyük olamaz.")

    yatirim_tipi, tem_geri_yatir = st.columns(2)
    with yatirim_tipi:
        yt = st.radio("Yatırım tipini seçiniz:", options=["Her ay düzenli yatırım", "Tek seferlik yatırım"], help="Düzenli yatırım, her ay aynı tutarda para ile yapılan düzenli yatırımdır. Tek seferlik yatırım ise tek seferde belli bir tutarda para ile yapılan yatırımdır.")
        if yt == "Her ay düzenli yatırım":
            hesaplama_tipi = "duzenli"
        elif yt == "Tek seferlik yatırım":
            hesaplama_tipi = "tek"

    with tem_geri_yatir:
        tem = st.radio("Temetttüler geri yatırılsın mı?", options=["Evet", "Hayır"], help="Temetttülerin geri yatırılması, temetttülerden gelen para ile yatırım yapılan hisseden yeniden pay almayı ifade eder.")
        if tem == "Evet":
            div_re = True
        else:
            div_re = False

    tutar = st.number_input("Yatırım tutarını giriniz:", min_value=0)
    return ticker, start_date, end_date, hesaplama_tipi, div_re, tutar


def calc(df0:pd.DataFrame, df1:pd.DataFrame):
    """
    Returns merged df of portfolio calculation. 
    df0 is df with no dividend reinvestment
    df1 is df with dividend reinvestment
    """
    df1 = df1.iloc[:, [0, -2, -1]].copy()
    df1.rename(columns={"PORTFOY-TL": "PORTFOY-TL-DIV-REINVEST", "PORTFOY-USD":"PORTFOY-USD-DIV-REINVEST"}, inplace=True)        
    df0 = df0.iloc[:, [0, -2, -1]]
    return df0.merge(df1, on="TARIH")

def calculate(button, ticker, start_date, end_date, hesaplama_tipi, div_re, tutar):    


    if button:
        # Users choice
        df, rp = get_data(
            hisse_kodu=ticker, 
            tarih_baslangic=start_date.strftime("%d-%m-%Y"), 
            tarih_son=end_date.strftime("%d-%m-%Y"),
            hesaplama_tipi=hesaplama_tipi,
            div_reinvest=div_re,
            tutar=tutar 
            )

        # Alternative scenario
        df_, rp_ = get_data(
            hisse_kodu=ticker, 
            tarih_baslangic=start_date.strftime("%d-%m-%Y"), 
            tarih_son=end_date.strftime("%d-%m-%Y"),
            hesaplama_tipi=hesaplama_tipi,
            div_reinvest=not div_re,
            tutar=tutar 
            )
        # Layout setting
        a, b = st.columns(2)
        # Outputting computation parameters
        with a:

            # Setting computation parameters
            secilen_hisse = ticker
            tarih1, tarih2 = start_date.strftime("%d/%m/%Y"), end_date.strftime("%d/%m/%Y")
            tarih1_dolar = df.loc[0, "USD/TRY"]
            tarih1_hisse_fiyati = df.loc[0, "HISSE KAPANIS FIYATI (TL)"]
            tarih1_hisse_fiyati_usd = df.loc[0, "HISSE KAPANIS FIYATI (USD)"]
            ht = "Tek seferlik yatırım" if hesaplama_tipi == "tek" else "Her ay düzenli yatırım"
            tem_geri_alim = "Evet" if div_re else "Hayır"
            common_cols = ["Parametre", "Değer"]

            st.text("Hesaplama parametreleri:")
            df_dict = {
                "Seçilen hisse": secilen_hisse, 
                "Başlangıç tarihi": tarih1, 
                "Bitiş tarihi": tarih2,
                "Yatırım tutarı (₺)": float(tutar),
                "Başlangıç tarihinde dolar kuru ($/₺)": round(tarih1_dolar, 2),
                "Başlangıç tarihinde hisse fiyatı (₺)": round(tarih1_hisse_fiyati, 2),
                "Başlangıç tarihinde hisse fiyatı ($/₺)": round(tarih1_hisse_fiyati_usd, 2),
                "Yatırım tipi": ht,
                "Temettülerle ile hisse alınacak mı?": tem_geri_alim
                }

            df_p = pd.DataFrame(data=df_dict.items(), columns=common_cols, index=[_ for _ in range(len(df_dict.keys()))])
            for col in df_p.columns:
                df_p[col] = df_p[col].astype(str)
            st.dataframe(df_p, use_container_width=True, hide_index=True)

        # Outputting result of the computation in dataframe format
        with b:
            
            # Results of the computation
            lot_tem = rp["tem_alinan_lot"] if div_re else 0
            lot_toplam = rp["toplam_lot"]
            tem_geliri_tl = rp["tem_geliri"]
            tem_geliri_usd = rp["tem_geliri_usd"]
            portfoy_tl = rp["guncel_portfoy"]
            portfoy_usd = rp["guncel_portfoy_usd"]
            yatirim_tl = rp["yatirim_tutari"]
            yatirim_usd = rp["yatirim_tutari_usd"]

            # Making a dictionary out of the result
            data_portfoy = {
                "Parametre": ["Toplam yatırım tutarı", "Toplam temettü geliri", "Güncel portföy değeri", "Toplam kazanç", "Toplam kazanç (%)"],
                "Türk Lirası (₺)": [yatirim_tl, tem_geliri_tl, portfoy_tl, portfoy_tl - yatirim_tl, round(100 * portfoy_tl / yatirim_tl - 100, 2)],
                "Amerikan Doları ($)": [yatirim_usd,  tem_geliri_usd, portfoy_usd, portfoy_usd - yatirim_usd, round(100 * portfoy_usd / yatirim_usd - 100, 2)]
            }
            # Making a df using the dict
            df_portfoy = pd.DataFrame(data=data_portfoy, index=[_ for _ in range(5)])
            # Some styling
            df_portfoy = df_portfoy.style\
                .format(precision=2, thousands=".", decimal=",")
            
            # Dictionary of shares computed
            data_lot = {
                "Temettülerle alınan lotlar": lot_tem,
                "Anapara ile alınan lotlar": lot_toplam - lot_tem,
                "Toplam lot": lot_toplam
            }
            # Making a df using the dict
            df_lot = pd.DataFrame(data=data_lot.items(), columns=common_cols, index=[_ for _ in range(len(data_lot.keys()))])
            df_lot = df_lot.style.\
                format(precision=2, thousands="", decimal=".")
            
            st.text(f"Hesaplama sonucu:")
            st.dataframe(df_lot, use_container_width=True, hide_index=True)
            st.dataframe(df_portfoy, use_container_width=True, hide_index=True)
        
        st.divider()

        # Setting up graphs with the chosen one and the alternative one
        if div_re:
            # If user chooses to dividend-reinvestment, then df0 is df_ and df1 is df
            df0 = df_
            df1 = df
            secilen = "div_re"
        else:
            # If user chooses not to dividend-reinvestment, then df0 is df and df1 is df_
            df0 = df
            df1 = df_
            secilen = "no_div_re"

        df_merged = calc(df0=df0, df1=df1) # df0: Temettu geri yatirilmiyor, df1: Temettu geri yatiriliyor
        # Graph columns; Turkish lira and US Dollars
        tl_graph, usd_graph = st.columns(2)
        with tl_graph:
            if secilen == "div_re":
                price_graph(df_merged, ticker=ticker, col1="PORTFOY-TL-DIV-REINVEST", col2="PORTFOY-TL", graph_name="TL", hesaplama_tipi=hesaplama_tipi, div_re=div_re)
            else:
                price_graph(df_merged, ticker=ticker, col1="PORTFOY-TL", col2="PORTFOY-TL-DIV-REINVEST", graph_name="TL", hesaplama_tipi=hesaplama_tipi, div_re=div_re)
        with usd_graph:
            if secilen == "div_re":
                price_graph(df_merged, ticker=ticker, col1="PORTFOY-USD-DIV-REINVEST", col2="PORTFOY-USD", graph_name="USD", hesaplama_tipi=hesaplama_tipi, div_re=div_re)
            else:
                price_graph(df_merged, ticker=ticker, col1="PORTFOY-USD", col2="PORTFOY-USD-DIV-REINVEST", graph_name="USD", hesaplama_tipi=hesaplama_tipi, div_re=div_re)


def main():
    ticker, start_date, end_date, hesaplama_tipi, div_re, tutar = get_input()
    calculate_button = st.button("Hesapla 📈")
    if calculate_button:
        calculate(button= calculate_button, ticker=ticker + ".IS", start_date=start_date, end_date=end_date, hesaplama_tipi=hesaplama_tipi, div_re=div_re, tutar=tutar)
if __name__ == "__main__":
    main()