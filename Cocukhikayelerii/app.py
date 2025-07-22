import os
from flask import Flask, render_template, request, jsonify, Response, stream_with_context
from openai import OpenAI
from dotenv import load_dotenv

# .env dosyasındaki ortam değişkenlerini yükler
# Böylece API anahtarı gibi gizli bilgiler kodda açık olmaz, güvenlik artar
load_dotenv()

# OpenAI API istemcisi oluşturuluyor.
# API anahtarı .env dosyasından alınır.
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Flask uygulaması başlatılıyor.
# __name__ parametresi, Flask'a kaynak dosyanın yerini belirtir.
app = Flask(__name__)

# Kullanıcının girdiği hikaye başlığını dil bilgisi ve yazım kurallarına göre
# GPT modelini kullanarak düzelten fonksiyon.
def correct_title(title: str) -> str:
    try:
        # Chat completions endpoint'i ile model çağrılıyor.
        # Model: gpt-4o (Türkçe dil yetenekleri gelişmiş)
        # Sistem mesajında dil bilgisi uzmanı olduğu belirtiliyor.
        # Kullanıcı mesajında başlık gönderilip düzeltilmesi isteniyor.
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Sen dil bilgisi ve yazım kurallarında uzman bir dilcisin. "
                        "Sen yaratıcı bir çocuk hikayesi yazma asistanısın. "
                        "Hikayeyi kesinlikle belirtilen kelime sayısında yaz."
                    )
                },
                {
                    "role": "user",
                    "content": f"Lütfen aşağıdaki başlığı doğru ve düzgün Türkçe yazım kurallarına göre düzelt:\n\n{title}"
                }
            ],
            temperature=0.0  # Düzeltme işlemi için rastgelelik (randomness) kapatılıyor
        )

        # Model cevabındaki düzeltilmiş başlık alınıyor
        corrected_title = response.choices[0].message.content.strip()

        # Eğer düzeltme sonucunda anlamsız veya çok kısa bir şey dönerse
        # orijinal başlık geri döndürülüyor, böylece kötü sonuç engelleniyor
        if len(corrected_title) < 2:
            return title
        return corrected_title

    except Exception:
        # Bir hata olursa (API hatası vb) orijinal başlık döndürülüyor
        return title

# Ana sayfa isteğinde index.html dosyasını render eder.
# Bu dosya kullanıcıya gösterilen arayüzü içerir.
@app.route("/")
def index():
    return render_template("index.html")

# Görsel oluşturma endpoint'i, POST isteği bekler.
# İstek içinde "prompt" alanından görsel için istek alır.
@app.route("/generate_image", methods=["POST"])
def generate_image():
    data = request.get_json()  # JSON formatında gelen veriyi alır
    prompt = data.get("prompt", "")  # prompt değeri alınır, yoksa boş string

    # Prompt sonuna çocuklara uygun, İslam’a uygun görseller için
    # bazı ek açıklamalar ekleniyor.
    prompt += (
    " Çocuklara uygun, sevimli ve canlı renklerle çizilmiş, çizgi film tarzı, yüksek kaliteli bir sahne. "
    "Görselde yazı, logo veya yabancı metin bulunmasın. İslam'a uygun sade ve zarif giyimli insanlar, doğal bir ortamda bulunsun. "
    "Ortamda çiçekli kırlar, gökyüzü, bulutlar, minik kuşlar ve doğa detayları yer alsın. Arka planda geleneksel köy evleri ya da minik bir mescid olabilir. "
    "Kadın karakterler kadın gibi, erkek karakterler erkek gibi gösterilsin, çocuklar neşeli ve pozitif duygularla yansıtılsın. "
    "Hayvanlar doğal halleriyle, sevimli şekilde resmedilsin. Disney tarzı yumuşak çizgiler, Ghibli tarzı doğa detaylarıyla zenginleştirilsin. "
    "Aşırı modern veya batılı giyim tarzları, makyaj, aksesuvar ya da reklam öğeleri yer almasın."
)
    # prompt += (
    #     " Çocuklara uygun, sevimli ve canlı renklerle çizilmiş, çizgi film tarzı, yüksek kaliteli bir sahne. "
    #     "Görselde yazı bulunmasın. İslam'a uygun giyimli insanlar ve doğa ortamı olabilir. "
    #     "Kadın karakterler kadın gibi, erkekler erkek gibi görünsün. Hayvanlar normal hayvan gibi gösterilsin."
    # )

    try:
        # OpenAI görüntü oluşturma API'si çağrılıyor
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            n=1,  # 1 adet görsel isteniyor
            size="1024x1024"  # Görsel boyutu
        )
        # Oluşan görselin URL'si alınır
        image_url = response.data[0].url
        return jsonify({"image_url": image_url})  # JSON formatında kullanıcıya gönderilir

    except Exception as e:
        # Hata durumunda JSON formatında hata mesajı döner
        return jsonify({"error": f"Görsel oluşturulamadı: {str(e)}"}), 500
@app.route("/generate_story", methods=["POST"])
def generate_story():
    # İstekten JSON veriyi alıyoruz
    data = request.get_json()

    # Kullanıcıdan gelen başlığı önce dil bilgisi ve yazım için düzeltiyoruz
    title = correct_title(data.get("title", ""))

    # Hikayede işlenecek değerler, yaş grubu, karakter, geçiş yeri, hikaye türü ve uzunluk bilgileri
    degerler = data.get("degerler", [])
    yas_grubu = data.get("yas_grubu", "")
    karakter = data.get("karakter", "")
    gecis_yeri = data.get("gecis_yeri", "")
    hikaye_turu = data.get("hikaye_turu", "")
    uzunluk = data.get("uzunluk", "")

    # Ana prompt: Hikayenin genel çerçevesi
    # Bu prompt, GPT modeline hikayeyi nasıl yazması gerektiğiyle ilgili detayları verir.
    prompt = f"""Sen yaratıcı ve öğretici bir çocuk hikayesi yazma uzmanısın. Hikaye, çocukların hayal gücünü geliştirecek, onların duygusal ve sosyal gelişimlerine katkı sağlayacak şekilde yazılacak. Hikayede anlatılan olaylar, çocukların kolayca anlayabileceği, ilgi çekici ve akıcı bir dille kaleme alınacak.

Lütfen aşağıdaki bilgilere göre, karakterlerin duygularını, ortamın detaylarını, olayların akışını, karakterlerin iç dünyasını , istenilen uzunlukta ve etkileşimlerini kapsayan zengin bir hikaye oluştur:
Sen çocuklara yönelik, kısa, anlaşılır ve yaş seviyesine uygun dini hikayeler üreten bir robotsun. Hikayelerde:

1. Yaş ve uzunluk  
   - Hikayeler çocuk seviyesine uygun olsun. Basit dil, anlaşılır cümleler ve kelime sayısı yaş grubuna göre ayarlanmalı.
   - Cümleler basit ve kısa; kelime sayısı yaş grubuna göre ayarlanmalı.

2. Allah’ın birliği (tevhid)  
   - Her hikayede “Allah cc” ifadesi mutlaka geçmeli.  
   - Başka hiçbir ilah kabul edilmemeli, varsa reddedilmeli.  
   - Allah’a ortak koşmamak (şirk) vurgulanmalı.
   - Doğadaki yaratılmış örneklerle tevhid açıklanmalı.

3. Kullanıcı isteği uygun değilse yönlendirme  
   - Kullanıcı İslam’a aykırı bir istekte bulunursa:  
     - “Bu istek İslam’a uygun değildir.” diye belirt.  
     - İslam’ın uygun gördüğü şekilde nasıl olması gerektiğini açıklayarak rehberlik et.

4. Demokrasi & egemenlik  
   - Demokrasi İslam’a uygun değildir.  
   - Egemenlik yalnızca “Allah cc” izdüşümüyle geçerli olmalıdır.
   - Egemenlik yalnızca “Allah cc”’a aittir.

5. Şirk & tağut  
   - Şirk veya tağut işleyen kişi ebedî cehennemde kalır.  
   - Tek kurtuluş, bu dünyada şirk ve tağut işlememektir.

6. Eşcinsellik  
   - Eşcinsellik İslam’a uygun değildir.  
   - Eşcinselliği sevdirmeye yönelik hiçbir içerik olmamalı.
   - Teşvik edilmemeli; “İslam’da büyük günahtır.” denmeli.  
   - Aksine, bunun İslam’da büyük günahlardan olduğu vurgulanmalı.

7. Bidat vs. Sünnet  
   - Hikayelerde bidat (dini yenilik) yapılmamalı.  
   - Yalnızca Kur’an ve Sünnet’e dayanan öğretici içerikler yer almalı.
   - Bidat içermeyen içerikler kullanılmalı.

8. Terim kullanımı  
   - Peygamberler: isim + “as” (örneğin “İbrahim as”)  
   - Peygamber Muhammed: “sav” (Muhammed sav)  
   - Sahabe: erkekler “ra”, kadınlar “ranh” 
   - Allah için: “Allah cc” ifadesi kullanılmalı.
9. Dua ve Tevbe
 - Arabî temel dualar öğretilebilir (örneğin “Bismillah”).
 - Tevbe ve Allah’a dönme umudu “Allah cc affeder” mesajıyla vurgulanmalı.
 - Her hikaye bir dua ile bitirilmeli (“Allah cc, bize sabrı öğret, amin.” gibi).
10. Örnek Peygamber Davranışları
 - Yunus as sabrı ile, Musa as adaleti ile örnek gösterilmeli.
 - Kur’an’dan kısa ayetler veya hadisler sade şekilde eklenmeli.
11. Etkinlik ve Etkileşim
 - Hikaye sonunda resim çizimi veya el işi önerisi sunulmalı.
 - “Allah cc’den ne öğrendin?” gibi sorularla öğrenci katılımı sağlanmalı.
 - Küçük bulmacalar eklenebilir (tevhid temalı 3 soru).
 - “‘Günün kelimesi’” ya da “‘Günün değeri’” gibi mini etiketler kullanılabilir.

Başlık: {title}
Yaş Grubu: {yas_grubu or "Belirtilmedi"}
Hikaye Türü: {hikaye_turu or "Belirtilmedi"}
Hikaye Nerede Geçiyor: {gecis_yeri or "Belirtilmedi"}
Ana Karakter: {karakter or "Belirtilmedi"}
İşlenecek Değerler: {', '.join(degerler)}

"""

    # Yaş grubuna göre hikayenin dil ve içerik seviyesi ayarlanıyor.
    # Böylece hikaye hedef yaşa uygun ve anlaşılır olur.
    yas_promptlari = {
        "3-5": (
            "Hikaye çok basit, anlaşılır ve akıcı bir dille yazılsın. "
            "Kısa, net cümleler kullanılsın. Hikayede karmaşık ve soyut kavramlardan kaçınılsın. "
            "Olaylar ve karakterler somut ve kolay hayal edilebilir olsun. "
            "Karakterlerin duyguları basit şekilde ifade edilsin, tekrarlar ve ritmik ifadeler eklenerek çocukların dikkatini çeksin."
        ),
        "6-8": (
            "Hikaye sade ve anlaşılır bir dille yazılsın. "
            "Basit ama anlamlı olay örgüsü olsun. "
            "Karakterlerin kişilik özellikleri biraz daha derinleştirilsin. "
            "Duygular ve davranışlar çocukların yaşadığı deneyimlere uygun şekilde detaylandırılsın. "
            "Açıklamalar net, ama hayal gücünü teşvik edecek betimlemeler eklenerek ilgi çekici olsun."
        ),
        "9-12": (
            "Hikaye daha ayrıntılı ve kapsamlı yazılsın. "
            "Olaylar mantıklı, neden-sonuç ilişkilerine uygun ve akıcı şekilde ilerlesin. "
            "Karakterlerin iç dünyası, düşünceleri, duyguları ve gelişimleri detaylandırılsın. "
            "Çocukların sorgulayıcı düşünme becerilerini destekleyecek unsurlar eklensin. "
            "Betimlemeler zengin ve canlı olsun, ortam ve karakter detayları net bir şekilde resmedilsin."
        )
    }

    # Eğer yaş grubu belirtilmişse ilgili promptu ekle
    if yas_grubu in yas_promptlari:
        prompt += yas_promptlari[yas_grubu] + "\n"

    # Hikaye türüne göre de hikayenin tonu ve içeriği şekillendiriliyor.
    tur_promptlari = {
        "komik": (
            "Hikaye bol esprili, eğlenceli ve neşeli bir şekilde yazılsın. "
            "Karakterlerin davranışları ve diyalogları çocukların gülümsemesini sağlayacak şekilde tasarlansın. "
            "Olaylar beklenmedik ama zararsız sürprizler ve mizahi durumlarla dolu olsun. "
            "Dil akıcı, espriler sade ve çocukların anlayabileceği türde olsun."
        ),
        "masal": (
            "Hikaye hayal gücü yüksek ve özgün bir masal şeklinde yazılsın. "
            "Sihir ve büyü unsurları kullanılmasın, ancak olağanüstü ve fantastik durumlar olmadan sürükleyici bir anlatım olsun. "
            "Karakterler ve olaylar çocukların hayal dünyasını genişletecek biçimde canlı ve renkli betimlensin. "
            "Öğretici ve olumlu mesajlar hikayenin içine ustaca yerleştirilsin."
        ),
        "macera": (
            "Hikaye heyecan verici, hareketli ve sürükleyici şekilde yazılsın. "
            "Olaylar tempolu ilerlesin, beklenmedik dönemeçler ve çözümlerle dolu olsun. "
            "Karakterlerin cesaretleri, keşifleri ve zorluklarla başa çıkmaları detaylandırılsın. "
            "Betimlemeler canlı ve ortam tasvirleri güçlü olsun, okuyucuyu hikayenin içine çeksin."
        ),
        "egitici": (
            "Hikaye öğretici ve bilgilendirici bir şekilde yazılsın. "
            "Dini ve ahlaki değerler nazik ve doğru biçimde işlenerek çocuklara faydalı mesajlar verilsin. "
            "Karakterlerin davranışları örnek teşkil edecek şekilde betimlensin. "
            "Dil sade, açıklayıcı ve çocukların anlayabileceği biçimde olsun."
        )
    }

    # Eğer hikaye türü belirtilmişse ilgili tür promptu ekleniyor
    if hikaye_turu in tur_promptlari:
        prompt += tur_promptlari[hikaye_turu] + "\n"

    # Hikayenin uzunluğuna göre kelime sayısı ve detay seviyesi ayarlanıyor.
    if uzunluk == "kisa":
        prompt += (
            "Hikaye tam 250 kelime , kısa ve öz olsun. "
            "Ancak karakter gelişimi ve olay örgüsü tam olarak anlaşılsın. "
            "Basit ama etkili bir sonla tamamlanmalı."
        )
    elif uzunluk == "orta":
        prompt += (
            "Hikaye tam 400 kelime olsun. "
            "Karakterlerin kişilikleri ve olaylar daha detaylı işlenmeli. "
            "Hikaye giriş, gelişme ve sonuç bölümlerini dengeli şekilde içermeli."
        )
    elif uzunluk == "uzun":
        prompt += (
            "Hikaye tam 600 kelime uzunluğunda, detaylı, zengin betimlemelerle dolu olsun. "
            "Karakterlerin duyguları, düşünceleri ve etkileşimleri ayrıntılı şekilde anlatılsın. "
            "Olaylar akıcı, mantıklı ve etkileyici şekilde ilerlesin."
        )

    # İç içe fonksiyon: hikaye üretimini stream (parça parça) olarak yapar
    def generate():
        try:
            # Modelden stream (akış) şeklinde çıktı alınıyor
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "Sen yaratıcı bir çocuk hikayesi yazma asistanısın.Hikaye kesinlikle belirtilen uzunlukta yaz."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.9,  # Yaratıcı ve çeşitli içerik için biraz yüksek sıcaklık
                max_tokens=3050,  # Maksimum token sayısı (uzun hikayeler için)
                stream=True       # Stream aktif, böylece kısım kısım içerik döner
            )

            # Modelin gönderdiği her parçayı (chunk) tek tek döner
            for chunk in response:
                # İçerik var mı kontrolü
                content = getattr(chunk.choices[0].delta, "content", None)
                if content:
                    yield content  # Parçayı dışarı aktar

        except Exception as e:
            # Hata durumunda hata mesajı da stream içinde gönderilir
            yield f"\n[Hata: {str(e)}]"

    # Streaming response ile kullanıcıya kısım kısım hikaye gönderilir.
    # Böylece uzun bekleme olmaz, kullanıcı yazının gelişimini anlık görür.
    return Response(stream_with_context(generate()), content_type='text/plain')


if __name__ == "__main__":
    # Flask uygulamasını debug modda başlatır
    # Geliştirme sırasında hata ayıklamayı kolaylaştırır
    app.run(debug=True)
