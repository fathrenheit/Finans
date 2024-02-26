# import requests, json, datetime
# import pandas as pd

# class YahooFinancePriceDataFetcher:
#     """
#     A class for fetching price data from Yahoo Finance API.

#     Attributes:
#         None

#     Methods:
#         fetch_prices(company_code, period_1, period_2, interval="1d", last_x_days=""):
#             Fetches price history of a requested company within a specified time range.
#     """

#     def __init__(self) -> None:
#         pass

#     def __str_to_unix_time(self, date_str:str) -> int:
#         """
#         Convert datetime in string dd-mm-YYYY format to a Unix timestamp.

#         Args:
#             date_str (str): Datetime in string format, specifically formatted as dd-mm-YYYY.

#         Returns:
#             int: Transformed Unix timestamp value.
#         """
#         try:
#             date_obj = datetime.datetime.strptime(date_str, "%d-%m-%Y") # do NOT use `format` keyword in the function, it is wrong. Details; https://stackoverflow.com/questions/49611520/strptime-does-not-convert-string-to-datetime-object-in-python-3-6
#             return int(date_obj.timestamp())
#         except:
#             return None
    
#     def get_prices_from_yahoo(self, company_code, period_1, period_2, interval="1d", last_x_days=""):
#         """
#         Get the price history of a requested company within a specified time range.

#         Parameters:
#             - company_code (str): The code of the requested company.
#             - interval (str): The interval between data points. Default is "1d" (1 day).
#             - last_x_days (str): Specifies the duration of the time range in days, months, or years. 
#                 - Valid options include: '1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max'.
#             - period_1 (str): The start date of the specific time range in 'dd-mm-YYYY' format.
#             - period_2 (str): The end date of the specific time range in 'dd-mm-YYYY' format.

#         Note:
#             - If 'last_x_days' is provided, the time range will be set accordingly.
#             - If 'period_1' and 'period_2' are provided, they will be used to specify the time range.
#             Dates should be in the format 'dd-mm-YYYY'.

#         Returns:
#             pandas DataFrame: DataFrame containing the price history data.
#         """
#         if company_code not in ["USDTRY=X", "EURTRY=X", "GBPTRY=X"]:
#             company_code += ".IS"

#         if last_x_days:
#             # last x days; a valid link https://query1.finance.yahoo.com/v8/finance/chart/EREGL/IS?&interval=1d&range=7d
#             URL = f"https://query1.finance.yahoo.com/v8/finance/chart/{company_code}?&interval={interval}&range={last_x_days}d" # temettu, hisse bolunmesi ve sermaye artirimi bilgilerini icermez
#             print(URL)
#         else:
#             period1 = self.__str_to_unix_time(period_1)
#             period2 = self.__str_to_unix_time(period_2)
#             URL = f"https://query1.finance.yahoo.com/v8/finance/chart/{company_code}?&interval={interval}&period1={period1}&period2={period2}&events=capitalGainldivlsplit&" # time range; a valid link https://query1.finance.yahoo.com/v8/finance/chart/EREGL.IS?&interval=1d&period1=1356991200&period2=1357768800
    
#     ### BURADAN DEVAM: &events=capitalGain%7Cdiv%7Csplit& YA DA &events=capitalGainldivlsplit& eklenince temettu ve bolunme gecmisi de elde ediliyor. Is Yatirim bolunme verilerini dahil etmedigi icin bazi hisselerde (TUPRS gibi) sacma sonuclar aldim.
#         headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"}
#         response = requests.get(url=URL, headers=headers)
#         data = json.loads(response.content)
#         data = data["chart"]["result"][0]
#         # print(data["events"])
#         # print(data["indicators"]["quote"])
#         # Extracting timestamp
#         timestamps_unix = data["timestamp"]
#         # Converting UNIX timestamps to regular time
#         timestamps_regular = [datetime.datetime.fromtimestamp(ts).date() for ts in timestamps_unix]
#         # Extracting indicators
#         indicators = data["indicators"]["quote"][0]
#         # Extracting open, close, high, low, adjclose values
#         open_values = indicators["open"]
#         close_values = indicators["close"]
#         high_values = indicators["high"]
#         low_values = indicators["low"]
#         adjclose_values = data["indicators"]["adjclose"][0]["adjclose"]

#         # Creating a DataFrametiner
#         data_dict = {
#             "TARIH": timestamps_regular,
#             "ACILIS": open_values,
#             "LOW": low_values,
#             "HIGH": high_values,
#             "KAPANIS-yahoo": close_values,
#             "ADJ.KAPANIS-yahoo": adjclose_values
#         }
#         df = pd.DataFrame(data_dict)
#         df["TARIH"] = pd.to_datetime(df["TARIH"])    
#         return df 

# y = YahooFinancePriceDataFetcher().get_prices_from_yahoo(company_code="FROTO", period_1="01-01-2022", period_2="01-01-2024")#"TUPRS", "01-01-2022", "30-09-2023")
# print(y)
# # print(y)https://query1.finance.yahoo.com/v8/finance/chart/TUPRS.IS?&interval=1d&period1=1640984400&period2=1696021200&events=capitalGain%7Cdiv%7Csplit&

import requests, json, datetime
import pandas as pd

class YahooFinancePriceDataFetcher:
    """
    A class for fetching price data from Yahoo Finance API.

    Attributes:
        None

    Methods:
        fetch_prices(company_code, period_1, period_2, interval="1d", last_x_days=""):
            Fetches price history of a requested company within a specified time range.
    """

    def __init__(self) -> None:
        pass

    def __str_to_unix_time(self, date_str:str) -> int:
        """
        Convert datetime in string dd-mm-YYYY format to a Unix timestamp.

        Args:
            date_str (str): Datetime in string format, specifically formatted as dd-mm-YYYY.

        Returns:
            int: Transformed Unix timestamp value.
        """
        try:
            date_obj = datetime.datetime.strptime(date_str, "%d-%m-%Y") # do NOT use `format` keyword in the function, it is wrong. Details; https://stackoverflow.com/questions/49611520/strptime-does-not-convert-string-to-datetime-object-in-python-3-6
            return int(date_obj.timestamp())
        except:
            return None
    
    def get_prices_from_yahoo(self, company_code, period_1, period_2, interval="1d", last_x_days=""):
        """
        Get the price history of a requested company within a specified time range.

        Parameters:
            - company_code (str): The code of the requested company.
            - interval (str): The interval between data points. Default is "1d" (1 day).
            - last_x_days (str): Specifies the duration of the time range in days, months, or years. 
                - Valid options include: '1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max'.
            - period_1 (str): The start date of the specific time range in 'dd-mm-YYYY' format.
            - period_2 (str): The end date of the specific time range in 'dd-mm-YYYY' format.

        Note:
            - If 'last_x_days' is provided, the time range will be set accordingly.
            - If 'period_1' and 'period_2' are provided, they will be used to specify the time range.
            Dates should be in the format 'dd-mm-YYYY'.

        Returns:
            pandas DataFrame: DataFrame containing the price history data.
        """
        if company_code not in ["USDTRY=X", "EURTRY=X", "GBPTRY=X"]:
            company_code += ".IS"

        if last_x_days:
            # last x days; a valid link https://query1.finance.yahoo.com/v8/finance/chart/EREGL/IS?&interval=1d&range=7d
            URL = f"https://query1.finance.yahoo.com/v8/finance/chart/{company_code}?&interval={interval}&range={last_x_days}d" # temettu, hisse bolunmesi ve sermaye artirimi bilgilerini icermez
            print(URL)
        else:
            period1 = self.__str_to_unix_time(period_1)
            period2 = self.__str_to_unix_time(period_2)
            URL = f"https://query1.finance.yahoo.com/v8/finance/chart/{company_code}?&interval={interval}&period1={period1}&period2={period2}&events=capitalGainldivlsplit&" # time range; a valid link https://query1.finance.yahoo.com/v8/finance/chart/EREGL.IS?&interval=1d&period1=1356991200&period2=1357768800
            # URL = f"https://query1.finance.yahoo.com/v8/finance/chart/{company_code}?&interval={interval}&period1={period1}&period2={period2}"
    
    ### BURADAN DEVAM: &events=capitalGain%7Cdiv%7Csplit& YA DA &events=capitalGainldivlsplit& eklenince temettu ve bolunme gecmisi de elde ediliyor. Is Yatirim bolunme verilerini dahil etmedigi icin bazi hisselerde (TUPRS gibi) sacma sonuclar aldim.
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"}
        response = requests.get(url=URL, headers=headers)
        data = json.loads(response.content)
        # 1. Extracting price values
        price_data = data["chart"]["result"][0]
        # Converting UNIX timestamps to regular time
        timestamps_unix = price_data["timestamp"]
        # Extracting timestamp
        timestamps_regular = [datetime.datetime.fromtimestamp(ts).date() for ts in timestamps_unix]
        # Extracting indicators
        indicators = price_data["indicators"]["quote"][0]
        # Extracting open, close, high, low, adjclose values
        open_values = indicators["open"]
        close_values = indicators["close"]
        high_values = indicators["high"]
        low_values = indicators["low"]
        adjclose_values = price_data["indicators"]["adjclose"][0]["adjclose"]

        data_dict = {
            "TARIH": timestamps_regular,
            "ACILIS": open_values,
            "LOW": low_values,
            "HIGH": high_values,
            "KAPANIS-yahoo": close_values,
            "ADJ.KAPANIS-yahoo": adjclose_values
        }
        df = pd.DataFrame(data_dict)
        df["TARIH"] = pd.to_datetime(df["TARIH"])    
        
        try:
            # 2. Extracting dividend, splits and capital gain values
            div_data = data["chart"]["result"][0]["events"]["dividends"]
            # Extracting timestamp
            timestamps_regular = [datetime.datetime.fromtimestamp(int(ts)).date() for ts in div_data.keys()]
            # Extracting the data; datetime_of_div: dividend_amount
            d = {
                datetime.datetime.fromtimestamp(int(timestamp)).date() : div["amount"] for timestamp, div in div_data.items()
            }
            # Mapping dividend values to TEMETTU column using TARIH column
            df["TEMETTU (TL)"] = df["TARIH"].map(d)
            # Filling NaN values with zeros
            df["TEMETTU (TL)"] = df["TEMETTU (TL)"].fillna(0)
            return df
        except:
            df["TEMETTU (TL)"] = 0.
            return df 

# y = YahooFinancePriceDataFetcher().get_prices_from_yahoo(company_code="GARAN", period_1="01-03-2023", period_2="01-04-2023")#"TUPRS", "01-01-2022", "30-09-2023")
# print(y)
