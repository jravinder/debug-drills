(function () {
  const series = JSON.parse(document.getElementById("seriesData").textContent);
  Chart.defaults.font.family = getComputedStyle(document.documentElement).fontFamily;
  Chart.defaults.color = "#4b5563";
  new Chart(document.getElementById("storeChart"), {
    type: "bar",
    data: {
      labels: series.map((p) => p.day.slice(5)),
      datasets: [{ data: series.map((p) => p.revenue_cents / 100), backgroundColor: "#1e40af", borderRadius: 3 }],
    },
    options: {
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: { x: { grid: { display: false }, ticks: { maxTicksLimit: 10 } }, y: { grid: { color: "#eceff3" } } },
    },
  });
})();
