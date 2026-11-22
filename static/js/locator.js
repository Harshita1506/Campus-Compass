/* Campus locator: Leaflet + OpenStreetMap + Django JSON search API. */
(function () {
  "use strict";
  const el = document.getElementById("campus-map");
  if (!el || typeof L === "undefined") return;

  const map = L.map(el).setView([parseFloat(el.dataset.lat), parseFloat(el.dataset.lng)], parseInt(el.dataset.zoom, 10));
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19, attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
  }).addTo(map);

  const COLORS = { academic: "#4f46e5", lab: "#7c3aed", library: "#2563eb", cafeteria: "#f59e0b", admin: "#13144a",
    hostel: "#10b981", sports: "#ef4444", auditorium: "#db2777", other: "#6b7280" };
  const markers = {};
  const esc = window.CC.escape;

  function icon(type) {
    const c = COLORS[type] || COLORS.other;
    return L.divIcon({ className: "", iconSize: [30, 30], iconAnchor: [15, 30], popupAnchor: [0, -28],
      html: '<div style="background:' + c + ';width:30px;height:30px;border-radius:50% 50% 50% 0;transform:rotate(-45deg);border:3px solid #fff;box-shadow:0 4px 10px rgba(0,0,0,.25)"></div>' });
  }

  function buildingPopup(b, room) {
    let html = '<div style="min-width:200px"><div class="fw-bold">' + esc(b.name) + ' <span class="text-muted">(' + esc(b.code) + ')</span></div>';
    if (b.type_label) html += '<div class="small text-muted mb-1">' + esc(b.type_label) + (b.floors ? " · " + b.floors + " floors" : "") + "</div>";
    if (room) {
      html += '<hr class="my-2"><div class="fw-semibold">Room ' + esc(room.room_number) + (room.name ? " — " + esc(room.name) : "") + "</div>" +
        '<div class="small">' + esc(room.floor_label) + " · " + esc(room.type_label) + "</div>" +
        (room.department ? '<div class="small">Dept: ' + esc(room.department) + "</div>" : "") +
        (room.faculty ? '<div class="small">Faculty: ' + esc(room.faculty) + "</div>" : "");
    } else {
      if (b.description) html += '<div class="small">' + esc(b.description) + "</div>";
      if (b.hours) html += '<div class="small mt-1"><i class="bi bi-clock"></i> ' + esc(b.hours) + "</div>";
      if (b.departments && b.departments.length) html += '<div class="small mt-1">Departments: ' + b.departments.map(esc).join(", ") + "</div>";
    }
    if (b.is_demo) html += '<div class="badge text-bg-warning mt-2">Demo location</div>';
    return html + "</div>";
  }

  function focusBuilding(b, room) {
    const m = markers[b.id];
    map.flyTo([b.lat, b.lng], Math.max(map.getZoom(), 18), { duration: .6 });
    if (m) m.setPopupContent(buildingPopup(b, room)).openPopup();
  }

  const buildingCache = {};
  window.CC.getJSON(el.dataset.buildingsUrl).then(data => {
    const group = [];
    data.buildings.forEach(b => {
      buildingCache[b.id] = b;
      markers[b.id] = L.marker([b.lat, b.lng], { icon: icon(b.type), title: b.name }).addTo(map).bindPopup(buildingPopup(b));
      group.push([b.lat, b.lng]);
    });
    if (group.length) map.fitBounds(group, { padding: [40, 40], maxZoom: 18 });
    renderBuildings(data.buildings, "All campus buildings");
  });

  const results = document.getElementById("locator-results");
  const counter = document.getElementById("locator-count");

  function renderBuildings(list, heading) {
    results.innerHTML = '<div class="small text-muted fw-semibold mb-2">' + esc(heading) + "</div>" + list.map(b =>
      '<div class="result-item" data-building="' + b.id + '"><div class="d-flex justify-content-between"><span class="fw-semibold">' +
      esc(b.name) + '</span><span class="chip chip-muted">' + esc(b.code) + '</span></div><div class="small text-muted">' + esc(b.type_label) + "</div></div>").join("");
  }

  function render(data) {
    const total = data.rooms.length + data.buildings.length;
    counter.textContent = total;
    if (!total) { results.innerHTML = '<div class="empty-state"><i class="bi bi-geo"></i>No matching places. Try a room number, faculty name or department.</div>'; return; }
    let html = "";
    if (data.rooms.length) {
      html += '<div class="small text-muted fw-semibold mb-2">Rooms & cabins</div>' + data.rooms.map((r, i) =>
        '<div class="result-item" data-room="' + i + '"><div class="d-flex justify-content-between"><span class="fw-semibold">' +
        esc(r.building.code) + "-" + esc(r.room_number) + (r.name ? " · " + esc(r.name) : "") + '</span><span class="chip">' + esc(r.type_label) +
        '</span></div><div class="small text-muted">' + esc(r.building.name) + " · " + esc(r.floor_label) +
        (r.department ? " · " + esc(r.department) : "") + "</div>" + (r.faculty ? '<div class="small"><i class="bi bi-person-badge"></i> ' + esc(r.faculty) + "</div>" : "") + "</div>").join("");
    }
    if (data.buildings.length) {
      html += '<div class="small text-muted fw-semibold my-2">Buildings</div>' + data.buildings.map(b =>
        '<div class="result-item" data-building="' + b.id + '"><div class="fw-semibold">' + esc(b.name) + '</div><div class="small text-muted">' + esc(b.type_label) + "</div></div>").join("");
    }
    results.innerHTML = html;
    results._rooms = data.rooms;
  }

  results.addEventListener("click", e => {
    const item = e.target.closest(".result-item"); if (!item) return;
    results.querySelectorAll(".result-item").forEach(x => x.classList.remove("active")); item.classList.add("active");
    if (item.dataset.room !== undefined) {
      const r = results._rooms[parseInt(item.dataset.room, 10)];
      focusBuilding(Object.assign({}, buildingCache[r.building.id] || r.building), r);
    } else { focusBuilding(buildingCache[item.dataset.building]); }
  });

  const form = document.getElementById("locator-form");
  const run = async () => {
    const params = window.CC.serializeForm(form);
    if (!params.toString()) { renderBuildings(Object.values(buildingCache), "All campus buildings"); counter.textContent = Object.keys(buildingCache).length; return; }
    try { render(await window.CC.getJSON(form.dataset.searchUrl + "?" + params.toString())); }
    catch (err) { window.CC.toast("Search failed", "danger"); }
  };
  form.addEventListener("input", window.CC.debounce(run, 250));
  form.addEventListener("change", run);
  form.addEventListener("submit", e => { e.preventDefault(); run(); });
  document.querySelectorAll("[data-quick]").forEach(btn => btn.addEventListener("click", () => {
    form.querySelector("[name=q]").value = ""; form.querySelector("[name=type]").value = btn.dataset.quick; run();
  }));
})();
