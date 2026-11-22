/* Campus Compass — shared front-end helpers (Fetch API + CSRF). */
(function () {
  "use strict";

  function getCookie(name) {
    const match = document.cookie.split(";").map(c => c.trim()).find(c => c.startsWith(name + "="));
    return match ? decodeURIComponent(match.split("=")[1]) : null;
  }

  const CC = (window.CC = window.CC || {});
  CC.csrf = () => getCookie("csrftoken") || (document.querySelector("[name=csrfmiddlewaretoken]") || {}).value;

  CC.debounce = function (fn, wait) {
    let t; return function (...args) { clearTimeout(t); t = setTimeout(() => fn.apply(this, args), wait || 300); };
  };

  CC.getJSON = async function (url) {
    const res = await fetch(url, { headers: { "X-Requested-With": "XMLHttpRequest", "Accept": "application/json" }, credentials: "same-origin" });
    if (!res.ok) throw new Error("Request failed: " + res.status);
    return res.json();
  };

  CC.post = async function (url, data, asJSON) {
    const headers = { "X-CSRFToken": CC.csrf(), "X-Requested-With": "XMLHttpRequest", "Accept": "application/json" };
    let body;
    if (asJSON) { headers["Content-Type"] = "application/json"; body = JSON.stringify(data || {}); }
    else { body = new FormData(); Object.entries(data || {}).forEach(([k, v]) => body.append(k, v)); }
    const res = await fetch(url, { method: "POST", headers, body, credentials: "same-origin" });
    const json = await res.json().catch(() => ({}));
    if (!res.ok) { const err = new Error(json.error || "Request failed"); err.data = json; throw err; }
    return json;
  };

  CC.escape = function (str) {
    const d = document.createElement("div"); d.textContent = str == null ? "" : String(str); return d.innerHTML;
  };

  CC.toast = function (message, variant) {
    const wrap = document.getElementById("toast-area"); if (!wrap) return;
    const el = document.createElement("div");
    el.className = "toast align-items-center text-bg-" + (variant || "dark") + " border-0 show mb-2";
    el.setAttribute("role", "status");
    el.innerHTML = '<div class="d-flex"><div class="toast-body">' + CC.escape(message) + '</div><button type="button" class="btn-close btn-close-white me-2 m-auto" aria-label="Close"></button></div>';
    el.querySelector("button").onclick = () => el.remove();
    wrap.appendChild(el); setTimeout(() => el.remove(), 3500);
  };

  CC.serializeForm = function (form) {
    const params = new URLSearchParams();
    new FormData(form).forEach((v, k) => { if (v !== "" && k !== "csrfmiddlewaretoken") params.append(k, v); });
    return params;
  };

  /* Live filter: any form with data-live-url renders JSON.html into data-target. */
  CC.bindLiveFilter = function (form) {
    const target = document.querySelector(form.dataset.target);
    const counter = form.dataset.counter ? document.querySelector(form.dataset.counter) : null;
    const run = async () => {
      const params = CC.serializeForm(form);
      target.classList.add("spinner-overlay");
      try {
        const data = await CC.getJSON(form.dataset.liveUrl + "?" + params.toString());
        target.innerHTML = data.html;
        if (counter) counter.textContent = data.count;
        history.replaceState(null, "", "?" + params.toString());
        const pager = document.getElementById("pager"); if (pager) pager.remove();
      } catch (e) { CC.toast("Could not load results. Please retry.", "danger"); }
      finally { target.classList.remove("spinner-overlay"); }
    };
    const debounced = CC.debounce(run, 300);
    form.addEventListener("input", e => { if (e.target.matches("input[type=text], input[type=search], input[type=number]")) debounced(); });
    form.addEventListener("change", e => { if (e.target.matches("select, input[type=checkbox], input[type=radio]")) run(); });
    form.addEventListener("submit", e => { e.preventDefault(); run(); });
  };

  /* Toggle buttons (save / bookmark) — event delegation so AJAX-rendered cards work too. */
  document.addEventListener("click", async function (e) {
    const btn = e.target.closest("[data-toggle-save]");
    if (!btn) return;
    e.preventDefault(); e.stopPropagation();
    try {
      const data = await CC.post(btn.dataset.toggleSave);
      btn.classList.toggle("saved", data.saved);
      const icon = btn.querySelector(".bi");
      if (icon) icon.className = "bi " + (data.saved ? "bi-heart-fill" : "bi-heart");
      const label = btn.querySelector(".label"); if (label) label.textContent = data.saved ? "Saved" : "Save";
      CC.toast(data.saved ? "Saved to your list" : "Removed from saved", "dark");
    } catch (err) { CC.toast("Something went wrong.", "danger"); }
  });

  /* Status buttons: data-status-url + data-status */
  document.addEventListener("click", async function (e) {
    const btn = e.target.closest("[data-status-url]");
    if (!btn) return;
    e.preventDefault();
    if (btn.dataset.confirm && !window.confirm(btn.dataset.confirm)) return;
    try {
      const data = await CC.post(btn.dataset.statusUrl, { status: btn.dataset.status });
      document.querySelectorAll("[data-status-badge]").forEach(b => { b.textContent = data.label; b.className = "badge status-" + data.status; });
      CC.toast("Status updated: " + data.label, "success");
      if (btn.dataset.reload) setTimeout(() => location.reload(), 600);
    } catch (err) { CC.toast(err.message || "Could not update status.", "danger"); }
  });

  /* Notifications polling */
  function renderNotifications(data) {
    const badge = document.getElementById("notif-count");
    if (badge) { badge.textContent = data.unread; badge.classList.toggle("d-none", data.unread === 0); }
    const list = document.getElementById("notif-list");
    if (!list) return;
    if (!data.latest.length) { list.innerHTML = '<div class="text-center text-muted small py-4">You\'re all caught up ✨</div>'; return; }
    list.innerHTML = data.latest.map(n =>
      '<a class="dropdown-item notif-row ' + (n.is_read ? "" : "unread") + '" href="' + CC.escape(n.url) + '">' +
      '<i class="bi ' + CC.escape(n.icon) + ' text-primary fs-5"></i><div><div class="fw-semibold small">' + CC.escape(n.title) +
      '</div><div class="text-muted small">' + CC.escape(n.message).slice(0, 90) + '</div><div class="text-muted" style="font-size:.7rem">' +
      CC.escape(n.time) + '</div></div></a>').join("");
  }
  CC.refreshNotifications = async function () {
    if (!document.body.dataset.auth) return;
    try { renderNotifications(await CC.getJSON("/notifications/api/unread/")); } catch (e) { /* offline */ }
  };

  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("form[data-live-url]").forEach(CC.bindLiveFilter);
    if (document.body.dataset.auth) {
      CC.refreshNotifications();
      setInterval(CC.refreshNotifications, 20000);
      const markAll = document.getElementById("mark-all-read");
      if (markAll) markAll.addEventListener("click", async (e) => {
        e.preventDefault(); await CC.post("/notifications/api/read-all/"); CC.refreshNotifications();
        document.querySelectorAll(".notif-item.unread").forEach(el => el.classList.remove("unread"));
      });
    }
    document.querySelectorAll("[data-mark-read]").forEach(btn => btn.addEventListener("click", async (e) => {
      e.preventDefault();
      await CC.post(btn.dataset.markRead);
      const row = btn.closest(".notif-item"); if (row) row.classList.remove("unread");
      btn.remove(); CC.refreshNotifications();
    }));
    /* Respond buttons via AJAX (roommate requests) */
    document.querySelectorAll("[data-respond-url]").forEach(btn => btn.addEventListener("click", async (e) => {
      e.preventDefault();
      try {
        const data = await CC.post(btn.dataset.respondUrl);
        const row = btn.closest("[data-request-row]");
        if (row) row.querySelector("[data-request-status]").innerHTML = '<span class="badge status-' + data.status + '">' + CC.escape(data.label) + "</span>";
        row && row.querySelectorAll("[data-respond-url]").forEach(b => b.remove());
        CC.toast("Request " + data.label.toLowerCase(), "success");
      } catch (err) { CC.toast(err.message, "danger"); }
    }));
  });
})();
