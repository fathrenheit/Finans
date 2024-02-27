import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))) # adding parent dir to python path
import streamlit as st

s = """
<div style="font-family: 'Trebuchet MS', sans-serif;">

Bu uygulama, BIST50 endeksinde yer alan hisseleri genel hatlarıyla analiz etmeyi amaçlar.
1. <b>Hisse Analiz</b> sayfasında, ilgili firma/hissenin:
    - Güncel temel şirket detaylarını,
    - Tarihsel fiyat bilgilerini,
    - Son çeyreklere ait varlık, kaynak ve gelir bilgilerini,
    - Temel ve teknik oranları,
    - Yayınlanmış son KAP haberlerini bulabilirsiniz.
   
2. <b>Getiri Hesaplama</b> sayfası ise ilgili firma için tarihsel verileri kullanarak çalışır. Bu sayfada:
    - Seçilen hisseye geçmişte yapılan tek seferlik yatırımın günümüzdeki durumunu veya düzenli alımlar yapıldığı takdirde hisse performansının günümüzdeki durumunu görebilirsiniz. 
    - Hesaplamalara temettüleri dahil ederek bileşik getirinin etkisini görmeniz de mümkün!

Bu uygulama, şurada yeralan 👉 <a href="https://github.com/fathrenheit/Finans" target="_blank">Finans</a> reposu kullanılarak oluşturulmuştur.

</div>
"""


def intro():
    st.write("# Hisse Analiz Uygulaması'na Hoş geldiniz!👋")
    st.markdown(
        s, 
        unsafe_allow_html=True
    )

def main():
    intro()

if __name__ == "__main__":
    main()