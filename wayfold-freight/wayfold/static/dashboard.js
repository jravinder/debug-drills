// Dashboard charts. Chart.js is loaded from cdnjs (pinned 4.4.1).
(function () {
  const ACCENT = "#1d3fa8";
  const GRID = "#eceff3";
  const TICK = "#4b5563";
  Chart.defaults.font.family = getComputedStyle(document.documentElement).fontFamily;
  Chart.defaults.color = TICK;

  const regions = JSON.parse(document.getElementById("regionData").textContent);
  new Chart(document.getElementById("regionChart"), {
    type: "bar",
    data: {
      labels: regions.map((r) => r.region),
      datasets: [{ data: regions.map((r) => r.stops), backgroundColor: ACCENT, borderRadius: 4, barThickness: 12 }],
    },
    options: {
      indexAxis: "y",
      maintainAspectRatio: false,
      plugins: { legend: { display: false }, tooltip: { callbacks: { label: (c) => c.raw.toLocaleString() + " stops" } } },
      scales: {
        x: { grid: { color: GRID }, ticks: { callback: (v) => (v >= 10000 ? Math.round(v / 1000) + "k" : v.toLocaleString()) } },
        y: { grid: { display: false }, ticks: { autoSkip: false, font: { size: 11 } } },
      },
    },
  });

  const canvas = document.getElementById("onTimeChart");
  fetch(`/api/t/${canvas.dataset.tenant}/on-time-series?days=${canvas.dataset.days}`)
    .then((r) => r.json())
    .then((payload) => {
      document.getElementById("onTimeLoading").remove();
      new Chart(canvas, {
        type: "line",
        data: {
          labels: payload.points.map((p) => p.day.slice(5)),
          datasets: [{ data: payload.points.map((p) => p.on_time_pct), borderColor: ACCENT, backgroundColor: "rgba(29,63,168,0.08)", fill: true, tension: 0.25, pointRadius: 0, borderWidth: 2 }],
        },
        options: {
          maintainAspectRatio: false,
          interaction: { mode: "index", intersect: false },
          plugins: { legend: { display: false }, tooltip: { callbacks: { label: (c) => c.raw.toFixed(1) + "% on time" } } },
          scales: {
            x: { grid: { display: false }, ticks: { maxTicksLimit: 9, autoSkip: true } },
            y: { grid: { color: GRID }, suggestedMin: 50, suggestedMax: 100, ticks: { callback: (v) => v + "%" } },
          },
        },
      });
    })
    .catch(() => {
      document.getElementById("onTimeLoading").textContent = "Could not load on-time series.";
    });
})();
