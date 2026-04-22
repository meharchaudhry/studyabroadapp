import { useState, useEffect, useRef } from 'react';
import { visaAPI } from '../api/visa';
import {
  FileCheck, Send, Bot, User, Sparkles,
  RefreshCw, Globe, ChevronDown,
} from 'lucide-react';

const COUNTRIES = [
  'General','USA','UK','Canada','Australia','Germany','France','Netherlands',
  'Ireland','Singapore','Japan','Sweden','Norway','Denmark','Finland',
  'New Zealand','UAE','Portugal','Italy','Spain','South Korea','Switzerland',
];

const SUGGESTED_QUESTIONS = {
  General:   [
    'What documents do I need for a European student visa?',
    'Do my parents need to be earning or can I use savings?',
    'Compare tuition fees across European countries',
    'Which country is best for Indian CS students?',
  ],
  UK:        [
    'What is the 28-day rule for UK visa funds?',
    'How many hours can I work on a UK student visa?',
    'What is the Immigration Health Surcharge?',
    'What is the Graduate Route visa?',
  ],
  USA:       [
    'What is OPT and STEM OPT extension?',
    'How do I get an I-20 form?',
    'What financial proof do I need for an F-1 visa?',
    'What is the SEVIS fee?',
  ],
  Canada:    [
    'What is a GIC for Canada study permit?',
    'What IELTS score do I need for Canada?',
    'Can I work while studying in Canada?',
    'What is the PGWP?',
  ],
  Germany:   [
    'What is the Blocked Account for Germany?',
    'What is APS and do Indian students need it?',
    'Do I need German language skills for a student visa?',
    'How much does it cost to study in Germany?',
  ],
  Australia: [
    'How much savings do I need for an Australian student visa?',
    'What is the GTE requirement?',
    'Can I bring my family to Australia on a student visa?',
    'What is the Subclass 485 visa?',
  ],
  default:   [
    'What documents do I need for a student visa?',
    'Do my parents need to earn or can I use savings?',
    'How long does visa processing take?',
    'Can I work while studying?',
  ],
};

const TOPIC_CHIPS = [
  { label: '🛂 Visa Docs', q: 'What are all the documents I need?' },
  { label: '💰 Financial Proof', q: 'Can I use savings or do my parents need to be earning?' },
  { label: '🏠 Housing', q: 'How do I find student accommodation?' },
  { label: '💼 Jobs', q: 'Can I work while studying and what post-study work options are available?' },
  { label: '🎓 Scholarships', q: 'What scholarships are available for Indian students?' },
  { label: '⏱️ Processing Time', q: 'How long does the visa process take from start to finish?' },
  { label: '💳 Total Cost', q: 'What is the total cost including tuition and living expenses?' },
];

const QUICK_COUNTRIES = ['General','UK','USA','Canada','Australia','Germany','France','Netherlands'];

function makeSessionId(c) {
  return `visa-${c}-${Date.now()}`;
}

function stripInlineSources(text) {
  return text
    .replace(/\(Source:\s*[^)]+\)/gi, '')
    .replace(/\[Source:\s*[^\]]+\]/gi, '')
    .replace(/According to [a-z0-9_\-]+\.(md|txt|pdf),?\s*/gi, '')
    .replace(/\s{2,}/g, ' ')
    .trim();
}

// Markdown-lite renderer with table support
function renderAnswer(text) {
  if (!text) return null;
  const str = typeof text === 'string' ? stripInlineSources(text) : JSON.stringify(text);
  const lines = str.split('\n');
  const elements = [];
  let tableBuffer = [];

  const flushTable = (key) => {
    if (tableBuffer.length < 2) { tableBuffer = []; return; }
    const cols = tableBuffer[0].split('|').filter(c => c.trim()).map(c => c.trim());
    const bodyRows = tableBuffer.slice(2).map(r =>
      r.split('|').filter(c => c.trim() !== undefined).map(c => c.trim())
    ).filter(r => r.length > 0);
    elements.push(
      <div key={key} className="overflow-x-auto my-2 rounded-lg border border-surfaceBorder text-xs">
        <table className="w-full min-w-full">
          <thead className="bg-lavendLight">
            <tr>{cols.map((c, i) => <th key={i} className="px-3 py-2 text-left font-semibold text-lavender whitespace-nowrap">{c}</th>)}</tr>
          </thead>
          <tbody>
            {bodyRows.map((r, ri) => (
              <tr key={ri} className={ri % 2 === 0 ? 'bg-white' : 'bg-surfaceAlt'}>
                {r.slice(0, cols.length).map((c, ci) => (
                  <td key={ci} className="px-3 py-1.5 text-textSoft">{c}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
    tableBuffer = [];
  };

  lines.forEach((line, i) => {
    if (line.trim().startsWith('|')) {
      tableBuffer.push(line);
      return;
    }
    if (tableBuffer.length > 0) flushTable(`t${i}`);

    const bold = line.split(/(\*\*[^*]+\*\*)/g).map((part, j) =>
      part.startsWith('**') && part.endsWith('**')
        ? <strong key={j}>{part.slice(2, -2)}</strong>
        : part
    );

    if (line.startsWith('### ')) {
      elements.push(<h4 key={i} className="font-bold text-text mt-3 mb-1 text-sm">{line.slice(4)}</h4>);
    } else if (line.startsWith('## ')) {
      elements.push(<h3 key={i} className="font-semibold text-text mt-4 mb-1">{line.slice(3)}</h3>);
    } else if (line.trimStart().match(/^[-•]\s/)) {
      elements.push(<li key={i} className="ml-4 list-disc leading-snug">{bold}</li>);
    } else if (line.match(/^\d+\.\s/)) {
      elements.push(<li key={i} className="ml-4 list-decimal leading-snug">{bold}</li>);
    } else if (line.trim() === '' || line.trim() === '---') {
      elements.push(<br key={i} />);
    } else {
      elements.push(<p key={i} className="leading-relaxed">{bold}</p>);
    }
  });
  if (tableBuffer.length > 0) flushTable('tf');
  return elements;
}

export default function VisaChat() {
  const [country, setCountry]           = useState('UK');
  const [sessionId, setSessionId]       = useState(() => makeSessionId('UK'));
  const [messages, setMessages]         = useState([{
    role: 'bot',
    text: "Hi! I'm your Study Abroad AI Assistant 🎓\n\nI can answer **any** question about student visas, documents, financial proof, housing, jobs, scholarships, or studying abroad — for any country.\n\nSelect a country above or just ask your question!",
  }]);
  const [input, setInput]               = useState('');
  const [chatLoading, setChatLoading]   = useState(false);
  const [showMore, setShowMore]         = useState(false);
  const messagesEndRef                  = useRef(null);
  const inputRef                        = useRef(null);

  const suggestions = SUGGESTED_QUESTIONS[country] || SUGGESTED_QUESTIONS.default;

  useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);

  const changeCountry = (c) => {
    setCountry(c);
    setShowMore(false);
    const sid = makeSessionId(c);
    setSessionId(sid);
    setMessages([{
      role: 'bot',
      text: c === 'General'
        ? "I'm in **General** mode — ask me about any country or compare across countries!"
        : `Switched to **${c}**. Ask me anything about the ${c} student visa, documents, housing, or jobs!`,
    }]);
    inputRef.current?.focus();
  };

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
        text: 'Gemini is experiencing high demand right now. Please wait a moment and try again.',
      }]);
    } finally {
      setChatLoading(false);
      inputRef.current?.focus();
    }
  };

  const isMoreSelected = !QUICK_COUNTRIES.includes(country);

  return (
    <div className="animate-fade-in flex flex-col gap-4">
      {/* Header */}
      <div className="page-header">
        <div className="page-icon bg-lavendLight">
          <FileCheck className="w-5 h-5 text-lavender" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-text">Visa Assistant</h1>
          <p className="text-muted text-sm mt-0.5">
            Visa requirements · Jobs · Housing · Scholarships
          </p>
        </div>
      </div>

      {/* Country selector */}
      <div className="card p-3">
        <div className="flex items-center gap-2 flex-wrap">
          <div className="flex items-center gap-1.5 text-xs font-bold text-muted uppercase tracking-wide mr-1">
            <Globe className="w-3.5 h-3.5" /> Country:
          </div>
          {QUICK_COUNTRIES.map(c => (
            <button key={c} onClick={() => changeCountry(c)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all ${
                country === c
                  ? 'bg-lavender text-white border-lavender shadow-sm'
                  : 'bg-surfaceAlt text-textSoft border-surfaceBorder hover:border-lavender hover:text-lavender'
              }`}>{c}</button>
          ))}
          <div className="relative">
            <button onClick={() => setShowMore(v => !v)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all flex items-center gap-1 ${
                isMoreSelected
                  ? 'bg-lavender text-white border-lavender'
                  : 'bg-surfaceAlt text-textSoft border-surfaceBorder hover:border-lavender hover:text-lavender'
              }`}>
              {isMoreSelected ? country : 'More ▾'}
              <ChevronDown className={`w-3 h-3 transition-transform ${showMore ? 'rotate-180' : ''}`} />
            </button>
            {showMore && (
              <div className="absolute top-full left-0 mt-1 z-50 bg-white rounded-xl shadow-lg border border-surfaceBorder p-2 grid grid-cols-3 gap-1 w-60">
                {COUNTRIES.filter(c => !QUICK_COUNTRIES.includes(c)).map(c => (
                  <button key={c} onClick={() => changeCountry(c)}
                    className={`px-2 py-1.5 rounded-lg text-xs font-medium text-left transition-all ${
                      country === c ? 'bg-lavender text-white' : 'hover:bg-lavendLight text-textSoft hover:text-lavender'
                    }`}>{c}</button>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Full-width chat */}
      <div className="card flex flex-col" style={{ height: '68vh', minHeight: '500px' }}>
        {/* Chat header */}
        <div className="px-4 py-3 border-b border-surfaceBorder flex items-center justify-between flex-shrink-0">
          <div className="flex items-center gap-2.5">
            <div className="relative">
              <div className="w-8 h-8 bg-lavendLight rounded-xl flex items-center justify-center">
                <Bot className="w-4 h-4 text-lavender" />
              </div>
              <span className="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 bg-teal-400 rounded-full border-2 border-white" />
            </div>
            <div>
              <p className="text-sm font-bold text-text">PathPilot Visa Assistant</p>
              <p className="text-[11px] text-muted">{country} · Visa guidance</p>
            </div>
          </div>
          <button onClick={() => changeCountry(country)} title="New conversation"
            className="p-1.5 rounded-lg text-muted hover:text-lavender hover:bg-surfaceAlt transition-colors">
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Topic chips */}
        <div className="px-4 py-2.5 border-b border-surfaceBorder flex gap-1.5 flex-wrap flex-shrink-0 bg-surfaceAlt/30">
          {TOPIC_CHIPS.map((chip, i) => (
            <button key={i} onClick={() => sendMessage(chip.q)} disabled={chatLoading}
              className="text-[11px] text-textSoft px-2.5 py-1 rounded-lg hover:bg-lavendLight hover:text-lavender transition-colors border border-surfaceBorder hover:border-lavender/40 bg-white disabled:opacity-50">
              {chip.label}
            </button>
          ))}
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((msg, i) => (
            <div key={i} className={`flex gap-2.5 ${msg.role === 'user' ? 'justify-end' : ''}`}>
              {msg.role === 'bot' && (
                <div className="w-7 h-7 bg-lavendLight rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                  <Bot className="w-3.5 h-3.5 text-lavender" />
                </div>
              )}
              <div className={`rounded-2xl px-4 py-3 text-sm ${
                msg.role === 'user'
                  ? 'bg-lavender text-white rounded-tr-sm max-w-[70%]'
                  : 'bg-surfaceAlt text-text rounded-tl-sm max-w-[92%] w-full'
              }`}>
                <div className="leading-relaxed space-y-1">
                  {renderAnswer(msg.text)}
                </div>
                {/* Sources */}
                {msg.sources?.length > 0 && (
                  <div className="mt-3 pt-2 border-t border-surfaceBorder/40 flex flex-wrap gap-1 items-center">
                    <span className="text-[10px] text-muted font-medium">Sources:</span>
                    {[...new Map(msg.sources.map(s => [s.doc, s])).values()].slice(0, 5).map((s, j) => (
                      <span key={j} className="inline-flex items-center gap-0.5 px-1.5 py-0.5 bg-lavendLight text-lavender rounded text-[10px] font-medium">
                        📄 {s.doc}
                      </span>
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
                      <span key={k} className="px-1.5 py-0.5 bg-teal-50 text-teal-700 rounded text-[10px] font-medium">
                        {k}: {typeof v === 'number' ? (v * 100).toFixed(0) : v}%
                      </span>
                    ))}
                  </div>
                )}
              </div>
              {msg.role === 'user' && (
                <div className="w-7 h-7 bg-lavender rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                  <User className="w-3.5 h-3.5 text-white" />
                </div>
              )}
            </div>
          ))}

          {chatLoading && (
            <div className="flex gap-2.5">
              <div className="w-7 h-7 bg-lavendLight rounded-full flex items-center justify-center">
                <Bot className="w-3.5 h-3.5 text-lavender" />
              </div>
              <div className="bg-surfaceAlt rounded-2xl rounded-tl-sm px-4 py-3">
                <div className="flex gap-1 items-center">
                  {[0, 0.15, 0.3].map((d, i) => (
                    <div key={i} className="w-2 h-2 bg-lavender rounded-full animate-bounce"
                      style={{ animationDelay: `${d}s` }} />
                  ))}
                  <span className="text-[10px] text-muted ml-2">Searching 104 knowledge docs…</span>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Suggested questions (first message only) */}
        {messages.length <= 1 && !chatLoading && (
          <div className="px-4 pb-2 flex gap-2 flex-wrap flex-shrink-0">
            {suggestions.map((q, i) => (
              <button key={i} onClick={() => sendMessage(q)}
                className="text-[11px] bg-lavendLight text-lavender px-2.5 py-1.5 rounded-lg hover:bg-lavender hover:text-white transition-colors border border-lavender/20 flex items-center gap-1">
                <Sparkles className="w-2.5 h-2.5 flex-shrink-0" /> {q}
              </button>
            ))}
          </div>
        )}

        {/* Input */}
        <div className="p-3 border-t border-surfaceBorder flex gap-2 flex-shrink-0">
          <input
            ref={inputRef}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && !e.shiftKey && sendMessage()}
            placeholder={
              country === 'General'
                ? 'Ask about any visa, housing, jobs, scholarships…'
                : `Ask about ${country} visa, documents, housing, jobs…`
            }
            className="input-field py-2.5 text-sm flex-1"
          />
          <button onClick={() => sendMessage()} disabled={chatLoading || !input.trim()}
            className="btn-primary px-4 py-2.5 disabled:opacity-50">
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
