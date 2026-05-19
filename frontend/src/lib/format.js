export const modelColors = {
  SARIMA: "#56b89f",
  "Holt-Winters": "#e86060",
  "Linear Regression": "#f0c96a",
  MLP: "#5b92cc"
};

export const seasonColors = {
  spring_trek: "#e86060",
  monsoon: "#4b525d",
  autumn_trek: "#d4a847",
  shoulder: "#56b89f"
};

export const seasonLabels = {
  spring_trek: "Spring trekking",
  monsoon: "Monsoon",
  autumn_trek: "Autumn trekking",
  shoulder: "Shoulder"
};

export function compactNumber(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "--";
  return Number(value).toLocaleString();
}

export function thousands(value) {
  return `${Math.round(Number(value || 0) / 1000)}k`;
}

export function average(values) {
  if (!values.length) return 0;
  return values.reduce((sum, value) => sum + Number(value || 0), 0) / values.length;
}
