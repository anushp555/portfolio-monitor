import { listReportDates } from "@/lib/reports";
import Link from "next/link";

export default async function Archive() {
  const dates = await listReportDates();
  return (
    <main className="mx-auto max-w-3xl px-6 py-16 lg:px-10">
      <div className="mb-10 border-b rule pb-6">
        <Link
          href="/"
          className="font-mono text-[11px] uppercase tracking-[0.22em] text-bone-300 hover:text-signal-amber"
        >
          ← Today
        </Link>
        <h1 className="mt-3 font-display text-5xl font-light tracking-tightest text-bone-50">
          Archive
        </h1>
        <p className="mt-2 font-display italic text-bone-200">
          Every issue of the Catalyst Desk, dated.
        </p>
      </div>
      <ul className="space-y-px bg-ink-700/30">
        {dates.map((d) => (
          <li key={d} className="bg-ink-900">
            <Link
              href={`/report/${d}`}
              className="flex items-baseline justify-between p-4 transition-colors hover:bg-ink-800"
            >
              <span className="font-mono text-base text-bone-50">{d}</span>
              <span className="font-display italic text-bone-300">
                {new Date(d).toLocaleDateString("en-IN", {
                  weekday: "long",
                  day: "2-digit",
                  month: "long",
                })}
              </span>
            </Link>
          </li>
        ))}
      </ul>
    </main>
  );
}
