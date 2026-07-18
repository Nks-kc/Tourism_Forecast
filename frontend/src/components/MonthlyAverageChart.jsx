import { useRef, useEffect } from "react";
import { Chart, registerables } from "chart.js";
import { getChartTheme, tooltipConfig, scaleConfig } from "../lib/chartTheme";

Chart.register(...registerables);

export default function MonthlyAverageChart({ monthlyAverage, theme = "dark", emptyText = "No monthly average data" }) {
  const canvasRef = useRef(null);
  const chartRef = useRef(null);

  useEffect(() => {
    if (!canvasRef.current) return;

    if (chartRef.current) { chartRef.current.destroy(); chartRef.current = null; }

    if (!monthlyAverage || !monthlyAverage.length) return;

    const t = getChartTheme(theme);
    const labels = monthlyAverage.map((m) => m.month_name);
    const data = monthlyAverage.map((m) => Math.round(m.average_arrivals));
    const maxVal = Math.max(...data);

    const tealBase = theme === "light" ? [42, 138, 106] : [80, 184, 152];
    const bgColors = data.map((v) => {
      const ratio = v / maxVal;
      const alpha = 0.25 + ratio * 0.55;
      return `rgba(${tealBase.join(",")}, ${alpha})`;
    });
    const hoverColors = data.map((v) => {
      const ratio = v / maxVal;
      const alpha = 0.45 + ratio * 0.45;
      return `rgba(${tealBase.join(",")}, ${alpha})`;
    });

    chartRef.current = new Chart(canvasRef.current, {
      type: "bar",
      data: {
        labels,
        datasets: [{
          label: "Avg. Arrivals",
          data,
          backgroundColor: bgColors,
          hoverBackgroundColor: hoverColors,
          borderColor: `rgba(${tealBase.join(",")}, 0.3)`,
          borderWidth: 1,
          borderRadius: 4,
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
              label: (ctx) => ` Average: ${ctx.parsed.y.toLocaleString()} arrivals`,
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
  }, [monthlyAverage, theme]);

  if (!monthlyAverage || !monthlyAverage.length) {
    return <div className="empty chart-empty">{emptyText}</div>;
  }

  return (
    <div className="chart-wrap" style={{ height: 260 }}>
      <canvas ref={canvasRef} />
    </div>
  );
}
