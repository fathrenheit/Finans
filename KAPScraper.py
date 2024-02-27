from urllib.request import urlopen, Request
from datetime import date, timedelta
from bs4 import BeautifulSoup
import pickle 
import random 
import time
import json
import sys 
import csv 
import io

class KAPHelper:
    """
    KAP scraper için bir yardımcı sınıf olarak tasarlanmıştır.
    A helper for KAP.org.tr scraper.
    
    This class provides helper functions to support scraping data from KAP.org.tr.
    Bu sınıf, KAP.org.tr'den güvenli bir şekilde veri kazımak almak için işlevler sağlar.

    Attributes:
        None

    Methods:
        make_request(url, method="GET"):
            Belirtilen URL'ye bir istek atar ve HTML içeriğini döndürür.
            Makes a request to the specified URL and returns the HTML content.

        parser(url):
            Belirtilen URL'nin HTML içeriğini ayrıştırır ve bir BeautifulSoup nesnesi olarak döndürür.
            Parses the HTML content of the specified URL and returns a BeautifulSoup object.

        firma_listesi() -> dict:
            KAP.org.tr web sitesindeki BIST firmalarını elde eder ve geri verir.
            Retrieves BIST companies from the KAP.org.tr website.

        endeksler() -> dict:
            KAP.org.tr/tr/Endeksler adresindeki endeks listesini, içindeki firmalarla beraber geri verir.
            Returns indexes and companies listed at KAP.org.tr/tr/Endeksler.

        ana_linkler(url:str) -> dict:
            Firmalara ait ilgili KAP sayfasındaki kazınacak ana linkleri geri verir.
            Returns main links to scrape on the relevant KAP page for companies.

        bildirimler(son_x_gun:1, bildirim_tipi: str = "ALL"):
            KAP anasayfasında yayınlanan bildirimleri elde eder ve liste olarak geri verir.
            Fetches all or specific types of notifications from the KAP main page.

        __firmalar_kap_id():
            Firmalara ait unique/benzersiz KAP kimliklerini bulur ve bir pickle nesnesi olarak kaydeder.
            Finds unique KAP IDs for companies and saves them as a pickle object.

        db_entegrasyonu():
            Bu fonksiyon, ana kazıyıcı sınıfına yardımcı olmak amacıyla değil, ileride kullanılması muhtemel SQLite3 veritabanında kullanılmak üzere tablo oluşturur.
            Oluşturulan tablo şu sütunları içerir: firma_hisse_kodu, firma_ismi, firma_kap_id, firma_kap_linki, firma_faaliyet_alani, bist100, bist50, bist30, bist_tem, bist_tem25, bist_katilim.
            This function is designed to create a table for potential future use in an SQLite3 database, rather than to assist the main scraper class.
    """

    user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        ]

    @staticmethod
    def make_request(url, method="GET"):
        """
        Belirtilen URL'ye bir istek atar ve HTML içeriğini döndürür.
        Makes a request to the specified URL and returns the HTML content.

        Args:
            url (str): The URL to make the request to.
            method (str, optional): The HTTP method to use (default is "GET").

        Returns:
            bytes: The HTML content if the request is successful, otherwise None.
        """
        timestamp = int(time.time())
        headers = {"User-Agent":f"{random.choice(KAPHelper.user_agents)} {timestamp}"}
        safe_url = Request(url, headers=headers, method=method)

        try:
            with urlopen(safe_url) as response:
                if response.status == 200:
                    return response.read()
                else:
                    raise Exception(f"İşlem {response.status} kodu ile sonlandırıldı.")
        except Exception as e:
            print(f"Sayfa bilgileri alınamadı. Hata: {e}")
            return None
        
    @staticmethod
    def parser(url):
        """
        Belirtilen URL'nin HTML içeriğini ayrıştırır ve bir BeautifulSoup nesnesi olarak döndürür.
        Parses the HTML content of the specified URL and returns a BeautifulSoup object.

        Args:
            url (str): The URL to parse.

        Returns:
            BeautifulSoup: The parsed HTML content as a BeautifulSoup object.
        """
        html = KAPHelper.make_request(url=url)
        if html is not None:
            soup = BeautifulSoup(html, "html.parser")
            return soup
        else:
            return None

    @staticmethod
    def firma_listesi() -> dict:
        """
        KAP.org.tr web sitesindeki BIST firmalarını elde eder ve geri verir.
        Retrieves BIST companies from the KAP.org.tr website.

        Returns:
            dict: A dictionary containing BIST companies, where keys are company codes and values are tuples of company name and KAP website address.
        """
        url = "https://www.kap.org.tr/tr/bist-sirketler"
        soup = KAPHelper.parser(url=url)
        if soup is not None:
            soup = soup.find_all("a", class_="vcell")
            bist = {}
            for i in range(0, len(soup)-2, 3):
                kod = soup[i].text
                link = soup[i].get("href")
                firma_ismi = soup[i+1].text
                bist[kod] = (firma_ismi, f"https://www.kap.org.tr{link}")
            return bist
        else:
            return None
    
    
    @staticmethod
    def endeksler() -> dict:
        """
        KAP.org.tr/tr/Endeksler adresindeki endeks listesini, içindeki firmalarla beraber geri verir.
        Returns indexes and companies listed at KAP.org.tr/tr/Endeksler.
        
        Returns:
        dict: A dictionary containing BIST indexes and their associated companies.
        """
        url = "https://www.kap.org.tr/tr/Endeksler"
        soup = KAPHelper.parser(url=url)
        endeks_listesi = soup.find_all("a", class_="w-inline-block sub-leftresultbox")
        if endeks_listesi:
            endeks_listesi = [e.find("div", class_="type-normal bold").get_text() for e in endeks_listesi]
            endeksler_dict = {}
            endeksler = soup.select("div[class*=column-type]")
            for e in range(len(endeks_listesi)):
                endeks = endeks_listesi[e]
                firmalar = endeksler[e*2+1].find_all("a", class_="vcell")
                firmalar = [f.get_text() for f in firmalar]
                firmalar = [firmalar[f] for f in range(1, len(firmalar), 3)]
                endeksler_dict[endeks] = firmalar
            return endeksler_dict
        else:
            return {}
            
    @staticmethod
    def ana_linkler(url:str) -> dict:
        """
        Firmalara ait ilgili KAP sayfasındaki kazınacak ana linkleri geri verir.
        Returns main links to scrape on the relevant KAP page for companies.
            
        Args:
            url (str): The URL from which the main links will be scraped.
        Returns:
            dict or None: A dictionary containing the main links for companies, or None if no links are found.
        """        
        soup = KAPHelper.parser(url=url) 
        soup = soup.find("div", class_="w-clearfix tab-block")
        if soup is not None:
            soup = soup.find_all("a") 
            if soup:
                basliklar_ve_linkler = {}
                for i in soup:
                    baslik = i.text.strip()
                    link = i.get("href") if i.get("href").startswith("/tr") else ""
                    if link:
                        basliklar_ve_linkler[baslik] = f"https://www.kap.org.tr{link}"
                return basliklar_ve_linkler
        return {}

    @staticmethod
    def bildirimler(son_x_gun:1, bildirim_tipi: str = "ALL"): # 
        """
        KAP anasayfasinda yayinlanan bildirimleri elde eder ve liste olarak geri verir.
        Fetches all or specific types of notifications from the KAP main page.
        Args:
            son_x_gun (int): Number of days to look back for notifications.
                - valid options are <= 180
            bildirim_tipi (str): Type of notifications to filter. Defaults to "ALL". Any other options must be separated with hyphen icon (-).
                - valid options are; 
                    - ALL
                    - IGS: Bist firmaları, 
                    - DDK: Düzenleyici ve denetleyici kuruluşlar, 
                    - YK: Yatırım kuruluşları
                    - PYS: Portföy Yönetim Şirketleri
                    - DG: Diğer Kap Üyeleri
        Returns:
            List[dict]: List of dictionaries containing information about each notification.
        """
        sirket_tipi = "IGS-DDK"
        if son_x_gun > 180:
            raise ValueError("En cok 6 ay/180 gun oncesine ait bildirimlere bakilabilir.")
        bugun = date.today().strftime("%Y-%m-%d") # Bugünün tarihi fakat str tipinde %Y-m-d formatında
        x_gun_oncesi = (date.today() - timedelta(days=son_x_gun)).strftime("%Y-%m-%d")
        timestamp = int(time.time())
        su_an = str(timestamp)[:9] if len(str(timestamp)) >= 9 else "1234567890"

        if bildirim_tipi=="ALL":
            # Örnek URL: https://www.kap.org.tr/tr/api/disclosures?ts=974262186&fromDate=2023-11-02&toDate=2023-11-02&memberTypes=IGS-DDK
            url = f"https://www.kap.org.tr/tr/api/disclosures?ts={su_an}&fromDate={x_gun_oncesi}&toDate={bugun}&memberTypes={sirket_tipi}"
        else:
            # Örnek URL: "https://www.kap.org.tr/tr/api/disclosures?ts=872311410&disclosureTypes=FR&fromDate=2023-10-17&toDate=2023-11-01&memberTypes=IGS-DDK"
            url = f"https://www.kap.org.tr/tr/api/disclosures?ts={su_an}&disclosureTypes={bildirim_tipi}&fromDate={x_gun_oncesi}&toDate={bugun}&memberTypes={sirket_tipi}"

        response = KAPHelper.make_request(url=url)
        json_data = json.loads(response)
        data_list = []
        tags_to_keep = ["disclosureIndex", "companyName", "stockCodes", "title", "publishDate", "disclosureType"]
        # Mapping of old keys to new keys
        key_mapping = {
            "disclosureIndex": "index",
            "companyName": "firma_ismi",
            "stockCodes": "firma_kodu",
            "title": "baslik",
            "publishDate": "yayin_tarihi",
            "disclosureType": "bildirim_tipi",
        }

        for js in json_data:
            df = js["basic"]
            record = {key_mapping.get(tag, tag): df[tag] for tag in tags_to_keep} #dict.get() metodu swiftteki hata ayiklayan sozluge cok benziyor ya da tam tersi lol .get metodu 1994ten beri varmis
            record["bildirim_linki"] = f"https://www.kap.org.tr/tr/Bildirim/{df['disclosureIndex']}"
            data_list.append(record)
        
        return sorted(data_list, key=lambda x: x["index"], reverse=True)
    
    @staticmethod
    def __firmalar_kap_id():
        """
        Firmalara ait unique/benzersiz KAP kimliklerini bulur ve bir pickle nesnesi olarak kaydeder.
        Bu fonksiyon, bu ya da baska bir class içinde herhangi bir yerde kullanılmamaktadır. Ancak, bu fonksiyon tarafından oluşturulan pickle nesnesi, db_entegrasyonu() fonksiyonu içinde okunarak kullanılmaktadır.
        Bu fonksiyon bulundugu class'in hicbir yerinde kullanilmiyor. Ancak bu fonksiyonun calismasi sonucu olusan pickle objesi, db_entegrasyonu() fonksiyonu icerisinde okunarak kullanilmistir.
  
        Finds unique KAP IDs for companies and saves them as a pickle object.
        This function is not used anywhere in the class. However, the pickle object generated by 
        this function is read and used within the db_entegrasyonu() function.

        Note: Although this function is currently unused, it performs an important task for 
        integrating KAP IDs with a database.
        """
        # This function is currently unused in the codebase.
        # It scans almost ~700 KAP pages to obtain information and then saves the result as a pickle file.
        # If you need to use this functionality in the future, you can uncomment and call it as needed.

        firma_listesi = {key:value[1] for key,value in KAPHelper.firma_listesi().items()} # SISE: 'https://www.kap.org.tr/tr/sirket-bilgileri/ozet/1087-turkiye-sise-ve-cam-fabrikalari-a-s')
        firma_id_dict = {}
        print("VERILER CEKILIYOR...")
        with open("firma_id_pickle", "ab") as file:
            for firma, kap_linki in firma_listesi.items():
                time.sleep(3)
                try:
                    firma_id = KAPHelper.parser(url=kap_linki).select("a.w-inline-block.tab-subpage2")[0].get("ng-click")
                    if len(firma_id) == 0:
                        raise ValueError("Firmaya ait KAP ID bulunamadi.")
                    else:
                        firma_id = firma_id.replace("'", "").split(",")[-1][:-1]
                except ValueError:
                    continue
                firma_id_dict[firma] = firma_id

            pickle.dump(firma_id_dict, file)

    @staticmethod
    def db_entegrasyonu(): #
        """
        Bu fonksiyon, ana kazıyıcı sınıfına yardımcı olmak amacıyla değil, ileride kullanılması muhtemel SQLite3 veritabanında kullanılmak üzere tablo oluşturur.
        Oluşturulan tablo şu sütunları içerir: firma_hisse_kodu, firma_ismi, firma_kap_id, firma_kap_linki, firma_faaliyet_alani, bist100, bist50, bist30, bist_tem, bist_tem25, bist_katilim.
        This function is designed to create a table for potential future use in an SQLite3 database, rather than to assist the main scraper class.
        
        Returns:
            list: A list of dictionaries representing the rows of the database table, with each dictionary containing the values for the corresponding columns.
        """           
        d =  {
        'BIST 100': 'bist100', 
        'BIST 50': 'bist50', 
        'BIST 30': 'bist30', 
        'BIST TEMETTÜ': 'bist_tem', 
        'BIST TEMETTÜ 25': 'bist_tem25', 
        'BIST KATILIM TUM': 'bist_katilim',       
        }
        kp = KAPHelper()
        firmalar = kp.firma_listesi() # firma_hisse_kodu, firma_ismi, firma_kap_linki
        with open("firma_id_pickle", "rb") as idler:
            idler = pickle.load(idler)
        endeksler = {d[endeks]:firmalar for endeks,firmalar in kp.endeksler().items() if endeks in d.keys()}   # bist100, bist50, bist30, bist_tem, bist_tem25, bist_katilim
        db_list = []
        bulunmayanlar = {}
        for firma_hisse_kodu, (firma_ismi, firma_kap_linki) in firmalar.items(): # firmalar.items() -> ('TUPRS', ('TÜPRAŞ-TÜRKİYE PETROL RAFİNERİLERİ A.Ş.', 'https://www.kap.org.tr/tr/sirket-bilgileri/ozet/1105-tupras-turkiye-petrol-rafinerileri-a-s'))
            try:
                f_dict = {
                        'firma_hisse_kodu': firma_hisse_kodu,
                        'firma_ismi': firma_ismi,
                        'firma_kap_linki': firma_kap_linki,
                        'firma_kap_id': idler[firma_hisse_kodu]
                    }
            except:
                bulunmayanlar[firma_hisse_kodu] = firma_ismi
                continue
            
            for k,v in endeksler.items(): # 'BIST100': [firmalar...]
                endeks_ismi = k
                if firma_hisse_kodu in v:
                    endekse_dahil = True
                else:
                    endekse_dahil = False
                f_dict[endeks_ismi] = endekse_dahil

            db_list.append(f_dict)

        print("Su firmalara ait bilgiler pickle dosyasinda bulunamamistir:\n", bulunmayanlar)
        return db_list

class KAP:
    """
    A simple KAP.org.tr scraper
    This class is responsible for performing scraping operations on KAP.org.tr.

    Attributes:
        kap_helper (KAPHelper): An instance of the KAPHelper class.
        firma_listesi (dict): A dictionary containing all companies in BIST.
        firma_kodu (str): The BIST code of the company.
        firma_kap_linki (str): The KAP homepage link of the company.
        firma_ana_linkler (dict): A dictionary containing the main links for the company.
        bildirim_tipleri (dict): A dictionary containing notification types.
        zaman_araligi (dict): A dictionary containing time ranges.

    Methods:
        __init__(firma_kodu): Initializes the KAP class with the given BIST code.
        __list_to_csv(data, num_of_cols): Converts data in list format to CSV format.
        _firma_kap_id(): Returns the unique identifier value of the relevant company in its KAP address.
        ozet_bilgiler(): Gathers summary information for the requested company.
        genel_bilgiler(): Collects the general information of the requested company.
        katilim_finans(): Collects KATILIM finance information from the KAP page of the requested company.
        finansal_bilgiler(): Collects the financial information (Financial Statements) from the KAP page of the requested company.
        bildirimler(bildirim_tipi, zaman_araligi): Collects the notifications/disclosures and their contents published for the requested company.
   
    """
    def __init__(self, firma_kodu) -> None:
        self.kap_helper = KAPHelper() # creating an instance of KAPHelper class.
        self.firma_listesi = self.kap_helper.firma_listesi() # BIST'teki tum firmalar
        self.firma_kodu = firma_kodu # firmanin BIST kodu
        try:
            self.firma_kap_linki = self.firma_listesi[firma_kodu][1] # 0: Firmanin tam ismi, 1: Firmaya ait KAP ana sayfa linki
        except KeyError:
            sys.exit(f"FIRMA KODU HATALI GIRILDI -> {firma_kodu}")
        self.firma_ana_linkler = self.kap_helper.ana_linkler(self.firma_kap_linki)
        # BILDIRIM SORGU EKRANI DEĞİŞKENLERİ
        self.bildirim_tipleri =  {
            "TUM BILDIRIMLER": "ALL",
            "FINANSAL RAPOLAR": "FR",
            "OZEL DURUM AÇIKLAMALARI": "ODA",
            "DUZENLEYİCİ KURUM BILDIRIMLERI": "DUY",
            "DIGER": "DG"
        }
        self.zaman_araligi = {
            "BUGUN": "0",
            "DUN": "1",
            "SON 1 HAFTA": "7",
            "SON 1 AY": "30",
            "SON 3 AY": "90",
            "SON 6 AY": "180",
            "SON 1 YIL": "365",
            "2023": "2023",
            "2022": "2022",
            "2021": "2021",
            "2020": "2020" # ... 
        }
         
    def __list_to_csv(self, data:list, num_of_cols:int):
        """
        Tablo formatındaki veriyi CSV formatına dönüştürür.
        Converts data in list format to CSV format.

        Args:
            data (list): The data to convert to CSV format.
            num_of_cols (int): The number of columns to use for each row in the CSV.

        Returns:
            csv: A CSV file-like object containing the converted data.
        """        
        # Create a file-like object in memory
        output = io.StringIO()  
        writer = csv.writer(output)
        # Split the data into rows based on the given number of columns
        rows = [data[i:i+num_of_cols] for i in range(0, len(data), num_of_cols)]
        # Write the rows to the CSV
        writer.writerows(rows)
        # Get the CSV data as a string
        csv_data = output.getvalue()
        return csv_data

    def _firma_kap_id(self):
        """
        Verilen firmanın KAP web sitesindeki benzersiz/unique kimlik değerini geri verir.
        Returns the unique identifier value of the relevant company in its KAP address.

        Returns:
            str: The unique identifier value of the relevant company in its KAP address.
        """
        firma_kap_id = self.kap_helper.parser(url=self.firma_kap_linki).select("a.w-inline-block.tab-subpage")
        firma_kap_id = [company.attrs["href"] for company in firma_kap_id if company.attrs["href"].startswith("/tr/cgif")][0]
        firma_kap_id = firma_kap_id.split("/")[-1]
        return firma_kap_id
    
    def ozet_bilgiler(self):
        """
        İstenen firmanın özet bilgilerini içeren verileri toplar.
        Bu bilgiler ilgili firmanın KAP sayfasındaki Özet Bilgiler sekmesinden elde edilir.
        Gathers summary information for the requested company.
        This information is obtained from the Summary Information tab on the company's KAP page.

        Returns:
            dict: A dictionary containing summary information for the requested company.
        """
        ozet_bilgiler_soup = self.kap_helper.parser(url=self.firma_ana_linkler["Özet Bilgiler"])
        ozet_bilgiler_soup = ozet_bilgiler_soup.find_all("div", class_="infoColumn")
        ozet_bilgiler_dict = {}
        for i in range(0, len(ozet_bilgiler_soup)-1, 2):
            k = ozet_bilgiler_soup[i].text.strip()
            v = ozet_bilgiler_soup[i+1].text.strip()
            ozet_bilgiler_dict[k] = v
        return ozet_bilgiler_dict
    
    def genel_bilgiler(self):
        """
        İstenen firmanın genel bilgilerini içeren verileri toplar. Bu bilgiler ilgili firmanın KAP sayfasındaki Genel Bilgiler sekmesinden elde edilir.
        Elde edilen bilgiler şu başlıkları içerir:
            [0] İLETİŞİM BİLGİLERİ	
            [1] FAALİYET ALANI VE BAĞIMSIZ DENETİM KURULUŞU BİLGİLERİ	
            [2] PAZAR, ENDEKS VE SERMAYE PİYASASI ARAÇLARI BİLGİLERİ	
            [3] TESCİL VE VERGİ BİLGİLERİ	
            [4] YÖNETİME İLİŞKİN BİLGİLER	
            [5] SERMAYE VE ORTAKLIK YAPISI BİLGİLERİ	
            [6] BAĞLI ORTAKLIKLAR, FİNANSAL DURAN VARLIKLAR İLE FİNANSAL YATIRIMLARA İLİŞKİN BİLGİLER	
            [7] DİĞER HUSUSLAR
        Collects the general information of the requested company.
        This information is obtained from the General Information tab on the relevant company's KAP page.
        
        Returns:
            dict: A dictionary containing the general information of the requested company.
        """

        d = {}
        genel_bilgiler_soup = self.kap_helper.parser(url=self.firma_ana_linkler["Genel Bilgiler"]) # Parsing the url
        genel_bilgiler_blocks = genel_bilgiler_soup.find_all("div", class_="sub-collapseblock") # Toplam 8 adet alt blok var
        # Burada uyguladigim yontem data-bloku icinde daha derine inerek sozluk formatinda bilgileri kazimak; {"baslik":"basligin altinda kalan veriler"}
        for block in genel_bilgiler_blocks:  
            for elem in block.find_all("div"):
                cl = elem.get("class")
                if cl:
                    if "column-type1" in cl:
                        title = elem.text.strip()
                        d[title] = None
                    elif "column-type3" in cl:
                        number_value = elem.text.strip()
                        d[title] = number_value
                    elif "exportClass" in cl:
                        values = elem.find_all(class_="infoRow")
                        table = []
                        for value in values:
                            value_ = value.find_all(class_="infoColumn")
                            number_of_keys = len(value_)
                            if number_of_keys not in table:
                                table.append(number_of_keys)
                            for v in value_:
                                table.append(v.text.strip())
                        d[title] = table
        for k,v in d.items():
            if type(v) == list:
                csv_data = self.__list_to_csv(data=v[1:], num_of_cols=v[0])
                d[k] = csv_data
        return d 
        
    def katilim_finans(self):
        """
        İstenen firmanın KAP sayfasında yer alan katılım finans bilgilerini toplar.
        Collects KATILIM finance information from the KAP page of the requested company.
    
        Returns:
            dict: A dictionary containing the participation finance information of the requested company, only the SUMMARY INFORMATION section.
        """
        katilim_finans_soup = self.kap_helper.parser(url=self.firma_ana_linkler["Katılım Finans"])
        katilim_finans_soup = katilim_finans_soup.find("div", class_="w-container middle-container")
        tablolar = katilim_finans_soup.find_all("div", id="tableArea")[0] # Tablolar
        baslik = [tablo.get_text(strip=True) for tablo in tablolar.find_all("div", class_="vcell")][0] # Ozet Bilgiler
        tablo = tablolar.find_all(class_="sub-collapseblock")[0]
        rows = tablo.find_all("td")
        rows = [row.get_text(strip=True) for row in rows]
        csv_data = self.__list_to_csv(data=rows, num_of_cols=2)
        return {
            baslik: csv_data
        }
    
    def finansal_bilgiler(self):
        """
        İstenen firmanın KAP sayfasında yer alan finansal bilgilerini (Mali tablolar) toplar.
        Collects the financial information (Financial Statements) from the KAP page of the requested company.
        
        Returns:
            dict: A dictionary containing the financial information of the requested company.
        """
        finansal_bilgiler_soup = self.kap_helper.parser(self.firma_ana_linkler["Finansal Bilgiler"])
        finansal_bilgiler_soup = finansal_bilgiler_soup.find(class_="exportClass")
        rows = finansal_bilgiler_soup.select("div.comp-cell-row-div.vtable")
        rows = [row.get_text(strip=True) for row in rows]
        csv_data = self.__list_to_csv(data=rows, num_of_cols=5) # Finansal bilgiler sayfasinda her zaman 5 kolon var
        return {
            "Finansal Bilgiler": csv_data
        }
    
    def bildirimler(self, bildirim_tipi="ALL", zaman_araligi="365"):
        """
        İstenen firmaya ait bildirimleri ve içeriklerini toplar.
        Collects the notifications/disclosures and their contents published for the requested company.
    
        Args:
            bildirim_tipi (str, optional): Type of notifications to filter. Defaults to "ALL".
            zaman_araligi (str, optional): Time range for notifications. Defaults to "365".
        
        Returns:
            List[dict]: A list of dictionaries containing information about each notification.
        Raises:
            ValueError: If the provided notification type or time range is invalid.
        """
        if bildirim_tipi not in self.bildirim_tipleri.values():
            raise ValueError(f"Bildirim tipi yanlış girildi. Doğru kullanım için bakınız: {self.bildirim_tipleri}")
        if zaman_araligi not in self.zaman_araligi.values():
            raise ValueError(f"Zaman aralığı yanlış girildi. Doğru kullanım için bakınız: {self.zaman_araligi}")
        
        firma_kap_id = self._firma_kap_id()
        url = f"https://www.kap.org.tr/tr/FilterSgbf/FILTERSGBF/{firma_kap_id}/{bildirim_tipi}/{zaman_araligi}"
        response = self.kap_helper.make_request(url=url)
        json_data = json.loads(response)
        data_list = []
        tags_to_keep = ["disclosureIndex", "companyName", "stockCodes", "title", "publishDate", "disclosureType"]
        # Mapping of old keys to new keys
        key_mapping = {
            "disclosureIndex": "index",
            "companyName": "firma_ismi",
            "stockCodes": "firma_kodu",
            "title": "baslik",
            "publishDate": "yayin_tarihi",
            "disclosureType": "bildirim_tipi",
        }

        for js in json_data:
            df = js["basic"]
            record = {key_mapping.get(tag, tag): df[tag] for tag in tags_to_keep} #dict.get() metodu swiftteki hata ayiklayan sozluge cok benziyor ya da tam tersi lol .get metodu 1994ten beri varmis
            record["disclosureLink"] = f"https://www.kap.org.tr/tr/Bildirim/{df['disclosureIndex']}"
            data_list.append(record)
        
        return sorted(data_list, key=lambda x: x["index"], reverse=True)