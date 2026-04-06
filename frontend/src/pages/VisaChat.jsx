import { useState, useEffect, useRef } from 'react';
import { visaAPI } from '../api/visa';
import { FileCheck, CheckSquare, Square, ChevronDown, Send, Bot, User, Gauge, ExternalLink } from 'lucide-react';

const COUNTRIES = ['USA','UK','Germany','France','Netherlands','Australia','Singapore','HongKong','Spain','Switzerland','Finland'];
const CATEGORY_COLORS = {
  'Admission':   'bg-lavendLight text-lavender',
  'Application': 'bg-skyLight text-blue-600',
  'Identity':    'bg-mintLight text-teal-600',
  'Financial':   'bg-amberLight text-amber-700',
  'Academic':    'bg-peachLight text-orange-600',
  'Health':      'bg-roseLight text-rose',
  'ATAS':        'bg-lavendLight text-lavender',
  'Tuberculosis':'bg-roseLight text-rose',
  'Criminal':    'bg-amberLight text-amber-700',
  'Interview':   'bg-skyLight text-blue-600',
  'Other':       'bg-surfaceAlt text-textSoft',
};

export default function VisaChat() {
  const [country, setCountry] = useState('UK');
  const [checklist, setChecklist] = useState(null);
  const [checked, setChecked] = useState({});
  const [expandedCats, setExpandedCats] = useState({});
  const [messages, setMessages] = useState([{ role: 'bot', text: 'Hello! I\'m your Visa Assistant. Select a country above and ask me anything about student visa requirements.' }]);
  const [input, setInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [lisLoading, setLisLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const fetchChecklist = async () => {
    setLisLoading(true);
    setChecked({});
    try {
      const data = await visaAPI.getChecklist(country);
      setChecklist(data);
      // Expand first category by default
      if (data.checklist?.length) {
        const firstCat = data.checklist[0].category;
        setExpandedCats({ [firstCat]: true });
      }
    } catch {
      setChecklist(null);
    } finally {
      setLisLoading(false);
    }
  };

  useEffect(() => { fetchChecklist(); }, [country]);
  useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);

  const toggleCheck = (id) => setChecked(prev => ({ ...prev, [id]: !prev[id] }));
  const toggleCat = (cat) => setExpandedCats(prev => ({ ...prev, [cat]: !prev[cat] }));

  const sendMessage = async () => {
    if (!input.trim() || chatLoading) return;
    const q = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', text: q }]);
    setChatLoading(true);
    try {
      const res = await visaAPI.query(country, q);
      setMessages(prev => [...prev, { role: 'bot', text: res.answer, metrics: res.metrics, sources: res.sources }]);
    } catch {
      setMessages(prev => [...prev, { role: 'bot', text: 'Sorry, the AI assistant is unavailable. Please check your Gemini API key.' }]);
    } finally {
      setChatLoading(false);
    }
  };

  // Group checklist by category
  const grouped = (checklist?.checklist || []).reduce((acc, item) => {
    (acc[item.category] = acc[item.category] || []).push(item);
    return acc;
  }, {});
  const checkedCount = Object.values(checked).filter(Boolean).length;
  const totalItems = checklist?.checklist?.length || 0;
  const progress = totalItems ? Math.round((checkedCount / totalItems) * 100) : 0;

  return (
    <div className="animate-fade-in space-y-6">
      <div className="page-header">
        <div className="page-icon bg-lavendLight"><FileCheck className="w-5 h-5 text-lavender"/></div>
        <div>
          <h1 className="text-2xl font-bold text-text">Visa Guide</h1>
          <p className="text-muted text-sm mt-0.5">Real visa checklists for Indian students + AI assistant</p>
        </div>
      </div>

      {/* Country selector */}
      <div className="card p-4 flex flex-wrap gap-2 items-center">
        <span className="text-sm font-semibold text-text mr-1">Select country:</span>
        {COUNTRIES.map(c => (
          <button key={c} onClick={() => setCountry(c)}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all ${
              country === c ? 'bg-lavender text-white border-lavender' : 'bg-surfaceAlt text-textSoft border-surfaceBorder hover:border-lavender hover:text-lavender'
            }`}>{c}</button>
        ))}
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        {/* ── Checklist ── */}
        <div className="space-y-4">
          {lisLoading ? (
            <div className="card p-10 flex justify-center"><div className="w-7 h-7 border-2 border-lavender/30 border-t-lavender rounded-full animate-spin"/></div>
          ) : !checklist ? (
            <div className="card p-8 text-center text-muted">No data for this country yet.</div>
          ) : (
            <>
              {/* Visa info header */}
              <div className="card p-5">
                <h2 className="font-bold text-text mb-1">{checklist.visa_type}</h2>
                <div className="grid grid-cols-2 gap-3 mt-3 text-xs">
                  <div className="bg-surfaceAlt rounded-lg p-2">
                    <p className="text-muted mb-0.5">Processing Time</p>
                    <p className="font-semibold text-text">{checklist.processing_time}</p>
                  </div>
                  {checklist.visa_fee_inr > 0 && (
                    <div className="bg-surfaceAlt rounded-lg p-2">
                      <p className="text-muted mb-0.5">Visa Fee</p>
                      <p className="font-semibold text-teal-600">₹{checklist.visa_fee_inr?.toLocaleString('en-IN')}</p>
                    </div>
                  )}
                </div>
                {/* Progress */}
                <div className="mt-4">
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-textSoft font-medium">Documents ready</span>
                    <span className="text-lavender font-bold">{checkedCount}/{totalItems}</span>
                  </div>
                  <div className="bg-lavendLight rounded-full h-2 overflow-hidden">
                    <div className="bg-lavender h-2 rounded-full transition-all duration-500" style={{width:`${progress}%`}}/>
                  </div>
                </div>
                <a href={checklist.official_link} target="_blank" rel="noreferrer"
                  className="btn-ghost mt-3 text-xs py-1.5">
                  <ExternalLink className="w-3.5 h-3.5"/> Official Visa Website
                </a>
              </div>

              {/* Checklist groups */}
              {Object.entries(grouped).map(([cat, items]) => (
                <div key={cat} className="card overflow-hidden">
                  <button className="w-full flex items-center justify-between p-4 hover:bg-surfaceAlt transition-colors"
                    onClick={() => toggleCat(cat)}>
                    <div className="flex items-center gap-2">
                      <span className={`badge text-[10px] ${CATEGORY_COLORS[cat]||'bg-surfaceAlt text-muted'}`}>{cat}</span>
                      <span className="text-xs text-muted">{items.filter(i=>checked[i.id]).length}/{items.length}</span>
                    </div>
                    <ChevronDown className={`w-4 h-4 text-muted transition-transform ${expandedCats[cat]?'rotate-180':''}`}/>
                  </button>
                  {expandedCats[cat] && (
                    <div className="px-4 pb-4 space-y-1 divider pt-2">
                      {items.map(item => (
                        <label key={item.id} className="checklist-item select-none" onClick={()=>toggleCheck(item.id)}>
                          {checked[item.id]
                            ? <CheckSquare className="w-4 h-4 text-lavender flex-shrink-0 mt-0.5"/>
                            : <Square className="w-4 h-4 text-muted flex-shrink-0 mt-0.5"/>}
                          <span className={`text-sm ${checked[item.id]?'line-through text-muted':'text-text'}`}>{item.item}</span>
                        </label>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </>
          )}
        </div>

        {/* ── Chatbot ── */}
        <div className="card flex flex-col h-[600px]">
          <div className="p-4 border-b border-surfaceBorder flex items-center gap-2">
            <div className="w-7 h-7 bg-lavendLight rounded-lg flex items-center justify-center"><Bot className="w-4 h-4 text-lavender"/></div>
            <div>
              <h3 className="text-sm font-bold text-text">Visa AI Assistant</h3>
              <p className="text-[10px] text-muted">{country} visa specialist</p>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {messages.map((msg, i) => (
              <div key={i} className={`flex gap-2 ${msg.role==='user'?'justify-end':''}`}>
                {msg.role==='bot' && <div className="w-6 h-6 bg-lavendLight rounded-full flex items-center justify-center flex-shrink-0 mt-0.5"><Bot className="w-3.5 h-3.5 text-lavender"/></div>}
                <div className={`max-w-[80%] rounded-2xl px-4 py-2.5 text-sm ${
                  msg.role==='user' ? 'bg-lavender text-white rounded-tr-sm' : 'bg-surfaceAlt text-text rounded-tl-sm'
                }`}>
                  <p className="leading-relaxed">{msg.text}</p>
                  {msg.metrics && (
                    <div className="flex gap-2 mt-2 flex-wrap">
                      {Object.entries(msg.metrics).map(([k,v]) => (
                        <span key={k} className="badge badge-lavender text-[10px]">
                          <Gauge className="w-2.5 h-2.5"/>{k.replace(/_/g,' ')}: {typeof v==='number'?v.toFixed(2):v}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
                {msg.role==='user' && <div className="w-6 h-6 bg-lavender rounded-full flex items-center justify-center flex-shrink-0 mt-0.5"><User className="w-3.5 h-3.5 text-white"/></div>}
              </div>
            ))}
            {chatLoading && (
              <div className="flex gap-2">
                <div className="w-6 h-6 bg-lavendLight rounded-full flex items-center justify-center"><Bot className="w-3.5 h-3.5 text-lavender"/></div>
                <div className="bg-surfaceAlt rounded-2xl rounded-tl-sm px-4 py-3">
                  <div className="flex gap-1"><div className="w-1.5 h-1.5 bg-lavender rounded-full animate-bounce [animation-delay:-0.3s]"/><div className="w-1.5 h-1.5 bg-lavender rounded-full animate-bounce [animation-delay:-0.15s]"/><div className="w-1.5 h-1.5 bg-lavender rounded-full animate-bounce"/></div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef}/>
          </div>

          <div className="p-3 border-t border-surfaceBorder flex gap-2">
            <input value={input} onChange={e=>setInput(e.target.value)} onKeyDown={e=>e.key==='Enter'&&sendMessage()}
              placeholder={`Ask about ${country} student visa…`}
              className="input-field py-2 text-sm flex-1"/>
            <button onClick={sendMessage} disabled={chatLoading||!input.trim()} className="btn-primary px-3 py-2">
              <Send className="w-4 h-4"/>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
