import { useState } from 'react';
import { Chart as ChartJS, ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement } from 'chart.js';
import { Doughnut, Bar } from 'react-chartjs-2';
import { Calculator, ArrowRight, TrendingUp, Clock, DollarSign, AlertTriangle, CheckCircle, Info, ChevronDown } from 'lucide-react';

ChartJS.register(ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement);

// ── Reference Data ────────────────────────────────────────────────────────────

const COUNTRY_PRESETS = {
  USA:         { tuition: 45000, living: 20000, salary: 78000, currency: 'USD', symbol: '$' },
  UK:          { tuition: 28000, living: 15000, salary: 54000, currency: 'GBP', symbol: '£' },
  Canada:      { tuition: 25000, living: 16000, salary: 62000, currency: 'CAD', symbol: 'C$' },
  Australia:   { tuition: 32000, living: 18000, salary: 64000, currency: 'AUD', symbol: 'A$' },
  Germany:     { tuition: 1000,  living: 12000, salary: 58000, currency: 'EUR', symbol: '€' },
  Netherlands: { tuition: 16000, living: 14000, salary: 55000, currency: 'EUR', symbol: '€' },
  Singapore:   { tuition: 30000, living: 18000, salary: 68000, currency: 'SGD', symbol: 'S$' },
  Ireland:     { tuition: 22000, living: 16000, salary: 62000, currency: 'EUR', symbol: '€' },
};

const FIELD_SALARY_MULTIPLIERS = {
  'Computer Science':  1.25,
  'Engineering':       1.15,
  'Data Science':      1.30,
  'Finance':           1.20,
  'Business':          1.05,
  'Medicine':          1.40,
  'Law':               1.15,
  'Economics':         1.10,
  'Architecture':      1.00,
  'Arts':              0.85,
  'Education':         0.90,
  'Other':             1.00,
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
const fmtK = (n, sym = '$') => `${sym}${(n / 1000).toFixed(0)}k`;

// ── Component ─────────────────────────────────────────────────────────────────

export default function Finance() {
  const [country, setCountry]   = useState('USA');
  const [field, setField]       = useState('Computer Science');
  const [tuition, setTuition]   = useState(45000);
  const [living, setLiving]     = useState(20000);
  const [loan, setLoan]         = useState(20000);
  const [yearsStudy, setYears]  = useState(2);
  const [budget, setBudget]     = useState(0);
  const [results, setResults]   = useState(null);
  const [showDetails, setShowDetails] = useState(false);

  const preset = COUNTRY_PRESETS[country] || COUNTRY_PRESETS.USA;
  const sym = preset.symbol;

  const applyPreset = (c) => {
    setCountry(c);
    const p = COUNTRY_PRESETS[c];
    if (p) { setTuition(p.tuition); setLiving(p.living); }
  };

  const calculate = (e) => {
    e.preventDefault();
    const totalTuition   = Number(tuition) * yearsStudy;
    const totalLiving    = Number(living) * yearsStudy;
    const totalCost      = totalTuition + totalLiving;
    const loanAmt        = Number(loan);
    const loanInterest   = loanAmt * 0.18 * yearsStudy; // ~18% p.a. Indian education loan
    const trueCost       = totalCost + loanInterest;

    const baseSalary     = preset.salary;
    const multiplier     = FIELD_SALARY_MULTIPLIERS[field] || 1.0;
    const grossSalary    = baseSalary * multiplier;
    const netSalary      = grossSalary * 0.75;             // ~25% tax
    const annualRepay    = netSalary * 0.30;               // 30% toward repayment
    const breakEven      = trueCost / annualRepay;
    const roi5yr         = ((netSalary * 5) - trueCost) / trueCost * 100;
    const roi10yr        = ((netSalary * 10) - trueCost) / trueCost * 100;

    const risk = computeRisk(breakEven, roi5yr, totalCost / yearsStudy, Number(budget));

    setResults({
      totalCost, totalTuition, totalLiving, loanInterest, trueCost,
      grossSalary, netSalary, annualRepay,
      breakEven: breakEven.toFixed(1),
      roi5yr:    roi5yr.toFixed(1),
      roi10yr:   roi10yr.toFixed(1),
      risk,
      yearlyBreakdown: Array.from({ length: Math.min(10, Math.ceil(breakEven) + 2) }, (_, yr) => ({
        year: yr + 1,
        cumEarnings: netSalary * (yr + 1),
        netPosition: netSalary * (yr + 1) - trueCost,
      })),
    });
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
          <p className="text-sm text-muted">Real salary benchmarks · Break-even timeline · Risk scoring · 10-year projection</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">

        {/* ── Input Panel ── */}
        <div className="lg:col-span-2 card p-6 space-y-5">
          <h2 className="font-bold text-text">Configure Your Scenario</h2>

          {/* Country preset */}
          <div>
            <label className="block text-xs font-semibold text-muted uppercase tracking-wide mb-2">Destination Country</label>
            <div className="grid grid-cols-4 gap-1.5">
              {Object.keys(COUNTRY_PRESETS).map(c => (
                <button key={c} onClick={() => applyPreset(c)}
                  className={`text-xs py-1.5 px-1 rounded-lg border font-medium transition-all
                    ${country === c ? 'bg-lavender text-white border-lavender' : 'border-surfaceBorder text-textSoft hover:border-lavender/50'}`}>
                  {c}
                </button>
              ))}
            </div>
          </div>

          {/* Field of study */}
          <div>
            <label className="block text-xs font-semibold text-muted uppercase tracking-wide mb-2">Field of Study</label>
            <select className="input-field" value={field} onChange={e => setField(e.target.value)}>
              {Object.keys(FIELD_SALARY_MULTIPLIERS).map(f => (
                <option key={f} value={f}>{f}</option>
              ))}
            </select>
            <p className="text-xs text-muted mt-1">
              Salary multiplier: <span className="font-semibold text-lavender">{FIELD_SALARY_MULTIPLIERS[field]}×</span> base for {country}
            </p>
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

            <button type="submit" className="btn-primary w-full">
              Calculate ROI <ArrowRight className="w-4 h-4" />
            </button>
          </form>

          {/* Benchmark note */}
          <div className="bg-surfaceAlt rounded-xl p-3 text-xs text-muted">
            <p className="font-semibold text-textSoft mb-1">📊 Salary benchmarks</p>
            <p>Base salary for {country}: <span className="font-bold text-text">{fmt(preset.salary, sym)}/yr</span></p>
            <p>With {field} premium: <span className="font-bold text-lavender">{fmt(preset.salary * (FIELD_SALARY_MULTIPLIERS[field]||1), sym)}/yr gross</span></p>
          </div>
        </div>

        {/* ── Results Panel ── */}
        <div className="lg:col-span-3 space-y-4">
          {results ? (
            <>
              {/* Risk badge */}
              <div className={`card p-4 flex items-center gap-3 ${results.risk.bg}`}>
                <results.risk.icon className={`w-5 h-5 ${results.risk.color} shrink-0`} />
                <div>
                  <p className={`font-bold ${results.risk.color}`}>{results.risk.label}</p>
                  <p className="text-xs text-muted">Based on break-even timeline, ROI, and budget fit</p>
                </div>
              </div>

              {/* Key metrics */}
              <div className="grid grid-cols-3 gap-3">
                <div className="card p-4 text-center">
                  <div className="page-icon bg-lavendLight text-lavender mx-auto mb-2"><Clock className="w-4 h-4" /></div>
                  <div className="text-2xl font-black text-text">{results.breakEven}<span className="text-xs font-normal text-muted ml-0.5">yrs</span></div>
                  <div className="text-xs text-muted mt-0.5">Break-Even</div>
                </div>
                <div className="card p-4 text-center">
                  <div className="page-icon bg-mintLight text-teal-600 mx-auto mb-2"><TrendingUp className="w-4 h-4" /></div>
                  <div className={`text-2xl font-black ${Number(results.roi5yr)>=0?'text-teal-600':'text-rose-500'}`}>
                    {Number(results.roi5yr)>=0?'+':''}{results.roi5yr}%
                  </div>
                  <div className="text-xs text-muted mt-0.5">5-yr ROI</div>
                </div>
                <div className="card p-4 text-center">
                  <div className="page-icon bg-peachLight text-peach mx-auto mb-2"><DollarSign className="w-4 h-4" /></div>
                  <div className={`text-2xl font-black ${Number(results.roi10yr)>=0?'text-text':'text-rose-500'}`}>
                    {Number(results.roi10yr)>=0?'+':''}{Math.round(results.roi10yr)}%
                  </div>
                  <div className="text-xs text-muted mt-0.5">10-yr ROI</div>
                </div>
              </div>

              {/* Cost breakdown doughnut */}
              <div className="card p-5 flex gap-6 items-center">
                <div className="w-40 h-40 shrink-0">
                  <Doughnut
                    data={{
                      labels: ['Tuition', 'Living Costs', 'Loan Interest'],
                      datasets: [{
                        data: [results.totalTuition, results.totalLiving, results.loanInterest],
                        backgroundColor: ['rgba(124,111,247,0.85)', 'rgba(78,204,163,0.85)', 'rgba(244,143,177,0.85)'],
                        borderColor: ['#7C6FF7','#4ECCA3','#F48FB1'],
                        borderWidth: 2,
                      }],
                    }}
                    options={{
                      plugins: { legend: { display: false } },
                      cutout: '65%',
                    }}
                  />
                </div>
                <div className="flex-1 space-y-2">
                  <h3 className="font-bold text-text text-sm">Total Investment</h3>
                  <p className="text-2xl font-black text-text">{fmt(results.trueCost, sym)}</p>
                  <p className="text-xs text-muted">including loan interest</p>
                  <div className="space-y-1 pt-1">
                    {[
                      { label: 'Tuition', val: results.totalTuition, color: 'bg-lavender' },
                      { label: 'Living',  val: results.totalLiving,  color: 'bg-teal-400' },
                      { label: 'Loan interest', val: results.loanInterest, color: 'bg-pink-400' },
                    ].map(({ label, val, color }) => (
                      <div key={label} className="flex items-center gap-2 text-xs">
                        <div className={`w-2 h-2 rounded-full ${color}`} />
                        <span className="text-muted flex-1">{label}</span>
                        <span className="font-semibold text-text">{fmt(val, sym)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* 10-year net position bar chart */}
              <div className="card p-5">
                <h3 className="font-bold text-text text-sm mb-3">Net Financial Position Over Time</h3>
                <Bar
                  data={{
                    labels: results.yearlyBreakdown.map(r => `Yr ${r.year}`),
                    datasets: [{
                      label: 'Net Position',
                      data: results.yearlyBreakdown.map(r => Math.round(r.netPosition)),
                      backgroundColor: results.yearlyBreakdown.map(r =>
                        r.netPosition >= 0 ? 'rgba(78,204,163,0.8)' : 'rgba(244,143,177,0.8)'
                      ),
                      borderRadius: 4,
                    }],
                  }}
                  options={{
                    plugins: { legend: { display: false } },
                    scales: {
                      y: {
                        ticks: {
                          callback: v => `${sym}${(v/1000).toFixed(0)}k`,
                          color: '#9AA0AD',
                          font: { size: 11 },
                        },
                        grid: { color: '#F0F1F5' },
                      },
                      x: {
                        ticks: { color: '#9AA0AD', font: { size: 11 } },
                        grid: { display: false },
                      },
                    },
                    maintainAspectRatio: false,
                  }}
                  style={{ height: '160px' }}
                />
              </div>

              {/* Detailed breakdown toggle */}
              <button onClick={() => setShowDetails(d => !d)}
                className="w-full flex items-center justify-between card p-4 text-sm font-semibold text-textSoft hover:bg-surfaceAlt transition-colors">
                <span>Salary &amp; repayment details</span>
                <ChevronDown className={`w-4 h-4 transition-transform ${showDetails ? 'rotate-180' : ''}`} />
              </button>
              {showDetails && (
                <div className="card p-5 text-sm space-y-2">
                  <Row label="Gross starting salary" val={fmt(results.grossSalary, sym) + '/yr'} />
                  <Row label="Net after ~25% tax" val={fmt(results.netSalary, sym) + '/yr'} />
                  <Row label="Annual loan repayment (30% of net)" val={fmt(results.annualRepay, sym) + '/yr'} />
                  <Row label="Total cost of education" val={fmt(results.totalCost, sym)} />
                  <Row label="Total with loan interest" val={fmt(results.trueCost, sym)} />
                  <div className="border-t border-surfaceBorder pt-2">
                    <Row label="10-year cumulative earnings (net)" val={fmt(results.netSalary * 10, sym)} highlight />
                    <Row label="10-year net position" val={fmt(results.netSalary * 10 - results.trueCost, sym)} highlight />
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="card p-16 flex flex-col items-center justify-center text-center">
              <div className="page-icon bg-lavendLight text-lavender mb-4 w-14 h-14">
                <Calculator className="w-6 h-6" />
              </div>
              <p className="font-bold text-text mb-1">Configure &amp; Calculate</p>
              <p className="text-sm text-muted max-w-xs">
                Select a country, your field, enter costs, and get a full ROI analysis with risk score and 10-year projection.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function Row({ label, val, highlight }) {
  return (
    <div className={`flex justify-between py-1 ${highlight ? 'font-bold text-text' : 'text-textSoft'}`}>
      <span>{label}</span>
      <span className={highlight ? 'text-lavender' : ''}>{val}</span>
    </div>
  );
}
