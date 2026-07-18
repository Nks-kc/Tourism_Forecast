import { useEffect, useRef, useState } from "react";

export default function AnimatedCounter({ value, duration = 1200, formatter }) {
  const [display, setDisplay] = useState(0);
  const prevValue = useRef(0);
  const rafId = useRef(null);

  useEffect(() => {
    const numericValue = Number(value);
    if (Number.isNaN(numericValue) || value === null || value === undefined) {
      setDisplay(null);
      return;
    }

    const start = prevValue.current;
    const end = numericValue;
    const diff = end - start;
    const startTime = performance.now();

    function animate(currentTime) {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      // ease-out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      const current = start + diff * eased;

      setDisplay(current);

      if (progress < 1) {
        rafId.current = requestAnimationFrame(animate);
      } else {
        prevValue.current = end;
      }
    }

    rafId.current = requestAnimationFrame(animate);

    return () => {
      if (rafId.current) cancelAnimationFrame(rafId.current);
    };
  }, [value, duration]);

  if (display === null) return "--";

  if (formatter) return formatter(display);
  return Math.round(display).toLocaleString();
}
