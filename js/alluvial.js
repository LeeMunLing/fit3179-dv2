function renderAlluvialChart() {
  const container = document.getElementById("chart-12");

  if (!container || typeof d3 === "undefined" || typeof d3.sankey === "undefined") {
    console.error("Could not render alluvial chart: D3 or the Sankey extension is unavailable.");
    return;
  }

  d3.json("charts/12_alluvial_diagram_funding_projects.json")
    .then((config) => d3.csv(config.data.url, (row) => ({
      ...row,
      value: Number(row.value)
    })))
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
        .text("Flow width represents total grant funding (AUD)");

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
