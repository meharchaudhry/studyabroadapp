import { useState, useEffect } from 'react';
import { 
  Sparkles, 
  ChevronRight, 
  Target, 
  BrainCircuit, 
  ArrowRight,
  TrendingUp,
  MapPin,
  GraduationCap,
  Loader2
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { decisionAPI } from '../api/decision';

const STEP_ICON = {
  profile: Target,
  visa: Sparkles,
  finance: TrendingUp,
  jobs: MapPin,
  synthesis: BrainCircuit,
};

const FLAG = { USA:'🇺🇸', UK:'🇬🇧', Germany:'🇩🇪', France:'🇫🇷', Netherlands:'🇳🇱', Australia:'🇦🇺', Singapore:'🇸🇬', HongKong:'🇭🇰', Spain:'🇪🇸', Switzerland:'🇨🇭', Finland:'🇫🇮' };

export default function Dashboard() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [decision, setDecision] = useState(null);
  const [isRunning, setIsRunning] = useState(false);
  const [activeStep, setActiveStep] = useState(4); // default to all done

  const fetchDecision = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await decisionAPI.getDecision();
      setDecision(data);
      const totalSteps = (data.agent_steps || []).length;
      setActiveStep(Math.max(0, totalSteps - 1));
    } catch {
      setError('Unable to load recommendation chain right now.');
      setDecision(null);
    } finally {
      setLoading(false);
      setIsRunning(false);
    }
  };

  useEffect(() => {
    fetchDecision();
  }, []);

  const runChain = () => {
    const steps = decision?.agent_steps || [];
    if (!steps.length) {
      fetchDecision();
      return;
    }

    setIsRunning(true);
    setActiveStep(-1);
    let step = 0;
    const interval = setInterval(() => {
      setActiveStep(step);
      step += 1;
      if (step >= steps.length) {
        clearInterval(interval);
        fetchDecision();
      }
    }, 900);
  };

  const recommendations = decision?.recommendations || [];
  const agentSteps = decision?.agent_steps || [];

  if (loading) {
    return (
      <div className="py-24 flex flex-col items-center gap-3 text-muted">
        <Loader2 className="w-8 h-8 animate-spin text-lavender" />
        <span className="text-sm">Running recommendation chain...</span>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-fade-in pb-10">
      
      {/* ── Welcome Banner ── */}
      <div className="relative card overflow-hidden bg-gradient-to-br from-lavender to-[#5C4DDF] p-8 text-white border-none">
        <div className="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2" />
        <div className="relative z-10 flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="max-w-xl">
            <div className="flex items-center gap-3 mb-3">
              <div className="p-2 bg-white/20 rounded-xl backdrop-blur-md"><Sparkles className="w-5 h-5 text-white"/></div>
              <h1 className="text-2xl font-bold">Your AI-Powered Decision Dashboard</h1>
            </div>
            <p className="text-white/80 text-sm leading-relaxed mb-6">
              This dashboard combines profile fit, visa complexity, financial ROI, and job-market signals to produce your top study-abroad options.
            </p>
            <button 
              onClick={runChain} 
              disabled={isRunning}
              className="px-6 py-2.5 bg-white text-lavender font-bold rounded-xl text-sm shadow-lg hover:shadow-xl transition-all flex items-center gap-2 group"
            >
              {isRunning ? 'Swarm Thinking...' : 're-run recommendation chain'}
              <ArrowRight className={`w-4 h-4 group-hover:translate-x-1 transition-transform ${isRunning ? 'animate-spin' : ''}`}/>
            </button>
          </div>
          <div className="hidden md:flex items-center gap-4 bg-white/10 p-5 rounded-2xl backdrop-blur-md">
            <div className="text-center px-4">
              <div className="text-2xl font-black">{recommendations.length || 0}</div>
              <div className="text-[10px] uppercase font-bold opacity-70">Top Options</div>
            </div>
            <div className="w-px h-10 bg-white/20"/>
            <div className="text-center px-4">
              <div className="text-2xl font-black">{Math.round((recommendations[0]?.final_score || 0) * 100)}%</div>
              <div className="text-[10px] uppercase font-bold opacity-70">Best Score</div>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* ── Agent Process Sidebar ── */}
        <div className="lg:col-span-1 space-y-4">
          <h2 className="text-sm font-bold text-text mb-4 uppercase tracking-wider flex items-center gap-2">
            <BrainCircuit className="w-4 h-4 text-lavender"/> Swarm Execution
          </h2>
          <div className="space-y-3 relative">
            <div className="absolute left-6 top-6 bottom-6 w-px bg-surfaceBorder hidden sm:block"/>
            {agentSteps.map((step, i) => {
              const Icon = STEP_ICON[step.id] || BrainCircuit;
              const isActive = activeStep === i;
              const isPast = activeStep > i;
              return (
                <div key={step.id} 
                  className={`card p-4 transition-all duration-500 relative ml-0 sm:ml-4 border-l-4 ${
                    isActive ? 'border-lavender bg-lavendLight/20 shadow-soft' : 
                    isPast ? 'border-mint bg-mintLight/5' : 'border-transparent opacity-60'
                  }`}
                >
                  <div className="flex items-center gap-3 mb-2">
                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center transition-colors ${
                      isActive ? 'bg-lavender text-white' : 
                      isPast ? 'bg-mint text-white' : 'bg-surfaceAlt text-muted'
                    }`}>
                      <Icon className="w-4 h-4"/>
                    </div>
                    <span className={`text-xs font-bold ${isActive ? 'text-lavender' : isPast ? 'text-teal-600' : 'text-text'}`}>
                      {step.name}
                    </span>
                    {isPast && <span className="ml-auto text-[10px] font-bold text-mint">Done</span>}
                  </div>
                  {(isActive || isPast) && (
                    <p className="text-[11px] text-textSoft leading-snug animate-slide-up">
                      {step.result}
                    </p>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* ── Top Recommendations ── */}
        <div className="lg:col-span-2 space-y-6">
          <h2 className="text-sm font-bold text-text uppercase tracking-wider flex items-center gap-2">
            <Target className="w-4 h-4 text-peach"/> Final Recommendations
          </h2>
          
          <div className="grid grid-cols-1 gap-4">
            {error && (
              <div className="card p-4 text-sm text-rose">{error}</div>
            )}
            {recommendations.length === 0 && !error && (
              <div className="card p-4 text-sm text-muted">No recommendations yet. Complete your profile and rerun the chain.</div>
            )}
            {recommendations.map((rec, i) => (
              <div key={rec.id} 
                className={`card flex flex-col md:flex-row overflow-hidden group transition-all duration-700 animate-slide-up`}
                style={{animationDelay: `${i * 200}ms`}}
              >
                <div className="w-full md:w-48 h-48 md:h-auto bg-surfaceAlt flex-shrink-0 relative flex items-center justify-center">
                  <GraduationCap className="w-12 h-12 text-lavender/30" />
                  <div className="absolute top-2 left-2 bg-white/90 px-2 py-1 rounded-lg text-xs font-bold text-lavender shadow-sm">
                    {Math.round((rec.final_score || rec.match_score || 0) * 100)}% Final
                  </div>
                </div>
                <div className="p-5 flex flex-1 flex-col justify-between">
                  <div>
                    <div className="flex items-start justify-between mb-1">
                      <h3 className="text-lg font-bold text-text group-hover:text-lavender transition-colors">{rec.name}</h3>
                      <Link to={`/universities/${rec.id}`} className="text-lavender p-1 hover:bg-lavendLight rounded-lg transition-colors" aria-label={`Open ${rec.name}`}>
                        <ChevronRight className="w-5 h-5"/>
                      </Link>
                    </div>
                    <div className="flex items-center gap-2 text-xs text-muted mb-4">
                      <MapPin className="w-3 h-3"/> {FLAG[rec.country] || '🌍'} {rec.country}
                    </div>
                    <div className="bg-lavendLight/30 border border-lavender/10 rounded-xl p-3 mb-4">
                      <p className="text-xs text-textSoft leading-relaxed italic">"{rec.reason}"</p>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      <span className="px-2 py-0.5 bg-mintLight text-teal-600 text-[10px] font-bold rounded-full">
                        Visa: {rec.visa?.difficulty || 'Unknown'}
                      </span>
                      <span className="px-2 py-0.5 bg-skyLight text-blue-700 text-[10px] font-bold rounded-full">
                        ROI 5Y: {rec.finance?.roi_5y ?? '--'}%
                      </span>
                      <span className="px-2 py-0.5 bg-peachLight text-orange-700 text-[10px] font-bold rounded-full">
                        Job Score: {Math.round((rec.jobs?.score || 0) * 100)}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-8">
            <Link to="/universities" className="card p-5 group flex flex-col justify-between hover:bg-lavendLight/10 transition-all">
              <div className="w-10 h-10 bg-lavendLight text-lavender rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                <GraduationCap className="w-5 h-5"/>
              </div>
              <div>
                <h3 className="font-bold text-text">Explore All Unis</h3>
                <p className="text-xs text-muted mt-1">Browse all universities and compare fit details.</p>
              </div>
            </Link>
            <Link to="/finance" className="card p-5 group flex flex-col justify-between hover:bg-mintLight/10 transition-all">
              <div className="w-10 h-10 bg-mintLight text-teal-600 rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                <TrendingUp className="w-5 h-5"/>
              </div>
              <div>
                <h3 className="font-bold text-text">ROI Deep Dive</h3>
                <p className="text-xs text-muted mt-1">Detailed financial breakdown for your top recommendations.</p>
              </div>
            </Link>
          </div>
        </div>

      </div>
    </div>
  );
}
