// Chart color presets for dark and light themes
// Chart.js uses canvas so it can't read CSS variables — we define colors explicitly

export const chartThemes = {
  dark: {
    grid: "rgba(255,255,255,0.04)",
    tick: "#6b6966",
    tooltipBg: "rgba(11, 15, 20, 0.92)",
    tooltipBorder: "rgba(255,255,255,0.08)",
    legendText: "#a8a5a0",
    line: "rgba(232, 230, 225, 0.6)",
    lineFill: "rgba(232, 230, 225, 0.04)",
    pointDefault: "#e8e6e1",
    donutBorder: "rgba(11, 15, 20, 0.8)",
  },
  light: {
    grid: "rgba(0,0,0,0.06)",
    tick: "#8b8982",
    tooltipBg: "rgba(255, 255, 255, 0.95)",
    tooltipBorder: "rgba(0,0,0,0.08)",
    legendText: "#6b6966",
    line: "rgba(40, 40, 40, 0.7)",
    lineFill: "rgba(40, 40, 40, 0.05)",
    pointDefault: "#333",
    donutBorder: "rgba(255, 255, 255, 0.9)",
  },
};

export function getChartTheme(theme) {
  return chartThemes[theme] || chartThemes.dark;
}

// Common tooltip config
export function tooltipConfig(t) {
  return {
    backgroundColor: t.tooltipBg,
    borderColor: t.tooltipBorder,
    borderWidth: 1,
    titleFont: { family: "'Inter', sans-serif", size: 12, weight: "500" },
    titleColor: t === chartThemes.light ? "#1a1a1a" : undefined,
    bodyFont: { family: "'JetBrains Mono', monospace", size: 11 },
    bodyColor: t === chartThemes.light ? "#333" : undefined,
    padding: 10,
    cornerRadius: 8,
  };
}

// Common scale config
export function scaleConfig(t, options = {}) {
  return {
    x: {
      grid: { color: t.grid, drawBorder: false },
      ticks: {
        color: t.tick,
        font: { family: "'JetBrains Mono', monospace", size: 10 },
        ...options.xTicks,
      },
    },
    y: {
      grid: { color: t.grid, drawBorder: false },
      ticks: {
        color: t.tick,
        font: { family: "'JetBrains Mono', monospace", size: 10 },
        callback: (v) => {
          if (v >= 1_000_000) return `${(v / 1_000_000).toFixed(1)}M`;
          if (v >= 1_000) return `${Math.round(v / 1_000)}k`;
          return v;
        },
        ...options.yTicks,
      },
    },
  };
}
