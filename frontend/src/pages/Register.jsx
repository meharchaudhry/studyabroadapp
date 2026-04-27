import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { authAPI } from '../api/auth';
import {
  Eye, EyeOff, ArrowRight, ArrowLeft,
  GraduationCap, User, BookOpen, Plane, ClipboardList, IndianRupee, Briefcase
} from 'lucide-react';

// ── Constants ──────────────────────────────────────────────────────────────────

const COUNTRIES = [
  { code: "United States",  flag: "🇺🇸", label: "USA"         },
  { code: "United Kingdom", flag: "🇬🇧", label: "UK"          },
  { code: "Canada",         flag: "🇨🇦", label: "Canada"      },
  { code: "Australia",      flag: "🇦🇺", label: "Australia"   },
  { code: "Germany",        flag: "🇩🇪", label: "Germany"     },
  { code: "France",         flag: "🇫🇷", label: "France"      },
  { code: "Netherlands",    flag: "🇳🇱", label: "Netherlands" },
  { code: "Ireland",        flag: "🇮🇪", label: "Ireland"     },
  { code: "Singapore",      flag: "🇸🇬", label: "Singapore"   },
  { code: "Japan",          flag: "🇯🇵", label: "Japan"       },
  { code: "Sweden",         flag: "🇸🇪", label: "Sweden"      },
  { code: "Norway",         flag: "🇳🇴", label: "Norway"      },
  { code: "New Zealand",    flag: "🇳🇿", label: "NZ"          },
  { code: "UAE",            flag: "🇦🇪", label: "UAE"         },
  { code: "Switzerland",    flag: "🇨🇭", label: "Switzerland" },
  { code: "South Korea",    flag: "🇰🇷", label: "S. Korea"    },
];

const CURRENT_DEGREES = [
  "B.Tech / B.E.", "B.Sc", "BCA", "B.Com", "BBA / BBM",
  "BA", "MBBS / BDS", "LLB", "B.Arch", "Other",
];

const FIELDS_OF_STUDY = [
  "Computer Science", "Data Science / AI", "Electrical Engineering",
  "Mechanical Engineering", "Civil Engineering", "Chemical Engineering",
  "Business / MBA", "Finance / Economics", "Marketing",
  "Medicine / Public Health", "Law", "Architecture / Design",
  "Physics / Mathematics", "Biotechnology", "Psychology",
];

const TARGET_DEGREES = [
  { value: "Masters",   label: "M.S. / M.Eng",  sub: "STEM Master's"     },
  { value: "MBA",       label: "MBA",            sub: "Business Master's" },
  { value: "PhD",       label: "PhD",            sub: "Doctoral research" },
  { value: "Bachelors", label: "Bachelor's",     sub: "Undergraduate"     },
  { value: "Diploma",   label: "PG Diploma",     sub: "Short programme"   },
  { value: "Other",     label: "Other",          sub: "Certificate etc."  },
];

const ENGLISH_TESTS = ["IELTS", "TOEFL", "PTE", "Duolingo", "Not yet taken"];

const INTAKE_OPTIONS = [
  { value: "Fall",   label: "Fall",   sub: "Aug–Sep intake" },
  { value: "Spring", label: "Spring", sub: "Jan–Feb intake" },
  { value: "Winter", label: "Winter", sub: "Dec intake"     },
];

const RANKING_OPTIONS = [
  { value: "Top 50",  label: "Top 50",  sub: "World-class, highly selective" },
  { value: "Top 100", label: "Top 100", sub: "Excellent, competitive"        },
  { value: "Top 200", label: "Top 200", sub: "Strong, good ROI"              },
  { value: "Any",     label: "Any",     sub: "Value & fit over rank"         },
];

const CAREER_GOALS = [
  { value: "tech industry",    label: "Tech Industry",    sub: "SWE, ML, product"      },
  { value: "finance",          label: "Finance",          sub: "Banking, consulting"    },
  { value: "academia",         label: "Academia",         sub: "Research, teaching"     },
  { value: "entrepreneurship", label: "Entrepreneurship", sub: "Startups, VC"           },
  { value: "healthcare",       label: "Healthcare",       sub: "Medicine, pharma"       },
  { value: "government",       label: "Government / NGO", sub: "Policy, public sector"  },
];

const STUDY_PRIORITIES = [
  { value: "research",          label: "Research",          sub: "Publications & labs"      },
  { value: "internships",       label: "Internships",       sub: "Industry exposure"         },
  { value: "coursework",        label: "Coursework",        sub: "Structured curriculum"     },
  { value: "networking",        label: "Networking",        sub: "Alumni & industry connects" },
  { value: "startup ecosystem", label: "Startup Ecosystem", sub: "Founders & investors"      },
];

const ENVIRONMENT_OPTIONS = [
  { value: "urban",         label: "Urban city",     sub: "NYC, London, Berlin" },
  { value: "campus town",   label: "Campus town",    sub: "Oxford, Ann Arbor"   },
  { value: "small city",    label: "Small city",     sub: "Quiet, affordable"   },
  { value: "no preference", label: "No preference",  sub: "Open to anything"    },
];

const LEARNING_STYLES = [
  { value: "seminars",            label: "Seminars",           sub: "Discussion-led"      },
  { value: "lectures",            label: "Lectures",           sub: "Traditional classes" },
  { value: "online flexibility",  label: "Online flexible",    sub: "Hybrid / async"      },
  { value: "project-based",       label: "Project-based",      sub: "Hands-on builds"     },
];

const LIVING_OPTIONS = [
  { value: "on-campus",    label: "On-campus",     sub: "Dorms / student halls"  },
  { value: "shared house", label: "Shared house",  sub: "With other students"    },
  { value: "studio",       label: "Studio / solo", sub: "Private accommodation"  },
  { value: "no preference",label: "No preference", sub: "Flexible"               },
];

// Budget presets in INR (annual, tuition + living)
const BUDGET_PRESETS_INR = [
  { label: "₹20L",  value: 2000000  },
  { label: "₹30L",  value: 3000000  },
  { label: "₹40L",  value: 4000000  },
  { label: "₹60L+", value: 6000000  },
];
const PASSWORD_COMPLEXITY_REGEX = /^(?=.*[A-Za-z])(?=.*\d).{8,}$/;
const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

const STEPS = [
  { id: 1, label: "Account",    icon: User          },
  { id: 2, label: "Academic",   icon: BookOpen      },
  { id: 3, label: "Test Scores",icon: ClipboardList },
  { id: 4, label: "Goals",      icon: Plane         },
  { id: 5, label: "Career",     icon: Briefcase     },
  { id: 6, label: "Budget",     icon: IndianRupee   },
];

// ── Component ──────────────────────────────────────────────────────────────────

export default function Register() {
  const navigate = useNavigate();
  const [step, setStep]       = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState('');
  const [showPwd, setShowPwd] = useState(false);

  const [form, setForm] = useState({
    // Step 1 — Account
    full_name: '',
    email: '',
    password: '',
    // Step 2 — Academic
    current_degree: '',
    home_university: '',
    field_of_study: '',
    cgpa: '',
    graduation_year: new Date().getFullYear() + 1,
    // Step 3 — Test scores
    english_test: '',
    english_score: '',
    toefl_score: '',
    gre_score: '',
    gmat_score: '',
    work_experience_years: '',
    // Step 4 — Goals
    preferred_degree: '',
    intake_preference: '',
    target_countries: [],
    ranking_preference: '',
    work_abroad_interest: false,
    // Step 5 — Career & Life
    career_goal: '',
    study_priority: '',
    preferred_environment: '',
    learning_style: '',
    living_preference: '',
    // Step 6 — Budget
    budget_inr: '',
    scholarship_interest: false,
  });

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));

  const toggleCountry = (code) =>
    setForm(f => ({
      ...f,
      target_countries: f.target_countries.includes(code)
        ? f.target_countries.filter(c => c !== code)
        : [...f.target_countries, code],
    }));

  // ── Validation ──────────────────────────────────────────────────────────────
  const validate = () => {
    setError('');
    if (step === 1) {
      if (!form.full_name.trim()) return err('Please enter your full name.');
      if (!form.email.trim()) return err('Please enter your email.');
      if (!EMAIL_REGEX.test(form.email.trim())) return err('Please enter a valid email address.');
      if (!PASSWORD_COMPLEXITY_REGEX.test(form.password)) {
        return err('Password must be at least 8 characters and include both letters and numbers.');
      }
    }
    if (step === 2) {
      if (!form.current_degree) return err('Please select your current degree.');
      if (!form.field_of_study) return err('Please select your field of study.');
      if (!form.cgpa) return err('Please enter your CGPA.');
      const cgpa = parseFloat(form.cgpa);
      if (cgpa < 0 || cgpa > 10) return err('CGPA must be between 0 and 10.');
    }
    if (step === 4) {
      if (!form.preferred_degree) return err('Please select your target degree.');
      if (!form.target_countries.length) return err('Select at least one target country.');
    }
    if (step === 6) {
      if (!form.budget_inr) return err('Please enter your annual budget.');
    }
    return true;
  };
  const err = (msg) => { setError(msg); return false; };

  const next = () => { if (validate()) setStep(s => s + 1); };
  const back = () => { setError(''); setStep(s => s - 1); };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;
    setLoading(true);
    setError('');
    try {
      const budgetInr = parseInt(form.budget_inr, 10) || null;
      const budgetUsd = budgetInr ? Math.round(budgetInr / 83) : null;

      const res = await authAPI.register({
        email:                form.email,
        password:             form.password,
        full_name:            form.full_name,
        current_degree:       form.current_degree || null,
        home_university:      form.home_university || null,
        field_of_study:       form.field_of_study || null,
        cgpa:                 parseFloat(form.cgpa) || null,
        graduation_year:      parseInt(form.graduation_year, 10) || null,
        english_test:         form.english_test || null,
        english_score:        form.english_score ? parseFloat(form.english_score) : null,
        toefl_score:          form.toefl_score ? parseInt(form.toefl_score, 10) : null,
        gre_score:            form.gre_score ? parseInt(form.gre_score, 10) : null,
        gmat_score:           form.gmat_score ? parseInt(form.gmat_score, 10) : null,
        work_experience_years:form.work_experience_years ? parseFloat(form.work_experience_years) : null,
        preferred_degree:     form.preferred_degree || null,
        intake_preference:    form.intake_preference || null,
        target_countries:     form.target_countries,
        ranking_preference:   form.ranking_preference || null,
        work_abroad_interest: form.work_abroad_interest,
        career_goal:          form.career_goal || null,
        study_priority:       form.study_priority || null,
        preferred_environment:form.preferred_environment || null,
        learning_style:       form.learning_style || null,
        living_preference:    form.living_preference || null,
        budget_inr:           budgetInr,
        budget:               budgetUsd,
        scholarship_interest: form.scholarship_interest,
      });
      navigate('/verify-otp', {
        state: { email: form.email },
      });
    } catch (e) {
      setError(e.response?.data?.detail || 'Registration failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const isLastStep = step === STEPS.length;

  return (
    <div className="min-h-screen flex">

      {/* ── Left brand panel ── */}
      <div className="hidden lg:flex lg:w-[38%] relative overflow-hidden flex-col justify-between p-12"
        style={{ background: 'linear-gradient(135deg, #1E40AF 0%, #2563EB 60%, #3B82F6 100%)' }}>
        <div className="absolute -top-20 -right-20 w-96 h-96 rounded-full bg-white/10 blur-3xl" />
        <div className="absolute -bottom-20 -left-20 w-80 h-80 rounded-full bg-white/10 blur-3xl" />

        <div className="relative z-10 flex items-center gap-3">
          <div className="w-10 h-10 bg-white/20 backdrop-blur-sm rounded-xl flex items-center justify-center border border-white/25">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
              <path d="M12 3 C7 8 3 10 3 16 C7 14 10 13 12 15 C14 13 17 14 21 16 C21 10 17 8 12 3Z"
                fill="white" fillOpacity="0.95"/>
              <path d="M12 15 L12 21" stroke="white" strokeWidth="2" strokeLinecap="round"/>
            </svg>
          </div>
          <span className="font-brand font-bold text-white tracking-wide" style={{ fontSize: '1.35rem' }}>udaan</span>
        </div>

        <div className="relative z-10 flex-1 flex flex-col justify-center">
          <h1 className="font-brand text-white leading-tight mb-3" style={{ fontSize: '2.4rem', fontWeight: 700 }}>
            Your advisor<br />for studying abroad
          </h1>
          <p className="text-white/75 text-sm mb-7 leading-relaxed">
            Tell us your academic profile and goals. We match you with the right universities, guide your visa, and show you the financial picture.
          </p>
          <div className="space-y-3">
            {[
              "600+ universities matched to your GPA and field of study",
              "Visa documents, timelines and requirements by country",
              "ROI calculator — tuition cost vs. graduate salaries",
              "Shortlist builder with side-by-side comparison",
            ].map(f => (
              <div key={f} className="flex items-start gap-2.5">
                <div className="w-1.5 h-1.5 rounded-full bg-white/60 flex-shrink-0 mt-2" />
                <span className="text-white/80 text-sm leading-relaxed">{f}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Step tracker */}
        <div className="relative z-10 bg-white/10 backdrop-blur-sm border border-white/20 rounded-2xl p-5">
          <p className="text-white/60 text-xs mb-3 font-medium uppercase tracking-wide">
            Setup Progress — Step {step} of {STEPS.length}
          </p>
          <div className="flex gap-1.5 mb-4">
            {STEPS.map(s => (
              <div key={s.id}
                className={`h-1.5 flex-1 rounded-full transition-all duration-500 ${step >= s.id ? 'bg-white' : 'bg-white/20'}`} />
            ))}
          </div>
          <div className="flex gap-3 flex-wrap">
            {STEPS.map(s => {
              const Icon = s.icon;
              const done = step > s.id, active = step === s.id;
              return (
                <div key={s.id}
                  className={`flex items-center gap-1.5 text-xs font-medium ${active ? 'text-white' : done ? 'text-white/60' : 'text-white/30'}`}>
                  <Icon className="w-3.5 h-3.5" />
                  {s.label}
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* ── Right form panel ── */}
      <div className="flex-1 flex items-start justify-center p-8 bg-[#F8F9FC] overflow-y-auto">
        <div className="w-full max-w-[500px] py-8">

          {/* Mobile logo + progress */}
          <div className="lg:hidden flex items-center gap-2 mb-4">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center"
              style={{ background: 'linear-gradient(135deg, #1E40AF, #3B82F6)' }}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                <path d="M12 3 C7 8 3 10 3 16 C7 14 10 13 12 15 C14 13 17 14 21 16 C21 10 17 8 12 3Z" fill="white" fillOpacity="0.95"/>
                <path d="M12 15 L12 21" stroke="white" strokeWidth="2" strokeLinecap="round"/>
              </svg>
            </div>
            <span className="font-brand font-bold text-text" style={{ fontSize: '1.1rem' }}>udaan</span>
          </div>
          <div className="lg:hidden flex gap-1.5 mb-5">
            {STEPS.map(s => (
              <div key={s.id}
                className={`h-1.5 flex-1 rounded-full transition-all ${step >= s.id ? 'bg-lavender' : 'bg-surfaceBorder'}`} />
            ))}
          </div>

          {/* Heading */}
          <div className="mb-5">
            <p className="text-xs font-bold text-lavender uppercase tracking-wider mb-1">
              Step {step} of {STEPS.length}
            </p>
            <h2 className="text-2xl font-black text-text mb-0.5">
              {step === 1 && 'Create your account'}
              {step === 2 && 'Academic background'}
              {step === 3 && 'Test scores & experience'}
              {step === 4 && 'Study goals'}
              {step === 5 && 'Career & lifestyle'}
              {step === 6 && 'Budget & preferences'}
            </h2>
            <p className="text-muted text-sm">
              {step === 1 && 'Free forever — no credit card required.'}
              {step === 2 && 'Your current education & CGPA (10-point scale).'}
              {step === 3 && 'All optional — add what you have.'}
              {step === 4 && 'Where and what you want to study.'}
              {step === 5 && 'Helps us match universities to your career & life goals.'}
              {step === 6 && 'Your total annual budget in Indian Rupees.'}
            </p>
          </div>

          {error && (
            <div className="mb-4 p-3.5 rounded-xl bg-rose/8 border border-rose/25 text-rose text-sm font-medium">
              {error}
            </div>
          )}

          <form
            onSubmit={isLastStep ? handleSubmit : (e) => { e.preventDefault(); next(); }}
            className="space-y-4"
          >

            {/* ── Step 1: Account ── */}
            {step === 1 && (
              <>
                <div>
                  <label className="block text-sm font-semibold text-textSoft mb-1.5">Full name</label>
                  <input type="text" required autoComplete="name" className="input-field"
                    placeholder="e.g. Priya Sharma"
                    value={form.full_name} onChange={e => set('full_name', e.target.value)} />
                </div>
                <div>
                  <label className="block text-sm font-semibold text-textSoft mb-1.5">Email address</label>
                  <input type="email" required autoComplete="email" className="input-field"
                    placeholder="you@gmail.com"
                    value={form.email} onChange={e => set('email', e.target.value)} />
                </div>
                <div>
                  <label className="block text-sm font-semibold text-textSoft mb-1.5">Password</label>
                  <div className="relative">
                    <input type={showPwd ? 'text' : 'password'} required minLength={8}
                      pattern="(?=.*[A-Za-z])(?=.*[0-9]).{8,}"
                      autoComplete="new-password"
                      className="input-field pr-11" placeholder="Min. 8 characters"
                      value={form.password} onChange={e => set('password', e.target.value)} />
                    <button type="button" onClick={() => setShowPwd(v => !v)}
                      className="absolute right-3.5 top-1/2 -translate-y-1/2 text-muted hover:text-textSoft">
                      {showPwd ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                  <p className="mt-1 text-xs text-muted">Use at least 8 characters with at least one letter and one number.</p>
                </div>
              </>
            )}

            {/* ── Step 2: Academic background ── */}
            {step === 2 && (
              <>
                <div>
                  <label className="block text-sm font-semibold text-textSoft mb-2">Current degree</label>
                  <div className="grid grid-cols-2 gap-2">
                    {CURRENT_DEGREES.map(d => (
                      <button key={d} type="button" onClick={() => set('current_degree', d)}
                        className={`py-2 px-3 rounded-lg border text-xs font-medium text-left transition-all
                          ${form.current_degree === d
                            ? 'border-lavender bg-lavendLight text-lavender shadow-sm'
                            : 'border-surfaceBorder bg-white text-textSoft hover:border-lavender/50'}`}>
                        {d}
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-semibold text-textSoft mb-1.5">
                    College / University <span className="text-muted font-normal">(optional)</span>
                  </label>
                  <input type="text" className="input-field"
                    placeholder="e.g. VIT Vellore, IIT Delhi, BITS Pilani…"
                    value={form.home_university} onChange={e => set('home_university', e.target.value)} />
                </div>

                <div>
                  <label className="block text-sm font-semibold text-textSoft mb-2">Field / Branch</label>
                  <div className="grid grid-cols-3 gap-1.5">
                    {FIELDS_OF_STUDY.map(f => (
                      <button key={f} type="button" onClick={() => set('field_of_study', f)}
                        className={`py-2 px-2 rounded-lg border text-center text-xs font-medium transition-all leading-tight
                          ${form.field_of_study === f
                            ? 'border-lavender bg-lavendLight text-lavender shadow-sm'
                            : 'border-surfaceBorder bg-white text-textSoft hover:border-lavender/50'}`}>
                        {f}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-sm font-semibold text-textSoft mb-1.5">
                      CGPA <span className="font-normal text-muted">(out of 10)</span>
                    </label>
                    <input type="number" required min="0" max="10" step="0.01" className="input-field"
                      placeholder="e.g. 8.5"
                      value={form.cgpa} onChange={e => set('cgpa', e.target.value)} />
                  </div>
                  <div>
                    <label className="block text-sm font-semibold text-textSoft mb-1.5">Graduation year</label>
                    <select className="input-field" value={form.graduation_year}
                      onChange={e => set('graduation_year', e.target.value)}>
                      {[2024, 2025, 2026, 2027, 2028].map(y => (
                        <option key={y} value={y}>{y}</option>
                      ))}
                    </select>
                  </div>
                </div>
              </>
            )}

            {/* ── Step 3: Test scores & experience ── */}
            {step === 3 && (
              <>
                <p className="text-xs text-muted bg-surfaceAlt rounded-lg p-3 border border-surfaceBorder">
                  ℹ️ All fields on this step are optional. Add what you have — you can update later.
                </p>

                <div>
                  <label className="block text-sm font-semibold text-textSoft mb-2">English test</label>
                  <div className="flex gap-2 flex-wrap">
                    {ENGLISH_TESTS.map(t => (
                      <button key={t} type="button" onClick={() => set('english_test', t)}
                        className={`px-3 py-2 rounded-lg border text-xs font-semibold transition-all
                          ${form.english_test === t
                            ? 'border-lavender bg-lavendLight text-lavender'
                            : 'border-surfaceBorder bg-white text-textSoft hover:border-lavender/50'}`}>
                        {t}
                      </button>
                    ))}
                  </div>
                </div>

                {form.english_test && form.english_test !== 'Not yet taken' && (
                  <div className="grid grid-cols-2 gap-3">
                    {(form.english_test === 'IELTS' || form.english_test === 'PTE') && (
                      <div>
                        <label className="block text-sm font-semibold text-textSoft mb-1.5">
                          {form.english_test} score
                          <span className="font-normal text-muted ml-1">
                            {form.english_test === 'IELTS' ? '(0–9 band)' : '(10–90)'}
                          </span>
                        </label>
                        <input type="number" min="0" max="90" step="0.5" className="input-field"
                          placeholder={form.english_test === 'IELTS' ? 'e.g. 7.5' : 'e.g. 65'}
                          value={form.english_score} onChange={e => set('english_score', e.target.value)} />
                      </div>
                    )}
                    {form.english_test === 'TOEFL' && (
                      <div>
                        <label className="block text-sm font-semibold text-textSoft mb-1.5">
                          TOEFL iBT score <span className="font-normal text-muted">(0–120)</span>
                        </label>
                        <input type="number" min="0" max="120" className="input-field"
                          placeholder="e.g. 105"
                          value={form.toefl_score} onChange={e => set('toefl_score', e.target.value)} />
                      </div>
                    )}
                    {form.english_test === 'Duolingo' && (
                      <div>
                        <label className="block text-sm font-semibold text-textSoft mb-1.5">
                          Duolingo score <span className="font-normal text-muted">(10–160)</span>
                        </label>
                        <input type="number" min="10" max="160" className="input-field"
                          placeholder="e.g. 120"
                          value={form.english_score} onChange={e => set('english_score', e.target.value)} />
                      </div>
                    )}
                  </div>
                )}

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-sm font-semibold text-textSoft mb-1.5">
                      GRE score <span className="font-normal text-muted">(260–340)</span>
                    </label>
                    <input type="number" min="260" max="340" className="input-field"
                      placeholder="e.g. 320"
                      value={form.gre_score} onChange={e => set('gre_score', e.target.value)} />
                  </div>
                  <div>
                    <label className="block text-sm font-semibold text-textSoft mb-1.5">
                      GMAT score <span className="font-normal text-muted">(200–800)</span>
                    </label>
                    <input type="number" min="200" max="800" className="input-field"
                      placeholder="e.g. 680"
                      value={form.gmat_score} onChange={e => set('gmat_score', e.target.value)} />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-semibold text-textSoft mb-1.5">
                    Work experience <span className="font-normal text-muted">(years full-time)</span>
                  </label>
                  <div className="flex gap-2 flex-wrap">
                    {['0', '1', '2', '3', '4', '5+'].map(y => (
                      <button key={y} type="button"
                        onClick={() => set('work_experience_years', y === '5+' ? '5' : y)}
                        className={`px-4 py-2 rounded-lg border text-sm font-semibold transition-all
                          ${form.work_experience_years === (y === '5+' ? '5' : y)
                            ? 'border-lavender bg-lavendLight text-lavender'
                            : 'border-surfaceBorder bg-white text-textSoft hover:border-lavender/50'}`}>
                        {y}
                      </button>
                    ))}
                  </div>
                </div>
              </>
            )}

            {/* ── Step 4: Study goals ── */}
            {step === 4 && (
              <>
                <div>
                  <label className="block text-sm font-semibold text-textSoft mb-2">Target degree</label>
                  <div className="grid grid-cols-2 gap-2">
                    {TARGET_DEGREES.map(d => (
                      <button key={d.value} type="button" onClick={() => set('preferred_degree', d.value)}
                        className={`py-2.5 px-3 rounded-xl border text-left transition-all
                          ${form.preferred_degree === d.value
                            ? 'border-lavender bg-lavendLight shadow-sm'
                            : 'border-surfaceBorder bg-white hover:border-lavender/50'}`}>
                        <p className={`text-sm font-bold ${form.preferred_degree === d.value ? 'text-lavender' : 'text-text'}`}>
                          {d.label}
                        </p>
                        <p className="text-xs text-muted">{d.sub}</p>
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-semibold text-textSoft mb-2">
                    Target countries <span className="text-muted font-normal">(select all that interest you)</span>
                  </label>
                  <div className="grid grid-cols-4 gap-1.5 sm:grid-cols-7">
                    {COUNTRIES.map(({ code, flag, label }) => {
                      const selected = form.target_countries.includes(code);
                      return (
                        <button key={code} type="button" onClick={() => toggleCountry(code)}
                          className={`flex flex-col items-center gap-1 py-2.5 px-1 rounded-xl border text-center transition-all text-xs font-medium
                            ${selected
                              ? 'border-lavender bg-lavendLight text-lavender shadow-sm'
                              : 'border-surfaceBorder bg-white text-textSoft hover:border-lavender/50'}`}>
                          <span className="text-xl">{flag}</span>
                          <span>{label}</span>
                        </button>
                      );
                    })}
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-sm font-semibold text-textSoft mb-2">Preferred intake</label>
                    <div className="space-y-2">
                      {INTAKE_OPTIONS.map(o => (
                        <button key={o.value} type="button" onClick={() => set('intake_preference', o.value)}
                          className={`w-full py-2 px-3 rounded-lg border text-left transition-all
                            ${form.intake_preference === o.value
                              ? 'border-lavender bg-lavendLight'
                              : 'border-surfaceBorder bg-white hover:border-lavender/50'}`}>
                          <p className={`text-sm font-bold ${form.intake_preference === o.value ? 'text-lavender' : 'text-text'}`}>{o.label}</p>
                          <p className="text-xs text-muted">{o.sub}</p>
                        </button>
                      ))}
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-textSoft mb-2">University ranking</label>
                    <div className="space-y-2">
                      {RANKING_OPTIONS.map(o => (
                        <button key={o.value} type="button" onClick={() => set('ranking_preference', o.value)}
                          className={`w-full py-2 px-3 rounded-lg border text-left transition-all
                            ${form.ranking_preference === o.value
                              ? 'border-lavender bg-lavendLight'
                              : 'border-surfaceBorder bg-white hover:border-lavender/50'}`}>
                          <p className={`text-sm font-bold ${form.ranking_preference === o.value ? 'text-lavender' : 'text-text'}`}>{o.label}</p>
                          <p className="text-xs text-muted">{o.sub}</p>
                        </button>
                      ))}
                    </div>
                  </div>
                </div>

                <label className="flex items-center gap-3 p-3 border border-surfaceBorder rounded-xl cursor-pointer hover:bg-surfaceAlt transition-colors">
                  <div
                    className={`w-10 h-5 rounded-full transition-colors relative flex-shrink-0 ${form.work_abroad_interest ? 'bg-lavender' : 'bg-surfaceBorder'}`}
                    onClick={() => set('work_abroad_interest', !form.work_abroad_interest)}>
                    <div className={`absolute top-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform ${form.work_abroad_interest ? 'translate-x-5' : 'translate-x-0.5'}`} />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-text">I want to work after graduation</p>
                    <p className="text-xs text-muted">Factors post-study work visa into recommendations</p>
                  </div>
                </label>
              </>
            )}

            {/* ── Step 5: Career & Life ── */}
            {step === 5 && (
              <>
                <p className="text-xs text-muted bg-surfaceAlt rounded-lg p-3 border border-surfaceBorder">
                  ℹ️ All fields are optional — the more you fill, the better your matches.
                </p>

                <div>
                  <label className="block text-sm font-semibold text-textSoft mb-2">Career goal</label>
                  <div className="grid grid-cols-2 gap-2">
                    {CAREER_GOALS.map(o => (
                      <button key={o.value} type="button" onClick={() => set('career_goal', o.value)}
                        className={`py-2.5 px-3 rounded-xl border text-left transition-all
                          ${form.career_goal === o.value
                            ? 'border-lavender bg-lavendLight shadow-sm'
                            : 'border-surfaceBorder bg-white hover:border-lavender/50'}`}>
                        <p className={`text-sm font-bold ${form.career_goal === o.value ? 'text-lavender' : 'text-text'}`}>{o.label}</p>
                        <p className="text-xs text-muted">{o.sub}</p>
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-semibold text-textSoft mb-2">Study priority</label>
                  <div className="grid grid-cols-2 gap-2">
                    {STUDY_PRIORITIES.map(o => (
                      <button key={o.value} type="button" onClick={() => set('study_priority', o.value)}
                        className={`py-2.5 px-3 rounded-xl border text-left transition-all
                          ${form.study_priority === o.value
                            ? 'border-lavender bg-lavendLight shadow-sm'
                            : 'border-surfaceBorder bg-white hover:border-lavender/50'}`}>
                        <p className={`text-sm font-bold ${form.study_priority === o.value ? 'text-lavender' : 'text-text'}`}>{o.label}</p>
                        <p className="text-xs text-muted">{o.sub}</p>
                      </button>
                    ))}
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-sm font-semibold text-textSoft mb-2">Preferred environment</label>
                    <div className="space-y-2">
                      {ENVIRONMENT_OPTIONS.map(o => (
                        <button key={o.value} type="button" onClick={() => set('preferred_environment', o.value)}
                          className={`w-full py-2 px-3 rounded-lg border text-left transition-all
                            ${form.preferred_environment === o.value
                              ? 'border-lavender bg-lavendLight'
                              : 'border-surfaceBorder bg-white hover:border-lavender/50'}`}>
                          <p className={`text-sm font-bold ${form.preferred_environment === o.value ? 'text-lavender' : 'text-text'}`}>{o.label}</p>
                          <p className="text-xs text-muted">{o.sub}</p>
                        </button>
                      ))}
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-semibold text-textSoft mb-2">Living preference</label>
                    <div className="space-y-2">
                      {LIVING_OPTIONS.map(o => (
                        <button key={o.value} type="button" onClick={() => set('living_preference', o.value)}
                          className={`w-full py-2 px-3 rounded-lg border text-left transition-all
                            ${form.living_preference === o.value
                              ? 'border-lavender bg-lavendLight'
                              : 'border-surfaceBorder bg-white hover:border-lavender/50'}`}>
                          <p className={`text-sm font-bold ${form.living_preference === o.value ? 'text-lavender' : 'text-text'}`}>{o.label}</p>
                          <p className="text-xs text-muted">{o.sub}</p>
                        </button>
                      ))}
                    </div>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-semibold text-textSoft mb-2">Learning style</label>
                  <div className="grid grid-cols-2 gap-2">
                    {LEARNING_STYLES.map(o => (
                      <button key={o.value} type="button" onClick={() => set('learning_style', o.value)}
                        className={`py-2.5 px-3 rounded-xl border text-left transition-all
                          ${form.learning_style === o.value
                            ? 'border-lavender bg-lavendLight shadow-sm'
                            : 'border-surfaceBorder bg-white hover:border-lavender/50'}`}>
                        <p className={`text-sm font-bold ${form.learning_style === o.value ? 'text-lavender' : 'text-text'}`}>{o.label}</p>
                        <p className="text-xs text-muted">{o.sub}</p>
                      </button>
                    ))}
                  </div>
                </div>
              </>
            )}

            {/* ── Step 6: Budget ── */}
            {step === 6 && (
              <>
                <div>
                  <label className="block text-sm font-semibold text-textSoft mb-1.5">
                    Annual budget (tuition + living) in ₹
                  </label>
                  <div className="relative">
                    <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-muted font-semibold text-sm">₹</span>
                    <input type="number" required min="500000" className="input-field pl-8"
                      placeholder="e.g. 3000000"
                      value={form.budget_inr} onChange={e => set('budget_inr', e.target.value)} />
                  </div>
                  <p className="text-xs text-muted mt-1">
                    {form.budget_inr
                      ? `≈ $${Math.round(parseInt(form.budget_inr) / 83).toLocaleString()} USD/year`
                      : 'Includes tuition fees + accommodation + living costs for one year'}
                  </p>
                  <div className="flex gap-2 mt-2 flex-wrap">
                    {BUDGET_PRESETS_INR.map(p => (
                      <button key={p.value} type="button"
                        onClick={() => set('budget_inr', String(p.value))}
                        className={`flex-1 py-1.5 rounded-lg text-xs font-semibold border transition-all
                          ${form.budget_inr === String(p.value)
                            ? 'bg-lavender text-white border-lavender'
                            : 'bg-white text-textSoft border-surfaceBorder hover:border-lavender/50'}`}>
                        {p.label}
                      </button>
                    ))}
                  </div>
                </div>

                <label className="flex items-center gap-3 p-3.5 border border-surfaceBorder rounded-xl cursor-pointer hover:bg-surfaceAlt transition-colors">
                  <div
                    className={`w-10 h-5 rounded-full transition-colors relative flex-shrink-0 ${form.scholarship_interest ? 'bg-lavender' : 'bg-surfaceBorder'}`}
                    onClick={() => set('scholarship_interest', !form.scholarship_interest)}>
                    <div className={`absolute top-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform ${form.scholarship_interest ? 'translate-x-5' : 'translate-x-0.5'}`} />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-text">I'm interested in scholarships</p>
                    <p className="text-xs text-muted">We'll highlight universities with strong merit scholarships for Indian students</p>
                  </div>
                </label>

                <div className="bg-lavendLight/50 border border-lavender/20 rounded-xl p-4 text-sm text-textSoft">
                  <p className="font-semibold text-lavender mb-1">Quick budget reference (₹ per year)</p>
                  <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
                    {[
                      ['Germany (public)', '₹8–15 L/yr'],
                      ['Canada (incl. living)', '₹25–40 L/yr'],
                      ['UK (London)', '₹35–55 L/yr'],
                      ['USA (top 100)', '₹40–60 L/yr'],
                      ['Australia', '₹30–50 L/yr'],
                      ['Singapore', '₹35–55 L/yr'],
                    ].map(([k, v]) => (
                      <div key={k} className="flex justify-between">
                        <span className="text-muted">{k}</span>
                        <span className="font-semibold text-text">{v}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </>
            )}

            {/* Navigation */}
            <div className="flex gap-3 pt-2">
              {step > 1 && (
                <button type="button" onClick={back}
                  className="btn-secondary flex items-center gap-2 px-5 py-3">
                  <ArrowLeft className="w-4 h-4" /> Back
                </button>
              )}
              <button type="submit" disabled={loading}
                className="btn-primary flex-1 py-3 text-[15px] flex items-center justify-center gap-2">
                {loading
                  ? 'Creating account…'
                  : isLastStep
                    ? <><GraduationCap className="w-4 h-4" /> Create account &amp; get OTP</>
                    : step === 3
                      ? <><span>Continue</span><ArrowRight className="w-4 h-4" /></>
                      : <><span>Continue</span><ArrowRight className="w-4 h-4" /></>
                }
              </button>
            </div>

            {step === 3 && (
              <button type="button" onClick={next}
                className="w-full text-center text-sm text-muted hover:text-lavender transition-colors">
                Skip test scores for now →
              </button>
            )}
          </form>

          <p className="text-center text-sm text-muted mt-5">
            Already have an account?{' '}
            <Link to="/login" className="text-lavender font-semibold hover:underline">Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
