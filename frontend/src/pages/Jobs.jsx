import { useState, useEffect } from 'react';
import { jobsAPI } from '../api/jobs';
import {
  Briefcase, Search, MapPin, DollarSign, ExternalLink, Loader2,
  Wifi, Building2, Clock, TrendingUp, Globe, ChevronDown
} from 'lucide-react';

const LOCATIONS = [
  "London", "New York", "Berlin", "Toronto", "Sydney",
  "Singapore", "Dublin", "Amsterdam", "Paris", "Dubai",
  "Los Angeles", "Tokyo", "Melbourne", "Edinburgh", "Munich",
  "Vancouver", "Zurich", "Boston", "Chicago", "San Francisco",
  "Hamburg", "Frankfurt", "Cologne", "Rotterdam", "Lyon", "Montreal", "Ottawa",
];

const FIELDS = [
  "All fields", "Computer Science", "Data Science", "Finance",
  "Marketing", "Engineering", "Medicine", "Law", "Business", "Design",
];

const JOB_TYPES = [
  { value: "all",        label: "All Jobs"    },
  { value: "graduate",   label: "Graduate"    },
  { value: "internship", label: "Internship"  },
  { value: "part-time",  label: "Part-time"   },
  { value: "remote",     label: "Remote"      },
];

const TYPE_STYLES = {
  "graduate":   "badge-mint",
  "internship": "badge-lavender",
  "part-time":  "badge-amber",
  "remote":     "badge-sky",
  "full-time":  "badge-peach",
};

// Salary range estimates by city (annual USD)
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

function formatSalary(salaryStr) {
  if (!salaryStr || salaryStr === 'Competitive') return null;
  // Already formatted — return as-is
  return salaryStr;
}

export default function Jobs() {
  const [location, setLocation]   = useState('London');
  const [jobType, setJobType]     = useState('all');
  const [field, setField]         = useState('All fields');
  const [keywords, setKeywords]   = useState('');
  const [jobs, setJobs]           = useState([]);
  const [loading, setLoading]     = useState(false);
  const [searched, setSearched]   = useState(false);
  const [error, setError]         = useState('');
  const [showFilters, setShowFilters] = useState(false);

  const buildKeywords = () => {
    const parts = [keywords];
    if (field !== 'All fields') parts.unshift(field);
    return parts.filter(Boolean).join(' ');
  };

  const search = async () => {
    setLoading(true); setError(''); setSearched(true);
    try {
      const res = await jobsAPI.searchJobs(location, jobType, buildKeywords());
      setJobs(res.jobs || []);
    } catch { setError('Failed to fetch jobs. Please try again.'); }
    finally { setLoading(false); }
  };

  useEffect(() => { search(); }, []);

  const salaryInfo = CITY_SALARY[location];
  const filteredJobs = jobs.filter(j =>
    jobType === 'all' || j.job_type === jobType || (jobType === 'remote' && j.remote)
  );

  return (
    <div className="space-y-5 animate-fade-in">
      {/* Header */}
      <div className="page-header">
        <div className="page-icon bg-skyLight text-blue-600"><Briefcase className="w-5 h-5" /></div>
        <div>
          <h1 className="text-2xl font-black text-text">Jobs & Careers</h1>
          <p className="text-muted text-sm">Live listings from Arbeitnow · Remotive · RemoteOK · The Muse — refreshed every 30 min</p>
        </div>
      </div>

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

      {/* Search bar */}
      <div className="card p-4 space-y-3">
        <div className="flex gap-3 flex-wrap">
          <div className="relative flex-1 min-w-48">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-muted pointer-events-none" />
            <input
              className="input-field pl-10"
              placeholder="Keywords: python, marketing, finance…"
              value={keywords}
              onChange={e => setKeywords(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && search()}
            />
          </div>
          <div className="relative w-44">
            <MapPin className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-muted pointer-events-none" />
            <select
              className="input-field pl-10 w-full appearance-none"
              value={location}
              onChange={e => setLocation(e.target.value)}
            >
              {LOCATIONS.map(l => <option key={l} value={l}>{l}</option>)}
            </select>
          </div>
          <button onClick={search} className="btn-primary px-6">
            <Search className="w-4 h-4" /> Search
          </button>
          <button
            onClick={() => setShowFilters(f => !f)}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl border border-surfaceBorder text-sm text-textSoft font-medium hover:border-lavender/50 transition-colors"
          >
            Filters <ChevronDown className={`w-3.5 h-3.5 transition-transform ${showFilters ? 'rotate-180' : ''}`} />
          </button>
        </div>

        {/* Expanded filters */}
        {showFilters && (
          <div className="pt-3 border-t border-surfaceBorder space-y-3">
            <div>
              <p className="text-xs font-semibold text-muted mb-2">Field of Study</p>
              <div className="flex gap-2 flex-wrap">
                {FIELDS.map(f => (
                  <button key={f} onClick={() => setField(f)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all
                      ${field === f ? 'bg-blue-500 text-white border-blue-500' : 'bg-white text-textSoft border-surfaceBorder hover:border-blue-300'}`}>
                    {f}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Job type chips */}
        <div className="flex gap-2 flex-wrap">
          {JOB_TYPES.map(t => (
            <button key={t.value} onClick={() => setJobType(t.value)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all
                ${jobType === t.value ? 'bg-lavender text-white border-lavender' : 'bg-white text-textSoft border-surfaceBorder hover:border-lavender/50'}`}>
              {t.label}
            </button>
          ))}
        </div>
      </div>

      {/* Results */}
      {loading ? (
        <div className="flex flex-col items-center py-20 gap-3">
          <Loader2 className="w-8 h-8 text-lavender animate-spin" />
          <p className="text-muted text-sm">Fetching live jobs from multiple sources…</p>
        </div>
      ) : error ? (
        <div className="card p-6 text-center text-rose font-medium">{error}</div>
      ) : filteredJobs.length > 0 ? (
        <div className="space-y-3">
          <p className="text-sm text-muted font-medium">
            <strong>{filteredJobs.length}</strong> jobs found near <strong>{location}</strong>
            {field !== 'All fields' && <> · {field}</>}
          </p>
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-3">
            {filteredJobs.map((job, i) => <JobCard key={job.id || i} job={job} locationSalary={salaryInfo} />)}
          </div>
        </div>
      ) : searched ? (
        <div className="card p-12 text-center">
          <Briefcase className="w-10 h-10 text-muted mx-auto mb-3 opacity-30" />
          <p className="font-semibold text-text">No jobs found</p>
          <p className="text-sm text-muted mt-1">Try different keywords or a different location</p>
        </div>
      ) : null}
    </div>
  );
}

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
  const salary    = formatSalary(job.salary);

  return (
    <div className="card p-4 hover:shadow-cardHov transition-shadow">
      <div className="flex items-start gap-3">
        {/* Company logo */}
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
