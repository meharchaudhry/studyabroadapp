import { useEffect, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { authAPI } from '../api/auth';
import { universitiesAPI } from '../api/universities';
import { 
  Globe, Mail, Lock, User, DollarSign, Flag, Eye, EyeOff, 
  ArrowRight, GraduationCap, BookOpen, Clock, Calendar, ChevronLeft, Check, Award,
  Target, Zap, MapPin, Building2, Coffee, Briefcase, Loader2, Sparkles
} from 'lucide-react';

const FALLBACK_COUNTRIES = ['USA','UK','Germany','France','Netherlands','Australia','Singapore','Hong Kong','Spain','Switzerland','Finland'];
const DEGREE_LEVELS = ['High School', 'Diploma', 'Bachelors', 'Masters', 'PhD'];
const STANDARDIZED_TESTS = ['IELTS', 'TOEFL', 'PTE', 'GRE', 'GMAT', 'SAT', 'Duolingo', 'Other'];

export default function Register() {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [showPass, setShowPass] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [countries, setCountries] = useState(FALLBACK_COUNTRIES);

  const [form, setForm] = useState({
    email: '',
    password: '',
    cgpa: '',
    budget: '',
    degree_level: '',
    specialization: '',
    english_test_type: '',
    english_test_score: '',
    work_experience_years: '',
    preferred_intake: '',
    target_countries: [],
    // Psychographic Fields
    career_goal: '',
    preferred_environment: '',
    study_priority: '',
    learning_style: '',
    living_preference: ''
  });

  const updateForm = (updates) => setForm(prev => ({ ...prev, ...updates }));

  useEffect(() => {
    const loadCountries = async () => {
      try {
        const data = await universitiesAPI.getCountries();
        const list = (data.countries || []).filter(Boolean);
        if (list.length) {
          setCountries(list);
        }
      } catch {
        setCountries(FALLBACK_COUNTRIES);
      }
    };
    loadCountries();
  }, []);

  const toggleCountry = (c) => {
    updateForm({
      target_countries: form.target_countries.includes(c)
        ? form.target_countries.filter(x => x !== c)
        : [...form.target_countries, c]
    });
  };

  const nextStep = () => {
    if (step === 1 && (!form.email || !form.password)) {
      setError('Please provide email and password');
      return;
    }
    setError('');
    setStep(step + 1);
  };

  const prevStep = () => {
    setError('');
    setStep(step - 1);
  };

  const handleSubmit = async (e) => {
    if (e) e.preventDefault();
    setLoading(true);
    setError('');
    try {
      // Construct nested academic objects for the new backend model
      const payload = {
        ...form,
        budget: parseInt(form.budget, 10) || null,
        work_experience_years: parseInt(form.work_experience_years, 10) || 0,
        degrees: [
          {
            degree_level: form.degree_level,
            specialization: form.specialization,
            cgpa: parseFloat(form.cgpa) || 0,
            institution: '', // Optional for onboarding
            year_graduated: '' // Optional for onboarding
          }
        ],
        tests: [
          {
            test_name: form.english_test_type || 'IELTS',
            score: parseFloat(form.english_test_score) || 0,
            test_date: '' // Optional for onboarding
          }
        ]
      };

      // Remove the old flat mappings that are no longer in the schema
      delete payload.cgpa;
      delete payload.degree_level;
      delete payload.specialization;
      delete payload.english_test_type;
      delete payload.english_test_score;

      await authAPI.register(payload);
      navigate(`/verify-otp?email=${encodeURIComponent(form.email)}`);
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const MCQOption = ({ value, label, icon: Icon, field, description }) => (
    <button type="button" onClick={() => updateForm({ [field]: value })}
      className={`relative p-4 rounded-xl border text-left transition-all group ${
        form[field] === value 
          ? 'bg-lavender text-white border-lavender shadow-lg -translate-y-1' 
          : 'bg-white border-surfaceBorder hover:border-lavender/50 text-textSoft hover:bg-lavender/5'
      }`}>
      <div className="flex items-center gap-3 mb-1">
        <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${form[field] === value ? 'bg-white/20' : 'bg-lavendLight text-lavender'}`}>
          <Icon className="w-4 h-4" />
        </div>
        <span className="font-bold text-sm">{label}</span>
      </div>
      {description && <p className={`text-[10px] leading-relaxed ${form[field] === value ? 'text-white/80' : 'text-muted'}`}>{description}</p>}
    </button>
  );

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-surfaceAlt pb-20"
      style={{ backgroundImage: 'radial-gradient(ellipse at top right, rgba(124,111,247,0.1) 0%, transparent 60%), radial-gradient(ellipse at bottom left, rgba(78,204,163,0.05) 0%, transparent 60%)' }}>
      
      <div className="w-full max-w-2xl animate-scale-in">
        {/* Header */}
        <div className="text-center mb-6">
          <div className="w-12 h-12 bg-lavender rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-card">
            <Globe className="w-6 h-6 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-text">AI Strategy Session</h1>
          <p className="text-muted text-sm mt-1">Collecting deep insights to architect your study abroad journey</p>
        </div>

        {/* Progress System */}
        <div className="flex items-center justify-between mb-8 px-8 bg-white/50 backdrop-blur-sm p-4 rounded-2xl border border-white/20 shadow-sm">
          {[1,2,3,4,5].map(s => (
            <div key={s} className="flex items-center flex-1 last:flex-none">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition-all duration-500 ${
                step === s ? 'bg-lavender text-white scale-125 shadow-lg ring-4 ring-lavender/20' : 
                step > s ? 'bg-mint text-white' : 'bg-surface border border-surfaceBorder text-muted'
              }`}>
                {step > s ? <Check className="w-4 h-4"/> : s}
              </div>
              {s < 5 && <div className={`h-1 flex-1 mx-2 rounded-full transition-all duration-700 ${step > s ? 'bg-mint' : 'bg-surfaceBorder'}`}/>}
            </div>
          ))}
        </div>

        <div className="card p-8 shadow-cardHov relative overflow-hidden min-h-[500px] flex flex-col">
          {error && <div className="bg-rose/10 border border-rose/20 text-rose rounded-xl px-4 py-3 text-sm mb-5 animate-shake">{error}</div>}

          <div className="flex-1">
            {/* ── Step 1: Account ── */}
            {step === 1 && (
              <div className="space-y-4 animate-slide-right">
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-lg font-bold text-text flex items-center gap-2">
                    <Mail className="w-5 h-5 text-lavender"/> Basic Credentials
                  </h2>
                  <span className="text-[10px] uppercase font-bold text-lavender bg-lavendLight px-2 py-1 rounded-md">Step 1 of 5</span>
                </div>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-text mb-1.5">Email address</label>
                    <div className="relative">
                      <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-muted" />
                      <input type="email" value={form.email} onChange={e=>updateForm({email:e.target.value})} placeholder="you@example.com" className="input-field pl-10"/>
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-text mb-1.5">Create Secure Password</label>
                    <div className="relative">
                      <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-muted" />
                      <input type={showPass?'text':'password'} value={form.password} onChange={e=>updateForm({password:e.target.value})} placeholder="Min. 8 characters" className="input-field pl-10 pr-10"/>
                      <button type="button" onClick={()=>setShowPass(!showPass)} className="absolute right-3.5 top-1/2 -translate-y-1/2 text-muted hover:text-text">
                        {showPass ? <EyeOff className="w-4 h-4"/> : <Eye className="w-4 h-4"/>}
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* ── Step 2: Academics ── */}
            {step === 2 && (
              <div className="space-y-4 animate-slide-right">
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-lg font-bold text-text flex items-center gap-2">
                    <GraduationCap className="w-5 h-5 text-lavender"/> Academic Profile
                  </h2>
                  <span className="text-[10px] uppercase font-bold text-lavender bg-lavendLight px-2 py-1 rounded-md">Step 2 of 5</span>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-text mb-1.5">Degree Level</label>
                    <select value={form.degree_level} onChange={e=>updateForm({degree_level:e.target.value})} className="input-field py-2">
                      <option value="">Select Level</option>
                      {DEGREE_LEVELS.map(d=><option key={d} value={d}>{d}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-text mb-1.5">Cumulative CGPA</label>
                    <input type="number" step="0.1" value={form.cgpa} onChange={e=>updateForm({cgpa:e.target.value})} placeholder="8.5 / 10" className="input-field"/>
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-text mb-1.5">Field of Study</label>
                  <div className="relative">
                    <BookOpen className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-muted" />
                    <input type="text" value={form.specialization} onChange={e=>updateForm({specialization:e.target.value})} placeholder="e.g. Artificial Intelligence, Data Science" className="input-field pl-10"/>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-text mb-1.5">English Test</label>
                    <select value={form.english_test_type} onChange={e=>updateForm({english_test_type:e.target.value})} className="input-field py-2">
                      {STANDARDIZED_TESTS.map(t=><option key={t} value={t}>{t}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-text mb-1.5">Score</label>
                    <input type="number" step="0.1" value={form.english_test_score} onChange={e=>updateForm({english_test_score:e.target.value})} placeholder="e.g. 7.5" className="input-field"/>
                  </div>
                </div>
              </div>
            )}

            {/* ── Step 3: Career Path (MCQ) ── */}
            {step === 3 && (
              <div className="space-y-6 animate-slide-right">
                <div className="flex items-center justify-between mb-2">
                  <h2 className="text-lg font-bold text-text flex items-center gap-2">
                    <Target className="w-5 h-5 text-lavender"/> Vision & Ambition
                  </h2>
                  <span className="text-[10px] uppercase font-bold text-lavender bg-lavendLight px-2 py-1 rounded-md">Step 3 of 5</span>
                </div>
                
                <div>
                  <p className="text-xs font-bold text-muted uppercase tracking-wider mb-3">What is your primary career goal?</p>
                  <div className="grid grid-cols-2 gap-3">
                    <MCQOption field="career_goal" value="Industry" label="High-Growth Tech" icon={Zap} description="High-paying roles in multinational companies."/>
                    <MCQOption field="career_goal" value="Research" label="Academic / Research" icon={BookOpen} description="PhD track and deep research in specialized labs."/>
                    <MCQOption field="career_goal" value="Entrepreneur" label="Entrepreneurship" icon={Globe} description="Scale my own startup or join a startup ecosystem."/>
                    <MCQOption field="career_goal" value="Pivot" label="Career Transformation" icon={User} description="Switching industries entirely for a fresh start."/>
                  </div>
                </div>

                <div>
                  <p className="text-xs font-bold text-muted uppercase tracking-wider mb-3">Preferred Learning Style?</p>
                  <div className="grid grid-cols-3 gap-3">
                    <MCQOption field="learning_style" value="Practical" label="Hands-on" icon={Zap}/>
                    <MCQOption field="learning_style" value="Theoretical" label="Academic" icon={BookOpen}/>
                    <MCQOption field="learning_style" value="Hybrid" label="Hybrid" icon={Globe}/>
                  </div>
                </div>
              </div>
            )}

            {/* ── Step 4: Lifestyle (MCQ) ── */}
            {step === 4 && (
              <div className="space-y-6 animate-slide-right">
                <div className="flex items-center justify-between mb-2">
                  <h2 className="text-lg font-bold text-text flex items-center gap-2">
                    <Coffee className="w-5 h-5 text-lavender"/> Environment & Cultural Fit
                  </h2>
                  <span className="text-[10px] uppercase font-bold text-lavender bg-lavendLight px-2 py-1 rounded-md">Step 4 of 5</span>
                </div>

                <div>
                  <p className="text-xs font-bold text-muted uppercase tracking-wider mb-3">Where do you see yourself thriving?</p>
                  <div className="grid grid-cols-2 gap-3">
                    <MCQOption field="preferred_environment" value="Urban" label="Metropolitan Hustle" icon={Building2} description="Big cities like London, NYC, or Tokyo."/>
                    <MCQOption field="preferred_environment" value="Campus" label="Classic University Town" icon={MapPin} description="Quiet, campus-centric towns like Oxford or Ithaca."/>
                  </div>
                </div>

                <div>
                  <p className="text-xs font-bold text-muted uppercase tracking-wider mb-3">Study Priority?</p>
                  <div className="grid grid-cols-3 gap-2">
                    <MCQOption field="study_priority" value="Ranking" label="Prestige" icon={Award}/>
                    <MCQOption field="study_priority" value="Budget" label="ROI" icon={DollarSign}/>
                    <MCQOption field="study_priority" value="Work" label="VWP" icon={Briefcase}/>
                  </div>
                </div>

                <div>
                  <p className="text-xs font-bold text-muted uppercase tracking-wider mb-3">Living Preference?</p>
                  <div className="flex gap-3">
                    <MCQOption field="living_preference" value="Dorm" label="On-Campus Dorm" icon={HomeIcon}/>
                    <MCQOption field="living_preference" value="Apartment" label="Private Rental" icon={User}/>
                  </div>
                </div>
              </div>
            )}

            {/* ── Step 5: Logistics ── */}
            {step === 5 && (
              <div className="space-y-4 animate-slide-right">
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-lg font-bold text-text flex items-center gap-2">
                    <Flag className="w-5 h-5 text-lavender"/> Final Strategy Details
                  </h2>
                  <span className="text-[10px] uppercase font-bold text-lavender bg-lavendLight px-2 py-1 rounded-md">Step 5 of 5</span>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-text mb-1.5">Work Experience (Yrs)</label>
                    <input type="number" value={form.work_experience_years} onChange={e=>updateForm({work_experience_years:e.target.value})} placeholder="0" className="input-field"/>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-text mb-1.5">Preferred Intake</label>
                    <input type="text" value={form.preferred_intake} onChange={e=>updateForm({preferred_intake:e.target.value})} placeholder="Fall 2025" className="input-field"/>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-text mb-1.5">Max Yearly Budget <span className="text-muted text-xs">(₹ Total)</span></label>
                  <input type="number" value={form.budget} onChange={e=>updateForm({budget:e.target.value})} placeholder="e.g. 5,000,000" className="input-field"/>
                </div>

                <div>
                  <label className="block text-sm font-medium text-text mb-2">Target Countries <span className="text-muted text-[10px]">(Select Multiple)</span></label>
                  <div className="flex flex-wrap gap-1.5 max-h-32 overflow-y-auto p-1 custom-scrollbar">
                    {countries.map(c => (
                      <button key={c} type="button" onClick={()=>toggleCountry(c)}
                        className={`px-3 py-1.5 rounded-lg text-[10px] font-bold border transition-all ${
                          form.target_countries.includes(c)
                            ? 'bg-lavender text-white border-lavender shadow-md'
                            : 'bg-surfaceAlt text-textSoft border-surfaceBorder hover:border-lavender hover:text-lavender'
                        }`}>
                        {c}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>

          <div className="flex gap-4 mt-8 pt-6 border-t border-surfaceBorder">
            {step > 1 && (
              <button onClick={prevStep} className="btn-secondary flex-1 py-1.5 flex justify-center items-center gap-2">
                <ChevronLeft className="w-4 h-4"/> Back
              </button>
            )}
            {step < 5 ? (
              <button onClick={nextStep} className="btn-primary flex-1 py-1.5">
                Next Stage <ArrowRight className="w-4 h-4"/>
              </button>
            ) : (
              <button onClick={handleSubmit} disabled={loading} className="btn-primary flex-1 py-1.5">
                {loading ? <Loader2 className="w-5 h-5 animate-spin mx-auto"/> : 'Finalize Profile & Get OTP'}
              </button>
            )}
          </div>

          <p className="text-center text-[11px] text-muted mt-5">
            Already a member?{' '}
            <Link to="/login" className="text-lavender font-bold hover:underline">Log in</Link>
          </p>
        </div>
      </div>
    </div>
  );
}

const HomeIcon = ({ className }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
  </svg>
);


