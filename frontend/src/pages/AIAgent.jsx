import { useState, useEffect, useRef } from 'react';
import {
  Bot, Send, User, Sparkles, FileCheck, BarChart3, Clock,
  BookOpen, CheckCircle2, Circle, ChevronDown, ChevronRight,
  Zap, Target, TrendingUp, AlertCircle, Trophy, RefreshCw,
  Download, Plus, ArrowRight, Loader2,
} from 'lucide-react';
import { aiAPI } from '../api/ai';
import { authAPI } from '../api/auth';

// ── Tabs ─────────────────────────────────────────────────────────────────────
const TABS = [
  { id: 'chat',      label: 'AI Coach',         icon: Bot       },
  { id: 'checklist', label: 'Doc Checklist',    icon: FileCheck  },
  { id: 'timeline',  label: 'Timeline',         icon: Clock     },
  { id: 'profile',   label: 'Profile Analysis', icon: BarChart3  },
  { id: 'sop',       label: 'SOP Builder',      icon: BookOpen  },
];

const COUNTRIES = [
  'UK','USA','Canada','Australia','Germany','Netherlands',
  'Ireland','Singapore','Japan','France',
];

const INTAKES = ['Fall (Sep)', 'Spring (Jan)', 'Winter (Jan/Feb)', 'Summer (May)'];

const PRIORITY_STYLES = {
  critical: 'bg-rose/10 text-rose border-rose/30',
  high:     'bg-amberLight text-amber-700 border-amber/30',
  medium:   'bg-skyLight text-blue-600 border-blue-200',
};

const CATEGORY_COLORS = {
  Identity:       'bg-lavendLight text-lavender',
  Admission:      'bg-skyLight text-blue-600',
  Financial:      'bg-amberLight text-amber-700',
  'Health & Other': 'bg-mintLight text-teal-600',
  'Interview Prep': 'bg-peachLight text-orange-600',
  Health:         'bg-mintLight text-teal-600',
};

// ── Markdown-lite renderer ───────────────────────────────────────────────────
function renderMd(text) {
  if (!text) return null;
  return text.split('\n').map((line, i) => {
    const parts = line.split(/(\*\*[^*]+\*\*)/g).map((p, j) =>
      p.startsWith('**') && p.endsWith('**')
        ? <strong key={j}>{p.slice(2, -2)}</strong>
        : p
    );
    if (line.trimStart().startsWith('- ') || line.trimStart().startsWith('• '))
      return <li key={i} className="ml-4 list-disc">{parts}</li>;
    if (line.match(/^\d+\.\s/))
      return <li key={i} className="ml-4 list-decimal">{parts}</li>;
    if (line.startsWith('###')) return <h4 key={i} className="font-bold text-text mt-2">{line.slice(3).trim()}</h4>;
    if (line.startsWith('##'))  return <h3 key={i} className="font-bold text-text mt-3">{line.slice(2).trim()}</h3>;
    if (line.startsWith('#'))   return <h2 key={i} className="font-bold text-text mt-3 text-base">{line.slice(1).trim()}</h2>;
    if (line.trim() === '') return <br key={i} />;
    return <p key={i}>{parts}</p>;
  });
}

// ── Suggested chat prompts ────────────────────────────────────────────────────
const SUGGESTIONS = [
  'What IELTS score do I need for UK universities?',
  'How do I get a GIC for Canada?',
  'What is the Germany blocked account requirement?',
  'How early should I start my visa application?',
  'What scholarships are available for Indian students?',
  'How do I write a strong SOP?',
];

// ═════════════════════════════════════════════════════════════════════════════
export default function AIAgent() {
  const [tab, setTab]         = useState('chat');
  const [profile, setProfile] = useState({});

  useEffect(() => {
    authAPI.getProfile().then(setProfile).catch(() => {});
  }, []);

  return (
    <div className="space-y-5 animate-fade-in">
      {/* Header */}
      <div className="page-header">
        <div className="page-icon bg-lavendLight text-lavender">
          <Sparkles className="w-5 h-5" />
        </div>
        <div>
          <h1 className="text-2xl font-black text-text">AI Study Coach</h1>
          <p className="text-muted text-sm">
            Claude-powered · Document checklists · Timeline planning · Profile analysis
          </p>
        </div>
      </div>

      {/* Tab bar */}
      <div className="flex gap-1 bg-surfaceAlt rounded-2xl p-1 flex-wrap">
        {TABS.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold transition-all flex-1 justify-center
              ${tab === t.id
                ? 'bg-white text-lavender shadow-soft'
                : 'text-textSoft hover:text-text'}`}>
            <t.icon className="w-4 h-4" /> {t.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {tab === 'chat'      && <ChatTab profile={profile} />}
      {tab === 'checklist' && <ChecklistTab profile={profile} />}
      {tab === 'timeline'  && <TimelineTab profile={profile} />}
      {tab === 'profile'   && <ProfileTab profile={profile} />}
      {tab === 'sop'       && <SopTab profile={profile} />}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════
// Chat Tab
// ═══════════════════════════════════════════════════════════
function ChatTab({ profile }) {
  const [messages, setMessages] = useState([{
    role: 'assistant',
    content: "Hi! I'm your AI Study Coach powered by Claude. I know everything about studying abroad as an Indian student — visas, universities, scholarships, IELTS/GRE prep, budgeting, and more.\n\nWhat would you like help with today?",
  }]);
  const [input, setInput]     = useState('');
  const [loading, setLoading] = useState(false);
  const bottomRef             = useRef(null);
  const inputRef              = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const send = async (text = input.trim()) => {
    if (!text || loading) return;
    setInput('');
    const userMsg = { role: 'user', content: text };
    setMessages(prev => [...prev, userMsg]);
    setLoading(true);
    try {
      const history = messages.map(m => ({ role: m.role, content: m.content }));
      const data = await aiAPI.chat(text, profile, history);
      setMessages(prev => [...prev, { role: 'assistant', content: data.reply }]);
    } catch {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Sorry, the AI service is temporarily unavailable.',
      }]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  return (
    <div className="card flex flex-col" style={{ height: '620px' }}>
      {/* Chat header */}
      <div className="p-4 border-b border-surfaceBorder flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 bg-gradient-to-br from-lavender to-blue-500 rounded-xl flex items-center justify-center shadow-sm">
            <Bot className="w-4 h-4 text-white" />
          </div>
          <div>
            <p className="text-sm font-bold text-text">AI Study Coach</p>
            <p className="text-[10px] text-muted">Claude · Personalised for your profile</p>
          </div>
        </div>
        <button onClick={() => setMessages([{
          role: 'assistant',
          content: "Hi again! What would you like help with?",
        }])} className="p-1.5 rounded-lg text-muted hover:text-lavender hover:bg-surfaceAlt transition-colors" title="New chat">
          <RefreshCw className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg, i) => (
          <div key={i} className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : ''}`}>
            {msg.role === 'assistant' && (
              <div className="w-7 h-7 bg-lavendLight rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                <Bot className="w-3.5 h-3.5 text-lavender" />
              </div>
            )}
            <div className={`max-w-[82%] rounded-2xl px-4 py-3 text-sm leading-relaxed space-y-1
              ${msg.role === 'user'
                ? 'bg-lavender text-white rounded-tr-sm'
                : 'bg-surfaceAlt text-text rounded-tl-sm'}`}>
              {renderMd(msg.content)}
            </div>
            {msg.role === 'user' && (
              <div className="w-7 h-7 bg-lavender rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                <User className="w-3.5 h-3.5 text-white" />
              </div>
            )}
          </div>
        ))}
        {loading && (
          <div className="flex gap-3">
            <div className="w-7 h-7 bg-lavendLight rounded-full flex items-center justify-center">
              <Bot className="w-3.5 h-3.5 text-lavender" />
            </div>
            <div className="bg-surfaceAlt rounded-2xl rounded-tl-sm px-4 py-3">
              <div className="flex gap-1">
                {[0, 0.15, 0.3].map((d, i) => (
                  <div key={i} className="w-1.5 h-1.5 bg-lavender rounded-full animate-bounce"
                    style={{ animationDelay: `${d}s` }} />
                ))}
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Suggestions */}
      {messages.length <= 1 && (
        <div className="px-4 pb-2 flex gap-2 flex-wrap">
          {SUGGESTIONS.map((q, i) => (
            <button key={i} onClick={() => send(q)}
              className="text-[11px] bg-lavendLight text-lavender px-2.5 py-1.5 rounded-lg hover:bg-lavender hover:text-white transition-colors border border-lavender/20 flex items-center gap-1">
              <Sparkles className="w-2.5 h-2.5" /> {q}
            </button>
          ))}
        </div>
      )}

      {/* Input */}
      <div className="p-3 border-t border-surfaceBorder flex gap-2">
        <input ref={inputRef} value={input} onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && !e.shiftKey && send()}
          placeholder="Ask anything about studying abroad…"
          className="input-field py-2 text-sm flex-1" />
        <button onClick={() => send()} disabled={loading || !input.trim()}
          className="btn-primary px-3 py-2 disabled:opacity-50">
          <Send className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════
// Checklist Tab
// ═══════════════════════════════════════════════════════════
function ChecklistTab({ profile }) {
  const [country, setCountry]         = useState('UK');
  const [result, setResult]           = useState(null);
  const [loading, setLoading]         = useState(false);
  const [checked, setChecked]         = useState({});
  const [expandedCats, setExpandedCats] = useState({});

  const generate = async () => {
    setLoading(true);
    setResult(null);
    setChecked({});
    try {
      const data = await aiAPI.generateChecklist(country, profile);
      setResult(data);
      // Auto-expand first category
      const firstCat = [...new Set((data.checklist || []).map(i => i.category))][0];
      if (firstCat) setExpandedCats({ [firstCat]: true });
    } catch {
      setResult({ error: true });
    } finally {
      setLoading(false);
    }
  };

  const toggleCheck = id => setChecked(p => ({ ...p, [id]: !p[id] }));
  const toggleCat   = cat => setExpandedCats(p => ({ ...p, [cat]: !p[cat] }));

  const grouped = (result?.checklist || []).reduce((acc, item) => {
    (acc[item.category] = acc[item.category] || []).push(item);
    return acc;
  }, {});

  const total     = result?.checklist?.length || 0;
  const doneCount = Object.values(checked).filter(Boolean).length;
  const progress  = total ? Math.round((doneCount / total) * 100) : 0;

  // Copy all tasks to a simple text list for "add to todo" feel
  const copyToClipboard = () => {
    const text = (result?.checklist || [])
      .map(i => `[ ] ${i.category}: ${i.task}`)
      .join('\n');
    navigator.clipboard.writeText(text).catch(() => {});
  };

  return (
    <div className="space-y-4">
      {/* Controls */}
      <div className="card p-4 flex flex-wrap gap-3 items-center">
        <div className="flex flex-wrap gap-2 flex-1">
          {COUNTRIES.map(c => (
            <button key={c} onClick={() => setCountry(c)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all
                ${country === c
                  ? 'bg-lavender text-white border-lavender'
                  : 'bg-white text-textSoft border-surfaceBorder hover:border-lavender/50'}`}>
              {c}
            </button>
          ))}
        </div>
        <button onClick={generate} disabled={loading}
          className="btn-primary px-5 py-2.5 gap-2 disabled:opacity-60 flex-shrink-0">
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Zap className="w-4 h-4" />}
          {loading ? 'Generating…' : 'Generate with AI'}
        </button>
      </div>

      {/* Empty state */}
      {!result && !loading && (
        <div className="card p-16 text-center">
          <div className="w-14 h-14 bg-lavendLight rounded-2xl flex items-center justify-center mx-auto mb-4">
            <FileCheck className="w-7 h-7 text-lavender" />
          </div>
          <p className="font-bold text-text text-lg mb-1">AI-Powered Document Checklist</p>
          <p className="text-sm text-muted max-w-sm mx-auto">
            Select a country and click "Generate with AI" to get a personalised,
            prioritised checklist tailored to your profile.
          </p>
        </div>
      )}

      {/* Error */}
      {result?.error && (
        <div className="card p-8 text-center">
          <AlertCircle className="w-8 h-8 text-rose mx-auto mb-2" />
          <p className="font-semibold text-text">Could not generate checklist</p>
          <p className="text-sm text-muted mt-1">Please check your API configuration and try again.</p>
        </div>
      )}

      {/* Results */}
      {result && !result.error && (
        <>
          {/* Overview card */}
          <div className="card p-5">
            <div className="flex items-start justify-between gap-4 flex-wrap">
              <div>
                <h2 className="font-bold text-text text-lg">{result.country} — Document Checklist</h2>
                <p className="text-sm text-muted mt-1 max-w-lg">{result.summary}</p>
              </div>
              <div className="flex gap-2">
                <button onClick={copyToClipboard}
                  className="btn-ghost text-xs py-1.5 px-3">
                  <Download className="w-3.5 h-3.5" /> Copy All
                </button>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-3 mt-4 text-xs">
              {result.visa_fee_usd > 0 && (
                <div className="bg-surfaceAlt rounded-lg p-2.5">
                  <p className="text-muted mb-0.5">Visa Fee</p>
                  <p className="font-bold text-text">${result.visa_fee_usd} USD</p>
                </div>
              )}
              {result.timeline_weeks > 0 && (
                <div className="bg-surfaceAlt rounded-lg p-2.5">
                  <p className="text-muted mb-0.5">Lead Time</p>
                  <p className="font-bold text-text">{result.timeline_weeks} weeks</p>
                </div>
              )}
              <div className="bg-surfaceAlt rounded-lg p-2.5">
                <p className="text-muted mb-0.5">Documents</p>
                <p className="font-bold text-text">{total} total</p>
              </div>
            </div>

            {/* Progress bar */}
            <div className="mt-4">
              <div className="flex justify-between text-xs mb-1.5">
                <span className="text-textSoft font-medium">Documents ready</span>
                <span className="font-bold text-lavender">{doneCount}/{total}</span>
              </div>
              <div className="bg-lavendLight rounded-full h-2 overflow-hidden">
                <div className="bg-lavender h-2 rounded-full transition-all duration-500"
                  style={{ width: `${progress}%` }} />
              </div>
              {progress === 100 && (
                <p className="text-xs text-teal-600 font-semibold mt-1.5">🎉 All documents ready!</p>
              )}
            </div>
          </div>

          {/* Checklist groups */}
          {Object.entries(grouped).map(([cat, items]) => (
            <div key={cat} className="card overflow-hidden">
              <button onClick={() => toggleCat(cat)}
                className="w-full flex items-center justify-between p-4 hover:bg-surfaceAlt transition-colors">
                <div className="flex items-center gap-2.5">
                  <span className={`badge text-[10px] ${CATEGORY_COLORS[cat] || 'bg-surfaceAlt text-textSoft'}`}>{cat}</span>
                  <span className="text-xs text-muted">
                    {items.filter(i => checked[i.id]).length}/{items.length} done
                  </span>
                </div>
                <ChevronDown className={`w-4 h-4 text-muted transition-transform ${expandedCats[cat] ? 'rotate-180' : ''}`} />
              </button>

              {expandedCats[cat] && (
                <div className="px-4 pb-4 space-y-2 border-t border-surfaceBorder pt-3">
                  {items.map(item => (
                    <div key={item.id}
                      className="flex items-start gap-3 p-3 rounded-xl hover:bg-surfaceAlt cursor-pointer transition-colors group"
                      onClick={() => toggleCheck(item.id)}>
                      {checked[item.id]
                        ? <CheckCircle2 className="w-4 h-4 text-teal-500 flex-shrink-0 mt-0.5" />
                        : <Circle className="w-4 h-4 text-muted flex-shrink-0 mt-0.5 group-hover:text-lavender" />}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className={`text-sm leading-snug ${checked[item.id] ? 'line-through text-muted' : 'text-text font-medium'}`}>
                            {item.task}
                          </span>
                          <span className={`badge text-[9px] border ${PRIORITY_STYLES[item.priority] || ''}`}>
                            {item.priority}
                          </span>
                        </div>
                        {item.note && (
                          <p className="text-xs text-muted mt-0.5">{item.note}</p>
                        )}
                        {item.deadline && (
                          <p className="text-[10px] text-blue-500 mt-0.5 flex items-center gap-1">
                            <Clock className="w-3 h-3" /> {item.deadline}
                          </p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </>
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════
// Timeline Tab
// ═══════════════════════════════════════════════════════════
function TimelineTab({ profile }) {
  const [intake, setIntake]     = useState('Fall (Sep)');
  const [countries, setCountries] = useState(profile?.target_countries || []);
  const [result, setResult]     = useState(null);
  const [loading, setLoading]   = useState(false);

  useEffect(() => {
    if (profile?.target_countries?.length) setCountries(profile.target_countries);
  }, [profile]);

  const generate = async () => {
    setLoading(true);
    try {
      const data = await aiAPI.generateTimeline(intake, countries, profile);
      setResult(data);
    } catch {
      setResult({ error: true });
    } finally {
      setLoading(false);
    }
  };

  const toggleCountry = c => setCountries(prev =>
    prev.includes(c) ? prev.filter(x => x !== c) : [...prev, c]
  );

  return (
    <div className="space-y-4">
      {/* Controls */}
      <div className="card p-5 space-y-4">
        <div>
          <p className="text-xs font-bold text-muted uppercase tracking-wide mb-2">Intake</p>
          <div className="flex gap-2 flex-wrap">
            {INTAKES.map(i => (
              <button key={i} onClick={() => setIntake(i)}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all
                  ${intake === i ? 'bg-lavender text-white border-lavender' : 'bg-white text-textSoft border-surfaceBorder hover:border-lavender/50'}`}>
                {i}
              </button>
            ))}
          </div>
        </div>
        <div>
          <p className="text-xs font-bold text-muted uppercase tracking-wide mb-2">Target Countries</p>
          <div className="flex gap-2 flex-wrap">
            {COUNTRIES.map(c => (
              <button key={c} onClick={() => toggleCountry(c)}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all
                  ${countries.includes(c) ? 'bg-blue-500 text-white border-blue-500' : 'bg-white text-textSoft border-surfaceBorder hover:border-blue-300'}`}>
                {c}
              </button>
            ))}
          </div>
        </div>
        <button onClick={generate} disabled={loading}
          className="btn-primary px-5 py-2.5 gap-2 w-full justify-center disabled:opacity-60">
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Clock className="w-4 h-4" />}
          {loading ? 'Generating timeline…' : 'Generate My Timeline'}
        </button>
      </div>

      {/* Empty state */}
      {!result && !loading && (
        <div className="card p-16 text-center">
          <Clock className="w-12 h-12 text-muted mx-auto mb-4 opacity-30" />
          <p className="font-bold text-text">Month-by-Month Application Plan</p>
          <p className="text-sm text-muted mt-1">Select your intake and target countries, then generate your personalised timeline.</p>
        </div>
      )}

      {/* Timeline results */}
      {result && !result.error && (
        <div className="space-y-3">
          <h2 className="font-bold text-text text-lg px-1">
            {result.intake} Intake — Application Roadmap
          </h2>
          <div className="relative">
            {/* Vertical line */}
            <div className="absolute left-5 top-5 bottom-5 w-0.5 bg-surfaceBorder rounded-full" />
            <div className="space-y-4">
              {(result.months || []).map((month, i) => (
                <div key={i} className="relative flex gap-4">
                  {/* Dot */}
                  <div className={`w-10 h-10 rounded-full flex-shrink-0 flex items-center justify-center z-10 border-2
                    ${month.milestone
                      ? 'bg-lavender border-lavender text-white shadow-sm'
                      : 'bg-white border-surfaceBorder text-muted'}`}>
                    {month.milestone ? <Trophy className="w-4 h-4" /> : <span className="text-xs font-bold">{i + 1}</span>}
                  </div>
                  <div className={`flex-1 card p-4 ${month.milestone ? 'border-lavender/30 bg-lavendLight/20' : ''}`}>
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-xs font-bold text-lavender uppercase tracking-wide">{month.month}</span>
                      <span className="font-bold text-text text-sm">{month.label}</span>
                      {month.milestone && (
                        <span className="badge badge-lavender text-[9px] ml-auto">Milestone</span>
                      )}
                    </div>
                    <ul className="space-y-1">
                      {(month.tasks || []).map((task, j) => (
                        <li key={j} className="flex items-start gap-2 text-sm text-textSoft">
                          <ArrowRight className="w-3 h-3 mt-1 text-lavender flex-shrink-0" />
                          {task}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════
// Profile Analysis Tab
// ═══════════════════════════════════════════════════════════
function ProfileTab({ profile }) {
  const [result, setResult]   = useState(null);
  const [loading, setLoading] = useState(false);

  const analyze = async () => {
    setLoading(true);
    try {
      const data = await aiAPI.analyzeProfile(profile);
      setResult(data);
    } catch {
      setResult({ error: true });
    } finally {
      setLoading(false);
    }
  };

  const scoreColor = (s) => {
    if (s >= 75) return 'text-teal-600';
    if (s >= 50) return 'text-amber-600';
    return 'text-rose';
  };

  const impactColor = { high: 'text-rose', medium: 'text-amber-600', low: 'text-teal-600' };

  return (
    <div className="space-y-4">
      <div className="card p-5 text-center space-y-3">
        <div className="w-14 h-14 bg-lavendLight rounded-2xl flex items-center justify-center mx-auto">
          <BarChart3 className="w-7 h-7 text-lavender" />
        </div>
        <div>
          <h2 className="font-bold text-text">AI Profile Analysis</h2>
          <p className="text-sm text-muted mt-1">
            Get an honest, data-driven assessment of your study abroad readiness — strengths, gaps, and a personalised action plan.
          </p>
        </div>
        <button onClick={analyze} disabled={loading}
          className="btn-primary px-6 py-2.5 gap-2 mx-auto disabled:opacity-60">
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Target className="w-4 h-4" />}
          {loading ? 'Analysing…' : 'Analyse My Profile'}
        </button>
      </div>

      {result?.error && (
        <div className="card p-8 text-center">
          <AlertCircle className="w-8 h-8 text-rose mx-auto mb-2" />
          <p className="font-semibold">Analysis failed — check API configuration.</p>
        </div>
      )}

      {result && !result.error && (
        <div className="space-y-4">
          {/* Score */}
          <div className="card p-6 text-center">
            <p className="text-sm font-semibold text-muted mb-2">Profile Strength Score</p>
            <div className={`text-6xl font-black ${scoreColor(result.overall_score)}`}>
              {result.overall_score}
              <span className="text-2xl text-muted font-normal">/100</span>
            </div>
            <div className="w-full bg-surfaceBorder rounded-full h-3 mt-4 overflow-hidden">
              <div
                className={`h-3 rounded-full transition-all duration-700 ${
                  result.overall_score >= 75 ? 'bg-teal-500' :
                  result.overall_score >= 50 ? 'bg-amber-400' : 'bg-rose'}`}
                style={{ width: `${result.overall_score}%` }} />
            </div>
            {result.verdict && (
              <p className="text-sm text-textSoft mt-4 max-w-lg mx-auto leading-relaxed">{result.verdict}</p>
            )}
          </div>

          <div className="grid md:grid-cols-2 gap-4">
            {/* Strengths */}
            <div className="card p-4">
              <h3 className="font-bold text-text mb-3 flex items-center gap-2">
                <Trophy className="w-4 h-4 text-teal-500" /> Strengths
              </h3>
              <ul className="space-y-2">
                {(result.strengths || []).map((s, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-textSoft">
                    <CheckCircle2 className="w-4 h-4 text-teal-500 flex-shrink-0 mt-0.5" /> {s}
                  </li>
                ))}
              </ul>
            </div>

            {/* Gaps */}
            <div className="card p-4">
              <h3 className="font-bold text-text mb-3 flex items-center gap-2">
                <AlertCircle className="w-4 h-4 text-rose" /> Gaps to Address
              </h3>
              <ul className="space-y-2">
                {(result.gaps || []).filter(Boolean).map((g, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-textSoft">
                    <AlertCircle className="w-4 h-4 text-rose flex-shrink-0 mt-0.5" /> {g}
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Actions */}
          {result.actions?.length > 0 && (
            <div className="card p-4">
              <h3 className="font-bold text-text mb-3 flex items-center gap-2">
                <Zap className="w-4 h-4 text-amber-500" /> Prioritised Action Plan
              </h3>
              <div className="space-y-2">
                {result.actions.map((a, i) => (
                  <div key={i} className="flex items-start gap-3 p-3 bg-surfaceAlt rounded-xl">
                    <span className="text-xs font-bold text-muted mt-0.5 w-5">{i + 1}.</span>
                    <div className="flex-1">
                      <p className="text-sm font-semibold text-text">{a.action}</p>
                      {a.deadline && <p className="text-xs text-muted mt-0.5">By: {a.deadline}</p>}
                    </div>
                    <div className="flex gap-1.5 flex-shrink-0">
                      <span className={`badge text-[9px] ${impactColor[a.impact] || ''}`}>
                        {a.impact} impact
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Country fit */}
          {result.match_countries?.length > 0 && (
            <div className="card p-4">
              <h3 className="font-bold text-text mb-3 flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-lavender" /> Country Fit Scores
              </h3>
              <div className="space-y-3">
                {result.match_countries.map((c, i) => (
                  <div key={i}>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="font-semibold text-text">{c.country}</span>
                      <span className={`font-bold ${scoreColor(c.fit)}`}>{c.fit}%</span>
                    </div>
                    <div className="bg-surfaceBorder rounded-full h-2 overflow-hidden">
                      <div className={`h-2 rounded-full transition-all duration-500
                        ${c.fit >= 75 ? 'bg-teal-500' : c.fit >= 50 ? 'bg-lavender' : 'bg-amber-400'}`}
                        style={{ width: `${c.fit}%` }} />
                    </div>
                    {c.reason && <p className="text-xs text-muted mt-1">{c.reason}</p>}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════
// SOP Builder Tab
// ═══════════════════════════════════════════════════════════
function SopTab({ profile }) {
  const [university, setUniversity] = useState('');
  const [program, setProgram]       = useState('');
  const [result, setResult]         = useState('');
  const [loading, setLoading]       = useState(false);

  const generate = async () => {
    if (!university.trim() || !program.trim()) return;
    setLoading(true);
    try {
      const data = await aiAPI.generateSop(profile, university, program);
      setResult(data.outline || '');
    } catch {
      setResult('SOP generation failed. Please check your API configuration.');
    } finally {
      setLoading(false);
    }
  };

  const copy = () => navigator.clipboard.writeText(result).catch(() => {});

  return (
    <div className="space-y-4">
      <div className="card p-5 space-y-4">
        <div className="flex items-center gap-2 mb-1">
          <BookOpen className="w-4 h-4 text-lavender" />
          <h2 className="font-bold text-text">Statement of Purpose Builder</h2>
        </div>
        <p className="text-sm text-muted">
          Generate a personalised SOP outline based on your profile, tailored to a specific university and program.
        </p>
        <div className="grid sm:grid-cols-2 gap-3">
          <div>
            <label className="text-xs font-semibold text-muted block mb-1">University</label>
            <input value={university} onChange={e => setUniversity(e.target.value)}
              placeholder="e.g. University of Toronto"
              className="input-field" />
          </div>
          <div>
            <label className="text-xs font-semibold text-muted block mb-1">Program / Course</label>
            <input value={program} onChange={e => setProgram(e.target.value)}
              placeholder="e.g. MSc Computer Science"
              className="input-field" />
          </div>
        </div>
        <button onClick={generate} disabled={loading || !university.trim() || !program.trim()}
          className="btn-primary px-5 py-2.5 gap-2 w-full justify-center disabled:opacity-60">
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <BookOpen className="w-4 h-4" />}
          {loading ? 'Generating SOP Outline…' : 'Generate My SOP Outline'}
        </button>
      </div>

      {result && (
        <div className="card p-5">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-bold text-text">Your SOP Outline</h3>
            <button onClick={copy} className="btn-ghost text-xs py-1.5 px-3">
              <Download className="w-3.5 h-3.5" /> Copy
            </button>
          </div>
          <div className="prose prose-sm max-w-none text-sm text-textSoft space-y-1 leading-relaxed bg-surfaceAlt rounded-xl p-4">
            {renderMd(result)}
          </div>
        </div>
      )}
    </div>
  );
}
