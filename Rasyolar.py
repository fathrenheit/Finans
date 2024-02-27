from typing import Any
import pandas as pd
from IsYatirim import IsYatirimScraper
from datetime import datetime, timedelta

class Review(object):
    """
    A class for simply reviewing financial data of any given company.

    Attributes:
        company_name (str): The name or ticker symbol of the company.
        year (int): The year for which financial data is to be reviewed.
        is_yatirim_init (IsYatirimScraper): An instance of IsYatirimScraper class for fetching financial data.
        financial_statement (tuple): A tuple containing financial statements as annually and quarterly.
        number_of_shares (float): The total number of shares of the company.
        current_price (float): The current price of the company's stock.
        market_value (float): The market value of the company calculated as number_of_shares * current_price.
        daily_price_change_rate (float): The daily percentage change in the company's stock price.
        cash_initial (float): The amount of cash at the beginning of the period.
        working_capital (float): The working capital of the company calculated as current assets - current liabilities.

    Methods:
        __init__(company_name, year): 
            Initializes the Review object.
        __initializer():
            Fetches balance-sheet as quarterly and annually.
        __setter(): 
            Sets initial values including current price, number of shares, cash initial, etc.
        price_to_earning_ratio(): 
            Calculates and returns the Price-to-Earnings (P/E) ratio.
        price_to_book_ratio(): 
            Calculates and returns the Price-to-Book (P/B) ratio.
        price_to_sales_ratio(): 
            Calculates and returns the Price-to-Sales (P/S) ratio.
        earning_per_share(): 
            Calculates and returns the earnings per share (EPS).
        return_on_equity(): 
            Calculates and returns the Return-On-Equity (ROE) ratio.
        return_on_assets(): 
            Calculates and returns the Return-On-Assets (ROA) ratio.
        debt_to_equity(): 
            Calculates and returns the Debt-to-Equity (D/E) ratio.
        liquidity(): 
            Calculates and returns liquidity ratios.
        net_sales(): 
            Returns the net sales amount quarterly.
        gross_profit_gpm(): 
            Calculates and returns gross profit and gross profit margin.
        operating_income(): 
            Calculates and returns operating income.
        net_operating_income(): 
            Returns the net operating income.
        ebitda():
            Calculates and returns Earnings Before Interest, Taxes, Depreciation, and Amortization (EBITDA).
        net_income():
            Returns the net income quarterly.
        financial_debt():
            Calculates and returns the sum of financial debts.
        net_debt():
            Calculates and returns the net debt.
    """

    def __init__(self, company_name, year) -> None:
        """
        Initializes the Review object.

        Args:
            company_name (str): The name or ticker symbol of the company.
            year (int): The year for which financial data is to be reviewed.
        """
        self.company_name = company_name
        self.is_yatirim_init = IsYatirimScraper() # initializes IsYatirimScraper
        self.year = year
        self.financial_statement = self.__initializer()
        self.number_of_shares = self.__setter()["number_of_shares"]
        self.current_price = self.__setter()["current_price"]
        self.market_value = self.number_of_shares * self.current_price
        self.daily_price_change_rate = self.__setter()["daily_price_change_rate"]
        self.cash_initial = self.__setter()["cash_initial"]
        self.working_capital = self.__setter()["working_capital"]
    
    def __initializer(self):
        """
        Fetches balance-sheet as quarterly and annually.
        Financial-statements consist of:
        (1) Balance-sheet, 
        (2) Income-statement, 
        (3) Cash Flow
        """
        is_yatirim = self.is_yatirim_init
        fs_ann = is_yatirim.get_is_yatirim_financial_data(ticker=self.company_name, current_year=self.year, cumulative=True)
        fs_qua = is_yatirim.get_is_yatirim_financial_data(ticker=self.company_name, current_year=self.year, cumulative=False)
        fs_ann["ACIKLAMA"] = fs_ann["ACIKLAMA"].apply(lambda x:x.strip())
        fs_qua["ACIKLAMA"] = fs_qua["ACIKLAMA"].apply(lambda x:x.strip())
        return fs_ann, fs_qua # financial-statements as annually and quarterly

    def __setter(self):
        """
        Sets some initial values.
        """
        # Gets current price of the requested company
        price_history = self.is_yatirim_init.get_is_yatirim_price_data(
            ticker=self.company_name, 
            start_date=(datetime.now() - timedelta(days=365 * 2)).strftime("%d-%m-%Y"),
            end_date=(datetime.now() + timedelta(days=1)).strftime("%d-%m-%Y")
            ).reset_index(drop=True)
        # Gets cumulative financial statement of the requested company
        financials = self.financial_statement[0] # 0; annual, 1; quarter
        # Current price of the company
        current_price = price_history["KAPANIS FIYATI (TL)"].iloc[-1]
        # Daily price change by % of the company
        price_change_rate = round((100 * current_price / price_history["KAPANIS FIYATI (TL)"].iloc[-2]) - 100, 2)
        # Total number of shares of the requested company
        number_of_shares = financials[financials["ACIKLAMA"]=="Ödenmiş Sermaye"].reset_index(drop=True).iloc[0,1] # The most up to date value
        # Amount of cash at the beginnig of the period
        cash_initial = financials[financials["ACIKLAMA"]=="Dönem Başı Nakit Değerler"].reset_index(drop=True).iloc[0,1]
        # Working capital of the company (current assets - current liabilities) # isletme sermayesi
        working_capital = financials[financials["ACIKLAMA"]=="Dönen Varlıklar"].reset_index(drop=True).iloc[0, 1] - financials[financials["ACIKLAMA"]=="Kısa Vadeli Yükümlülükler"].reset_index(drop=True).iloc[0, 1]
        # Controlling whether the year is the same as the latest year on financial sheet
        latest_year = [int(year.split("/")[1]) for year in financials.columns[1:]][0]
        return {
            "current_price":current_price,
            "number_of_shares":number_of_shares,
            "cash_initial":cash_initial,
            "daily_price_change_rate":price_change_rate,
            "working_capital":working_capital,
            "year":latest_year
            }

    def price_to_earning_ratio(self):
        """
        F/K oranını çeyreklik olarak hesaplar ve geri verir.
        Calculates the Price-to-Earnings (P/E) ratio using the price and earnings for the last quarters, and returns it.
        Formula:
            P/E = Price / Earnings-per-Share
            Earnings-per-Share = Total Earnings for the last 4 quarters / number of shares

        Returns:
            float: The calculated P/E ratio.
        """
        fs_qua = self.financial_statement[1]
        earnings = fs_qua[fs_qua["ACIKLAMA"]=="Ana Ortaklık Payları"].reset_index(drop=True)
        total_earnings = sum(earnings.iloc[0, 1:5])
        eps = total_earnings / self.number_of_shares
        return round(self.current_price / eps, 2)

    def price_to_book_ratio(self):
        """
        PD/DD oranını hesaplar ve geri verir.
        Returns the Price-to-Book (P/B) Value ratio.
        Formula:
            P/B (or M/B) = Market Value / Book Value
            Market Value = Price of the stock * Number of Shares
            Book Value = Assets - Liabilities

        Returns:
            float: The calculated P/B ratio.
        """
        fs_ann = self.financial_statement[0]
        book_value = fs_ann[fs_ann["ACIKLAMA"]=="Ana Ortaklığa Ait Özkaynaklar"].reset_index(drop=True).iloc[0,1]
        return round(self.market_value / book_value, 2)
    
    def price_to_sales_ratio(self):
        """
        PD/S oranını çeyreklik olarak hesaplar ve geri verir.
        Returns the Price-to-Sales (P/S) ratio.
        Formula:
            P/S = Market Value / Total Sales

        Returns:
            float: The calculated P/S ratio.
        """
        fs_qua = self.financial_statement[1]
        total_sales = fs_qua[fs_qua["ACIKLAMA"]=="Satış Gelirleri"].reset_index(drop=True)
        return {
            "last quarter":round(self.market_value/total_sales.iloc[0,1], 3),
            "annually":round(self.market_value / sum(total_sales.iloc[0, 1:5]), 3)
        }
    
    def earning_per_share(self):
        """
        Hisse başı kazancı (HBK) çeyreklik olarak hesaplar ve geri verir.
        Returns the earnings per share (EPS).
        Formula:
            EPS = (Net Income - Preferred Dividends) / Number of Shares

        Returns:
            float: The calculated EPS.
        """
        fs_qua = self.financial_statement[1]
        net_income = fs_qua[fs_qua["ACIKLAMA"]=="Ana Ortaklık Payları"].reset_index(drop=True)
               # Initialize the ebitda df
    
        eps = pd.DataFrame(index=[0], columns=fs_qua.columns)
        eps.iloc[0, 0] = "Hisse Başı Kazanç (₺)"
        eps.iloc[0, 1:] = eps.iloc[0, 1:].astype("float64")
        eps.iloc[0, 1:] = round(net_income.iloc[0, 1:] / self.number_of_shares, 3)
        return eps 

    def return_on_equity(self):
        """
        Özsermaye karlılığını hesaplar ve geri verir.
        Returns the Return-On-Equity (ROE) ratio.
        Formula:
            ROE = Net Income (Annually) / Average Total Equity

        Returns:
            float: The calculated ROE.
        """
        fs_ann, fs_qua = self.financial_statement[0], self.financial_statement[1]
        net_income = fs_qua[fs_qua["ACIKLAMA"]=="Ana Ortaklık Payları"].reset_index(drop=True)
        equity = fs_ann[fs_ann["ACIKLAMA"]=="Ana Ortaklığa Ait Özkaynaklar"].reset_index(drop=True)
        
        roe = pd.DataFrame(columns=net_income.columns)
        roe.loc[0, "ACIKLAMA"] = "Ana Ortaklık Payları (TTM)"
        roe.loc[1, "ACIKLAMA"] = "Ana Ortaklığa Ait Ortalama Özkaynaklar"
        roe.loc[2, "ACIKLAMA"] = "Özsermaye Kârlılığı (ROE) %"
        for i in range(1, len(net_income.columns)-4):
            roe.iloc[0, i] = net_income.iloc[0, i:i+4].sum()
            roe.iloc[1, i] = equity.iloc[0, i]/2 + equity.iloc[0, i+4]/2 
        
        roe.iloc[2, 1:] = 100 * roe.iloc[0, 1:] / roe.iloc[1, 1:]
        roe.iloc[2, 1:] = roe.iloc[2, 1:].astype("float64").round(3)
        roe.dropna(axis=1, inplace=True)
        return roe
    
    def return_on_assets(self):
        """
        Aktif karlılığı hesaplar ve geri verir.
        Returns the Return-On-Assets (ROA) ratio.
        Formula:
            ROA = Net Income (Annually) / Average Assets

        Returns:
            float: The calculated ROA.
        """
        fs_ann, fs_qua = self.financial_statement[0], self.financial_statement[1]
        net_income = fs_qua[fs_qua["ACIKLAMA"]=="Ana Ortaklık Payları"].reset_index(drop=True)
        assets = fs_ann[fs_ann["ACIKLAMA"]=="TOPLAM VARLIKLAR"].reset_index(drop=True)
        
        roa = pd.DataFrame(columns=net_income.columns)
        roa.loc[0, "ACIKLAMA"] = "Ana Ortaklık Payları (TTM)"
        roa.loc[1, "ACIKLAMA"] = "Toplam Varlıklar"
        roa.loc[2, "ACIKLAMA"] = "Aktif Kârlılık (ROA) %"
        for i in range(1, len(net_income.columns)-4):
            roa.iloc[0, i] = net_income.iloc[0, i:i+4].sum()
            roa.iloc[1, i] = assets.iloc[0, i]/2 + assets.iloc[0, i+4]/2

        roa.iloc[2, 1:] = 100 * roa.iloc[0, 1:] / roa.iloc[1, 1:]
        roa.dropna(axis=1, inplace=True)
        return roa
            
    def debt_to_equity(self):
        """
        Borç / özsermaye oranını hesaplar ve geri verir.
        Returns the Debt-to-Equity (D/E) ratio.
        Formula:
            D/E = Total Financial Debt / Total Shareholder's Equity

        Returns:
            float: The calculated D/E ratio.
        """
        
        fs_ann = self.financial_statement[0]
        financial_debts = fs_ann[fs_ann["ACIKLAMA"]=="Finansal Borçlar"].reset_index(drop=True)
        equity = fs_ann[fs_ann["ACIKLAMA"]=="Ana Ortaklığa Ait Özkaynaklar"].reset_index(drop=True)
        
        dte = pd.DataFrame(columns=financial_debts.columns)
        dte.loc[0, "ACIKLAMA"] = "Toplam Finansal Borçlar"
        dte.loc[1, "ACIKLAMA"] = "Ana Ortaklığa Ait Özkaynaklar"
        dte.loc[2, "ACIKLAMA"] = "Borçluluk/Özkaynak Oranı %"
        
        dte.iloc[0, 1:] = financial_debts.iloc[0, 1:] + financial_debts.iloc[1, 1:]
        dte.iloc[1, 1:] = equity.iloc[0, 1:]
        dte.iloc[2, 1:] = 100 * dte.iloc[0, 1:] / dte.iloc[1, 1:]
        dte.dropna(axis=1, inplace=True)
        return dte
    
    def liquidty(self): 
        """
        Likidite oranlarını; Cari Oran, Likidite Oranı ve Nakit Oranını hesaplar ve geri verir.
        Returns liquidity ratios: Current-Ratio, Quick-Ratio, and Cash-Ratio.
        Formulas:
            Current Ratio = Current Assets / Current Liabilities
            Quick Ratio = Liquid Assets / Current Liabilities = (Current Assets - Inventories) / Current Liabilities
            Cash Ratio = (Cash and Cash Equivalent + Short Term Investments) / Current Liabilities

        Returns:
            dict: A dictionary containing the calculated liquidity ratios.
        """
        fs_ann = self.financial_statement[0]
        current_liabilities = fs_ann[fs_ann["ACIKLAMA"]=="Kısa Vadeli Yükümlülükler"].reset_index(drop=True).iloc[0, 1] # cari yukumlulukler ya da diger ismiyle kisa vadeli yukumlulukler
        # Current-Ratio
        current_assets = fs_ann[fs_ann["ACIKLAMA"]=="Dönen Varlıklar"].reset_index(drop=True).iloc[0, 1] # cari aktifler ya da diger ismiyle donen varliklar
        current_ratio = current_assets / current_liabilities
        # Quick-Ratio
        inventories = fs_ann[fs_ann["ACIKLAMA"]=="Stoklar"].reset_index(drop=True).iloc[0, 1] # stoklar
        quick_ratio = (current_assets - inventories) / current_liabilities
        # Cash-Ratio
        cash_equivalents = fs_ann[fs_ann["ACIKLAMA"]=="Nakit ve Nakit Benzerleri"].reset_index(drop=True).iloc[0, 1]
        securities = fs_ann[fs_ann["ACIKLAMA"]=="Finansal Yatırımlar"].reset_index(drop=True).iloc[0, 1] # menkul kiymetler ya da diger ismiyle finansal yatirimlar
        cash_ratio = (cash_equivalents + securities) / current_liabilities
        return {
            "current ratio": round(current_ratio, 2),
            "quick ratio": round(quick_ratio, 2),
            "cash ratio": round(cash_ratio, 2) 
        }
    
    def net_sales(self):
        """
        Net satış miktarını çeyreklik olarak geri verir.
        Returns the net sales amount quarterly.

        Returns:
            pd.DataFrame: A pandas DataFrame contains Net-Sales as quarterly.
        """
        fs_qua = self.financial_statement[1]
        net_sales = fs_qua[fs_qua["ACIKLAMA"]=="Satış Gelirleri"].reset_index(drop=True)
        return net_sales 
        
    def gross_profit_gpm(self):
        """
        Brüt kar ve brüt kar marjını çeyreklik olarak hesaplar ve geri verir.
        Calculates gross profit and gross profit margin.
        
        Formula:
        Gross Profit = Net Sales - Cost of Goods Sold
        Gross Profit Margin = (Net Sales - Cost of Goods Sold) / Net Sales
        
        Returns:
            pd.DataFrame: A pandas DataFrame containing gross profit and gross profit margin.
        """
        fs_qua = self.financial_statement[1]
        gross_profit = fs_qua[fs_qua["ACIKLAMA"] == "BRÜT KAR (ZARAR)"]
        net_sales = fs_qua[fs_qua["ACIKLAMA"] == "Satış Gelirleri"]

        # Creating the DataFrame 'gp'
        gp = pd.DataFrame(index=[0, 1, 2], columns=fs_qua.columns)
        gp["ACIKLAMA"] = ["BRUT KAR", "NET SATISLAR", "BRUT KAR MARJI (%)"]

        gp.iloc[0, 1:] = gross_profit.iloc[0, 1:]
        gp.iloc[1, 1:] = net_sales.iloc[0, 1:]
        gp.iloc[2, 1:] = 100 * gross_profit.iloc[0, 1:] / net_sales.iloc[0, 1:]
        gp.iloc[2, 1:] = round(gp.iloc[2, 1:].astype("float64"), 2)
        
        return gp
        
    def operating_income(self):
        """
        Esas Faaliyet Karını çeyreklik olarak hesaplar ve geri verir.
        Calculates operating income.
        
        Formula:
        Operating Income = Gross Profit - Operating Expenses - Depreciation - Amortization
        
        Returns:
            float: The calculated operating income.
        """
        fs_qua = self.financial_statement[1]        
        operation_income = fs_qua[fs_qua["ACIKLAMA"]=="FAALİYET KARI (ZARARI)"].reset_index(drop=True)
        return operation_income 
    
    def net_operating_income(self):
        """
        Net Faaliyet Karını çeyreklik olarak hesaplar ve geri verir.
        Returns the net operating income, which represents the profit generated from the core business operations. 
        Formula:
        Net Operating Income = Total Revenue - Total Expenses 

        Returns:
            float: The calculated net operating income.
        """
        fs_qua = self.financial_statement[1]
        net_operating_income = fs_qua[fs_qua["ACIKLAMA"]=="Net Faaliyet Kar/Zararı"].reset_index(drop=True)
        return net_operating_income
    
    def ebitda(self):
        """
        FAVÖK (Faiz, Amortisman Vergi Öncesi Kazanç) değerini çeyreklik olarak hesaplar ve geri verir.
        Returns EBITDA (Earnings Before Interest, Taxes, Depreciation, and Amortization), an alternate measure of profitability to net income.
        
        Formula:
        EBITDA = Operating Income + Depreciation & Amortization 
        or
        EBITDA = Net Income + Taxes + Interest Expense + Depreciation & Amortization
        EBITDA Margin (%) = EBITDA / Total Revenue

        Returns:
            float: The calculated EBITDA.
        """
        # Getting the quarterly financial statement
        fs_qua = self.financial_statement[1]
        # Getting the relevant data
        operation_income = fs_qua[fs_qua["ACIKLAMA"]=="Net Faaliyet Kar/Zararı"].reset_index(drop=True)
        dep_amor = fs_qua[fs_qua["ACIKLAMA"]=="Amortisman Giderleri"].reset_index(drop=True)
        total_revenue = fs_qua[fs_qua["ACIKLAMA"]=="Satış Gelirleri"].reset_index(drop=True)
        # Initialize the ebitda df
        ebitda = pd.DataFrame(index=[0, 1, 2], columns=fs_qua.columns)
        ebitda["ACIKLAMA"] = ["FAVÖK", "SATIS GELIRLERI", "FAVÖK MARJI (%)"]
        ebitda.iloc[0, 1:] = operation_income.iloc[0, 1:] + dep_amor.iloc[0, 1:]
        ebitda.iloc[1, 1:] = total_revenue.iloc[0, 1:]
        ebitda.iloc[2, 1:] = 100 * (operation_income.iloc[0, 1:] + dep_amor.iloc[0, 1:]) / total_revenue.iloc[0, 1:]
        ebitda.iloc[2, 1:] = round(ebitda.iloc[2, 1:].astype("float64"), 2)
        return ebitda
                
    def net_income(self): # ..............
        """
        Net Dönem Kârını ve kâr marjını çeyreklik olarak hesaplar ve geri verir.
        Returns Net Profit quarterly.
        
        Formula:
            Net Income = Total Revenue - Total Expenses

        Returns:
            pd.DatFrame: A pandas DataFrame containing net income values.
        """
        fs_qua = self.financial_statement[1]
        net_income = fs_qua[fs_qua["ACIKLAMA"]=="Ana Ortaklık Payları"].reset_index(drop=True)
        total_revenue = fs_qua[fs_qua["ACIKLAMA"]=="Satış Gelirleri"].reset_index(drop=True)
        # Creating a new df
        net_income_df = pd.DataFrame(index = [0, 1], columns=fs_qua.columns)
        net_income_df["ACIKLAMA"] = ["Ana Ortaklık Paylarına Ait Net Dönem Karı", "Net Kar Marji (%)"]
        net_income_df.iloc[0, 1:] = net_income.iloc[0, 1:]
        net_income_df.iloc[1, 1:] = 100 * net_income.iloc[0, 1:] / total_revenue.iloc[0, 1:]
        net_income_df.iloc[1, 1:] = round(net_income_df.iloc[1, 1:].astype("float64"), 2)

        return net_income_df
    
    def financial_debt(self):
        """
        Finansal borç toplamını hesaplar ve geri verir.
        Returns the sum of financial debts (TR: FINANSAL BORCLAR).
    
        Formula:
            Financial Debts = Short Term Financial Debts + Long Term Financial Debts

        Returns:
            float: The total sum of financial debts.
        """
        fs_ann = self.financial_statement[0]
        financial_debts = fs_ann[fs_ann["ACIKLAMA"]=="Finansal Borçlar"].reset_index(drop=True)
        return financial_debts.groupby("ACIKLAMA", as_index=False).sum() # financial_debts.iloc[0, 1] + financial_debts.iloc[1, 1] 
    
    def net_debt(self):
        """
        Net borcu hesaplar ve geri verir.
        Returns the net debt (TR: NET BORC).

        Formula:
            Net Debt = Financial Debts + Cash and Cash Equivalent + Financial Investments

        Returns:
            pd.DataFrame: A pandas DataFrame containing the net debt value.
        """
        # Getting the annual financial statement
        fs_ann = self.financial_statement[0]
        # Cash equivalents
        cash_equivalents = fs_ann[fs_ann["ACIKLAMA"]=="Nakit ve Nakit Benzerleri"].reset_index(drop=True)
        # Financial investments
        financial_investments = fs_ann[fs_ann["ACIKLAMA"]=="Finansal Yatırımlar"].reset_index(drop=True).iloc[0,:]
        # Financial debts
        financial_debts = self.financial_debt()
        # Net Debt = Financial debts - Cash Equivalents - Financial Investments
        values = (financial_debts.iloc[0,1:] - cash_equivalents.iloc[0,1:] - financial_investments.iloc[1:])
        net_debt_df = pd.DataFrame(columns=fs_ann.columns)
        net_debt_df.loc[0, "ACIKLAMA"] = "Net Borç"
        net_debt_df.iloc[0, 1:] = values
        return net_debt_df