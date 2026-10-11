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
  clearTimeout(timer);
  sessionId = null;
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
  if ("Notification" in window) await Notification.requestPermission();

  try {
    const data = await post(`/api/start?minutes=${minutes}`);
    sessionId = data.id;
    const challengePromise = post(`/api/${sessionId}/challenge`).catch((error) => ({ error }));
    setVisible(settings, false);
    setVisible(startBtn, false);
    show("Okay.", `Keep working. We'll check in after ${minutes} minute(s).`);

    timer = setTimeout(() => nudge(challengePromise), data.idle_seconds * 1000);
  } catch (error) {
    show("Something went wrong.", error.detail || "");
  }
};

async function nudge(challengePromise) {
  const message = "You've been looking down for a while.";
  if ("Notification" in window && Notification.permission === "granted") {
    new Notification("Step Outside", { body: message });
  }
  const result = await challengePromise;
  if (result.error) {
    show(message, result.error.detail || "Could not get a challenge. Please start again.");
    setVisible(againBtn, true);
    return;
  }
  const data = result;
  show(message, data.challenge);
  setVisible(photoBtn, true);
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
