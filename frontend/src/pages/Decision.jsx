import { useState, useEffect, useRef } from 'react';
import {
  GraduationCap, TrendingUp, Briefcase, FileCheck,
  MapPin, Loader2, AlertCircle, Trophy, RefreshCw,
  DollarSign, Clock, Star, ChevronDown, ChevronUp,
  CheckCircle, XCircle, Info, Sparkles, Bot, Cpu,
  BarChart3, Globe,
} from 'lucide-react';
import { decisionAPI } from '../api/decision';

// ── Agent chain definition ────────────────────────────────────────────────────
const AGENT_STEPS = [
  { id: 'profile', icon: GraduationCap, label: 'Profile Agent',   desc: 'Matching CGPA, field & degree requirements',  color: 'text-lavender',   bg: 'bg-lavendLight'  },
  { id: 'finance', icon: DollarSign,    label: 'Finance Agent',    desc: 'Calculating ROI, break-even & total costs',   color: 'text-teal-600',   bg: 'bg-mintLight'    },
  { id: 'jobs',    icon: Briefcase,     label: 'Jobs Agent',       desc: 'Scoring grad employment & post-study work',   color: 'text-blue-600',   bg: 'bg-blue-50'      },
  { id: 'visa',    icon: FileCheck,     label: 'Visa Agent',       desc: 'Assessing student visa ease for Indians',     color: 'text-amber-600',  bg: 'bg-amberLight'   },
  { id: 'synth',   icon: Sparkles,      label: 'Synthesis Agent',  desc: 'Gemini AI ranking & final recommendation',    color: 'text-purple-600', bg: 'bg-purple-50'    },
];

// Animated agent progress during loading
function AgentChainProgress({ step }) {
  return (
    <div className="card p-6 space-y-3">
      <div className="flex items-center gap-2 mb-4">
        <div className="w-8 h-8 bg-lavendLight rounded-xl flex items-center justify-center">
          <Bot className="w-4 h-4 text-lavender" />
        </div>
        <div>
          <p className="font-bold text-text text-sm">Multi-Agent Analysis Running</p>
          <p className="text-[11px] text-muted">5 specialised AI agents working in sequence</p>
        </div>
        <span className="ml-auto text-[10px] bg-purple-100 text-purple-700 px-2 py-1 rounded-full font-bold">
          LANGCHAIN
        </span>
      </div>

      <div className="space-y-2">
        {AGENT_STEPS.map((s, i) => {
          const done    = i < step;
          const active  = i === step;
          const pending = i > step;
          const Icon    = s.icon;
          return (
            <div key={s.id}
              className={`flex items-center gap-3 p-3 rounded-xl border transition-all duration-500 ${
                done    ? 'bg-teal-50 border-teal-200'      :
                active  ? `${s.bg} border-current/20 shadow-sm` :
                          'bg-surfaceAlt border-surfaceBorder opacity-40'
              }`}
            >
              <div className={`w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 ${
                done   ? 'bg-teal-500'     :
                active ? s.bg              :
                         'bg-surfaceBorder'
              }`}>
                {done ? (
                  <CheckCircle className="w-3.5 h-3.5 text-white" />
                ) : active ? (
                  <Loader2 className={`w-3.5 h-3.5 ${s.color} animate-spin`} />
                ) : (
                  <Icon className="w-3.5 h-3.5 text-muted" />
                )}
              </div>
              <div className="flex-1 min-w-0">
                <p className={`text-xs font-bold ${done ? 'text-teal-700' : active ? s.color : 'text-muted'}`}>
                  {s.label}
                </p>
                <p className={`text-[10px] ${done ? 'text-teal-600' : active ? 'text-textSoft' : 'text-muted'}`}>
                  {done ? 'Complete ✓' : active ? s.desc : s.desc}
                </p>
              </div>
              {active && (
                <div className="flex gap-0.5 flex-shrink-0">
                  {[0, 0.2, 0.4].map((d, j) => (
                    <div key={j} className={`w-1.5 h-1.5 rounded-full ${s.bg} border border-current/30 animate-bounce`}
                      style={{ animationDelay: `${d}s` }} />
                  ))}
                </div>
              )}
              {done && (
                <span className="text-[9px] text-teal-600 font-bold flex-shrink-0">✓ Done</span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function fmtUSD(val) {
  if (!val && val !== 0) return '—';
  if (val >= 1000) return `$${(val / 1000).toFixed(0)}k`;
  return `$${Math.round(val).toLocaleString()}`;
}

function ScoreRing({ value, size = 56 }) {
  const pct   = Math.round((value || 0) * 100);
  const r     = (size / 2) - 6;
  const circ  = 2 * Math.PI * r;
  const fill  = circ * (1 - pct / 100);
  const color = pct >= 75 ? '#22C55E' : pct >= 50 ? '#2563EB' : '#f59e0b';
  const cx    = size / 2;
  return (
    <div className="relative flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={cx} cy={cx} r={r} fill="none" stroke="#e5e7eb" strokeWidth="5" />
        <circle cx={cx} cy={cx} r={r} fill="none" stroke={color} strokeWidth="5"
          strokeDasharray={circ} strokeDashoffset={fill}
          strokeLinecap="round" style={{ transition: 'stroke-dashoffset 0.8s ease' }} />
      </svg>
      <span className="absolute text-[11px] font-black text-text">{pct}%</span>
    </div>
  );
}

function ScoreBar({ label, value, color = 'bg-lavender' }) {
  const pct = Math.round((value || 0) * 100);
  return (
    <div>
      <div className="flex justify-between mb-1">
        <span className="text-xs text-muted">{label}</span>
        <span className="text-xs font-bold text-textSoft">{pct}%</span>
      </div>
      <div className="h-1.5 bg-surfaceBorder rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full`} style={{ width: `${pct}%`, transition: 'width 0.7s ease' }} />
      </div>
    </div>
  );
}

function StatCell({ icon: Icon, iconColor, label, value, valueColor = 'text-text' }) {
  return (
    <div className="bg-surfaceAlt rounded-xl p-3">
      <div className="flex items-center gap-1.5 mb-1">
        <Icon className={`w-3 h-3 ${iconColor}`} />
        <span className="text-[10px] text-muted">{label}</span>
      </div>
      <span className={`text-sm font-bold ${valueColor}`}>{value}</span>
    </div>
  );
}

// ── University Card ───────────────────────────────────────────────────────────

function UniversityCard({ uni, rank }) {
  const [open, setOpen] = useState(false);

  const pct     = Math.round((uni.match_score || 0) * 100);
  const rankColors = ['from-amber-400 to-amber-500', 'from-slate-400 to-slate-500', 'from-orange-400 to-orange-500'];
  const rankBg    = rankColors[rank] || 'from-surfaceBorder to-surfaceBorder';
  const rankLabel = ['1st', '2nd', '3rd'][rank] || `${rank + 1}th`;

  const roi      = uni.roi_5yr_pct;
  const roiColor = roi >= 0 ? 'text-teal-600' : 'text-rose-500';
  const roiSign  = roi >= 0 ? '+' : '';

  return (
    <div className="card overflow-hidden">
      {/* Top gradient bar with rank */}
      <div className={`h-1.5 bg-gradient-to-r ${rankBg}`} />

      <div className="p-5">
        {/* Header row */}
        <div className="flex items-start gap-3 mb-4">
          <div className={`shrink-0 w-9 h-9 rounded-full bg-gradient-to-br ${rankBg} flex items-center justify-center shadow-sm`}>
            <span className="text-white text-xs font-black">{rankLabel}</span>
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="font-bold text-text text-sm leading-snug">{uni.name}</h3>
            <div className="flex items-center gap-2 mt-0.5 flex-wrap">
              <div className="flex items-center gap-1">
                <MapPin className="w-3 h-3 text-muted" />
                <span className="text-xs text-muted">{uni.country}</span>
              </div>
              {uni.ranking && (
                <span className="badge badge-lavender">QS #{uni.ranking}</span>
              )}
            </div>
          </div>
          <ScoreRing value={uni.match_score} size={52} />
        </div>

        {/* Key stats */}
        <div className="grid grid-cols-2 gap-2">
          <StatCell
            icon={DollarSign} iconColor="text-peach"
            label="Annual Cost" value={fmtUSD(uni.total_cost_usd)}
          />
          <StatCell
            icon={TrendingUp} iconColor="text-teal-500"
            label="5-yr ROI" value={roi != null ? `${roiSign}${roi?.toFixed(1)}%` : '—'}
            valueColor={roiColor}
          />
          <StatCell
            icon={Clock} iconColor="text-lavender"
            label="Break-even" value={uni.break_even_years != null ? `${uni.break_even_years?.toFixed(1)} yrs` : '—'}
          />
          <StatCell
            icon={Briefcase} iconColor="text-amber-500"
            label="Job Market" value={`${(uni.job_availability_score || 0).toFixed(1)}/10`}
          />
        </div>

        {/* Visa blurb */}
        {uni.visa_assessment && (
          <div className="mt-3 flex gap-2 bg-amberLight/40 rounded-xl p-3">
            <FileCheck className="w-3.5 h-3.5 text-amber-600 shrink-0 mt-0.5" />
            <p className="text-[11px] text-textSoft leading-relaxed">{uni.visa_assessment}</p>
          </div>
        )}

        {/* Score breakdown (collapsible) */}
        <button
          onClick={() => setOpen(o => !o)}
          className="w-full mt-3 flex items-center justify-between text-xs text-muted hover:text-lavender transition-colors"
        >
          <span className="font-semibold">Score breakdown</span>
          {open ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
        </button>

        {open && (
          <div className="mt-3 space-y-2 pt-3 border-t border-surfaceBorder">
            <ScoreBar label="Profile fit"  value={uni.confidence_profile} color="bg-lavender"  />
            <ScoreBar label="Finance ROI"  value={uni.confidence_finance} color="bg-teal-400"  />
            <ScoreBar label="Job market"   value={uni.confidence_jobs}    color="bg-blue-400"  />
            <ScoreBar label="Visa ease"    value={uni.confidence_visa}    color="bg-amber-400" />
          </div>
        )}
      </div>
    </div>
  );
}

// ── Comparison Table ──────────────────────────────────────────────────────────

function ComparisonTable({ universities }) {
  if (!universities?.length) return null;
  const headers = ['', ...universities.map(u => u.name)];

  const rows = [
    {
      label: 'Match Score',
      vals:  universities.map(u => `${Math.round((u.match_score || 0) * 100)}%`),
      color: universities.map(u => {
        const p = Math.round((u.match_score || 0) * 100);
        return p >= 75 ? 'text-teal-600 font-bold' : p >= 50 ? 'text-lavender font-bold' : 'text-amber-500 font-semibold';
      }),
    },
    {
      label: 'Annual Cost',
      vals:  universities.map(u => fmtUSD(u.total_cost_usd)),
      color: universities.map(() => 'text-text'),
    },
    {
      label: '5-yr ROI',
      vals:  universities.map(u => u.roi_5yr_pct != null ? `${u.roi_5yr_pct >= 0 ? '+' : ''}${u.roi_5yr_pct?.toFixed(1)}%` : '—'),
      color: universities.map(u => (u.roi_5yr_pct || 0) >= 0 ? 'text-teal-600' : 'text-rose-500'),
    },
    {
      label: 'Break-even',
      vals:  universities.map(u => u.break_even_years != null ? `${u.break_even_years?.toFixed(1)} yrs` : '—'),
      color: universities.map(() => 'text-text'),
    },
    {
      label: 'Job Market',
      vals:  universities.map(u => `${(u.job_availability_score || 0).toFixed(1)}/10`),
      color: universities.map(u => (u.job_availability_score || 0) >= 8 ? 'text-teal-600' : 'text-textSoft'),
    },
    {
      label: 'QS Ranking',
      vals:  universities.map(u => u.ranking ? `#${u.ranking}` : '—'),
      color: universities.map(() => 'text-text'),
    },
  ];

  return (
    <div className="card overflow-hidden">
      <div className="px-5 py-4 border-b border-surfaceBorder">
        <h2 className="font-bold text-text text-base">Side-by-Side Comparison</h2>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-surfaceBorder">
              <th className="text-left px-5 py-3 text-muted font-semibold text-xs w-32">Metric</th>
              {universities.map((u, i) => (
                <th key={u.name} className="text-left px-4 py-3 text-xs font-bold text-text">
                  <div className="flex items-center gap-1.5">
                    <span className={`w-5 h-5 rounded-full flex items-center justify-center text-white text-[10px] font-black
                      ${i === 0 ? 'bg-amber-400' : i === 1 ? 'bg-slate-400' : 'bg-orange-400'}`}>
                      {i + 1}
                    </span>
                    <span className="truncate max-w-28">{u.name.split(' ').slice(0, 3).join(' ')}</span>
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, ri) => (
              <tr key={row.label} className={ri % 2 === 0 ? 'bg-surfaceAlt/30' : ''}>
                <td className="px-5 py-2.5 text-xs text-muted font-medium">{row.label}</td>
                {row.vals.map((val, vi) => (
                  <td key={vi} className={`px-4 py-2.5 text-xs ${row.color[vi]}`}>{val}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ── Top Pick Card ─────────────────────────────────────────────────────────────

function TopPickCard({ uni }) {
  if (!uni) return null;
  const pct = Math.round((uni.match_score || 0) * 100);
  return (
    <div className="card p-5 border-teal-200 bg-gradient-to-br from-mintLight/60 to-white">
      <div className="flex items-center gap-2 mb-3">
        <div className="page-icon bg-mintLight text-teal-600"><Star className="w-4 h-4" /></div>
        <h2 className="font-bold text-text">Top Pick</h2>
      </div>
      <div className="flex items-start gap-4">
        <ScoreRing value={uni.match_score} size={64} />
        <div className="flex-1">
          <h3 className="font-black text-text text-lg leading-tight">{uni.name}</h3>
          <div className="flex items-center gap-1.5 mt-1">
            <MapPin className="w-3 h-3 text-muted" />
            <span className="text-sm text-muted">{uni.country}</span>
            {uni.ranking && <span className="badge badge-lavender">QS #{uni.ranking}</span>}
          </div>
          <div className="mt-3 flex flex-wrap gap-3">
            <div className="flex items-center gap-1.5">
              <CheckCircle className="w-3.5 h-3.5 text-teal-500" />
              <span className="text-xs text-textSoft">{pct}% profile match</span>
            </div>
            {uni.roi_5yr_pct != null && (
              <div className="flex items-center gap-1.5">
                <TrendingUp className={`w-3.5 h-3.5 ${(uni.roi_5yr_pct || 0) >= 0 ? 'text-teal-500' : 'text-rose-500'}`} />
                <span className="text-xs text-textSoft">
                  {(uni.roi_5yr_pct || 0) >= 0 ? '+' : ''}{uni.roi_5yr_pct?.toFixed(1)}% 5-yr ROI
                </span>
              </div>
            )}
            {uni.break_even_years != null && (
              <div className="flex items-center gap-1.5">
                <Clock className="w-3.5 h-3.5 text-lavender" />
                <span className="text-xs text-textSoft">Break-even in {uni.break_even_years?.toFixed(1)} yrs</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Cache helpers ─────────────────────────────────────────────────────────────

const CACHE_KEY = 'decision_result';
const CACHE_TTL = 30 * 60 * 1000;

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
  const [data, setData]           = useState(() => loadCachedResult());
  const [loading, setLoading]     = useState(false);
  const [error, setError]         = useState(null);
  const [fromCache, setFromCache] = useState(() => !!loadCachedResult());
  const [agentStep, setAgentStep] = useState(0);
  const stepTimerRef              = useRef(null);

  // Animate agent steps every ~2s during loading
  useEffect(() => {
    if (loading) {
      setAgentStep(0);
      stepTimerRef.current = setInterval(() => {
        setAgentStep(prev => Math.min(prev + 1, AGENT_STEPS.length - 1));
      }, 2200);
    } else {
      clearInterval(stepTimerRef.current);
    }
    return () => clearInterval(stepTimerRef.current);
  }, [loading]);

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

  const top1 = data?.top_universities?.[0];

  return (
    <div className="space-y-5 animate-fade-in">

      {/* ── Header ── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="page-header mb-0">
          <div className="page-icon bg-mintLight text-teal-600"><Trophy className="w-5 h-5" /></div>
          <div>
            <h1 className="text-2xl font-black text-text">My Shortlist</h1>
            <p className="text-muted text-sm">
              {data
                ? `${data.top_universities?.length || 0} universities ranked across 4 dimensions`
                : 'Data-driven university ranking for your profile'}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {fromCache && !loading && (
            <span className="text-xs text-muted">Cached result ·
              <button onClick={() => run(true)} className="text-lavender underline ml-1 hover:no-underline">refresh</button>
            </span>
          )}
          <button
            onClick={() => run(true)}
            disabled={loading}
            className="btn-primary flex items-center gap-2 disabled:opacity-60"
          >
            {loading
              ? <><Loader2 className="w-4 h-4 animate-spin" /> Analysing…</>
              : data
                ? <><RefreshCw className="w-4 h-4" /> Re-run</>
                : <><Trophy className="w-4 h-4" /> Generate Shortlist</>
            }
          </button>
        </div>
      </div>

      {/* ── How it works banner (shown before first run) ── */}
      {!data && !loading && !error && (
        <div className="card p-5 border-purple-100 bg-gradient-to-br from-purple-50/30 to-lavendLight/20">
          <div className="flex items-center gap-2 mb-4">
            <Cpu className="w-4 h-4 text-purple-600" />
            <p className="text-sm font-bold text-text">5-Agent LangChain Analysis</p>
            <span className="text-[9px] bg-purple-100 text-purple-700 px-2 py-0.5 rounded-full font-bold ml-auto">MULTI-AGENT</span>
          </div>
          <div className="space-y-2">
            {AGENT_STEPS.map((s, i) => {
              const Icon = s.icon;
              return (
                <div key={s.id} className="flex items-center gap-3 p-3 bg-white rounded-xl border border-surfaceBorder">
                  <div className={`w-7 h-7 ${s.bg} rounded-full flex items-center justify-center flex-shrink-0`}>
                    <Icon className={`w-3.5 h-3.5 ${s.color}`} />
                  </div>
                  <div className="flex-1">
                    <p className="text-xs font-bold text-text">{s.label}</p>
                    <p className="text-[10px] text-muted">{s.desc}</p>
                  </div>
                  <span className="text-[9px] text-muted font-medium">Step {i + 1}</span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* ── Error ── */}
      {error && (
        <div className="card p-4 border-rose/30 bg-rose/5 flex items-center gap-3 text-rose text-sm">
          <AlertCircle className="w-5 h-5 shrink-0" />
          {error}
        </div>
      )}

      {/* ── Loading — animated agent chain ── */}
      {loading && <AgentChainProgress step={agentStep} />}

      {data && (
        <>
          {/* Top pick highlight */}
          {top1 && <TopPickCard uni={top1} />}

          {/* University cards */}
          {data.top_universities?.length > 0 && (
            <div>
              <h2 className="font-bold text-text text-base mb-3">Your Ranked Shortlist</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {data.top_universities.map((uni, i) => (
                  <UniversityCard key={uni.name} uni={uni} rank={i} />
                ))}
              </div>
            </div>
          )}

          {/* Comparison table */}
          <ComparisonTable universities={data.top_universities} />

          {/* AI Synthesis — Gemini counsellor notes */}
          {data.synthesis && (
            <div className="card p-5 border-purple-100 bg-gradient-to-br from-purple-50/40 to-white">
              <div className="flex items-center gap-2 mb-4">
                <div className="w-7 h-7 bg-purple-100 rounded-xl flex items-center justify-center">
                  <Sparkles className="w-3.5 h-3.5 text-purple-600" />
                </div>
                <div>
                  <h2 className="font-bold text-text text-sm">AI Synthesis — Gemini Counsellor</h2>
                  <p className="text-[10px] text-muted">Generated by 5-agent LangChain chain · Powered by Gemini 2.5 Flash</p>
                </div>
                <span className="ml-auto text-[9px] bg-purple-100 text-purple-700 px-2 py-0.5 rounded-full font-bold">GEMINI AI</span>
              </div>
              <div className="space-y-2">
                {data.synthesis
                  .split('\n')
                  .filter(line => line.trim())
                  .slice(0, 7)
                  .map((line, i) => {
                    const clean = line.replace(/^\*+\s*/, '').replace(/\*\*/g, '').trim();
                    if (!clean) return null;
                    return (
                      <div key={i} className="flex gap-3 p-3 bg-white rounded-xl border border-purple-100">
                        <div className="w-5 h-5 bg-purple-50 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                          <span className="text-purple-600 text-[10px] font-bold">{i + 1}</span>
                        </div>
                        <p className="text-xs text-textSoft leading-relaxed">{clean}</p>
                      </div>
                    );
                  })}
              </div>
            </div>
          )}
        </>
      )}

      {/* ── Empty state ── */}
      {!loading && !data && !error && (
        <div className="card p-12 flex flex-col items-center justify-center text-center">
          <div className="page-icon bg-lavendLight text-lavender mb-4 w-14 h-14">
            <Trophy className="w-7 h-7" />
          </div>
          <h3 className="font-bold text-text mb-2">Ready when you are</h3>
          <p className="text-sm text-muted max-w-sm leading-relaxed">
            Click <strong>"Generate Shortlist"</strong> to get your personalised ranked university list
            with financial ROI, job market data, and visa assessment — all in one place.
          </p>
          <button
            onClick={() => run(true)}
            className="btn-primary mt-5 flex items-center gap-2"
          >
            <Trophy className="w-4 h-4" /> Generate My Shortlist
          </button>
        </div>
      )}
    </div>
  );
}
