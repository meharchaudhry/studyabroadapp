import { useState, useEffect, useRef } from 'react';
import {
  Bot, Send, User, Sparkles, FileCheck, BarChart3, Clock,
  BookOpen, CheckCircle2, Circle, ChevronDown, ChevronRight,
  Zap, Target, TrendingUp, AlertCircle, Trophy, RefreshCw,
  Download, ArrowRight, Loader2, Calendar, AlertTriangle,
  ChevronLeft, Info,
} from 'lucide-react';
import { aiAPI } from '../api/ai';
import { authAPI } from '../api/auth';

// ── Tabs ─────────────────────────────────────────────────────────────────────
const TABS = [
  { id: 'checklist', label: 'Doc Checklist',    icon: FileCheck  },
  { id: 'timeline',  label: 'Timeline',         icon: Clock     },
  { id: 'profile',   label: 'Profile Analysis', icon: BarChart3  },
  { id: 'sop',       label: 'SOP Builder',      icon: BookOpen  },
];

const COUNTRIES = [
  'United Kingdom','United States','Canada','Australia','Germany',
  'Netherlands','Ireland','Singapore','Japan','France','Sweden',
  'Switzerland','South Korea','New Zealand','UAE',
];

const INTAKE_MONTHS = ['January','February','March','April','May','June','July','August','September','October','November','December'];
const INTAKE_YEARS  = [new Date().getFullYear(), new Date().getFullYear() + 1, new Date().getFullYear() + 2];

const PRIORITY_STYLES = {
  critical: 'bg-rose-50 text-rose-700 border-rose-200',
  high:     'bg-amber-50 text-amber-700 border-amber-200',
  medium:   'bg-sky-50 text-blue-600 border-blue-200',
};

const CATEGORY_COLORS = {
  Identity:         'bg-lavendLight text-lavender',
  Admission:        'bg-skyLight text-blue-600',
  Financial:        'bg-amberLight text-amber-700',
  'Health & Other': 'bg-mintLight text-teal-600',
  'Interview Prep': 'bg-peachLight text-orange-600',
  Health:           'bg-mintLight text-teal-600',
};

// ── Markdown-lite renderer ───────────────────────────────────────────────────
function formatInline(text) {
  if (typeof text !== 'string') return text;
  // Parse **bold**, *italic*, strip stray lone asterisks
  const parts = text.split(/(\*\*[^*\n]+\*\*|\*[^*\n]+\*)/g);
  return parts.map((p, j) => {
    if (p.startsWith('**') && p.endsWith('**') && p.length > 4)
      return <strong key={j} className="font-semibold text-text">{p.slice(2, -2)}</strong>;
    if (p.startsWith('*') && p.endsWith('*') && p.length > 2)
      return <em key={j} className="italic text-textSoft">{p.slice(1, -1)}</em>;
    return p.replace(/\*/g, '');
  });
}

function renderMd(text) {
  if (!text) return null;
  const clean = text.replace(/\*\*\*/g, '**'); // collapse triple → double
  const lines = clean.split('\n');
  const elements = [];

  lines.forEach((line, i) => {
    const trimmed = line.trimStart();

    if (line.startsWith('# ')) {
      elements.push(
        <h2 key={i} className="font-black text-text mt-5 mb-2 text-lg border-b-2 border-lavender/40 pb-1.5">
          {line.slice(2).replace(/\*/g, '')}
        </h2>
      );
    } else if (line.startsWith('## ')) {
      elements.push(
        <h3 key={i} className="font-bold text-text mt-4 mb-1.5 text-base border-b border-surfaceBorder pb-1">
          {line.slice(3).replace(/\*/g, '')}
        </h3>
      );
    } else if (line.startsWith('### ')) {
      elements.push(
        <h4 key={i} className="font-semibold text-lavender mt-3 mb-1 text-sm uppercase tracking-wide">
          {line.slice(4).replace(/\*/g, '')}
        </h4>
      );
    } else if (/^Section \d+[:\s]/.test(line) || /^[A-Z][A-Z\s]+:$/.test(line.trim())) {
      // "Section 1: Title" or "ACADEMIC BACKGROUND:" style headings
      elements.push(
        <h3 key={i} className="font-bold text-lavender mt-5 mb-2 text-base border-b-2 border-lavender/30 pb-1.5">
          {line.replace(/\*/g, '')}
        </h3>
      );
    } else if (line.trim() === '---' || line.trim() === '***' || line.trim() === '===') {
      elements.push(<hr key={i} className="border-surfaceBorder my-3" />);
    } else if (trimmed.startsWith('- ') || trimmed.startsWith('• ') || trimmed.startsWith('* ')) {
      const content = formatInline(trimmed.slice(2));
      elements.push(
        <div key={i} className="flex items-start gap-2 ml-1 py-0.5">
          <span className="text-lavender flex-shrink-0 mt-1 text-xs font-bold">▸</span>
          <span className="text-sm leading-relaxed text-textSoft">{content}</span>
        </div>
      );
    } else if (line.match(/^\d+\.\s/)) {
      const num  = line.match(/^(\d+)\./)?.[1];
      const rest = formatInline(line.replace(/^\d+\.\s*/, ''));
      elements.push(
        <div key={i} className="flex items-start gap-2 ml-1 py-0.5">
          <span className="text-lavender font-bold flex-shrink-0 w-5 text-xs mt-1">{num}.</span>
          <span className="text-sm leading-relaxed text-textSoft">{rest}</span>
        </div>
      );
    } else if (line.trim() === '') {
      elements.push(<div key={i} className="h-2" />);
    } else {
      elements.push(<p key={i} className="text-sm leading-relaxed text-textSoft">{formatInline(line)}</p>);
    }
  });
  return <div className="space-y-0.5">{elements}</div>;
}

// ── Chat suggestions ──────────────────────────────────────────────────────────
const SUGGESTIONS = [
  'What IELTS score do I need for UK universities?',
  'How do I get a GIC for Canada?',
  'What is the Germany APS certificate and how long does it take?',
  'What scholarships are available for Indian students going to the USA?',
  'How early should I start my UK student visa application?',
  'What is the difference between F-1 and F-2 visa?',
  'How do I write a strong SOP for MSc Computer Science?',
  'What is post-study work rights in Australia vs UK?',
];

// (ICS generation removed — using direct Google Calendar links instead)

// ── Google Calendar URL builder ──────────────────────────────────────────────
function makeGCalURL(title, yyyymmdd, details = '') {
  // All-day event: end date = next day
  const d    = new Date(`${yyyymmdd.slice(0,4)}-${yyyymmdd.slice(4,6)}-${yyyymmdd.slice(6,8)}`);
  d.setDate(d.getDate() + 1);
  const end  = d.toISOString().slice(0, 10).replace(/-/g, '');
  const p    = new URLSearchParams({
    action:  'TEMPLATE',
    text:    title,
    dates:   `${yyyymmdd}/${end}`,
    details: details.slice(0, 1500), // GCal URL length limit
    sf:      'true',
  });
  return `https://calendar.google.com/calendar/render?${p.toString()}`;
}

// Compute the calendar date for timeline month index i (from today + i months)
function timelineDate(i) {
  const d = new Date();
  d.setDate(1); // avoid month-end edge cases
  d.setMonth(d.getMonth() + i);
  return d.toISOString().slice(0, 10).replace(/-/g, '');
}

// ═════════════════════════════════════════════════════════════════════════════
// Main Page
// ═════════════════════════════════════════════════════════════════════════════
export default function AIAgent() {
  const [tab, setTab]         = useState('checklist');
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
          <h1 className="text-2xl font-black text-text">Study Tools</h1>
          <p className="text-muted text-sm">
            Document checklist · Application timeline · Profile analysis · SOP builder
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
    content: "Hi! I'm your AI Study Coach, powered by Google Gemini and trained on everything you need to know about studying abroad as an Indian student.\n\nI can help with:\n- **Visa requirements** for UK, USA, Canada, Germany, Australia and more\n- **University applications**, SOPs, LORs, and deadlines\n- **Scholarship opportunities** — Chevening, Fulbright, DAAD, MEXT, GKS\n- **IELTS, TOEFL, GRE, GMAT** preparation strategies\n- **Financial planning**, GIC, blocked accounts, and budgeting\n- **Post-study work** rights in each country\n\nWhat would you like help with today?",
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
        content: 'Sorry, I\'m having trouble connecting right now. Please check your internet connection and try again.',
      }]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  return (
    <div className="card flex flex-col" style={{ height: '640px' }}>
      {/* Header */}
      <div className="p-4 border-b border-surfaceBorder flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl flex items-center justify-center shadow-sm">
            <Bot className="w-4 h-4 text-white" />
          </div>
          <div>
            <p className="text-sm font-bold text-text">Study Tools</p>
            <div className="flex items-center gap-1.5">
              <div className="w-1.5 h-1.5 rounded-full bg-teal-500 animate-pulse" />
              <p className="text-[10px] text-muted">Personalised to your profile</p>
            </div>
          </div>
        </div>
        <button onClick={() => setMessages([{
          role: 'assistant',
          content: "Hi again! What would you like to know about studying abroad?",
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
              <div className="flex gap-1 items-center">
                {[0, 0.15, 0.3].map((d, i) => (
                  <div key={i} className="w-2 h-2 bg-lavender/60 rounded-full animate-bounce"
                    style={{ animationDelay: `${d}s` }} />
                ))}
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Suggestion chips */}
      {messages.length <= 1 && (
        <div className="px-4 pb-2 flex gap-2 flex-wrap max-h-24 overflow-y-auto">
          {SUGGESTIONS.map((q, i) => (
            <button key={i} onClick={() => send(q)}
              className="text-[11px] bg-lavendLight text-lavender px-2.5 py-1.5 rounded-lg hover:bg-lavender hover:text-white transition-colors border border-lavender/20 flex items-center gap-1 flex-shrink-0">
              <Sparkles className="w-2.5 h-2.5 flex-shrink-0" /> {q}
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
  const profileCountries = profile?.target_countries || [];
  const defaultCountry   = profileCountries[0] || 'United Kingdom';

  const [country, setCountry]           = useState(defaultCountry);
  const [result, setResult]             = useState(null);
  const [loading, setLoading]           = useState(false);
  const [loadingSaved, setLoadingSaved] = useState(false);
  const [checked, setChecked]           = useState({});
  const [expandedCats, setExpandedCats] = useState({});
  const [savedIndicator, setSavedIndicator] = useState(false);
  const saveTimerRef = useRef(null);

  // When profile loads, update default country
  useEffect(() => {
    if (profileCountries.length > 0 && !result) setCountry(profileCountries[0]);
  }, [profile?.target_countries]);

  // Load saved checklist whenever country changes
  useEffect(() => {
    setResult(null); setChecked({});
    setLoadingSaved(true);
    aiAPI.getChecklist(country)
      .then(data => {
        if (data.saved && data.items?.length) {
          setResult({
            country:        data.country || country,
            visa_type:      data.visa_type,
            visa_fee_usd:   data.visa_fee_usd,
            timeline_weeks: data.timeline_weeks,
            summary:        data.summary,
            checklist:      data.items,
          });
          setChecked(data.checked || {});
          const cats = [...new Set(data.items.map(i => i.category))];
          const init = {};
          cats.slice(0, 2).forEach(c => { init[c] = true; });
          setExpandedCats(init);
        }
      })
      .catch(() => {})
      .finally(() => setLoadingSaved(false));
  }, [country]);

  const generate = async () => {
    setLoading(true); setResult(null); setChecked({});
    try {
      const data = await aiAPI.generateChecklist(country, profile);
      setResult(data);
      setChecked({});
      const cats = [...new Set((data.checklist || []).map(i => i.category))];
      const init = {};
      cats.slice(0, 2).forEach(c => { init[c] = true; });
      setExpandedCats(init);
      // Backend auto-saves on generate — show indicator
      setSavedIndicator(true);
      setTimeout(() => setSavedIndicator(false), 2000);
    } catch {
      setResult({ error: true });
    } finally {
      setLoading(false);
    }
  };

  const toggleCheck = id => {
    const newChecked = { ...checked, [id]: !checked[id] };
    setChecked(newChecked);
    // Debounced save to DB
    clearTimeout(saveTimerRef.current);
    saveTimerRef.current = setTimeout(async () => {
      if (!result?.checklist) return;
      try {
        await aiAPI.saveChecklist(country, result.checklist, newChecked, {
          visa_type:      result.visa_type,
          visa_fee_usd:   result.visa_fee_usd,
          timeline_weeks: result.timeline_weeks,
          summary:        result.summary,
          country:        result.country || country,
        });
        setSavedIndicator(true);
        setTimeout(() => setSavedIndicator(false), 1500);
      } catch {}
    }, 600);
  };

  const toggleCat = cat => setExpandedCats(p => ({ ...p, [cat]: !p[cat] }));

  const grouped = (result?.checklist || []).reduce((acc, item) => {
    (acc[item.category] = acc[item.category] || []).push(item);
    return acc;
  }, {});

  const total     = result?.checklist?.length || 0;
  const doneCount = Object.values(checked).filter(Boolean).length;
  const progress  = total ? Math.round((doneCount / total) * 100) : 0;

  const copyToClipboard = () => {
    const text = (result?.checklist || [])
      .map(i => `[ ] [${i.priority?.toUpperCase()}] ${i.category}: ${i.task}${i.note ? ` — ${i.note}` : ''}`)
      .join('\n');
    navigator.clipboard.writeText(text).catch(() => {});
  };

  // Show profile countries first, then the rest
  const orderedCountries = [
    ...profileCountries,
    ...COUNTRIES.filter(c => !profileCountries.includes(c)),
  ];

  return (
    <div className="space-y-4">
      {/* Country selector */}
      <div className="card p-4 space-y-3">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <p className="text-xs font-bold text-muted uppercase tracking-wide">Select Destination Country</p>
          {savedIndicator && (
            <span className="text-[11px] text-teal-600 flex items-center gap-1 font-semibold">
              <CheckCircle2 className="w-3.5 h-3.5" /> Progress saved
            </span>
          )}
          {loadingSaved && (
            <span className="text-[11px] text-muted flex items-center gap-1">
              <Loader2 className="w-3 h-3 animate-spin" /> Loading saved…
            </span>
          )}
        </div>
        {profileCountries.length > 0 && (
          <p className="text-[11px] text-lavender font-medium">
            Your target countries shown first
          </p>
        )}
        <div className="flex flex-wrap gap-2">
          {orderedCountries.map(c => (
            <button key={c} onClick={() => setCountry(c)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all
                ${country === c
                  ? 'bg-lavender text-white border-lavender'
                  : profileCountries.includes(c)
                    ? 'bg-lavendLight text-lavender border-lavender/30 hover:bg-lavender hover:text-white'
                    : 'bg-white text-textSoft border-surfaceBorder hover:border-lavender/50'}`}>
              {c}
            </button>
          ))}
        </div>
        <button onClick={generate} disabled={loading}
          className="btn-primary px-5 py-2.5 gap-2 disabled:opacity-60 flex-shrink-0">
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Zap className="w-4 h-4" />}
          {loading ? 'Generating personalised checklist…' : result ? `Regenerate ${country} Checklist` : `Generate ${country} Checklist`}
        </button>
      </div>

      {/* Empty state */}
      {!result && !loading && (
        <div className="card p-14 text-center">
          <div className="w-14 h-14 bg-lavendLight rounded-2xl flex items-center justify-center mx-auto mb-4">
            <FileCheck className="w-7 h-7 text-lavender" />
          </div>
          <p className="font-bold text-text text-lg mb-1">Document Checklist</p>
          <p className="text-sm text-muted max-w-sm mx-auto">
            Select a destination and click Generate to get a comprehensive,
            prioritised checklist personalised to your exact profile.
          </p>
          <div className="flex gap-2 justify-center mt-4 flex-wrap">
            {['✅ Personalised to your CGPA & test scores', '⚡ Country-specific requirements', '📋 Priority-sorted with deadlines'].map(f => (
              <span key={f} className="text-[11px] bg-surfaceAlt text-textSoft px-2.5 py-1 rounded-full">{f}</span>
            ))}
          </div>
        </div>
      )}

      {result?.error && (
        <div className="card p-8 text-center">
          <AlertCircle className="w-8 h-8 text-rose-500 mx-auto mb-2" />
          <p className="font-semibold text-text">Could not generate checklist</p>
          <p className="text-sm text-muted mt-1">Please check your GOOGLE_API_KEY is configured.</p>
        </div>
      )}

      {result && !result.error && (
        <>
          {/* Overview */}
          <div className="card p-5">
            <div className="flex items-start justify-between gap-4 flex-wrap">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <h2 className="font-bold text-text text-lg">{result.country}</h2>
                  {result.visa_type && (
                    <span className="badge bg-lavendLight text-lavender text-[10px]">{result.visa_type}</span>
                  )}
                </div>
                <p className="text-sm text-muted max-w-xl">{result.summary}</p>
              </div>
              <button onClick={copyToClipboard} className="btn-ghost text-xs py-1.5 px-3 flex-shrink-0">
                <Download className="w-3.5 h-3.5" /> Copy All
              </button>
            </div>
            <div className="grid grid-cols-3 gap-3 mt-4 text-xs">
              {result.visa_fee_usd > 0 && (
                <div className="bg-surfaceAlt rounded-xl p-3">
                  <p className="text-muted mb-0.5">Visa Fee</p>
                  <p className="font-bold text-text">${result.visa_fee_usd} USD</p>
                </div>
              )}
              {result.timeline_weeks > 0 && (
                <div className="bg-surfaceAlt rounded-xl p-3">
                  <p className="text-muted mb-0.5">Lead Time</p>
                  <p className="font-bold text-text">{result.timeline_weeks} weeks</p>
                </div>
              )}
              <div className="bg-surfaceAlt rounded-xl p-3">
                <p className="text-muted mb-0.5">Documents</p>
                <p className="font-bold text-text">{total} items</p>
              </div>
            </div>
            {/* Progress */}
            <div className="mt-4">
              <div className="flex justify-between text-xs mb-1.5">
                <span className="text-textSoft font-medium">Progress</span>
                <span className="font-bold text-lavender">{doneCount}/{total} ready</span>
              </div>
              <div className="bg-lavendLight rounded-full h-2 overflow-hidden">
                <div className="bg-lavender h-2 rounded-full transition-all duration-500"
                  style={{ width: `${progress}%` }} />
              </div>
              {progress === 100 && (
                <p className="text-xs text-teal-600 font-bold mt-1.5">🎉 All documents ready! Go apply!</p>
              )}
            </div>
          </div>

          {/* Checklist grouped by category */}
          {Object.entries(grouped).map(([cat, items]) => (
            <div key={cat} className="card overflow-hidden">
              <button onClick={() => toggleCat(cat)}
                className="w-full flex items-center justify-between p-4 hover:bg-surfaceAlt transition-colors">
                <div className="flex items-center gap-3">
                  <span className={`badge text-[10px] ${CATEGORY_COLORS[cat] || 'bg-surfaceAlt text-textSoft'}`}>{cat}</span>
                  <span className="text-xs text-muted">{items.filter(i => checked[i.id]).length}/{items.length} done</span>
                </div>
                <ChevronDown className={`w-4 h-4 text-muted transition-transform ${expandedCats[cat] ? 'rotate-180' : ''}`} />
              </button>
              {expandedCats[cat] && (
                <div className="px-4 pb-4 space-y-2 border-t border-surfaceBorder pt-3">
                  {items.map(item => (
                    <div key={item.id}
                      onClick={() => toggleCheck(item.id)}
                      className="flex items-start gap-3 p-3 rounded-xl hover:bg-surfaceAlt cursor-pointer transition-colors group">
                      {checked[item.id]
                        ? <CheckCircle2 className="w-4 h-4 text-teal-500 flex-shrink-0 mt-0.5" />
                        : <Circle className="w-4 h-4 text-muted flex-shrink-0 mt-0.5 group-hover:text-lavender" />}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className={`text-sm leading-snug font-medium ${checked[item.id] ? 'line-through text-muted' : 'text-text'}`}>
                            {item.task}
                          </span>
                          <span className={`badge text-[9px] border ${PRIORITY_STYLES[item.priority] || ''}`}>
                            {item.priority}
                          </span>
                        </div>
                        {item.note && (
                          <p className="text-xs text-muted mt-0.5 flex items-start gap-1">
                            <Info className="w-3 h-3 mt-0.5 flex-shrink-0" />{item.note}
                          </p>
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
// Timeline Tab — Multi-step questionnaire
// ═══════════════════════════════════════════════════════════
function TimelineTab({ profile }) {
  const [step, setStep]   = useState(1);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const [intakeMonth, setIntakeMonth] = useState('September');
  const [intakeYear,  setIntakeYear]  = useState(INTAKE_YEARS[1]);
  const [countries,        setCountries]        = useState([]);
  const countriesInitRef = useRef(false); // guard: only init from profile once

  const [ieltsDone,  setIeltsDone]  = useState(profile?.english_test === 'IELTS' ? 'done' : 'planned');
  const [ieltsScore, setIeltsScore] = useState(profile?.english_score || '');
  const [ieltsWhen,  setIeltsWhen]  = useState('');
  const [greDone,    setGreDone]    = useState(profile?.gre_score ? 'done' : 'planned');
  const [greScore,   setGreScore]   = useState(profile?.gre_score || '');
  const [greWhen,    setGreWhen]    = useState('');
  const [greNA,      setGreNA]      = useState(false);

  const [appStatus, setAppStatus] = useState({
    shortlisted: false, sop_started: false, lors_arranged: false,
    transcripts_ready: false, budget_confirmed: false,
    offer_received: false, deposit_paid: false, visa_started: false,
  });

  useEffect(() => {
    // Only seed countries from profile ONCE — after that, user controls the selection
    if (!countriesInitRef.current && profile?.target_countries?.length) {
      const arr = Array.isArray(profile.target_countries)
        ? profile.target_countries
        : [profile.target_countries];
      setCountries(arr);
      countriesInitRef.current = true;
    }
    if (profile?.english_test === 'IELTS' && profile?.english_score) {
      setIeltsDone('done'); setIeltsScore(String(profile.english_score));
    }
    if (profile?.gre_score) { setGreDone('done'); setGreScore(String(profile.gre_score)); }
  }, [profile]);

  // Multi-select toggle — clicking a selected country deselects it
  const toggleCountry = c => setCountries(prev =>
    prev.includes(c) ? prev.filter(x => x !== c) : [...prev, c]
  );
  const toggleStatus  = k => setAppStatus(p => ({ ...p, [k]: !p[k] }));

  const monthsUntilIntake = () => {
    const now    = new Date();
    const target = new Date(`${intakeMonth} 1, ${intakeYear}`);
    return Math.max(1, Math.round((target - now) / (1000 * 60 * 60 * 24 * 30)));
  };

  const generate = async () => {
    setLoading(true);
    try {
      const intake        = `${intakeMonth} ${intakeYear}`;
      const currentStatus = {
        ielts_done: ieltsDone === 'done', ielts_score: ieltsScore, ielts_when: ieltsWhen,
        gre_done:   greDone  === 'done',  gre_score:   greScore,   gre_when:   greWhen,
        gre_not_needed: greNA,
        months_until_intake: monthsUntilIntake(),
        ...appStatus,
      };
      const data = await aiAPI.generateTimeline(intake, countries, profile, currentStatus);
      setResult(data);
      setStep(4);
    } catch {
      setResult({ error: true }); setStep(4);
    } finally {
      setLoading(false);
    }
  };

  const reset = () => { setResult(null); setStep(1); };

  // ── Step 1: Planning ──
  if (step === 1) return (
    <div className="space-y-4">
      <StepHeader step={1} total={3} title="When & Where?" sub="Set your target intake and destination countries" />
      <div className="card p-5 space-y-5">
        <div>
          <p className="text-xs font-bold text-muted uppercase tracking-wide mb-2">Target Intake</p>
          <div className="flex gap-3 flex-wrap">
            <div>
              <label className="text-xs text-muted block mb-1">Month</label>
              <select value={intakeMonth} onChange={e => setIntakeMonth(e.target.value)}
                className="input-field text-sm py-2 pr-8">
                {INTAKE_MONTHS.map(m => <option key={m}>{m}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs text-muted block mb-1">Year</label>
              <select value={intakeYear} onChange={e => setIntakeYear(Number(e.target.value))}
                className="input-field text-sm py-2 pr-8">
                {INTAKE_YEARS.map(y => <option key={y}>{y}</option>)}
              </select>
            </div>
            <div className="flex items-end">
              <div className="bg-surfaceAlt rounded-xl px-4 py-2 text-xs">
                <p className="text-muted">Time available</p>
                <p className="font-bold text-lavender text-sm">{monthsUntilIntake()} months</p>
              </div>
            </div>
          </div>
        </div>
        <div>
          <p className="text-xs font-bold text-muted uppercase tracking-wide mb-2">Target Countries <span className="normal-case font-normal">(select all that apply)</span></p>
          <div className="flex flex-wrap gap-2">
            {COUNTRIES.map(c => (
              <button key={c} onClick={() => toggleCountry(c)}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all
                  ${countries.includes(c)
                    ? 'bg-lavender text-white border-lavender'
                    : 'bg-white text-textSoft border-surfaceBorder hover:border-lavender/50'}`}>
                {c}
              </button>
            ))}
          </div>
          {countries.length > 0 && (
            <p className="text-xs text-lavender mt-2">Selected: {countries.join(', ')}</p>
          )}
        </div>
      </div>
      {/* Germany APS warning */}
      {countries.includes('Germany') && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 flex gap-3">
          <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-bold text-amber-800">Germany APS Certificate Warning</p>
            <p className="text-xs text-amber-700 mt-0.5">
              Indian students need an APS certificate from APS India (Delhi) — processing takes <strong>6–8 months</strong>.
              This is the biggest bottleneck. If not already applied, this should be your first action.
            </p>
          </div>
        </div>
      )}
      <div className="flex justify-end">
        <button onClick={() => setStep(2)} disabled={countries.length === 0}
          className="btn-primary px-6 py-2.5 gap-2 disabled:opacity-60">
          Next: Test Status <ChevronRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );

  // ── Step 2: Test Status ──
  if (step === 2) return (
    <div className="space-y-4">
      <StepHeader step={2} total={3} title="Test Status" sub="Tell us where you are with your English and aptitude tests" />
      <div className="card p-5 space-y-5">
        {/* IELTS/TOEFL */}
        <div>
          <p className="text-sm font-bold text-text mb-3">English Proficiency Test (IELTS / TOEFL)</p>
          <div className="flex gap-2 mb-3 flex-wrap">
            {['done', 'planned', 'not started'].map(v => (
              <button key={v} onClick={() => setIeltsDone(v)}
                className={`px-4 py-2 rounded-lg text-xs font-semibold border transition-all capitalize
                  ${ieltsDone === v ? 'bg-lavender text-white border-lavender' : 'bg-white text-textSoft border-surfaceBorder hover:border-lavender/50'}`}>
                {v === 'done' ? '✅ Already done' : v === 'planned' ? '📅 Planned' : '❌ Not started'}
              </button>
            ))}
          </div>
          {ieltsDone === 'done' && (
            <input value={ieltsScore} onChange={e => setIeltsScore(e.target.value)}
              placeholder="Your score (e.g. 7.0 for IELTS, 100 for TOEFL)"
              className="input-field text-sm" />
          )}
          {ieltsDone === 'planned' && (
            <input value={ieltsWhen} onChange={e => setIeltsWhen(e.target.value)}
              placeholder="When are you taking it? (e.g. 'March 2025' or '2 months from now')"
              className="input-field text-sm" />
          )}
        </div>

        {/* GRE/GMAT */}
        <div>
          <p className="text-sm font-bold text-text mb-3">GRE / GMAT</p>
          <div className="flex gap-2 mb-3 flex-wrap">
            {['done', 'planned', 'not started'].map(v => (
              <button key={v} onClick={() => { setGreDone(v); setGreNA(false); }}
                className={`px-4 py-2 rounded-lg text-xs font-semibold border transition-all capitalize
                  ${!greNA && greDone === v ? 'bg-blue-500 text-white border-blue-500' : 'bg-white text-textSoft border-surfaceBorder hover:border-blue-300'}`}>
                {v === 'done' ? '✅ Already done' : v === 'planned' ? '📅 Planned' : '❌ Not started'}
              </button>
            ))}
            <button onClick={() => { setGreNA(true); setGreDone(''); }}
              className={`px-4 py-2 rounded-lg text-xs font-semibold border transition-all
                ${greNA ? 'bg-teal-500 text-white border-teal-500' : 'bg-white text-textSoft border-surfaceBorder hover:border-teal-300'}`}>
              ℹ️ Not required for my programs
            </button>
          </div>
          {!greNA && greDone === 'done' && (
            <input value={greScore} onChange={e => setGreScore(e.target.value)}
              placeholder="Your GRE score (e.g. 320) or GMAT score (e.g. 680)"
              className="input-field text-sm" />
          )}
          {!greNA && greDone === 'planned' && (
            <input value={greWhen} onChange={e => setGreWhen(e.target.value)}
              placeholder="When are you taking it? (e.g. 'April 2025')"
              className="input-field text-sm" />
          )}
        </div>
      </div>
      <div className="flex justify-between">
        <button onClick={() => setStep(1)} className="btn-ghost px-4 py-2 gap-2">
          <ChevronLeft className="w-4 h-4" /> Back
        </button>
        <button onClick={() => setStep(3)} className="btn-primary px-6 py-2.5 gap-2">
          Next: Application Stage <ChevronRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );

  // ── Step 3: Application stage ──
  if (step === 3) {
    const statusItems = [
      { key: 'shortlisted',       label: 'Researched and shortlisted universities',  icon: '🎓' },
      { key: 'sop_started',       label: 'Started writing my SOP/personal statement', icon: '✍️' },
      { key: 'lors_arranged',     label: 'Arranged/requested Letters of Recommendation', icon: '📄' },
      { key: 'transcripts_ready', label: 'Official transcripts ordered/ready',        icon: '📋' },
      { key: 'budget_confirmed',  label: 'Budget / funding source confirmed',          icon: '💰' },
      { key: 'offer_received',    label: 'Received an offer letter from a university', icon: '🎉' },
      { key: 'deposit_paid',      label: 'Paid tuition deposit to confirm enrolment',  icon: '💳' },
      { key: 'visa_started',      label: 'Started visa application process',           icon: '🛂' },
    ];

    return (
      <div className="space-y-4">
        <StepHeader step={3} total={3} title="Application Stage" sub="Tick everything you've already completed — we'll skip these in your timeline" />
        <div className="card p-5">
          <div className="space-y-2">
            {statusItems.map(({ key, label, icon }) => (
              <button key={key} onClick={() => toggleStatus(key)}
                className={`w-full flex items-center gap-3 p-3 rounded-xl border transition-all text-left
                  ${appStatus[key]
                    ? 'bg-teal-50 border-teal-200 text-teal-700'
                    : 'bg-white border-surfaceBorder text-textSoft hover:border-lavender/40'}`}>
                <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center flex-shrink-0
                  ${appStatus[key] ? 'bg-teal-500 border-teal-500' : 'border-gray-300'}`}>
                  {appStatus[key] && <CheckCircle2 className="w-3 h-3 text-white" />}
                </div>
                <span className="text-sm">{icon} {label}</span>
              </button>
            ))}
          </div>
          <p className="text-xs text-muted mt-3">
            {Object.values(appStatus).filter(Boolean).length} of {statusItems.length} steps completed
          </p>
        </div>
        <div className="flex justify-between">
          <button onClick={() => setStep(2)} className="btn-ghost px-4 py-2 gap-2">
            <ChevronLeft className="w-4 h-4" /> Back
          </button>
          <button onClick={generate} disabled={loading}
            className="btn-primary px-6 py-2.5 gap-2 disabled:opacity-60">
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
            {loading ? 'Generating personalised timeline…' : 'Generate My Timeline'}
          </button>
        </div>
      </div>
    );
  }

  // ── Step 4: Results ──
  if (step === 4) return (
    <div className="space-y-4">
      {result?.error ? (
        <div className="card p-10 text-center">
          <AlertCircle className="w-8 h-8 text-rose-500 mx-auto mb-2" />
          <p className="font-semibold text-text">Could not generate timeline</p>
          <p className="text-sm text-muted mt-1 mb-4">Check your GOOGLE_API_KEY configuration.</p>
          <button onClick={reset} className="btn-secondary">Try Again</button>
        </div>
      ) : (
        <>
          {/* Header */}
          <div className="flex items-center justify-between flex-wrap gap-3">
            <div>
              <h2 className="font-bold text-text text-lg">
                {intakeMonth} {intakeYear} — Application Roadmap
              </h2>
              <p className="text-sm text-muted">{countries.join(', ')}</p>
            </div>
            <div className="flex gap-2">
              <button onClick={reset} className="btn-ghost text-xs px-3 py-2 flex items-center gap-1.5">
                <RefreshCw className="w-3.5 h-3.5" /> Redo
              </button>
            </div>
          </div>

          {/* Urgent warnings */}
          {(result?.urgent_warnings || []).length > 0 && (
            <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 space-y-1.5">
              <p className="text-sm font-bold text-amber-800 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4" /> Urgent Actions Required
              </p>
              {result.urgent_warnings.map((w, i) => (
                <p key={i} className="text-xs text-amber-700">{w}</p>
              ))}
            </div>
          )}

          {/* Calendar actions */}
          {(() => {
            const months         = result?.months || [];
            const milestones     = months.map((m, i) => ({ ...m, idx: i })).filter(m => m.milestone);
            const intakeMonthIdx = INTAKE_MONTHS.indexOf(intakeMonth);
            const intakeDateStr  = intakeMonthIdx >= 0
              ? `${intakeYear}${String(intakeMonthIdx + 1).padStart(2, '0')}01`
              : null;
            const intakeGCalUrl  = intakeDateStr
              ? makeGCalURL(`🎓 University Intake — ${intakeMonth} ${intakeYear}`, intakeDateStr,
                  `University intake! ${countries.join(', ')}`)
              : null;

            // Opens all milestone tabs synchronously (must be in click handler to bypass popup blocker)
            const openAllMilestones = () => {
              milestones.forEach(m => {
                window.open(
                  makeGCalURL(`📌 ${m.label}`, timelineDate(m.idx), m.tasks.join(' | ')),
                  '_blank'
                );
              });
              if (intakeDateStr) window.open(intakeGCalUrl, '_blank');
            };

            return (
              <div className="bg-lavendLight border border-lavender/20 rounded-xl p-4 space-y-3">
                <p className="text-xs font-bold text-lavender flex items-center gap-1.5">
                  <Calendar className="w-3.5 h-3.5" /> Add to Google Calendar
                </p>
                <div className="flex flex-wrap gap-2">
                  <button onClick={openAllMilestones}
                    className="text-xs bg-lavender text-white px-4 py-2 rounded-lg hover:bg-lavender/90 transition-all font-semibold flex items-center gap-1.5 shadow-sm">
                    <Calendar className="w-3.5 h-3.5" />
                    Add all {milestones.length} milestones + intake to Google Calendar
                  </button>
                  {intakeGCalUrl && (
                    <a href={intakeGCalUrl} target="_blank" rel="noopener noreferrer"
                      className="text-xs bg-white border border-lavender/30 text-lavender px-3 py-2 rounded-lg hover:bg-lavendLight transition-all font-semibold flex items-center gap-1.5">
                      <Calendar className="w-3 h-3" /> Intake date only
                    </a>
                  )}
                </div>
                <p className="text-[11px] text-lavender/70">
                  Opens Google Calendar in new tabs — one per milestone. Allow pop-ups if your browser blocks them.
                  Each event pre-filled with tasks for that month.
                </p>
              </div>
            );
          })()}

          {/* Timeline */}
          <div className="relative">
            <div className="absolute left-5 top-5 bottom-5 w-0.5 bg-surfaceBorder rounded-full" />
            <div className="space-y-4">
              {(result?.months || []).map((month, i) => {
                const dateStr   = timelineDate(i);
                const gcalUrl   = makeGCalURL(
                  `PathPilot: ${month.label}`,
                  dateStr,
                  (month.tasks || []).join(' | '),
                );
                return (
                  <div key={i} className="relative flex gap-4">
                    <div className={`w-10 h-10 rounded-full flex-shrink-0 flex items-center justify-center z-10 border-2 shadow-sm
                      ${month.milestone
                        ? 'bg-lavender border-lavender text-white'
                        : 'bg-white border-surfaceBorder text-muted'}`}>
                      {month.milestone ? <Trophy className="w-4 h-4" /> : <span className="text-xs font-bold">{i + 1}</span>}
                    </div>
                    <div className={`flex-1 card p-4 ${month.milestone ? 'border-lavender/30 bg-lavendLight/20' : ''}`}>
                      <div className="flex items-start justify-between gap-2 mb-2 flex-wrap">
                        <div>
                          <span className="text-xs font-bold text-lavender uppercase tracking-wide">{month.month}</span>
                          <p className="font-bold text-text text-sm">{month.label}</p>
                        </div>
                        <div className="flex items-center gap-1.5 flex-shrink-0">
                          {month.milestone && (
                            <span className="badge bg-lavender text-white text-[9px]">Milestone</span>
                          )}
                          <a href={gcalUrl} target="_blank" rel="noopener noreferrer"
                            title="Add to Google Calendar"
                            className="text-[10px] text-blue-500 hover:text-blue-700 border border-blue-200 rounded-md px-1.5 py-0.5 hover:bg-blue-50 transition-colors flex items-center gap-1">
                            <Calendar className="w-2.5 h-2.5" /> +GCal
                          </a>
                        </div>
                      </div>
                      <ul className="space-y-1.5">
                        {(month.tasks || []).map((task, j) => (
                          <li key={j} className="flex items-start gap-2 text-sm text-textSoft">
                            <ArrowRight className="w-3 h-3 mt-1 text-lavender flex-shrink-0" />
                            {task}
                          </li>
                        ))}
                      </ul>
                      {month.country_specific && (
                        <p className="mt-2 text-xs text-blue-600 bg-skyLight px-2.5 py-1.5 rounded-lg flex items-start gap-1.5">
                          <Info className="w-3 h-3 mt-0.5 flex-shrink-0" />{month.country_specific}
                        </p>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </>
      )}
    </div>
  );

  return null;
}

function StepHeader({ step, total, title, sub }) {
  return (
    <div className="flex items-center gap-4">
      <div className="flex gap-1.5">
        {Array.from({ length: total }, (_, i) => (
          <div key={i} className={`h-1.5 rounded-full transition-all ${i < step ? 'bg-lavender w-8' : 'bg-surfaceBorder w-4'}`} />
        ))}
      </div>
      <div>
        <span className="text-xs text-muted">Step {step} of {total}</span>
        <p className="font-bold text-text text-sm">{title}</p>
        <p className="text-xs text-muted">{sub}</p>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════
// Profile Analysis Tab
// ═══════════════════════════════════════════════════════════
const DIMENSION_META = {
  academic:          { label: 'Academic (CGPA)',         max: 30, color: 'bg-lavender' },
  english:           { label: 'English Proficiency',     max: 20, color: 'bg-teal-500' },
  standardized_test: { label: 'GRE / GMAT',              max: 10, color: 'bg-blue-500' },
  experience:        { label: 'Work Experience',         max: 15, color: 'bg-amber-500' },
  financial:         { label: 'Financial Preparedness',  max: 10, color: 'bg-orange-400' },
  completeness:      { label: 'Profile Completeness',    max: 10, color: 'bg-indigo-400' },
  clarity:           { label: 'Career Clarity',          max: 5,  color: 'bg-pink-400' },
};

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

  const scoreColor = s => s >= 75 ? 'text-teal-600' : s >= 50 ? 'text-amber-600' : 'text-rose-500';
  const bgColor    = s => s >= 75 ? 'bg-teal-500'  : s >= 50 ? 'bg-amber-400'   : 'bg-rose-400';
  const impactBadge = { high: 'bg-rose-50 text-rose-700', medium: 'bg-amber-50 text-amber-700', low: 'bg-teal-50 text-teal-700' };

  return (
    <div className="space-y-4">
      <div className="card p-5 text-center space-y-3">
        <div className="w-14 h-14 bg-lavendLight rounded-2xl flex items-center justify-center mx-auto">
          <BarChart3 className="w-7 h-7 text-lavender" />
        </div>
        <div>
          <h2 className="font-bold text-text">AI Profile Analysis</h2>
          <p className="text-sm text-muted mt-1 max-w-lg mx-auto">
            7-dimensional analysis: Academic · English · GRE · Experience · Financial · Completeness · Career Clarity
          </p>
        </div>
        <button onClick={analyze} disabled={loading}
          className="btn-primary px-6 py-2.5 gap-2 mx-auto disabled:opacity-60">
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Target className="w-4 h-4" />}
          {loading ? 'Analysing your profile…' : 'Analyse My Profile'}
        </button>
      </div>

      {result?.error && (
        <div className="card p-8 text-center">
          <AlertCircle className="w-8 h-8 text-rose-500 mx-auto mb-2" />
          <p className="font-semibold">Analysis failed — check API configuration.</p>
        </div>
      )}

      {result && !result.error && (
        <div className="space-y-4">
          {/* Score + grade */}
          <div className="card p-6">
            <div className="flex items-center justify-between mb-4 flex-wrap gap-3">
              <div>
                <p className="text-xs font-bold text-muted uppercase tracking-wide mb-1">Overall Profile Strength</p>
                <div className="flex items-baseline gap-2">
                  <span className={`text-5xl font-black ${scoreColor(result.overall_score)}`}>{result.overall_score}</span>
                  <span className="text-xl text-muted font-normal">/100</span>
                  <span className={`badge ml-2 font-bold text-sm px-3 py-1 ${
                    result.grade === 'Excellent' ? 'bg-teal-100 text-teal-700' :
                    result.grade === 'Good'      ? 'bg-lavendLight text-lavender' :
                    result.grade === 'Fair'      ? 'bg-amberLight text-amber-700' :
                    'bg-rose-50 text-rose-700'}`}>
                    {result.grade}
                  </span>
                </div>
              </div>
              {/* Circular indicator */}
              <div className={`w-16 h-16 rounded-full border-4 flex items-center justify-center
                ${result.overall_score >= 75 ? 'border-teal-400' : result.overall_score >= 50 ? 'border-lavender' : 'border-amber-400'}`}>
                <span className="text-xs font-black text-text">{result.overall_score}%</span>
              </div>
            </div>
            <div className={`w-full rounded-full h-3 bg-surfaceBorder overflow-hidden`}>
              <div className={`h-3 rounded-full transition-all duration-700 ${bgColor(result.overall_score)}`}
                style={{ width: `${result.overall_score}%` }} />
            </div>
            {result.verdict && (
              <p className="text-sm text-textSoft mt-4 leading-relaxed">{result.verdict}</p>
            )}
          </div>

          {/* Dimension breakdown */}
          {result.dimension_scores && (
            <div className="card p-5">
              <h3 className="font-bold text-text mb-4 flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-lavender" /> Score Breakdown
              </h3>
              <div className="space-y-3">
                {Object.entries(DIMENSION_META).map(([key, meta]) => {
                  const val = result.dimension_scores[key] ?? 0;
                  const pct = Math.round((val / meta.max) * 100);
                  return (
                    <div key={key}>
                      <div className="flex justify-between text-xs mb-1">
                        <span className="text-textSoft font-medium">{meta.label}</span>
                        <span className="font-bold text-text">{val}<span className="text-muted font-normal">/{meta.max}</span></span>
                      </div>
                      <div className="bg-surfaceBorder rounded-full h-2 overflow-hidden">
                        <div className={`h-2 rounded-full transition-all duration-700 ${meta.color}`}
                          style={{ width: `${pct}%` }} />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

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
                <AlertCircle className="w-4 h-4 text-rose-500" /> Gaps to Address
              </h3>
              <ul className="space-y-2">
                {(result.gaps || []).filter(Boolean).map((g, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-textSoft">
                    <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0 mt-0.5" /> {g}
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Action plan */}
          {result.actions?.length > 0 && (
            <div className="card p-4">
              <h3 className="font-bold text-text mb-3 flex items-center gap-2">
                <Zap className="w-4 h-4 text-amber-500" /> Prioritised Action Plan
              </h3>
              <div className="space-y-2">
                {result.actions.map((a, i) => (
                  <div key={i} className="flex items-start gap-3 p-3 bg-surfaceAlt rounded-xl">
                    <span className="text-xs font-bold text-muted mt-0.5 w-5 flex-shrink-0">{i + 1}.</span>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-semibold text-text">{a.action}</p>
                      {a.why && <p className="text-xs text-muted mt-0.5">{a.why}</p>}
                      {a.deadline && <p className="text-xs text-blue-500 mt-0.5">⏰ By: {a.deadline}</p>}
                    </div>
                    <div className="flex gap-1.5 flex-shrink-0">
                      <span className={`badge text-[9px] font-semibold px-2 py-0.5 rounded-full ${impactBadge[a.impact] || ''}`}>
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
              <div className="grid sm:grid-cols-2 gap-3">
                {result.match_countries.map((c, i) => (
                  <div key={i} className="bg-surfaceAlt rounded-xl p-3">
                    <div className="flex justify-between text-sm mb-1.5">
                      <span className="font-semibold text-text">{c.country}</span>
                      <span className={`font-bold ${scoreColor(c.fit)}`}>{c.fit}%</span>
                    </div>
                    <div className="bg-white rounded-full h-2 overflow-hidden">
                      <div className={`h-2 rounded-full transition-all duration-500 ${bgColor(c.fit)}`}
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
// Client-side university → country lookup for instant feedback (subset of backend dict)
const UNI_COUNTRY_HINTS = {
  "ie university": "Spain", "ie business school": "Spain",
  "esade": "Spain", "iese": "Spain", "bocconi": "Italy",
  "politecnico di milano": "Italy", "polimi": "Italy",
  "hec paris": "France", "insead": "France", "sciences po": "France",
  "sorbonne": "France", "école polytechnique": "France",
  "tum": "Germany", "lmu munich": "Germany", "heidelberg": "Germany",
  "rwth aachen": "Germany", "humboldt": "Germany", "whu": "Germany",
  "tu delft": "Netherlands", "delft": "Netherlands",
  "erasmus": "Netherlands", "leiden": "Netherlands",
  "eth zurich": "Switzerland", "epfl": "Switzerland",
  "st. gallen": "Switzerland", "imd lausanne": "Switzerland",
  "oxford": "United Kingdom", "cambridge": "United Kingdom",
  "imperial": "United Kingdom", "ucl": "United Kingdom",
  "lse": "United Kingdom", "warwick": "United Kingdom",
  "edinburgh": "United Kingdom", "glasgow": "United Kingdom",
  "mit": "United States", "stanford": "United States",
  "harvard": "United States", "caltech": "United States",
  "carnegie mellon": "United States", "cmu": "United States",
  "columbia": "United States", "yale": "United States",
  "princeton": "United States", "cornell": "United States",
  "duke": "United States", "nyu": "United States",
  "berkeley": "United States", "ucla": "United States",
  "georgia tech": "United States", "purdue": "United States",
  "mcgill": "Canada", "waterloo": "Canada", "ubc": "Canada",
  "toronto": "Canada", "mcmaster": "Canada",
  "melbourne": "Australia", "sydney": "Australia",
  "monash": "Australia", "anu": "Australia", "unsw": "Australia",
  "nus": "Singapore", "ntu": "Singapore", "nanyang": "Singapore",
  "karolinska": "Sweden", "kth": "Sweden", "lund": "Sweden",
  "trinity college dublin": "Ireland", "ucd": "Ireland",
  "ku leuven": "Belgium", "nova sbe": "Portugal",
  "aalto": "Finland", "copenhagen business school": "Denmark",
};

function detectUniCountry(uniName) {
  const key = uniName.toLowerCase().trim();
  for (const [hint, country] of Object.entries(UNI_COUNTRY_HINTS)) {
    if (key.includes(hint) || hint.includes(key)) return country;
  }
  return null;
}

function SopTab({ profile }) {
  const profileCountries = profile?.target_countries || [];
  const [university, setUniversity]   = useState('');
  const [program, setProgram]         = useState('');
  const [country, setCountry]         = useState(profileCountries[0] || '');
  const [detectedCountry, setDetected] = useState(null); // auto-detected from uni name
  const [countryNote, setCountryNote] = useState('');    // mismatch warning from backend
  const [resolvedCountry, setResolved] = useState('');   // what backend actually used
  const [result, setResult]           = useState('');
  const [loading, setLoading]         = useState(false);

  useEffect(() => {
    if (profileCountries.length > 0 && !country) setCountry(profileCountries[0]);
  }, [profile?.target_countries]);

  // Auto-detect country as user types university name
  const handleUniChange = (val) => {
    setUniversity(val);
    if (val.length > 3) {
      const detected = detectUniCountry(val);
      setDetected(detected);
      if (detected && detected !== country) {
        // Auto-update country to the correct one
        setCountry(detected);
      }
    } else {
      setDetected(null);
    }
  };

  const generate = async () => {
    if (!university.trim() || !program.trim()) return;
    setLoading(true); setCountryNote(''); setResolved('');
    try {
      const data = await aiAPI.generateSop(profile, university, program, country);
      setResult(data.outline || '');
      setResolved(data.resolved_country || country);
      setCountryNote(data.country_note || '');
      // Update country selector to what backend resolved
      if (data.resolved_country && data.resolved_country !== country) {
        setCountry(data.resolved_country);
      }
    } catch {
      setResult('SOP generation failed. Please check your API configuration.');
    } finally {
      setLoading(false);
    }
  };

  const cleanResult = result.replace(/\*\*\*/g, '').replace(/\*\*/g, '').replace(/\*/g, '');
  const copy = () => navigator.clipboard.writeText(cleanResult).catch(() => {});

  const allCountries = [...new Set([
    ...profileCountries,
    ...Object.values(UNI_COUNTRY_HINTS),
    ...COUNTRIES,
  ])].sort((a, b) => {
    // Profile countries first
    if (profileCountries.includes(a) && !profileCountries.includes(b)) return -1;
    if (!profileCountries.includes(a) && profileCountries.includes(b)) return 1;
    return a.localeCompare(b);
  });

  return (
    <div className="space-y-4">
      <div className="card p-5 space-y-4">
        <div className="flex items-center gap-2 mb-1">
          <BookOpen className="w-4 h-4 text-lavender" />
          <h2 className="font-bold text-text">Statement of Purpose Builder</h2>
        </div>
        <p className="text-sm text-muted">
          Country auto-detected from university name. SOP tone and structure tailored to that country's application style.
        </p>
        <div className="grid sm:grid-cols-2 gap-3">
          <div>
            <label className="text-xs font-semibold text-muted block mb-1">Target University</label>
            <input value={university} onChange={e => handleUniChange(e.target.value)}
              placeholder="e.g. IE University, Oxford, MIT"
              className="input-field" />
            {detectedCountry && (
              <p className="text-[11px] text-teal-600 mt-1 flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3" /> Detected: {detectedCountry}
              </p>
            )}
          </div>
          <div>
            <label className="text-xs font-semibold text-muted block mb-1">Program / Course</label>
            <input value={program} onChange={e => setProgram(e.target.value)}
              placeholder="e.g. MSc Data Science"
              className="input-field" />
          </div>
        </div>
        <div>
          <label className="text-xs font-semibold text-muted block mb-1">Country of Study</label>
          <select value={country} onChange={e => setCountry(e.target.value)} className="input-field text-sm py-2 pr-8">
            <option value="">Select country…</option>
            {allCountries.map(c => (
              <option key={c} value={c}>{c}{profileCountries.includes(c) ? ' ★' : ''}</option>
            ))}
          </select>
          {country && (
            <p className="text-[11px] text-lavender mt-1">
              SOP tailored to {country} application standards.
            </p>
          )}
        </div>
        <button onClick={generate} disabled={loading || !university.trim() || !program.trim()}
          className="btn-primary px-5 py-2.5 gap-2 w-full justify-center disabled:opacity-60">
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <BookOpen className="w-4 h-4" />}
          {loading ? 'Generating personalised SOP outline…' : 'Generate My SOP Outline'}
        </button>
      </div>

      {countryNote && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-3 flex items-start gap-2.5">
          <AlertTriangle className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
          <p className="text-xs text-amber-800">{countryNote}</p>
        </div>
      )}

      {result && (
        <div className="card p-5">
          <div className="flex items-center justify-between mb-3 flex-wrap gap-2">
            <div>
              <h3 className="font-bold text-text">SOP Outline — {university}</h3>
              <p className="text-xs text-muted mt-0.5">
                {program} · {resolvedCountry || country} style
              </p>
            </div>
            <button onClick={copy} className="btn-ghost text-xs py-1.5 px-3 flex items-center gap-1.5">
              <Download className="w-3.5 h-3.5" /> Copy Plain Text
            </button>
          </div>
          <div className="text-sm text-textSoft leading-relaxed bg-surfaceAlt rounded-xl p-5">
            {renderMd(cleanResult)}
          </div>
          <p className="text-xs text-muted mt-3 flex items-center gap-1.5">
            <Info className="w-3.5 h-3.5" />
            Framework based on your actual profile. Fill in sections marked [Add your own: ...] with your personal details.
          </p>
        </div>
      )}
    </div>
  );
}
