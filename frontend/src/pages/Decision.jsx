import { useState } from 'react';
import {
  Sparkles, GraduationCap, FileCheck, TrendingUp, Briefcase,
  Star, ChevronDown, ChevronUp, Loader2, AlertCircle, Trophy,
  DollarSign, Clock, MapPin, ShieldCheck
} from 'lucide-react';
import { decisionAPI } from '../api/decision';

// ── Helpers ──────────────────────────────────────────────────────────────────

function ScoreBadge({ score }) {
  const pct = Math.round((score || 0) * 100);
  const color = pct >= 75 ? 'badge-mint' : pct >= 50 ? 'badge-lavender' : 'badge-amber';
  return <span className={`badge ${color}`}>{pct}% match</span>;
}

function JobScoreDots({ score }) {
  const full = Math.round(score);
  return (
    <div className="flex items-center gap-1">
      {[...Array(10)].map((_, i) => (
        <div
          key={i}
          className={`w-2 h-2 rounded-full ${i < full ? 'bg-teal-400' : 'bg-surfaceBorder'}`}
        />
      ))}
      <span className="text-xs text-muted ml-1">{score.toFixed(1)}/10</span>
    </div>
  );
}

// ── Confidence bar: label + filled track + % ──────────────────────────────────
function ConfidenceBar({ label, value, color = 'bg-lavender' }) {
  const pct = Math.round((value || 0) * 100);
  return (
    <div>
      <div className="flex items-center justify-between mb-0.5">
        <span className="text-[10px] text-muted">{label}</span>
        <span className="text-[10px] font-semibold text-textSoft">{pct}%</span>
      </div>
      <div className="h-1.5 bg-surfaceBorder rounded-full overflow-hidden">
        <div
          className={`h-full ${color} rounded-full transition-all duration-700`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

// ── Overall confidence ring (SVG arc) ─────────────────────────────────────────
function ConfidenceRing({ value }) {
  const pct  = Math.round((value || 0) * 100);
  const r    = 28;
  const circ = 2 * Math.PI * r;
  const fill = circ * (1 - pct / 100);
  const color = pct >= 80 ? '#14b8a6' : pct >= 60 ? '#7C6FF7' : '#f59e0b';
  return (
    <div className="relative w-16 h-16 flex items-center justify-center">
      <svg width="64" height="64" className="-rotate-90">
        <circle cx="32" cy="32" r={r} fill="none" stroke="#e5e7eb" strokeWidth="5" />
        <circle cx="32" cy="32" r={r} fill="none" stroke={color} strokeWidth="5"
          strokeDasharray={circ} strokeDashoffset={fill}
          strokeLinecap="round" style={{ transition: 'stroke-dashoffset 1s ease' }} />
      </svg>
      <span className="absolute text-xs font-black text-text">{pct}%</span>
    </div>
  );
}

function AgentStep({ icon: Icon, color, label, content, defaultOpen = false }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="card overflow-hidden">
      <button
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center justify-between p-4 hover:bg-surfaceAlt transition-colors"
      >
        <div className="flex items-center gap-3">
          <div className={`page-icon ${color}`}><Icon className="w-4 h-4" /></div>
          <span className="font-semibold text-sm text-text">{label}</span>
        </div>
        {open ? <ChevronUp className="w-4 h-4 text-muted" /> : <ChevronDown className="w-4 h-4 text-muted" />}
      </button>
      {open && (
        <div className="px-4 pb-4 text-sm text-textSoft whitespace-pre-wrap leading-relaxed border-t border-surfaceBorder pt-3">
          {content}
        </div>
      )}
    </div>
  );
}

function UniversityCard({ uni, rank }) {
  const rankColors = ['bg-amber-400', 'bg-slate-400', 'bg-orange-400'];
  const rankLabels = ['1st', '2nd', '3rd'];

  const hasConf = uni.confidence_overall != null;
  const overallConf = uni.confidence_overall || 0;
  const confColor = overallConf >= 0.80 ? 'text-teal-600' : overallConf >= 0.60 ? 'text-lavender' : 'text-amber-500';
  const confBg    = overallConf >= 0.80 ? 'bg-mintLight' : overallConf >= 0.60 ? 'bg-lavendLight' : 'bg-amberLight';

  return (
    <div className="card-hover card p-5 relative">
      {/* Rank badge */}
      <div className={`absolute -top-3 -left-3 w-8 h-8 ${rankColors[rank] || 'bg-surfaceBorder'} rounded-full flex items-center justify-center shadow-md`}>
        <span className="text-white text-xs font-bold">{rankLabels[rank] || rank + 1}</span>
      </div>

      <div className="flex items-start justify-between mb-3 pl-4">
        <div>
          <h3 className="font-bold text-text">{uni.name}</h3>
          <div className="flex items-center gap-1.5 mt-1">
            <MapPin className="w-3 h-3 text-muted" />
            <span className="text-xs text-muted">{uni.country}</span>
            {uni.ranking && (
              <span className="badge badge-lavender">QS #{uni.ranking}</span>
            )}
          </div>
        </div>
        <ScoreBadge score={uni.match_score} />
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-2 gap-3 mt-3">
        <div className="bg-surfaceAlt rounded-xl p-3">
          <div className="flex items-center gap-1.5 mb-1">
            <DollarSign className="w-3 h-3 text-peach" />
            <span className="text-xs text-muted">Total Cost</span>
          </div>
          <span className="text-sm font-bold text-text">
            ${(uni.total_cost_usd || 0).toLocaleString()}
          </span>
        </div>

        <div className="bg-surfaceAlt rounded-xl p-3">
          <div className="flex items-center gap-1.5 mb-1">
            <TrendingUp className="w-3 h-3 text-teal-500" />
            <span className="text-xs text-muted">5-yr ROI</span>
          </div>
          <span className={`text-sm font-bold ${(uni.roi_5yr_pct || 0) >= 0 ? 'text-teal-600' : 'text-rose'}`}>
            {uni.roi_5yr_pct >= 0 ? '+' : ''}{uni.roi_5yr_pct?.toFixed(1)}%
          </span>
        </div>

        <div className="bg-surfaceAlt rounded-xl p-3">
          <div className="flex items-center gap-1.5 mb-1">
            <Clock className="w-3 h-3 text-lavender" />
            <span className="text-xs text-muted">Break-even</span>
          </div>
          <span className="text-sm font-bold text-text">{uni.break_even_years?.toFixed(1)} yrs</span>
        </div>

        <div className="bg-surfaceAlt rounded-xl p-3">
          <div className="flex items-center gap-1.5 mb-1">
            <Briefcase className="w-3 h-3 text-amber-500" />
            <span className="text-xs text-muted">Jobs</span>
          </div>
          <JobScoreDots score={uni.job_availability_score || 0} />
        </div>
      </div>

      {/* Visa assessment */}
      {uni.visa_assessment && (
        <div className="mt-3 bg-lavendLight/40 rounded-xl p-3">
          <div className="flex items-center gap-1.5 mb-1">
            <FileCheck className="w-3 h-3 text-lavender" />
            <span className="text-xs font-semibold text-lavender">Visa Summary</span>
          </div>
          <p className="text-xs text-textSoft leading-relaxed">{uni.visa_assessment}</p>
        </div>
      )}

      {/* ── Confidence breakdown ── */}
      {hasConf && (
        <div className="mt-3 border-t border-surfaceBorder pt-3">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-1.5">
              <ShieldCheck className="w-3 h-3 text-muted" />
              <span className="text-[10px] font-semibold text-muted uppercase tracking-wide">AI Confidence</span>
            </div>
            <span className={`text-xs font-black ${confColor} ${confBg} px-2 py-0.5 rounded-full`}>
              {Math.round(overallConf * 100)}% overall
            </span>
          </div>
          <div className="space-y-1.5">
            <ConfidenceBar label="Profile fit"    value={uni.confidence_profile} color="bg-lavender"   />
            <ConfidenceBar label="Finance ROI"    value={uni.confidence_finance} color="bg-teal-400"   />
            <ConfidenceBar label="Job market"     value={uni.confidence_jobs}    color="bg-blue-400"   />
            <ConfidenceBar label="Visa ease"      value={uni.confidence_visa}    color="bg-amber-400"  />
          </div>
        </div>
      )}
    </div>
  );
}

// ── Cache helpers ─────────────────────────────────────────────────────────────

const CACHE_KEY = 'decision_result';
const CACHE_TTL = 30 * 60 * 1000; // 30 minutes

function loadCachedResult() {
  try {
    const raw = localStorage.getItem(CACHE_KEY);
    if (!raw) return null;
    const { data, ts } = JSON.parse(raw);
    if (Date.now() - ts > CACHE_TTL) { localStorage.removeItem(CACHE_KEY); return null; }
    return data;
  } catch { return null; }
}

function saveCachedResult(data) {
  try { localStorage.setItem(CACHE_KEY, JSON.stringify({ data, ts: Date.now() })); } catch {}
}

// ── Main Page ─────────────────────────────────────────────────────────────────

export default function Decision() {
  const [data, setData]       = useState(() => loadCachedResult());
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState(null);
  const [fromCache, setFromCache] = useState(() => !!loadCachedResult());

  const run = async (force = false) => {
    if (!force && data) return;
    setLoading(true);
    setError(null);
    setFromCache(false);
    try {
      const result = await decisionAPI.getDecision();
      setData(result);
      saveCachedResult(result);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to load recommendation.');
    } finally {
      setLoading(false);
    }
  };

  const pipelineConf = data?.confidence_score || 0;
  const confLabel = pipelineConf >= 0.80 ? 'High confidence' : pipelineConf >= 0.60 ? 'Moderate confidence' : 'Low confidence';
  const confLabelColor = pipelineConf >= 0.80 ? 'text-teal-600' : pipelineConf >= 0.60 ? 'text-lavender' : 'text-amber-500';

  return (
    <div className="space-y-6 animate-fade-in">

      {/* ── Header ── */}
      <div className="relative card overflow-hidden bg-gradient-to-br from-lavender to-[#5C4DDF] p-8 text-white border-none">
        <div className="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2" />
        <div className="relative z-10">
          <div className="flex items-center gap-3 mb-3">
            <div className="p-2 bg-white/20 rounded-xl backdrop-blur-sm">
              <Sparkles className="w-6 h-6 text-white" />
            </div>
            <h1 className="text-2xl font-bold">Decision Dashboard</h1>
          </div>
          <p className="text-white/80 text-sm max-w-xl leading-relaxed mb-5">
            Our 5-agent AI chain analyses your academic profile, visa difficulty, financial ROI,
            and job market — then ranks your top 3 university options with per-agent confidence scores.
          </p>
          <div className="flex items-center gap-3 flex-wrap">
            <button
              onClick={() => run(true)}
              disabled={loading}
              className="inline-flex items-center gap-2 px-5 py-2.5 bg-white text-lavender font-bold text-sm rounded-xl shadow-md hover:bg-lavendLight transition-all disabled:opacity-60"
            >
              {loading
                ? <><Loader2 className="w-4 h-4 animate-spin" /> Running 5-agent analysis…</>
                : data
                  ? <><Sparkles className="w-4 h-4" /> Re-run Analysis</>
                  : <><Trophy className="w-4 h-4" /> Generate My Recommendation</>
              }
            </button>
            {fromCache && !loading && (
              <span className="text-white/60 text-xs">Loaded from cache · <button onClick={() => run(true)} className="underline hover:text-white">refresh</button></span>
            )}
          </div>
        </div>
      </div>

      {/* ── Agent pipeline legend ── */}
      <div className="grid grid-cols-5 gap-2">
        {[
          { icon: GraduationCap, label: 'Profile Agent',   color: 'bg-lavendLight text-lavender', weight: '35%' },
          { icon: TrendingUp,    label: 'Finance Agent',   color: 'bg-mintLight text-teal-600',   weight: '30%' },
          { icon: Briefcase,     label: 'Jobs Agent',      color: 'bg-skyLight text-blue-600',    weight: '20%' },
          { icon: FileCheck,     label: 'Visa Agent',      color: 'bg-amberLight text-amber-600', weight: '15%' },
          { icon: Sparkles,      label: 'Synthesis Agent', color: 'bg-peachLight text-peach',     weight: null  },
        ].map(({ icon: Icon, label, color, weight }) => (
          <div key={label} className="card p-3 flex flex-col items-center text-center gap-1.5">
            <div className={`page-icon ${color}`}><Icon className="w-4 h-4" /></div>
            <span className="text-[11px] font-semibold text-textSoft">{label}</span>
            {weight && <span className="text-[10px] text-muted">{weight} weight</span>}
          </div>
        ))}
      </div>

      {/* ── Error ── */}
      {error && (
        <div className="card p-4 border-rose/30 bg-rose/5 flex items-center gap-3 text-rose text-sm">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          {error}
        </div>
      )}

      {/* ── Loading placeholder ── */}
      {loading && (
        <div className="card p-10 flex flex-col items-center justify-center text-center gap-4">
          <Loader2 className="w-10 h-10 text-lavender animate-spin" />
          <div>
            <p className="font-bold text-text">Running 5-agent pipeline…</p>
            <p className="text-sm text-muted mt-1">Profile → Finance → Jobs → Visa → Synthesis</p>
          </div>
        </div>
      )}

      {data && (
        <>
          {/* ── Pipeline confidence banner ── */}
          {data.confidence_score != null && (
            <div className="card p-5 flex items-center gap-5 border-lavender/20 bg-lavendLight/10">
              <ConfidenceRing value={data.confidence_score} />
              <div className="flex-1">
                <p className={`font-bold text-base ${confLabelColor}`}>{confLabel}</p>
                <p className="text-xs text-muted mt-0.5">
                  Weighted pipeline score across Profile (35%), Finance (30%), Jobs (20%) and Visa (15%) agents.
                  Higher confidence means stronger signal alignment across all data sources.
                </p>
              </div>
              <div className="hidden sm:flex flex-col items-end gap-0.5 text-right">
                <span className={`text-3xl font-black ${confLabelColor}`}>
                  {Math.round(data.confidence_score * 100)}%
                </span>
                <span className="text-xs text-muted">pipeline score</span>
              </div>
            </div>
          )}

          {/* ── Top 3 University Cards ── */}
          {data.top_universities?.length > 0 && (
            <div>
              <h2 className="font-bold text-text text-lg mb-4">Your Top 3 Recommendations</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-6">
                {data.top_universities.map((uni, i) => (
                  <UniversityCard key={uni.name} uni={uni} rank={i} />
                ))}
              </div>
            </div>
          )}

          {/* ── Synthesis ── */}
          {data.synthesis && (
            <div className="card p-6 border-lavender/20 bg-lavendLight/20">
              <div className="flex items-center gap-3 mb-4">
                <div className="page-icon bg-lavendLight text-lavender">
                  <Star className="w-4 h-4" />
                </div>
                <h2 className="font-bold text-text">AI Synthesis — Final Recommendation</h2>
              </div>
              <div className="text-sm text-textSoft leading-relaxed whitespace-pre-wrap">
                {data.synthesis}
              </div>
            </div>
          )}

          {/* ── Agent Steps (collapsible) ── */}
          {data.agent_steps && (
            <div>
              <h2 className="font-bold text-text text-lg mb-3">Agent Reasoning Steps</h2>
              <div className="space-y-2">
                <AgentStep
                  icon={GraduationCap}
                  color="bg-lavendLight text-lavender"
                  label="Agent 1 — Profile Analysis"
                  content={data.agent_steps.profile_analysis}
                  defaultOpen
                />
                <AgentStep
                  icon={TrendingUp}
                  color="bg-mintLight text-teal-600"
                  label="Agent 2 — Finance Analysis"
                  content={data.agent_steps.finance_analysis}
                />
                <AgentStep
                  icon={Briefcase}
                  color="bg-skyLight text-blue-600"
                  label="Agent 3 — Jobs Analysis"
                  content={data.agent_steps.jobs_analysis}
                />
                <AgentStep
                  icon={FileCheck}
                  color="bg-amberLight text-amber-600"
                  label="Agent 4 — Visa Assessment"
                  content={data.agent_steps.visa_assessment}
                />
                <AgentStep
                  icon={Sparkles}
                  color="bg-peachLight text-peach"
                  label="Agent 5 — Synthesis"
                  content={data.agent_steps.final_synthesis}
                />
              </div>
            </div>
          )}
        </>
      )}

      {/* ── Empty state ── */}
      {!loading && !data && !error && (
        <div className="card p-12 flex flex-col items-center justify-center text-center">
          <div className="page-icon bg-lavendLight text-lavender mb-4">
            <Trophy className="w-7 h-7" />
          </div>
          <h3 className="font-bold text-text mb-2">Ready when you are</h3>
          <p className="text-sm text-muted max-w-sm">
            Click "Generate My Recommendation" above to run the full 5-agent pipeline
            and receive your personalised ranked shortlist with per-agent confidence scores.
          </p>
        </div>
      )}
    </div>
  );
}
