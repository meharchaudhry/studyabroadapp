import { useState, useEffect } from 'react';
import {
  Sparkles, ArrowRight, GraduationCap, FileCheck, Briefcase,
  Calculator, Globe, Trophy, MapPin, BookOpen, CheckCircle2,
  TrendingUp, DollarSign,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { authAPI } from '../api/auth';
import { universitiesAPI } from '../api/universities';
import { getUniversityImage, getCountryFlag } from '../utils/universityImages';

// ── Checklist data ─────────────────────────────────────────────────────────────

const CHECKLIST = [
  { id: 'profile',    label: 'Complete your profile',      href: '/profile',     key: 'has_profile'   },
  { id: 'unis',       label: 'Explore university matches',  href: '/universities',key: null            },
  { id: 'visa',       label: 'Check visa requirements',     href: '/visa-chat',  key: null            },
  { id: 'finance',    label: 'Run financial ROI analysis',  href: '/finance',    key: null            },
  { id: 'decision',   label: 'Get AI Decision Dashboard',   href: '/decision',   key: null            },
  { id: 'housing',    label: 'Browse student housing',      href: '/housing',    key: null            },
];

export default function Dashboard() {
  const [profile, setProfile]   = useState(null);
  const [topUnis, setTopUnis]   = useState([]);
  const [done, setDone]         = useState(() => {
    try { return JSON.parse(localStorage.getItem('sp_checklist') || '{}'); }
    catch { return {}; }
  });

  useEffect(() => {
    authAPI.getProfile().then(setProfile).catch(() => {});
    universitiesAPI.getRecommendations(3)
      .then(r => setTopUnis((r.recommendations || []).slice(0, 3)))
      .catch(() => {});
  }, []);

  const toggleDone = (id) => {
    setDone(prev => {
      const next = { ...prev, [id]: !prev[id] };
      localStorage.setItem('sp_checklist', JSON.stringify(next));
      return next;
    });
  };

  const name        = profile?.full_name || profile?.email?.split('@')[0] || 'Student';
  const cgpa        = profile?.cgpa;
  const ielts       = profile?.english_score;
  const countries   = (profile?.target_countries || []).join(', ') || null;
  const field       = profile?.field_of_study;
  const completedN  = CHECKLIST.filter(c => done[c.id]).length;

  return (
    <div className="space-y-6 animate-fade-in">

      {/* ── Hero banner ── */}
      <div className="relative overflow-hidden rounded-2xl p-8 text-white"
        style={{ background: 'linear-gradient(135deg,#4C3BCF 0%,#7C6FF7 55%,#9B8FF7 100%)' }}>
        <div className="absolute -top-16 -right-16 w-64 h-64 bg-white/10 rounded-full blur-3xl" />
        <div className="absolute -bottom-8 -left-8 w-48 h-48 bg-white/10 rounded-full blur-3xl" />
        <div className="relative z-10">
          <div className="flex items-center gap-2 mb-3">
            <div className="w-8 h-8 bg-white/20 rounded-lg flex items-center justify-center backdrop-blur-sm">
              <Sparkles className="w-4 h-4 text-white" />
            </div>
            <span className="text-white/70 text-sm font-medium">AI Study Abroad Platform</span>
          </div>
          <h1 className="text-3xl font-black mb-1">Welcome back, {name}! 👋</h1>
          <div className="flex flex-wrap gap-3 mt-1 text-sm text-white/70">
            {cgpa && <span>CGPA {cgpa}</span>}
            {ielts && <span>· IELTS {ielts}</span>}
            {field && <span>· {field}</span>}
            {countries && <span>· Targeting {countries}</span>}
          </div>
          <div className="flex gap-3 mt-5 flex-wrap">
            <Link to="/decision"
              className="inline-flex items-center gap-2 bg-white text-lavender px-4 py-2.5 rounded-xl font-bold text-sm hover:bg-lavendLight transition-colors shadow-md">
              <Trophy className="w-4 h-4" /> Run AI Decision
            </Link>
            <Link to="/universities"
              className="inline-flex items-center gap-2 bg-white/15 backdrop-blur-sm border border-white/25 px-4 py-2.5 rounded-xl font-semibold text-sm hover:bg-white/20 transition-colors">
              <GraduationCap className="w-4 h-4" /> View My Matches
            </Link>
          </div>
        </div>
      </div>

      {/* ── Stats row ── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { icon: GraduationCap, label: 'Universities',  value: '600+', sub: 'in database',           color: 'bg-lavendLight text-lavender'  },
          { icon: Globe,          label: 'Countries',     value: '21',   sub: 'with visa AI guidance', color: 'bg-skyLight text-blue-600'     },
          { icon: Briefcase,      label: 'Jobs',          value: 'Live', sub: '4 live sources',        color: 'bg-mintLight text-teal-600'    },
          { icon: Sparkles,       label: 'AI Features',   value: '5',    sub: 'Claude-powered tools',  color: 'bg-amberLight text-amber-600'  },
        ].map(({ icon: Icon, label, value, sub, color }) => (
          <div key={label} className="card p-5">
            <div className={`page-icon ${color} mb-3`}><Icon className="w-4 h-4" /></div>
            <p className="text-2xl font-black text-text">{value}</p>
            <p className="text-xs font-semibold text-textSoft">{label}</p>
            <p className="text-xs text-muted mt-0.5">{sub}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

        {/* ── Top matches ── */}
        <div className="lg:col-span-2">
          <div className="flex items-center justify-between mb-3">
            <h2 className="font-bold text-text flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-lavender" /> Your Top Matches
            </h2>
            <Link to="/universities" className="text-sm text-lavender font-semibold hover:underline flex items-center gap-1">
              See all <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
          {topUnis.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {topUnis.map((uni, i) => {
                const img  = getUniversityImage(uni);
                const flag = getCountryFlag(uni.country);
                const pct  = uni.match_score ? Math.round(uni.match_score * 100) : null;
                const rankColors = ['bg-amber-400', 'bg-slate-400', 'bg-orange-400'];
                return (
                  <Link key={uni.id} to={`/universities/${uni.id}`} className="group">
                    <div className="card-hover card overflow-hidden">
                      <div className="relative h-32 overflow-hidden bg-surfaceAlt">
                        <img src={img} alt={uni.name}
                          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                          onError={e => e.target.style.display = 'none'} />
                        <div className="absolute top-2 left-2">
                          <span className={`badge ${rankColors[i]} text-white`}>#{i + 1}</span>
                        </div>
                        {pct && (
                          <div className="absolute top-2 right-2">
                            <div className={`w-9 h-9 rounded-full text-[10px] font-black flex items-center justify-center border-2 border-white shadow
                              ${pct >= 75 ? 'bg-teal-500 text-white' : 'bg-lavender text-white'}`}>{pct}%</div>
                          </div>
                        )}
                        <div className="absolute bottom-0 inset-x-0 bg-gradient-to-t from-black/60 to-transparent p-2 pt-6">
                          <span className="text-white/90 text-xs">{flag} {uni.country}</span>
                        </div>
                      </div>
                      <div className="p-3">
                        <h3 className="font-bold text-text text-xs line-clamp-2 group-hover:text-lavender transition-colors">{uni.name}</h3>
                        <div className="flex gap-3 mt-1.5">
                          {uni.tuition && <span className="text-[10px] text-muted">${(uni.tuition / 1000).toFixed(0)}k/yr</span>}
                          {uni.grad_salary_usd && (
                            <span className="text-[10px] text-teal-600 font-semibold">
                              Grad: ${(uni.grad_salary_usd / 1000).toFixed(0)}k
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  </Link>
                );
              })}
            </div>
          ) : (
            <div className="card p-8 text-center">
              <GraduationCap className="w-10 h-10 text-muted mx-auto mb-3 opacity-30" />
              <p className="font-semibold text-text">No matches yet</p>
              <p className="text-sm text-muted mt-1 mb-4">Complete your profile to get AI recommendations</p>
              <Link to="/profile" className="btn-primary text-sm">Complete Profile</Link>
            </div>
          )}
        </div>

        {/* ── Checklist ── */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <h2 className="font-bold text-text">Getting Started</h2>
            <span className="text-xs text-muted">{completedN}/{CHECKLIST.length} done</span>
          </div>
          <div className="card p-4 space-y-1">
            {/* Progress bar */}
            <div className="h-1.5 bg-surfaceBorder rounded-full mb-4 overflow-hidden">
              <div className="h-full bg-lavender rounded-full transition-all duration-500"
                style={{ width: `${(completedN / CHECKLIST.length) * 100}%` }} />
            </div>
            {CHECKLIST.map(({ id, label, href }) => (
              <div key={id} className="flex items-center gap-3 p-2 rounded-lg hover:bg-surfaceAlt transition-colors">
                <button onClick={() => toggleDone(id)} className="shrink-0">
                  <CheckCircle2 className={`w-5 h-5 transition-colors ${done[id] ? 'text-teal-500' : 'text-surfaceBorder'}`} />
                </button>
                <Link to={href} className={`flex-1 text-sm transition-colors ${done[id] ? 'text-muted line-through' : 'text-textSoft hover:text-lavender'}`}>
                  {label}
                </Link>
              </div>
            ))}
          </div>
        </div>

      </div>

      {/* ── Quick Actions ── */}
      <div>
        <h2 className="font-bold text-text mb-3">Quick Access</h2>
        <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
          {[
            { to: '/ai-coach',     icon: Sparkles,      label: 'AI Study Coach',       sub: 'Claude · Checklist · Timeline', color: 'bg-lavendLight text-lavender'  },
            { to: '/visa-chat',    icon: FileCheck,     label: 'Visa AI Assistant',    sub: 'RAG-powered, 96% accuracy',   color: 'bg-amberLight text-amber-600'  },
            { to: '/jobs',         icon: Briefcase,     label: 'Browse Jobs',          sub: '4 live sources, global',      color: 'bg-skyLight text-blue-600'     },
            { to: '/finance',      icon: Calculator,    label: 'ROI Calculator',       sub: 'Real salary + risk scoring',  color: 'bg-mintLight text-teal-600'    },
            { to: '/decision',     icon: Trophy,        label: 'Decision Dashboard',   sub: '5-agent AI ranking',          color: 'bg-peachLight text-peach'      },
            { to: '/universities', icon: GraduationCap, label: 'All Universities',     sub: '600+ with AI matching',       color: 'bg-roseLight text-rose'        },
          ].map(({ to, icon: Icon, label, sub, color }) => (
            <Link key={to} to={to}
              className="card p-4 flex items-center gap-3 hover:shadow-cardHov transition-all group">
              <div className={`page-icon ${color} flex-shrink-0`}><Icon className="w-4 h-4" /></div>
              <div className="min-w-0">
                <p className="font-semibold text-sm text-text group-hover:text-lavender transition-colors">{label}</p>
                <p className="text-xs text-muted truncate">{sub}</p>
              </div>
              <ArrowRight className="w-4 h-4 text-muted ml-auto group-hover:text-lavender transition-colors flex-shrink-0" />
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
