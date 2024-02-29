### Financial Dashboard App

Financial Dashboard uygulamasina hosgeldiniz!
Bu uygulama ana klasorde bulunan `IsYatirim.py`, `Yahoo.py`, `KAPScraper.py`, `Rasyolar.py` ve `ReturnCalculator.py` sciptlerini kullanir ve sade bir arayuz ile kullaniciya BIST50 endeksinde yer alan firmalarla ilgili hisse analizi ve getiri analizi yapabilmesini saglar. `Financial Dashboard` uygualamasi [`streamlit`](https://streamlit.io/) frameworku kullanilarak gelistirilmistir. 

## Buraya gif gelecek...

### Kurulum

1. Bu repoyu klonlayın: <br>

    ```bash
    $ git clone https://github.com/fathrenheit/Finans.git
    ```

2. Bir sanal ortam oluşturun (Virtual environment) ve aktifleştirin: <br>
   - Linux ve macOS: <br>
        
        ```bash
        $ python3 -m venv finance-venv
        $ source venv/bin/activate
        ```
    
   - Windows PowerShell:

        ```powershell
        PS> python3 -m venv finance-venv
        PS> finance-venv\Scripts\Activate.ps1
        ```

3. `use_case_using_streamlit` klasörüne geçiş yapın: <br>

    ```bash
    $ cd ./use_case_using_streamlit/
    ```

4. Gerekli kütüphaneleri `req_streamlit.txt` dosyasını kullanarak yükleyin: <br>
        
    ```bash
    $ pip install -r req_streamlit.txt
    ```

5. Uygulamayı çalıştırın: <br>

    ```bash
    $ streamlit run './Ana sayfa.py'
    ```

### Kullanım

Bu uygulama, yukarıda yazılı olan yönergeler izlendikten sonra yerel makinenizde harici tarayıcıyı kullanarak çalışır. `Streamlit` frameworku üzerine yazılmıştır. Uygulama açıldıktan sonra yan barda `Ana Sayfa`, `Hisse Analiz 📊`, `Getiri Hesaplama 📈`, ve `Hakkında 📋` sayfalarını göreceksiniz.

- `Ana sayfa:` Uygulamanın giriş sayfasıdır.
  
- `Hisse Analiz 📊:` Bu sayfada BIST50 endeksinde yer alan firmalardan birini seçerek `Hesapla` butonuna tıkladığınızda, seçtiğiniz firmanın fiyat, bilanço, gelir tablosu, teknik ve temel rasyolar gibi birçok bilgiyi kullanarak genel hatlarıyla analiz eder; gerekli yerleri tablo ve grafik olarak gösterir.
  
- `Getiri Hesaplama 📈:` Bu sayfada yine BIST50 endeksinde yer alan firmalardan birini seçerek getiri analizini elde edebilirsiniz. Buradaki hesaplama için şu aşamalar izlenir:
    - Firma seçilir.
    - Tarih aralığı seçilir. Tarihler 2015 yılından başlayarak günümüze kadar olan tarihleri kapsamaktadır.
    - Yatırım tipi seçilir. `Tek seferlik yatırım`; geçmişteki herhangi bir tarihte yapılan _tek seferlik_ bir yatırımı, `Her ay düzenli yatırım` ise _her ay yapılan düzenli_ hisse alımlarıyla yapılan yatırımı ifade eder. Düzenli alımlarda hissenin her ayın ilk iş gününde satın alındığı varsayılmıştır.
    - Temettüler ile ne yapılacağı seçilir. Bu parametre ile firmaların size ödediği temettüler ile ne yapacağınızı seçebilirsiniz; hisse geri alımı yaparak bileşik getiri potansiyelini de artırabilirsiniz, gelen temettüleri doğrudan hesabınızda da tutabilirsiniz.
