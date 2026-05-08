import { EmptyState } from "@/components/EmptyState";
import { ReportHeader } from "@/components/ReportHeader";
import { StockCard } from "@/components/StockCard";
import { TickerTape } from "@/components/TickerTape";
import { listReportDates, loadLatestReport } from "@/lib/reports";
import Link from "next/link";

// Re-read the report on every request during dev; in prod this gets ISR'd
export const revalidate = 300;

export default async function Home() {
  const report = await loadLatestReport();
  if (!report) return <EmptyState />;

  const dates = await listReportDates();

  // Sort: anomalies first, then biggest movers, then quiet stocks, then SGBs/ETFs
  const ORDER: Record<string, number> = {
    move_without_catalyst: 0,
    catalyst_drove_move: 1,
    catalyst_without_move: 2,
    no_signal: 3,
    price_only: 4,
  };
  const sortedStocks = [...report.stocks].sort((a, b) => {
    const oa = ORDER[a.analysis.classification] ?? 9;
    const ob = ORDER[b.analysis.classification] ?? 9;
    if (oa !== ob) return oa - ob;
    return (
      Math.abs(b.price_action?.change_pct ?? 0) -
      Math.abs(a.price_action?.change_pct ?? 0)
    );
  });

  return (
    <main>
      <TickerTape stocks={report.stocks} />
      <div className="mx-auto max-w-6xl px-6 lg:px-10">
        <ReportHeader report={report} />

        {/* Editorial intro line */}
        <div className="my-10 flex items-baseline justify-between gap-6 border-b rule pb-6">
          <p className="font-display text-lg italic text-bone-200">
            Sorted by signal strength. Anomalies surface first.
          </p>
          {dates.length > 1 && (
            <Link
              href="/archive"
              className="font-mono text-[11px] uppercase tracking-[0.22em] text-bone-300 underline-offset-4 hover:text-signal-amber hover:underline"
            >
              Archive ({dates.length}) →
            </Link>
          )}
        </div>

        {/* Stock cards grid */}
        <div className="grid grid-cols-1 gap-px bg-ink-700/30 lg:grid-cols-2">
          {sortedStocks.map((stock, i) => (
            <div key={stock.symbol} className="bg-ink-900">
              <StockCard stock={stock} index={i} />
            </div>
          ))}
        </div>

        {/* Footer */}
        <footer className="my-16 border-t rule pt-8">
          <div className="flex flex-col gap-2 font-mono text-[11px] uppercase tracking-[0.22em] text-bone-300 sm:flex-row sm:justify-between">
            <span>Catalyst Desk · {report.stocks.length} stocks tracked</span>
            <span>
              Data: yfinance, BSE, NSE, Google News, SEBI · Analysis: Gemini 2.0 Flash
            </span>
          </div>
        </footer>
      </div>
    </main>
  );
}
