import { useEffect, useState } from 'react';
import { Chart as ChartJS, ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement } from 'chart.js';
import { Doughnut, Bar } from 'react-chartjs-2';
import { Calculator, ArrowRight, TrendingUp, Clock, DollarSign, AlertTriangle, CheckCircle, Info, ChevronDown, BrainCircuit } from 'lucide-react';
import { universitiesAPI } from '../api/universities';
import { financeAPI } from '../api/finance';
import Markdown from 'react-markdown';

ChartJS.register(ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement);

// ── Reference Data ────────────────────────────────────────────────────────────

const DEFAULT_BENCHMARK = {
  country: 'United States',
  university_count: 0,
  avg_tuition: 45000,
  avg_living_cost: 20000,
  avg_salary_usd: 78000,
  job_market_score: 9.0,
};

const COUNTRY_SYMBOLS = {
  'United States': '$',
  'United Kingdom': '£',
  Canada: 'C$',
  Australia: 'A$',
  Germany: '€',
  France: '€',
  Netherlands: '€',
  Ireland: '€',
  Singapore: 'S$',
  Japan: '¥',
  Sweden: 'kr',
  Norway: 'kr',
  Denmark: 'kr',
  Finland: '€',
  UAE: 'AED',
  'New Zealand': 'NZ$',
  Portugal: '€',
  Italy: '€',
  Spain: '€',
  'South Korea': '₩',
  Switzerland: 'CHF',
};

// ── Helpers ───────────────────────────────────────────────────────────────────

function computeRisk(breakEven, roi, totalCost, budget) {
  let risk = 0;
  if (breakEven > 10) risk += 35;
  else if (breakEven > 7) risk += 20;
  else if (breakEven > 5) risk += 10;

  if (roi < 50) risk += 25;
  else if (roi < 100) risk += 10;

  if (budget > 0 && totalCost > budget) risk += Math.min(30, ((totalCost - budget) / budget) * 60);

  if (risk >= 60) return { label: 'High Risk', color: 'text-rose-500', bg: 'bg-rose-50', icon: AlertTriangle };
  if (risk >= 35) return { label: 'Moderate Risk', color: 'text-amber-500', bg: 'bg-amber-50', icon: Info };
  return { label: 'Low Risk', color: 'text-teal-600', bg: 'bg-teal-50', icon: CheckCircle };
}

const fmt = (n, sym = '$') => `${sym}${Math.round(n).toLocaleString()}`;

// ── Component ─────────────────────────────────────────────────────────────────

export default function Finance() {
  const [countries, setCountries] = useState([]);
  const [benchmarks, setBenchmarks] = useState([]);
  const [country, setCountry]   = useState('');
  const [selected, setSelected] = useState(null);
  const [tuition, setTuition]   = useState(0);
  const [living, setLiving]     = useState(0);
  const [loan, setLoan]         = useState(0);
  const [yearsStudy, setYears]  = useState(2);
  const [budget, setBudget]     = useState(0);
  const [careerGoal, setCareerGoal] = useState('Software Engineer');
  const [results, setResults]   = useState(null);
  const [loading, setLoading] = useState(false);
  const [showDetails, setShowDetails] = useState(false);

  useEffect(() => {
    universitiesAPI.getFinanceBenchmarks()
      .then((res) => {
        const bench = Array.isArray(res?.benchmarks) ? res.benchmarks : [];
        const countryList = Array.isArray(res?.countries) ? res.countries : [];
        setBenchmarks(bench);
        setCountries(countryList);

        const initial = bench[0] || DEFAULT_BENCHMARK;
        setCountry(initial.country);
        setSelected(initial);
        setTuition(Math.round(initial.avg_tuition || 0));
        setLiving(Math.round(initial.avg_living_cost || 0));
        setLoan(Math.round((initial.avg_tuition || 0) * 0.5));
      })
      .catch(() => {
        setCountries([DEFAULT_BENCHMARK.country]);
        setBenchmarks([DEFAULT_BENCHMARK]);
        setCountry(DEFAULT_BENCHMARK.country);
        setSelected(DEFAULT_BENCHMARK);
        setTuition(DEFAULT_BENCHMARK.avg_tuition);
        setLiving(DEFAULT_BENCHMARK.avg_living_cost);
        setLoan(Math.round(DEFAULT_BENCHMARK.avg_tuition * 0.5));
      });
  }, []);

  useEffect(() => {
    const next = benchmarks.find(b => b.country === country) || DEFAULT_BENCHMARK;
    setSelected(next);
    setTuition(Math.round(next.avg_tuition || 0));
    setLiving(Math.round(next.avg_living_cost || 0));
    setLoan(Math.round((next.avg_tuition || 0) * 0.5));
  }, [country, benchmarks]);

  const sym = COUNTRY_SYMBOLS[country] || '$';

  const calculate = async (e) => {
    e.preventDefault();
    setLoading(true);
    setResults(null);

    try {
      const response = await financeAPI.getROIAnalysis({
        country,
        tuition,
        living_cost: living,
        loan_amount: loan,
        study_duration: yearsStudy,
        career_goal: careerGoal,
        budget,
      });

      // The response is a string containing a JSON object. We need to parse it.
      const analysisText = response.analysis.replace(/```json/g, '').replace(/```/g, '');
      const analysis = JSON.parse(analysisText);

      setResults(analysis);
    } catch (error) {
      console.error("Error fetching ROI analysis:", error);
      // Handle error state here
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="page-header">
        <div className="page-icon bg-mintLight text-teal-600">
          <Calculator className="w-5 h-5" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-text">Financial ROI Analyzer</h1>
          <p className="text-sm text-muted">AI-powered analysis · Real salary benchmarks · 10-year projection</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">

        {/* ── Input Panel ── */}
        <div className="lg:col-span-2 card p-6 space-y-5">
          <h2 className="font-bold text-text">Configure Your Scenario</h2>

          {/* Country benchmark */}
          <div>
            <label className="block text-xs font-semibold text-muted uppercase tracking-wide mb-2">Destination Country</label>
            <select className="input-field" value={country} onChange={e => setCountry(e.target.value)}>
              {(countries.length ? countries : [DEFAULT_BENCHMARK.country]).map(c => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>

          <form onSubmit={calculate} className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-semibold text-muted uppercase tracking-wide mb-1">Tuition/yr ({sym})</label>
                <input type="number" className="input-field" value={tuition}
                  onChange={e => setTuition(e.target.value)} min="0" />
              </div>
              <div>
                <label className="block text-xs font-semibold text-muted uppercase tracking-wide mb-1">Living/yr ({sym})</label>
                <input type="number" className="input-field" value={living}
                  onChange={e => setLiving(e.target.value)} min="0" />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-semibold text-muted uppercase tracking-wide mb-1">Loan ({sym})</label>
                <input type="number" className="input-field" value={loan}
                  onChange={e => setLoan(e.target.value)} min="0" />
              </div>
              <div>
                <label className="block text-xs font-semibold text-muted uppercase tracking-wide mb-1">Duration (yrs)</label>
                <select className="input-field" value={yearsStudy} onChange={e => setYears(Number(e.target.value))}>
                  {[1,2,3,4,5].map(y => <option key={y} value={y}>{y} year{y>1?'s':''}</option>)}
                </select>
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-muted uppercase tracking-wide mb-1">Annual Budget ({sym}, optional)</label>
              <input type="number" className="input-field" value={budget}
                onChange={e => setBudget(e.target.value)} min="0" placeholder="0 = skip budget check" />
            </div>

            <div>
              <label className="block text-xs font-semibold text-muted uppercase tracking-wide mb-1">Career Goal</label>
              <input type="text" className="input-field" value={careerGoal}
                onChange={e => setCareerGoal(e.target.value)} placeholder="e.g., Data Scientist" />
            </div>

            <button type="submit" className="btn-primary w-full" disabled={loading}>
              {loading ? 'Analyzing...' : <>Calculate ROI <ArrowRight className="w-4 h-4" /></>}
            </button>
          </form>
        </div>

        {/* ── Results Panel ── */}
        <div className="lg:col-span-3 space-y-4">
          {loading && (
            <div className="card p-16 flex flex-col items-center justify-center text-center">
              <div className="page-icon bg-lavendLight text-lavender mb-4 w-14 h-14 animate-pulse">
                <BrainCircuit className="w-6 h-6" />
              </div>
              <p className="font-bold text-text mb-1">AI is Analyzing Your Profile</p>
              <p className="text-sm text-muted max-w-xs">
                This may take a moment. The AI is considering your career goals, financial inputs, and the job market in {country}.
              </p>
            </div>
          )}

          {results ? (
            <div className="space-y-4">
              <div className="card p-5">
                <h3 className="font-bold text-lg text-text mb-2">ROI Analysis for a {careerGoal} in {country}</h3>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-center">
                  <MetricCard label="Total Investment" value={fmt(results.total_investment, sym)} icon={DollarSign} />
                  <MetricCard label="Expected Salary" value={fmt(results.expected_salary, '$') + '/yr'} icon={TrendingUp} />
                  <MetricCard label="Break-Even" value={`${results.break_even_years} yrs`} icon={Clock} />
                  <MetricCard label="5-Year ROI" value={`${results.roi_5_year}%`} icon={TrendingUp} />
                  <MetricCard label="10-Year ROI" value={`${results.roi_10_year}%`} icon={TrendingUp} />
                  <MetricCard label="Risk Assessment" value={results.risk_assessment} icon={AlertTriangle} />
                </div>
              </div>

              <div className="card p-5">
                <h3 className="font-bold text-lg text-text mb-2">Personalized Advice</h3>
                <div className="prose prose-sm max-w-none text-textSoft">
                  <Markdown>{results.personalized_advice}</Markdown>
                </div>
              </div>

               <div className="card p-5">
                <h3 className="font-bold text-lg text-text mb-2">Country Specific Data</h3>
                <div className="prose prose-sm max-w-none text-textSoft">
                  <Markdown>{results.country_specific_data}</Markdown>
                </div>
              </div>
            </div>
          ) : (
            !loading && <div className="card p-16 flex flex-col items-center justify-center text-center">
              <div className="page-icon bg-lavendLight text-lavender mb-4 w-14 h-14">
                <Calculator className="w-6 h-6" />
              </div>
              <p className="font-bold text-text mb-1">Configure &amp; Calculate</p>
              <p className="text-sm text-muted max-w-xs">
                Select a country, enter your financial details and career goals, and let our AI provide a detailed ROI analysis.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function MetricCard({ label, value, icon: Icon }) {
  return (
    <div className="bg-surfaceAlt p-4 rounded-lg">
      <div className="flex items-center justify-center text-muted mb-2">
        <Icon className="w-4 h-4 mr-2" />
        <h4 className="font-semibold text-xs uppercase tracking-wider">{label}</h4>
      </div>
      <p className="text-xl font-bold text-text">{value}</p>
    </div>
  );
}
