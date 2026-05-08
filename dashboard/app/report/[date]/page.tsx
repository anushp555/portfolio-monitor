import { ReportHeader } from "@/components/ReportHeader";
import { StockCard } from "@/components/StockCard";
import { TickerTape } from "@/components/TickerTape";
import { listReportDates, loadReportByDate } from "@/lib/reports";
import Link from "next/link";
import { notFound } from "next/navigation";

export async function generateStaticParams() {
  const dates = await listReportDates();
  return dates.map((date) => ({ date }));
}

const ORDER: Record<string, number> = {
  move_without_catalyst: 0,
  catalyst_drove_move: 1,
  catalyst_without_move: 2,
  no_signal: 3,
  price_only: 4,
};

export default async function ReportByDate({
  params,
}: {
  params: { date: string };
}) {
  const report = await loadReportByDate(params.date);
  if (!report) notFound();

  const sorted = [...report.stocks].sort((a, b) => {
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
        <div className="pt-8">
          <Link
            href="/archive"
            className="font-mono text-[11px] uppercase tracking-[0.22em] text-bone-300 hover:text-signal-amber"
          >
            ← Archive
          </Link>
        </div>
        <ReportHeader report={report} />
        <div className="my-10" />
        <div className="grid grid-cols-1 gap-px bg-ink-700/30 lg:grid-cols-2">
          {sorted.map((stock, i) => (
            <div key={stock.symbol} className="bg-ink-900">
              <StockCard stock={stock} index={i} />
            </div>
          ))}
        </div>
        <div className="my-16" />
      </div>
    </main>
  );
}
