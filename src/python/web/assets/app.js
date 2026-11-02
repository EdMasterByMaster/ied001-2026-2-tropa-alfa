const grid = document.querySelector("#event-grid");
const notice = document.querySelector("#notice");
const registerDialog = document.querySelector("#register-dialog");
const createDialog = document.querySelector("#create-dialog");

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[char]);
}

function showNotice(message, isError = false) {
  notice.textContent = message;
  notice.hidden = !message;
  notice.style.borderColor = isError ? "rgba(226,62,50,.65)" : "";
}

async function api(url, options = {}) {
  const response = await fetch(url, {
    ...options,
    headers: { "Content-Type": "application/json", ...options.headers },
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.error || "Não foi possível concluir a operação.");
  return data;
}

function formatDate(isoDate) {
  return new Intl.DateTimeFormat("pt-BR", {
    day: "2-digit", month: "short", year: "numeric", timeZone: "UTC",
  }).format(new Date(`${isoDate}T12:00:00Z`)).replace(".", "").toUpperCase();
}

function renderEvents(events) {
  document.querySelector("#event-count").textContent = String(events.length).padStart(2, "0");
  if (!events.length) {
    grid.innerHTML = '<div class="empty-state">Nenhum evento encontrado. Tente outros filtros ou publique um novo evento.</div>';
    return;
  }
  grid.innerHTML = events.map((event, index) => {
    const fill = event.capacity ? Math.min(100, Math.round(event.occupied / event.capacity * 100)) : 0;
    const full = event.available === 0;
    return `
      <article class="event-card">
        <div class="event-cover">
          <span class="cover-number">${String(index + 1).padStart(2, "0")}</span>
          <span class="status-pill ${full ? "sold-out" : ""}">${full ? "Lotado · fila aberta" : "Inscrições abertas"}</span>
          <span class="cover-orb"></span>
        </div>
        <div class="event-content">
          <p class="event-date">${escapeHtml(formatDate(event.date))}</p>
          <h3>${escapeHtml(event.name)}</h3>
          <p class="event-location">⌖ &nbsp;${escapeHtml(event.location)}</p>
          <div class="event-meta"><span>${event.available} vagas disponíveis</span><span>${event.waiting} na fila</span></div>
          <div class="capacity-track"><div class="capacity-fill" style="width:${fill}%"></div></div>
          <button class="button ${full ? "button-outline" : "button-primary"}" data-register="${event.id}">
            ${full ? "Entrar na lista de espera" : "Quero participar"} <span aria-hidden="true">→</span>
          </button>
        </div>
      </article>`;
  }).join("");
}

async function loadEvents() {
  const params = new URLSearchParams(new FormData(document.querySelector("#search-form")));
  for (const [key, value] of [...params.entries()]) if (!value) params.delete(key);
  showNotice("");
  grid.innerHTML = '<div class="empty-state">Carregando eventos...</div>';
  try {
    renderEvents(await api(`/api/events?${params.toString()}`));
  } catch (error) {
    grid.innerHTML = "";
    showNotice(error.message, true);
  }
}

document.querySelector("#search-form").addEventListener("submit", (event) => {
  event.preventDefault();
  loadEvents();
});

grid.addEventListener("click", (event) => {
  const button = event.target.closest("[data-register]");
  if (!button) return;
  const card = button.closest(".event-card");
  document.querySelector("#register-form").reset();
  document.querySelector("#register-form [name=event_id]").value = button.dataset.register;
  document.querySelector("#register-event").textContent = `${card.querySelector("h3").textContent} · ${card.querySelector(".event-date").textContent}`;
  document.querySelector("#register-message").textContent = "";
  registerDialog.showModal();
});

document.querySelector("#register-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const message = document.querySelector("#register-message");
  const button = form.querySelector("button[type=submit]");
  button.disabled = true;
  message.textContent = "Confirmando sua inscrição...";
  try {
    const result = await api(`/api/events/${form.elements.event_id.value}/registrations`, {
      method: "POST",
      body: JSON.stringify({ name: form.elements.name.value, email: form.elements.email.value }),
    });
    message.textContent = result.status === "confirmada"
      ? `Inscrição confirmada! Guarde seu número de ingresso: #${result.id}.`
      : `Evento lotado: você entrou na lista de espera. Guarde seu número para consulta: #${result.id}.`;
    form.reset();
    await loadEvents();
  } catch (error) {
    message.textContent = error.message;
  } finally {
    button.disabled = false;
  }
});

document.querySelector("#lookup-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const output = document.querySelector("#lookup-result");
  output.textContent = "Consultando...";
  try {
    const registration = await api(`/api/registrations/${encodeURIComponent(form.elements.id.value)}`);
    const labels = { confirmada: "Confirmada", lista_espera: "Na lista de espera", cancelada: "Cancelada" };
    output.textContent = `Ingresso #${registration.id} · Evento #${registration.event_id} · ${labels[registration.status] || registration.status}`;
    if (registration.status !== "cancelada") {
      const cancel = document.createElement("button");
      cancel.className = "button button-outline button-small";
      cancel.type = "button";
      cancel.textContent = "Cancelar inscrição";
      cancel.addEventListener("click", async () => {
        cancel.disabled = true;
        try {
          const result = await api(`/api/registrations/${registration.id}`, { method: "DELETE" });
          output.textContent = result.promoted_id
            ? `Ingresso #${registration.id} cancelado. Inscrição #${result.promoted_id} promovida da fila.`
            : `Ingresso #${registration.id} cancelado.`;
          await loadEvents();
        } catch (error) {
          output.textContent = error.message;
          cancel.disabled = false;
        }
      });
      output.append(document.createElement("br"), cancel);
    }
  } catch (error) {
    output.textContent = error.message;
  }
});

function openCreateDialog() {
  document.querySelector("#create-form").reset();
  document.querySelector("#create-message").textContent = "";
  createDialog.showModal();
}
document.querySelector("#open-create").addEventListener("click", openCreateDialog);
document.querySelector("#open-create-bottom").addEventListener("click", openCreateDialog);

document.querySelector("#create-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const message = document.querySelector("#create-message");
  const button = form.querySelector("button[type=submit]");
  button.disabled = true;
  message.textContent = "Publicando seu evento...";
  try {
    const created = await api("/api/events", {
      method: "POST",
      body: JSON.stringify({
        name: form.elements.name.value,
        date: form.elements.date.value,
        location: form.elements.location.value,
        capacity: Number(form.elements.capacity.value),
      }),
    });
    createDialog.close();
    await loadEvents();
    showNotice(`Evento criado com sucesso! Seu código é #${created.id}.`);
    document.querySelector("#eventos").scrollIntoView({ behavior: "smooth" });
  } catch (error) {
    message.textContent = error.message;
  } finally {
    button.disabled = false;
  }
});

document.querySelectorAll("[data-close]").forEach((button) => {
  button.addEventListener("click", () => button.closest("dialog").close());
});
document.querySelectorAll("dialog").forEach((dialog) => {
  dialog.addEventListener("click", (event) => {
    if (event.target === dialog) dialog.close();
  });
});

loadEvents();
