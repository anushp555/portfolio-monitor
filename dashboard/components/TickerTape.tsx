import type { StockEntry } from "@/lib/reports";

export function TickerTape({ stocks }: { stocks: StockEntry[] }) {
  const items = stocks.map((s) => ({
    symbol: s.symbol,
    pct: s.price_action?.change_pct ?? 0,
    close: s.price_action?.close ?? 0,
  }));
  // Duplicate so the marquee loops seamlessly
  const looped = [...items, ...items];

  return (
    <div className="overflow-hidden border-b rule bg-ink-800">
      <div className="flex whitespace-nowrap py-2 animate-marquee">
        {looped.map((it, i) => (
          <span
            key={i}
            className="mx-6 inline-flex items-baseline gap-2 font-mono text-[12px] tracking-tight"
          >
            <span className="text-bone-300">{it.symbol}</span>
            <span className="text-bone-50">₹{it.close.toFixed(2)}</span>
            <span
              className={
                it.pct >= 0 ? "text-signal-emerald" : "text-signal-crimson"
              }
            >
              {it.pct >= 0 ? "▲" : "▼"} {Math.abs(it.pct).toFixed(2)}%
            </span>
          </span>
        ))}
      </div>
    </div>
  );
}
