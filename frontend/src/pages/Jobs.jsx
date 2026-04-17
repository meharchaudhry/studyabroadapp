import { useState, useEffect } from 'react';
import { jobsAPI_ext } from '../api/visa';
import { jobsAPI } from '../api/jobs';
import { Briefcase, ExternalLink, Search, MapPin, Loader2, Building2, Bookmark } from 'lucide-react';

const ALL_COUNTRIES = ['UK','Germany','France','Netherlands','Australia','Singapore','HongKong','USA','Finland','Spain','Switzerland'];
const JOB_TYPES = [
  { label: 'All', value: '' },
  { label: 'Internships', value: 'internship' },
  { label: 'Part-Time', value: 'part-time' },
  { label: 'Graduate', value: 'graduate' },
];
const FLAG = { USA:'🇺🇸', UK:'🇬🇧', Germany:'🇩🇪', France:'🇫🇷', Netherlands:'🇳🇱', Australia:'🇦🇺', Singapore:'🇸🇬', HongKong:'🇭🇰', Spain:'🇪🇸', Switzerland:'🇨🇭', Finland:'🇫🇮' };

export default function Jobs() {
  const [country, setCountry] = useState('UK');
  const [jobType, setJobType] = useState('');
  const [portals, setPortals] = useState([]);
  const [portalsLoading, setPortalsLoading] = useState(true);

  // Live search state
  const [liveJobs, setLiveJobs] = useState([]);
  const [location, setLocation] = useState('London');
  const [keywords, setKeywords] = useState('Software');
  const [liveLoading, setLiveLoading] = useState(false);
  const [savedJobs, setSavedJobs] = useState(new Set());

  const fetchPortals = async () => {
    setPortalsLoading(true);
    try {
      const params = { country };
      if (jobType) params.job_type = jobType;
      const res = await jobsAPI_ext.getPortals(params);
      setPortals(res.results || []);
    } catch {
      setPortals([]);
    } finally {
      setPortalsLoading(false);
    }
  };

  const fetchLiveJobs = async () => {
    setLiveLoading(true);
    try {
      const data = await jobsAPI.searchJobs(location, 'graduate', keywords);
      setLiveJobs(data.jobs || []);
    } catch {
      setLiveJobs([]);
    } finally {
      setLiveLoading(false);
    }
  };

  useEffect(() => { fetchPortals(); }, [country, jobType]);
  useEffect(() => { fetchLiveJobs(); }, []);

  const handleSave = async (id) => {
    try {
      await jobsAPI.saveJob(id);
      setSavedJobs(new Set([...savedJobs, id]));
    } catch {}
  };

  return (
    <div className="animate-fade-in space-y-6">
      <div className="page-header">
        <div className="page-icon bg-peachLight"><Briefcase className="w-5 h-5 text-peach"/></div>
        <div>
          <h1 className="text-2xl font-bold text-text">Jobs & Internships</h1>
          <p className="text-muted text-sm mt-0.5">Country-specific job portals + live Adzuna listings</p>
        </div>
      </div>

      {/* ── Section 1: Job Portals ── */}
      <div className="card p-5 space-y-4">
        <h2 className="font-bold text-text text-base">🌐 Job Portals by Country</h2>

        {/* Filters */}
        <div className="flex flex-wrap gap-3">
          <div>
            <label className="text-xs font-semibold text-muted block mb-1">Country</label>
            <div className="flex flex-wrap gap-1.5">
              {ALL_COUNTRIES.map(c => (
                <button key={c} onClick={() => setCountry(c)}
                  className={`px-2.5 py-1 rounded-lg text-xs font-semibold border transition-all ${
                    country===c ? 'bg-peach text-white border-peach' : 'bg-surfaceAlt text-textSoft border-surfaceBorder hover:border-peach hover:text-peach'
                  }`}>
                  {FLAG[c]||'🌍'} {c}
                </button>
              ))}
            </div>
          </div>
          <div>
            <label className="text-xs font-semibold text-muted block mb-1">Job Type</label>
            <div className="flex gap-1.5">
              {JOB_TYPES.map(t => (
                <button key={t.value} onClick={() => setJobType(t.value)}
                  className={`px-3 py-1 rounded-lg text-xs font-semibold border transition-all ${
                    jobType===t.value ? 'bg-peach text-white border-peach' : 'bg-surfaceAlt text-textSoft border-surfaceBorder hover:border-peach hover:text-peach'
                  }`}>
                  {t.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {portalsLoading ? (
          <div className="py-8 flex justify-center"><div className="w-7 h-7 border-2 border-peach/30 border-t-peach rounded-full animate-spin"/></div>
        ) : portals.length === 0 ? (
          <div className="text-center text-muted py-6 text-sm">No portals found.</div>
        ) : (
          portals.map(group => (
            <div key={group.country}>
              <h3 className="text-sm font-bold text-text mb-2">{FLAG[group.country]||'🌍'} {group.country}</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {group.portals.map(p => (
                  <a key={p.id} href={p.url} target="_blank" rel="noreferrer"
                    className="block border border-surfaceBorder rounded-xl p-4 hover:border-peach/50 hover:shadow-soft hover:-translate-y-0.5 transition-all group">
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <div className="flex items-center gap-2">
                        <div className="w-7 h-7 rounded-lg flex items-center justify-center text-white text-xs font-bold flex-shrink-0" style={{backgroundColor:p.logo_color}}>
                          {p.name[0]}
                        </div>
                        <h4 className="font-bold text-text text-sm group-hover:text-peach transition-colors">{p.name}</h4>
                      </div>
                      <ExternalLink className="w-3.5 h-3.5 text-muted flex-shrink-0 mt-0.5 group-hover:text-peach transition-colors"/>
                    </div>
                    <p className="text-xs text-textSoft leading-snug mb-2">{p.description}</p>
                    <div className="flex flex-wrap gap-1">
                      {p.type?.map(t=>(
                        <span key={t} className="badge badge-peach text-[10px]">
                          {t==='internship'?'🎓 Internship':t==='part-time'?'⏰ Part-time':'💼 Graduate'}
                        </span>
                      ))}
                      {p.student_friendly && <span className="badge badge-mint text-[10px]">✅ Student Friendly</span>}
                    </div>
                  </a>
                ))}
              </div>
            </div>
          ))
        )}
      </div>

      {/* ── Section 2: Live Listings ── */}
      <div className="card p-5 space-y-4">
        <h2 className="font-bold text-text text-base">🔴 Live Job Search</h2>
        <form onSubmit={e=>{e.preventDefault();fetchLiveJobs();}} className="flex flex-wrap gap-3">
          <div className="relative flex-1 min-w-[180px]">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted"/>
            <input type="text" className="input-field pl-9 py-2 text-sm" placeholder="Keywords" value={keywords} onChange={e=>setKeywords(e.target.value)}/>
          </div>
          <div className="relative flex-1 min-w-[150px]">
            <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted"/>
            <input type="text" className="input-field pl-9 py-2 text-sm" placeholder="Location" value={location} onChange={e=>setLocation(e.target.value)}/>
          </div>
          <button type="submit" disabled={liveLoading} className="btn-primary py-2">
            {liveLoading ? <Loader2 className="w-4 h-4 animate-spin"/> : 'Search'}
          </button>
        </form>

        {liveLoading ? (
          <div className="py-8 flex justify-center"><Loader2 className="w-7 h-7 text-peach animate-spin"/></div>
        ) : liveJobs.length === 0 ? (
          <div className="text-center text-muted py-6 text-sm bg-surfaceAlt rounded-xl">
            No live listings yet. Live results require an Adzuna API key in your <code className="bg-surfaceBorder px-1 rounded">.env</code>.
          </div>
        ) : (
          <div className="space-y-3">
            {liveJobs.map((job, i) => (
              <div key={job.id} className="card p-4 flex flex-col sm:flex-row gap-4 justify-between items-center group">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="font-bold text-text group-hover:text-peach transition-colors">{job.title}</h3>
                    <span className={`px-2 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider ${
                      job.title.toLowerCase().includes('graduate') ? 'bg-lavendLight text-lavender' :
                      i % 3 === 0 ? 'bg-mintLight text-teal-600' : 'bg- peachLight text-peach'
                    }`}>
                      {job.title.toLowerCase().includes('graduate') ? '🎓 Graduate Role' :
                       i % 3 === 0 ? '🏠 On-campus' : '⏰ Part-time'}
                    </span>
                  </div>
                  <div className="flex flex-wrap gap-3 text-xs text-muted mt-1">
                    <span className="flex items-center gap-1"><Building2 className="w-3.5 h-3.5"/>{job.company}</span>
                    <span className="flex items-center gap-1"><MapPin className="w-3.5 h-3.5"/>{job.location}</span>
                    {job.salary && <span className="font-semibold text-teal-600 bg-mintLight px-2 py-0.5 rounded-full">{job.salary}</span>}
                  </div>
                </div>
                <div className="flex items-center gap-2 flex-shrink-0">
                  <button onClick={()=>handleSave(job.id)}
                    className={`p-2 rounded-lg border transition-all ${savedJobs.has(job.id)?'bg-peachLight border-peach text-peach':'border-surfaceBorder hover:bg-surfaceAlt'}`}>
                    <Bookmark className="w-4 h-4"/>
                  </button>
                  <a href={job.apply_link||'#'} target="_blank" rel="noreferrer" className="btn-primary py-2 text-xs">Apply Now</a>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
