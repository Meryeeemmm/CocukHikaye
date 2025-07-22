// DOM yüklendiğinde işlemlere başlamak için olay dinleyicisi ekleniyor
document.addEventListener("DOMContentLoaded", () => {
  // Form, hata mesajı, sonuç kutuları ve diğer HTML elemanları seçiliyor
  const storyForm = document.getElementById("storyForm");
  const errorMessage = document.getElementById("errorMessage");
  const storyResultContainer = document.getElementById("storyResultContainer");
  const storyContentP = document.getElementById("storyContent");
  const imageResult = document.getElementById("storyImage");
  const generateButton = document.getElementById("generateButton");
  const loadingIndicator = document.getElementById("loadingIndicator");
  const hikayeTuruSelect = document.getElementById("hikayeTuru");

  // Arka plan partikül animasyonlarını yükler (tsParticles kütüphanesi kullanılıyor)
  function loadParticles(color) {
    tsParticles.load("tsparticles", {
      fpsLimit: 60, // saniyede maksimum 60 kare çizilir
      particles: {
        number: { value: 60, density: { enable: true, area: 800 } }, // 60 partikül
        color: { value: color }, // partikül rengi temaya göre ayarlanır
        shape: { type: "circle" }, // şekli daire
        opacity: { value: 0.5 },
        size: { value: 4, random: { enable: true, minimumValue: 1 } },
        links: {
          enable: true,
          distance: 150,
          color: color,
          opacity: 0.4,
          width: 1,
        },
        move: {
          enable: true,
          speed: 2,
          direction: "none",
          random: false,
          straight: false,
          outModes: "out",
        },
      },
      interactivity: {
        detectsOn: "canvas",
        events: {
          onHover: { enable: true, mode: "repulse" }, // fare üzerine gelince partiküller uzaklaşır
          onClick: { enable: false },
          resize: true,
        },
        modes: { repulse: { distance: 100, duration: 0.4 } },
      },
      detectRetina: true,
    });
  }

  // Tema seçildiğinde sayfa arka planı ve partikül rengi değiştiriliyor
  function applyTheme() {
    const selectedTheme = hikayeTuruSelect.value;
    
    // Önce tüm temaları kaldır
    document.body.classList.remove("theme-masal", "theme-macera", "theme-egitici", "theme-komik");

    // Varsayılan partikül rengi
    let particleColor = "#7c3aed";

    // Seçilen temaya göre sınıf ve renk belirlenir
    switch (selectedTheme) {
      case "Masal":
        document.body.classList.add("theme-masal");
        particleColor = "#a78bfa";
        break;
      case "Macera":
        document.body.classList.add("theme-macera");
        particleColor = "#f97316";
        break;
      case "Eğitici":
        document.body.classList.add("theme-egitici");
        particleColor = "#2563eb";
        break;
      case "Komik":
        document.body.classList.add("theme-komik");
        particleColor = "#facc15";
        break;
    }

    // Eski partikülleri silip yenisini yükler
    tsParticles.domItem(0)?.destroy();
    loadParticles(particleColor);
  }

  // Tema her değiştiğinde fonksiyon çağrılır
  hikayeTuruSelect.addEventListener("change", applyTheme);
  applyTheme(); // Sayfa yüklendiğinde de varsayılan temayı uygular

  // Hikaye içerik alanına "yazılıyor efekti" için animasyon ayarı
  function updateCaretAnimation() {
    if (storyContentP.textContent.trim().length === 0) {
      storyContentP.style.borderRight = "2px solid #5b21b6";
      storyContentP.style.animation = "blink-caret 0.75s step-end infinite";
    } else {
      storyContentP.style.borderRight = "none";
      storyContentP.style.animation = "none";
    }
  }

  updateCaretAnimation(); // Sayfa ilk açıldığında animasyon kontrolü yapılır

  // Form gönderildiğinde yapılacak işlemler
  storyForm.addEventListener("submit", async (e) => {
    e.preventDefault(); // Sayfanın yeniden yüklenmesini engeller

    // Önce bazı alanlar temizlenir veya gizlenir
    errorMessage.classList.add("hidden");
    storyResultContainer.classList.add("hidden");
    loadingIndicator.classList.remove("hidden"); // Yükleniyor göstergesi gösterilir
    generateButton.disabled = true;
    generateButton.textContent = "Oluşturuluyor..."; // Buton yazısı değişir

    storyContentP.textContent = "";
    updateCaretAnimation();

    // Formdan gelen veriler alınır
    const title = document.getElementById("title").value.trim();
    const selectedValues = [];
    document.querySelectorAll('input[name="degerler"]:checked').forEach((cb) => {
      selectedValues.push(cb.value);
    });
    const yasGrubu = document.getElementById("yasGrubu").value;
    const karakter = document.getElementById("karakter").value.trim();
    const gecisYeri = document.getElementById("gecisYer").value.trim();
    const hikayeTuru = hikayeTuruSelect.value;
    const uzunluk = document.getElementById("uzunluk").value;

    // Zorunlu alanlar için kontroller yapılır
    if (!title) {
      errorMessage.textContent = "Hikaye başlığı boş bırakılamaz.";
      errorMessage.classList.remove("hidden");
      loadingIndicator.classList.add("hidden");
      generateButton.disabled = false;
      generateButton.textContent = "📖 Hikaye Oluştur";
      return;
    }
    if (selectedValues.length === 0) {
      errorMessage.textContent = "Lütfen en az bir değer seçin.";
      errorMessage.classList.remove("hidden");
      loadingIndicator.classList.add("hidden");
      generateButton.disabled = false;
      generateButton.textContent = "📖 Hikaye Oluştur";
      return;
    }

    try {
      // Görsel için uygun bir prompt oluşturuluyor
      let imagePrompt = `${title}`;
      if (karakter) imagePrompt += `, karakter: ${karakter}`;
      if (gecisYeri) imagePrompt += `, ortam: ${gecisYeri}`;
      imagePrompt += ", çocuk kitabı çizimi, canlı renkler, sevimli";

      // Görsel oluşturma API'sine istek gönderilir
      const imageResponse = await fetch("/generate_image", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: imagePrompt }),
      });
      const imageData = await imageResponse.json();

      // Görsel oluşturulamazsa hata fırlatılır
      if (!imageResponse.ok) {
        throw new Error(imageData.error || "Görsel oluşturulamadı.");
      }

      // Görsel ekrana yerleştirilir
      imageResult.src = imageData.image_url;
      imageResult.alt = `${title} görseli`;
      imageResult.style.display = "block";

      // Hikaye oluşturma isteği gönderilir
      const response = await fetch("/generate_story", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title,
          degerler: selectedValues,
          yas_grubu: yasGrubu,
          karakter,
          gecis_yeri: gecisYeri,
          hikaye_turu: hikayeTuru,
          uzunluk,
        }),
      });

      if (!response.ok || !response.body) {
        throw new Error("Hikaye akışı alınamadı.");
      }

      // Streaming için response body reader kullanılır
      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      storyContentP.textContent = "";
      storyResultContainer.classList.remove("hidden");

      let firstChunk = true;

      // Sunucudan gelen veriler parçalar halinde alınır
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        storyContentP.textContent += chunk; // Hikaye metni parça parça eklenir

        // İlk veri geldiğinde yükleme göstergesi kaldırılır
        if (firstChunk) {
          loadingIndicator.classList.add("hidden");
          firstChunk = false;
        }

        updateCaretAnimation(); // Her eklemede caret kontrolü yapılır

        // Sayfa otomatik olarak aşağıya kayar
        window.scrollTo({ top: document.body.scrollHeight, behavior: "smooth" });
      }
    } catch (error) {
      // Hata durumunda kullanıcıya mesaj gösterilir
      console.error(error);
      errorMessage.textContent = error.message || "Bir hata oluştu.";
      errorMessage.classList.remove("hidden");
    } finally {
      // Her durumda buton aktif hale getirilir ve yükleniyor mesajı kaldırılır
      loadingIndicator.classList.add("hidden");
      generateButton.disabled = false;
      generateButton.textContent = "📖 Hikaye Oluştur";
    }
  });
});
