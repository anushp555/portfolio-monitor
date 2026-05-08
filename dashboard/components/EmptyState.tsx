export function EmptyState() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center px-6">
      <div className="max-w-xl text-center">
        <div className="font-mono text-[10px] uppercase tracking-[0.4em] text-bone-300">
          Catalyst Desk
        </div>
        <h1 className="mt-3 font-display text-5xl font-light text-bone-50">
          No report yet
        </h1>
        <p className="mt-4 font-display text-lg italic text-bone-200">
          The morning bulletin hasn&apos;t printed. Run the pipeline to generate today&apos;s edition.
        </p>
        <div className="mt-8 inline-block border rule bg-ink-800/40 p-4 text-left font-mono text-xs text-bone-100">
          <div className="text-bone-300"># From the project root:</div>
          <div className="mt-1">
            export GEMINI_API_KEY=<span className="text-signal-amber">your-key</span>
          </div>
          <div>python -m scripts.run_daily</div>
          <div className="mt-2 text-bone-300"># Or for a sample report:</div>
          <div>python -m scripts.make_sample</div>
        </div>
      </div>
    </div>
  );
}
