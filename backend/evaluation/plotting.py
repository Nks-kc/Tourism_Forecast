from __future__ import annotations
from pathlib import Path

_FONT = "font-family='Helvetica, Arial, sans-serif'"


def _svg_header(width: int, height: int) -> str:
    return f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}' viewBox='0 0 {width} {height}'><rect width='{width}' height='{height}' fill='white'/>"


def _text(
    x: float,
    y: float,
    content: str,
    size: int = 12,
    anchor: str = "start",
    weight: str = "normal",
    color: str = "#1a1a1a",
) -> str:
    return f"<text x='{x}' y='{y}' {_FONT} font-size='{size}' text-anchor='{anchor}' font-weight='{weight}' fill='{color}'>{content}</text>"


def plot_training_loss(
    history: dict, save_path: str | Path, title: str = "MLP Training Loss"
) -> None:
    save_path = Path(save_path)
    save_path.parent.mkdir(parents=True, exist_ok=True)
    train_loss = history.get("train_loss") or []
    val_loss = history.get("val_loss") or []
    if not train_loss:
        return
    width, height = (720, 420)
    margin_left, margin_right, margin_top, margin_bottom = (70, 30, 50, 60)
    plot_w = width - margin_left - margin_right
    plot_h = height - margin_top - margin_bottom
    n = len(train_loss)
    all_values = train_loss + val_loss
    min_loss, max_loss = (min(all_values), max(all_values))
    loss_range = max_loss - min_loss or 1.0

    def x_at(i):
        return margin_left + i / max(n - 1, 1) * plot_w

    def y_at(value):
        return margin_top + plot_h - (value - min_loss) / loss_range * plot_h

    def polyline(series, color):
        points = " ".join(
            (f"{x_at(i):.1f},{y_at(v):.1f}" for i, v in enumerate(series))
        )
        return f"<polyline points='{points}' fill='none' stroke='{color}' stroke-width='2'/>"

    svg = [_svg_header(width, height)]
    svg.append(_text(width / 2, 28, title, size=16, anchor="middle", weight="bold"))
    svg.append(
        f"<line x1='{margin_left}' y1='{margin_top}' x2='{margin_left}' y2='{margin_top + plot_h}' stroke='#333' stroke-width='1'/>"
    )
    svg.append(
        f"<line x1='{margin_left}' y1='{margin_top + plot_h}' x2='{margin_left + plot_w}' y2='{margin_top + plot_h}' stroke='#333' stroke-width='1'/>"
    )
    for step in range(5):
        value = min_loss + loss_range * step / 4
        y = y_at(value)
        svg.append(
            f"<line x1='{margin_left}' y1='{y:.1f}' x2='{margin_left + plot_w}' y2='{y:.1f}' stroke='#eee' stroke-width='1'/>"
        )
        svg.append(
            _text(margin_left - 10, y + 4, f"{value:.2f}", size=10, anchor="end")
        )
    for i in (0, n // 2, n - 1):
        svg.append(
            _text(
                x_at(i), margin_top + plot_h + 20, str(i + 1), size=10, anchor="middle"
            )
        )
    svg.append(
        _text(width / 2, height - 30, "Epoch", size=11, anchor="middle", color="#555")
    )
    svg.append(
        f"<text x='16' y='{height / 2}' {_FONT} font-size='11' fill='#555' text-anchor='middle' transform='rotate(-90 16,{height / 2})'>Loss</text>"
    )
    svg.append(polyline(train_loss, "#2563eb"))
    if val_loss:
        svg.append(polyline(val_loss, "#dc2626"))
    legend_y = height - 12
    svg.append(f"<circle cx='{margin_left}' cy='{legend_y}' r='4' fill='#2563eb'/>")
    svg.append(_text(margin_left + 10, legend_y + 4, "Train loss", size=11))
    if val_loss:
        svg.append(
            f"<circle cx='{margin_left + 110}' cy='{legend_y}' r='4' fill='#dc2626'/>"
        )
        svg.append(_text(margin_left + 120, legend_y + 4, "Validation loss", size=11))
    svg.append("</svg>")
    save_path.write_text("".join(svg))


def plot_model_comparison(results: dict, save_path: str | Path) -> None:
    save_path = Path(save_path)
    save_path.parent.mkdir(parents=True, exist_ok=True)
    if not results:
        return
    metrics = ["MAE", "RMSE", "MAPE"]
    model_names = list(results.keys())
    panel_w, panel_h = (260, 280)
    gap = 20
    margin_top = 60
    width = panel_w * len(metrics) + gap * (len(metrics) + 1)
    height = panel_h + margin_top + 40
    colors = ["#2563eb", "#16a34a", "#d97706", "#dc2626", "#7c3aed", "#0891b2"]
    svg = [_svg_header(width, height)]
    svg.append(
        _text(
            width / 2, 30, "Model Comparison", size=18, anchor="middle", weight="bold"
        )
    )
    for panel_index, metric in enumerate(metrics):
        panel_x = gap + panel_index * (panel_w + gap)
        panel_y = margin_top
        values = [results[name][metric] for name in model_names]
        max_value = max(values) or 1.0
        svg.append(
            _text(
                panel_x + panel_w / 2,
                panel_y - 10,
                metric,
                size=14,
                anchor="middle",
                weight="bold",
            )
        )
        svg.append(
            f"<line x1='{panel_x}' y1='{panel_y + panel_h}' x2='{panel_x + panel_w}' y2='{panel_y + panel_h}' stroke='#333' stroke-width='1'/>"
        )
        bar_gap = 14
        bar_w = (panel_w - bar_gap * (len(model_names) + 1)) / len(model_names)
        for bar_index, (name, value) in enumerate(zip(model_names, values)):
            bar_h = value / max_value * (panel_h - 30)
            bar_x = panel_x + bar_gap + bar_index * (bar_w + bar_gap)
            bar_y = panel_y + panel_h - bar_h
            color = colors[bar_index % len(colors)]
            svg.append(
                f"<rect x='{bar_x:.1f}' y='{bar_y:.1f}' width='{bar_w:.1f}' height='{bar_h:.1f}' fill='{color}' rx='3'/>"
            )
            label_value = f"{value:.1f}%" if metric == "MAPE" else f"{value:.0f}"
            svg.append(
                _text(
                    bar_x + bar_w / 2, bar_y - 6, label_value, size=10, anchor="middle"
                )
            )
            svg.append(
                f"<text x='{bar_x + bar_w / 2:.1f}' y='{panel_y + panel_h + 16}' {_FONT} font-size='9' text-anchor='end' transform='rotate(-35 {bar_x + bar_w / 2:.1f},{panel_y + panel_h + 16})'>{name}</text>"
            )
    svg.append("</svg>")
    save_path.write_text("".join(svg))
