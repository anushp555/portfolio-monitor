# Catalyst Desk

A daily morning report on your Indian equity portfolio. For each stock it
correlates the previous day's price action against catalysts (filings, news,
earnings, SEBI orders) and surfaces anomalies — particularly **moves without
catalysts** (possible flow/leak) and **catalysts without moves** (possible lag
setups).

Built to run **entirely free** on Indian market data:

- Data: yfinance (prices), BSE & NSE public APIs (filings), Google News RSS,
  SEBI press feed
- Analysis: Gemini 2.0 Flash (free tier — 1500 requests/day, well above what a
  20-stock portfolio needs)
- Schedule: GitHub Actions cron (free for public repos)
- Storage: JSON files committed to the repo (no DB to manage)
- Hosting: Vercel free tier (Next.js dashboard)

## Architecture

```
GitHub Actions cron (09:00 IST daily)
      │
      ├─ collectors/ (parallel async pulls)
      │     ├─ prices.py            yfinance OHLC + volume
      │     ├─ bse_announcements.py BSE corp filings JSON API
      │     ├─ nse_announcements.py NSE corp filings (cookie-warmed)
      │     ├─ news.py              Google News RSS, India edition
      │     ├─ earnings.py          NSE event calendar
      │     └─ sebi.py              SEBI press releases RSS
      │
      ├─ analyzer/correlator.py     Gemini 2.0 Flash → JSON analysis
      │
      ├─ reports/YYYY-MM-DD.json    Committed back to the repo
      │
      └─ Vercel auto-deploys        Next.js dashboard reads reports/
```

## Setup (one-time, ~20 minutes)

### 1. Fork or clone this repo

```bash
git clone https://github.com/<you>/catalyst-desk.git
cd catalyst-desk
```

### 2. Edit your portfolio

Open `portfolio.yaml` and replace the placeholder stocks with your holdings.
For each stock you need:

- `symbol`   — NSE trading symbol (e.g. `RELIANCE`, `TCS`)
- `bse_code` — BSE numeric code (look up at bseindia.com — e.g. `500325`)
- `name`     — Full company name (used to match news headlines)
- `sector`   — Optional, used for sector grouping in the dashboard

### 3. Get a free Gemini API key

Visit https://aistudio.google.com/apikey, sign in with a Google account, and
create an API key. No credit card required. Free tier limits at the time of
writing: 15 RPM, 1,500 requests per day.

### 4. Add the key as a GitHub Actions secret

In your repo on GitHub: **Settings → Secrets and variables → Actions → New
repository secret**

- Name: `GEMINI_API_KEY`
- Value: paste your key

### 5. Test locally (optional but recommended)

```bash
pip install -r requirements.txt
export GEMINI_API_KEY=your-key-here
python -m scripts.run_daily
```

You should see `reports/YYYY-MM-DD.json` and `reports/latest.json` populated.

### 6. Test the dashboard locally

```bash
cd dashboard
npm install
npm run dev
```

Open http://localhost:3000.

If you don't have a Gemini key yet, generate placeholder data first:

```bash
python -m scripts.make_sample
```

### 7. Deploy the dashboard to Vercel

- Sign up at https://vercel.com (free)
- Import your GitHub repo
- Vercel auto-detects Next.js. Use the `vercel.json` settings already in this
  repo (root build command is set to `cd dashboard && npm install && npm run build`)
- Deploy. Each commit to `main` triggers a redeploy, so when GitHub Actions
  pushes a new report, Vercel rebuilds the dashboard with the latest data.

### 8. Enable the daily cron

The workflow file is at `.github/workflows/daily.yml` and is already set to
run at 03:30 UTC (09:00 IST) Mon–Fri. It triggers automatically once you push
to GitHub. To run it manually for testing, go to **Actions → Daily Portfolio
Report → Run workflow**.

## What the dashboard shows

Every stock card shows:

- **Classification badge** — one of four states:
  - 🟢 `Catalyst → Move` — story checks out
  - 🔴 `Move w/o Catalyst` — possible flow/leak (highest signal)
  - 🟡 `Catalyst w/o Move` — possible lag setup
  - ⚫ `No Signal` — quiet day
- **Primary catalyst** — the dominant driver, in plain English
- **Analyst note** — 2-3 sentences from Gemini correlating catalyst & price
- **Confidence** — high / medium / low
- **Flags** — including `POSSIBLE_LEAK_OR_FLOW` for unexplained moves
- **Metrics** — Open, intraday range, volume, volume ratio (highlighted if ≥1.5×)
- **Catalysts list** — filings, news, SEBI items with sources and direct links

Cards are sorted: anomalies first, then biggest movers, then quiet stocks.

## Costs

| Component | Cost |
|---|---|
| GitHub Actions | Free (unlimited for public repos; 2000 min/mo for private — you'll use ~5/day) |
| Gemini API | Free (1500 req/day; 5-stock portfolio uses ~5) |
| Vercel | Free (Hobby tier) |
| yfinance / BSE / NSE / Google News / SEBI | Free |
| **Total** | **₹0/month** |

## Troubleshooting

**No data for a stock?** Check that `symbol` matches the NSE ticker exactly
and `bse_code` is correct. Run `python -m scripts.run_daily` locally to see
which collector failed.

**NSE collector returns empty?** NSE blocks unauth'd scrapers. The collector
warms cookies first, but if NSE changes its anti-bot rules the collector will
break. BSE is more stable; the dashboard works fine with just BSE data.

**Gemini analysis says "Automated analysis unavailable"?** The Gemini call
failed (rate limit, network, malformed JSON). Raw catalysts are still shown.
Re-run; usually transient.

**GitHub Actions doesn't fire on holidays?** Yes, the cron runs Mon–Fri but
doesn't know about NSE holidays. The pipeline gracefully handles this — when
prices are stale, the LLM flags it and you see a quiet day.

## Project layout

```
catalyst-desk/
├── portfolio.yaml             your tickers
├── requirements.txt           Python deps
├── collectors/                data sources
│   ├── common.py
│   ├── prices.py
│   ├── bse_announcements.py
│   ├── nse_announcements.py
│   ├── news.py
│   ├── earnings.py
│   └── sebi.py
├── analyzer/
│   ├── prompts.py             LLM prompt template
│   └── correlator.py          Gemini call + retries
├── scripts/
│   ├── run_daily.py           orchestrator
│   └── make_sample.py         dev fixtures
├── reports/                   YYYY-MM-DD.json, latest.json, index.json
├── dashboard/                 Next.js app
│   ├── app/
│   ├── components/
│   ├── lib/reports.ts
│   └── tailwind.config.ts
├── .github/workflows/
│   └── daily.yml              03:30 UTC cron
└── vercel.json
```

## Roadmap (when you want more)

- Holiday-aware scheduling (skip NSE holidays)
- Earnings preview mode (T-1 before scheduled results)
- Sector-level summaries
- Price-action history charts beyond sparklines
- Telegram or email push alerts on `move_without_catalyst` flags
- Integration with a broker (Kite/Upstox) to pull holdings automatically

These are deliberately not built yet — the MVP earns its keep first.
