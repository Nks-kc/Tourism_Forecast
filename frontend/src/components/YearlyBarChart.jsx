import { useRef, useEffect } from "react";
import { Chart, registerables } from "chart.js";
import { getChartTheme, tooltipConfig, scaleConfig } from "../lib/chartTheme";

Chart.register(...registerables);

export default function YearlyBarChart({ records, theme = "dark", emptyText = "No yearly data available" }) {
  const canvasRef = useRef(null);
  const chartRef = useRef(null);

  useEffect(() => {
    if (!canvasRef.current) return;

    if (chartRef.current) {
      chartRef.current.destroy();
      chartRef.current = null;
    }

    if (!records || !records.length) return;

    const t = getChartTheme(theme);
    const byYear = {};
    for (const r of records) {
      byYear[r.year] = (byYear[r.year] || 0) + r.arrivals;
    }

    const years = Object.keys(byYear).sort();
    const totals = years.map((y) => byYear[y]);
    const maxVal = Math.max(...totals);

    const tealBase = theme === "light" ? [42, 138, 106] : [80, 184, 152];
    const bgColors = totals.map((v) => {
      const ratio = v / maxVal;
      const alpha = 0.3 + ratio * 0.5;
      return `rgba(${tealBase.join(",")}, ${alpha})`;
    });
    const hoverColors = totals.map((v) => {
      const ratio = v / maxVal;
      const alpha = 0.5 + ratio * 0.4;
      return `rgba(${tealBase.join(",")}, ${alpha})`;
    });

    chartRef.current = new Chart(canvasRef.current, {
      type: "bar",
      data: {
        labels: years,
        datasets: [{
          label: "Total Arrivals",
          data: totals,
          backgroundColor: bgColors,
          hoverBackgroundColor: hoverColors,
          borderColor: `rgba(${tealBase.join(",")}, 0.35)`,
          borderWidth: 1,
          borderRadius: 5,
          borderSkipped: false,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            ...tooltipConfig(t),
            callbacks: {
              label: (ctx) => ` Total: ${ctx.parsed.y.toLocaleString()} arrivals`,
            },
          },
        },
        scales: {
          x: { grid: { display: false }, ticks: { color: t.tick, font: { family: "'JetBrains Mono', monospace", size: 10 } } },
          y: scaleConfig(t).y,
        },
        animation: { duration: 800, easing: "easeOutCubic" },
      },
    });

    return () => {
      if (chartRef.current) { chartRef.current.destroy(); chartRef.current = null; }
    };
  }, [records, theme]);

  if (!records || !records.length) {
    return <div className="empty chart-empty">{emptyText}</div>;
  }

  return (
    <div className="chart-wrap" style={{ height: 300 }}>
      <canvas ref={canvasRef} />
    </div>
  );
}
