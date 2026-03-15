const BACKEND = "http://localhost:8000";
const MIN_TIME_SECONDS = 15;
let tabStartTimes = {};

chrome.tabs.onActivated.addListener(async (activeInfo) => {
  tabStartTimes[activeInfo.tabId] = Date.now();
  try {
    const tab = await chrome.tabs.get(activeInfo.tabId);
    if (!tab.url || tab.url.startsWith("chrome://") || tab.url.startsWith("chrome-extension://")) return;
    const response = await fetch(`${BACKEND}/check-tab`, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({url: tab.url, title: tab.title || ""})
    });
    const data = await response.json();

    if (data.surface && data.message) {
      await chrome.storage.local.set({
        latestReminder: {
          message: data.message,
          timestamp: Date.now(),
          tabId: activeInfo.tabId
        }
      });
      chrome.notifications.create("reminder", {
        type: "basic",
        iconUrl: "icon.png",
        title: "Tab Memory",
        message: data.message
      });
    } else {
      await chrome.storage.local.remove("latestReminder");
    }
  } catch (err) {
    console.error("check-tab error:", err);
  }
});

chrome.tabs.onRemoved.addListener(async (tabId) => {
  await storeTabMemory(tabId);
  delete tabStartTimes[tabId];
});

chrome.tabs.onUpdated.addListener(async (tabId, changeInfo, tab) => {
  if (changeInfo.status === "loading" && tabStartTimes[tabId]) {
    await storeTabMemory(tabId, tab);
    tabStartTimes[tabId] = Date.now();
  }
});

async function storeTabMemory(tabId, tabOverride = null) {
  try {
    const startTime = tabStartTimes[tabId];
    if (!startTime) return;
    const timeSpent = Math.floor((Date.now() - startTime) / 1000);
    if (timeSpent < MIN_TIME_SECONDS) return;
    const tab = tabOverride || await chrome.tabs.get(tabId).catch(() => null);
    if (!tab || !tab.url || tab.url.startsWith("chrome://")) return;
    await fetch(`${BACKEND}/tab-event`, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        url: tab.url,
        title: tab.title || "",
        time_spent_seconds: timeSpent,
        event: "closed"
      })
    });
  } catch (err) {
    console.error("tab-event error:", err);
  }
}
// Feature 1: Session restore on Chrome startup
chrome.runtime.onStartup.addListener(async () => {
  await chrome.storage.local.remove("sessionShown");
});

// Feature 3: Idle tab nudge every 30 minutes
chrome.alarms.create("idle-check", { periodInMinutes: 30 });

chrome.alarms.onAlarm.addListener(async (alarm) => {
  if (alarm.name !== "idle-check") return;
  try {
    const res = await fetch(`${BACKEND}/idle-check`, { method: "POST" });
    const data = await res.json();
    if (data.has_idle && data.topics.length > 0) {
      // Badge the extension icon
      chrome.action.setBadgeText({ text: "!" });
      chrome.action.setBadgeBackgroundColor({ color: "#f59e0b" });
      await chrome.storage.local.set({
        idleNudge: {
          topics: data.topics,
          timestamp: Date.now()
        }
      });
    }
  } catch (err) {
    console.error("idle-check error:", err);
  }
});