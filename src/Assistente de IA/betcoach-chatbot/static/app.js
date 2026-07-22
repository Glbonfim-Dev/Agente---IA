const messages = document.querySelector("#messages");
const emptyState = document.querySelector("#empty-state");
const form = document.querySelector("#chat-form");
const input = document.querySelector("#message-input");
const sendButton = document.querySelector("#send-button");
const clearButton = document.querySelector("#clear-button");
const statusDot = document.querySelector("#status-dot");
const statusText = document.querySelector("#status-text");

function removeEmptyState() {
  document.querySelector("#empty-state")?.remove();
}

function addMessage(role, content, meta = "") {
  removeEmptyState();
  const row = document.createElement("div");
  row.className = `message-row ${role}`;
  if (role === "assistant") {
    const avatar = document.createElement("div");
    avatar.className = "avatar";
    avatar.textContent = "🎓";
    row.appendChild(avatar);
  }
  const bubble = document.createElement("div");
  bubble.className = "bubble";
  const text = document.createElement("div");
  text.textContent = content;
  bubble.appendChild(text);
  if (meta) {
    const info = document.createElement("div");
    info.className = "meta";
    info.textContent = meta;
    bubble.appendChild(info);
  }
  row.appendChild(bubble);
  messages.appendChild(row);
  window.scrollTo({ top: document.body.scrollHeight, behavior: "smooth" });
  return row;
}

function addTyping() {
  removeEmptyState();
  const row = document.createElement("div");
  row.className = "message-row assistant typing";
  row.innerHTML = '<div class="avatar">🎓</div><div class="bubble typing-dots"><span>●</span> <span>●</span> <span>●</span></div>';
  messages.appendChild(row);
  return row;
}

async function loadHistory() {
  try {
    const response = await fetch("/api/history");
    const history = await response.json();
    history.forEach(item => addMessage(item.role, item.content));
  } catch (_) {}
}

async function loadStatus() {
  try {
    const response = await fetch("/api/status");
    const status = await response.json();
    if (status.connected && status.available) {
      statusDot.classList.add("online");
      statusText.textContent = `Modelo local ${status.model}`;
    } else {
      statusText.textContent = "Modo básico local";
    }
  } catch (_) {
    statusText.textContent = "Modo básico local";
  }
}

form.addEventListener("submit", async event => {
  event.preventDefault();
  const question = input.value.trim();
  if (!question || sendButton.disabled) return;
  addMessage("user", question);
  input.value = "";
  input.style.height = "auto";
  sendButton.disabled = true;
  const typing = addTyping();
  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: question })
    });
    const data = await response.json();
    typing.remove();
    if (!response.ok) throw new Error(data.error || "Falha ao responder.");
    const sourceText = data.sources?.length ? `Base: ${data.sources.join(", ")}` : "Modo básico local";
    addMessage("assistant", data.answer, sourceText);
  } catch (error) {
    typing.remove();
    addMessage("assistant", error.message || "Não foi possível responder agora.");
  } finally {
    sendButton.disabled = false;
    input.focus();
  }
});

input.addEventListener("keydown", event => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    form.requestSubmit();
  }
});

input.addEventListener("input", () => {
  input.style.height = "auto";
  input.style.height = `${Math.min(input.scrollHeight, 130)}px`;
});

clearButton.addEventListener("click", async () => {
  await fetch("/api/clear", { method: "POST", headers: { "Content-Type": "application/json" }, body: "{}" });
  messages.innerHTML = '<div id="empty-state" class="empty-state"><div class="empty-icon">💬</div><strong>O que você quer entender hoje?</strong><span>Faça sua pergunta. As respostas são educativas e não prometem resultados.</span></div>';
  input.focus();
});

loadHistory();
loadStatus();
input.focus();
