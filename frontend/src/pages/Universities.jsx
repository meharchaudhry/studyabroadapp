import { useState, useEffect } from 'react';
import { universitiesAPI } from '../api/universities';
import { GraduationCap, MapPin, Star, ExternalLink, ChevronRight, X, BookOpen, DollarSign, Award, Clock } from 'lucide-react';

const COUNTRIES = ['All','USA','UK','Germany','France','Netherlands','Australia','Singapore','HongKong','Spain','Switzerland','Finland'];
const SUBJECTS  = ['All','Computer Science','Engineering','Business','Life Sciences','Medicine','Law','Arts & Humanities','Social Sciences','Mathematics','Physics','Data Science'];

const FLAG = { USA:'🇺🇸', UK:'🇬🇧', Germany:'🇩🇪', France:'🇫🇷', Netherlands:'🇳🇱', Australia:'🇦🇺', Singapore:'🇸🇬', HongKong:'🇭🇰', Spain:'🇪🇸', Switzerland:'🇨🇭', Finland:'🇫🇮' };

function formatINR(n) {
  if (!n) return '—';
  if (n >= 100000) return `₹${(n/100000).toFixed(1)}L/yr`;
  return `₹${n.toLocaleString('en-IN')}/yr`;
}

import { Link } from 'react-router-dom';

export default function Universities() {
  const [unis, setUnis] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedCountry, setSelectedCountry] = useState('All');
  const [selectedSubject, setSelectedSubject] = useState('All');
  const [viewMode, setViewMode] = useState('browse'); // 'browse' | 'recommend'

  const fetchUnis = async () => {
    setLoading(true);
    setError('');
    try {
      if (viewMode === 'recommend') {
        const data = await universitiesAPI.getRecommendations();
        setUnis(data.recommendations || []);
      } else {
        const params = {};
        if (selectedCountry !== 'All') params.country = selectedCountry;
        if (selectedSubject !== 'All') params.subject = selectedSubject;
        params.limit = 50;
        const data = await universitiesAPI.list(params);
        setUnis(data.universities || []);
      }
    } catch {
      setError('Failed to load universities. Make sure the backend is running with the DB connected.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchUnis(); }, [selectedCountry, selectedSubject, viewMode]);

  return (
    <div className="animate-fade-in space-y-6">
      {/* Header */}
      <div className="page-header">
        <div className="page-icon bg-lavendLight"><GraduationCap className="w-5 h-5 text-lavender"/></div>
        <div>
          <h1 className="text-2xl font-bold text-text">Universities</h1>
          <p className="text-muted text-sm mt-0.5">80+ universities across 11 countries — with real admission requirements</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 p-1 bg-surfaceAlt rounded-xl border border-surfaceBorder w-fit">
        {[['browse','Browse All'],['recommend','My Matches']].map(([v,l])=>(
          <button key={v} onClick={()=>setViewMode(v)}
            className={`px-4 py-2 rounded-lg text-sm font-semibold transition-all ${viewMode===v?'bg-lavender text-white shadow-soft':'text-textSoft hover:text-text'}`}>{l}</button>
        ))}
      </div>

      {/* Filters (browse mode) */}
      {viewMode === 'browse' && (
        <div className="card p-4 flex flex-wrap gap-3 items-center">
          <div>
            <label className="text-xs font-semibold text-muted block mb-1">Country</label>
            <select value={selectedCountry} onChange={e=>setSelectedCountry(e.target.value)}
              className="input-field py-2 text-sm pr-8 min-w-[140px]">
              {COUNTRIES.map(c=><option key={c}>{c}</option>)}
            </select>
          </div>
          <div>
            <label className="text-xs font-semibold text-muted block mb-1">Subject</label>
            <select value={selectedSubject} onChange={e=>setSelectedSubject(e.target.value)}
              className="input-field py-2 text-sm pr-8 min-w-[180px]">
              {SUBJECTS.map(s=><option key={s}>{s}</option>)}
            </select>
          </div>
          <div className="ml-auto self-end">
            <span className="badge badge-lavender">{unis.length} universities</span>
          </div>
        </div>
      )}

      {/* Content */}
      {loading ? (
        <div className="py-20 flex flex-col items-center gap-3 text-muted">
          <div className="w-8 h-8 border-2 border-lavender/30 border-t-lavender rounded-full animate-spin"/>
          <span className="text-sm">Loading universities…</span>
        </div>
      ) : error ? (
        <div className="card p-8 text-center text-rose text-sm">{error}</div>
      ) : unis.length === 0 ? (
        <div className="card p-12 text-center text-muted">No universities found. Try changing your filters.</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {unis.map(uni => (
            <Link to={`/universities/${uni.id}`} key={uni.id}
              className="card-hover cursor-pointer overflow-hidden group block">
              <div className="h-32 bg-lavendLight overflow-hidden relative">
                {uni.image_url ? (
                  <img src={uni.image_url} alt={uni.name} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300" onError={e=>{e.target.style.display='none'}}/>
                ) : (
                  <div className="w-full h-full flex items-center justify-center"><GraduationCap className="w-12 h-12 text-lavender/30"/></div>
                )}
                {uni.match_score && (
                  <div className="absolute top-2 right-2 bg-lavender text-white text-xs font-bold px-2 py-1 rounded-lg shadow">
                    {Math.round(uni.match_score*100)}% match
                  </div>
                )}
                {(uni.qs_subject_ranking || uni.ranking) && (
                  <div className="absolute top-2 left-2 bg-white/90 text-amber-600 text-xs font-bold px-2 py-1 rounded-lg shadow flex items-center gap-1">
                    <Star className="w-3 h-3 fill-amber-400 text-amber-400"/> QS #{uni.qs_subject_ranking || uni.ranking}
                  </div>
                )}
              </div>
              <div className="p-4">
                <h3 className="font-bold text-text text-sm leading-snug mb-1 group-hover:text-lavender transition-colors">{uni.name}</h3>
                <div className="flex items-center gap-2 text-xs text-muted mb-2">
                  <MapPin className="w-3 h-3"/>{FLAG[uni.country]||'🌍'} {uni.country}
                  {uni.subject && <><span>·</span><span className="truncate">{uni.subject}</span></>}
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-teal-600 bg-mintLight px-2 py-0.5 rounded-full">{formatINR(uni.tuition)}</span>
                  <span className="text-lavender text-xs font-medium flex items-center gap-1">Details <ChevronRight className="w-3 h-3"/></span>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}

    </div>
  );
}
