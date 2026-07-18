import { useRef, useEffect } from "react";
import { Chart, registerables } from "chart.js";
import zoomPlugin from "chartjs-plugin-zoom";
import { seasonColors } from "../lib/format";
import { getChartTheme, tooltipConfig, scaleConfig } from "../lib/chartTheme";

Chart.register(...registerables, zoomPlugin);

export default function HistoryLineChart({ records, theme = "dark", emptyText = "No data available" }) {
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
    const labels = records.map((r) => r.date);
    const values = records.map((r) => r.arrivals);
    const pointBgColors = records.map((r) => seasonColors[r.season] || t.pointDefault);

    chartRef.current = new Chart(canvasRef.current, {
      type: "line",
      data: {
        labels,
        datasets: [
          {
            label: "Monthly Arrivals",
            data: values,
            borderColor: t.line,
            backgroundColor: t.lineFill,
            pointBackgroundColor: pointBgColors,
            pointBorderColor: pointBgColors,
            pointRadius: records.length > 80 ? 1.5 : 3,
            pointHoverRadius: 6,
            borderWidth: 1.8,
            fill: true,
            tension: 0.3,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: "index", intersect: false },
        plugins: {
          legend: { display: false },
          tooltip: {
            ...tooltipConfig(t),
            displayColors: true,
            callbacks: {
              label: (ctx) => ` ${ctx.parsed.y.toLocaleString()} arrivals`,
            },
          },
          zoom: {
            pan: { enabled: true, mode: "x" },
            zoom: {
              wheel: { enabled: true, speed: 0.05 },
              pinch: { enabled: true },
              drag: { enabled: false },
              mode: "x",
            },
            limits: { x: { minRange: 5 } },
          },
        },
        scales: scaleConfig(t, { xTicks: { maxRotation: 45, maxTicksLimit: 12 } }),
        animation: { duration: 800, easing: "easeOutCubic" },
      },
    });

    return () => {
      if (chartRef.current) {
        chartRef.current.destroy();
        chartRef.current = null;
      }
    };
  }, [records, theme]);

  function handleReset() {
    if (chartRef.current) chartRef.current.resetZoom();
  }

  if (!records || !records.length) {
    return <div className="empty chart-empty">{emptyText}</div>;
  }

  return (
    <div>
      <div className="chart-wrap" style={{ height: 300 }}>
        <canvas ref={canvasRef} />
      </div>
      <div className="chart-controls">
        <span className="chart-hint">Scroll to zoom · Drag to pan</span>
        <button className="ghost-btn chart-reset-btn" type="button" onClick={handleReset}>
          Reset zoom
        </button>
      </div>
    </div>
  );
}
