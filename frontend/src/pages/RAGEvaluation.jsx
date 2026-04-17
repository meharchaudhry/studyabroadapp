import { useState } from 'react';
import { 
  Radar, 
  RadarChart, 
  PolarGrid, 
  PolarAngleAxis, 
  PolarRadiusAxis, 
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as ChartTooltip,
  Legend
} from 'recharts';
import { Shield, Target, Zap, Activity, Info, ChevronRight, Search, FileText } from 'lucide-react';

const evaluationData = [
  { metric: 'Faithfulness', Baseline: 0.65, Hybrid: 0.78, ReRanked: 0.92 },
  { metric: 'Answer Relevancy', Baseline: 0.70, Hybrid: 0.82, ReRanked: 0.88 },
  { metric: 'Context Precision', Baseline: 0.55, Hybrid: 0.75, ReRanked: 0.94 },
  { metric: 'Context Recall', Baseline: 0.62, Hybrid: 0.80, ReRanked: 0.86 },
];

const testSetResults = [
  { id: 1, question: "What is the post-study work visa for the UK?", status: "Pass", faithfulness: 0.95, relevancy: 0.90 },
  { id: 2, question: "Do I need block account for Germany?", status: "Pass", faithfulness: 0.92, relevancy: 0.88 },
  { id: 3, question: "What are the SDS requirements for Canada?", status: "Pass", faithfulness: 0.96, relevancy: 0.92 },
  { id: 4, question: "How much is the IHS fee for UK?", status: "Fail", faithfulness: 0.45, relevancy: 0.70, note: "Stale data referenced" },
  { id: 5, question: "Is IELTS mandatory for Norway?", status: "Pass", faithfulness: 0.88, relevancy: 0.85 },
];

export default function RAGEvaluation() {
  const [activeMetric, setActiveMetric] = useState(null);

  return (
    <div className="space-y-6 animate-fade-in pb-10">
      
      {/* ── Page Header ── */}
      <div className="page-header">
        <div className="page-icon bg-mintLight"><Activity className="w-5 h-5 text-mint"/></div>
        <div>
          <h1 className="text-2xl font-bold text-text">RAG Evaluation Dashboard</h1>
          <p className="text-muted text-sm mt-0.5">Automated quality metrics (RAGAS) for the Visa Assistant</p>
        </div>
      </div>

      {/* ── Scorecards ── */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: 'Faithfulness', value: '92%', icon: Shield, color: 'text-mint', bg: 'bg-mintLight' },
          { label: 'Answer Relevancy', value: '88%', icon: Target, color: 'text-lavender', bg: 'bg-lavendLight' },
          { label: 'Context Precision', value: '94%', icon: Zap, color: 'text-blue-600', bg: 'bg-skyLight' },
          { label: 'Context Recall', value: '86%', icon: Info, color: 'text-amber-600', bg: 'bg-amberLight' },
        ].map((s) => (
          <div key={s.label} className="card p-5 group hover:border-lavender/30 transition-all cursor-default">
            <div className="flex items-center justify-between mb-3">
              <div className={`p-2 rounded-xl ${s.bg} ${s.color}`}><s.icon className="w-5 h-5"/></div>
              <span className="text-[10px] font-bold text-mint uppercase tracking-wider">Experimental</span>
            </div>
            <div className="text-2xl font-black text-text mb-0.5">{s.value}</div>
            <div className="text-xs font-semibold text-textSoft">{s.label}</div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* ── Metric Comparison (Radar Chart) ── */}
        <div className="card p-6 min-h-[400px]">
          <div className="flex items-center justify-between mb-6">
            <h2 className="font-bold text-text">Pipeline Evolution</h2>
            <div className="flex gap-3 text-[10px] font-bold">
              <span className="flex items-center gap-1.5 text-rose"><div className="w-2 h-2 rounded-full bg-rose"/> Baseline</span>
              <span className="flex items-center gap-1.5 text-lavender"><div className="w-2 h-2 rounded-full bg-lavender"/> Hybrid</span>
              <span className="flex items-center gap-1.5 text-teal-600"><div className="w-2 h-2 rounded-full bg-teal-600"/> Re-Ranked</span>
            </div>
          </div>
          
          <div className="w-full h-80">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart cx="50%" cy="50%" outerRadius="80%" data={evaluationData}>
                <PolarGrid stroke="#e2e8f0" />
                <PolarAngleAxis dataKey="metric" tick={{ fill: '#64748b', fontSize: 11, fontWeight: 600 }} />
                <PolarRadiusAxis angle={30} domain={[0, 1]} tick={false} axisLine={false} />
                <Radar name="Baseline" dataKey="Baseline" stroke="#ef4444" fill="#ef4444" fillOpacity={0.1} />
                <Radar name="Hybrid" dataKey="Hybrid" stroke="#7C6FF7" fill="#7C6FF7" fillOpacity={0.2} />
                <Radar name="Re-Ranked" dataKey="ReRanked" stroke="#0d9488" fill="#0d9488" fillOpacity={0.3} />
                <Legend iconType="circle" wrapperStyle={{ fontSize: '11px', paddingTop: '20px' }} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
          <p className="text-[11px] text-muted text-center mt-4 italic">
            The re-ranker stage significantly improved Context Precision by narrowing down the most relevant chunks.
          </p>
        </div>

        {/* ── Test Suite Performance ── */}
        <div className="card p-6 flex flex-col">
          <div className="flex items-center justify-between mb-6">
            <h2 className="font-bold text-text">Test Case Analysis</h2>
            <button className="btn-ghost text-xs text-lavender">View Full Test Set <ChevronRight className="w-3 h-3"/></button>
          </div>
          
          <div className="space-y-3 flex-1 overflow-y-auto pr-2 custom-scrollbar">
            {testSetResults.map(t => (
              <div key={t.id} className="p-3 bg-surfaceAlt border border-surfaceBorder rounded-xl hover:border-lavender/30 transition-all group">
                <div className="flex items-start justify-between gap-3 mb-2">
                  <div className="flex gap-3">
                    <div className="w-8 h-8 rounded-lg bg-white flex items-center justify-center flex-shrink-0 shadow-sm">
                      <FileText className={`w-4 h-4 ${t.status==='Pass'?'text-mint':'text-rose'}`}/>
                    </div>
                    <p className="text-xs font-bold text-text leading-snug">{t.question}</p>
                  </div>
                  <span className={`badge ${t.status==='Pass'?'badge-mint':'badge-rose'} text-[10px]`}>{t.status}</span>
                </div>
                <div className="flex gap-4 ml-11">
                  <div className="flex items-center gap-1.5">
                    <div className="w-1.5 h-1.5 rounded-full bg-mint"/>
                    <span className="text-[10px] text-muted font-bold">Faith: {t.faithfulness}</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <div className="w-1.5 h-1.5 rounded-full bg-lavender"/>
                    <span className="text-[10px] text-muted font-bold">Rel: {t.relevancy}</span>
                  </div>
                </div>
                {t.note && <p className="mt-2 text-[10px] text-rose font-medium bg-roseLight/20 p-1.5 rounded-md border border-rose/10 ml-11">Error: {t.note}</p>}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── RAG Strategy Breakdown ── */}
      <div className="card p-6 border-lavender/20 bg-lavendLight/5">
        <h2 className="font-bold text-text mb-4">Pipeline Architecture Optimization</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="space-y-2">
            <div className="badge badge-rose text-[10px]">Step 1: Hybrid Search</div>
            <p className="text-xs text-textSoft leading-relaxed">
              We merged dense semantic search with BM25 keyword matching using Reciprocal Rank Fusion to improve recall on domain-specific visa terms.
            </p>
          </div>
          <div className="space-y-2">
            <div className="badge badge-lavender text-[10px]">Step 2: Cross-Encoder Re-ranker</div>
            <p className="text-xs text-textSoft leading-relaxed">
              We used `ms-marco-MiniLM-L-6-v2` to score the top candidates, improving precision for the LLM input window.
            </p>
          </div>
          <div className="space-y-2">
            <div className="badge badge-mint text-[10px]">Step 3: Response Generation</div>
            <p className="text-xs text-textSoft leading-relaxed">
              Gemini 1.5 Flash generates cited answers grounded in the re-ranked context with memory preservation via LangChain.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
