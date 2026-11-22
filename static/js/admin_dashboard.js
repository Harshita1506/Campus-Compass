/* Admin dashboard charts — data loaded from the Django stats JSON API. */
(function () {
  "use strict";
  const root = document.getElementById("admin-charts");
  if (!root || typeof Chart === "undefined") return;
  Chart.defaults.font.family = '"Plus Jakarta Sans", system-ui, sans-serif';
  Chart.defaults.color = "#6b6f8e";
  const PALETTE = ["#4f46e5", "#8b5cf6", "#60a5fa", "#10b981", "#f59e0b", "#ef4444", "#ec4899", "#14b8a6", "#13144a"];
  const charts = {};

  function draw(id, type, payload, opts) {
    const ctx = document.getElementById(id); if (!ctx) return;
    if (charts[id]) charts[id].destroy();
    const isRound = type === "doughnut" || type === "pie";
    charts[id] = new Chart(ctx, {
      type: type,
      data: { labels: payload.labels, datasets: [{ label: opts.label || "Count", data: payload.data,
        backgroundColor: isRound ? PALETTE : (type === "line" ? "rgba(79,70,229,.12)" : (opts.color || "#4f46e5")), borderColor: opts.color || "#4f46e5",
        borderRadius: type === "bar" ? 8 : 0, tension: .35, fill: type === "line", borderWidth: isRound ? 0 : 2,
        pointRadius: type === "line" ? 3 : 0 }] },
      options: { responsive: true, maintainAspectRatio: false, indexAxis: opts.horizontal ? "y" : "x",
        plugins: { legend: { display: isRound, position: "bottom" } },
        scales: isRound ? {} : { y: { beginAtZero: true, ticks: { precision: 0 }, grid: { color: "#eef0f7" } }, x: { grid: { display: false } } },
        cutout: type === "doughnut" ? "65%" : undefined }
    });
  }

  async function load() {
    const data = await window.CC.getJSON(root.dataset.url + window.location.search);
    const c = data.charts;
    draw("chart-lostfound", "bar", c.lostfound, { label: "Items", color: "#4f46e5" });
    draw("chart-categories", "bar", c.products_by_category, { label: "Products", color: "#8b5cf6", horizontal: true });
    draw("chart-sold", "doughnut", c.available_vs_sold, {});
    draw("chart-registrations", "line", c.registrations, { label: "Registrations", color: "#4f46e5" });
    draw("chart-mentorship", "doughnut", c.mentorship_status, {});
    draw("chart-accommodation", "pie", c.accommodation, {});
  }
  load().catch(() => window.CC.toast("Could not load chart data", "danger"));
})();
