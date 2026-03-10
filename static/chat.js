const chatLog = document.getElementById("chat-log");
const chatForm = document.getElementById("chat-form");
const messageInput = document.getElementById("message");
const sendButton = document.getElementById("send-button");

const STORAGE_KEY = "letterguard-chat-history";

function createMessageElement(role, text, extraClass = "") {
  const message = document.createElement("article");
  message.className = `message message-${role}${extraClass ? ` ${extraClass}` : ""}`;
  message.textContent = text;
  return message;
}

function appendMessage(role, text, extraClass = "") {
  const message = createMessageElement(role, text, extraClass);
  chatLog.appendChild(message);
  chatLog.scrollTop = chatLog.scrollHeight;
  return message;
}

function saveHistory() {
  const history = Array.from(chatLog.querySelectorAll(".message"))
    .filter((node) => !node.classList.contains("message-status"))
    .map((node) => ({
      role: node.classList.contains("message-user") ? "user" : "assistant",
      text: node.textContent || "",
    }));
  window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(history));
}

function restoreHistory() {
  const raw = window.sessionStorage.getItem(STORAGE_KEY);
  if (!raw) {
    appendMessage(
      "assistant",
      "Ask me about a letter, run a QA check, or request an explanation of a saved result."
    );
    return;
  }

  try {
    const history = JSON.parse(raw);
    if (!Array.isArray(history) || history.length === 0) {
      throw new Error("Empty history");
    }

    history.forEach((item) => {
      if (!item || typeof item.text !== "string") {
        return;
      }
      appendMessage(item.role === "user" ? "user" : "assistant", item.text);
    });
  } catch {
    window.sessionStorage.removeItem(STORAGE_KEY);
    appendMessage("assistant", "Ask me about a letter, run a QA check, or request an explanation of a saved result.");
  }
}

async function sendMessage(message) {
  const thinkingMessage = appendMessage("assistant", "Thinking...", "message-status");

  try {
    const response = await fetch("/api/chat/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });

    if (!response.ok) {
      throw new Error("The server could not process the request.");
    }

    const payload = await response.json();
    thinkingMessage.classList.remove("message-status");
    thinkingMessage.textContent = payload.answer || "No response was returned.";
  } catch (error) {
    thinkingMessage.classList.remove("message-status");
    thinkingMessage.textContent =
      error instanceof Error
        ? `Sorry, something went wrong. ${error.message}`
        : "Sorry, something went wrong while contacting the server.";
  }

  saveHistory();
}

chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  const message = messageInput.value.trim();
  if (!message) {
    return;
  }

  appendMessage("user", message);
  saveHistory();

  messageInput.value = "";
  sendButton.disabled = true;
  messageInput.focus();

  await sendMessage(message);

  sendButton.disabled = false;
});

messageInput.addEventListener("keydown", async (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    chatForm.requestSubmit();
  }
});

restoreHistory();
