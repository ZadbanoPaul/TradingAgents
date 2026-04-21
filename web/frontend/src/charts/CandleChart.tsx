import { useEffect, useRef } from "react";
import { CandlestickSeries, ColorType, createChart } from "lightweight-charts";

export type OhlcvRow = {
  date: string;
  open: number | null;
  high: number | null;
  low: number | null;
  close: number | null;
};

export default function CandleChart({ rows }: { rows: OhlcvRow[] }) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = containerRef.current;
    if (!el || !rows.length) return;

    const chart = createChart(el, {
      layout: {
        background: { type: ColorType.Solid, color: "#09090b" },
        textColor: "#a1a1aa",
      },
      grid: {
        vertLines: { color: "#27272a" },
        horzLines: { color: "#27272a" },
      },
      width: el.clientWidth,
      height: 440,
      timeScale: { borderColor: "#3f3f46", fixLeftEdge: true },
      rightPriceScale: { borderColor: "#3f3f46" },
    });

    const series = chart.addSeries(CandlestickSeries, {
      upColor: "#4ade80",
      downColor: "#f87171",
      borderVisible: false,
      wickUpColor: "#4ade80",
      wickDownColor: "#f87171",
    });

    const data = rows
      .filter(
        (r) =>
          r.open != null &&
          r.high != null &&
          r.low != null &&
          r.close != null &&
          r.date
      )
      .map((r) => ({
        time: r.date as string,
        open: r.open as number,
        high: r.high as number,
        low: r.low as number,
        close: r.close as number,
      }));

    series.setData(data);

    const ro = new ResizeObserver(() => {
      if (containerRef.current) {
        chart.applyOptions({ width: containerRef.current.clientWidth });
      }
    });
    ro.observe(el);

    return () => {
      ro.disconnect();
      chart.remove();
    };
  }, [rows]);

  return <div ref={containerRef} className="w-full min-h-[440px]" />;
}
