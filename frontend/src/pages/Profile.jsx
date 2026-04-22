import { useState, useEffect } from 'react';
import { authAPI } from '../api/auth';
import { universitiesAPI } from '../api/universities';
import { 
  User, Mail, Lock, GraduationCap, BookOpen, Clock, 
  Calendar, DollarSign, Save, Loader2, CheckCircle2, ShieldCheck, Key,
  Target, Zap, MapPin, Building2, Coffee, Sparkles, Plus, Trash2, Award, History
} from 'lucide-react';

const FALLBACK_COUNTRIES = ['USA','UK','Germany','France','Netherlands','Australia','Singapore','Hong Kong','Spain','Switzerland','Finland'];
const DEGREE_LEVELS = ['High School', 'Diploma', 'Bachelors', 'Masters', 'PhD'];
const TEST_NAMES = ['IELTS', 'TOEFL', 'PTE', 'Duolingo', 'GRE', 'GMAT', 'SAT', 'ACT'];
const CURRENT_DEGREES = [
  'B.Tech / B.E.', 'B.Sc', 'BCA', 'B.Com', 'BBA / BBM',
  'BA', 'MBBS / BDS', 'LLB', 'B.Arch', 'Other'
];
const FIELDS_OF_STUDY = [
  'Computer Science', 'Data Science / AI', 'Electrical Engineering',
  'Mechanical Engineering', 'Civil Engineering', 'Chemical Engineering',
  'Business / MBA', 'Finance / Economics', 'Marketing',
  'Medicine / Public Health', 'Law', 'Architecture / Design',
  'Physics / Mathematics', 'Biotechnology', 'Psychology'
];
const TARGET_DEGREES = ['Masters', 'MBA', 'PhD', 'Bachelors', 'Diploma', 'Other'];
const ENGLISH_TESTS = ['IELTS', 'TOEFL', 'PTE', 'Duolingo', 'Not yet taken'];
const INTAKE_OPTIONS = ['Fall', 'Spring', 'Winter'];
const RANKING_OPTIONS = ['Top 50', 'Top 100', 'Top 200', 'Any'];
const LIVING_OPTIONS = ['Urban', 'Campus', 'Flexible'];

export default function Profile() {
  const [activeTab, setActiveTab] = useState('personal'); // 'personal', 'strategy', or 'security'
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState('');
  const [error, setError] = useState('');
  const [countries, setCountries] = useState(FALLBACK_COUNTRIES);

  const [form, setForm] = useState({
    email: '',
    full_name: '',
    current_degree: '',
    home_university: '',
    field_of_study: '',
    cgpa: '',
    graduation_year: '',
    english_test: '',
    english_score: '',
    toefl_score: '',
    gre_score: '',
    gmat_score: '',
    budget: '',
    budget_inr: '',
    work_experience_years: '',
    preferred_degree: '',
    intake_preference: '',
    ranking_preference: '',
    work_abroad_interest: false,
    scholarship_interest: false,
    target_countries: [],
    degrees: [],
    tests: [],
    // Psychographic
    career_goal: '',
    preferred_environment: '',
    study_priority: '',
    learning_style: '',
    living_preference: ''
  });

  const [securityForm, setSecurityForm] = useState({
    newPassword: '',
    confirmPassword: ''
  });

  const fetchProfile = async () => {
    try {
      const data = await authAPI.getProfile();
      setForm({
        email: data.email || '',
        full_name: data.full_name || '',
        current_degree: data.current_degree || '',
        home_university: data.home_university || '',
        field_of_study: data.field_of_study || '',
        cgpa: data.cgpa ?? '',
        graduation_year: data.graduation_year ?? '',
        english_test: data.english_test || '',
        english_score: data.english_score ?? '',
        toefl_score: data.toefl_score ?? '',
        gre_score: data.gre_score ?? '',
        gmat_score: data.gmat_score ?? '',
        budget: data.budget ?? '',
        budget_inr: data.budget_inr ?? '',
        work_experience_years: data.work_experience_years ?? '',
        preferred_degree: data.preferred_degree || '',
        intake_preference: data.intake_preference || data.preferred_intake || '',
        ranking_preference: data.ranking_preference || '',
        work_abroad_interest: Boolean(data.work_abroad_interest),
        scholarship_interest: Boolean(data.scholarship_interest),
        target_countries: data.target_countries || [],
        degrees: data.degrees || [],
        tests: data.tests || [],
        career_goal: data.career_goal || '',
        preferred_environment: data.preferred_environment || '',
        study_priority: data.study_priority || '',
        learning_style: data.learning_style || '',
        living_preference: data.living_preference || ''
      });
    } catch (err) {
      setError('Failed to load profile');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const bootstrap = async () => {
      await fetchProfile();
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

    bootstrap();
  }, []);

  const handleUpdateProfile = async (e) => {
    if (e) e.preventDefault();
    setSaving(true);
    setError('');
    setSuccess('');
    try {
      const budgetInr = form.budget_inr ? parseInt(form.budget_inr, 10) : null;
      await authAPI.updateProfile({
        full_name: form.full_name || null,
        current_degree: form.current_degree || null,
        home_university: form.home_university || null,
        field_of_study: form.field_of_study || null,
        cgpa: form.cgpa !== '' ? parseFloat(form.cgpa) : null,
        graduation_year: form.graduation_year !== '' ? parseInt(form.graduation_year, 10) : null,
        english_test: form.english_test || null,
        english_score: form.english_score !== '' ? parseFloat(form.english_score) : null,
        toefl_score: form.toefl_score !== '' ? parseInt(form.toefl_score, 10) : null,
        gre_score: form.gre_score !== '' ? parseInt(form.gre_score, 10) : null,
        gmat_score: form.gmat_score !== '' ? parseInt(form.gmat_score, 10) : null,
        work_experience_years: form.work_experience_years !== '' ? parseFloat(form.work_experience_years) : null,
        preferred_degree: form.preferred_degree || null,
        intake_preference: form.intake_preference || null,
        ranking_preference: form.ranking_preference || null,
        work_abroad_interest: form.work_abroad_interest,
        budget_inr: budgetInr,
        budget: budgetInr ? Math.round(budgetInr / 83) : (form.budget ? parseInt(form.budget, 10) : null),
        scholarship_interest: form.scholarship_interest,
        target_countries: form.target_countries,
        career_goal: form.career_goal || null,
        preferred_environment: form.preferred_environment || null,
        study_priority: form.study_priority || null,
        learning_style: form.learning_style || null,
        living_preference: form.living_preference || null,
        degrees: form.degrees.map(d => ({
          ...d,
          cgpa: d.cgpa !== '' ? parseFloat(d.cgpa) : null
        })),
        tests: form.tests.map(t => ({
          ...t,
          score: t.score !== '' ? parseFloat(t.score) : null
        }))
      });
      setSuccess('Portfolio updated successfully!');
    } catch (err) {
      setError('Failed to update portfolio');
    } finally {
      setSaving(false);
    }
  };

  const handleUpdatePassword = async (e) => {
    e.preventDefault();
    if (securityForm.newPassword !== securityForm.confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    setSaving(true);
    setError('');
    setSuccess('');
    try {
      await authAPI.updateProfile({ password: securityForm.newPassword });
      setSuccess('Password changed successfully!');
      setSecurityForm({ newPassword: '', confirmPassword: '' });
    } catch (err) {
      setError('Failed to update password');
    } finally {
      setSaving(false);
    }
  };

  const toggleCountry = (c) => {
    setForm(prev => ({
      ...prev,
      target_countries: prev.target_countries.includes(c)
        ? prev.target_countries.filter(x => x !== c)
        : [...prev.target_countries, c]
    }));
  };

  // ── List Management Helpers ──────────────────────────────────────────────

  const addDegree = () => {
    setForm(prev => ({
      ...prev,
      degrees: [...prev.degrees, { degree_level: 'Bachelors', specialization: '', cgpa: '', institution: '', year_graduated: '' }]
    }));
  };

  const removeDegree = (index) => {
    setForm(prev => ({
      ...prev,
      degrees: prev.degrees.filter((_, i) => i !== index)
    }));
  };

  const updateDegree = (index, field, value) => {
    const newDegrees = [...form.degrees];
    newDegrees[index][field] = value;
    setForm(prev => ({ ...prev, degrees: newDegrees }));
  };

  const addTest = () => {
    setForm(prev => ({
      ...prev,
      tests: [...prev.tests, { test_name: 'IELTS', score: '', test_date: '' }]
    }));
  };

  const removeTest = (index) => {
    setForm(prev => ({
      ...prev,
      tests: prev.tests.filter((_, i) => i !== index)
    }));
  };

  const updateTest = (index, field, value) => {
    const newTests = [...form.tests];
    newTests[index][field] = value;
    setForm(prev => ({ ...prev, tests: newTests }));
  };

  if (loading) return <div className="flex justify-center p-20"><Loader2 className="w-8 h-8 text-lavender animate-spin"/></div>;

  return (
    <div className="space-y-6 animate-fade-in pb-20">
      <div className="page-header">
        <div className="page-icon bg-lavendLight"><History className="w-5 h-5 text-lavender"/></div>
        <div>
          <h1 className="text-2xl font-bold text-text">Academic Portfolio</h1>
          <p className="text-muted text-sm mt-0.5">Manage your global education history and standardized test assets</p>
        </div>
      </div>

      <div className="flex flex-wrap gap-2 p-1 bg-white/50 backdrop-blur-sm rounded-2xl border border-surfaceBorder w-fit shadow-sm">
        <button onClick={()=>setActiveTab('personal')}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all ${activeTab==='personal'?'bg-lavender text-white shadow-md':'text-textSoft hover:bg-lavender/5'}`}>
          <GraduationCap className="w-4 h-4"/> Academic History
        </button>
        <button onClick={()=>setActiveTab('strategy')}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all ${activeTab==='strategy'?'bg-peach text-white shadow-md':'text-textSoft hover:bg-peach/5'}`}>
          <Target className="w-4 h-4"/> AI Strategy
        </button>
        <button onClick={()=>setActiveTab('security')}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all ${activeTab==='security'?'bg-slate-700 text-white shadow-md':'text-textSoft hover:bg-slate-50'}`}>
          <ShieldCheck className="w-4 h-4"/> Security
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2">
          <div className="card p-8 min-h-[600px] flex flex-col">
            {success && <div className="bg-mintLight border border-mint/20 text-teal-600 rounded-xl px-4 py-3 text-sm mb-6 flex items-center gap-2 animate-fade-in"><CheckCircle2 className="w-4 h-4"/> {success}</div>}
            {error && <div className="bg-rose/10 border border-rose/20 text-rose rounded-xl px-4 py-3 text-sm mb-6 animate-shake">{error}</div>}

            {activeTab === 'personal' && (
              <form onSubmit={handleUpdateProfile} className="space-y-10 flex-1">
                {/* ── Section: Profile Basics ── */}
                <section className="space-y-6">
                  <div className="flex items-center gap-2">
                    <User className="w-4 h-4 text-lavender" />
                    <h3 className="text-sm font-bold text-text uppercase tracking-widest">Profile Basics</h3>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <label className="block text-[10px] font-bold text-muted uppercase mb-1.5 ml-1">Full Name</label>
                      <input type="text" value={form.full_name} onChange={e=>setForm({...form, full_name: e.target.value})} className="input-field" placeholder="Your full name" />
                    </div>
                    <div>
                      <label className="block text-[10px] font-bold text-muted uppercase mb-1.5 ml-1">Current Degree</label>
                      <select value={form.current_degree} onChange={e=>setForm({...form, current_degree: e.target.value})} className="input-field">
                        <option value="">Select degree</option>
                        {CURRENT_DEGREES.map(item => <option key={item} value={item}>{item}</option>)}
                      </select>
                    </div>
                    <div>
                      <label className="block text-[10px] font-bold text-muted uppercase mb-1.5 ml-1">Field of Study</label>
                      <select value={form.field_of_study} onChange={e=>setForm({...form, field_of_study: e.target.value})} className="input-field">
                        <option value="">Select field</option>
                        {FIELDS_OF_STUDY.map(item => <option key={item} value={item}>{item}</option>)}
                      </select>
                    </div>
                    <div>
                      <label className="block text-[10px] font-bold text-muted uppercase mb-1.5 ml-1">Home University</label>
                      <input type="text" value={form.home_university} onChange={e=>setForm({...form, home_university: e.target.value})} className="input-field" placeholder="Institution name" />
                    </div>
                    <div>
                      <label className="block text-[10px] font-bold text-muted uppercase mb-1.5 ml-1">CGPA</label>
                      <input type="number" step="0.01" value={form.cgpa} onChange={e=>setForm({...form, cgpa: e.target.value})} className="input-field" placeholder="e.g. 8.6" />
                    </div>
                    <div>
                      <label className="block text-[10px] font-bold text-muted uppercase mb-1.5 ml-1">Graduation Year</label>
                      <input type="number" value={form.graduation_year} onChange={e=>setForm({...form, graduation_year: e.target.value})} className="input-field" placeholder="2026" />
                    </div>
                  </div>
                </section>

                <section className="border-t border-surfaceBorder pt-10 space-y-6">
                  <div className="flex items-center gap-2">
                    <Award className="w-4 h-4 text-lavender" />
                    <h3 className="text-sm font-bold text-text uppercase tracking-widest">English and Test Scores</h3>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <label className="block text-[10px] font-bold text-muted uppercase mb-1.5 ml-1">English Test</label>
                      <select value={form.english_test} onChange={e=>setForm({...form, english_test: e.target.value})} className="input-field">
                        <option value="">Select test</option>
                        {ENGLISH_TESTS.map(item => <option key={item} value={item}>{item}</option>)}
                      </select>
                    </div>
                    <div>
                      <label className="block text-[10px] font-bold text-muted uppercase mb-1.5 ml-1">English Score</label>
                      <input type="number" step="0.01" value={form.english_score} onChange={e=>setForm({...form, english_score: e.target.value})} className="input-field" placeholder="7.5" />
                    </div>
                    <div>
                      <label className="block text-[10px] font-bold text-muted uppercase mb-1.5 ml-1">TOEFL Score</label>
                      <input type="number" value={form.toefl_score} onChange={e=>setForm({...form, toefl_score: e.target.value})} className="input-field" placeholder="105" />
                    </div>
                    <div>
                      <label className="block text-[10px] font-bold text-muted uppercase mb-1.5 ml-1">GRE Score</label>
                      <input type="number" value={form.gre_score} onChange={e=>setForm({...form, gre_score: e.target.value})} className="input-field" placeholder="320" />
                    </div>
                    <div>
                      <label className="block text-[10px] font-bold text-muted uppercase mb-1.5 ml-1">GMAT Score</label>
                      <input type="number" value={form.gmat_score} onChange={e=>setForm({...form, gmat_score: e.target.value})} className="input-field" placeholder="650" />
                    </div>
                  </div>
                </section>
                
                {/* ── Section: Degrees ── */}
                <section>
                  <div className="flex items-center justify-between mb-6">
                    <h3 className="text-sm font-bold text-text uppercase tracking-widest flex items-center gap-2">
                      <GraduationCap className="w-4 h-4 text-lavender"/> Academic Degrees
                    </h3>
                    <button type="button" onClick={addDegree} className="btn-ghost text-[10px] uppercase font-bold py-1 px-3 border border-lavender/20 rounded-lg">
                      <Plus className="w-3 h-3"/> Add Qualification
                    </button>
                  </div>
                  
                  <div className="space-y-4">
                    {form.degrees.length === 0 && (
                      <div className="border-2 border-dashed border-surfaceBorder rounded-2xl p-8 text-center">
                        <p className="text-xs text-muted">No degrees added. Click "Add Qualification" to begin.</p>
                      </div>
                    )}
                    {form.degrees.map((deg, idx) => (
                      <div key={idx} className="group relative bg-surfaceAlt border border-surfaceBorder rounded-2xl p-5 hover:border-lavender/30 transition-all">
                        <button type="button" onClick={()=>removeDegree(idx)} className="absolute top-4 right-4 text-muted hover:text-rose opacity-0 group-hover:opacity-100 transition-opacity">
                          <Trash2 className="w-4 h-4"/>
                        </button>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                          <div>
                            <label className="block text-[10px] font-bold text-muted uppercase mb-1.5">Degree Level</label>
                            <select value={deg.degree_level} onChange={e=>updateDegree(idx, 'degree_level', e.target.value)} className="input-field py-2">
                              {DEGREE_LEVELS.map(d=><option key={d} value={d}>{d}</option>)}
                            </select>
                          </div>
                          <div className="md:col-span-2">
                            <label className="block text-[10px] font-bold text-muted uppercase mb-1.5">Major / Specialization</label>
                            <input type="text" value={deg.specialization} onChange={e=>updateDegree(idx, 'specialization', e.target.value)} placeholder="e.g. Computer Science" className="input-field"/>
                          </div>
                          <div className="md:col-span-2">
                            <label className="block text-[10px] font-bold text-muted uppercase mb-1.5">Institution / University</label>
                            <input type="text" value={deg.institution} onChange={e=>updateDegree(idx, 'institution', e.target.value)} placeholder="e.g. IIT Bombay" className="input-field"/>
                          </div>
                          <div>
                            <label className="block text-[10px] font-bold text-muted uppercase mb-1.5">CGPA / GPA</label>
                            <input type="number" step="0.1" value={deg.cgpa} onChange={e=>updateDegree(idx, 'cgpa', e.target.value)} placeholder="0.0" className="input-field"/>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </section>

                {/* ── Section: Tests ── */}
                <section className="border-t border-surfaceBorder pt-10">
                  <div className="flex items-center justify-between mb-6">
                    <h3 className="text-sm font-bold text-text uppercase tracking-widest flex items-center gap-2">
                      <Award className="w-4 h-4 text-lavender"/> Standardized Tests
                    </h3>
                    <button type="button" onClick={addTest} className="btn-ghost text-[10px] uppercase font-bold py-1 px-3 border border-lavender/20 rounded-lg">
                      <Plus className="w-3 h-3"/> Add Test Score
                    </button>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {form.tests.map((test, idx) => (
                      <div key={idx} className="group relative bg-white border border-surfaceBorder rounded-2xl p-4 shadow-sm hover:ring-1 hover:ring-lavender/30 transition-all">
                        <button type="button" onClick={()=>removeTest(idx)} className="absolute top-4 right-4 text-muted hover:text-rose opacity-0 group-hover:opacity-100 transition-opacity">
                          <Trash2 className="w-3 h-3"/>
                        </button>
                        <div className="flex gap-4">
                          <div className="flex-1">
                            <label className="block text-[10px] font-bold text-muted uppercase mb-1">Test Name</label>
                            <select value={test.test_name} onChange={e=>updateTest(idx, 'test_name', e.target.value)} className="input-field py-1 text-xs">
                              {TEST_NAMES.map(t=><option key={t} value={t}>{t}</option>)}
                            </select>
                          </div>
                          <div className="w-24">
                            <label className="block text-[10px] font-bold text-muted uppercase mb-1">Score</label>
                            <input type="number" step="0.1" value={test.score} onChange={e=>updateTest(idx, 'score', e.target.value)} placeholder="0.0" className="input-field py-1 text-xs text-center"/>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </section>

                {/* ── Section: Goals & Financials ── */}
                <section className="border-t border-surfaceBorder pt-10">
                  <h3 className="text-xs font-bold text-muted uppercase tracking-widest flex items-center gap-2 mb-6">
                    <DollarSign className="w-4 h-4 text-lavender"/> Goals & Financials
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <label className="block text-[10px] font-bold text-muted uppercase mb-1.5 ml-1">Target Degree</label>
                      <select value={form.preferred_degree} onChange={e=>setForm({...form, preferred_degree: e.target.value})} className="input-field">
                        <option value="">Select target degree</option>
                        {TARGET_DEGREES.map(item => <option key={item} value={item}>{item}</option>)}
                      </select>
                    </div>
                    <div>
                      <label className="block text-[10px] font-bold text-muted uppercase mb-1.5 ml-1">Target Intake</label>
                      <select value={form.intake_preference} onChange={e=>setForm({...form, intake_preference: e.target.value})} className="input-field">
                        <option value="">Select intake</option>
                        {INTAKE_OPTIONS.map(item => <option key={item} value={item}>{item}</option>)}
                      </select>
                    </div>
                    <div>
                      <label className="block text-[10px] font-bold text-muted uppercase mb-1.5 ml-1">Ranking Preference</label>
                      <select value={form.ranking_preference} onChange={e=>setForm({...form, ranking_preference: e.target.value})} className="input-field">
                        <option value="">Select preference</option>
                        {RANKING_OPTIONS.map(item => <option key={item} value={item}>{item}</option>)}
                      </select>
                    </div>
                    <div>
                      <label className="block text-[10px] font-bold text-muted uppercase mb-1.5 ml-1">Budget in INR</label>
                      <input type="number" value={form.budget_inr} onChange={e=>setForm({...form, budget_inr: e.target.value})} className="input-field" placeholder="5000000" />
                    </div>
                    <div>
                      <label className="block text-[10px] font-bold text-muted uppercase mb-1.5 ml-1">Current Work Exp (Yrs)</label>
                      <input type="number" value={form.work_experience_years} onChange={e=>setForm({...form, work_experience_years: e.target.value})} className="input-field"/>
                    </div>
                    <div>
                      <label className="block text-[10px] font-bold text-muted uppercase mb-1.5 ml-1">Scholarship Interest</label>
                      <button type="button" onClick={()=>setForm({...form, scholarship_interest: !form.scholarship_interest})} className={`w-full py-3 rounded-xl border text-xs font-bold transition-all ${form.scholarship_interest ? 'bg-mint text-white border-mint shadow-md' : 'bg-white border-surfaceBorder hover:border-mint text-textSoft'}`}>
                        {form.scholarship_interest ? 'Scholarship support desired' : 'No scholarship preference selected'}
                      </button>
                    </div>
                  </div>
                </section>

                <div className="mt-auto pt-8 border-t border-surfaceBorder flex justify-end">
                  <button type="submit" disabled={saving} className="btn-primary px-10">
                    {saving ? <Loader2 className="w-4 h-4 animate-spin"/> : <><Save className="w-4 h-4"/> Commit Global Portfolio</>}
                  </button>
                </div>
              </form>
            )}

            {activeTab === 'strategy' && (
              <div className="space-y-8 flex-1 animate-slide-up">
                {/* ... (Keep existing strategy tab content, it was already well-implemented) ... */}
                <div className="bg-peach/5 border border-peach/10 rounded-2xl p-6 mb-4">
                  <div className="flex items-center gap-3 mb-2">
                    <Sparkles className="w-5 h-5 text-peach animate-pulse"/>
                    <h3 className="font-bold text-peach text-sm uppercase tracking-wider">Psychographic Blueprint</h3>
                  </div>
                  <p className="text-xs text-muted leading-relaxed">
                    These deep preferences dictate the **weights** our Agentic Chain applies to your university search. 
                    Changes here will fundamentally shift your "Top 3" recommendations.
                  </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                  <div className="space-y-6">
                    <div>
                      <label className="block text-[10px] font-bold text-muted uppercase mb-3 ml-1 tracking-widest">Main Career Goal</label>
                      <select value={form.career_goal} onChange={e=>setForm({...form, career_goal: e.target.value})} className="input-field-peach py-2 font-bold text-xs">
                        <option value="Industry">High-Growth Industry (Tech/Finance)</option>
                        <option value="Research">Academic Research / PhD Track</option>
                        <option value="Entrepreneur">Entrepreneurial / Startup Ecosystem</option>
                        <option value="Pivot">Career Transformation / Pivot</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-[10px] font-bold text-muted uppercase mb-3 ml-1 tracking-widest">Preferred Environment</label>
                      <div className="grid grid-cols-2 gap-2">
                        {['Urban', 'Campus'].map(env => (
                          <button key={env} type="button" onClick={()=>setForm({...form, preferred_environment: env})}
                            className={`px-4 py-3 rounded-xl border text-[10px] font-bold transition-all ${form.preferred_environment===env?'bg-peach text-white border-peach shadow-md':'bg-white border-surfaceBorder hover:border-peach text-textSoft'}`}>
                            {env === 'Urban' ? '🏙️ Metropolitan' : '🎓 University Town'}
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>

                  <div className="space-y-6">
                    <div>
                      <label className="block text-[10px] font-bold text-muted uppercase mb-3 ml-1 tracking-widest">Primary Selection Driver</label>
                      <select value={form.study_priority} onChange={e=>setForm({...form, study_priority: e.target.value})} className="input-field-peach py-2 font-bold text-xs">
                        <option value="Ranking">Global Ranking & Prestige</option>
                        <option value="Budget">ROI & Budget Efficiency</option>
                        <option value="Work">Post-Study Working Rights (VWP)</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-[10px] font-bold text-muted uppercase mb-3 ml-1 tracking-widest">Learning Style</label>
                      <div className="flex gap-2">
                        {['Practical', 'Theoretical', 'Hybrid'].map(style => (
                          <button key={style} type="button" onClick={()=>setForm({...form, learning_style: style})}
                            className={`flex-1 py-3 rounded-xl border text-[10px] font-bold transition-all ${form.learning_style===style?'bg-peach text-white border-peach shadow-md':'bg-white border-surfaceBorder hover:border-peach text-textSoft'}`}>
                            {style}
                          </button>
                        ))}
                      </div>
                    </div>
                    <div>
                      <label className="block text-[10px] font-bold text-muted uppercase mb-3 ml-1 tracking-widest">Living Preference</label>
                      <div className="grid grid-cols-3 gap-2">
                        {LIVING_OPTIONS.map(option => (
                          <button key={option} type="button" onClick={()=>setForm({...form, living_preference: option})}
                            className={`py-3 rounded-xl border text-[10px] font-bold transition-all ${form.living_preference===option?'bg-peach text-white border-peach shadow-md':'bg-white border-surfaceBorder hover:border-peach text-textSoft'}`}>
                            {option}
                          </button>
                        ))}
                      </div>
                    </div>
                    <div className="flex items-center justify-between rounded-xl border border-surfaceBorder bg-white px-4 py-3">
                      <div>
                        <p className="text-[10px] font-bold text-muted uppercase tracking-widest">Work Abroad Interest</p>
                        <p className="text-xs text-textSoft">Use this to bias recommendations toward post-study work pathways.</p>
                      </div>
                      <button type="button" onClick={()=>setForm({...form, work_abroad_interest: !form.work_abroad_interest})} className={`px-4 py-2 rounded-lg text-[10px] font-bold border transition-all ${form.work_abroad_interest ? 'bg-peach text-white border-peach shadow-md' : 'bg-surfaceAlt border-surfaceBorder text-textSoft hover:border-peach'}`}>
                        {form.work_abroad_interest ? 'Enabled' : 'Disabled'}
                      </button>
                    </div>
                  </div>
                </div>

                <div className="border-t border-surfaceBorder pt-8">
                  <label className="block text-[10px] font-bold text-muted uppercase mb-4 ml-1 tracking-widest">Target Geographical Zones</label>
                  <div className="flex flex-wrap gap-2">
                    {countries.map(c => (
                      <button key={c} type="button" onClick={()=>toggleCountry(c)}
                        className={`px-3 py-1.5 rounded-lg text-[10px] font-bold border transition-all ${
                          form.target_countries.includes(c)
                            ? 'bg-peach text-white border-peach shadow-md'
                            : 'bg-surfaceAlt text-textSoft border-surfaceBorder hover:border-peach hover:text-peach'
                        }`}>
                        {c}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="mt-auto pt-8 border-t border-surfaceBorder flex justify-end">
                  <button type="button" onClick={handleUpdateProfile} disabled={saving} className="btn-peach px-10">
                    {saving ? <Loader2 className="w-4 h-4 animate-spin"/> : <><Sparkles className="w-4 h-4"/> Update AI Strategy</>}
                  </button>
                </div>
              </div>
            )}

            {activeTab === 'security' && (
              <form onSubmit={handleUpdatePassword} className="space-y-6 max-w-md animate-slide-right pt-4 flex-1">
                <h3 className="text-sm font-bold text-text mb-6 uppercase tracking-widest flex items-center gap-2">
                  <ShieldCheck className="w-5 h-5 text-slate-700"/> Account Security
                </h3>
                <div className="bg-slate-50 border border-slate-100 rounded-2xl p-6 space-y-4">
                  <div>
                    <label className="block text-[10px] font-bold text-muted uppercase mb-1.5 ml-1">New Password</label>
                    <input type="password" required value={securityForm.newPassword} onChange={e=>setSecurityForm({...securityForm, newPassword: e.target.value})} className="input-field" placeholder="••••••••"/>
                  </div>
                  <div>
                    <label className="block text-[10px] font-bold text-muted uppercase mb-1.5 ml-1">Confirm New Password</label>
                    <input type="password" required value={securityForm.confirmPassword} onChange={e=>setSecurityForm({...securityForm, confirmPassword: e.target.value})} className="input-field" placeholder="••••••••"/>
                  </div>
                </div>
                <div className="flex justify-start">
                  <button type="submit" disabled={saving} className="bg-slate-800 text-white font-bold text-xs py-3 px-8 rounded-xl hover:bg-slate-900 transition-all shadow-lg flex items-center gap-2">
                    {saving ? <Loader2 className="w-4 h-4 animate-spin"/> : <><Key className="w-4 h-4"/> Update Credentials</>}
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>

        <div className="lg:col-span-1">
          <div className="card p-6 bg-gradient-to-br from-lavender/5 to-white border-lavender/10 sticky top-8">
            <h3 className="font-bold text-text mb-6 flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-lavender"/> Strategy Metrics
            </h3>
            <div className="space-y-6">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-white rounded-2xl flex items-center justify-center shadow-md text-lavender font-bold text-xl border border-lavendLight">
                  {form.email[0]?.toUpperCase()}
                </div>
                <div>
                  <p className="text-[10px] text-muted font-bold uppercase tracking-wider">Active Strategist</p>
                  <p className="text-sm font-bold text-text truncate max-w-[150px]">{form.email}</p>
                </div>
              </div>

              <div className="pt-6 border-t border-surfaceBorder space-y-3">
                 <div className="flex justify-between items-center text-[10px] font-bold">
                    <span className="text-muted uppercase">Onboarding Health</span>
                    <span className="text-mint uppercase">100% Verified</span>
                 </div>
                 <div className="flex flex-col gap-2">
                    <div className="flex items-center justify-between text-[9px] font-bold text-muted">
                        <span>Degrees: {form.degrees.length}</span>
                        <span>Tests: {form.tests.length}</span>
                    </div>
                    <div className="w-full h-1.5 bg-surfaceAlt rounded-full overflow-hidden">
                        <div className="h-full bg-mint rounded-full w-full shadow-glow"></div>
                    </div>
                 </div>
              </div>

              <div className="bg-white rounded-2xl p-4 border border-surfaceBorder space-y-3">
                 <div className="flex justify-between items-center">
                    <span className="text-[9px] font-bold text-muted uppercase">Career Focus</span>
                    <span className="text-[10px] font-bold text-peach uppercase">{form.career_goal || 'TBD'}</span>
                 </div>
                 <div className="flex justify-between items-center">
                    <span className="text-[9px] font-bold text-muted uppercase">Env Vibe</span>
                    <span className="text-[10px] font-bold text-lavender uppercase">{form.preferred_environment || 'TBD'}</span>
                 </div>
              </div>

              <div className="bg-mintLight p-4 rounded-2xl border border-mint/20 flex flex-col gap-2">
                <div className="flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-teal-600"/>
                  <span className="text-[10px] font-bold text-teal-800 uppercase tracking-wider">Decision Guard Active</span>
                </div>
                <p className="text-[9px] text-teal-700 leading-relaxed font-medium">
                  Your academic assets are now synced with our global RAG vector engine.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
