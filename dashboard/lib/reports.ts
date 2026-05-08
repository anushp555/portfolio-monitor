import fs from "node:fs/promises";
import path from "node:path";

export type Classification =
  | "catalyst_drove_move"
  | "move_without_catalyst"
  | "catalyst_without_move"
  | "no_signal"
  | "price_only";

export interface PriceAction {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  prev_close: number;
  change_pct: number;
  gap_pct: number;
  intraday_range_pct: number;
  volume: number;
  avg_volume_20d: number;
  volume_ratio: number;
  sparkline: number[];
  error?: string;
}

export interface NewsItem {
  title: string;
  source: string;
  url?: string;
  published_at?: string;
  summary?: string;
}

export interface Announcement {
  headline: string;
  category?: string;
  subcategory?: string;
  more_info?: string;
  pdf_url?: string | null;
  attached_at?: string;
  source: "BSE" | "NSE";
}

export interface Analysis {
  classification: Classification;
  primary_catalyst: string | null;
  analysis: string;
  confidence: "high" | "medium" | "low";
  flags: string[];
}

export interface StockEntry {
  symbol: string;
  name: string;
  sector?: string;
  notes?: string;
  skip_catalysts?: boolean;
  price_action: PriceAction;
  bse_announcements: Announcement[];
  nse_announcements: Announcement[];
  news: NewsItem[];
  events: Array<Record<string, unknown>>;
  sebi_mentions: Array<{ title?: string; published_at?: string; url?: string }>;
  analysis: Analysis;
}

export interface DailyReport {
  report_date: string;
  trading_day: string;
  generated_at: string;
  stocks: StockEntry[];
}

const REPORTS_DIR = path.join(process.cwd(), "..", "reports");

export async function loadLatestReport(): Promise<DailyReport | null> {
  try {
    const raw = await fs.readFile(path.join(REPORTS_DIR, "latest.json"), "utf-8");
    return JSON.parse(raw) as DailyReport;
  } catch {
    return null;
  }
}

export async function loadReportByDate(date: string): Promise<DailyReport | null> {
  try {
    const raw = await fs.readFile(path.join(REPORTS_DIR, `${date}.json`), "utf-8");
    return JSON.parse(raw) as DailyReport;
  } catch {
    return null;
  }
}

export async function listReportDates(): Promise<string[]> {
  try {
    const raw = await fs.readFile(path.join(REPORTS_DIR, "index.json"), "utf-8");
    const idx = JSON.parse(raw) as { reports: string[] };
    return idx.reports.sort().reverse();
  } catch {
    return [];
  }
}
