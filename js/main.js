const chartContainers = [
  "chart-01",
  "chart-02",
  "chart-03",
  "chart-04",
  "chart-05",
  "chart-06",
  "chart-07",
  "chart-08",
  "chart-09",
  "chart-10",
  "chart-11",
  'chart-12'
];

function checkChartContainers() {
  chartContainers.forEach((chartId) => {
    if (!document.getElementById(chartId)) {
      console.warn(`Chart container not found: ${chartId}`);
    }
  });
}

function renderChart(containerId, specPath) {
  vegaEmbed(`#${containerId}`, specPath, {
    actions: false,
    renderer: "svg"
  }).catch((error) => {
    console.error(`Could not render ${containerId}:`, error);
  });
}

document.addEventListener("DOMContentLoaded", () => {
  checkChartContainers();

  renderChart(
    "chart-01",
    "charts/01_listings_over_time.json"
  );

  renderChart(
  "chart-02",
  "charts/02_heritage_class.json"
);

  renderChart(
  "chart-03",
  "charts/03_listing_status.json"
);

  renderChart(
  "chart-04",
  "charts/04_listings_by_state.json"
);

  renderChart(
  "chart-05",
  "charts/05_grants_over_time.json"
);

  renderChart(
    "chart-06", 
    "charts/06_funding_by_state.json"
);

  renderChart(
    "chart-07", 
    "charts/07_funding_heatmap.json"
);

  renderChart(
    "chart-08", 
    "charts/08_prop_symbol_map.json"
);

renderChart(
    "chart-09", 
    "charts/09_grant_projects_map.json"
);

renderChart(
    "chart-12", 
    "charts/12_funding_by_heritage_type.json"
);

  console.log("Heritage Conservation website loaded.");
});
