import { useRef, useEffect } from "react";
import { Chart, registerables } from "chart.js";
import { modelColors } from "../lib/format";
import { getChartTheme, tooltipConfig, scaleConfig } from "../lib/chartTheme";

Chart.register(...registerables);

export default function ModelComparisonChart({ predictions, theme = "dark", emptyText = "Generate a forecast to compare models" }) {
  const canvasRef = useRef(null);
  const chartRef = useRef(null);

  useEffect(() => {
    if (!canvasRef.current) return;

    if (chartRef.current) { chartRef.current.destroy(); chartRef.current = null; }

    const names = Object.keys(predictions || {});
    if (!names.length) return;

    const labels = predictions[names[0]]?.months || [];
    if (!labels.length) return;

    const t = getChartTheme(theme);
    const datasets = names.map((name) => ({
      label: name,
      data: predictions[name].arrivals,
      borderColor: modelColors[name] || t.pointDefault,
      pointBackgroundColor: modelColors[name] || t.pointDefault,
      pointBorderColor: modelColors[name] || t.pointDefault,
      pointRadius: 4,
      pointHoverRadius: 7,
      borderWidth: 2.2,
      tension: 0.3,
      fill: false,
    }));

    chartRef.current = new Chart(canvasRef.current, {
      type: "line",
      data: { labels, datasets },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: "index", intersect: false },
        plugins: {
          legend: {
            position: "top", align: "end",
            labels: {
              color: t.legendText,
              font: { family: "'JetBrains Mono', monospace", size: 10 },
              boxWidth: 14, boxHeight: 2, padding: 12,
            },
          },
          tooltip: {
            ...tooltipConfig(t),
            callbacks: {
              label: (ctx) => ` ${ctx.dataset.label}: ${ctx.parsed.y?.toLocaleString()}`,
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
  }, [predictions, theme]);

  const names = Object.keys(predictions || {});
  if (!names.length) {
    return <div className="empty chart-empty">{emptyText}</div>;
  }

  return (
    <div className="chart-wrap" style={{ height: 300 }}>
      <canvas ref={canvasRef} />
    </div>
  );
}
