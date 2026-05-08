import type { StockEntry } from "@/lib/reports";
import { ClassificationBadge, CLASSIFICATION_CONFIG } from "./ClassificationBadge";
import { Sparkline } from "./Sparkline";

function fmtNum(n: number, digits = 2) {
  return new Intl.NumberFormat("en-IN", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  }).format(n);
}

function fmtCompactVolume(n: number) {
  if (n >= 1e7) return `${(n / 1e7).toFixed(2)} Cr`;
  if (n >= 1e5) return `${(n / 1e5).toFixed(2)} L`;
  return new Intl.NumberFormat("en-IN").format(n);
}

function relTime(iso?: string): string {
  if (!iso) return "";
  const t = new Date(iso).getTime();
  if (isNaN(t)) return iso;
  const diffH = (Date.now() - t) / 3_600_000;
  if (diffH < 1) return `${Math.max(1, Math.round(diffH * 60))}m ago`;
  if (diffH < 24) return `${Math.round(diffH)}h ago`;
  return `${Math.round(diffH / 24)}d ago`;
}

export function StockCard({ stock, index }: { stock: StockEntry; index: number }) {
  const pa = stock.price_action;
  const a = stock.analysis;
  const isPositive = (pa?.change_pct ?? 0) >= 0;
  const isAnomaly = a.classification === "move_without_catalyst";
  const classConfig = CLASSIFICATION_CONFIG[a.classification];

  const allCatalysts = [
    ...stock.bse_announcements.map((b) => ({
      kind: "FILING",
      headline: b.headline,
      meta: `BSE · ${b.category ?? "—"}`,
      time: b.attached_at,
      url: b.pdf_url ?? undefined,
    })),
    ...stock.nse_announcements.map((b) => ({
      kind: "FILING",
      headline: b.headline,
      meta: `NSE · ${b.category ?? "—"}`,
      time: b.attached_at,
      url: b.pdf_url ?? undefined,
    })),
    ...stock.news.slice(0, 3).map((n) => ({
      kind: "NEWS",
      headline: n.title,
      meta: n.source,
      time: n.published_at,
      url: n.url,
    })),
    ...stock.sebi_mentions.map((s) => ({
      kind: "SEBI",
      headline: s.title ?? "SEBI mention",
      meta: "SEBI Press",
      time: s.published_at,
      url: s.url,
    })),
  ].slice(0, 5);

  return (
    <article
      className={`reveal group relative border ${
        isAnomaly ? "border-signal-crimson/30" : "rule"
      } bg-ink-800/40 backdrop-blur-sm`}
      style={{ animationDelay: `${index * 80}ms` }}
    >
      {/* Anomaly accent stripe */}
      {isAnomaly && (
        <div className="absolute left-0 top-0 h-full w-[3px] bg-signal-crimson" />
      )}

      <header className="flex items-start justify-between gap-6 border-b rule p-6">
        <div className="min-w-0 flex-1">
          <div className="flex items-baseline gap-3">
            <h2 className="font-mono text-xl tracking-tight text-bone-50">
              {stock.symbol}
            </h2>
            {stock.sector && (
              <span className="text-[10px] uppercase tracking-[0.22em] text-bone-300">
                {stock.sector}
              </span>
            )}
          </div>
          <p className="mt-1 font-display text-sm italic text-bone-200">
            {stock.name}
          </p>
        </div>

        <div className="flex flex-col items-end gap-2">
          <div className="tabular text-right">
            <div className="font-mono text-2xl text-bone-50">
              ₹{fmtNum(pa?.close ?? 0)}
            </div>
            <div
              className={`font-mono text-sm ${
                isPositive ? "text-signal-emerald" : "text-signal-crimson"
              }`}
            >
              {isPositive ? "+" : ""}
              {fmtNum(pa?.change_pct ?? 0)}%
            </div>
          </div>
          <Sparkline values={pa?.sparkline ?? []} positive={isPositive} />
        </div>
      </header>

      {/* Analysis */}
      <section className="space-y-4 border-b rule p-6">
        <div className="flex flex-wrap items-center gap-2">
          <ClassificationBadge
            classification={a.classification}
            confidence={a.confidence}
          />
          {a.flags.map((flag) => (
            <span
              key={flag}
              className="inline-flex items-center border border-signal-crimson/40 bg-signal-crimson/10 px-2 py-0.5 font-mono text-[10px] uppercase tracking-[0.18em] text-signal-crimson"
            >
              ▲ {flag.replace(/_/g, " ")}
            </span>
          ))}
        </div>

        {a.primary_catalyst && (
          <div className="text-[11px] uppercase tracking-[0.2em] text-bone-300">
            Primary catalyst
            <p className="mt-1 normal-case tracking-normal text-base font-display text-bone-50">
              {a.primary_catalyst}
            </p>
          </div>
        )}

        <p className="font-display text-[15px] leading-relaxed text-bone-100">
          {a.analysis}
        </p>
      </section>

      {/* Metrics strip */}
      <section className="grid grid-cols-4 border-b rule">
        {[
          { k: "Open", v: `₹${fmtNum(pa?.open ?? 0)}` },
          { k: "Range", v: `${fmtNum(pa?.intraday_range_pct ?? 0)}%` },
          {
            k: "Volume",
            v: fmtCompactVolume(pa?.volume ?? 0),
          },
          {
            k: "Vol Ratio",
            v: `${fmtNum(pa?.volume_ratio ?? 0, 2)}×`,
            highlight: (pa?.volume_ratio ?? 0) >= 1.5,
          },
        ].map((m, i) => (
          <div
            key={m.k}
            className={`border-r rule p-4 last:border-r-0 ${
              i === 3 && m.highlight ? "bg-signal-amber/5" : ""
            }`}
          >
            <div className="text-[10px] uppercase tracking-[0.2em] text-bone-300">
              {m.k}
            </div>
            <div
              className={`tabular mt-1 font-mono text-sm ${
                i === 3 && m.highlight ? "text-signal-amber" : "text-bone-50"
              }`}
            >
              {m.v}
            </div>
          </div>
        ))}
      </section>

      {/* Catalysts */}
      <section className="p-6">
        <h3 className="mb-3 text-[10px] uppercase tracking-[0.22em] text-bone-300">
          Catalysts ({allCatalysts.length})
        </h3>
        {allCatalysts.length === 0 ? (
          <p className="font-display text-sm italic text-bone-300">
            No filings, news, or regulatory items in the lookback window.
          </p>
        ) : (
          <ul className="space-y-3">
            {allCatalysts.map((c, i) => (
              <li key={i} className="flex gap-3 text-sm">
                <span
                  className={`mt-0.5 shrink-0 font-mono text-[10px] tracking-wider ${
                    c.kind === "FILING"
                      ? "text-signal-emerald"
                      : c.kind === "SEBI"
                      ? "text-signal-crimson"
                      : "text-bone-300"
                  }`}
                >
                  {c.kind}
                </span>
                <div className="min-w-0 flex-1">
                  {c.url ? (
                    <a
                      href={c.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-bone-50 underline decoration-bone-400/30 underline-offset-4 transition-colors hover:decoration-signal-amber"
                    >
                      {c.headline}
                    </a>
                  ) : (
                    <span className="text-bone-50">{c.headline}</span>
                  )}
                  <div className="mt-0.5 flex gap-2 text-[11px] text-bone-300">
                    <span>{c.meta}</span>
                    {c.time && (
                      <>
                        <span>·</span>
                        <span>{relTime(c.time)}</span>
                      </>
                    )}
                  </div>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>
    </article>
  );
}
