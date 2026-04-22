import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { universitiesAPI } from '../api/universities';
import { getUniversityImage, getCountryFlag } from '../utils/universityImages';
import { GraduationCap, Search, Sparkles, Loader2, SlidersHorizontal, X, TrendingUp, Briefcase } from 'lucide-react';

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
  // Match scores keyed by university id — fetched once for browse mode overlay
  const [matchScores, setMatchScores] = useState({});
  const PER_PAGE = 18;

  const activeFilters = [country, subject, maxTuition].filter(Boolean).length;

  // Fetch top-100 recommendations once to overlay match % on browse cards
  useEffect(() => {
    universitiesAPI.getRecommendations(100)
      .then(res => {
        const map = {};
        (res.recommendations || []).forEach(r => { if (r.id) map[r.id] = r.match_score; });
        setMatchScores(map);
      })
      .catch(() => {}); // silently fail if not logged in
  }, []);

  const load = useCallback(async () => {
    setLoading(true); setError('');
    try {
      if (mode === 'browse') {
        const params = { limit: PER_PAGE, offset: page * PER_PAGE };
        if (country) params.country = country;
        if (subject) params.subject = subject;
        if (maxTuition) params.max_tuition = maxTuition;
        if (search) params.search = search;
        const res = await universitiesAPI.list(params);
        setUniversities(res.universities || []);
        setTotal(res.total || 0);
      } else {
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
      {mode === 'matches' && !loading && !error && universities.length > 0 && (
        <div className="bg-lavendLight border border-lavender/20 rounded-xl p-4 space-y-2">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-lavender shrink-0" />
            <p className="text-sm text-lavender font-bold">
              Personalised ranking — scored out of 100 across 8 factors specific to your profile
            </p>
          </div>
          <div className="flex flex-wrap gap-1.5 text-[10px]">
            {[
              { label: 'Subject match', pts: '35pts', color: 'bg-lavender/20 text-lavender' },
              { label: 'Budget fit', pts: '20pts', color: 'bg-mintLight text-teal-700' },
              { label: 'CGPA eligibility', pts: '15pts', color: 'bg-amberLight text-amber-700' },
              { label: 'Ranking preference', pts: '10pts', color: 'bg-skyLight text-blue-700' },
              { label: 'Country preference', pts: '10pts', color: 'bg-peachLight text-orange-700' },
              { label: 'English score', pts: '5pts', color: 'bg-mintLight text-teal-700' },
              { label: 'Profile bonus', pts: '+3pts', color: 'bg-lavendLight text-lavender' },
              { label: 'Scholarships / work visa', pts: '+2pts', color: 'bg-lavendLight text-lavender' },
            ].map(f => (
              <span key={f.label} className={`px-2 py-0.5 rounded-full font-semibold flex items-center gap-1 ${f.color}`}>
                {f.label} <span className="opacity-60">{f.pts}</span>
              </span>
            ))}
          </div>
          <p className="text-xs text-lavender/70">
            Click any card → <strong>Why this for me?</strong> for a full factor-by-factor breakdown.
            Hard exclusions (cost &gt;2× budget, CGPA gap &gt;2pts) are filtered out automatically.
          </p>
        </div>
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
              <UniCard
                key={uni.id}
                uni={uni}
                rank={mode === 'matches' ? i + 1 : null}
                browseMatchScore={mode === 'browse' ? matchScores[uni.id] : null}
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

function UniCard({ uni, rank, browseMatchScore }) {
  const img   = getUniversityImage(uni);
  const flag  = getCountryFlag(uni.country);
  // AI Matches mode: use uni.match_score; browse mode: use overlay from recommendations fetch
  const rawScore   = uni.match_score ?? browseMatchScore ?? null;
  const pct        = rawScore !== null ? Math.round(rawScore * 100) : null;
  const rankColors = ['bg-amber-400', 'bg-slate-400', 'bg-orange-400'];
  const scoreColor = pct >= 75 ? 'bg-teal-500' : pct >= 50 ? 'bg-lavender' : pct >= 30 ? 'bg-amber-400' : 'bg-slate-400';

  return (
    <Link to={`/universities/${uni.id}`} className="group block">
      <div className="card-hover card overflow-hidden flex flex-col">
        <div className="relative h-48 bg-surfaceAlt overflow-hidden">
          <img src={img} alt={uni.name}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
            onError={e => {
              // On error, replace with a gradient placeholder
              e.target.style.display = 'none';
              e.target.parentElement.classList.add('bg-gradient-to-br', 'from-lavendLight', 'to-mintLight');
            }} />

          {/* Rank / QS badges */}
          <div className="absolute top-3 left-3 flex gap-1.5">
            {uni.ranking && (
              <span className="badge bg-white/90 backdrop-blur-sm text-lavender border border-lavender/20 shadow-sm">
                QS #{uni.ranking}
              </span>
            )}
            {rank && rank <= 3 && (
              <span className={`badge ${rankColors[rank - 1]} text-white shadow-sm`}>#{rank}</span>
            )}
          </div>

          {/* Match score ring */}
          {pct !== null && (
            <div className="absolute top-3 right-3">
              <div className={`w-11 h-11 rounded-full flex flex-col items-center justify-center border-2 border-white shadow-md ${scoreColor} text-white`}>
                <span className="text-[10px] font-black leading-none">{pct}%</span>
                <span className="text-[7px] opacity-80">match</span>
              </div>
            </div>
          )}

          {/* Country + subject overlay */}
          <div className="absolute bottom-0 inset-x-0 bg-gradient-to-t from-black/75 to-transparent p-3 pt-10">
            <div className="flex items-center gap-1.5 flex-wrap">
              <span className="text-sm">{flag}</span>
              <span className="text-white/90 text-xs font-semibold">{uni.country}</span>
              {uni.subject && (
                <div className="ml-auto flex gap-1 flex-wrap justify-end">
                  {uni.subject.split('|').slice(0, 2).map(s => (
                    <span key={s} className="text-white/85 text-[9px] bg-white/25 px-1.5 py-0.5 rounded-full backdrop-blur-sm">
                      {s.trim()}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="p-4 flex flex-col flex-1">
          <h3 className="font-bold text-text text-sm leading-snug mb-3 group-hover:text-lavender transition-colors line-clamp-2">
            {uni.name}
          </h3>
          <div className="grid grid-cols-2 gap-2 mt-auto">
            {uni.tuition && <Chip label="Tuition/yr" val={fmtINR(uni.tuition)} />}
            {uni.ielts && <Chip label="IELTS min" val={`${uni.ielts}+`} />}
            {uni.requirements_cgpa && <Chip label="Min CGPA" val={uni.requirements_cgpa} />}
            {uni.job_market_score && <Chip label="Jobs score" val={`${uni.job_market_score}/10`} accent />}
          </div>
        </div>
      </div>
    </Link>
  );
}

const Chip = ({ label, val, accent }) => (
  <div className={`rounded-lg p-2 ${accent ? 'bg-lavendLight' : 'bg-surfaceAlt'}`}>
    <p className="text-[10px] text-muted">{label}</p>
    <p className={`text-xs font-bold ${accent ? 'text-lavender' : 'text-text'}`}>{val}</p>
  </div>
);
