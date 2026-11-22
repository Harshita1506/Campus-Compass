/* One-to-one chat with AJAX polling. */
(function () {
  "use strict";
  const box = document.getElementById("chat-box");
  if (!box) return;
  const form = document.getElementById("chat-form");
  const input = form.querySelector("textarea");
  let lastId = parseInt(box.dataset.lastId || "0", 10);
  const esc = window.CC.escape;

  function append(m) {
    if (m.id <= lastId && box.querySelector('[data-id="' + m.id + '"]')) return;
    const div = document.createElement("div");
    div.className = "bubble " + (m.mine ? "mine" : "theirs");
    div.dataset.id = m.id;
    div.innerHTML = esc(m.body) + '<div class="meta">' + esc(m.time) + "</div>";
    box.appendChild(div);
    lastId = Math.max(lastId, m.id);
  }
  const scroll = () => { box.scrollTop = box.scrollHeight; };
  scroll();

  async function poll() {
    try {
      const data = await window.CC.getJSON(box.dataset.pollUrl + "?after=" + lastId);
      if (data.messages.length) { data.messages.forEach(append); scroll(); }
    } catch (e) { /* ignore transient errors */ }
  }
  setInterval(poll, 3000);

  form.addEventListener("submit", async e => {
    e.preventDefault();
    const body = input.value.trim(); if (!body) return;
    input.value = ""; input.focus();
    try { const data = await window.CC.post(box.dataset.sendUrl, { body: body }, true); append(data.message); scroll(); }
    catch (err) { input.value = body; window.CC.toast("Message not sent", "danger"); }
  });
  input.addEventListener("keydown", e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); form.requestSubmit(); } });
})();
