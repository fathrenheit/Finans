from datetime import datetime
from Yahoo import YahooFinancePriceDataFetcher
import pandas as pd

class ReturnCalculator:

    def __init__(self, ticker, period1, period2) -> None:
        try:
            self.ticker = ticker
            self.period1 = period1
            self.period2 = period2
            self.price_df = YahooFinancePriceDataFetcher().get_prices_from_yahoo(company_code=ticker, period_1=period1, period_2=period2)
            self.currency = YahooFinancePriceDataFetcher().get_prices_from_yahoo(company_code="USDTRY=X", period_1=period1, period_2=period2)
            if len(self.price_df) == 1:
                raise ValueError("Fiyatlar cekilirken hata olustu.")
        except Exception as e:
            raise RuntimeError(f"Error occurred during initialization: {e}")

    def preprocess_fiyatlar(self):

        """
        Tarihsel hisse fiyat bilgilerini, ayni tarihlerdeki Dolar/Tl kapanis kur fiyatlarini ve dagitilan temettu tutarlarini finance.yahoo sitesinden kazir ve gerekli duzenlemeleri yapar.
        """
        # Hisseye ait tarihsel fiyat bilgisi
        f = self.price_df
        f["HISSE KODU"] = self.ticker
        cols_to_keep = ["TARIH", "HISSE KODU", "KAPANIS-yahoo", "TEMETTU (TL)"]
        f = f[cols_to_keep].reset_index(drop=True)
        f.rename(columns={"KAPANIS-yahoo":"HISSE KAPANIS FIYATI (TL)"}, inplace=True)

        # Ayni zaman dilimine ait dolar/tl bilgisi
        c = self.currency
        cols_to_keep = ["TARIH", "KAPANIS-yahoo"]
        c = c[cols_to_keep].reset_index(drop=True)
        c.rename(columns={"KAPANIS-yahoo":"USD/TRY"}, inplace=True)
        
        # Bu iki dataframei birlestirir ve ek duzenlemeler yapar
        df = pd.merge(left=c, right=f, on="TARIH")
        df["TARIH"] = pd.to_datetime(df["TARIH"])
        df["HISSE KAPANIS FIYATI (USD)"] = df["HISSE KAPANIS FIYATI (TL)"] / df["USD/TRY"]
        col_order = ["TARIH", "HISSE KODU", "USD/TRY", "HISSE KAPANIS FIYATI (TL)", "HISSE KAPANIS FIYATI (USD)", "TEMETTU (TL)", "NET TEMETTU (TL)"]

        #  22 Aralik 2021 oncesi stopaj vergisi %15 iken bu tarih sonrasinda %10 seviyesine indirilmistir
        cond = df["TARIH"] > datetime(2021, 12, 22)
        df["NET TEMETTU (TL)"] = df["TEMETTU (TL)"] * .9
        df.loc[~cond, "NET TEMETTU (TL)"] = df["TEMETTU (TL)"] * .85
        df = df[col_order]
        return df
    
    def process(self, hesaplama_tipi):
        """
        fiyat_df uzerinde temettu tarihlerini ve hesaplama tipini baz alarak gerekli duzenlemeleri yapar. 
        """
        fiyat_df = self.preprocess_fiyatlar()
        # Duzenli alimlarda her ayin ilk gunu belli tutarlarda alim yapilmasi ongorulur
        if hesaplama_tipi == "duzenli":
            # Istenen tarih araligindaki ayin ilk is gunlerini verir
            dates_price = fiyat_df.groupby([fiyat_df["TARIH"].dt.year, fiyat_df["TARIH"].dt.month + 1])["TARIH"].min().reset_index(drop=True)[1:]
            # Istenen tarih araligindaki ilk ve son is gunlerini verir
            first_last = pd.Series([fiyat_df.iloc[0]["TARIH"], fiyat_df.iloc[-1]["TARIH"]])
            # Bu tarihleri bir Seri olarak birlestirir.
            dates_price = pd.concat([dates_price, first_last]).reset_index(drop=True)

        # Tek seferlik alimlarda istenen tarih araliginin en basinda alim yapilir
        elif hesaplama_tipi == "tek": # tek seferlik
            dates_price = pd.Series([fiyat_df.iloc[0]["TARIH"], fiyat_df.iloc[-1]["TARIH"]])
        
        dates_div = fiyat_df[fiyat_df["TEMETTU (TL)"] != 0]["TARIH"].to_list()
        new_fiyat_df = pd.concat([fiyat_df[fiyat_df["TARIH"].isin(dates_price)], fiyat_df[fiyat_df["TARIH"].isin(dates_div)]]).sort_values(by="TARIH")
        return new_fiyat_df.reset_index(drop=True)

    def df_maker(self, hesaplama_tipi, div_reinvest, tutar):
        """
        Nihai dfleri olusturur. bu dfler hesaplama tipi, tutar, period1 ve period2'ye gore degiskenlik gosterecektir.
        """
        df = self.process(hesaplama_tipi=hesaplama_tipi)
        # print(df)
        if hesaplama_tipi == "tek":
            baslangic_lot = tutar // df.loc[0, "HISSE KAPANIS FIYATI (TL)"]
            artan = tutar % df.loc[0, "HISSE KAPANIS FIYATI (TL)"]
            df["BASLANGIC YATIRIM (TL)"] = df.apply(lambda row: tutar if row.name == 0 else 0, axis=1)
            df["TEMETTU GELIRI (TL)"] = 0.0
            df["TEMETTU GELIRI + ARTAN (TL)"] = 0.0
            df["LOT"] = df.apply(lambda row: baslangic_lot if row.name == 0 else 0, axis=1)
            df["HARCANAN (TL)"] = df.apply(lambda row: baslangic_lot * row["HISSE KAPANIS FIYATI (TL)"] if row.name == 0 else 0, axis=1)
            df["ARTAN (TL)"] = df.apply(lambda row: artan if row.name == 0 else 0, axis=1)
            for i in range(1, len(df) - 1):
                toplam_tem = df.loc[i, "NET TEMETTU (TL)"] * df.loc[:i, "LOT"].sum()
                df.loc[i, "TEMETTU GELIRI (TL)"] = toplam_tem
                if div_reinvest:
                    tem_ve_artan = toplam_tem + df.loc[df.index[i-1], "ARTAN (TL)"]
                    lot = tem_ve_artan // df.loc[i, "HISSE KAPANIS FIYATI (TL)"]
                    artan = tem_ve_artan % df.loc[i, "HISSE KAPANIS FIYATI (TL)"]
                    harcanan = lot * df.loc[i, "HISSE KAPANIS FIYATI (TL)"]
                    df.loc[i, "TEMETTU GELIRI + ARTAN (TL)"], df.loc[i, "LOT"] = tem_ve_artan, lot
                    df.loc[i, "ARTAN (TL)"], df.loc[i, "HARCANAN (TL)"] = artan, harcanan
                else:
                    pass
                   
        elif hesaplama_tipi == "duzenli":
            artan = 0.0
            df["AYLIK YATIRIM TUTARI + ARTAN (TL)"] = 0.0
            df["TEMETTU GELIRI (TL)"] = 0.0
            df["LOT"] = 0.0
            df["HARCANAN (TL)"] = 0.0 
            df["ARTAN (TL)"] = 0.0
            for i in range(len(df) - 1):
                hb_net_tem = df.loc[i, "NET TEMETTU (TL)"]
                if hb_net_tem == 0:
                    df.loc[i, "AYLIK YATIRIM TUTARI + ARTAN (TL)"] = (tutar + artan)
                    lot = (tutar + artan) // df.loc[i, "HISSE KAPANIS FIYATI (TL)"]
                    artan = (tutar + artan) % df.loc[i, "HISSE KAPANIS FIYATI (TL)"]
                    harcanan = lot * df.loc[i, "HISSE KAPANIS FIYATI (TL)"]
                    df.loc[i, "LOT"], df.loc[i, "HARCANAN (TL)"], df.loc[i, "ARTAN (TL)"] = lot, harcanan, artan
                else:
                    df.loc[i, "TEMETTU GELIRI (TL)"] = hb_net_tem * df.loc[:i, "LOT"].sum()
                    if div_reinvest: 
                        df.loc[i, "AYLIK YATIRIM TUTARI + ARTAN (TL)"] = df.loc[i, "TEMETTU GELIRI (TL)"] + artan
                        lot = df.loc[i, "AYLIK YATIRIM TUTARI + ARTAN (TL)"] // df.loc[i, "HISSE KAPANIS FIYATI (TL)"]
                        artan = df.loc[i, "AYLIK YATIRIM TUTARI + ARTAN (TL)"] % df.loc[i, "HISSE KAPANIS FIYATI (TL)"]
                        harcanan = lot * df.loc[i, "HISSE KAPANIS FIYATI (TL)"]
                        df.loc[i, "LOT"], df.loc[i, "HARCANAN (TL)"], df.loc[i, "ARTAN (TL)"] = lot, harcanan, artan
                    else:
                        artan = df.loc[i-1, "ARTAN (TL)"]
                        df.loc[i, "ARTAN (TL)"] = artan
        df["LOT-kumulatif"] = df["LOT"].cumsum()
        df["PORTFOY-TL"] = df["HISSE KAPANIS FIYATI (TL)"] * df["LOT-kumulatif"]
        df["PORTFOY-USD"] = df["HISSE KAPANIS FIYATI (USD)"] * df["LOT-kumulatif"]
        if not div_reinvest:
            df["PORTFOY-TL"] += df["TEMETTU GELIRI (TL)"]
            df["PORTFOY-USD"] += df["TEMETTU GELIRI (TL)"] / df["USD/TRY"]
        return df
    
    def report(self, hesaplama_tipi, div_reinvest, tutar):
        """
        Hesaplamaya ait bir rapor olusturur
        """
        return_df = self.df_maker(hesaplama_tipi=hesaplama_tipi, div_reinvest=div_reinvest, tutar=tutar)
        toplam_lot = return_df["LOT"].sum()
        guncel_fiyat = return_df.loc[return_df.index[-1], "HISSE KAPANIS FIYATI (TL)"]
        guncel_fiyat_usd = return_df.loc[return_df.index[-1], "HISSE KAPANIS FIYATI (USD)"]
        guncel_portfoy = toplam_lot * guncel_fiyat + return_df.loc[return_df.index[-2], "ARTAN (TL)"]
        guncel_portfoy_usd = toplam_lot * guncel_fiyat_usd + return_df.loc[return_df.index[-2], "ARTAN (TL)"] / return_df.loc[return_df.index[-2], "USD/TRY"]
        tem_geliri = return_df["TEMETTU GELIRI (TL)"].sum()
        tem_geliri_usd = (return_df["TEMETTU GELIRI (TL)"] / return_df["USD/TRY"]).sum()

        if div_reinvest:
            tem_lot = return_df[return_df["NET TEMETTU (TL)"] > 0]["LOT"].sum()
            yatirim_tutari = return_df["HARCANAN (TL)"].sum() + return_df.loc[return_df.index[-2], "ARTAN (TL)"]
            yatirim_tutari_usd = (return_df["HARCANAN (TL)"] / return_df["USD/TRY"]).sum() + return_df.loc[return_df.index[-2], "ARTAN (TL)"] / return_df.loc[return_df.index[-2], "USD/TRY"]

            return {
                "yatirim_tutari": yatirim_tutari,
                "yatirim_tutari_usd": yatirim_tutari_usd,
                "tem_geliri": tem_geliri,
                "tem_geliri_usd": tem_geliri_usd,
                "tem_alinan_lot": tem_lot,
                "toplam_lot": toplam_lot,
                "guncel_portfoy": guncel_portfoy,
                "guncel_portfoy_usd": guncel_portfoy_usd
            }
        if not div_reinvest:
            tem_lot = 0

            if hesaplama_tipi == "tek":
                yatirim_tutari = return_df.loc[0, "HARCANAN (TL)"] + return_df.loc[0, "ARTAN (TL)"]
                yatirim_tutar_usd = (return_df.loc[0, "HARCANAN (TL)"] + return_df.loc[0, "ARTAN (TL)"]) / return_df.loc[0, "USD/TRY"]
            else:
                yatirim_tutari = return_df["HARCANAN (TL)"].sum() + return_df.loc[return_df.index[-2], "ARTAN (TL)"]
                yatirim_tutar_usd = (return_df["HARCANAN (TL)"] / return_df["USD/TRY"]).sum() + return_df.loc[return_df.index[-2], "ARTAN (TL)"] / return_df.loc[return_df.index[-2], "USD/TRY"]

            return {
                "yatirim_tutari":yatirim_tutari,
                "yatirim_tutari_usd": yatirim_tutar_usd,
                "tem_geliri": tem_geliri,
                "tem_geliri_usd": tem_geliri_usd,
                "toplam_lot": toplam_lot,
                "guncel_portfoy": guncel_portfoy + tem_geliri,
                "guncel_portfoy_usd": guncel_portfoy_usd + tem_geliri_usd
                }

# rx = ReturnCalculator(ticker="ASTOR", period1="25-02-2020", period2="25-02-2024")
# print(rx.df_maker(hesaplama_tipi="tek", div_reinvest=1, tutar=10000))
# print(rx.report(hesaplama_tipi="tek", div_reinvest=1, tutar=10000))