import { useState, useEffect } from 'react';
import {
  ArrowRight, GraduationCap, FileCheck, Briefcase,
  Calculator, Globe, Trophy, BookOpen, CheckCircle2,
  TrendingUp, Home,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { authAPI } from '../api/auth';
import { universitiesAPI } from '../api/universities';
import { getCountryFlag } from '../utils/universityImages';

const CHECKLIST = [
  { id: 'profile',  label: 'Complete your profile',       href: '/profile'     },
  { id: 'unis',     label: 'Browse university matches',   href: '/universities' },
  { id: 'visa',     label: 'Review visa requirements',    href: '/visa-chat'   },
  { id: 'finance',  label: 'Run an ROI analysis',         href: '/finance'     },
  { id: 'decision', label: 'Build your shortlist',        href: '/decision'    },
  { id: 'housing',  label: 'Explore student housing',     href: '/housing'     },
];

export default function Dashboard() {
  const [profile, setProfile] = useState(null);
  const [topUnis, setTopUnis] = useState([]);
  const [uniError, setUniError] = useState(false);
  const [fromShortlist, setFromShortlist] = useState(false);
  const [done, setDone]       = useState(() => {
    try { return JSON.parse(localStorage.getItem('sp_checklist') || '{}'); }
    catch { return {}; }
  });

  useEffect(() => {
    authAPI.getProfile().then(setProfile).catch(() => {});

    // Prefer the user's Decision shortlist (localStorage) over generic API matches
    try {
      const raw = localStorage.getItem('decision_result');
      if (raw) {
        const { data, ts } = JSON.parse(raw);
        const AGE_MS = 60 * 60 * 1000; // 1 hour
        if (Date.now() - ts < AGE_MS && data?.top_universities?.length) {
          setTopUnis(data.top_universities.slice(0, 3));
          setFromShortlist(true);
          return;
        }
      }
    } catch { /* fall through to API */ }

    universitiesAPI.getRecommendations(6)
      .then(r => setTopUnis((r.recommendations || []).slice(0, 3)))
      .catch(() => setUniError(true));
  }, []);

  const toggleDone = (id) => {
    setDone(prev => {
      const next = { ...prev, [id]: !prev[id] };
      localStorage.setItem('sp_checklist', JSON.stringify(next));
      return next;
    });
  };

  const name       = profile?.full_name || profile?.email?.split('@')[0] || 'there';
  const cgpa       = profile?.cgpa;
  const ielts      = profile?.english_score;
  const countries  = (profile?.target_countries || []).join(', ') || null;
  const field      = profile?.field_of_study;
  const completedN = CHECKLIST.filter(c => done[c.id]).length;

  return (
    <div className="space-y-6 animate-fade-in">

      {/* ── Hero ── */}
      <div className="relative overflow-hidden rounded-xl p-7 text-white"
        style={{ background: 'linear-gradient(135deg, #1E40AF 0%, #2563EB 60%, #3B82F6 100%)' }}>
        {/* Subtle geometric accent */}
        <div className="absolute -top-10 -right-10 w-56 h-56 bg-white/5 rounded-full" />
        <div className="absolute -bottom-6 -left-6 w-40 h-40 bg-white/5 rounded-full" />
        <div className="relative z-10">
          <p className="text-blue-200 text-sm font-medium mb-1">Welcome back</p>
          <h1 className="text-2xl font-bold mb-1">Hi, {name} 👋</h1>
          <div className="flex flex-wrap gap-x-3 gap-y-1 text-sm text-blue-100">
            {cgpa       && <span>GPA {cgpa}</span>}
            {ielts      && <span>· IELTS {ielts}</span>}
            {field      && <span>· {field}</span>}
            {countries  && <span>· {countries}</span>}
          </div>
          <div className="flex gap-2.5 mt-5 flex-wrap">
            <Link to="/decision"
              className="inline-flex items-center gap-2 bg-white text-blue-700 px-4 py-2 rounded-lg font-semibold text-sm hover:bg-blue-50 transition-colors">
              <Trophy className="w-4 h-4" /> View My Shortlist
            </Link>
            <Link to="/universities"
              className="inline-flex items-center gap-2 bg-white/15 border border-white/25 px-4 py-2 rounded-lg font-medium text-sm hover:bg-white/20 transition-colors">
              <GraduationCap className="w-4 h-4" /> Browse Universities
            </Link>
          </div>
        </div>
      </div>

      {/* ── Stats ── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {[
          { icon: GraduationCap, label: 'Universities',  value: '2,900+', sub: 'across 21 countries',    color: 'bg-lavendLight text-lavender'  },
          { icon: Globe,          label: 'Countries',     value: '21',   sub: 'with visa guidance',     color: 'bg-blue-50 text-blue-600'      },
          { icon: Briefcase,      label: 'Job Listings',  value: 'Live', sub: 'updated daily',          color: 'bg-mintLight text-green-600'   },
          { icon: TrendingUp,     label: 'ROI Analysis',  value: 'Free', sub: 'salary + cost model',    color: 'bg-amberLight text-amber-600'  },
        ].map(({ icon: Icon, label, value, sub, color }) => (
          <div key={label} className="card p-4">
            <div className={`page-icon ${color} mb-3 w-8 h-8`}><Icon className="w-4 h-4" /></div>
            <p className="text-xl font-bold text-text">{value}</p>
            <p className="text-xs font-semibold text-textSoft">{label}</p>
            <p className="text-xs text-muted mt-0.5">{sub}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">

        {/* ── Top matches ── */}
        <div className="lg:col-span-2">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <h2 className="font-semibold text-text text-sm">
                {fromShortlist ? 'Your Shortlist' : 'Your Top Matches'}
              </h2>
              {fromShortlist && (
                <span className="text-[10px] bg-mintLight text-green-700 font-semibold px-2 py-0.5 rounded-full">
                  from AI analysis
                </span>
              )}
            </div>
            <Link
              to={fromShortlist ? '/decision' : '/universities'}
              className="text-xs text-lavender font-medium hover:underline flex items-center gap-1"
            >
              {fromShortlist ? 'View full shortlist' : 'See all'} <ArrowRight className="w-3 h-3" />
            </Link>
          </div>
          {topUnis.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {topUnis.map((uni, i) => {
                const flag = getCountryFlag(uni.country);
                const pct  = uni.match_score ? Math.round(uni.match_score * 100) : null;
                const rankColors = ['bg-amber-400', 'bg-slate-400', 'bg-orange-400'];
                const linkTo = fromShortlist ? '/decision' : `/universities/${uni.id}`;
                const scoreColor = pct >= 75 ? 'bg-teal-500' : pct >= 50 ? 'bg-lavender' : 'bg-amber-400';
                const reason = uni.top_reason || null;
                return (
                  <Link key={uni.name || uni.id} to={linkTo} className="group">
                    <div className="card-hover card overflow-hidden flex flex-col">
                      <div className="relative h-24 flex-shrink-0 overflow-hidden"
                        style={{ background: 'linear-gradient(135deg, #1E40AF 0%, #2563EB 60%, #3B82F6 100%)' }}>
                        <div className="absolute top-2 left-2 flex gap-1">
                          <span className={`badge ${rankColors[i]} text-white text-[9px]`}>#{i + 1}</span>
                          {uni.ranking && <span className="badge bg-white/80 text-lavender text-[9px]">QS {uni.ranking}</span>}
                        </div>
                        {pct && (
                          <div className="absolute top-2 right-2">
                            <div className={`w-9 h-9 rounded-full text-[10px] font-black flex flex-col items-center justify-center ${scoreColor} text-white border-2 border-white shadow`}>
                              <span className="leading-none">{pct}%</span>
                            </div>
                          </div>
                        )}
                        <div className="absolute bottom-0 inset-x-0 p-2">
                          <span className="text-white/90 text-[10px]">{flag} {uni.country}</span>
                        </div>
                      </div>
                      <div className="p-3 flex flex-col flex-1">
                        <p className="font-semibold text-text text-xs line-clamp-1 group-hover:text-lavender transition-colors mb-1">{uni.name}</p>
                        {reason && (
                          <p className="text-[10px] text-textSoft line-clamp-2 leading-relaxed">{reason}</p>
                        )}
                      </div>
                    </div>
                  </Link>
                );
              })}
            </div>
          ) : uniError ? (
            <div className="card p-8 text-center">
              <GraduationCap className="w-8 h-8 text-muted mx-auto mb-3 opacity-40" />
              <p className="font-semibold text-text text-sm">Couldn't load matches</p>
              <p className="text-xs text-muted mt-1 mb-4">Make sure the backend is running, then refresh the page</p>
              <button onClick={() => window.location.reload()} className="btn-primary text-xs">Retry</button>
            </div>
          ) : (
            <div className="card p-8 text-center">
              <GraduationCap className="w-8 h-8 text-muted mx-auto mb-3 opacity-40" />
              <p className="font-semibold text-text text-sm">No matches yet</p>
              <p className="text-xs text-muted mt-1 mb-4">Complete your profile to get personalised recommendations</p>
              <Link to="/profile" className="btn-primary text-xs">Complete Profile</Link>
            </div>
          )}
        </div>

        {/* ── Getting started checklist ── */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <h2 className="font-semibold text-text text-sm">Getting Started</h2>
            <span className="text-xs text-muted">{completedN}/{CHECKLIST.length}</span>
          </div>
          <div className="card p-4">
            <div className="h-1 bg-surfaceBorder rounded-full mb-4 overflow-hidden">
              <div className="h-full bg-lavender rounded-full transition-all duration-500"
                style={{ width: `${(completedN / CHECKLIST.length) * 100}%` }} />
            </div>
            <div className="space-y-0.5">
              {CHECKLIST.map(({ id, label, href }) => (
                <div key={id} className="flex items-center gap-2.5 px-2 py-2 rounded-md hover:bg-surfaceAlt transition-colors">
                  <button onClick={() => toggleDone(id)} className="shrink-0">
                    <CheckCircle2 className={`w-4 h-4 transition-colors ${done[id] ? 'text-green-500' : 'text-surfaceBorder'}`} />
                  </button>
                  <Link to={href}
                    className={`flex-1 text-xs transition-colors ${done[id] ? 'text-muted line-through' : 'text-textSoft hover:text-lavender'}`}>
                    {label}
                  </Link>
                </div>
              ))}
            </div>
          </div>
        </div>

      </div>

      {/* ── Quick access ── */}
      <div>
        <h2 className="font-semibold text-text text-sm mb-3">Quick Access</h2>
        <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
          {[
            { to: '/ai-coach',     icon: BookOpen,      label: 'Study Tools',        sub: 'Checklist · Timeline · SOP',       color: 'bg-lavendLight text-lavender'  },
            { to: '/visa-chat',    icon: FileCheck,     label: 'Visa Assistant',     sub: 'Requirements by country',          color: 'bg-amberLight text-amber-600'  },
            { to: '/jobs',         icon: Briefcase,     label: 'Jobs',               sub: 'Live listings worldwide',          color: 'bg-blue-50 text-blue-600'      },
            { to: '/finance',      icon: Calculator,    label: 'ROI Calculator',     sub: 'Cost vs. graduate salary',         color: 'bg-mintLight text-green-600'   },
            { to: '/decision',     icon: Trophy,        label: 'My Shortlist',       sub: 'Rankings · cost · visa',           color: 'bg-amberLight text-amber-600'  },
            { to: '/universities', icon: GraduationCap, label: 'Universities',       sub: '600+ with match scoring',          color: 'bg-lavendLight text-lavender'  },
          ].map(({ to, icon: Icon, label, sub, color }) => (
            <Link key={to} to={to}
              className="card p-4 flex items-center gap-3 hover:shadow-cardHov transition-all group">
              <div className={`page-icon ${color} w-8 h-8 flex-shrink-0`}><Icon className="w-4 h-4" /></div>
              <div className="min-w-0">
                <p className="font-semibold text-sm text-text group-hover:text-lavender transition-colors">{label}</p>
                <p className="text-xs text-muted truncate">{sub}</p>
              </div>
              <ArrowRight className="w-3.5 h-3.5 text-muted ml-auto group-hover:text-lavender transition-colors flex-shrink-0" />
            </Link>
          ))}
        </div>
      </div>

    </div>
  );
}
