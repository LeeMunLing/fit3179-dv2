const chartContainers = [
  "chart-01",
  "chart-02",
  "chart-03",
  "chart-04",
  "chart-05",
  "chart-06",
  "chart-07",
  "chart-09",
  "chart-10",
  'chart-12',
  "chart-14",
  "chart-15"
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

async function renderListingsChoropleth() {
  try {
    const [specResponse, rows] = await Promise.all([
      fetch("charts/05_choropleth_map_listings_by_state.json"),
      d3.csv("data/au-national-heritage-list-places_2026-02-26.csv")
    ]);
    const spec = await specResponse.json();
    const states = ["ACT", "NSW", "NT", "QLD", "SA", "TAS", "VIC", "WA"];
    const validRows = rows.filter((row) => (
      states.includes(row.state) && /^\d{4}-/.test(row.register_date)
    ));
    const values = [];

    for (let year = 2004; year <= 2026; year += 1) {
      states.forEach((state) => {
        const count = validRows.filter((row) => (
          row.state === state && Number(row.register_date.slice(0, 4)) <= year
        )).length;
        values.push({ state_year: `${state}_${year}`, count });
      });
    }

    const lookupTransform = spec.layer[0].transform.find((transform) => transform.lookup === "state_year");
    lookupTransform.from.data.values = values;

    vegaEmbed("#chart-04", spec, {
      actions: false,
      renderer: "svg"
    }).catch((error) => console.error("Could not render chart-04:", error));
  } catch (error) {
    console.error("Could not prepare chart-04:", error);
  }
}


document.addEventListener("DOMContentLoaded", () => {
  checkChartContainers();

  renderChart(
    "chart-01",
    "charts/01_line_chart_listings_over_time.json"
  );

  renderChart(
  "chart-02",
  "charts/02_pie_chart_heritage_class.json"
);

  renderChart(
  "chart-03",
  "charts/03_waffle_chart_listing_status.json"
);

  renderChart(
    "chart-10",
    "charts/04_slope_chart_listings_change_by_state.json"
  );

  renderListingsChoropleth();

  renderChart(
  "chart-05",
  "charts/08_line_chart_grants_over_time.json"
);

  renderChart(
    "chart-06", 
    "charts/09_connected_dot_plot_funding_by_state.json"
);

  renderChart(
    "chart-07", 
    "charts/10_heatmap_funding_by_state_year.json"
);

  renderChart(
    "chart-14",
    "charts/06_dot_map_heritage_class.json"
  );

  renderChart(
    "chart-15",
    "charts/07_proportional_symbol_map_heritage_area.json"
  );

renderChart(
    "chart-09", 
    "charts/13_choropleth_map_funded_sites.json"
);

  renderAlluvialChart();

  renderChart(
    "chart-13",
    "charts/11_scatter_plot_funding_vs_listings.json"
  );

  console.log("Heritage Conservation website loaded.");
});
