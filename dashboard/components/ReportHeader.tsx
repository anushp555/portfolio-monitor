import type { DailyReport } from "@/lib/reports";

function fmtDate(s: string): string {
  const d = new Date(s);
  return d.toLocaleDateString("en-IN", {
    weekday: "long",
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

export function ReportHeader({ report }: { report: DailyReport }) {
  const counts = {
    catalyst_drove_move: 0,
    move_without_catalyst: 0,
    catalyst_without_move: 0,
    no_signal: 0,
    price_only: 0,
  };
  for (const s of report.stocks) {
    const c = s.analysis.classification;
    if (c in counts) counts[c as keyof typeof counts]++;
  }

  const sorted = [...report.stocks].sort(
    (a, b) =>
      Math.abs(b.price_action?.change_pct ?? 0) -
      Math.abs(a.price_action?.change_pct ?? 0)
  );
  const biggest = sorted[0];
  const biggestPct = biggest?.price_action?.change_pct ?? 0;

  return (
    <header className="border-b rule pb-10 pt-12">
      {/* Masthead */}
      <div className="mb-10 flex items-end justify-between border-b rule pb-6">
        <div>
          <div className="font-mono text-[10px] uppercase tracking-[0.4em] text-bone-300">
            VOLUME I · ISSUE {report.trading_day}
          </div>
          <h1 className="mt-2 font-display text-6xl font-light tracking-tightest text-bone-50">
            Catalyst&nbsp;Desk
          </h1>
          <p className="mt-1 font-display italic text-bone-200">
            A daily reading of your portfolio. {fmtDate(report.trading_day)}.
          </p>
        </div>
        <div className="text-right">
          <div className="font-mono text-[10px] uppercase tracking-[0.3em] text-bone-300">
            Generated
          </div>
          <div className="font-mono text-sm text-bone-100">
            {new Date(report.generated_at).toLocaleString("en-IN", {
              hour: "2-digit",
              minute: "2-digit",
              hour12: false,
            })}{" "}
            IST
          </div>
        </div>
      </div>

      {/* Signal grid */}
      <div className="grid grid-cols-2 gap-px bg-ink-700/50 sm:grid-cols-5">
        {[
          {
            label: "Catalyst → Move",
            value: counts.catalyst_drove_move,
            tone: "text-signal-emerald",
          },
          {
            label: "Move w/o Catalyst",
            value: counts.move_without_catalyst,
            tone: "text-signal-crimson",
            urgent: counts.move_without_catalyst > 0,
          },
          {
            label: "Catalyst w/o Move",
            value: counts.catalyst_without_move,
            tone: "text-signal-amber",
          },
          {
            label: "No Signal",
            value: counts.no_signal,
            tone: "text-bone-300",
          },
          {
            label: "Price Only",
            value: counts.price_only,
            tone: "text-bone-200",
          },
        ].map((s) => (
          <div
            key={s.label}
            className={`bg-ink-900 p-6 ${s.urgent ? "ring-1 ring-inset ring-signal-crimson/30" : ""}`}
          >
            <div className="text-[10px] uppercase tracking-[0.22em] text-bone-300">
              {s.label}
            </div>
            <div className={`mt-2 font-display text-5xl font-light ${s.tone}`}>
              {s.value}
            </div>
          </div>
        ))}
      </div>

      {biggest && (
        <div className="mt-6 flex items-baseline gap-3 font-display italic text-bone-200">
          <span className="text-[10px] not-italic uppercase tracking-[0.22em] text-bone-300">
            Biggest mover
          </span>
          <span className="font-mono text-base not-italic text-bone-50">
            {biggest.symbol}
          </span>
          <span
            className={`font-mono text-base not-italic ${
              biggestPct >= 0 ? "text-signal-emerald" : "text-signal-crimson"
            }`}
          >
            {biggestPct >= 0 ? "+" : ""}
            {biggestPct.toFixed(2)}%
          </span>
        </div>
      )}
    </header>
  );
}
