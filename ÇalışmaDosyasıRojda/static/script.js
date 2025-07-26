document.addEventListener("DOMContentLoaded", () => {
  const storyForm = document.getElementById("story-form");
  const errorMessage = document.getElementById("errorMessage");
  const storyResultContainer = document.getElementById("storyResultContainer");
  const storyContentP = document.getElementById("storyContent");
  const generateButton = document.getElementById("submit-btn");

  const openModal = document.getElementById("show-values");
  const closeModal = document.getElementById("close-degerler");
  const modal = document.getElementById("degerler-modal");
  const valuesForm = document.getElementById("valuesForm");

  openModal.addEventListener("click", () => {
    modal.classList.remove("hidden");
    document.body.style.overflow = "hidden";
  });

  closeModal.addEventListener("click", () => {
    modal.classList.add("hidden");
    document.body.style.overflow = "auto";
  });

  storyForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const selectedValues = Array.from(
      valuesForm.querySelectorAll('input[name="degerler"]:checked')
    ).map(cb => cb.value);

    if (selectedValues.length === 0) {
      errorMessage.textContent = "Lütfen en az bir değer seçin.";
      errorMessage.classList.remove("hidden");
      return;
    }

    errorMessage.classList.add("hidden");
    storyResultContainer.classList.add("hidden");
    generateButton.disabled = true;
    generateButton.textContent = "Oluşturuluyor...";
    storyContentP.textContent = "";

    const payload = {
      degerler: selectedValues,
      yas_grubu: document.getElementById("age").value,
      karakter: document.getElementById("character").value.trim(),
      gecis_yeri: document.getElementById("place").value.trim(),
      hikaye_turu: document.getElementById("genre").value,
      uzunluk: document.getElementById("length").value
    };

    try {
      const response = await fetch("/generate_story", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      storyResultContainer.classList.remove("hidden");

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        storyContentP.textContent += decoder.decode(value, { stream: true });
        window.scrollTo({ top: document.body.scrollHeight, behavior: "smooth" });
      }
    } catch (err) {
      errorMessage.textContent = "Bir hata oluştu.";
      errorMessage.classList.remove("hidden");
    } finally {
      generateButton.disabled = false;
      generateButton.textContent = "🙌 Hikaye Oluştur";
    }
  });
});