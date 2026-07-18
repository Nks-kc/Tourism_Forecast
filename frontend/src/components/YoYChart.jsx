import { useRef, useEffect } from "react";
import { Chart, registerables } from "chart.js";
import { getChartTheme, tooltipConfig, scaleConfig } from "../lib/chartTheme";

Chart.register(...registerables);

const MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

function generateTealShades(count, theme) {
  const baseH = 160;
  const baseSRange = [45, 55];
  const baseLRange = theme === "light" ? [30, 55] : [25, 65];

  return Array.from({ length: count }, (_, i) => {
    const ratio = count === 1 ? 0.7 : i / (count - 1);
    const s = baseSRange[0] + (baseSRange[1] - baseSRange[0]) * (0.5 + ratio * 0.5);
    const l = baseLRange[0] + (baseLRange[1] - baseLRange[0]) * ratio;
    return `hsl(${baseH}, ${s}%, ${l}%)`;
  });
}

export default function YoYChart({ records, theme = "dark", emptyText = "No data for year-over-year comparison" }) {
  const canvasRef = useRef(null);
  const chartRef = useRef(null);

  useEffect(() => {
    if (!canvasRef.current) return;

    if (chartRef.current) { chartRef.current.destroy(); chartRef.current = null; }

    if (!records || !records.length) return;

    const t = getChartTheme(theme);
    const byYear = {};
    for (const r of records) {
      if (!byYear[r.year]) byYear[r.year] = {};
      byYear[r.year][r.month] = r.arrivals;
    }

    const years = Object.keys(byYear).sort();
    const colors = generateTealShades(years.length, theme);

    const datasets = years.map((year, idx) => ({
      label: year,
      data: MONTH_LABELS.map((_, mIdx) => byYear[year][mIdx + 1] ?? null),
      borderColor: colors[idx],
      pointBackgroundColor: colors[idx],
      pointBorderColor: colors[idx],
      pointRadius: 3,
      pointHoverRadius: 6,
      borderWidth: years.length > 4 ? 1.5 : 2,
      tension: 0.35,
      spanGaps: false,
    }));

    chartRef.current = new Chart(canvasRef.current, {
      type: "line",
      data: { labels: MONTH_LABELS, datasets },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: "index", intersect: false },
        plugins: {
          legend: {
            position: "top",
            align: "end",
            labels: {
              color: t.legendText,
              font: { family: "'JetBrains Mono', monospace", size: 10 },
              boxWidth: 12, boxHeight: 2, padding: 12,
            },
          },
          tooltip: {
            ...tooltipConfig(t),
            callbacks: {
              label: (ctx) => ` ${ctx.dataset.label}: ${ctx.parsed.y?.toLocaleString() ?? "N/A"}`,
            },
          },
        },
        scales: scaleConfig(t),
        animation: { duration: 900, easing: "easeOutCubic" },
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
