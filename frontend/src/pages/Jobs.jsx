import { useState, useEffect } from 'react';
import { jobsAPI } from '../api/jobs';
import {
  Briefcase, Search, MapPin, DollarSign, ExternalLink, Loader2,
  Wifi, Building2, Clock, TrendingUp, Globe, ChevronDown, BookOpen
} from 'lucide-react';

// ── Constants ──────────────────────────────────────────────────────────────────

const LOCATION_GROUPS = [
  {
    label: "Top Study Hubs",
    cities: ["London", "New York", "Toronto", "Berlin", "Sydney", "Singapore", "Dublin", "Amsterdam"]
  },
  {
    label: "North America",
    cities: ["New York", "Los Angeles", "San Francisco", "Boston", "Chicago", "Toronto", "Vancouver", "Montreal", "Ottawa"]
  },
  {
    label: "Europe",
    cities: ["London", "Berlin", "Munich", "Frankfurt", "Hamburg", "Cologne", "Amsterdam", "Rotterdam", "Paris", "Lyon", "Dublin", "Zurich", "Edinburgh"]
  },
  {
    label: "Asia-Pacific & Middle East",
    cities: ["Singapore", "Tokyo", "Sydney", "Melbourne", "Dubai"]
  },
];

const FIELDS = [
  "All fields", "Computer Science", "Data Science", "Finance",
  "Marketing", "Engineering", "Medicine", "Law", "Business", "Design",
];

const JOB_TYPES = [
  { value: "all",        label: "All Jobs"   },
  { value: "graduate",   label: "Graduate"   },
  { value: "internship", label: "Internship" },
  { value: "part-time",  label: "Part-time"  },
  { value: "remote",     label: "Remote"     },
];

const TYPE_STYLES = {
  "graduate":   "badge-mint",
  "internship": "badge-lavender",
  "part-time":  "badge-amber",
  "remote":     "badge-sky",
  "full-time":  "badge-peach",
};

const TYPE_PILL_COLORS = {
  internship: "bg-lavendLight text-lavender border border-lavender/20",
  graduate:   "bg-mintLight text-teal-600 border border-teal-200",
  "part-time":"bg-amberLight text-amber-700 border border-amber-200",
};

const CITY_SALARY = {
  "London":        { min: 28000,  max: 65000,  currency: 'GBP', symbol: '£'  },
  "New York":      { min: 50000,  max: 110000, currency: 'USD', symbol: '$'  },
  "Berlin":        { min: 32000,  max: 70000,  currency: 'EUR', symbol: '€'  },
  "Toronto":       { min: 45000,  max: 90000,  currency: 'CAD', symbol: 'C$' },
  "Sydney":        { min: 55000,  max: 95000,  currency: 'AUD', symbol: 'A$' },
  "Singapore":     { min: 40000,  max: 85000,  currency: 'SGD', symbol: 'S$' },
  "Dublin":        { min: 35000,  max: 75000,  currency: 'EUR', symbol: '€'  },
  "Amsterdam":     { min: 38000,  max: 80000,  currency: 'EUR', symbol: '€'  },
  "Paris":         { min: 30000,  max: 65000,  currency: 'EUR', symbol: '€'  },
  "Dubai":         { min: 60000,  max: 130000, currency: 'AED', symbol: 'AED'},
  "Los Angeles":   { min: 50000,  max: 105000, currency: 'USD', symbol: '$'  },
  "Tokyo":         { min: 3000000,max: 7000000,currency: 'JPY', symbol: '¥'  },
  "Melbourne":     { min: 55000,  max: 90000,  currency: 'AUD', symbol: 'A$' },
  "Edinburgh":     { min: 25000,  max: 55000,  currency: 'GBP', symbol: '£'  },
  "Munich":        { min: 42000,  max: 85000,  currency: 'EUR', symbol: '€'  },
  "Vancouver":     { min: 50000,  max: 95000,  currency: 'CAD', symbol: 'C$' },
  "Zurich":        { min: 75000,  max: 140000, currency: 'CHF', symbol: 'CHF'},
  "Boston":        { min: 55000,  max: 115000, currency: 'USD', symbol: '$'  },
  "Chicago":       { min: 48000,  max: 100000, currency: 'USD', symbol: '$'  },
  "San Francisco": { min: 80000,  max: 160000, currency: 'USD', symbol: '$'  },
};

// Portal country tabs — ordered by popularity for Indian students
const PORTAL_COUNTRIES = [
  { name: "UK",          code: "GB", flag: "🇬🇧" },
  { name: "USA",         code: "US", flag: "🇺🇸" },
  { name: "Canada",      code: "CA", flag: "🇨🇦" },
  { name: "Germany",     code: "DE", flag: "🇩🇪" },
  { name: "Australia",   code: "AU", flag: "🇦🇺" },
  { name: "Ireland",     code: "IE", flag: "🇮🇪" },
  { name: "Netherlands", code: "NL", flag: "🇳🇱" },
  { name: "Singapore",   code: "SG", flag: "🇸🇬" },
  { name: "UAE",         code: "AE", flag: "🇦🇪" },
  { name: "France",      code: "FR", flag: "🇫🇷" },
  { name: "Sweden",      code: "SE", flag: "🇸🇪" },
  { name: "Norway",      code: "NO", flag: "🇳🇴" },
  { name: "New Zealand", code: "NZ", flag: "🇳🇿" },
  { name: "Japan",       code: "JP", flag: "🇯🇵" },
  { name: "Switzerland", code: "CH", flag: "🇨🇭" },
  { name: "South Korea", code: "KR", flag: "🇰🇷" },
];

// Domain → clearbit logo URL helper
function logoUrl(url) {
  try {
    const domain = new URL(url).hostname.replace(/^www\./, '');
    return `https://logo.clearbit.com/${domain}`;
  } catch {
    return null;
  }
}

function timeAgo(dateStr) {
  if (!dateStr) return null;
  const ts = typeof dateStr === 'number' ? dateStr * 1000 : Date.parse(dateStr);
  if (!ts || isNaN(ts)) return null;
  const diff = Date.now() - ts;
  const days = Math.floor(diff / 86400000);
  if (days === 0) return 'Today';
  if (days === 1) return 'Yesterday';
  if (days < 30) return `${days}d ago`;
  return `${Math.floor(days / 30)}mo ago`;
}

// ── Job Portals section ───────────────────────────────────────────────────────

function PortalLogo({ url, name, color }) {
  const [imgErr, setImgErr] = useState(false);
  const src = logoUrl(url);
  const initial = (name || '?')[0].toUpperCase();

  if (!src || imgErr) {
    return (
      <div
        className="w-10 h-10 rounded-xl flex items-center justify-center font-bold text-white text-sm flex-shrink-0"
        style={{ backgroundColor: color || '#6366f1' }}
      >
        {initial}
      </div>
    );
  }
  return (
    <img
      src={src}
      alt={name}
      onError={() => setImgErr(true)}
      className="w-10 h-10 rounded-xl object-contain bg-white border border-surfaceBorder flex-shrink-0 p-1"
    />
  );
}

function PortalCard({ portal }) {
  return (
    <a
      href={portal.url}
      target="_blank"
      rel="noopener noreferrer"
      className="card p-4 hover:shadow-cardHov hover:border-lavender/30 transition-all flex items-start gap-3 group"
    >
      <PortalLogo url={portal.url} name={portal.name} color={portal.logo_color} />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1.5">
          <h3 className="font-bold text-text text-sm group-hover:text-lavender transition-colors truncate">
            {portal.name}
          </h3>
          <ExternalLink className="w-3 h-3 text-muted flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity" />
        </div>
        <p className="text-xs text-muted mt-0.5 leading-relaxed line-clamp-2">
          {portal.description}
        </p>
        <div className="flex flex-wrap gap-1.5 mt-2">
          {(portal.type || []).map(t => (
            <span key={t} className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${TYPE_PILL_COLORS[t] || 'bg-surfaceAlt text-textSoft border border-surfaceBorder'}`}>
              {t}
            </span>
          ))}
          {portal.student_friendly && (
            <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-mintLight text-teal-600 border border-teal-100">
              student-friendly
            </span>
          )}
        </div>
      </div>
    </a>
  );
}

function JobPortalsPanel() {
  const [activeCountry, setActiveCountry] = useState('UK');
  const [portals, setPortals] = useState({});
  const [globalFallbackPortals, setGlobalFallbackPortals] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (portals[activeCountry]) return;
    setLoading(true);
    jobsAPI.getPortals(activeCountry)
      .then(data => {
        const list = (data.results || []).flatMap(r => r.portals);
        setPortals(p => ({ ...p, [activeCountry]: list }));
      })
      .catch(() => setPortals(p => ({ ...p, [activeCountry]: [] })))
      .finally(() => setLoading(false));
  }, [activeCountry]);

  useEffect(() => {
    if (globalFallbackPortals.length) return;
    jobsAPI.getPortals()
      .then(data => {
        const all = (data.results || []).flatMap(r =>
          (r.portals || []).map(p => ({ ...p, _country: r.country }))
        );
        const seen = new Set();
        const curated = all
          .filter(p => p.student_friendly)
          .filter(p => {
            const key = (p.name || p.url || '').toLowerCase();
            if (!key || seen.has(key)) return false;
            seen.add(key);
            return true;
          })
          .slice(0, 12);
        setGlobalFallbackPortals(curated);
      })
      .catch(() => setGlobalFallbackPortals([]));
  }, [globalFallbackPortals.length]);

  const current = portals[activeCountry] || [];
  const activeFlag = PORTAL_COUNTRIES.find(c => c.name === activeCountry)?.flag || '';
  const showFallback = !loading && current.length === 0 && globalFallbackPortals.length > 0;

  return (
    <div className="card overflow-hidden">
      {/* Header */}
      <div className="px-5 py-4 border-b border-surfaceBorder bg-gradient-to-r from-lavendLight/40 to-skyLight/20">
        <div className="flex items-center gap-2 mb-1">
          <div className="w-7 h-7 bg-lavendLight rounded-lg flex items-center justify-center">
            <BookOpen className="w-4 h-4 text-lavender" />
          </div>
          <h2 className="text-base font-bold text-text">Job Portals by Country</h2>
        </div>
        <p className="text-xs text-muted">Student-friendly job boards and graduate platforms — click to visit</p>
      </div>

      {/* Country tabs (scrollable) */}
      <div className="flex gap-1.5 px-4 py-3 overflow-x-auto border-b border-surfaceBorder scrollbar-none">
        {PORTAL_COUNTRIES.map(c => (
          <button
            key={c.name}
            onClick={() => setActiveCountry(c.name)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-all flex-shrink-0
              ${activeCountry === c.name
                ? 'bg-lavender text-white shadow-sm'
                : 'bg-surfaceAlt text-textSoft hover:bg-lavendLight hover:text-lavender border border-surfaceBorder'}`}
          >
            <span>{c.flag}</span>
            {c.name}
          </button>
        ))}
      </div>

      {/* Portal grid */}
      <div className="p-4">
        {loading ? (
          <div className="flex items-center gap-2 py-6 justify-center text-muted text-sm">
            <Loader2 className="w-4 h-4 animate-spin" /> Loading portals…
          </div>
        ) : showFallback ? (
          <>
            <p className="text-xs text-muted mb-3 font-medium">
              No curated list for {activeCountry} yet. Showing global student-friendly portals.
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-3">
              {globalFallbackPortals.map(portal => (
                <PortalCard
                  key={`fallback-${portal.id || portal.url}`}
                  portal={{
                    ...portal,
                    description: portal._country
                      ? `${portal.description} (${portal._country})`
                      : portal.description,
                  }}
                />
              ))}
            </div>
          </>
        ) : current.length === 0 ? (
          <p className="text-muted text-sm text-center py-6">No portals available for {activeCountry} yet.</p>
        ) : (
          <>
            <p className="text-xs text-muted mb-3 font-medium">
              {activeFlag} <strong>{current.length} portals</strong> for students in {activeCountry}
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-3">
              {current.map(portal => <PortalCard key={portal.id} portal={portal} />)}
            </div>
          </>
        )}
      </div>
    </div>
  );
}

// ── Main Jobs page ────────────────────────────────────────────────────────────

export default function Jobs() {
  const [locationGroups, setLocationGroups] = useState(LOCATION_GROUPS);
  const [sources, setSources]     = useState([]);
  const [location, setLocation]   = useState('London');
  const [jobType, setJobType]     = useState('all');
  const [source, setSource]       = useState('all');
  const [field, setField]         = useState('All fields');
  const [keywords, setKeywords]   = useState('');
  const [jobs, setJobs]           = useState([]);
  const [loading, setLoading]     = useState(false);
  const [searched, setSearched]   = useState(false);
  const [error, setError]         = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [page, setPage]           = useState(1);
  const [total, setTotal]         = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const PAGE_SIZE                 = 12;
  const [searchNonce, setSearchNonce] = useState(0);

  const canonicalCity = (city) =>
    String(city || '')
      .trim()
      .replace(/\s+/g, ' ')
      .replace(/\b\w/g, ch => ch.toUpperCase());

  const dedupeCities = (cities) => {
    const seen = new Set();
    const result = [];
    cities.forEach((city) => {
      const normalized = canonicalCity(city);
      const key = normalized.toLowerCase();
      if (!normalized || seen.has(key)) return;
      seen.add(key);
      result.push(normalized);
    });
    return result;
  };

  const mergeLocationGroups = (apiLocations = []) => {
    const grouped = LOCATION_GROUPS.map(group => ({
      label: group.label,
      cities: dedupeCities(group.cities),
    }));
    const baseSet = new Set(grouped.flatMap(g => g.cities).map(c => c.toLowerCase()));
    const apiUnique = dedupeCities(apiLocations).filter(c => !baseSet.has(c.toLowerCase()));
    if (apiUnique.length) {
      grouped.push({ label: "More Cities", cities: apiUnique.sort((a, b) => a.localeCompare(b)) });
    }
    return grouped;
  };

  const allLocations = locationGroups.flatMap(g => g.cities);

  const buildKeywords = () => {
    const parts = [keywords];
    if (field !== 'All fields') parts.unshift(field);
    return parts.filter(Boolean).join(' ');
  };

  const search = async () => {
    setLoading(true); setError(''); setSearched(true);
    try {
      const res = await jobsAPI.searchJobs(location, jobType, buildKeywords(), source === 'all' ? '' : source, page, PAGE_SIZE);
      setJobs(res.jobs || []);
      setTotal(res.total || 0);
      setTotalPages(res.total_pages || 0);
      if (typeof res.page === 'number' && res.page !== page) {
        setPage(res.page);
      }
    } catch { setError('Failed to fetch jobs. Please try again.'); }
    finally { setLoading(false); }
  };

  useEffect(() => {
    jobsAPI.getFilters()
      .then((res) => {
        const fromApi = Array.isArray(res?.locations) ? res.locations.filter(Boolean) : [];
        const sourceList = Array.isArray(res?.sources) ? res.sources.filter(Boolean) : [];
        const merged = mergeLocationGroups(fromApi);
        setLocationGroups(merged);
        const firstAvailable = merged.flatMap(g => g.cities)[0];
        const currentExists = merged.some(g => g.cities.includes(location));
        if (!currentExists && firstAvailable) {
          setLocation(firstAvailable);
        }
        setSources(sourceList);
      })
      .catch(() => {});
    search();
  }, []);

  useEffect(() => {
    if (!searched) return;
    search();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, searchNonce]);

  const triggerSearch = () => {
    setPage(1);
    setSearchNonce(n => n + 1);
  };

  const salaryInfo = CITY_SALARY[location];
  const filteredJobs = jobs;

  return (
    <div className="space-y-5 animate-fade-in">
      {/* Header */}
      <div className="page-header">
        <div className="page-icon bg-skyLight text-blue-600"><Briefcase className="w-5 h-5" /></div>
        <div>
          <h1 className="text-2xl font-black text-text">Jobs & Careers</h1>
          <p className="text-muted text-sm">Live listings + job portals curated for international students</p>
        </div>
      </div>

      {/* Job Portals by Country */}
      <JobPortalsPanel />

      {/* Salary insight banner */}
      {salaryInfo && (
        <div className="card p-4 bg-gradient-to-r from-skyLight/50 to-lavendLight/30 border-blue-100 flex items-center gap-4 flex-wrap">
          <div className="flex items-center gap-2">
            <div className="page-icon bg-skyLight text-blue-600 w-8 h-8">
              <TrendingUp className="w-4 h-4" />
            </div>
            <div>
              <p className="text-xs font-bold text-text">Typical graduate salary in {location}</p>
              <p className="text-xs text-muted">
                {salaryInfo.symbol}{(salaryInfo.min / 1000).toFixed(0)}k – {salaryInfo.symbol}{(salaryInfo.max / 1000).toFixed(0)}k {salaryInfo.currency}/year · based on market data
              </p>
            </div>
          </div>
          <div className="ml-auto hidden sm:flex items-center gap-1 text-xs text-muted">
            <Globe className="w-3.5 h-3.5" />
            Salaries vary by role and experience
          </div>
        </div>
      )}

      {/* Live job search */}
      <div className="card p-4 space-y-3">
        <div className="flex flex-wrap items-center gap-2 mb-1">
          <Search className="w-4 h-4 text-lavender flex-shrink-0" />
          <h2 className="text-sm font-bold text-text">Search Live Listings</h2>
          <span className="text-xs text-muted basis-full sm:basis-auto sm:ml-1">
            Arbeitnow · Remotive · RemoteOK · The Muse — refreshed every 30 min
          </span>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-[minmax(0,1fr)_180px_auto_auto] gap-3 items-stretch">
          <div className="relative min-w-0">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-muted pointer-events-none" />
            <input
              className="input-field !pl-11 min-w-0"
              placeholder="Keywords: python, marketing, finance…"
              value={keywords}
              onChange={e => setKeywords(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && triggerSearch()}
            />
          </div>
          <div className="relative min-w-0">
            <MapPin className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-muted pointer-events-none" />
            <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted pointer-events-none" />
            <select
              className="input-field !pl-11 !pr-10 w-full appearance-none truncate"
              value={location}
              onChange={e => { setLocation(e.target.value); setPage(1); setSearchNonce(n => n + 1); }}
            >
              {locationGroups.map(group => (
                <optgroup key={group.label} label={group.label}>
                  {group.cities.map(city => (
                    <option key={`${group.label}-${city}`} value={city}>{city}</option>
                  ))}
                </optgroup>
              ))}
            </select>
          </div>
          <button onClick={triggerSearch} className="btn-primary px-6 justify-center whitespace-nowrap">
            <Search className="w-4 h-4" /> Search
          </button>
          <button
            onClick={() => setShowFilters(f => !f)}
            className="flex items-center justify-center gap-1.5 px-4 py-2 rounded-xl border border-surfaceBorder text-sm text-textSoft font-medium hover:border-lavender/50 transition-colors whitespace-nowrap"
          >
            Filters <ChevronDown className={`w-3.5 h-3.5 transition-transform ${showFilters ? 'rotate-180' : ''}`} />
          </button>
        </div>

        {showFilters && (
          <div className="pt-3 border-t border-surfaceBorder space-y-3">
            <div>
              <p className="text-xs font-semibold text-muted mb-2">Field of Study</p>
              <div className="flex gap-2 flex-wrap">
                {FIELDS.map(f => (
                  <button key={f} onClick={() => { setField(f); setPage(1); setSearchNonce(n => n + 1); }}
                    className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all whitespace-nowrap leading-tight
                      ${field === f ? 'bg-blue-500 text-white border-blue-500' : 'bg-white text-textSoft border-surfaceBorder hover:border-blue-300'}`}>
                    {f}
                  </button>
                ))}
              </div>
            </div>
            {sources.length > 0 && (
              <div>
                <p className="text-xs font-semibold text-muted mb-2">Source</p>
                <div className="flex gap-2 flex-wrap">
                  <button
                    onClick={() => { setSource('all'); setPage(1); setSearchNonce(n => n + 1); }}
                    className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all whitespace-nowrap leading-tight
                      ${source === 'all' ? 'bg-blue-500 text-white border-blue-500' : 'bg-white text-textSoft border-surfaceBorder hover:border-blue-300'}`}
                  >
                    All Sources
                  </button>
                  {sources.map(s => (
                    <button
                      key={s}
                      onClick={() => { setSource(s); setPage(1); setSearchNonce(n => n + 1); }}
                      className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all whitespace-nowrap leading-tight
                        ${source === s ? 'bg-blue-500 text-white border-blue-500' : 'bg-white text-textSoft border-surfaceBorder hover:border-blue-300'}`}
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        <div className="flex gap-2 flex-wrap">
          {JOB_TYPES.map(t => (
            <button key={t.value} onClick={() => { setJobType(t.value); setPage(1); setSearchNonce(n => n + 1); }}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all
                ${jobType === t.value ? 'bg-lavender text-white border-lavender' : 'bg-white text-textSoft border-surfaceBorder hover:border-lavender/50'}`}>
              {t.label}
            </button>
          ))}
        </div>
      </div>

      {/* Results */}
      {loading ? (
        <div className="flex flex-col items-center py-16 gap-3">
          <Loader2 className="w-8 h-8 text-lavender animate-spin" />
          <p className="text-muted text-sm">Fetching live jobs from multiple sources…</p>
        </div>
      ) : error ? (
        <div className="card p-6 text-center text-rose font-medium">{error}</div>
      ) : filteredJobs.length > 0 ? (
        <div className="space-y-3">
          <p className="text-sm text-muted font-medium">
            Showing <strong>{Math.min((page - 1) * PAGE_SIZE + 1, total || filteredJobs.length)}</strong>
            -<strong>{Math.min(page * PAGE_SIZE, total || filteredJobs.length)}</strong>
            of <strong>{total || filteredJobs.length}</strong> jobs near <strong>{location}</strong>
            {field !== 'All fields' && <> · {field}</>}
          </p>
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-3">
            {filteredJobs.map((job, i) => <JobCard key={job.id || i} job={job} locationSalary={salaryInfo} />)}
          </div>
          {totalPages > 1 && (
            <div className="flex items-center justify-between pt-2">
              <button
                className="px-4 py-2 rounded-xl border border-surfaceBorder text-sm text-textSoft font-medium disabled:opacity-40"
                disabled={page <= 1 || loading}
                onClick={() => setPage(p => Math.max(1, p - 1))}
              >
                Previous
              </button>
              <span className="text-sm text-muted font-medium">
                Page {page} of {totalPages}
              </span>
              <button
                className="px-4 py-2 rounded-xl border border-surfaceBorder text-sm text-textSoft font-medium disabled:opacity-40"
                disabled={page >= totalPages || loading}
                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
              >
                Next
              </button>
            </div>
          )}
        </div>
      ) : searched ? (
        <div className="card p-12 text-center">
          <Briefcase className="w-10 h-10 text-muted mx-auto mb-3 opacity-30" />
          <p className="font-semibold text-text">No live listings found</p>
          <p className="text-sm text-muted mt-1">Try different keywords or use the Job Portals above to search directly</p>
        </div>
      ) : null}
    </div>
  );
}

// ── Job Card ──────────────────────────────────────────────────────────────────

function JobCard({ job, locationSalary }) {
  const initials  = (job.company || 'Co').slice(0, 2).toUpperCase();
  const colorIdx  = initials.charCodeAt(0) % 5;
  const colors    = [
    'bg-lavendLight text-lavender',
    'bg-mintLight text-teal-600',
    'bg-skyLight text-blue-600',
    'bg-peachLight text-peach',
    'bg-amberLight text-amber-600',
  ];
  const posted    = timeAgo(job.posted);
  const salary    = (job.salary && job.salary !== 'Competitive') ? job.salary : null;

  return (
    <div className="card p-4 hover:shadow-cardHov transition-shadow">
      <div className="flex items-start gap-3">
        <div className={`w-11 h-11 rounded-xl flex items-center justify-center font-bold text-sm flex-shrink-0 ${colors[colorIdx]}`}>
          {initials}
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <div>
              <h3 className="font-bold text-text text-sm line-clamp-1">{job.title}</h3>
              <p className="text-textSoft text-xs mt-0.5 flex items-center gap-1">
                <Building2 className="w-3 h-3" />{job.company || 'Company'}
              </p>
            </div>
            {job.apply_url && (
              <a
                href={job.apply_url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex-shrink-0 btn-primary px-3 py-1.5 text-xs"
              >
                Apply <ExternalLink className="w-3 h-3" />
              </a>
            )}
          </div>

          <div className="flex flex-wrap gap-2 mt-2">
            {job.location && (
              <span className="flex items-center gap-1 text-xs text-muted">
                {job.remote ? <Wifi className="w-3 h-3" /> : <MapPin className="w-3 h-3" />}
                {job.location}
              </span>
            )}
            {salary ? (
              <span className="flex items-center gap-1 text-xs font-semibold text-teal-600">
                <DollarSign className="w-3 h-3" />{salary}
              </span>
            ) : locationSalary ? (
              <span className="flex items-center gap-1 text-xs text-muted">
                <DollarSign className="w-3 h-3" />
                est. {locationSalary.symbol}{(locationSalary.min / 1000).toFixed(0)}k–{locationSalary.symbol}{(locationSalary.max / 1000).toFixed(0)}k/yr
              </span>
            ) : null}
            {posted && (
              <span className="flex items-center gap-1 text-xs text-muted">
                <Clock className="w-3 h-3" />{posted}
              </span>
            )}
          </div>

          <div className="flex flex-wrap gap-1.5 mt-2">
            <span className={`badge ${TYPE_STYLES[job.job_type] || 'badge-lavender'}`}>
              {job.job_type}
            </span>
            {job.remote && <span className="badge badge-sky">Remote</span>}
            {job.source && (
              <span className="text-[9px] font-bold px-1.5 py-0.5 rounded-full bg-surfaceAlt text-textSoft border border-surfaceBorder">
                {job.source}
              </span>
            )}
            {(job.tags || []).slice(0, 2).map(t => (
              <span key={t} className="badge badge-lavender opacity-70">{t}</span>
            ))}
          </div>

          {job.description && (
            <p className="text-xs text-muted mt-2 line-clamp-2 leading-relaxed">{job.description}</p>
          )}
        </div>
      </div>
    </div>
  );
}
