# Finans

[![Finance](https://img.shields.io/badge/Finance-Project-blue.svg)](https://github.com/https://github.com/fathrenheit/Finans/)
[![Python Versiyonu](https://img.shields.io/badge/Python-3.10.6-blue)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Made%20with-Streamlit-FF6F61.svg)](https://streamlit.io/)
[![Lisans: MIT](https://img.shields.io/badge/Lisans-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Bu repo; İş Yatırım, KAP ve Yahoo Finance web sitelerinde yayınlanan verilere erişerek istenilen finansal bilgilere ulaşmayı sağlar.

## Açıklamalar

Bu repo, BIST endekslerinde yer alan şirketlerle ilgili çeşitli verileri toplamayı amaçlayan araçlar içerir. Söz konusu veriler, çoğunlukla herkese açık API'lerden elde edilir (`IsYatirim.py`, `Yahoo.py`); bununla birlikte web kazıma yöntemleri kullanılarak elde edilen veriler de vardır (`KAPScraper.py`). <br>
Ham verilerin eldesi dışında araçlar da mevcuttur. Bunlar; `Rasyolar.py` ve `ReturnCalculator.py` dosyalarıdır. Rasyolar.py ve ReturnCalculator.py, IsYatirim.py ve Yahoo.py'den elde edilen ham verileri kullanarak kullanıcıya daha anlamlı bilgiler sunan araçlardır. <br>
Son olarak, `use_case_using_streamlit` klasörü içerisinde yukarıda bahsedilen araçların Streamlit frameworku ile beraber kullanıldığı bir web uygulaması yer almaktadır.

### Dosyalar

#### `IsYatirim.py`
İş Yatırım Menkul Değerler A.Ş.'ne ait olan [isyatirim.com.tr](https://www.isyatirim.com.tr) web sitesinin herkese açık API'sini kullanarak BIST firmalarına ait çeşitli verileri çeker. Bunlar:
- İlgili firmanın tarihsel fiyat bilgisi
- İlgili firmanın çeyreklik finansal tabloları
- İlgili firmanın sermaye artırımı ve temettü geçmişi
- Yabancı takas oranı değişimi
- Değerli metaller (altın, gümüş, vb.) için tarihsel fiyat bilgisi

#### `Rasyolar.py`
`IsYatirim.py` ile elde edilen finansal tabloları kullanarak ilgili firmanın temel oranlarını hesaplar. Bu oranlar şunlardır:
- Fiyat/Kazanç oranı
- Piyasa değeri/Defter değeri
- Piyasa değeri/Satışlar
- Hisse başı kazanç
- Özsermaye kârlılığı (ROE)
- Aktif kârlılık (ROA)
- Likidite oranları
- Net Satışlar
- Brüt Kâr ve Brüt Kâr Marjı
- Esas Faaliyet Kârı
- Net Faaliyet Kârı
- FAVÖK
- Net Gelir
- Finansal Borçlar
- Net Borç

#### `KAPScraper.py`
Kamu Aydınlatma Platformu'nda ([KAP.org.tr](https://www.kap.org.tr/tr/)) yer alan verileri kazır. Bu veriler:
- Firmalara ait genel bilgiler
- BIST'te yer alan firmaların listesi
- Endeksler ve bu endekslerde yer alan firmaların listesi
- Son 6 aya ait tüm firmalara ait bildirimler
- Herhangi bir firma özelinde geçmişe yönelik bildirimler (tüm bildirimler, finansal raporlar, özel durum açıklamaları vb.)

#### `Yahoo.py`
Yahoo Inc.'ye ait olan [finance.yahoo.com](https://www.finance.yahoo.com) web sitesinin API'sini kullanarak, hem BIST hem de Nasdaq, NYSE gibi endekslerde yer alan firmalara ait tarihsel fiyat verilerini elde eder. 

#### `ReturnCalculator.py`
BIST'teki şirketler için belirlenen tarih aralığında yapılan yatırımın bugünkü değerini Türk Lirası ve Amerikan Doları cinsinden hesaplar. Hesaplama parametreleri şunlardır:

- Tek seferlik yapılan yatırımın bugünkü değeri
- Her ay düzenli alım ile yapılan yatırımın bugünkü değeri
- Temettülerin geri yatırılması seçeneği


### Kurulum

1. Bu repoyu klonlayın: <br>

        $ git clone https://github.com/fathrenheit/Finans.git

2. Bir sanal ortam oluşturun (Virtual environment) ve aktifleştirin: <br>
    Linux ve macOS: <br>
        
        $ python3 -m venv finance-venv
        $ source venv/bin/activate
    
    Windows Powershell:

        PS> python3 -m venv finance-venv
        PS> finance-venv\scripts\activate.ps1

3. Gerekli kütüphaneleri `requirements.txt` dosyasını kullanarak yükleyin: <br>
        
        $ pip install -r requirements.txt

4. Bu aşamadan sonra herhangi bir IDE ya da Python 3.x destekli metin düzenleyici ile kodları çalıştırabilir, düzenleyebilir, kendi projelerinizde kullanabilirsiniz!

`Streamlit` ile geliştirilen web uygulamasının kurulumu için şuradaki [`readme_streamlit.md`](https://github.com/fathrenheit/Finans/blob/main/use_case_streamlit/readme_streamlit.md) talimatları izleyin.
