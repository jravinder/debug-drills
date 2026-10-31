// Dashboard charts. Chart.js is loaded from cdnjs (pinned 4.4.1).
(function () {
  const ACCENT = "#1e40af";
  const GRID = "#eceff3";
  const TICK = "#4b5563";
  Chart.defaults.font.family = getComputedStyle(document.documentElement).fontFamily;
  Chart.defaults.color = TICK;

  const dollars = (cents) => "$" + Math.round(cents / 100).toLocaleString();

  // Category bar chart: server-rendered aggregate.
  const cats = JSON.parse(document.getElementById("categoryData").textContent);
  new Chart(document.getElementById("categoryChart"), {
    type: "bar",
    data: {
      labels: cats.map((c) => c.category),
      datasets: [{ data: cats.map((c) => c.revenue_cents / 100), backgroundColor: ACCENT, borderRadius: 4, barThickness: 12 }],
    },
    options: {
      indexAxis: "y",
      maintainAspectRatio: false,
      plugins: { legend: { display: false }, tooltip: { callbacks: { label: (c) => dollars(c.raw * 100) } } },
      scales: {
        x: { grid: { color: GRID }, ticks: { callback: (v) => "$" + (v >= 1000 ? Math.round(v / 1000) + "k" : v) } },
        y: { grid: { display: false }, ticks: { autoSkip: false, font: { size: 11 } } },
      },
    },
  });

  // Daily revenue line chart: bucket sale lines by day.
  const canvas = document.getElementById("revenueChart");
  const tenant = canvas.dataset.tenant;
  const days = Number(canvas.dataset.days);

  fetch(`/api/t/${tenant}/revenue-series?days=${days}`)
    .then((r) => r.json())
    .then((payload) => {
      const byDay = new Map();
      for (const line of payload.lines) {
        const day = line.sold_at.slice(0, 10);
        const net = line.qty * line.unit_price_cents - line.discount_cents;
        byDay.set(day, (byDay.get(day) || 0) + net);
      }
      const labels = [];
      const values = [];
      const today = new Date();
      for (let i = days; i >= 1; i--) {
        const d = new Date(today.getFullYear(), today.getMonth(), today.getDate() - i);
        const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
        labels.push(key.slice(5));
        values.push((byDay.get(key) || 0) / 100);
      }
      document.getElementById("revenueLoading").remove();
      new Chart(canvas, {
        type: "line",
        data: {
          labels,
          datasets: [{ data: values, borderColor: ACCENT, backgroundColor: "rgba(30,64,175,0.08)", fill: true, tension: 0.25, pointRadius: 0, borderWidth: 2 }],
        },
        options: {
          maintainAspectRatio: false,
          interaction: { mode: "index", intersect: false },
          plugins: { legend: { display: false }, tooltip: { callbacks: { label: (c) => dollars(c.raw * 100) } } },
          scales: {
            x: { grid: { display: false }, ticks: { maxTicksLimit: 9, autoSkip: true } },
            y: { grid: { color: GRID }, ticks: { callback: (v) => "$" + (v >= 1000 ? Math.round(v / 1000) + "k" : v) } },
          },
        },
      });
    })
    .catch(() => {
      document.getElementById("revenueLoading").textContent = "Could not load revenue.";
    });
})();
