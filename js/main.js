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
      fetch("charts/04_listings_by_state.json"),
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

function renderAlluvialChart() {
  const container = document.getElementById("chart-12");

  if (!container || typeof d3 === "undefined" || typeof d3.sankey === "undefined") {
    console.error("Could not render alluvial chart: D3 or the Sankey extension is unavailable.");
    return;
  }

  d3.csv("data/funding_alluvial_links.csv", (row) => ({
    ...row,
    value: Number(row.value)
  }))
    .then((rawRows) => {
      const excludedStates = new Set(["Multiple states", "ACT/NSW/VIC"]);
      const rows = rawRows.filter((row) => (
        !excludedStates.has(row.source_label) && !excludedStates.has(row.target_label)
      ));
      container.replaceChildren();

      const width = Math.max(container.clientWidth, 780);
      const height = 560;
      const margin = { top: 52, right: 210, bottom: 30, left: 165 };

      const nodeMap = new Map();
      rows.forEach((row) => {
        if (!nodeMap.has(row.source)) {
          nodeMap.set(row.source, {
            id: row.source,
            label: row.source_label,
            kind: row.source.split("|")[0]
          });
        }
        if (!nodeMap.has(row.target)) {
          nodeMap.set(row.target, {
            id: row.target,
            label: row.target_label,
            kind: row.target.split("|")[0]
          });
        }
      });

      const graph = {
        nodes: Array.from(nodeMap.values()),
        links: rows.map((row) => ({
          source: row.source,
          target: row.target,
          value: row.value,
          linkType: row.link_type
        }))
      };

      const sankeyLayout = d3.sankey()
        .nodeId((node) => node.id)
        .nodeWidth(18)
        .nodePadding(10)
        .nodeAlign(d3.sankeyJustify)
        .extent([
          [margin.left, margin.top],
          [width - margin.right, height - margin.bottom]
        ]);

      sankeyLayout(graph);

      const stateColors = {
        ACT: "#5B6770",
        NSW: "#2F6B8F",
        NT: "#C2643F",
        QLD: "#4F8A63",
        SA: "#B28A3E",
        TAS: "#6E5B95",
        VIC: "#A14F6B",
        WA: "#3C7A78",
        "Multiple states": "#8B6F47",
        "ACT/NSW/VIC": "#8B6F47"
      };

      const svg = d3.select(container)
        .append("svg")
        .attr("class", "alluvial-svg")
        .attr("viewBox", `0 0 ${width} ${height}`)
        .attr("role", "img")
        .attr("aria-label", "Alluvial diagram showing grant funding flows from funding rounds to states and project types.");

      d3.select(container).classed("alluvial-container", true);
      const tooltip = d3.select(container)
        .append("div")
        .attr("class", "alluvial-tooltip");

      const showTooltip = (event, html) => {
        const bounds = container.getBoundingClientRect();
        tooltip
          .html(html)
          .style("left", `${event.clientX - bounds.left + 12}px`)
          .style("top", `${event.clientY - bounds.top + 12}px`)
          .style("opacity", 1);
      };

      const hideTooltip = () => tooltip.style("opacity", 0);

      svg.append("text")
        .attr("x", margin.left)
        .attr("y", 16)
        .attr("fill", "#666A64")
        .attr("font-size", 12)
        .text("Flow width represents total grant funding (AUD, including GST where available)");

      svg.append("g")
        .attr("fill", "none")
        .selectAll("path")
        .data(graph.links.slice().sort((a, b) => b.width - a.width))
        .join("path")
        .attr("d", d3.sankeyLinkHorizontal())
        .attr("stroke", (link) => {
          const stateLabel = link.linkType === "round-to-state"
            ? link.target.label
            : link.source.label;
          return stateColors[stateLabel] || "#9AA39D";
        })
        .attr("stroke-width", (link) => Math.max(1, link.width))
        .attr("stroke-opacity", 0.38)
        .append("title")
        .text((link) => `${link.source.label} → ${link.target.label}: $${d3.format(",.0f")(link.value)}`);

      svg.selectAll("path")
        .on("mouseover", (event, link) => {
          showTooltip(event, `<strong>${link.source.label} to ${link.target.label}</strong><br>Funding: $${d3.format(",.0f")(link.value)}`);
        })
        .on("mousemove", (event, link) => {
          showTooltip(event, `<strong>${link.source.label} to ${link.target.label}</strong><br>Funding: $${d3.format(",.0f")(link.value)}`);
        })
        .on("mouseout", hideTooltip);

      const nodes = svg.append("g")
        .selectAll("g")
        .data(graph.nodes)
        .join("g");

      nodes.append("rect")
        .attr("x", (node) => node.x0)
        .attr("y", (node) => node.y0)
        .attr("height", (node) => Math.max(1, node.y1 - node.y0))
        .attr("width", (node) => node.x1 - node.x0)
        .attr("fill", (node) => {
          if (node.kind === "state") return stateColors[node.label] || "#6C6D68";
          if (node.kind === "type") return "#23483D";
          return "#23483D";
        })
        .attr("rx", 2)
        .append("title")
        .text((node) => `${node.label}: $${d3.format(",.0f")(node.value)}`);

      nodes.selectAll("rect")
        .on("mouseover", (event, node) => {
          showTooltip(event, `<strong>${node.label}</strong><br>Total funding: $${d3.format(",.0f")(node.value)}`);
        })
        .on("mousemove", (event, node) => {
          showTooltip(event, `<strong>${node.label}</strong><br>Total funding: $${d3.format(",.0f")(node.value)}`);
        })
        .on("mouseout", hideTooltip);

      svg.append("text")
        .attr("x", margin.left + 9)
        .attr("y", 42)
        .attr("text-anchor", "middle")
        .attr("fill", "#23483D")
        .attr("font-size", 14)
        .attr("font-weight", 700)
        .text("Funding rounds");

      svg.append("text")
        .attr("x", width - margin.right - 9)
        .attr("y", 42)
        .attr("text-anchor", "middle")
        .attr("fill", "#23483D")
        .attr("font-size", 14)
        .attr("font-weight", 700)
        .text("Project types");

      nodes.append("text")
        .attr("x", (node) => node.kind === "round" ? node.x0 - 8 : node.x1 + 8)
        .attr("y", (node) => (node.y0 + node.y1) / 2)
        .attr("dy", "0.35em")
        .attr("text-anchor", (node) => node.kind === "round" ? "end" : "start")
        .attr("fill", "#292C29")
        .attr("font-size", 11)
        .text((node) => node.label);
    })
    .catch((error) => {
      console.error("Could not render alluvial chart:", error);
    });
}

function renderFundingHexbin() {
  const container = document.getElementById("chart-14");
  if (!container || typeof d3 === "undefined") return;

  Promise.all([
    d3.json("data/heritage_funding_polygons_simplified.geojson"),
    d3.json("data/australian-states.json")
  ]).then(([fundingGeoJson, stateGeoJson]) => {
    const width = Math.max(container.clientWidth, 760);
    const height = 540;
    const radius = 13;
    const sqrt3 = Math.sqrt(3);
    const projection = d3.geoMercator().fitExtent([[30, 45], [width - 30, height - 40]], stateGeoJson);
    const path = d3.geoPath(projection);
    const points = fundingGeoJson.features
      .filter((feature) => feature.properties.STATE !== "EXT" && Number(feature.properties.total_funding) > 0)
      .map((feature) => ({
        point: path.centroid(feature),
        name: feature.properties.NAME,
        state: feature.properties.STATE,
        funding: Number(feature.properties.total_funding)
      }))
      .filter((entry) => Number.isFinite(entry.point[0]) && Number.isFinite(entry.point[1]));
    const bins = new Map();
    points.forEach((entry) => {
      const column = Math.round(entry.point[0] / (radius * 1.5));
      const row = Math.round((entry.point[1] - (column % 2) * radius * sqrt3 / 2) / (radius * sqrt3));
      const key = `${column},${row}`;
      if (!bins.has(key)) bins.set(key, { column, row, funding: 0, places: [] });
      bins.get(key).funding += entry.funding;
      bins.get(key).places.push(entry);
    });
    const maxFunding = d3.max(Array.from(bins.values()), (bin) => bin.funding) || 1;
    const color = d3.scaleSequential(d3.interpolateYlGn).domain([0, maxFunding]);

    container.replaceChildren();
    const svg = d3.select(container).append("svg")
      .attr("class", "cartogram-svg")
      .attr("viewBox", `0 0 ${width} ${height}`)
      .attr("role", "img")
      .attr("aria-label", "Hexagonal bin map showing total conservation grant funding in local areas of Australia.");

    svg.append("text").attr("x", 20).attr("y", 24).attr("class", "cartogram-note")
      .text("Each hexagon contains the total recorded grant funding assigned to nearby heritage sites.");
    svg.append("g").selectAll("path").data(stateGeoJson.features).join("path")
      .attr("d", path).attr("class", "hexbin-boundary");

    const tooltip = d3.select(container).append("div").attr("class", "cartogram-tooltip");
    const showTooltip = (event, bin) => {
      const bounds = container.getBoundingClientRect();
      const states = Array.from(new Set(bin.places.map((place) => place.state))).join(", ");
      const names = bin.places.map((place) => place.name).slice(0, 3).join("<br>");
      tooltip.html(`<strong>$${d3.format(",.0f")(bin.funding)} funding</strong><br>${bin.places.length} funded site${bin.places.length === 1 ? "" : "s"}<br>State / territory: ${states || "Australia"}<br>${names}`)
        .style("left", `${event.clientX - bounds.left + 12}px`)
        .style("top", `${event.clientY - bounds.top + 12}px`)
        .style("opacity", 1);
    };
    const hexPath = `M 0,-${radius} L ${radius * 0.866},-${radius / 2} L ${radius * 0.866},${radius / 2} L 0,${radius} L -${radius * 0.866},${radius / 2} L -${radius * 0.866},-${radius / 2} Z`;
    svg.append("g").selectAll("g").data(Array.from(bins.values())).join("g")
      .attr("class", "cartogram-cell")
      .attr("transform", (bin) => `translate(${bin.column * radius * 1.5},${bin.row * radius * sqrt3 + (bin.column % 2) * radius * sqrt3 / 2})`)
      .on("mouseenter", showTooltip).on("mousemove", showTooltip)
      .on("mouseleave", () => tooltip.style("opacity", 0))
      .append("path").attr("d", hexPath)
      .attr("fill", (bin) => color(bin.funding))
      .attr("stroke", "#23483D").attr("stroke-width", 0.8);

    const legend = svg.append("g").attr("transform", `translate(${width - 245},${height - 34})`);
    legend.append("text").attr("class", "cartogram-legend-title").text("Funding per hexagon (AUD)");
    [0, Math.ceil(maxFunding / 2), maxFunding].forEach((value, index) => {
      const x = index * 65;
      legend.append("rect").attr("x", x).attr("y", 10).attr("width", 55).attr("height", 12).attr("fill", color(value));
      legend.append("text").attr("x", x).attr("y", 38).attr("class", "cartogram-legend-label").text(d3.format("~s")(value));
    });
  }).catch((error) => console.error("Could not render funding hexbin map:", error));
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
    "chart-10",
    "charts/10_listings_change_by_state.json"
  );

  renderListingsChoropleth();

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
    "chart-14",
    "charts/14_heritage_class_dot_map.json"
  );

  renderChart(
    "chart-15",
    "charts/15_heritage_area_symbol_map.json"
  );

renderChart(
    "chart-09", 
    "charts/09_grant_projects_map.json"
);

  renderAlluvialChart();

  renderChart(
    "chart-13",
    "charts/13_funding_vs_listings.json"
  );

  console.log("Heritage Conservation website loaded.");
});
