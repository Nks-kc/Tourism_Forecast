import { compactNumber, modelColors } from "../lib/format";

export default function ModelsPanel({ metrics, onRefresh, isLoggedIn, bestModel }) {
  const names = Object.keys(metrics || {});

  return (
    <section className="panel">
      <div className="panel-head">
        <span className="panel-title">Saved model performance</span>
        <button className="ghost-btn" type="button" disabled={!isLoggedIn} onClick={onRefresh}>Refresh Metrics</button>
      </div>

      {!isLoggedIn && <div className="empty">Login to load saved model metrics.</div>}
      {isLoggedIn && !names.length && <div className="empty">No metrics loaded yet.</div>}

      {names.length > 0 && (
        <table className="model-table">
          <thead>
            <tr>
              <th>Model</th>
              <th>MAE</th>
              <th>RMSE</th>
              <th>MAPE</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {names.map((name) => (
              <tr key={name}>
                <td><span className="dot" style={{ background: modelColors[name] || "#8b8982" }} />{name}</td>
                <td>{compactNumber(Math.round(metrics[name].MAE))}</td>
                <td>{compactNumber(Math.round(metrics[name].RMSE))}</td>
                <td><span className={`badge ${name === bestModel ? "badge-good" : "badge-warn"}`}>{Number(metrics[name].MAPE).toFixed(2)}%</span></td>
                <td>{name === bestModel ? <span className="badge badge-good">Best</span> : <span className="badge badge-muted">Baseline</span>}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
