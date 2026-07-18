import { useRef, useEffect } from "react";
import { Chart, registerables } from "chart.js";
import { seasonColors, seasonLabels } from "../lib/format";
import { getChartTheme, tooltipConfig } from "../lib/chartTheme";

Chart.register(...registerables);

export default function SeasonalDonutChart({ seasonAverage, theme = "dark", emptyText = "No seasonal data" }) {
  const canvasRef = useRef(null);
  const chartRef = useRef(null);

  useEffect(() => {
    if (!canvasRef.current) return;

    if (chartRef.current) { chartRef.current.destroy(); chartRef.current = null; }

    if (!seasonAverage || !seasonAverage.length) return;

    const t = getChartTheme(theme);
    const labels = seasonAverage.map((s) => seasonLabels[s.season] || s.season);
    const data = seasonAverage.map((s) => Math.round(s.average_arrivals));
    const bgColors = seasonAverage.map((s) => seasonColors[s.season] || "#6b6966");

    chartRef.current = new Chart(canvasRef.current, {
      type: "doughnut",
      data: {
        labels,
        datasets: [{
          data,
          backgroundColor: bgColors,
          borderColor: t.donutBorder,
          borderWidth: 2,
          hoverOffset: 6,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: "62%",
        plugins: {
          legend: {
            position: "right",
            labels: {
              color: t.legendText,
              font: { family: "'Inter', sans-serif", size: 11 },
              boxWidth: 10, boxHeight: 10, padding: 14,
              usePointStyle: true, pointStyle: "circle",
            },
          },
          tooltip: {
            ...tooltipConfig(t),
            callbacks: {
              label: (ctx) => {
                const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
                const pct = ((ctx.parsed / total) * 100).toFixed(1);
                return ` ${ctx.label}: ${ctx.parsed.toLocaleString()} avg (${pct}%)`;
              },
            },
          },
        },
        animation: { animateRotate: true, duration: 1000, easing: "easeOutCubic" },
      },
    });

    return () => {
      if (chartRef.current) { chartRef.current.destroy(); chartRef.current = null; }
    };
  }, [seasonAverage, theme]);

  if (!seasonAverage || !seasonAverage.length) {
    return <div className="empty chart-empty">{emptyText}</div>;
  }

  return (
    <div className="chart-wrap" style={{ height: 260 }}>
      <canvas ref={canvasRef} />
    </div>
  );
}
