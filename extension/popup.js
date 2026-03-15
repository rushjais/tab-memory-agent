const BACKEND = "http://localhost:8000";

document.addEventListener("DOMContentLoaded", async () => {
  await checkSessionRestore();
  await loadReminder();
  setupChat();
});

// Feature 1: Session restore
async function checkSessionRestore() {
  const { sessionShown, lastSessionDate } = await chrome.storage.local.get(["sessionShown", "lastSessionDate"]);
  const today = new Date().toDateString();

  if (sessionShown === today) return;

  try {
    const res = await fetch(`${BACKEND}/session-summary`, { method: "POST" });
    const data = await res.json();

    if (data.summary) {
      document.getElementById("session-view").style.display = "block";
      document.getElementById("chat-view").style.display = "none";
      document.getElementById("session-summary").textContent = data.summary;

      const pillsEl = document.getElementById("topic-pills");
      data.topics.forEach(t => {
        const pill = document.createElement("span");
        pill.className = "pill";
        pill.textContent = t;
        pillsEl.appendChild(pill);
      });

      const urlsEl = document.getElementById("session-urls");
      data.urls.forEach(url => {
        const btn = document.createElement("button");
        btn.className = "reopen-url-btn";
        btn.textContent = url;
        btn.onclick = () => chrome.tabs.create({ url });
        urlsEl.appendChild(btn);
      });

      await chrome.storage.local.set({ sessionShown: today });
    }
  } catch (err) {
    console.error("session-summary error:", err);
  }

  document.getElementById("dismiss-session").addEventListener("click", () => {
    document.getElementById("session-view").style.display = "none";
    document.getElementById("chat-view").style.display = "block";
  });
}

// Feature 4: Load current reminder with reopen button
async function loadReminder() {
  const data = await chrome.storage.local.get("latestReminder");
  if (!data.latestReminder) return;

  const { message, url } = data.latestReminder;
  document.getElementById("reminder-text").textContent = message;
  document.getElementById("reminder").style.display = "block";

  if (url) {
    const reopenBtn = document.getElementById("reopen-btn");
    reopenBtn.style.display = "block";
    reopenBtn.onclick = () => chrome.tabs.create({ url });
  }

  document.getElementById("speak-btn").addEventListener("click", async () => {
    const btn = document.getElementById("speak-btn");
    btn.textContent = "Generating...";
    btn.disabled = true;
    try {
      const res = await fetch(`${BACKEND}/speak`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message })
      });
      const blob = await res.blob();
      const audio = new Audio(URL.createObjectURL(blob));
      audio.play();
    } catch (e) {
      console.error(e);
    }
    btn.textContent = "▶ Hear this";
    btn.disabled = false;
  });

  document.getElementById("clear-btn").addEventListener("click", async () => {
    await chrome.storage.local.remove("latestReminder");
    document.getElementById("reminder").style.display = "none";
  });
}

// Feature 2: Chat interface
function setupChat() {
  const input = document.getElementById("chat-input");
  const sendBtn = document.getElementById("chat-send");
  const messages = document.getElementById("chat-messages");

  async function sendMessage() {
    const text = input.value.trim();
    if (!text) return;
    input.value = "";

    // Clear hint
    const hint = messages.querySelector(".chat-hint");
    if (hint) hint.remove();

    // Add user message
    const userMsg = document.createElement("div");
    userMsg.className = "msg user";
    userMsg.textContent = text;
    messages.appendChild(userMsg);
    messages.scrollTop = messages.scrollHeight;

    // Add loading
    const loadingMsg = document.createElement("div");
    loadingMsg.className = "msg assistant";
    loadingMsg.textContent = "Thinking...";
    messages.appendChild(loadingMsg);
    messages.scrollTop = messages.scrollHeight;

    try {
      const res = await fetch(`${BACKEND}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text })
      });
      const data = await res.json();

      loadingMsg.textContent = data.reply;

      // Add reopen URL buttons if any
      if (data.urls && data.urls.length > 0) {
        const urlsDiv = document.createElement("div");
        urlsDiv.className = "msg-urls";
        data.urls.forEach(url => {
          const btn = document.createElement("button");
          btn.className = "msg-url-btn";
          btn.textContent = "↩ " + url.replace("https://", "").split("/")[0];
          btn.onclick = () => chrome.tabs.create({ url });
          urlsDiv.appendChild(btn);
        });
        loadingMsg.appendChild(urlsDiv);
      }
    } catch (err) {
      loadingMsg.textContent = "Error reaching backend.";
    }

    messages.scrollTop = messages.scrollHeight;
  }

  sendBtn.addEventListener("click", sendMessage);
  input.addEventListener("keydown", e => {
    if (e.key === "Enter") sendMessage();
  });
}