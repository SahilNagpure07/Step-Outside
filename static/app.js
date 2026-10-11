const title = document.getElementById("title");
const text = document.getElementById("text");
const settings = document.getElementById("settings");
const minutesInput = document.getElementById("minutes");
const startBtn = document.getElementById("start-btn");
const photoBtn = document.getElementById("photo-btn");
const photoInput = document.getElementById("photo-input");
const againBtn = document.getElementById("again-btn");

let sessionId = null;
let timer = null;
let nudgeAt = null;
let nudged = false;

function setVisible(element, visible) {
  element.classList.toggle("hidden", !visible);
}

function show(heading, body) {
  title.textContent = heading;
  text.textContent = body || "";
}

async function post(url, body) {
  const response = await fetch(url, { method: "POST", body: body });
  const data = await response.json();
  if (!response.ok) throw data;
  return data;
}

function showLanding() {
  clearInterval(timer);
  sessionId = null;
  nudgeAt = null;
  nudged = false;
  minutesInput.value = localStorage.getItem("minutes") || 20;
  show("🌱 Step Outside", "A small nudge to look up. One photo, then you're done.");
  setVisible(settings, true);
  setVisible(startBtn, true);
  setVisible(photoBtn, false);
  setVisible(againBtn, false);
}

startBtn.onclick = async () => {
  const minutes = parseFloat(minutesInput.value);
  if (!(minutes >= 0.25 && minutes <= 240)) {
    show("🌱 Step Outside", "Please choose between 0.25 and 240 minutes.");
    return;
  }
  localStorage.setItem("minutes", minutes);
  try {
    if ("Notification" in window) await Notification.requestPermission();
  } catch (error) {
    console.log("Notifications not supported here");
  }

  try {
    const data = await post(`/api/start?minutes=${minutes}`);
    sessionId = data.id;
    setVisible(settings, false);
    setVisible(startBtn, false);
    show("Okay.", `Keep working. We'll check in after ${minutes} minute(s).`);

    nudged = false;
    nudgeAt = Date.now() + data.idle_seconds * 1000;
    timer = setInterval(checkTime, 1000);
  } catch (error) {
    show("Something went wrong.", error.detail || "");
  }
};

function checkTime() {
  if (sessionId && !nudged && nudgeAt && Date.now() >= nudgeAt) {
    nudge();
  }
}

document.addEventListener("visibilitychange", () => {
  if (!document.hidden) checkTime();
});

async function nudge() {
  if (nudged) return;
  nudged = true;
  clearInterval(timer);
  const message = "You've been looking down for a while.";

  try {
    if ("Notification" in window && Notification.permission === "granted") {
      new Notification("Step Outside", { body: message });
    }
  } catch (error) {
    console.log("Notifications not supported here");
  }

  try {
    const data = await post(`/api/${sessionId}/challenge`);
    show(message, data.challenge);
    setVisible(photoBtn, true);
  } catch (error) {
    show("Couldn't load your challenge.", error.detail || "Please press Start again.");
    setVisible(againBtn, true);
  }
}

photoInput.onchange = async () => {
  const form = new FormData();
  form.append("file", photoInput.files[0]);
  photoInput.value = "";
  setVisible(photoBtn, false);
  show("Looking closely...", "");

  try {
    const data = await post(`/api/${sessionId}/photo`, form);
    show(data.reply, "");
    await playVoice();

    await post(`/api/${sessionId}/end`);
    show(data.closing, "");
    showInfo();
  } catch (error) {
    show(error.detail || "Something went wrong.", "");
  }
  setVisible(againBtn, true);
};

againBtn.onclick = showLanding;

function playVoice() {
  return new Promise((done) => {
    const speech = new SpeechSynthesisUtterance("Nice. That's enough. Put your phone away.");
    speech.rate = 0.9;
    speech.onend = done;
    speech.onerror = done;
    speechSynthesis.speak(speech);
    setTimeout(done, 6000);
  });
}

async function showInfo() {
  try {
    const response = await fetch(`/api/${sessionId}/info`);
    const info = await response.json();
    if (info.title && info.description) {
      text.textContent = `${info.title}: ${info.description}`;
    }
  } catch (error) {
    console.log("No extra info", error);
  }
}

showLanding();
