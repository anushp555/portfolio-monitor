import type { Classification } from "@/lib/reports";

const CONFIG: Record<
  Classification,
  { label: string; tone: string; glyph: string; description: string }
> = {
  catalyst_drove_move: {
    label: "Catalyst → Move",
    tone: "text-signal-emerald border-signal-emerald/40 bg-signal-emerald/10",
    glyph: "→",
    description: "Story checks out",
  },
  move_without_catalyst: {
    label: "Move w/o Catalyst",
    tone: "text-signal-crimson border-signal-crimson/50 bg-signal-crimson/15",
    glyph: "⚠",
    description: "Possible flow / leak",
  },
  catalyst_without_move: {
    label: "Catalyst w/o Move",
    tone: "text-signal-amber border-signal-amber/40 bg-signal-amber/10",
    glyph: "⊘",
    description: "Possible lag setup",
  },
  no_signal: {
    label: "No Signal",
    tone: "text-bone-300 border-bone-300/20 bg-bone-300/5",
    glyph: "·",
    description: "Quiet day",
  },
  price_only: {
    label: "Price Only",
    tone: "text-bone-200 border-bone-200/25 bg-bone-200/5",
    glyph: "◇",
    description: "Tracking price; no catalysts",
  },
};

export function ClassificationBadge({
  classification,
  confidence,
}: {
  classification: Classification;
  confidence: "high" | "medium" | "low";
}) {
  const c = CONFIG[classification];
  return (
    <div
      className={`inline-flex items-center gap-2 border px-2.5 py-1 text-[11px] uppercase tracking-[0.18em] ${c.tone}`}
    >
      <span className="text-sm leading-none">{c.glyph}</span>
      <span className="font-mono">{c.label}</span>
      <span className="opacity-60">·</span>
      <span className="opacity-70">{confidence}</span>
    </div>
  );
}

export const CLASSIFICATION_CONFIG = CONFIG;
