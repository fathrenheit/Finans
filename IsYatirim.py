import requests
import time
import random 
import json
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

class IsYatirimScraper(object):
    """
    A class that collects information about a given company from isyatirim.com.tr

    Attributes:
        API_URL_FIYAT (str): URL for retrieving historical price data.
        API_URL_MALI_TABLO (str): URL for retrieving financial data.
        API_URL_SERMAYE_ARTIRIMLARI (str): URL for retrieving capital gain data.
        API_URL_TEMETTU_GECMISI (str): URL for retrieving dividend data.
        API_URL_YABANCI_ORANI (str): URL for retrieving foreign exchange rate data.
        API_URL_DEGERLI_METALLER_VE_EMTIA (dict): URLs for retrieving precious metals data.

    Methods:
        make_request(method, url, params, json_payload, header):
            Simply makes a request to given url and returns the response.
        get_is_yatirim_price_data(ticker, start_date, end_date):
            Retrieves historical price data of a given company
        get_is_yatirim_financial_data(ticker, current_year, cumulative):
            Retrieves financial data; balance-sheet, revenue table and cash-flow of a given company.
        get_capital_gain_data(ticker, year):
            Retrieves capital gain data of a given company.
        get_dividend_data(ticker):
            Retrieves dividend data of a given company
        get_foreign_exchange_rate(ticker, start_date, end_date):
            Retrieves foreign exchange rate of a given company in a time range
        get_precious_metals_data(parameters, start_date, end_date, rep_type):
            Retrieves data for various precious metals such as gold, silver, platin etc.
    """

    def __init__(self) -> None:
        # Gerekli API URL'leri
        self.API_URL_FIYAT = "https://www.isyatirim.com.tr/_layouts/15/Isyatirim.Website/Common/Data.aspx/HisseTekil"
        self.API_URL_MALI_TABLO = "https://www.isyatirim.com.tr/_layouts/15/IsYatirim.Website/Common/Data.aspx/MaliTablo"
        self.API_URL_SERMAYE_ARTIRIMLARI = "https://www.isyatirim.com.tr/_layouts/15/IsYatirim.Website/StockInfo/CompanyInfoAjax.aspx/GetSermayeArttirimlari"
        self.API_URL_TEMETTU_GECMISI = 'https://www.isyatirim.com.tr/tr-tr/analiz/hisse/Sayfalar/sirket-karti.aspx?hisse='
        self.API_URL_YABANCI_ORANI = "https://www.isyatirim.com.tr/_layouts/15/IsYatirim.Website/StockInfo/CompanyInfoAjax.aspx/GetYabanciOranlarXHR"
        self.API_URL_DEGERLI_METALLER_VE_EMTIA = {
            "historical":"https://www.isyatirim.com.tr/_Layouts/15/IsYatirim.Website/Common/ChartData.aspx/IndexHistoricalAll",
            "daily": f'https://www.isyatirim.com.tr/_layouts/15/Isyatirim.Website/Common/Data.aspx/OneEndeks'
        }
        
    def make_request(self, method, url, params=None, json_payload=None, headers=None):
        """
        Makes a request to the specified API URL and returns its content.
        Belirtilen/verilen API URL'sine bir istek yapar ve içeriğini döndürür/geri verir.

        Args:
            method (str): The HTTP method to be used for the request (e.g., 'GET', 'POST').
            url (str): The API URL from which data will be retrieved.
            params (dict, optional): The required parameters to retrieve data (default is None).
            json_payload (dict, optional): The payload data in JSON format, used for POST requests (default is None).
            headers (dict, optional): The required headers to be used for successful requests (default is None).

        Returns:
            Union[dict, None]: The response data if the request is successful; otherwise, None.
        """

        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        ]
        response = None
        timestamp = int(time.time())
        headers = {"User-Agent":f"{random.choice(user_agents)} {timestamp}"}
        if method == "GET":
            response = requests.get(url, params=params, headers=headers)
        elif method == "POST":
            response = requests.post(url, json=json_payload, headers=headers)
        
        if response is None:
            print("Failed to make request. No response recieved.")
            return None

        if response.status_code == 200:
            content_type = response.headers.get("content-type", "")
            if "text/html" in content_type:
                return response.content

            try:
                data = response.json()

                if "value" in data:
                    return data["value"]
            
                if "d" in data:
                    if isinstance(data["d"], str):
                        return json.loads(data["d"])
                    else:
                        return data["d"]
                if "data" in data:
                    return data["data"]
                return data # returns directly if no special process needed
            except json.JSONDecodeError:
                print("Failed to decode JSON data.")
        else:
            print(f"Failed to fecth data. Status code: {response.status_code}")

        return None

    def __process_is_yatirim_price_data(self, data) -> pd.DataFrame:
        """
        Process the data retrived from isyatirim website and returns a dataframe.
        API'den elde edilen fiyat verilerini işler ve bir DataFrame olarak döndürür/geri verir.

        Args:
            data (dict): The response data retrieved from the API.

        Returns:
            pd.DataFrame: A pandas DataFrame containing modified historical price data.
        """
        df = pd.DataFrame(data) # Price values are inside of "value" key.
        column_mapping = {
        'HGDG_HS_KODU': 'HISSE KODU',
        'HGDG_TARIH': 'TARIH',
        'HGDG_KAPANIS': 'KAPANIS FIYATI (TL)',
        "HGDG_MIN": "GUN ICI EN DUSUK",
        "HGDG_MAX": "GUN ICI EN YUKSEK",
        'END_DEGER': 'ENDEKS DEGERI (BIST100)',
        'DD_DEGER': 'DOLAR KURU (TL)',
        'DOLAR_BAZLI_FIYAT': 'DOLAR BAZLI FIYAT (USD)',
        'ENDEKS_BAZLI_FIYAT': 'ENDEKS BAZLI FIYAT',
        'HG_HACIM': 'HACIM (TL)'
        }
        # List of columns to keep based on the mapping
        columns_to_keep = list(column_mapping.keys())
        # Find the columns that are not in the 'columns_to_keep' list
        columns_to_delete = df.columns.difference(columns_to_keep)
        # Drop the unwanted columns
        df = df.drop(columns=columns_to_delete)
        # Changing the column names
        df = df.rename(columns=column_mapping)
        # Desired order of columns
        desired_order = ['TARIH', 'HISSE KODU', 'GUN ICI EN DUSUK', 'GUN ICI EN YUKSEK', 'KAPANIS FIYATI (TL)', 'ENDEKS DEGERI (BIST100)', 'ENDEKS BAZLI FIYAT', 'DOLAR KURU (TL)', 'DOLAR BAZLI FIYAT (USD)', 'HACIM (TL)']
        # Reindex the DataFrame with the desired order of columns
        df = df.reindex(columns=desired_order)
        df["TARIH"] = pd.to_datetime(df["TARIH"], format="%d-%m-%Y")
        return df

    def get_is_yatirim_price_data(self, ticker:str, start_date:str, end_date:str) -> json:
        """
        Retrieves historical price data for the specified stock code from the API and returns it as a JSON object.
        Belirtilen hisse kodu için API'den geçmiş fiyat verilerini alır ve bunları bir JSON nesnesi olarak döndürür/geri verir.

        Args:
            ticker (str): The stock code of the requested company.
            start_date (str): The start date for retrieving historical price data. Valid format is dd-mm-YYYY.
            end_date (str): The end date for retrieving historical price data. Valid format is dd-mm-YYYY.

        Returns:
            json: A JSON object containing the necessary information to be processed by the helper function __process_is_yatirim_price_data().
        """
        # Necessary parameters
        params = {
            "hisse": ticker,            
            "startdate": start_date,    # dd-mm-yyyy
            "enddate": end_date         # dd-mm-yyyy
        }
        data = self.make_request(
            method="GET", 
            url=self.API_URL_FIYAT, 
            params=params
            )
        if data is not None:
            return self.__process_is_yatirim_price_data(data=data)
        
    def __process_financial_data(self, data, params:dict) -> pd.DataFrame:
        """
        Processes financial data retrieved from the API and returns a DataFrame containing 20 quarters/5 years.
        API'den alınan finansal verileri işler ve 20 çeyrek/5 yıl içeren bir DataFrame döndürür/geri verir.

        Args:
            data: Response data retrieved from the API.
            params (dict): Additional parameters (if any) used for processing the data.

        Returns:
            pd.DataFrame: A pandas DataFrame containing modified financial data.
        """
        data = pd.DataFrame(data)
        # Gets financial data rows description rows as Turkish if exhange was chosen as TRY and set these rows as indices.
        if params["exchange"] == "TRY":
            new_rows = data["itemDescTr"].to_list()
        # Gets financial data rows description rows as English if exhange was chosen as USD and set these rows as indices.
        elif params["exchange"] == "USD":
            new_rows = data["itemDescEng"].to_list()
        data.index = new_rows # Setting
        data = data.drop(columns=data.columns[[0,1,2]])
        column_mapping = {
            # "itemDescTr":"BILANCO",
            # "itemDescEng":"BALANCE-SHEET",
            "value1":f"{params['period1']}/{params['year1']}",
            "value2":f"{params['period2']}/{params['year1']}",
            "value3":f"{params['period3']}/{params['year1']}",
            "value4":f"{params['period4']}/{params['year1']}",
        }
        data = data.rename(columns=column_mapping).dropna(axis=1, how="all")
        data = data.astype('int64')
        return data
    
    def get_is_yatirim_financial_data(self, ticker:str, current_year:int, cumulative=True):
        """
        Retrieves financial data including balance-sheet, revenue table, and cash-flow for 20 quarters and returns as a JSON object.
        20 çeyrek için bilanço, gelir tablosu ve nakit akışı da dahil olmak üzere finansal verileri alır ve JSON nesnesi olarak döndürür.

        Args:
            ticker (str): Stock code of the requested company.
            current_year (int): The current year for which financial data is requested.
            cumulative (bool, optional): Whether to retrieve cumulative financial data. Defaults to True.

        Returns:
            dict: A JSON object containing financial data.
        """
        # preparing time objects
        years = range(current_year - 3, current_year+1) # last 5 years
        quarters = [3, 6, 9, 12]
        time_range = sorted([(q,y) for q in reversed(quarters) for y in years], key=lambda x:x[1], reverse=True)

        all_data_frames = []
        # preparing parameters
        for time_index in range(0, len(time_range), 4):
            time_ = time_range[time_index:time_index+4]
            params = {
                "companyCode": f"{ticker}",
                "exchange": "TRY", #USD
                "financialGroup": "XI_29",
                "_":f"{int(time.time())}",
            }
            for i, (quarter, year) in enumerate(time_, start=1):
                params[f"year{i}"] = str(year)
                params[f"period{i}"] = str(quarter)
            data = self.make_request(method="GET", url=self.API_URL_MALI_TABLO, params=params)
            if data:
                all_data_frames.append(self.__process_financial_data(data=data, params=params))
        
        if not all_data_frames:
            raise ValueError("HATALI FIRMA/HISSE KODU ya da TARIH GIRILDI. LUTFEN KONTROL EDIN.")
        
        # make balance-sheet table out of the list
        df = pd.concat(all_data_frames, axis=1).dropna(axis=1, how="all") 
        df = df.reset_index()
        df.columns = ["ACIKLAMA"] + list(df.columns[1:])                
        
        if cumulative:
            return df
        else:
            new_df = pd.DataFrame(data=0, columns=df.columns[:-2], index=df.index)
            new_df["ACIKLAMA"] = df["ACIKLAMA"]
            try:
                for col in df.columns[1:]:
                    if '3/' in col:
                        new_df[col] = df[col]
                for col in df.columns[1:]:
                    if '3/' not in col:
                        new_df[col] = df[col] - df[df.columns[df.columns.get_loc(col) + 1]]
            except Exception:
                print(f"Firma son zamanlarda halka arz oldugundan gecmis veriler tam olarak alinamadi.")
                return new_df
            return new_df

    def __process_capital_gain_data(self, data:list) -> pd.DataFrame:
        """
        Processes the capital gain data and returns a processed DataFrame.
        Sermaye artışı verilerini işler ve düzenlenmiş bir DataFrame döndürür. Sadece get_capital_gain_data() yöntemi içinde kullanılmak üzere tasarlanmıştır.
        
        Args:
            data (list): List of capital gain data.
            
        Returns:
            pd.DataFrame: A pandas DataFrame containing processed capital gain information.
        """
        df = pd.DataFrame(data)
        column_mapping = {
            "SHHE_HS_KODU": "HISSE KODU", 
            "SHHE_TARIH": "TARIH", 
            "HSP_BOLUNME_SONRASI_SERMAYE": "BOLUNME SONRASI SERMAYE (TL)", 
            "SHHE_BDLI_ORAN": "BEDELLI ORAN (%)", 
            "SHHE_BDLI_NOM_TUTAR": "BEDELLI NOMINAL TUTAR (TL)", 
            "SHHE_RHK_ORAN": "DIGER (%)", 
            "SHHE_BDSZ_IK_ORAN": "BEDELSIZ IK ORANI (%)", 
            "SHHE_BDSZ_TM_ORAN": "BEDELSIZ TEMETTU ORANI"
        }
        # List of columns to keep based on the mapping
        columns_to_keep = list(column_mapping.keys())
        # Find the columns that are not in the 'columns_to_keep' list
        columns_to_delete = df.columns.difference(columns_to_keep)
        df = df.drop(columns=columns_to_delete)
        # Changing the column names
        df = df.rename(columns=column_mapping)
        # Desired order of columns
        desired_order = ['HISSE KODU', 'TARIH', 'BOLUNME SONRASI SERMAYE (TL)', 'BEDELLI ORAN (%)', 'BEDELLI NOMINAL TUTAR (TL)', 'DIGER (%)', 'BEDELSIZ IK ORANI (%)', 'BEDELSIZ TEMETTU ORANI']
        # Reindex the DataFrame with the desired order of columns
        df = df.reindex(columns=desired_order)
        # From unix-time to regular time unit.
        df["TARIH"] = df["TARIH"].apply(lambda timestamp: "Açıklanmadı" if timestamp < 0 else pd.to_datetime(timestamp / 1000, unit="s").date()) # Negative timestamps are used as NOT ANNOUNCED/Açıklanmadı in isyatirim website.
        df = pd.concat([
            df[df["TARIH"] == "Açıklanmadı"],
            df[df["TARIH"] != "Açıklanmadı"].sort_values(by=["TARIH"], ascending=False) #[::-1],
        ])
        return df.reset_index(drop=True) 

    def get_capital_gain_data(self, ticker: str, year=0):
        """
        Retrieves historical capital gain data of a given company.
        Verilen bir şirketin geçmiş sermaye artış verilerini alır.
        
        Args:
            ticker (str): Stock code of the requested company.
            year (int): Year for which capital gain data is requested. Use 0 for all years or specify a specific year.

        Returns:
            pd.DataFrame: A pandas DataFrame containing historical capital gain data.
        """
        payload = {
            "hisseKodu": f"{ticker}",
            "hisseTanimKodu": "", # FILTRE KODLARI -> NAKIT TEMETTU: 04, BIRLESME: 90, BIRINCIL HALKA ARZ: 99, HEPSI:"" 
            "yil": 0, # BURADA FILTRE KODU OLARAK ISTENEN TARIH OZELLIKLE GIRILEBILIR; 2023 GIBI AMA GEREK YOK.
            "zaman": "HEPSI", # FILTRE KODLARI -> "Tamamlanan", "Planlanan"
            "endeksKodu": "09",
            "sektorKodu": "",
        }
        json_data = self.make_request(method="POST", url=self.API_URL_SERMAYE_ARTIRIMLARI, json_payload=payload)
        return self.__process_capital_gain_data(data=json_data)
    
    def get_dividend_data(self, ticker:str) -> pd.DataFrame:
        """
        Retrieves historical dividend information for a given company from isyatirim.com.tr.
        This function does not use API calls, instead it use pure scraping to get the data
        Belirtilen şirket için geçmiş temettü bilgilerini alır. Bu fonksiyon, API çağrıları kullanmaz; bunun yerine veriyi
        kazıyarak https://www.isyatirim.com.tr/tr-tr/analiz/hisse/Sayfalar/sirket-karti.aspx?hisse={HISSEKODU} adresinden alır.
        
        Args:
            ticker (str): The stock code of the requested company.

        Returns:
            pd.DataFrame: A pandas DataFrame containing historical dividend data.
        """

        URL = self.API_URL_TEMETTU_GECMISI + ticker
        parsed = BeautifulSoup(self.make_request(method="GET", url=URL), "html.parser")
        
        # Getting column names in a list
        dividend_table = parsed.select(selector='table.dataTable.hover.nowrap.excelexport[data-csvname="temettugercek"]')
        dividend_table_columns = dividend_table[0].find_all('th')
        columns = [col.get_text(strip=True) for col in dividend_table_columns]

        # Getting rows
        rows = parsed.select(selector='tbody.temettugercekvarBody.gercek tr.temettugercekvarrow td')
        rows = [r.get_text(strip=True) for r in rows]
        rows = [rows[i:i+8] for i in range(0, len(rows), 8)]
        df = pd.DataFrame(data=rows, columns=columns)
        df = df.drop(columns=df.columns[[2,4,5]])
        # Convert the string date column to datetime object
        df[df.columns[1]] = pd.to_datetime(df[df.columns[1]], format="%d.%m.%Y")
        # Add day of the week information with Latin names
        df['DAGITIM GUNU'] = df[df.columns[1]].dt.strftime('%A') # In order to get the day of the date by using .dt.strftime("%A")
        df[df.columns[1]] = df[df.columns[1]].dt.date
        col_mapping = {
            df.columns[ind]:val for ind, val in enumerate(["HISSE KODU", "DAGITIM TARIHI", "HISSE BASI TEM. BRUT (TL)", "TOPLAM TEMETTU (TL)", "DAGITMA ORANI (%)"])
            }
        df = df.rename(columns=col_mapping)
        return df[["HISSE KODU", "DAGITIM TARIHI", "DAGITIM GUNU", "HISSE BASI TEM. BRUT (TL)", "TOPLAM TEMETTU (TL)", "DAGITMA ORANI (%)"]]
    
    def __date_edit(self, current_date, increment_factor):
        """
        Converts a string datetime object to a datetime object, increments it by one, and returns it as a string-datetime object.
        Bir string-datetime nesnesini bir datetime nesnesine dönüştürür, bir birim artırır ve sonucu string-datetime olarak döndürür.
        
        Args:
            current_date (str): The current date in string-datetime format.
            increment_factor: The factor by which the date will be incremented.

        Returns:
            str: The modified date in string-datetime format.
        """

        date_form = '%d-%m-%Y'
        try:
            datetime_obj = datetime.strptime(current_date, date_form)
        except:
            print(f'Hatali tarih formati. Dogru format: dd-mm-yyyy. Duzeltilmesi gereken tarih: {current_date}')
            return None 
        if increment_factor == 1:
            new_dt = datetime_obj + timedelta(days=1) # increment current date by 1.
        elif increment_factor == -1:
            new_dt = datetime_obj - timedelta(days=1) # increment current date by -1.
        return datetime.strftime(new_dt.date(), date_form)
        
    def get_foreign_exchange_rate(self, ticker:str, start_date, end_date): # tarihler ddmmyy olarak girilecek.
        """
        Retrieves the foreign exchange rate for the requested company within the specified time range.
        Belirtilen bir firmanın belirli bir zaman aralığında yabancı takas oranını alır.

        Args:
            ticker (str): The stock code of the company.
            start_date (str): The beginning date of the time range in 'dd-mm-YYYY' format.
            end_date (str): The ending date of the time range in 'dd-mm-YYYY' format.

        Returns:
            pandas.DataFrame: A DataFrame containing the exchange rate.
        """
        json_params = {
            "baslangicTarih": start_date, #f"{baslangicTarihi[:2]}-{baslangicTarihi[2:4]}-20{baslangicTarihi[4:]}",
            "bitisTarihi": end_date, #f"{bitisTarihi[:2]}-{bitisTarihi[2:4]}-20{bitisTarihi[4:]}",
            "sektor": "",
            "endeks": "09",
            "hisse": f"{ticker}"
        }
        response = self.make_request(method="POST", url=self.API_URL_YABANCI_ORANI, json_payload=json_params)
        if not response: # if there is no result, it returns an empty list
            print("Belirtilen tarihlere ait yabanci takas orani bulunamamistir.\nEn yakin tarihler deneniyor...")    
            date_info = json_params['baslangicTarih'], json_params['bitisTarihi']
            df_dict = {}
            try:
                day_obj = datetime.strptime(json_params['bitisTarihi'], '%d-%m-%Y') - datetime.strptime(json_params['baslangicTarih'], '%d-%m-%Y')
                day_obj = day_obj.days # Istenen tarih araligindaki toplam gun sayisi
            except ValueError:
                print(f"Valid format of the date is dd-mm-yyyy.\nControl start date({json_params['baslangicTarih']}) and end date({json_params['bitisTarihi']})")
                return None
            json_params['bitisTarihi'] = date_info[0]
            # Baslangic tarihi denenir, sonuc alinamazsa ileri dogru gidilir.
            for _ in range(day_obj):
                response = self.make_request(method="POST", url=self.API_URL_YABANCI_ORANI, json_payload=json_params)
                if response:
                    df_dict['baslangicTarih'] = json_params['baslangicTarih']
                    break
                else:
                    json_params['baslangicTarih'] = self.__date_edit(current_date=json_params['baslangicTarih'], increment_factor=1)
                    json_params['bitisTarihi'] = self.__date_edit(current_date=json_params['bitisTarihi'], increment_factor=1)

            # Bitis tarihi denenir, sonuc alinamazsa geriye dogru gidilir.
            json_params['bitisTarihi'] = date_info[1]
            for _ in range(day_obj):
                response = self.make_request(method="POST", url=self.API_URL_YABANCI_ORANI, json_payload=json_params)
                if response:
                    df_dict['bitisTarihi'] = json_params['bitisTarihi']
                    break
                else:
                    json_params['bitisTarihi'] = self.__date_edit(current_date=json_params['bitisTarihi'], increment_factor=-1)

            if len(df_dict.keys()) == 0:
                print(f"Istenilen tarih araliginda data bulunamadi. Tarihleri ({start_date} ve {end_date}) dogru sirada ve dogru formatta girdiginden emin ol.\nAyrica hisse kodunu ({ticker}) da kontrol et.")
                return None
        
            json_params['baslangicTarih'] = df_dict['baslangicTarih']
            json_params['bitisTarihi'] = df_dict['bitisTarihi']
            # Makes a new request if dates are absolutely correct.
            response = self.make_request(method="POST", url=self.API_URL_YABANCI_ORANI, json_payload=json_params)

        df = pd.DataFrame(response)    
        column_mapping = {
            'HISSE_KODU': 'HISSE KODU',
            'PRICE_TL': 'GUNCEL FIYAT',
            'YAB_ORAN_START': json_params['baslangicTarih'],
            'YAB_ORAN_END': json_params['bitisTarihi'],
            'DEGISIM': 'DEGISIM (%)',
            'HISSE_TANIM': 'HISSE ISMI'
        }

        df = df.drop(columns=df.columns.difference(column_mapping.keys()))
        df = df.rename(columns=column_mapping)
        df.insert(df.columns.get_loc('HISSE KODU') + 1, 'HISSE ISMI', df.pop('HISSE ISMI'))
        df['HISSE ISMI'] = df['HISSE ISMI'].str.strip()
        return df

    def get_precious_metals_data(self, parameters:list, start_date:str, end_date:str, rep_type="historical"):
        """
        Gets precious metal data for the specified time range.
        Belirtilen zaman aralığı için değerli metal verilerini alır.

        Args:
            parameters: List of metal symbols to be retrieved.
                Options are:
                    XAU/USD: Gold/Usd
                    XAG/USD: Silver/Usd
                    BRENT: Brent Oil/Usd
                    XPD/USD: Palladium/Usd
                    XPT/USD: Platin/Usd             
            start_date (str): Beginning date for the data. Valid format is 'dd-mm-YYYY' in str format.
            end_date (str): End date for the data. Valid format is 'dd-mm-YYYY' in str format.
            rep_type (str, optional): Type of data to retrieve, either "historical" or "daily". Defaults to "historical".

        Returns:
            pandas.DataFrame: A DataFrame containing historical/daily price information of precious metals.
        """
        
        if rep_type not in ["historical", "daily"]:
            print(f"Hatali parametre girisi. {rep_type} degerini kontrol ediniz.")
            return None
        for param in parameters:
            if param not in ["XAU/USD", "BRENT", "XAG/USD", "XPD/USD", "XPT/USD"]:
                print(f"Hatali parametre girisi. {parameters} degerini kontrol ediniz.")
                return None
            
        param_details = {
        'BRENT': 'BRENT PETROL ($)',
        'XAG/USD': 'GUMUS ($)',
        'XAU/USD': 'ALTIN ($)',
        'XPD/USD': 'PALLADIUM ($)',
        'XPT/USD': 'PLATIN ($)',
        }
        dfs = []
        # returns historical values of requested metals
        if rep_type == "historical":
            print("TARIHSEL VERILER:")
            start_date = "".join(start_date.split("-")[::-1])
            end_date = "".join(end_date.split("-")[::-1])
            
            for param in parameters:
                params = {
                    "period":1440, #60:saatlik, 180:3 saatlik, 360:6 saatlik, 60*24:1440; gunluk ...
                    "endeks":param,
                    "from":f"{start_date}000000",
                    "to":f"{end_date}235959"
                }
                
                data = self.make_request(method="GET", url=self.API_URL_DEGERLI_METALLER_VE_EMTIA["historical"], params=params)
                if data:
                    column_name = param_details[param]
                    df = pd.DataFrame(data, columns=["TARIH", column_name])
                    df["TARIH"] = df["TARIH"].apply(lambda unix_time_obj: datetime.fromtimestamp(unix_time_obj/1000.0).date())
                    dfs.append(df)
                    
            merged_df = dfs[0] # herhangi bir df baz alinarak yan yana merger edilir
            for df in dfs[1:]:
                merged_df = pd.merge(merged_df, df, on="TARIH")
            return merged_df
        
        # returns daily changes of requested metals
        elif rep_type == "daily":
            print("GUNLUK DEGISIM:")
            for param in parameters:
                params = {
                    "endeks":param
                }
                data = self.make_request(method="GET", url=self.API_URL_DEGERLI_METALLER_VE_EMTIA["daily"], params=params)
                if data:
                    dfs.append(data)
            flatten_list_of_dicts = [item for df in dfs for item in df]
            df = pd.DataFrame(flatten_list_of_dicts)
            column_mapping = {
            'dailyChangePercentage': 'GUNLUK DEGISIM (%)',
            'dailyChange': 'GUNLUK DEGISIM ($)',
            'c': 'EMTIA KODU',
            'last': 'SON DEGER ($)',  
            'previousDayClose': 'ONCEKI KAPANIS ($)',
            'description': 'EMTIA ISMI (EN)'
            }
            df = df.rename(columns=column_mapping)
            df["EMTIA ISMI (TR)"] = df["EMTIA KODU"].map(param_details)
            desired_order = ['EMTIA KODU', 'EMTIA ISMI (EN)', "EMTIA ISMI (TR)", 'ONCEKI KAPANIS ($)','SON DEGER ($)', 'GUNLUK DEGISIM ($)','GUNLUK DEGISIM (%)',]
            return df[desired_order] # ya da -> .reindex(columns=desired_order) 
