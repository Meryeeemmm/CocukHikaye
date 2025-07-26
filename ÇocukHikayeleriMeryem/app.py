import os
from flask import Flask, render_template, request, Response, stream_with_context
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/generate_story", methods=["POST"])
def generate_story():
    data = request.get_json()

    degerler = data.get("degerler", [])
    yas_grubu = data.get("yas_grubu", "")
    karakter = data.get("karakter", "")
    gecis_yeri = data.get("gecis_yeri", "")
    hikaye_turu = data.get("hikaye_turu", "")
    uzunluk = data.get("uzunluk", "")

    prompt = f"""
Sen İslamî değerlere uygun, çocuklara yönelik öğretici bir hikaye yazma uzmanısın.
Aşağıdaki bilgilere göre hikaye yaz:
- Yaş Grubu: {yas_grubu}
- Hikaye Türü: {hikaye_turu}
- Mekan: {gecis_yeri}
- Ana Karakter: {karakter}
- İşlenecek Değerler: {', '.join(degerler)}
- Uzunluk: {uzunluk} (kısa: 250, orta: 400, uzun: 600 kelime)

Kurallar:
- Allah (cc) zikri mutlaka geçmeli.
- Şirk, eşcinsellik, demokrasi gibi konular anlatılmamalı.
- Hikaye dili yaş grubuna uygun olmalı.
- Her hikaye bir dua ile bitmeli.
- Sadece hikaye içeriği yazılmalı, açıklama yapma.
"""

    yas_promptlari = {
        "3-5": "Çok kısa, basit ve tekrarlı cümleler kullan.",
        "6-8": "Basit ama anlamlı cümleler, duygular açıkça ifade edilsin.",
        "9-11": "Daha zengin kelime, duygu ve olay örgüsü kullan."
    }

    if yas_grubu in yas_promptlari:
        prompt += yas_promptlari[yas_grubu]

    kelime_limit = {"kisa": 250, "orta": 400, "uzun": 600}
    max_tokens = kelime_limit.get(uzunluk, 400) * 2  # Yaklaşık hesap

    def generate():
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "Sen İslamî çocuk hikayesi yazma uzmanısın."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=max_tokens,
                stream=True
            )
            for chunk in response:
                content = chunk.choices[0].delta.content
                if content:
                    yield content
        except Exception as e:
            yield f"\n[Hata: {str(e)}]"

    return Response(stream_with_context(generate()), content_type='text/plain')

if __name__ == "__main__":
    app.run(debug=True)