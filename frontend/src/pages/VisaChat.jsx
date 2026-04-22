import { useState, useEffect, useRef } from 'react';
import { visaAPI } from '../api/visa';
import { aiAPI } from '../api/ai';
import { authAPI } from '../api/auth';
import { Link } from 'react-router-dom';
import {
  FileCheck, CheckSquare, Square, ChevronDown, Send, Bot, User,
  Gauge, ExternalLink, Sparkles, RefreshCw, Zap, CheckCircle2, Loader2,
} from 'lucide-react';

const SUGGESTED_QUESTIONS = {
  UK:          ['What is the 28-day rule for funds?', 'How many hours can I work on a UK student visa?', 'What is the Immigration Health Surcharge?'],
  USA:         ['What is OPT and STEM OPT extension?', 'How do I get an I-20 form?', 'What financial proof do I need for an F-1 visa?'],
  Canada:      ['What is a GIC for Canada study permit?', 'What IELTS score do I need for Canada?', 'Can I work while studying in Canada?'],
  Australia:   ['How much savings do I need for an Australian student visa?', 'What is the student visa processing time for Australia?', 'Can I bring my family to Australia?'],
  Germany:     ['Do I need to learn German for a student visa?', 'What is the Blocked Account for Germany?', 'What are the health insurance requirements for Germany?'],
  default:     ['What documents do I need for a student visa?', 'What is the IELTS score requirement?', 'How long does the visa processing take?'],
};

const CATEGORY_COLORS = {
  'Admission':    'bg-lavendLight text-lavender',
  'Application':  'bg-skyLight text-blue-600',
  'Identity':     'bg-mintLight text-teal-600',
  'Financial':    'bg-amberLight text-amber-700',
  'Academic':     'bg-peachLight text-orange-600',
  'Health':       'bg-roseLight text-rose',
  'ATAS':         'bg-lavendLight text-lavender',
  'Tuberculosis': 'bg-roseLight text-rose',
  'Criminal':     'bg-amberLight text-amber-700',
  'Interview':    'bg-skyLight text-blue-600',
  'Other':        'bg-surfaceAlt text-textSoft',
};

function makeSessionId(country) {
  return `visa-${country}-${Date.now()}`;
}

// Simple markdown-lite renderer: bold **text**, bullet - item
function renderAnswer(text) {
  if (!text) return null;
  const str = typeof text === 'string' ? text : JSON.stringify(text);
  return str.split('\n').map((line, i) => {
    const parts = line.split(/(\*\*[^*]+\*\*)/g).map((part, j) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={j}>{part.slice(2, -2)}</strong>;
      }
      return part;
    });
    // Bullet
    if (line.trimStart().startsWith('- ') || line.trimStart().startsWith('• ')) {
      return <li key={i} className="ml-4 list-disc">{parts}</li>;
    }
    if (line.match(/^\d+\.\s/)) {
      return <li key={i} className="ml-4 list-decimal">{parts}</li>;
    }
    if (line.trim() === '') return <br key={i} />;
    return <p key={i}>{parts}</p>;
  });
}

export default function VisaChat() {
  const [countries, setCountries]     = useState([]);
  const [country, setCountry]         = useState('UK');
  const [sessionId, setSessionId]     = useState(() => makeSessionId('UK'));
  const [checklist, setChecklist]     = useState(null);
  const [checked, setChecked]         = useState({});
  const [expandedCats, setExpandedCats] = useState({});
  const [messages, setMessages]       = useState([{
    role: 'bot',
    text: "Hello! I'm your Visa Assistant. Select a country and ask me anything about student visa requirements, documents, or the application process.",
  }]);
  const [input, setInput]             = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [lisLoading, setLisLoading]   = useState(false);
  const [aiChecklist, setAiChecklist] = useState(null);
  const [aiLoading, setAiLoading]     = useState(false);
  const [aiChecked, setAiChecked]     = useState({});
  const [userProfile, setUserProfile] = useState({});
  const messagesEndRef                = useRef(null);
  const inputRef                      = useRef(null);

  useEffect(() => {
    authAPI.getProfile().then(setUserProfile).catch(() => {});
    visaAPI.getCountries()
      .then((res) => {
        const fetched = Array.isArray(res?.countries) ? res.countries : [];
        if (!fetched.length) return;
        setCountries(fetched);
        if (!fetched.includes(country)) {
          setCountry(fetched[0]);
        }
      })
      .catch(() => {});
  }, []);

  const suggestions = SUGGESTED_QUESTIONS[country] || SUGGESTED_QUESTIONS.default;

  const fetchChecklist = async (c = country) => {
    setLisLoading(true);
    setChecked({});
    setAiChecklist(null);
    setAiChecked({});
    const sid = makeSessionId(c);
    setSessionId(sid);
    setMessages([{
      role: 'bot',
      text: `I'm now your ${c} Visa Assistant. Ask me anything about the ${c} student visa process for Indian students!`,
    }]);
    try {
      const data = await visaAPI.getChecklist(c);
      setChecklist(data);
      if (data.checklist?.length) {
        setExpandedCats({ [data.checklist[0].category]: true });
      }

      try {
        const saved = await visaAPI.getSavedChecklist(c, 'official');
        setChecked(saved?.checked || {});
      } catch {
        setChecked({});
      }

      try {
        const savedAi = await visaAPI.getSavedChecklist(c, 'ai');
        if (savedAi?.items?.length) {
          setAiChecklist({ checklist: savedAi.items });
          setAiChecked(savedAi.checked || {});
        }
      } catch {
        setAiChecklist(null);
        setAiChecked({});
      }
    } catch {
      setChecklist(null);
    } finally {
      setLisLoading(false);
    }
  };

  useEffect(() => { fetchChecklist(country); }, [country]);
  useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);

  const saveOfficialChecklist = async (nextChecked, activeChecklist = checklist, activeCountry = country) => {
    if (!activeChecklist?.checklist?.length) return;
    try {
      await visaAPI.saveChecklist({
        country: activeCountry,
        checklist_type: 'official',
        title: activeChecklist.visa_type,
        metadata: {
          official_link: activeChecklist.official_link,
          processing_time: activeChecklist.processing_time,
          visa_fee_inr: activeChecklist.visa_fee_inr,
          source_doc: activeChecklist.source_doc,
        },
        items: activeChecklist.checklist,
        checked: nextChecked,
      });
    } catch {
      // Keep UI responsive even if save fails.
    }
  };

  const toggleCheck = (id) => {
    setChecked(prev => {
      const next = { ...prev, [id]: !prev[id] };
      saveOfficialChecklist(next);
      return next;
    });
  };
  const toggleCat   = (cat) => setExpandedCats(prev => ({ ...prev, [cat]: !prev[cat] }));

  const sendMessage = async (q = input.trim()) => {
    if (!q || chatLoading) return;
    setInput('');
    setMessages(prev => [...prev, { role: 'user', text: q }]);
    setChatLoading(true);
    try {
      const res = await visaAPI.query(country, q, sessionId);
      setMessages(prev => [...prev, {
        role: 'bot',
        text: res.answer,
        metrics: res.metrics,
        sources: res.sources,
      }]);
    } catch {
      setMessages(prev => [...prev, {
        role: 'bot',
        text: 'Sorry, the AI assistant is currently unavailable. Please ensure the Gemini API key is configured.',
      }]);
    } finally {
      setChatLoading(false);
      inputRef.current?.focus();
    }
  };

  const generateAiChecklist = async () => {
    setAiLoading(true);
    setAiChecklist(null);
    setAiChecked({});
    try {
      const data = await aiAPI.generateChecklist(country, userProfile);
      setAiChecklist(data);
      await visaAPI.saveChecklist({
        country,
        checklist_type: 'ai',
        title: `AI Personalised Checklist (${country})`,
        metadata: { source: 'ai-generate-checklist' },
        items: data?.checklist || [],
        checked: {},
      });
    } catch {
      setAiChecklist({ error: true });
    } finally {
      setAiLoading(false);
    }
  };

  const toggleAiCheck = (id) => {
    setAiChecked(prev => {
      const next = { ...prev, [id]: !prev[id] };
      if (aiChecklist?.checklist?.length) {
        visaAPI.saveChecklist({
          country,
          checklist_type: 'ai',
          title: `AI Personalised Checklist (${country})`,
          metadata: { source: 'ai-generate-checklist' },
          items: aiChecklist.checklist,
          checked: next,
        }).catch(() => {});
      }
      return next;
    });
  };

  const grouped = (checklist?.checklist || []).reduce((acc, item) => {
    (acc[item.category] = acc[item.category] || []).push(item);
    return acc;
  }, {});
  const checkedCount = Object.values(checked).filter(Boolean).length;
  const totalItems   = checklist?.checklist?.length || 0;
  const progress     = totalItems ? Math.round((checkedCount / totalItems) * 100) : 0;

  return (
    <div className="animate-fade-in space-y-5">
      {/* Header */}
      <div className="page-header">
        <div className="page-icon bg-lavendLight"><FileCheck className="w-5 h-5 text-lavender" /></div>
        <div>
          <h1 className="text-2xl font-bold text-text">Visa Guide + AI Assistant</h1>
          <p className="text-muted text-sm mt-0.5">
            Document checklists · Hybrid RAG pipeline · 96.4% accuracy on standard queries
          </p>
        </div>
      </div>

      {/* Country selector */}
      <div className="card p-4 flex flex-wrap gap-2 items-center">
        <span className="text-xs font-bold text-muted uppercase tracking-wide mr-1">Country:</span>
        {(countries.length ? countries : [country]).map(c => (
          <button key={c} onClick={() => setCountry(c)}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all ${
              country === c
                ? 'bg-lavender text-white border-lavender shadow-sm'
                : 'bg-surfaceAlt text-textSoft border-surfaceBorder hover:border-lavender hover:text-lavender'
            }`}>{c}</button>
        ))}
      </div>

      <div className="grid lg:grid-cols-2 gap-5">
        {/* ── Checklist ── */}
        <div className="space-y-4">
          {lisLoading ? (
            <div className="card p-10 flex justify-center">
              <div className="w-7 h-7 border-2 border-lavender/30 border-t-lavender rounded-full animate-spin" />
            </div>
          ) : !checklist ? (
            <div className="card p-8 text-center text-muted">No checklist data for this country yet.</div>
          ) : (
            <>
              {/* Visa overview card */}
              <div className="card p-5">
                <h2 className="font-bold text-text mb-1">{checklist.visa_type}</h2>
                <div className="grid grid-cols-2 gap-3 mt-3 text-xs">
                  <div className="bg-surfaceAlt rounded-lg p-2.5">
                    <p className="text-muted mb-0.5">Processing Time</p>
                    <p className="font-semibold text-text">{checklist.processing_time}</p>
                  </div>
                  {checklist.visa_fee_inr > 0 && (
                    <div className="bg-surfaceAlt rounded-lg p-2.5">
                      <p className="text-muted mb-0.5">Visa Fee</p>
                      <p className="font-semibold text-teal-600">₹{checklist.visa_fee_inr?.toLocaleString('en-IN')}</p>
                    </div>
                  )}
                </div>
                {/* Progress */}
                <div className="mt-4">
                  <div className="flex justify-between text-xs mb-1.5">
                    <span className="text-textSoft font-medium">Documents ready</span>
                    <span className="text-lavender font-bold">{checkedCount}/{totalItems}</span>
                  </div>
                  <div className="bg-lavendLight rounded-full h-2 overflow-hidden">
                    <div className="bg-lavender h-2 rounded-full transition-all duration-500" style={{ width: `${progress}%` }} />
                  </div>
                  {progress === 100 && (
                    <p className="text-xs text-teal-600 font-semibold mt-1.5">🎉 All documents ready!</p>
                  )}
                </div>
                {checklist.official_link && (
                  <a href={checklist.official_link} target="_blank" rel="noreferrer"
                    className="btn-ghost mt-3 text-xs py-1.5">
                    <ExternalLink className="w-3.5 h-3.5" /> Official Visa Website
                  </a>
                )}
                {(checklist.overview_summary || checklist.overview_points?.length) && (
                  <div className="mt-4 p-3 rounded-lg bg-skyLight/40 border border-blue-100">
                    <p className="text-[11px] font-bold uppercase tracking-wide text-blue-700 mb-1">Overview</p>
                    {checklist.overview_summary && (
                      <p className="text-xs text-textSoft leading-relaxed">{checklist.overview_summary}</p>
                    )}
                    {checklist.overview_points?.length > 0 && (
                      <ul className="mt-2 space-y-1">
                        {checklist.overview_points.map((point, idx) => (
                          <li key={idx} className="text-xs text-textSoft leading-relaxed flex gap-2">
                            <span className="text-blue-600">•</span>
                            <span>{point}</span>
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                )}
                {checklist.official_guidance && (
                  <details className="mt-3 rounded-lg border border-surfaceBorder bg-surfaceAlt/60 p-2">
                    <summary className="text-xs font-medium text-textSoft cursor-pointer">Read source excerpt</summary>
                    <div className="mt-2 text-xs text-muted leading-relaxed whitespace-pre-line">
                      {checklist.official_guidance}
                    </div>
                  </details>
                )}
              </div>

              {/* Checklist groups */}
              {Object.entries(grouped).map(([cat, items]) => (
                <div key={cat} className="card overflow-hidden">
                  <button className="w-full flex items-center justify-between p-4 hover:bg-surfaceAlt transition-colors"
                    onClick={() => toggleCat(cat)}>
                    <div className="flex items-center gap-2">
                      <span className={`badge text-[10px] ${CATEGORY_COLORS[cat] || 'bg-surfaceAlt text-muted'}`}>{cat}</span>
                      <span className="text-xs text-muted">
                        {items.filter(i => checked[i.id]).length}/{items.length} done
                      </span>
                    </div>
                    <ChevronDown className={`w-4 h-4 text-muted transition-transform ${expandedCats[cat] ? 'rotate-180' : ''}`} />
                  </button>
                  {expandedCats[cat] && (
                    <div className="px-4 pb-4 space-y-1 border-t border-surfaceBorder pt-3">
                      {items.map(item => (
                        <label key={item.id} className="flex items-start gap-3 p-2 rounded-lg hover:bg-surfaceAlt cursor-pointer select-none"
                          onClick={() => toggleCheck(item.id)}>
                          {checked[item.id]
                            ? <CheckSquare className="w-4 h-4 text-lavender flex-shrink-0 mt-0.5" />
                            : <Square className="w-4 h-4 text-muted flex-shrink-0 mt-0.5" />}
                          <span className={`text-sm leading-snug ${checked[item.id] ? 'line-through text-muted' : 'text-text'}`}>
                            {item.item}
                          </span>
                        </label>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </>
          )}

          {/* ── AI Personalised Checklist ── */}
          <div className="card p-4 border-lavender/20 bg-gradient-to-br from-lavendLight/30 to-white">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 bg-lavender rounded-lg flex items-center justify-center">
                  <Zap className="w-3.5 h-3.5 text-white" />
                </div>
                <div>
                  <p className="text-sm font-bold text-text">AI Personalised Checklist</p>
                  <p className="text-[10px] text-muted">Claude analyses your profile and tailors the list</p>
                </div>
              </div>
              <Link to="/ai-coach" className="text-[10px] text-lavender font-semibold hover:underline">Full AI Coach →</Link>
            </div>

            {!aiChecklist && (
              <button onClick={generateAiChecklist} disabled={aiLoading}
                className="btn-primary w-full py-2.5 gap-2 justify-center text-sm disabled:opacity-60">
                {aiLoading
                  ? <><Loader2 className="w-4 h-4 animate-spin" /> Generating for {country}…</>
                  : <><Zap className="w-4 h-4" /> Generate My {country} Checklist</>}
              </button>
            )}

            {aiChecklist && !aiChecklist.error && (
              <>
                <div className="text-xs text-muted mb-2">
                  {Object.values(aiChecked).filter(Boolean).length}/{aiChecklist.checklist?.length || 0} documents ready ·{' '}
                  <button onClick={() => { setAiChecklist(null); setAiChecked({}); }}
                    className="text-lavender hover:underline">Regenerate</button>
                </div>
                <div className="space-y-1 max-h-64 overflow-y-auto pr-1">
                  {(aiChecklist.checklist || []).map(item => (
                    <div key={item.id}
                      className="flex items-start gap-2 p-2 rounded-lg hover:bg-white cursor-pointer transition-colors group"
                      onClick={() => toggleAiCheck(item.id)}>
                      {aiChecked[item.id]
                        ? <CheckCircle2 className="w-4 h-4 text-teal-500 flex-shrink-0 mt-0.5" />
                        : <div className="w-4 h-4 rounded-full border-2 border-muted flex-shrink-0 mt-0.5 group-hover:border-lavender transition-colors" />}
                      <div className="flex-1 min-w-0">
                        <span className={`text-xs leading-snug ${aiChecked[item.id] ? 'line-through text-muted' : 'text-text'}`}>
                          {item.task}
                        </span>
                        {item.note && <p className="text-[10px] text-muted mt-0.5">{item.note}</p>}
                      </div>
                      <span className={`badge text-[9px] flex-shrink-0
                        ${item.priority === 'critical' ? 'bg-rose/10 text-rose' :
                          item.priority === 'high' ? 'bg-amberLight text-amber-700' : 'bg-skyLight text-blue-600'}`}>
                        {item.priority}
                      </span>
                    </div>
                  ))}
                </div>
              </>
            )}

            {aiChecklist?.error && (
              <p className="text-xs text-rose text-center py-2">Generation failed — check your API key.</p>
            )}
          </div>
        </div>

        {/* ── Chatbot ── */}
        <div className="card flex flex-col" style={{ height: '640px' }}>
          {/* Chat header */}
          <div className="p-4 border-b border-surfaceBorder flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 bg-lavendLight rounded-lg flex items-center justify-center">
                <Bot className="w-4 h-4 text-lavender" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-text">Visa AI Assistant</h3>
                <p className="text-[10px] text-muted">{country} · Hybrid RAG · Gemini 2.5 Flash</p>
              </div>
            </div>
            <button onClick={() => fetchChecklist(country)}
              className="text-muted hover:text-lavender transition-colors p-1.5 rounded-lg hover:bg-surfaceAlt"
              title="New conversation">
              <RefreshCw className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {messages.map((msg, i) => (
              <div key={i} className={`flex gap-2 ${msg.role === 'user' ? 'justify-end' : ''}`}>
                {msg.role === 'bot' && (
                  <div className="w-6 h-6 bg-lavendLight rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                    <Bot className="w-3.5 h-3.5 text-lavender" />
                  </div>
                )}
                <div className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm ${
                  msg.role === 'user'
                    ? 'bg-lavender text-white rounded-tr-sm'
                    : 'bg-surfaceAlt text-text rounded-tl-sm'
                }`}>
                  <div className="leading-relaxed space-y-1">
                    {renderAnswer(msg.text)}
                  </div>
                  {/* Sources */}
                  {msg.sources?.length > 0 && (
                    <div className="mt-2 pt-2 border-t border-surfaceBorder/50 flex flex-wrap gap-1">
                      <span className="text-[10px] text-muted">Sources:</span>
                      {[...new Map(msg.sources.map(s => [s.doc, s])).values(.map(s => (typeof s === 'string' ? s : s.doc)).filter(Boolean))].slice(0, 4).map((s, j) => (
                        <span key={j} className="badge badge-lavender text-[10px]">{s.doc}</span>
                      ))}
                    </div>
                  )}
                  {/* Metrics */}
                  {msg.metrics && (
                    <div className="mt-1.5 flex gap-1.5 flex-wrap">
                      {[
                        ['Precision', msg.metrics.contextual_precision],
                        ['Faithfulness', msg.metrics.faithfulness],
                        ['Relevancy', msg.metrics.answer_relevancy],
                      ].map(([k, v]) => v != null && (
                        <span key={k} className="badge bg-teal-50 text-teal-700 text-[10px] border-0">
                          {k}: {typeof v === 'number' ? (v * 100).toFixed(0) : v}%
                        </span>
                      ))}
                    </div>
                  )}
                </div>
                {msg.role === 'user' && (
                  <div className="w-6 h-6 bg-lavender rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                    <User className="w-3.5 h-3.5 text-white" />
                  </div>
                )}
              </div>
            ))}
            {chatLoading && (
              <div className="flex gap-2">
                <div className="w-6 h-6 bg-lavendLight rounded-full flex items-center justify-center">
                  <Bot className="w-3.5 h-3.5 text-lavender" />
                </div>
                <div className="bg-surfaceAlt rounded-2xl rounded-tl-sm px-4 py-3">
                  <div className="flex gap-1">
                    {[0, 0.15, 0.3].map((d, i) => (
                      <div key={i} className="w-1.5 h-1.5 bg-lavender rounded-full animate-bounce"
                        style={{ animationDelay: `${-d}s` }} />
                    ))}
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Suggested questions (only when chat is idle) */}
          {messages.length <= 1 && !chatLoading && (
            <div className="px-4 pb-2 flex gap-2 flex-wrap">
              {suggestions.map((q, i) => (
                <button key={i} onClick={() => sendMessage(q)}
                  className="text-[11px] bg-lavendLight text-lavender px-2.5 py-1.5 rounded-lg hover:bg-lavender hover:text-white transition-colors border border-lavender/20 flex items-center gap-1">
                  <Sparkles className="w-2.5 h-2.5" /> {q}
                </button>
              ))}
            </div>
          )}

          {/* Input */}
          <div className="p-3 border-t border-surfaceBorder flex gap-2">
            <input
              ref={inputRef}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && !e.shiftKey && sendMessage()}
              placeholder={`Ask about ${country} student visa…`}
              className="input-field py-2 text-sm flex-1"
            />
            <button onClick={() => sendMessage()} disabled={chatLoading || !input.trim()}
              className="btn-primary px-3 py-2 disabled:opacity-50">
              <Send className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
