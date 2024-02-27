import pandas as pd
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))) # adding parent dir to python path
from Rasyolar import Review
from KAPScraper import KAPHelper, KAP
from datetime import datetime, timedelta

class HisseAnaliz():
    """
    A class to analyze stock data and provide various financial indicators.

    Attributes:
        firma_kodu (str): The company code for analysis.

    Methods:
        __init__(self, firma_kodu): Initializes the HisseAnaliz object.
        
        last_update(self): Returns the last update time.
        
        get_company_info(self): Returns useful information about the company.
        
        get_balance_sheet_summary(self): Returns balance-sheet short summary.
        
        __revenue_summary(self, time_type): Returns revenue summary.
        
        get_sum(self, time_type="quarterly"): Returns revenue summary + EBITDA.
        
        get_sources(self): Returns main sources of the company.
        
        simple_moving_average(self, price_df, span, source="is_yatirim"): Calculates x days of moving average price.
        
        exponential_moving_average(self, price_df, span, source="is_yatirim"): Calculates exponential moving average.
        
        rsi(self, price_df, source, days, rolling): Returns simple RSI value.
        
        momentum(self, price_df, source, days): Returns momentum value.
        
        min_max_price_52w(self, price_df, source): Returns min and max price values of the last 52 weeks.
                
        indicators(self, price_df, div_df): Returns various financial indicators.
        
        fundamental_ratios(self): Returns fundamental ratios of the company.
    """

    def __init__(self, firma_kodu) -> None:
        """
        Initializes the HisseAnaliz object with the given company code.

        Args:
            firma_kodu (str): The company code for analysis.
        """
        self.firma_kodu = firma_kodu
        try:
            self.rev = Review(company_name=firma_kodu, year=datetime.today().year)
        except Exception as e:
            print(f"Firma temel verileri alinirken hata olustu. Hata: {e}")
        try:
            self.kap = KAP(firma_kodu=firma_kodu)
        except Exception as e:
            pass
            # print(f"KAP bilgileri alinirken hata olustu. Hata: {e}")

    def last_update(self):
        """
        Returns the last update time in 
        HH:MM:SS
        mm-dd-YYYY format.
        """
        return datetime.today().strftime("%H:%M:%S\n%m-%d-%Y")

    def get_company_info(self):
        """
        Returns useful information about the company.
        """
        gb = self.kap.genel_bilgiler()
        return {
            "company_name": self.rev.company_name,
            "current_price": self.rev.current_price,
            "daily_price_change": self.rev.daily_price_change_rate,
            "market_value": self.rev.market_value,
            "working_capital": self.rev.working_capital, 
            "sector_industry": f"{gb['Şirketin Sektörü']}",
            # KAP ve Is Yatirim farkli sonuclar verdigi icin KAP'i tercih ettim.
            "number_of_shares": gb["Ödenmiş/Çıkarılmış Sermaye"], 
            "outstanding_shares": gb['Fiili Dolaşımdaki Paylar'].split("\r\n")[1].split('"')[1] if gb['Fiili Dolaşımdaki Paylar']!="Bilgi Mevcut Değil" else "", # outstanding shares: fiili dolasimdaki hisse senedi adedi
            "outstanding_shares%": gb['Fiili Dolaşımdaki Paylar'].split("\r\n")[1].split('"')[3] if gb['Fiili Dolaşımdaki Paylar']!="Bilgi Mevcut Değil" else "",
        }

    def get_balance_sheet_summary(self):
        """
        Returns balance-sheet short summary of the requested company.
        """
        rows_to_keep = [
        "Dönen Varlıklar",
        "Duran Varlıklar",
        "Özkaynaklar"
        ]
        bs_df = self.rev.financial_statement[0] # 0; annual, 1; quarter
        bs_df = bs_df[bs_df["ACIKLAMA"].isin(rows_to_keep)].reset_index(drop=True) 
        bs_df = pd.concat([bs_df, self.rev.financial_debt(), self.rev.net_debt()]).reset_index(drop=True)

        return bs_df

    def __revenue_summary(self, time_type):
        """
        Returns revenue summary of the requested company.

        Args:
            time_type (str): Type of time range for revenue summary.

        Returns:
            pandas.DataFrame: Revenue summary data.
        """
        
        rows_to_keep = [
            "Satış Gelirleri",
            "BRÜT KAR (ZARAR)",
            "FAALİYET KARI (ZARARI)",
            "Net Faaliyet Karı (Zararı)",
            "Ana Ortaklık Payları",
            ]
        if time_type=="quarterly":
            rev_df = self.rev.financial_statement[1] #quarterly
            rev_df = rev_df[rev_df["ACIKLAMA"].isin(rows_to_keep)].reset_index(drop=True)
        elif time_type=="cumulative":
            rev_df = self.rev.financial_statement[0] #quarterly
            rev_df = rev_df[rev_df["ACIKLAMA"].isin(rows_to_keep)].reset_index(drop=True)
            quarter, year = rev_df.columns[1].split("/")
            rev_df = rev_df.filter(regex=f"(ACIKLAMA|^{quarter}/({year}|{int(year)-1}))")
            rev_df["DEGISIM ORANI"] = round(100 * (rev_df.iloc[:,1] / rev_df.iloc[:,2]) - 100, 2)

        rev_df["ACIKLAMA"] = rev_df["ACIKLAMA"].apply(lambda x: x.title())
        mapping = {
            "Faali̇yet Kari (Zarari)": "Esas Faaliyet Karı (Zararı)",
            "Ana Ortaklık Payları": "Net Dönem Karı (Zararı)",
            "Ebitda": "FAVÖK"
            }
        rev_df["ACIKLAMA"] = rev_df["ACIKLAMA"].apply(lambda x: mapping.get(x, x))
        return rev_df

    def get_sum(self, time_type="quarterly"):
  
        """
        Returns revenue summary + EBITDA dataframe for the requested company.

        Args:
            time_type (str, optional): Type of time range. Defaults to "quarterly".
                - valid options are [quarterly, cumulative]

        Returns:
            pandas.DataFrame: Revenue summary + EBITDA data.
        """
        ebitda = self.rev.ebitda()
        if time_type=="quarterly":
            ebitda.loc[0, "ACIKLAMA"] = "FAVÖK"
            return pd.concat([self.__revenue_summary(time_type=time_type), ebitda], ignore_index=True) 
        
        elif time_type=="cumulative":    
            # Guncel yil ve ceyrek 
            year = ebitda.columns[1].split("/")[1]
            quarter = ebitda.columns[1].split("/")[0]
            # Mevcut yila gore filtrelenmis
            df = ebitda.filter(regex=f"{year}$")
            # Bir onceki seneye gore filtrelenmis
            dff = ebitda.filter(regex=f"{int(year)-1}$")
            dff = dff.loc[:, f"{quarter}/{int(year)-1}":]
            new_df = pd.DataFrame([{
                "ACIKLAMA": "FAVÖK",
                f"{quarter}/{year}": sum(df.iloc[0]),
                f"{quarter}/{int(year)-1}": sum(dff.iloc[0]),
            }])
            return pd.concat([self.__revenue_summary(time_type=time_type), new_df], ignore_index=True) 

    def get_sources(self):
        """
        Returns main sources of the requested company.
        """
        rows_to_keep = [
            "Kısa Vadeli Yükümlülükler",
            "Uzun Vadeli Yükümlülükler",
            "Ana Ortaklığa Ait Özkaynaklar"
        ]
        fs_ann = self.rev.financial_statement[0] # annual
        sources = fs_ann[fs_ann["ACIKLAMA"].isin(rows_to_keep)].reset_index(drop=True)
        return sources

    def simple_moving_average(self, price_df, span, source="is_yatirim"):
        """
        Calculates x days of moving average price.

        Args:
            price_df (pandas.DataFrame): DataFrame containing price data.
            span (int): Number of days for moving average.
            source (str, optional): Source of data. Defaults to "is_yatirim".

        Returns:
            pandas.DataFrame: DataFrame with moving average data.
        
        """
        if source == "yahoo":
            col = "KAPANIS-yahoo"
        elif source == "is_yatirim":
            col = "KAPANIS FIYATI (TL)"
        price_df[f"Simple Moving Average ({span})"] = price_df[col].rolling(window=span, min_periods=1).mean()
        return price_df
    
    def exponential_moving_average(self, price_df, span, source="is_yatirim"):
        """
        Calculates exponential moving average.

        Args:
            price_df (pandas.DataFrame): DataFrame containing price data.
            span (int): Span for exponential moving average.
            source (str, optional): Source of data. Defaults to "is_yatirim".

        Returns:
            pandas.DataFrame: DataFrame with exponential moving average data.
        """
        if source == "yahoo":
            col = "KAPANIS-yahoo"
        elif source == "is_yatirim":
            col = "KAPANIS FIYATI (TL)"
        
        price_df[f"EMA ({span})"] = price_df[col].ewm(span=span, adjust=True).mean()
        return  price_df
    
    def rsi(self, price_df, source, days, rolling):
        """
        Returns simple RSI value.
        Formula:
        RSI = 100 - (100/(1 + AVG GAIN / AVG LOSS)) or RSI = 100 * AVG GAIN / (AVG GAIN + AVG LOSS)
        Args:
            price_df (pandas.DataFrame): DataFrame containing price data.
            source (str): Source of data.
            days (int): Number of days for RSI calculation.
            rolling (int): Rolling window size.

        Returns:
            pandas.DataFrame: DataFrame with RSI data.
        """
        if source == "yahoo":
            col = "KAPANIS-yahoo"
        elif source == "is_yatirim":
            col = "KAPANIS FIYATI (TL)"
        # Son X gunun datasi
        price_df = price_df.iloc[-days:].copy()
        price_df.loc[:, "CHANGE"] = price_df[col].diff() # .diff() fonksiyonu uygulanan kolon icin default olarak bir onceki row ile farkini alarak geri verir
        price_df = price_df.dropna().reset_index(drop=True)
        price_df["CHANGE UP"] = price_df["CHANGE"].apply(lambda x: max(0, x)) 
        price_df["CHANGE DOWN"] = price_df["CHANGE"].apply(lambda x: abs(min(0, x))) 
        price_df["AVG GAIN"] = price_df["CHANGE UP"].rolling(rolling).mean() 
        price_df["AVG LOSS"] = price_df["CHANGE DOWN"].rolling(rolling).mean().abs() 
        price_df["RSI"] = 100 * price_df["AVG GAIN"] / (price_df["AVG GAIN"] + price_df["AVG LOSS"])
        return price_df
    
    def momentum(self, price_df, source, days):
        """ 
        Returns momentum value.
        Formula:
        The latest closing price - X days ago closing price

        Args:
            price_df (pandas.DataFrame): DataFrame containing price data.
            source (str): Source of data.
            days (int): Number of days for momentum calculation.

        Returns:
            float: Momentum value.
        """
        price_df = price_df.iloc[-(days+1):,:].reset_index(drop=True) # used days + 1 cause we calculate X days AGO, which actually excludes that number of days
        if source == "yahoo":
            col = "KAPANIS-yahoo"
        elif source == "is_yatirim":
            col = "KAPANIS FIYATI (TL)"
        return round(price_df.loc[price_df.index[-1], col] - price_df.loc[price_df.index[0], col], 2) 

    def min_max_price_52w(self, price_df, source):
        """
        Returns min and max price values of the last 52 weeks.

        Args:
            price_df (pandas.DataFrame): DataFrame containing price data.
            source (str): Source of data.

        Returns:
            tuple: Min and max price values.
        """
        date = price_df["TARIH"].iloc[-1]
        date_1y_ago = date - timedelta(weeks=52)
        price_df = price_df[price_df["TARIH"]>=date_1y_ago].reset_index(drop=True)
        if source == "yahoo":
            return round(price_df["LOW"].min(), 2), round(price_df["HIGH"].max(), 2)
        elif source == "is_yatirim":
            return round(price_df["GUN ICI EN DUSUK"].min(), 2), round(price_df["GUN ICI EN YUKSEK"].max(), 2)


    def indicators(self, price_df):
        """
        Returns various financial indicators.

        Args:
            price_df (pandas.DataFrame): DataFrame containing price data.
            div_df (pandas.DataFrame): DataFrame containing dividend data.

        Returns:
            dict: Dictionary containing financial indicators.
        """
        return {
            "simple_moving_average": (self.simple_moving_average(price_df=price_df, span=10).iloc[-1, -1], self.simple_moving_average(price_df=price_df, span=50).iloc[-1, -1], self.simple_moving_average(price_df=price_df, span=200).iloc[-1, -1]), # guncel deger
            "exponential_moving_average": (self.exponential_moving_average(price_df=price_df, span=10).iloc[-1, -1], self.exponential_moving_average(price_df=price_df, span=50).iloc[-1, -1], self.exponential_moving_average(price_df=price_df, span=200).iloc[-1, -1]),
            "relative_strength_index": self.rsi(price_df=price_df, source="is_yatirim", days=100, rolling=14).iloc[-1, -1],
            "momentum": self.momentum(price_df=price_df, source="is_yatirim", days=10),
            "min_max": self.min_max_price_52w(price_df=price_df, source="is_yatirim"),
        }
    def fundamental_ratios(self):
        """
        Returns fundamental ratios of the company.

        Returns:
            dict: Dictionary containing fundamental ratios.
        """
        return {
            "fk": self.rev.price_to_earning_ratio(),
            "pd/dd": self.rev.price_to_book_ratio(),
            "eps": self.rev.earning_per_share(),
            "roa": self.rev.return_on_assets(),
            "roe": self.rev.return_on_equity(),
            "debt_to_equity": self.rev.debt_to_equity()
        }