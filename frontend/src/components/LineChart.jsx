import { thousands } from "../lib/format";

function pathFor(points) {
  return points.map((point, index) => `${index === 0 ? "M" : "L"} ${point.x} ${point.y}`).join(" ");
}

export default function LineChart({ labels, series, height = 300, emptyText = "No data available" }) {
  const width = 960;
  const padding = { top: 18, right: 22, bottom: 42, left: 58 };
  const allValues = series.flatMap((item) => item.values).filter((value) => value !== null && value !== undefined);

  if (!labels.length || !allValues.length) {
    return <div className="empty chart-empty">{emptyText}</div>;
  }

  const minValue = Math.min(0, ...allValues);
  const maxValue = Math.max(...allValues);
  const valueRange = Math.max(maxValue - minValue, 1);
  const plotWidth = width - padding.left - padding.right;
  const plotHeight = height - padding.top - padding.bottom;
  const xFor = (index) => padding.left + (labels.length === 1 ? plotWidth / 2 : (index / (labels.length - 1)) * plotWidth);
  const yFor = (value) => padding.top + plotHeight - ((Number(value) - minValue) / valueRange) * plotHeight;
  const tickValues = [0, 0.25, 0.5, 0.75, 1].map((step) => minValue + valueRange * step);
  const labelStep = Math.max(1, Math.ceil(labels.length / 8));

  return (
    <div className="svg-chart" style={{ height }}>
      <svg viewBox={`0 0 ${width} ${height}`} role="img">
        {tickValues.map((tick) => {
          const y = yFor(tick);
          return (
            <g key={tick}>
              <line className="grid-line" x1={padding.left} x2={width - padding.right} y1={y} y2={y} />
              <text className="axis-label" x={padding.left - 10} y={y + 4} textAnchor="end">{thousands(tick)}</text>
            </g>
          );
        })}

        {labels.map((label, index) => index % labelStep === 0 && (
          <text key={label} className="axis-label" x={xFor(index)} y={height - 14} textAnchor="middle">{label}</text>
        ))}

        {series.map((item) => {
          const points = item.values.map((value, index) => ({ x: xFor(index), y: yFor(value), value }));
          return (
            <g key={item.name}>
              <path className="chart-line" d={pathFor(points)} stroke={item.color} />
              {points.map((point, index) => (
                <circle key={`${item.name}-${labels[index]}`} cx={point.x} cy={point.y} r={labels.length > 80 ? 2 : 3.5} fill={item.pointColors?.[index] || item.color}>
                  <title>{`${item.name} · ${labels[index]} · ${Number(point.value).toLocaleString()}`}</title>
                </circle>
              ))}
            </g>
          );
        })}
      </svg>
    </div>
  );
}
