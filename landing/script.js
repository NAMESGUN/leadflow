const BACKEND_URL = "http://localhost:8000";

const state = {};

// Захватываем UTM-метки из URL при заходе на страницу
const params = new URLSearchParams(window.location.search);
["utm_source", "utm_medium", "utm_campaign"].forEach((key) => {
  if (params.has(key)) state[key] = params.get(key);
});

function showStep(stepName) {
  document.querySelectorAll(".step").forEach((el) => {
    el.hidden = el.dataset.step !== stepName;
  });
}

// Шаг 1: выбор типа объекта
document.querySelectorAll("[data-field='project_type']").forEach((btn) => {
  btn.addEventListener("click", () => {
    state.project_type = btn.dataset.value;
    document
      .querySelectorAll("[data-field='project_type']")
      .forEach((b) => b.classList.remove("selected"));
    btn.classList.add("selected");
    setTimeout(() => showStep("2"), 200);
  });
});

// Шаг 2: площадь
document.querySelector(".next-btn").addEventListener("click", () => {
  const area = document.querySelector("input[name='area']").value;
  if (!area) return;
  state.area = area;
  showStep("3");
});

// Шаг 3: контакты и отправка
document.getElementById("quiz-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  state.name = document.querySelector("input[name='name']").value;
  state.phone = document.querySelector("input[name='phone']").value;

  if (!state.name || !state.phone) return;

  const payload = {
    name: state.name,
    phone: state.phone,
    source: "form",
    project_type: state.project_type,
    utm_source: state.utm_source || "direct",
    utm_medium: state.utm_medium || null,
    utm_campaign: state.utm_campaign || null,
    raw_payload: { area: state.area },
  };

  try {
    await fetch(`${BACKEND_URL}/webhook/form`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  } catch (err) {
    console.error("Не удалось отправить заявку", err);
  }

  showStep("done");
});
