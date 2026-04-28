import { useEffect, useState } from 'react';
import {
  Chart as ChartJS, ArcElement, Tooltip, Legend,
  CategoryScale, LinearScale, BarElement,
  LineElement, PointElement, Filler,
} from 'chart.js';
import { Doughnut, Bar, Line } from 'react-chartjs-2';
import {
  Calculator, ArrowRight, TrendingUp, Clock, IndianRupee,
  AlertTriangle, CheckCircle, Info, BrainCircuit, Loader2,
  Download, ExternalLink, ChevronDown, ChevronUp,
} from 'lucide-react';
import { universitiesAPI } from '../api/universities';
import { financeAPI } from '../api/finance';
import Markdown from 'react-markdown';
import { saveAs } from 'file-saver';

ChartJS.register(
  ArcElement, Tooltip, Legend,
  CategoryScale, LinearScale, BarElement,
  LineElement, PointElement, Filler,
);

// ── Constants ─────────────────────────────────────────────────────────────────
const INR_TO_USD = 1 / 83;

const CAREER_OPTIONS = [
  'Software Engineer', 'Data Scientist', 'Machine Learning Engineer',
  'Product Manager', 'Management Consultant', 'Investment Banker',
  'Financial Analyst', 'Data Analyst', 'Business Analyst',
  'Mechanical Engineer', 'Civil Engineer', 'Electrical Engineer',
  'Marketing Manager', 'UX Designer', 'Researcher / PhD',
  'Doctor / Medicine', 'Lawyer', 'Accountant', 'Architect',
];

const CHART_COLORS = {
  lavender: 'rgba(139, 92, 246, 0.85)',
  lavenderLight: 'rgba(139, 92, 246, 0.15)',
  teal: 'rgba(20, 184, 166, 0.85)',
  tealLight: 'rgba(20, 184, 166, 0.15)',
  amber: 'rgba(245, 158, 11, 0.85)',
  rose: 'rgba(244, 63, 94, 0.85)',
  sky: 'rgba(14, 165, 233, 0.85)',
};

// ── Helpers ───────────────────────────────────────────────────────────────────
function fmtINR(n, decimals = 1) {
  if (!n && n !== 0) return '—';
  if (n >= 10000000) return `₹${(n / 10000000).toFixed(decimals)} Cr`;
  if (n >= 100000)   return `₹${(n / 100000).toFixed(decimals)} L`;
  if (n >= 1000)     return `₹${(n / 1000).toFixed(0)}k`;
  return `₹${Math.round(n)}`;
}

function fmtINRFull(n) {
  if (!n && n !== 0) return '₹0';
  return `₹${Math.round(n).toLocaleString('en-IN')}`;
}

function riskLevel(breakEven, roi5, loanINR, totalInv) {
  let score = 0;
  if (breakEven > 10) score += 3;
  else if (breakEven > 7) score += 2;
  else if (breakEven > 5) score += 1;
  if (roi5 < 0)   score += 3;
  else if (roi5 < 30) score += 1;
  const loanRatio = totalInv > 0 ? loanINR / totalInv : 0;
  if (loanRatio > 0.7) score += 2;
  else if (loanRatio > 0.5) score += 1;
  if (score >= 5) return { label: 'High Risk', color: 'text-rose-500', bg: 'bg-rose-50 border-rose-200', icon: AlertTriangle };
  if (score >= 3) return { label: 'Moderate', color: 'text-amber-500', bg: 'bg-amber-50 border-amber-200', icon: Info };
  return { label: 'Low Risk', color: 'text-teal-600', bg: 'bg-teal-50 border-teal-200', icon: CheckCircle };
}

function buildTSV(results, inputs) {
  // Tab-separated for pasting directly into Google Sheets
  const { country, studyDuration, careerGoal } = inputs;
  const { total_investment_inr, year1_salary_inr, break_even_year,
          roi_5yr, roi_10yr, emi_monthly_inr, projections, cost_breakdown } = results;

  const lines = [
    ['PathPilot ROI Analysis'],
    [],
    ['SUMMARY'],
    ['Country', country],
    ['Career Goal', careerGoal],
    ['Study Duration (yrs)', studyDuration],
    [],
    ['COST BREAKDOWN', 'INR', 'Approx USD'],
    ['Total Tuition', cost_breakdown.tuition_total, Math.round(cost_breakdown.tuition_total * INR_TO_USD)],
    ['Total Living', cost_breakdown.living_total, Math.round(cost_breakdown.living_total * INR_TO_USD)],
    ['Loan Interest', cost_breakdown.loan_interest, Math.round(cost_breakdown.loan_interest * INR_TO_USD)],
    ['TOTAL INVESTMENT', total_investment_inr, Math.round(total_investment_inr * INR_TO_USD)],
    [],
    ['ROI METRICS'],
    ['Yr-1 Expected Salary', year1_salary_inr, Math.round(year1_salary_inr * INR_TO_USD)],
    ['Monthly EMI', emi_monthly_inr, Math.round(emi_monthly_inr * INR_TO_USD)],
    ['Break-Even Year', break_even_year],
    ['5-Year ROI', `${roi_5yr}%`],
    ['10-Year ROI', `${roi_10yr}%`],
    [],
    ['10-YEAR PROJECTION'],
    ['Year','Annual Salary (INR)','Loan EMI (INR)','Net Annual (INR)','Cumulative Earnings (INR)','Net vs Investment (INR)'],
    ...projections.map(p => [
      `Year ${p.year}`, p.salary_inr, p.emi_inr, p.net_annual_inr,
      p.cumulative_earnings_inr, p.net_position_inr,
    ]),
  ];
  return lines.map(r => r.join('\t')).join('\n');
}

// kept for reference — actual download now goes through backend
function exportToCSV(inputs, results) {
  const { country, studyDuration, careerGoal } = inputs;
  const { total_investment_inr, year1_salary_inr, break_even_year, roi_5yr, roi_10yr,
          cost_breakdown, projections, emi_monthly_inr } = results;

  const rows = [
    ['PathPilot ROI Analysis'],
    [''],
    ['SUMMARY'],
    ['Country', country],
    ['Career Goal', careerGoal],
    ['Study Duration (yrs)', studyDuration],
    [''],
    ['COST BREAKDOWN', 'INR', 'Approx USD'],
    ['Total Tuition', cost_breakdown.tuition_total, Math.round(cost_breakdown.tuition_total * INR_TO_USD)],
    ['Total Living', cost_breakdown.living_total, Math.round(cost_breakdown.living_total * INR_TO_USD)],
    ['Loan Interest', cost_breakdown.loan_interest, Math.round(cost_breakdown.loan_interest * INR_TO_USD)],
    ['Scholarship Savings', -cost_breakdown.scholarship_savings, Math.round(-cost_breakdown.scholarship_savings * INR_TO_USD)],
    ['TOTAL INVESTMENT', total_investment_inr, Math.round(total_investment_inr * INR_TO_USD)],
    [''],
    ['ROI METRICS'],
    ['Yr-1 Expected Salary', year1_salary_inr, Math.round(year1_salary_inr * INR_TO_USD)],
    ['Monthly Loan EMI', emi_monthly_inr, Math.round(emi_monthly_inr * INR_TO_USD)],
    ['Break-Even Year', break_even_year],
    ['5-Year ROI', `${roi_5yr}%`],
    ['10-Year ROI', `${roi_10yr}%`],
    [''],
    ['10-YEAR PROJECTION'],
    ['Year', 'Annual Salary (INR)', 'Loan EMI (INR)', 'Net Annual (INR)', 'Cumulative Earnings (INR)', 'Net Position vs Investment (INR)'],
    ...projections.map(p => [
      p.year, p.salary_inr, p.emi_inr, p.net_annual_inr,
      p.cumulative_earnings_inr, p.net_position_inr,
    ]),
  ];

  const csv = rows.map(r =>
    r.map(cell => {
      const s = String(cell ?? '');
      return s.includes(',') || s.includes('"') || s.includes('\n')
        ? `"${s.replace(/"/g, '""')}"` : s;
    }).join(',')
  ).join('\r\n');

  const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8' });
  saveAs(blob, `PathPilot_ROI_${country.replace(/\s+/g, '_')}.csv`);
}

// ── Main Component ─────────────────────────────────────────────────────────────
export default function Finance() {
  const [benchmarks, setBenchmarks] = useState([]);
  const [countries, setCountries]   = useState([]);
  const [country, setCountry]       = useState('United States');
  const [tuitionINR, setTuition]    = useState(3750000);
  const [livingINR, setLiving]      = useState(1300000);
  const [loanINR, setLoan]          = useState(1500000);
  const [duration, setDuration]     = useState(2);
  const [scholarship, setScholarship] = useState(0);
  const [budgetINR, setBudget]      = useState(0);
  const [careerGoal, setCareerGoal] = useState('Software Engineer');
  const [salaryOverride, setSalaryOverride] = useState('');

  const [results, setResults]       = useState(null);
  const [loading, setLoading]       = useState(false);
  const [error, setError]           = useState('');
  const [showAdvice, setShowAdvice] = useState(false);
  const [showTable, setShowTable]   = useState(false);

  // Load benchmarks
  useEffect(() => {
    universitiesAPI.getFinanceBenchmarks()
      .then(res => {
        const bench = Array.isArray(res?.benchmarks) ? res.benchmarks : [];
        const cList  = Array.isArray(res?.countries) ? res.countries : [];
        setBenchmarks(bench);
        setCountries(cList.filter(c => ['United States','United Kingdom','Canada','Australia',
          'Germany','France','Netherlands','Ireland','Singapore','Japan','Sweden','Norway',
          'Denmark','Finland','New Zealand','UAE','Spain','Italy','South Korea','Switzerland'].includes(c)));
      })
      .catch(() => {});
  }, []);

  // Auto-fill when country changes
  useEffect(() => {
    const b = benchmarks.find(b => b.country === country);
    if (b) {
      setTuition(Math.round(b.avg_tuition || 3750000));
      setLiving(Math.round(b.avg_living_cost || 1300000));
      setLoan(Math.round((b.avg_tuition || 3750000) * 0.4));
    }
  }, [country, benchmarks]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setResults(null);
    try {
      const res = await financeAPI.getROIAnalysis({
        country,
        tuition_inr: Number(tuitionINR),
        living_inr: Number(livingINR),
        loan_inr: Number(loanINR),
        study_duration: Number(duration),
        career_goal: careerGoal,
        scholarship_inr: Number(scholarship),
        budget_inr: Number(budgetINR),
        salary_inr: salaryOverride ? Number(salaryOverride) : null,
      });
      setResults(res);
      setShowAdvice(true);
    } catch (err) {
      setError(err.response?.status === 401 ? 'Please log in to use the ROI analyzer.' : 'Calculation failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const risk = results
    ? riskLevel(results.break_even_year, results.roi_5yr, loanINR, results.total_investment_inr)
    : null;

  return (
    <div className="space-y-6 animate-fade-in pb-10">
      {/* Header */}
      <div className="page-header">
        <div className="page-icon bg-mintLight text-teal-600"><Calculator className="w-5 h-5" /></div>
        <div>
          <h1 className="text-2xl font-bold text-text">Financial ROI Analyzer</h1>
          <p className="text-sm text-muted">All values in ₹ INR · Deterministic projections · AI advisor</p>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-5 gap-6">

        {/* ── Input Panel ──────────────────────────────────────────────────── */}
        <div className="xl:col-span-2 card p-6 space-y-5 self-start">
          <h2 className="font-bold text-text text-base">Your Study Scenario</h2>

          <div>
            <Label>Destination Country</Label>
            <select className="input-field" value={country} onChange={e => setCountry(e.target.value)}>
              {(countries.length ? countries : ['United States']).map(c => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <INRInput label="Tuition / yr" value={tuitionINR} onChange={setTuition} />
              <INRInput label="Living cost / yr" value={livingINR} onChange={setLiving} />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <INRInput label="Education loan (total)" value={loanINR} onChange={setLoan} hint="8.5% p.a." />
              <INRInput label="Scholarship / yr" value={scholarship} onChange={setScholarship} hint="optional" />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label>Duration</Label>
                <select className="input-field" value={duration} onChange={e => setDuration(Number(e.target.value))}>
                  {[1,2,3,4,5].map(y => <option key={y} value={y}>{y} yr{y>1?'s':''}</option>)}
                </select>
              </div>
              <INRInput label="Annual budget cap" value={budgetINR} onChange={setBudget} hint="0 = no limit" />
            </div>

            <div>
              <Label>Career Goal</Label>
              <select className="input-field" value={careerGoal} onChange={e => setCareerGoal(e.target.value)}>
                {CAREER_OPTIONS.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>

            <div>
              <Label>Expected starting salary / yr <span className="text-muted font-normal">(optional override)</span></Label>
              <div className="relative">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted text-sm font-semibold">₹</span>
                <input
                  type="number" className="input-field pl-7"
                  value={salaryOverride} onChange={e => setSalaryOverride(e.target.value)}
                  placeholder="Auto-estimated from benchmarks" min="0"
                />
              </div>
            </div>

            {error && (
              <p className="text-xs text-rose-500 flex items-center gap-1.5">
                <AlertTriangle className="w-3.5 h-3.5" />{error}
              </p>
            )}

            <button type="submit" className="btn-primary w-full" disabled={loading}>
              {loading
                ? <><Loader2 className="w-4 h-4 animate-spin" /> Analyzing…</>
                : <><Calculator className="w-4 h-4" /> Calculate ROI <ArrowRight className="w-4 h-4" /></>
              }
            </button>
          </form>

          {/* Quick cost preview (live, no submit needed) */}
          <CostPreview
            tuition={Number(tuitionINR)} living={Number(livingINR)}
            loan={Number(loanINR)} duration={Number(duration)}
            scholarship={Number(scholarship)}
          />
        </div>

        {/* ── Results Panel ─────────────────────────────────────────────────── */}
        <div className="xl:col-span-3 space-y-5">
          {loading && <LoadingCard country={country} />}

          {!loading && !results && <EmptyState />}

          {results && !loading && (
            <>
              {/* KPI row */}
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                <KPI label="Total Investment" value={fmtINR(results.total_investment_inr)}
                  sub={`~$${Math.round(results.total_investment_inr * INR_TO_USD / 1000)}k`}
                  icon={IndianRupee} color="text-lavender" bg="bg-lavendLight" />
                <KPI label="Year 1 Salary" value={fmtINR(results.year1_salary_inr)}
                  sub={`~$${Math.round(results.year1_salary_inr * INR_TO_USD / 1000)}k/yr`}
                  icon={TrendingUp} color="text-teal-600" bg="bg-mintLight" />
                <KPI label="Break-Even"
                  value={results.break_even_year > 12 ? '12+ yrs' : `${results.break_even_year} yr${results.break_even_year !== 1 ? 's' : ''}`}
                  sub="post graduation"
                  icon={Clock} color="text-amber-600" bg="bg-amber-50" />
                <KPI label="5-Year ROI" value={`${results.roi_5yr > 0 ? '+' : ''}${results.roi_5yr}%`}
                  sub="return on investment"
                  icon={TrendingUp} color={results.roi_5yr >= 0 ? 'text-teal-600' : 'text-rose-500'} bg="bg-surfaceAlt" />
                <KPI label="10-Year ROI" value={`${results.roi_10yr > 0 ? '+' : ''}${results.roi_10yr}%`}
                  sub="return on investment"
                  icon={TrendingUp} color={results.roi_10yr >= 50 ? 'text-teal-600' : 'text-amber-500'} bg="bg-surfaceAlt" />
                <div className={`rounded-xl p-3 border ${risk.bg} flex flex-col justify-between`}>
                  <p className="text-[10px] text-muted uppercase tracking-wide font-semibold mb-1">Risk Level</p>
                  <div className="flex items-center gap-1.5">
                    <risk.icon className={`w-4 h-4 ${risk.color}`} />
                    <p className={`text-sm font-bold ${risk.color}`}>{risk.label}</p>
                  </div>
                  {results.emi_monthly_inr > 0 && (
                    <p className="text-[10px] text-muted mt-1">
                      EMI: {fmtINR(results.emi_monthly_inr, 0)}/mo
                    </p>
                  )}
                </div>
              </div>

              {/* Charts row */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                <BreakevenChart results={results} />
                <CostDoughnut breakdown={results.cost_breakdown} />
              </div>

              <SalaryBarChart projections={results.projections} totalInv={results.total_investment_inr} />

              {/* AI Advice */}
              {results.advice && (
                <div className="card overflow-hidden">
                  <button
                    onClick={() => setShowAdvice(v => !v)}
                    className="w-full flex items-center justify-between p-4 hover:bg-surfaceAlt transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <div className="page-icon bg-lavendLight text-lavender w-9 h-9">
                        <BrainCircuit className="w-4 h-4" />
                      </div>
                      <div className="text-left">
                        <p className="font-bold text-text text-sm">AI Financial Advisor</p>
                        <p className="text-xs text-muted">Personalised advice for {careerGoal} in {country}</p>
                      </div>
                    </div>
                    {showAdvice ? <ChevronUp className="w-4 h-4 text-muted" /> : <ChevronDown className="w-4 h-4 text-muted" />}
                  </button>
                  {showAdvice && (
                    <div className="px-5 pb-5 border-t border-surfaceBorder pt-4">
                      <div className="prose prose-sm max-w-none text-textSoft [&_ul]:space-y-1.5 [&_li]:text-sm">
                        <Markdown>{results.advice}</Markdown>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Projection table (collapsible) */}
              <div className="card overflow-hidden">
                <button
                  onClick={() => setShowTable(v => !v)}
                  className="w-full flex items-center justify-between p-4 hover:bg-surfaceAlt transition-colors"
                >
                  <p className="font-bold text-text text-sm">10-Year Projection Table</p>
                  {showTable ? <ChevronUp className="w-4 h-4 text-muted" /> : <ChevronDown className="w-4 h-4 text-muted" />}
                </button>
                {showTable && (
                  <div className="overflow-x-auto border-t border-surfaceBorder">
                    <table className="w-full text-xs">
                      <thead>
                        <tr className="bg-surfaceAlt text-muted">
                          {['Year','Annual Salary','Loan EMI','Net Annual','Cumulative Earnings','vs Investment'].map(h => (
                            <th key={h} className="px-3 py-2 text-left font-semibold whitespace-nowrap">{h}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {results.projections.map((p, i) => (
                          <tr key={p.year} className={`border-t border-surfaceBorder ${i % 2 === 0 ? '' : 'bg-surfaceAlt/40'} ${p.net_position_inr >= 0 ? 'bg-teal-50/30' : ''}`}>
                            <td className="px-3 py-2 font-bold text-text">Yr {p.year}</td>
                            <td className="px-3 py-2 text-teal-600 font-medium">{fmtINR(p.salary_inr)}</td>
                            <td className="px-3 py-2 text-rose-500">{p.emi_inr > 0 ? `-${fmtINR(p.emi_inr)}` : '—'}</td>
                            <td className={`px-3 py-2 font-medium ${p.net_annual_inr >= 0 ? 'text-teal-600' : 'text-rose-500'}`}>
                              {fmtINR(p.net_annual_inr)}
                            </td>
                            <td className="px-3 py-2">{fmtINR(p.cumulative_earnings_inr)}</td>
                            <td className={`px-3 py-2 font-bold ${p.net_position_inr >= 0 ? 'text-teal-600' : 'text-rose-500'}`}>
                              {p.net_position_inr >= 0 ? '+' : ''}{fmtINR(p.net_position_inr)}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>

              {/* Export row */}
              <ExportBar
                country={country} duration={duration} careerGoal={careerGoal}
                tuitionINR={tuitionINR} livingINR={livingINR} loanINR={loanINR}
                scholarship={scholarship} results={results}
              />
            </>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Sub-components ─────────────────────────────────────────────────────────────

function ExportBar({ country, duration, careerGoal, tuitionINR, livingINR, loanINR, scholarship, results }) {
  const [copied, setCopied]     = useState(false);
  const [showSteps, setShowSteps] = useState(false);
  const [dlError, setDlError]   = useState('');

  const handleDownload = async () => {
    setDlError('');
    try {
      const params = new URLSearchParams({
        country,
        tuition_inr:     tuitionINR,
        living_inr:      livingINR,
        loan_inr:        loanINR,
        study_duration:  duration,
        career_goal:     careerGoal,
        scholarship_inr: scholarship,
      });
      const BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api/v1';
      const token = localStorage.getItem('token') || '';
      const res = await fetch(`${BASE}/finance/export-csv?${params}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error(`Server error ${res.status}`);
      const blob = await res.blob();
      const url  = URL.createObjectURL(blob);
      const a    = document.createElement('a');
      a.href     = url;
      a.download = `PathPilot_ROI_${country.replace(/\s+/g, '_')}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      setTimeout(() => URL.revokeObjectURL(url), 2000);
    } catch (err) {
      setDlError(err.message);
    }
  };

  const handleCopyToSheets = async () => {
    const tsv = buildTSV(results, { country, studyDuration: duration, careerGoal });
    try {
      await navigator.clipboard.writeText(tsv);
      setCopied(true);
      setShowSteps(true);
      setTimeout(() => setCopied(false), 4000);
      window.open('https://sheets.new', '_blank');
    } catch {
      alert('Clipboard access denied. Please allow clipboard permissions in your browser.');
    }
  };

  return (
    <div className="space-y-3">
      <div className="flex gap-3 flex-wrap items-center">
        <button onClick={handleDownload} className="btn-secondary flex items-center gap-2 text-sm">
          <Download className="w-4 h-4" /> Download .csv
        </button>
        <button
          onClick={handleCopyToSheets}
          className={`btn-secondary flex items-center gap-2 text-sm transition-colors ${copied ? 'border-teal-400 text-teal-600' : 'text-lavender'}`}
        >
          <ExternalLink className="w-4 h-4" />
          {copied ? '✓ Copied to clipboard!' : 'Open in Google Sheets'}
        </button>
      </div>

      {dlError && (
        <p className="text-xs text-rose-500 flex items-center gap-1.5">
          <AlertTriangle className="w-3.5 h-3.5" /> Download error: {dlError}
        </p>
      )}

      {/* Google Sheets step-by-step instructions */}
      {showSteps && (
        <div className="bg-teal-50 border border-teal-200 rounded-xl p-4 text-sm space-y-2">
          <p className="font-bold text-teal-800 flex items-center gap-2">
            <ExternalLink className="w-4 h-4" /> How to paste into Google Sheets
          </p>
          <ol className="space-y-1.5 text-teal-700 list-decimal list-inside text-xs leading-relaxed">
            <li>A new Google Sheet just opened in your browser (or click <a href="https://sheets.new" target="_blank" rel="noreferrer" className="underline font-medium">sheets.new</a>)</li>
            <li>Click on cell <strong>A1</strong> in the empty spreadsheet</li>
            <li>Press <kbd className="bg-white border border-teal-300 rounded px-1.5 py-0.5 font-mono text-[11px]">Ctrl+V</kbd> (Windows) or <kbd className="bg-white border border-teal-300 rounded px-1.5 py-0.5 font-mono text-[11px]">⌘V</kbd> (Mac) to paste</li>
            <li>All rows and columns will auto-fill — your full 10-year ROI projection is now in Sheets!</li>
          </ol>
          <button onClick={() => setShowSteps(false)} className="text-xs text-teal-500 underline mt-1">Dismiss</button>
        </div>
      )}
    </div>
  );
}

function Label({ children }) {
  return <label className="block text-xs font-semibold text-muted uppercase tracking-wide mb-1">{children}</label>;
}

function INRInput({ label, value, onChange, hint }) {
  return (
    <div>
      <label className="block text-xs font-semibold text-muted uppercase tracking-wide mb-1">
        {label} {hint && <span className="text-muted font-normal normal-case">· {hint}</span>}
      </label>
      <div className="relative">
        <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted text-sm font-semibold">₹</span>
        <input
          type="number" className="input-field !pl-8"
          value={value} onChange={e => onChange(e.target.value)}
          min="0"
        />
      </div>
      <p className="text-[10px] text-muted mt-0.5">{fmtINR(Number(value))}</p>
    </div>
  );
}

function CostPreview({ tuition, living, loan, duration, scholarship }) {
  const annual = tuition + living - scholarship;
  const total = annual * duration + loan * 0.085 * duration;
  return (
    <div className="bg-surfaceAlt rounded-xl p-4 space-y-1.5 text-xs border border-surfaceBorder">
      <p className="font-bold text-text text-sm mb-2">Live Cost Preview</p>
      <PreviewRow label="Annual net cost" val={fmtINR(annual)} />
      <PreviewRow label={`Total study cost (${duration} yr)`} val={fmtINR(annual * duration)} />
      {loan > 0 && <PreviewRow label={`Loan interest (8.5%)`} val={fmtINR(loan * 0.085 * duration)} />}
      <div className="border-t border-surfaceBorder pt-1.5 mt-1">
        <PreviewRow label="Est. total investment" val={fmtINR(total)} bold />
      </div>
    </div>
  );
}

function PreviewRow({ label, val, bold }) {
  return (
    <div className="flex justify-between">
      <span className="text-muted">{label}</span>
      <span className={bold ? 'font-bold text-text' : 'font-medium text-textSoft'}>{val}</span>
    </div>
  );
}

function KPI({ label, value, sub, icon: Icon, color, bg }) {
  return (
    <div className={`rounded-xl p-3 ${bg}`}>
      <div className="flex items-center gap-1.5 mb-1">
        <Icon className={`w-3.5 h-3.5 ${color}`} />
        <p className="text-[10px] text-muted uppercase tracking-wide font-semibold">{label}</p>
      </div>
      <p className={`text-base font-black ${color}`}>{value}</p>
      {sub && <p className="text-[10px] text-muted mt-0.5">{sub}</p>}
    </div>
  );
}

function BreakevenChart({ results }) {
  const { projections, total_investment_inr, break_even_year } = results;
  const labels = projections.map(p => `Yr ${p.year}`);
  const earnings = projections.map(p => p.cumulative_earnings_inr);
  const invLine  = projections.map(() => total_investment_inr);

  const data = {
    labels,
    datasets: [
      {
        label: 'Cumulative Earnings',
        data: earnings,
        borderColor: CHART_COLORS.teal,
        backgroundColor: CHART_COLORS.tealLight,
        fill: true,
        tension: 0.4,
        pointRadius: 3,
      },
      {
        label: 'Total Investment',
        data: invLine,
        borderColor: CHART_COLORS.rose,
        borderDash: [6, 3],
        borderWidth: 2,
        backgroundColor: 'transparent',
        pointRadius: 0,
      },
    ],
  };

  const options = {
    responsive: true,
    plugins: {
      legend: { position: 'bottom', labels: { font: { size: 11 }, boxWidth: 12 } },
      tooltip: {
        callbacks: {
          label: ctx => `${ctx.dataset.label}: ${fmtINR(ctx.raw)}`,
        },
      },
    },
    scales: {
      y: {
        ticks: {
          callback: v => fmtINR(v, 0),
          font: { size: 10 },
          maxTicksLimit: 6,
        },
        grid: { color: 'rgba(0,0,0,0.05)' },
      },
      x: { ticks: { font: { size: 10 } }, grid: { display: false } },
    },
  };

  return (
    <div className="card p-4">
      <p className="font-bold text-text text-sm mb-1">Break-Even Chart</p>
      <p className="text-xs text-muted mb-3">
        {break_even_year <= 12
          ? `Earnings cross investment at Year ${break_even_year}`
          : 'Break-even beyond 12-year window'}
      </p>
      <Line data={data} options={options} />
    </div>
  );
}

function CostDoughnut({ breakdown }) {
  const items = [
    { label: 'Tuition', val: breakdown.tuition_total, color: CHART_COLORS.lavender },
    { label: 'Living', val: breakdown.living_total, color: CHART_COLORS.sky },
    { label: 'Loan Interest', val: breakdown.loan_interest, color: CHART_COLORS.amber },
  ].filter(i => i.val > 0);

  const data = {
    labels: items.map(i => i.label),
    datasets: [{
      data: items.map(i => i.val),
      backgroundColor: items.map(i => i.color),
      borderWidth: 2,
      borderColor: '#fff',
    }],
  };

  const options = {
    responsive: true,
    cutout: '62%',
    plugins: {
      legend: { position: 'bottom', labels: { font: { size: 11 }, boxWidth: 12 } },
      tooltip: {
        callbacks: {
          label: ctx => ` ${ctx.label}: ${fmtINR(ctx.raw)}`,
        },
      },
    },
  };

  return (
    <div className="card p-4 flex flex-col">
      <p className="font-bold text-text text-sm mb-1">Cost Breakdown</p>
      {breakdown.scholarship_savings > 0 && (
        <p className="text-xs text-teal-600 mb-2">
          ✓ Scholarship saves {fmtINR(breakdown.scholarship_savings)}
        </p>
      )}
      <div className="flex-1 flex items-center justify-center">
        <Doughnut data={data} options={options} />
      </div>
    </div>
  );
}

function SalaryBarChart({ projections, totalInv }) {
  const data = {
    labels: projections.map(p => `Yr ${p.year}`),
    datasets: [
      {
        label: 'Annual Salary',
        data: projections.map(p => p.salary_inr),
        backgroundColor: CHART_COLORS.lavender,
        borderRadius: 4,
      },
      {
        label: 'Loan EMI',
        data: projections.map(p => -p.emi_inr),
        backgroundColor: CHART_COLORS.rose,
        borderRadius: 4,
      },
    ],
  };

  const options = {
    responsive: true,
    plugins: {
      legend: { position: 'bottom', labels: { font: { size: 11 }, boxWidth: 12 } },
      tooltip: {
        callbacks: {
          label: ctx => `${ctx.dataset.label}: ${fmtINR(Math.abs(ctx.raw))}`,
        },
      },
    },
    scales: {
      y: {
        ticks: {
          callback: v => fmtINR(Math.abs(v), 0),
          font: { size: 10 },
          maxTicksLimit: 6,
        },
        grid: { color: 'rgba(0,0,0,0.05)' },
      },
      x: { ticks: { font: { size: 10 } }, grid: { display: false } },
    },
  };

  return (
    <div className="card p-4">
      <p className="font-bold text-text text-sm mb-1">Salary Growth vs Loan Repayment</p>
      <p className="text-xs text-muted mb-3">8% annual salary growth · 7-year loan repayment at 8.5% p.a.</p>
      <Bar data={data} options={options} />
    </div>
  );
}

function LoadingCard({ country }) {
  return (
    <div className="card p-16 flex flex-col items-center justify-center text-center">
      <div className="page-icon bg-lavendLight text-lavender mb-4 w-14 h-14 animate-pulse">
        <BrainCircuit className="w-6 h-6" />
      </div>
      <p className="font-bold text-text mb-1">Crunching the numbers…</p>
      <p className="text-sm text-muted max-w-xs">
        Calculating your 10-year ROI projection for {country} and getting AI advice.
      </p>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="card p-16 flex flex-col items-center justify-center text-center">
      <div className="page-icon bg-lavendLight text-lavender mb-4 w-14 h-14">
        <Calculator className="w-6 h-6" />
      </div>
      <p className="font-bold text-text mb-1">Set your scenario &amp; calculate</p>
      <p className="text-sm text-muted max-w-xs">
        Enter your costs in ₹ INR, pick a career goal, and get instant ROI projections with AI advice.
      </p>
      <div className="mt-6 grid grid-cols-3 gap-4 text-center text-xs text-muted w-full max-w-sm">
        {[
          { icon: IndianRupee, label: 'All in ₹ INR' },
          { icon: TrendingUp, label: '10-yr projection' },
          { icon: Download, label: 'Export to Sheets' },
        ].map(({ icon: Icon, label }) => (
          <div key={label} className="bg-surfaceAlt rounded-xl p-3">
            <Icon className="w-5 h-5 text-lavender mx-auto mb-1" />
            <p>{label}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
