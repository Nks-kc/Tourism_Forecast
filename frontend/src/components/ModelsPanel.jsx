import { compactNumber, modelColors } from "../lib/format";

function formatTrainedAt(iso) {
  if (!iso) return null;
  const d = new Date(iso);
  if (isNaN(d)) return null;
  const now = new Date();
  const diffMs = now - d;
  const diffDays = Math.floor(diffMs / 86400000);
  if (diffDays === 0) return "Trained today";
  if (diffDays === 1) return "Trained yesterday";
  if (diffDays < 30) return `Trained ${diffDays}d ago`;
  return `Trained ${d.toLocaleDateString("en-US", { month: "short", year: "numeric" })}`;
}

const METRIC_LABELS = { MAE: "MAE", RMSE: "RMSE", MAPE: "MAPE" };

export default function ModelsPanel({ metrics, bestModel }) {
  const trainedAt = metrics?.trained_at ?? null;
  const names = Object.keys(metrics || {}).filter((k) => k !== "trained_at");
  const trainedLabel = formatTrainedAt(trainedAt);

  if (!names.length) {
    return (
      <section className="panel">
        <div className="panel-head">
          <span className="panel-title">Model performance</span>
        </div>
        <div className="empty">No metrics loaded yet.</div>
      </section>
    );
  }

  // Compute bar widths relative to worst (highest MAPE = full bar)
  const mapes = names.map((n) => Number(metrics[n].MAPE));
  const maes  = names.map((n) => Number(metrics[n].MAE));
  const rmses = names.map((n) => Number(metrics[n].RMSE));
  const maxMape = Math.max(...mapes);
  const maxMae  = Math.max(...maes);
  const maxRmse = Math.max(...rmses);

  // Sort: best (lowest MAPE) first
  const sorted = [...names].sort(
    (a, b) => Number(metrics[a].MAPE) - Number(metrics[b].MAPE)
  );

  return (
    <section className="panel">
      <div className="panel-head">
        <span className="panel-title">Model performance</span>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          {trainedLabel && (
            <span className="section-meta">{trainedLabel}</span>
          )}
          <span className="section-meta">{names.length ? `${names.length} models · MAPE ranking` : ""}</span>
        </div>
      </div>

      {/* Visual MAPE bars */}
      <div className="model-bars">
        {sorted.map((name, idx) => {
          const mape = Number(metrics[name].MAPE);
          const barPct = (mape / maxMape) * 100;
          const isBest = name === bestModel;
          return (
            <div className="model-bar-row" key={name}>
              <div className="model-bar-label">
                <span
                  className="dot"
                  style={{ background: modelColors[name] || "#8b8982" }}
                />
                <span className="model-bar-name">{name}</span>
                {isBest && <span className="badge badge-good model-best-badge">Best</span>}
              </div>

              <div className="model-bar-track">
                <div
                  className="model-bar-fill"
                  style={{
                    width: `${barPct}%`,
                    background: isBest
                      ? "var(--teal)"
                      : `${modelColors[name]}99` || "rgba(139,137,130,0.4)",
                  }}
                />
              </div>

              <span className={`model-bar-value ${isBest ? "teal" : ""}`}>
                {mape.toFixed(2)}%
              </span>
            </div>
          );
        })}
      </div>

      {/* Detailed metrics table */}
      <div className="model-detail-label">Detailed metrics</div>
      <table className="model-table">
        <thead>
          <tr>
            <th>Model</th>
            <th>
              MAE
              <span className="model-th-sub"> · arrivals</span>
            </th>
            <th>
              RMSE
              <span className="model-th-sub"> · arrivals</span>
            </th>
            <th>MAPE</th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((name) => {
            const m = metrics[name];
            const isBest = name === bestModel;
            const maePct  = (Number(m.MAE)  / maxMae)  * 100;
            const rmsePct = (Number(m.RMSE) / maxRmse) * 100;
            return (
              <tr key={name} className={isBest ? "model-row-best" : ""}>
                <td>
                  <span
                    className="dot"
                    style={{ background: modelColors[name] || "#8b8982" }}
                  />
                  {name}
                </td>
                <td>
                  <div className="model-cell">
                    <span>{compactNumber(Math.round(m.MAE))}</span>
                    <div className="model-cell-bar">
                      <div
                        className="model-cell-fill"
                        style={{
                          width: `${maePct}%`,
                          background: isBest ? "var(--teal)" : "var(--border2)",
                        }}
                      />
                    </div>
                  </div>
                </td>
                <td>
                  <div className="model-cell">
                    <span>{compactNumber(Math.round(m.RMSE))}</span>
                    <div className="model-cell-bar">
                      <div
                        className="model-cell-fill"
                        style={{
                          width: `${rmsePct}%`,
                          background: isBest ? "var(--teal)" : "var(--border2)",
                        }}
                      />
                    </div>
                  </div>
                </td>
                <td>
                  <span
                    className={`badge ${isBest ? "badge-good" : Number(m.MAPE) < 12 ? "badge-warn" : "badge-muted"}`}
                  >
                    {Number(m.MAPE).toFixed(2)}%
                  </span>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </section>
  );
}
