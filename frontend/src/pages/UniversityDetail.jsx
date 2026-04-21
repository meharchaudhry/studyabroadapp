import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { universitiesAPI } from '../api/universities';
import {
  ArrowLeft, MapPin, Star, BookOpen, ExternalLink, Award, GraduationCap,
  Calendar, CheckCircle2, TrendingUp, Briefcase, DollarSign, Info,
  ChevronDown, ChevronUp, Loader2
} from 'lucide-react';

const FLAG_MAP = {
  // Full names (canonical)
  'United States': '🇺🇸', 'United Kingdom': '🇬🇧', 'Canada': '🇨🇦',
  'Australia': '🇦🇺', 'Germany': '🇩🇪', 'France': '🇫🇷',
  'Netherlands': '🇳🇱', 'Ireland': '🇮🇪', 'Singapore': '🇸🇬',
  'Japan': '🇯🇵', 'Sweden': '🇸🇪', 'Norway': '🇳🇴', 'Denmark': '🇩🇰',
  'Finland': '🇫🇮', 'New Zealand': '🇳🇿', 'UAE': '🇦🇪', 'Portugal': '🇵🇹',
  'Italy': '🇮🇹', 'Spain': '🇪🇸', 'South Korea': '🇰🇷', 'Switzerland': '🇨🇭',
  'Belgium': '🇧🇪', 'Poland': '🇵🇱', 'Czech Republic': '🇨🇿',
  // Short aliases
  USA: '🇺🇸', UK: '🇬🇧',
};

function fmtUSD(n) {
  if (!n && n !== 0) return '—';
  return `$${Math.round(n).toLocaleString()}`;
}

function FactorBar({ label, value, hint, color = 'bg-lavender' }) {
  const pct = Math.round(value * 100);
  const barW = Math.max(4, pct);
  return (
    <div className="space-y-1">
      <div className="flex justify-between items-center text-xs">
        <span className="font-medium text-textSoft">{label}</span>
        <span className={`font-bold ${pct >= 70 ? 'text-teal-600' : pct >= 45 ? 'text-amber-500' : 'text-rose-500'}`}>{pct}%</span>
      </div>
      <div className="h-2 bg-surfaceBorder rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full transition-all duration-700`} style={{ width: `${barW}%` }} />
      </div>
      {hint && <p className="text-[11px] text-muted leading-snug">{hint}</p>}
    </div>
  );
}

export default function UniversityDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [uni, setUni]         = useState(null);
  const [explain, setExplain] = useState(null);
  const [loadingUni, setLoadingUni]         = useState(true);
  const [loadingExplain, setLoadingExplain] = useState(false);
  const [showExplain, setShowExplain]       = useState(false);
  const [explainError, setExplainError]     = useState('');

  useEffect(() => {
    universitiesAPI.getById(id)
      .then(d => setUni(d))
      .catch(() => setUni(null))
      .finally(() => setLoadingUni(false));
  }, [id]);

  const loadExplanation = async () => {
    if (explain) { setShowExplain(v => !v); return; }
    setLoadingExplain(true);
    setExplainError('');
    try {
      const data = await universitiesAPI.explain(id);
      setExplain(data);
      setShowExplain(true);
    } catch (err) {
      if (err.response?.status === 401) {
        setExplainError('Log in to see personalised match explanation.');
      } else {
        setExplainError('Unable to load explanation. Please try again.');
      }
    } finally {
      setLoadingExplain(false);
    }
  };

  if (loadingUni) {
    return (
      <div className="flex flex-col items-center justify-center p-20 gap-4">
        <Loader2 className="w-10 h-10 text-lavender animate-spin" />
        <p className="text-muted text-sm font-medium">Loading university profile…</p>
      </div>
    );
  }

  if (!uni) {
    return (
      <div className="card p-12 text-center">
        <h2 className="text-xl font-bold text-text mb-2">University Not Found</h2>
        <p className="text-muted mb-6">This institution does not exist in our database.</p>
        <button onClick={() => navigate('/universities')} className="btn-primary">Browse All Universities</button>
      </div>
    );
  }

  const flag = FLAG_MAP[uni.country] || '🏳️';
  const totalCost = (uni.tuition || 0) + (uni.living_cost || 0);

  return (
    <div className="animate-fade-in pb-10">
      <button onClick={() => navigate(-1)} className="btn-ghost text-muted mb-4 group -ml-4">
        <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" /> Back to Catalog
      </button>

      {/* Hero */}
      <div className="card overflow-hidden mb-6 border-none shadow-card">
        <div className="h-64 bg-lavendLight relative">
          {uni.image_url ? (
            <img src={uni.image_url} alt={uni.name} className="w-full h-full object-cover" />
          ) : (
            <div className="w-full h-full flex items-center justify-center bg-gradient-to-r from-lavender/20 to-skyLight">
              <GraduationCap className="w-20 h-20 text-lavender/40" />
            </div>
          )}
          <div className="absolute inset-0 bg-gradient-to-t from-text/80 via-text/20 to-transparent" />
          <div className="absolute bottom-0 left-0 right-0 p-8">
            <h1 className="text-3xl font-bold text-white mb-2">{uni.name}</h1>
            <div className="flex flex-wrap items-center gap-4 text-white/90 text-sm font-medium">
              <span className="flex items-center gap-1.5"><MapPin className="w-4 h-4" />{flag} {uni.country}</span>
              {(uni.qs_subject_ranking || uni.ranking) && (
                <span className="flex items-center gap-1.5">
                  <Star className="w-4 h-4 fill-amber-400 text-amber-400" />
                  QS #{uni.qs_subject_ranking || uni.ranking}
                </span>
              )}
              {uni.subject && (
                <div className="flex flex-wrap gap-1.5">
                  {uni.subject.split('|').slice(0, 4).map(s => (
                    <span key={s} className="bg-white/20 backdrop-blur-sm text-white text-[10px] px-2 py-0.5 rounded-full">
                      {s.trim()}
                    </span>
                  ))}
                </div>
              )}
              {uni.acceptance_rate && (
                <span className="text-xs bg-white/20 backdrop-blur-sm px-2 py-0.5 rounded-full">
                  {Math.round(uni.acceptance_rate * 100)}% acceptance rate
                </span>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Requirements + Explainability */}
        <div className="lg:col-span-2 space-y-5">

          {/* Why this university? — expandable */}
          <div className="card overflow-hidden">
            <button
              onClick={loadExplanation}
              className="w-full flex items-center justify-between p-5 hover:bg-surfaceAlt transition-colors"
            >
              <div className="flex items-center gap-3">
                <div className="page-icon bg-lavendLight text-lavender"><TrendingUp className="w-4 h-4" /></div>
                <div className="text-left">
                  <p className="font-bold text-text text-sm">Why this university?</p>
                  <p className="text-xs text-muted">Personalised match explanation for your profile</p>
                </div>
              </div>
              {loadingExplain
                ? <Loader2 className="w-4 h-4 text-lavender animate-spin" />
                : showExplain
                  ? <ChevronUp className="w-4 h-4 text-muted" />
                  : <ChevronDown className="w-4 h-4 text-muted" />
              }
            </button>

            {explainError && (
              <div className="px-5 pb-4 text-xs text-muted flex items-center gap-2">
                <Info className="w-4 h-4 shrink-0" />{explainError}
              </div>
            )}

            {showExplain && explain && (
              <div className="border-t border-surfaceBorder px-5 pb-5 pt-4 space-y-4">
                {/* Summary */}
                <div className={`rounded-xl p-3 text-sm font-medium ${
                  explain.match_score >= 0.75 ? 'bg-teal-50 text-teal-700' :
                  explain.match_score >= 0.50 ? 'bg-lavender/10 text-lavender' : 'bg-amber-50 text-amber-700'
                }`}>
                  {explain.summary}
                </div>

                {/* Factor bars */}
                <div className="space-y-3">
                  <p className="text-xs font-bold text-muted uppercase tracking-wide">Match Factors</p>
                  {[
                    { key: 'field',   label: 'Subject Match',     good: ['Strong match', 'directly aligned', 'overlap'], bad: ["don't closely"] },
                    { key: 'cgpa',    label: 'CGPA Eligibility',  good: ['exceeds', 'competitive'], bad: ['below', 'points below'] },
                    { key: 'budget',  label: 'Budget Fit',        good: ['within budget', 'to spare'], bad: ['significantly exceeds', '40%'] },
                    { key: 'ranking', label: 'QS Ranking',        good: ['World-class', 'Elite', 'Top-100', 'Well-ranked'], bad: [] },
                    { key: 'country', label: 'Country Preference',good: ['target destinations'], bad: ['outside'] },
                    { key: 'ielts',   label: 'IELTS Eligibility', good: ['meets', 'acceptable'], bad: ['below the required'] },
                  ].map(({ key, label, good, bad }) => {
                    const hint = explain.reasons[key] || '';
                    const isGood = good.some(w => hint.includes(w));
                    const isBad  = bad.some(w => hint.includes(w));
                    const value  = isGood ? 0.85 : isBad ? 0.30 : 0.55;
                    return (
                      <FactorBar key={key} label={label} value={value} hint={hint}
                        color={isGood ? 'bg-teal-500' : isBad ? 'bg-rose' : 'bg-amber-400'} />
                    );
                  })}
                </div>

                {/* Financial snapshot */}
                {explain.financial && (
                  <div className="bg-surfaceAlt rounded-xl p-4 space-y-2 text-xs">
                    <p className="font-bold text-text text-sm mb-2">Financial Snapshot</p>
                    {[
                      { label: 'Est. grad salary', val: fmtUSD(explain.financial.estimated_grad_salary_usd) + '/yr' },
                      { label: '5-yr ROI', val: explain.financial.roi_5yr_pct != null ? `+${explain.financial.roi_5yr_pct}%` : '—' },
                      { label: 'Break-even', val: explain.financial.break_even_years != null ? `${explain.financial.break_even_years} yrs` : '—' },
                      { label: 'Job market', val: `${explain.financial.job_market_score}/10` },
                    ].map(({ label, val }) => (
                      <div key={label} className="flex justify-between">
                        <span className="text-muted">{label}</span>
                        <span className="font-semibold text-text">{val}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Admission Requirements */}
          <div className="card p-6">
            <h2 className="text-base font-bold text-text mb-4 pb-2 border-b border-surfaceBorder">Admission Requirements</h2>
            <div className="grid sm:grid-cols-2 gap-3">
              <Req label="Min CGPA" val={uni.requirements_cgpa ? `${uni.requirements_cgpa}/10` : '7.0/10'} />
              <Req label="IELTS" val={uni.ielts ? `${uni.ielts}+` : '6.5+'} />
              <Req label="TOEFL" val={uni.toefl ? `${uni.toefl}+` : '90+'} />
              <Req label="GRE / GMAT" val={uni.gre_required ? 'Required' : 'Optional'} accent={uni.gre_required} />
              <Req label="Course Duration" val={`${uni.course_duration || 2} years`} />
              {uni.intake_months?.length > 0 && (
                <Req label="Intakes" val={uni.intake_months.join(', ')} />
              )}
            </div>
          </div>

          {/* Scholarships */}
          {uni.scholarships && (
            <div className="card p-6 bg-gradient-to-br from-amberLight to-orange-50/50 border-amber/20">
              <h2 className="text-base font-bold text-amber-900 mb-3 flex items-center gap-2">
                <Award className="w-5 h-5" /> Available Scholarships
              </h2>
              <p className="text-sm text-amber-800 leading-relaxed">{uni.scholarships}</p>
            </div>
          )}

          {/* About */}
          {uni.description && (
            <div className="card p-6">
              <h2 className="text-base font-bold text-text mb-3">About</h2>
              <p className="text-sm text-textSoft leading-relaxed">{uni.description}</p>
            </div>
          )}
        </div>

        {/* Right: Cost + Enriched Stats */}
        <div className="space-y-5">

          {/* Annual cost card */}
          <div className="card p-6">
            <h2 className="font-bold text-text mb-4">Cost Estimate (per year)</h2>
            <div className="space-y-3">
              <CostRow label="Tuition" val={fmtUSD(uni.tuition)} />
              <CostRow label="Living expenses" val={fmtUSD(uni.living_cost)} />
              <div className="border-t border-surfaceBorder pt-3 flex justify-between items-center">
                <span className="font-bold text-text text-sm">Total / yr</span>
                <span className="text-lg font-black text-teal-600 bg-mintLight px-3 py-1 rounded-lg">
                  {fmtUSD(totalCost)}
                </span>
              </div>
            </div>
          </div>

          {/* Country stats */}
          <div className="card p-5 space-y-3">
            <h2 className="font-bold text-text text-sm">Country Highlights</h2>
            {uni.grad_salary_usd && (
              <StatRow icon={DollarSign} label="Avg grad salary" val={`${fmtUSD(uni.grad_salary_usd)}/yr`} color="text-teal-600" />
            )}
            {uni.job_market_score && (
              <StatRow icon={Briefcase} label="Job market score" val={`${uni.job_market_score}/10`} color="text-lavender" />
            )}
          </div>

          {/* CTA */}
          <div className="space-y-3">
            {uni.website && (
              <a href={uni.website} target="_blank" rel="noreferrer" className="btn-primary w-full shadow-cardHov">
                Visit Official Website <ExternalLink className="w-4 h-4" />
              </a>
            )}
            <button onClick={loadExplanation} className="btn-secondary w-full">
              {explain ? 'View Match Details' : 'Why this for me?'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function Req({ label, val, accent }) {
  return (
    <div className="bg-surfaceAlt rounded-xl p-3">
      <p className="text-[10px] text-muted uppercase tracking-wide font-semibold mb-1">{label}</p>
      <p className={`text-sm font-bold ${accent ? 'text-peach' : 'text-text'}`}>{val}</p>
    </div>
  );
}

function CostRow({ label, val }) {
  return (
    <div className="flex justify-between items-center pb-3 border-b border-dashed border-surfaceBorder last:border-0 last:pb-0">
      <span className="text-sm text-muted">{label}</span>
      <span className="font-bold text-text">{val}</span>
    </div>
  );
}

function StatRow({ icon: Icon, label, val, color }) {
  return (
    <div className="flex items-center gap-3">
      <div className="page-icon bg-surfaceAlt w-8 h-8"><Icon className={`w-3.5 h-3.5 ${color}`} /></div>
      <div className="flex-1">
        <p className="text-xs text-muted">{label}</p>
        <p className={`text-sm font-bold ${color}`}>{val}</p>
      </div>
    </div>
  );
}
