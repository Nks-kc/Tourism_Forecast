import { describe, it, expect, vi, afterEach } from "vitest";
import "@testing-library/jest-dom/vitest";
import { render, screen, fireEvent, cleanup } from "@testing-library/react";
import ForecastPanel from "./ForecastPanel";

// ForecastPanel renders ModelComparisonChart, which draws to a real <canvas> via Chart.js.
// jsdom doesn't implement the Canvas 2D API, so we stub the chart out.
vi.mock("./ModelComparisonChart", () => ({
    default: ({ predictions, emptyText }) => (
        <div data-testid="chart-stub">
            {Object.keys(predictions || {}).length ? "chart" : emptyText}
        </div>
    ),
}));

// RTL's automatic cleanup-between-tests relies on a global afterEach; since we're using
// explicit imports instead of vitest's `globals: true`, we register it ourselves.
afterEach(() => cleanup());

const baseProps = {
    horizon: 3, setHorizon: () => { }, predictions: {}, onGenerate: () => { },
    loading: false, isLoggedIn: true, message: null, theme: "dark",
};

describe("ForecastPanel", () => {
    it("shows the logged-out prompt when not logged in", () => {
        render(<ForecastPanel {...baseProps} isLoggedIn={false} />);
        expect(screen.getByText("Login to generate forecasts.")).toBeInTheDocument();
    });

    it("disables Generate Forecast when logged out", () => {
        render(<ForecastPanel {...baseProps} isLoggedIn={false} />);
        expect(screen.getByRole("button", { name: /generate forecast/i })).toBeDisabled();
    });

    it("disables Generate Forecast while loading", () => {
        render(<ForecastPanel {...baseProps} loading={true} />);
        expect(screen.getByRole("button", { name: /generating/i })).toBeDisabled();
    });

    it("calls onGenerate when clicked while logged in", () => {
        const onGenerate = vi.fn();
        render(<ForecastPanel {...baseProps} onGenerate={onGenerate} />);
        fireEvent.click(screen.getByRole("button", { name: /generate forecast/i }));
        expect(onGenerate).toHaveBeenCalledTimes(1);
    });

    it("calls setHorizon with the clicked horizon value", () => {
        const setHorizon = vi.fn();
        render(<ForecastPanel {...baseProps} setHorizon={setHorizon} />);
        fireEvent.click(screen.getByRole("button", { name: "12 mo" }));
        expect(setHorizon).toHaveBeenCalledWith(12);
    });

    it("marks the active horizon chip", () => {
        render(<ForecastPanel {...baseProps} horizon={6} />);
        expect(screen.getByRole("button", { name: "6 mo" })).toHaveClass("active");
        expect(screen.getByRole("button", { name: "3 mo" })).not.toHaveClass("active");
    });

    it("renders a prediction card per model with formatted numbers", () => {
        const predictions = { MLP: { months: ["2026-08"], arrivals: [1200] } };
        render(<ForecastPanel {...baseProps} predictions={predictions} />);
        expect(screen.getByText("MLP")).toBeInTheDocument();
        expect(screen.getByText("1,200")).toBeInTheDocument();
    });

    it("shows an error-styled message when message.error is true", () => {
        render(<ForecastPanel {...baseProps} message={{ text: "Something failed", error: true }} />);
        expect(screen.getByText("Something failed")).toHaveClass("error");
    });
});