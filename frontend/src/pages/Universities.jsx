import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { universitiesAPI } from '../api/universities';
import { getCountryFlag } from '../utils/universityImages';
import { GraduationCap, Search, Sparkles, Loader2, SlidersHorizontal, X, TrendingUp, Briefcase, Trophy, RefreshCw } from 'lucide-react';

const SHORTLIST_KEY = 'decision_result';
const SHORTLIST_TTL = 60 * 60 * 1000; // 1 hour

function loadShortlist() {
  try {
    const raw = localStorage.getItem(SHORTLIST_KEY);
    if (!raw) return null;
    const { data, ts } = JSON.parse(raw);
    if (Date.now() - ts > SHORTLIST_TTL) return null;
    return data?.top_universities?.length ? data.top_universities : null;
  } catch { return null; }
}

const COUNTRIES = [
  "United Kingdom","United States","Canada","Australia","Germany","France",
  "Netherlands","Ireland","Singapore","Japan","Sweden","Norway","Denmark",
  "Finland","UAE","New Zealand","Portugal","Italy","Spain","South Korea","Switzerland",
];
const SUBJECTS = [
  "Computer Science","Engineering","Business","Medicine","Law","Arts",
  "Economics","Data Science","Finance","Architecture","Psychology","Physics",
  "Environmental","Public Health","Education","Social Science",
];
// All tuition/living_cost values in DB are stored in INR — display directly
function fmtINR(inr) {
  if (!inr && inr !== 0) return '—';
  if (inr >= 10000000) return `₹${(inr / 10000000).toFixed(1)} Cr`;
  if (inr >= 100000)   return `₹${(inr / 100000).toFixed(1)} L`;
  return `₹${Math.round(inr / 1000)}k`;
}

const BUDGET_OPTIONS = [
  { label: 'Under ₹20 L/yr',  value: 2000000 },
  { label: 'Under ₹35 L/yr',  value: 3500000 },
  { label: 'Under ₹50 L/yr',  value: 5000000 },
  { label: 'Any',              value: '' },
];

export default function Universities() {
  const [mode, setMode]             = useState('browse');
  const [universities, setUniversities] = useState([]);
  const [loading, setLoading]       = useState(false);
  const [error, setError]           = useState('');
  const [search, setSearch]         = useState('');
  const [country, setCountry]       = useState('');
  const [subject, setSubject]       = useState('');
  const [maxTuition, setMaxTuition] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [page, setPage]             = useState(0);
  const [total, setTotal]           = useState(0);
  const [fromShortlist, setFromShortlist] = useState(false);
  // Match scores keyed by university id — fetched once for browse mode overlay
  const [matchScores, setMatchScores] = useState({});
  const PER_PAGE = 18;

  const activeFilters = [country, subject, maxTuition].filter(Boolean).length;

  // Fetch top-100 recommendations once to overlay match % + reason on browse cards
  useEffect(() => {
    universitiesAPI.getRecommendations(100)
      .then(res => {
        const map = {};
        (res.recommendations || []).forEach(r => {
          if (r.id) map[r.id] = { score: r.match_score, reason: r.top_reason, label: r.match_label };
        });
        setMatchScores(map);
      })
      .catch(() => {});
  }, []);

  const load = useCallback(async () => {
    setLoading(true); setError('');
    try {
      if (mode === 'browse') {
        setFromShortlist(false);
        const params = { limit: PER_PAGE, offset: page * PER_PAGE };
        if (country) params.country = country;
        if (subject) params.subject = subject;
        if (maxTuition) params.max_tuition = maxTuition;
        if (search) params.search = search;
        const res = await universitiesAPI.list(params);
        setUniversities(res.universities || []);
        setTotal(res.total || 0);
      } else {
        // AI Matches: prefer the Decision page shortlist cache
        const cached = loadShortlist();
        if (cached) {
          setUniversities(cached);
          setTotal(cached.length);
          setFromShortlist(true);
          setLoading(false);
          return;
        }
        // No shortlist yet — fall back to simple scoring
        setFromShortlist(false);
        const res = await universitiesAPI.getRecommendations(15);
        setUniversities(res.recommendations || []);
        setTotal(res.recommendations?.length || 0);
      }
    } catch (err) {
      setError(err.response?.status === 401 ? 'Log in to see your AI matches.' : 'Failed to load universities.');
    } finally { setLoading(false); }
  }, [mode, country, subject, maxTuition, search, page]);

  useEffect(() => { load(); }, [load]);

  const clearFilters = () => { setCountry(''); setSubject(''); setMaxTuition(''); setPage(0); };

  return (
    <div className="space-y-5 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="page-header mb-0">
          <div className="page-icon bg-lavendLight text-lavender"><GraduationCap className="w-5 h-5" /></div>
          <div>
            <h1 className="text-2xl font-black text-text">Universities</h1>
            <p className="text-muted text-sm">
              {loading ? 'Loading…' : `${total.toLocaleString()} institutions across 21 countries`}
            </p>
          </div>
        </div>
        <div className="flex bg-surfaceAlt rounded-xl p-1 border border-surfaceBorder self-start">
          {[
            { id: 'browse',  label: 'Browse All' },
            { id: 'matches', label: 'AI Matches', icon: Sparkles },
          ].map(({ id, label, icon: Icon }) => (
            <button key={id} onClick={() => { setMode(id); setPage(0); }}
              className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-semibold transition-all
                ${mode === id ? 'bg-white text-lavender shadow-soft' : 'text-muted hover:text-textSoft'}`}>
              {Icon && <Icon className="w-3.5 h-3.5" />}{label}
            </button>
          ))}
        </div>
      </div>

      {/* Filters bar (browse mode) */}
      {mode === 'browse' && (
        <div className="space-y-3">
          <div className="flex gap-3 flex-wrap">
            <div className="relative flex-1 min-w-48">
              <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-muted pointer-events-none" />
              <input
                className="input-field !pl-10"
                placeholder="Search by name…"
                value={search}
                onChange={e => { setSearch(e.target.value); setPage(0); }}
              />
            </div>
            <select className="input-field w-44" value={country} onChange={e => { setCountry(e.target.value); setPage(0); }}>
              <option value="">All Countries</option>
              {COUNTRIES.map(c => <option key={c} value={c}>{getCountryFlag(c)} {c}</option>)}
            </select>
            <select className="input-field w-48" value={subject} onChange={e => { setSubject(e.target.value); setPage(0); }}>
              <option value="">All Subjects</option>
              {SUBJECTS.map(s => <option key={s} value={s}>{s}</option>)}
            </select>
            <button
              onClick={() => setShowFilters(v => !v)}
              className={`btn-secondary flex items-center gap-2 relative ${showFilters ? 'border-lavender text-lavender' : ''}`}
            >
              <SlidersHorizontal className="w-4 h-4" />
              Filters
              {activeFilters > 0 && (
                <span className="absolute -top-1.5 -right-1.5 bg-lavender text-white text-[10px] w-4 h-4 rounded-full flex items-center justify-center font-bold">
                  {activeFilters}
                </span>
              )}
            </button>
          </div>

          {/* Expanded filters */}
          {showFilters && (
            <div className="card p-4 space-y-3">
              <div className="flex items-center justify-between">
                <p className="text-sm font-bold text-text">Advanced Filters</p>
                {activeFilters > 0 && (
                  <button onClick={clearFilters} className="text-xs text-muted hover:text-rose-500 flex items-center gap-1">
                    <X className="w-3 h-3" /> Clear all
                  </button>
                )}
              </div>
              <div>
                <p className="text-xs text-muted font-semibold mb-2">Annual Budget</p>
                <div className="flex gap-2 flex-wrap">
                  {BUDGET_OPTIONS.map(({ label, value }) => (
                    <button key={label}
                      onClick={() => { setMaxTuition(value); setPage(0); }}
                      className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all
                        ${maxTuition === value
                          ? 'bg-lavender text-white border-lavender'
                          : 'border-surfaceBorder text-textSoft hover:border-lavender/50'}`}>
                      {label}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* AI matches banner */}
      {mode === 'matches' && !loading && !error && (
        <>
          {fromShortlist && universities.length > 0 ? (
            <div className="bg-mintLight border border-green-200 rounded-xl p-4 flex items-start justify-between gap-4">
              <div className="flex items-start gap-3">
                <Trophy className="w-5 h-5 text-teal-600 shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm text-teal-700 font-bold mb-0.5">
                    Showing your AI shortlist — {universities.length} universities ranked across 4 dimensions
                  </p>
                  <p className="text-xs text-teal-600/80">
                    Academic fit · Financial ROI · Job market · Visa confidence — run on your full profile
                  </p>
                </div>
              </div>
              <Link to="/decision"
                className="shrink-0 flex items-center gap-1.5 text-xs font-semibold text-teal-700 bg-white border border-green-200 px-3 py-1.5 rounded-lg hover:bg-green-50 transition-colors">
                <RefreshCw className="w-3.5 h-3.5" /> Re-run
              </Link>
            </div>
          ) : !fromShortlist && universities.length > 0 ? (
            <div className="bg-amberLight border border-amber-200 rounded-xl p-4 flex items-start justify-between gap-4">
              <div className="flex items-start gap-3">
                <Sparkles className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm text-amber-700 font-bold mb-0.5">
                    Showing profile-based matches — no shortlist generated yet
                  </p>
                  <p className="text-xs text-amber-600/80">
                    Run the full AI analysis on the Shortlist page to get ROI, job scores and visa confidence
                  </p>
                </div>
              </div>
              <Link to="/decision"
                className="shrink-0 flex items-center gap-1.5 text-xs font-semibold text-amber-700 bg-white border border-amber-200 px-3 py-1.5 rounded-lg hover:bg-amber-50 transition-colors">
                <Trophy className="w-3.5 h-3.5" /> Build Shortlist
              </Link>
            </div>
          ) : null}
        </>
      )}

      {/* Results */}
      {loading ? (
        <div className="flex flex-col items-center py-24 gap-3">
          <Loader2 className="w-8 h-8 text-lavender animate-spin" />
          <p className="text-muted text-sm">
            {mode === 'matches' ? 'Running AI matching algorithm…' : 'Loading universities…'}
          </p>
        </div>
      ) : error ? (
        <div className="card p-8 text-center">
          <p className="font-semibold text-text mb-1">{error}</p>
          {error.includes('Log in') && (
            <a href="/login" className="btn-primary mt-3 inline-flex">Log In</a>
          )}
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {universities.map((uni, i) => (
              mode === 'matches' && fromShortlist
                ? <ShortlistCard key={uni.name || i} uni={uni} rank={i + 1} />
                : <UniCard
                    key={uni.id || i}
                    uni={uni}
                    rank={mode === 'matches' ? i + 1 : null}
                    browseMatchScore={mode === 'browse' ? (matchScores[uni.id]?.score ?? null) : null}
                    browseMatchReason={mode === 'browse' ? (matchScores[uni.id]?.reason ?? null) : null}
                  />
            ))}
          </div>
          {mode === 'browse' && total > PER_PAGE && (
            <div className="flex justify-center gap-2 pt-2">
              <button onClick={() => setPage(p => Math.max(0, p - 1))} disabled={page === 0}
                className="btn-secondary px-4 py-2 text-sm disabled:opacity-40">Previous</button>
              <span className="flex items-center px-4 text-sm text-muted">
                Page {page + 1} of {Math.ceil(total / PER_PAGE)}
              </span>
              <button onClick={() => setPage(p => p + 1)} disabled={(page + 1) * PER_PAGE >= total}
                className="btn-secondary px-4 py-2 text-sm disabled:opacity-40">Next</button>
            </div>
          )}
          {universities.length === 0 && (
            <div className="card p-12 text-center">
              <GraduationCap className="w-10 h-10 text-muted mx-auto mb-3 opacity-30" />
              <p className="font-semibold text-text">No universities found</p>
              <p className="text-sm text-muted mt-1">Try adjusting your filters or clearing them</p>
              {activeFilters > 0 && (
                <button onClick={clearFilters} className="btn-secondary mt-3 text-sm">Clear Filters</button>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}

function fmtUSD(v) {
  if (!v && v !== 0) return '—';
  return `$${Math.round(v / 1000)}k`;
}

function ShortlistCard({ uni, rank }) {
  const flag = getCountryFlag(uni.country);
  const pct  = Math.round((uni.match_score || 0) * 100);
  const rankColors = ['bg-amber-400', 'bg-slate-400', 'bg-orange-400'];
  const rankLabels = ['1st', '2nd', '3rd'];
  const scoreColor = pct >= 75 ? 'bg-teal-500' : pct >= 50 ? 'bg-lavender' : pct >= 30 ? 'bg-amber-400' : 'bg-slate-400';
  const roi = uni.roi_5yr_pct;
  const roiColor = roi >= 0 ? 'text-teal-600' : 'text-rose-500';

  return (
    <Link to="/decision" className="group block">
      <div className="card-hover card overflow-hidden flex flex-col">
        <div className="relative h-40 overflow-hidden"
          style={{ background: 'linear-gradient(135deg, #1E40AF 0%, #2563EB 60%, #3B82F6 100%)' }}>
          {/* Rank badge */}
          <div className="absolute top-3 left-3 flex gap-1.5">
            {uni.ranking && (
              <span className="badge bg-white/90 backdrop-blur-sm text-lavender border border-lavender/20 shadow-sm">
                QS #{uni.ranking}
              </span>
            )}
            {rank <= 3 && (
              <span className={`badge ${rankColors[rank - 1]} text-white shadow-sm`}>
                {rankLabels[rank - 1]}
              </span>
            )}
          </div>
          {/* Match score */}
          <div className="absolute top-3 right-3">
            <div className={`w-11 h-11 rounded-full flex flex-col items-center justify-center border-2 border-white shadow-md ${scoreColor} text-white`}>
              <span className="text-[10px] font-black leading-none">{pct}%</span>
              <span className="text-[7px] opacity-80">match</span>
            </div>
          </div>
          {/* Country overlay */}
          <div className="absolute bottom-0 inset-x-0 bg-gradient-to-t from-black/70 to-transparent p-3 pt-8">
            <span className="text-sm">{flag}</span>
            <span className="text-white/90 text-xs font-semibold ml-1">{uni.country}</span>
          </div>
        </div>

        <div className="p-4 flex flex-col flex-1">
          <h3 className="font-bold text-text text-sm leading-snug mb-3 group-hover:text-lavender transition-colors line-clamp-2">
            {uni.name}
          </h3>
          <div className="grid grid-cols-2 gap-2 mt-auto">
            {uni.total_cost_usd != null && (
              <Chip label="Annual cost" val={fmtUSD(uni.total_cost_usd)} />
            )}
            {roi != null && (
              <Chip label="5yr ROI" val={`${roi >= 0 ? '+' : ''}${roi?.toFixed(1)}%`} accent roiColor={roiColor} />
            )}
            {uni.break_even_years != null && (
              <Chip label="Break-even" val={`${uni.break_even_years?.toFixed(1)} yrs`} />
            )}
            {uni.job_availability_score != null && (
              <Chip label="Jobs score" val={`${uni.job_availability_score.toFixed(1)}/10`} accent />
            )}
          </div>
        </div>
      </div>
    </Link>
  );
}

// Matches from recommendations endpoint carry top_reason + match_label
// Browse mode overlays match_score from the recommendations map
function UniCard({ uni, rank, browseMatchScore, browseMatchReason }) {
  const flag     = getCountryFlag(uni.country);
  const rawScore = uni.match_score ?? browseMatchScore ?? null;
  const pct      = rawScore !== null ? Math.round(rawScore * 100) : null;
  const reason   = uni.top_reason || browseMatchReason || null;
  const label    = uni.match_label || null;

  const scoreColor = pct >= 75 ? 'bg-teal-500'
                   : pct >= 50 ? 'bg-lavender'
                   : pct >= 30 ? 'bg-amber-400'
                   : 'bg-slate-400';

  const labelColor = pct >= 75 ? 'text-teal-700 bg-teal-50 border-teal-200'
                   : pct >= 50 ? 'text-lavender bg-lavendLight border-lavender/20'
                   : pct >= 30 ? 'text-amber-700 bg-amber-50 border-amber-200'
                   : 'text-slate-600 bg-surfaceAlt border-surfaceBorder';

  return (
    <Link to={`/universities/${uni.id}`} className="group block">
      <div className="card-hover card overflow-hidden flex flex-col h-full">

        {/* Banner */}
        <div className="relative h-36 flex-shrink-0 overflow-hidden"
          style={{ background: 'linear-gradient(135deg, #1E40AF 0%, #2563EB 60%, #3B82F6 100%)' }}>

          {/* QS rank badge */}
          {uni.ranking && (
            <div className="absolute top-3 left-3">
              <span className="badge bg-white/90 backdrop-blur-sm text-lavender border border-lavender/20 shadow-sm">
                QS #{uni.ranking}
              </span>
            </div>
          )}

          {/* Match score */}
          {pct !== null && (
            <div className="absolute top-3 right-3">
              <div className={`w-12 h-12 rounded-full flex flex-col items-center justify-center border-2 border-white shadow-lg ${scoreColor} text-white`}>
                <span className="text-[11px] font-black leading-none">{pct}%</span>
                <span className="text-[7px] opacity-80 mt-0.5">match</span>
              </div>
            </div>
          )}

          {/* Country + subject chips */}
          <div className="absolute bottom-0 inset-x-0 bg-gradient-to-t from-black/75 to-transparent p-3 pt-10">
            <div className="flex items-center gap-1.5">
              <span className="text-base leading-none">{flag}</span>
              <span className="text-white/90 text-xs font-semibold">{uni.country}</span>
              {uni.subject && (
                <span className="ml-auto text-white/80 text-[9px] bg-white/20 px-1.5 py-0.5 rounded-full backdrop-blur-sm">
                  {uni.subject.split('|')[0].trim()}
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Body */}
        <div className="p-4 flex flex-col flex-1">
          <h3 className="font-bold text-text text-sm leading-snug group-hover:text-lavender transition-colors line-clamp-2 mb-2">
            {uni.name}
          </h3>

          {/* Match label + reason — the key new addition */}
          {pct !== null && (
            <div className="mb-3 space-y-1.5">
              {label && (
                <span className={`inline-block text-[10px] font-bold px-2 py-0.5 rounded-full border ${labelColor}`}>
                  {label}
                </span>
              )}
              {reason && (
                <p className="text-[11px] text-textSoft leading-relaxed line-clamp-2">{reason}</p>
              )}
            </div>
          )}

          {/* Stats row */}
          <div className="grid grid-cols-2 gap-1.5 mt-auto">
            {uni.tuition  && <MiniChip label="Tuition/yr" val={fmtINR(uni.tuition)} />}
            {uni.ielts    && <MiniChip label="IELTS min"  val={`${uni.ielts}+`} />}
            {uni.requirements_cgpa && <MiniChip label="Min CGPA" val={uni.requirements_cgpa} />}
            {uni.job_market_score  && <MiniChip label="Jobs" val={`${uni.job_market_score}/10`} green />}
          </div>
        </div>
      </div>
    </Link>
  );
}

const MiniChip = ({ label, val, green }) => (
  <div className={`rounded-lg px-2.5 py-1.5 ${green ? 'bg-mintLight' : 'bg-surfaceAlt'}`}>
    <p className="text-[9px] text-muted uppercase tracking-wide">{label}</p>
    <p className={`text-xs font-bold ${green ? 'text-teal-700' : 'text-text'}`}>{val}</p>
  </div>
);

// Keep legacy Chip for ShortlistCard
const Chip = ({ label, val, accent, roiColor }) => (
  <div className={`rounded-lg p-2 ${accent ? 'bg-lavendLight' : 'bg-surfaceAlt'}`}>
    <p className="text-[10px] text-muted">{label}</p>
    <p className={`text-xs font-bold ${roiColor || (accent ? 'text-lavender' : 'text-text')}`}>{val}</p>
  </div>
);
