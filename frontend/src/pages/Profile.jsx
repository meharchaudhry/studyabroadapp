import { useState, useEffect, useRef } from 'react';
import { authAPI } from '../api/auth';
import api from '../api/client';
import {
  User, GraduationCap, Save, Loader2, CheckCircle2, ShieldCheck, Key,
  Target, Sparkles, History, ClipboardList, Upload, FileText, X, Zap
} from 'lucide-react';

const APP_COUNTRIES = [
  'United States', 'United Kingdom', 'Canada', 'Australia', 'Germany', 'France',
  'Netherlands', 'Ireland', 'Singapore', 'Japan', 'Sweden', 'Norway',
  'New Zealand', 'UAE', 'Switzerland', 'South Korea'
];
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
const CAREER_GOALS = [
  { value: 'tech industry', label: 'Tech Industry', sub: 'SWE, ML, product' },
  { value: 'finance', label: 'Finance', sub: 'Banking, consulting' },
  { value: 'academia', label: 'Academia', sub: 'Research, teaching' },
  { value: 'entrepreneurship', label: 'Entrepreneurship', sub: 'Startups, VC' },
  { value: 'healthcare', label: 'Healthcare', sub: 'Medicine, pharma' },
  { value: 'government', label: 'Government / NGO', sub: 'Policy, public sector' },
];
const STUDY_PRIORITIES = [
  { value: 'research', label: 'Research', sub: 'Publications & labs' },
  { value: 'internships', label: 'Internships', sub: 'Industry exposure' },
  { value: 'coursework', label: 'Coursework', sub: 'Structured curriculum' },
  { value: 'networking', label: 'Networking', sub: 'Alumni & industry connects' },
  { value: 'startup ecosystem', label: 'Startup Ecosystem', sub: 'Founders & investors' },
];
const ENVIRONMENT_OPTIONS = [
  { value: 'urban', label: 'Urban city', sub: 'NYC, London, Berlin' },
  { value: 'campus town', label: 'Campus town', sub: 'Oxford, Ann Arbor' },
  { value: 'small city', label: 'Small city', sub: 'Quiet, affordable' },
  { value: 'no preference', label: 'No preference', sub: 'Open to anything' },
];
const LEARNING_STYLES = [
  { value: 'seminars', label: 'Seminars', sub: 'Discussion-led' },
  { value: 'lectures', label: 'Lectures', sub: 'Traditional classes' },
  { value: 'online flexibility', label: 'Online flexible', sub: 'Hybrid / async' },
  { value: 'project-based', label: 'Project-based', sub: 'Hands-on builds' },
];
const LIVING_OPTIONS = [
  { value: 'on-campus', label: 'On-campus', sub: 'Dorms / student halls' },
  { value: 'shared house', label: 'Shared house', sub: 'With other students' },
  { value: 'studio', label: 'Studio / solo', sub: 'Private accommodation' },
  { value: 'no preference', label: 'No preference', sub: 'Flexible' },
];
const PASSWORD_COMPLEXITY_REGEX = /^(?=.*[A-Za-z])(?=.*\d).{8,}$/;

// ── CV Upload + AI Extraction Component ───────────────────────────────────────
function CVUploadBanner({ onExtracted }) {
  const [file, setFile]         = useState(null);
  const [loading, setLoading]   = useState(false);
  const [result, setResult]     = useState(null);
  const [error, setError]       = useState('');
  const [applied, setApplied]   = useState(false);
  const inputRef                = useRef(null);

  const handleFile = (f) => {
    if (!f) return;
    setFile(f);
    setResult(null);
    setError('');
    setApplied(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const f = e.dataTransfer.files?.[0];
    if (f) handleFile(f);
  };

  const extract = async () => {
    if (!file) return;
    setLoading(true);
    setError('');
    setResult(null);
    try {
      const fd = new FormData();
      fd.append('file', file);
      const resp = await api.post('/cv/extract', fd, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setResult(resp.data.extracted);
    } catch (e) {
      setError(e?.response?.data?.detail || 'Extraction failed. Try a text-based PDF.');
    } finally {
      setLoading(false);
    }
  };

  const apply = () => {
    if (!result) return;
    onExtracted(result);
    setApplied(true);
  };

  const FIELD_LABELS = {
    field_of_study: 'Field of Study',
    preferred_degree: 'Target Degree',
    cgpa: 'CGPA',
    english_test: 'English Test',
    english_score: 'English Score',
    toefl_score: 'TOEFL Score',
    gre_score: 'GRE Score',
    gmat_score: 'GMAT Score',
    work_experience_years: 'Work Experience (yrs)',
    career_goal: 'Career Goal',
    target_countries: 'Target Countries',
    education_summary: 'Education',
    experience_summary: 'Experience',
    projects_summary: 'Projects',
  };

  const displayFields = result
    ? Object.entries(result).filter(([k, v]) =>
        FIELD_LABELS[k] && v !== null && v !== undefined && v !== '' &&
        !(Array.isArray(v) && v.length === 0)
      )
    : [];

  return (
    <div className="mb-8 rounded-2xl border-2 border-dashed border-lavender/30 bg-lavendLight/20 overflow-hidden">
      {/* Header */}
      <div className="px-5 py-4 flex items-center gap-3 border-b border-lavender/10">
        <div className="w-8 h-8 bg-lavender/10 rounded-xl flex items-center justify-center">
          <Zap className="w-4 h-4 text-lavender" />
        </div>
        <div>
          <p className="text-sm font-bold text-text">AI CV Autofill</p>
          <p className="text-[11px] text-muted">Upload your resume — Gemini extracts and fills your profile automatically</p>
        </div>
      </div>

      <div className="p-5 space-y-4">
        {/* Drop zone */}
        {!result && (
          <div
            onDrop={handleDrop}
            onDragOver={e => e.preventDefault()}
            onClick={() => inputRef.current?.click()}
            className="border border-dashed border-lavender/40 rounded-xl p-6 text-center cursor-pointer hover:bg-lavendLight/30 transition-colors"
          >
            <input
              ref={inputRef}
              type="file"
              accept=".pdf,.docx,.doc,.txt"
              className="hidden"
              onChange={e => handleFile(e.target.files?.[0])}
            />
            {file ? (
              <div className="flex items-center justify-center gap-3">
                <FileText className="w-5 h-5 text-lavender" />
                <span className="text-sm font-medium text-text">{file.name}</span>
                <button
                  onClick={e => { e.stopPropagation(); setFile(null); setResult(null); }}
                  className="text-muted hover:text-rose transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <div>
                <Upload className="w-6 h-6 text-lavender/60 mx-auto mb-2" />
                <p className="text-sm text-muted">Drop your CV here or <span className="text-lavender font-semibold">browse</span></p>
                <p className="text-[11px] text-muted mt-1">PDF, DOCX, or TXT · max 5 MB</p>
              </div>
            )}
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="text-sm text-rose bg-rose/10 rounded-xl px-4 py-3 border border-rose/20">{error}</div>
        )}

        {/* Extract button */}
        {file && !result && (
          <button
            onClick={extract}
            disabled={loading}
            className="btn-primary w-full flex items-center justify-center gap-2 disabled:opacity-60"
          >
            {loading
              ? <><Loader2 className="w-4 h-4 animate-spin"/> Extracting with Gemini AI…</>
              : <><Sparkles className="w-4 h-4"/> Extract Profile from CV</>}
          </button>
        )}

        {/* Extracted fields preview */}
        {result && (
          <div className="space-y-3">
            <p className="text-xs font-bold text-muted uppercase tracking-wide">
              Extracted {displayFields.length} fields — review before applying
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-64 overflow-y-auto">
              {displayFields.map(([key, val]) => (
                <div key={key} className="bg-surface rounded-xl px-3 py-2 border border-surfaceBorder">
                  <p className="text-[10px] font-bold text-muted uppercase">{FIELD_LABELS[key]}</p>
                  <p className="text-sm text-text font-medium truncate">
                    {Array.isArray(val) ? val.join(', ') : String(val)}
                  </p>
                </div>
              ))}
            </div>

            {applied ? (
              <div className="flex items-center gap-2 text-sm text-teal-600 font-semibold">
                <CheckCircle2 className="w-4 h-4" /> Applied to profile! Review and save below.
              </div>
            ) : (
              <div className="flex gap-2">
                <button onClick={apply} className="btn-primary flex-1 flex items-center justify-center gap-2">
                  <CheckCircle2 className="w-4 h-4"/> Apply to Profile
                </button>
                <button
                  onClick={() => { setFile(null); setResult(null); }}
                  className="btn-ghost px-4"
                >
                  Discard
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function SaveChangesButton({ variant = 'primary', saving, onClick, type = 'button', label = 'Save Changes' }) {
  const variantClass = variant === 'peach' ? 'btn-peach' : 'btn-primary';
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={saving}
      className={`${variantClass} px-8 inline-flex items-center gap-2 min-h-[44px]`}
    >
      {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <><Save className="w-4 h-4" /> {label}</>}
    </button>
  );
}

export default function Profile() {
  const [activeTab, setActiveTab] = useState('personal'); // 'personal', 'strategy', or 'security'
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState('');
  const [error, setError] = useState('');

  const [form, setForm] = useState({
    is_verified: false,
    email: '',
    full_name: '',
    resume_filename: null,
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
    // Psychographic
    career_goal: '',
    preferred_environment: '',
    study_priority: '',
    learning_style: '',
    living_preference: '',
    degrees: [],
    tests: []
  });

  const [securityForm, setSecurityForm] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  });
  const setField = (key, value) => setForm(prev => ({ ...prev, [key]: value }));

  // Apply CV-extracted fields to the form
  const applyExtracted = (extracted) => {
    setForm(prev => {
      const next = { ...prev };
      if (extracted.field_of_study)       next.field_of_study       = extracted.field_of_study;
      if (extracted.preferred_degree)     next.preferred_degree     = extracted.preferred_degree;
      if (extracted.cgpa)                 next.cgpa                 = String(extracted.cgpa);
      if (extracted.english_test)         next.english_test         = extracted.english_test;
      if (extracted.english_score)        next.english_score        = String(extracted.english_score);
      if (extracted.toefl_score)          next.toefl_score          = String(extracted.toefl_score);
      if (extracted.gre_score)            next.gre_score            = String(extracted.gre_score);
      if (extracted.gmat_score)           next.gmat_score           = String(extracted.gmat_score);
      if (extracted.work_experience_years) next.work_experience_years = String(extracted.work_experience_years);
      if (extracted.career_goal)          next.career_goal          = extracted.career_goal;
      if (extracted.target_countries?.length) next.target_countries = extracted.target_countries;
      if (extracted.intake_preference)    next.intake_preference    = extracted.intake_preference;
      if (extracted.budget_inr)           next.budget_inr           = String(extracted.budget_inr);
      if (extracted.name && !prev.full_name) next.full_name         = extracted.name;
      return next;
    });
    setSuccess('CV data applied! Review the fields below and click Save Profile.');
    setTimeout(() => setSuccess(''), 5000);
  };

  const buildProfilePayload = () => {
    const budgetInr = form.budget_inr ? parseInt(form.budget_inr, 10) : null;
    return {
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
    };
  };

  const buildStrategyPayload = () => ({
    career_goal: form.career_goal || null,
    preferred_environment: form.preferred_environment || null,
    study_priority: form.study_priority || null,
    learning_style: form.learning_style || null,
    living_preference: form.living_preference || null,
  });

  const fetchProfile = async () => {
    try {
      const data = await authAPI.getProfile();
      setForm({
        is_verified: Boolean(data.is_verified),
        email: data.email || '',
        full_name: data.full_name || '',
        resume_filename: data.resume_filename || null,
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
        target_countries: (data.target_countries || []).filter(c => APP_COUNTRIES.includes(c)),
        career_goal: data.career_goal || '',
        preferred_environment: data.preferred_environment || '',
        study_priority: data.study_priority || '',
        learning_style: data.learning_style || '',
        living_preference: data.living_preference || '',
        degrees: data.degrees || [],
        tests: data.tests || []
      });
    } catch (err) {
      setError('Failed to load profile');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProfile();
  }, []);
  
  const handleUpdateProfile = async (e) => {
    if (e) e.preventDefault();
    setSaving(true);
    setError('');
    setSuccess('');
    try {
      await authAPI.updateProfile(buildProfilePayload());
      await fetchProfile();
      setSuccess('Portfolio updated successfully!');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update portfolio');
    } finally {
      setSaving(false);
    }
  };

  const handleUpdateStrategy = async () => {
    setSaving(true);
    setError('');
    setSuccess('');
    try {
      await authAPI.updateProfile(buildStrategyPayload());
      await fetchProfile();
      setSuccess('AI strategy updated successfully!');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update AI strategy');
    } finally {
      setSaving(false);
    }
  };

  const handleUpdatePassword = async (e) => {
    e.preventDefault();
    if (!securityForm.currentPassword) {
      setError('Please enter your current password');
      return;
    }
    if (!PASSWORD_COMPLEXITY_REGEX.test(securityForm.newPassword)) {
      setError('Password must be at least 8 characters and include both letters and numbers');
      return;
    }
    if (securityForm.newPassword !== securityForm.confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    setSaving(true);
    setError('');
    setSuccess('');
    try {
      await authAPI.updateProfile({
        current_password: securityForm.currentPassword,
        password: securityForm.newPassword
      });
      setSuccess('Password changed successfully! Please log in again.');
      setSecurityForm({ currentPassword: '', newPassword: '', confirmPassword: '' });
      localStorage.removeItem('token');
      window.location.href = '/login';
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update password');
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

  const strategySignals = [
    form.career_goal,
    form.preferred_environment,
    form.study_priority,
    form.learning_style,
    form.living_preference,
  ];
  const completedSignals = strategySignals.filter(Boolean).length;
  const strategyCompletionPct = Math.round((completedSignals / strategySignals.length) * 100);
  const profileHealthPct = Math.round(
    (
      (form.full_name ? 1 : 0) +
      (form.current_degree ? 1 : 0) +
      (form.field_of_study ? 1 : 0) +
      (form.cgpa !== '' ? 1 : 0) +
      (form.preferred_degree ? 1 : 0) +
      (form.target_countries.length > 0 ? 1 : 0) +
      (form.budget_inr !== '' ? 1 : 0)
    ) / 7 * 100
  );

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
                {/* ── CV Autofill ── */}
                <CVUploadBanner onExtracted={applyExtracted} />
                {form.resume_filename && (
                  <div className="flex items-center gap-2 text-xs text-teal-700 bg-mintLight border border-mint/20 rounded-xl px-4 py-2.5 -mt-4">
                    <CheckCircle2 className="w-3.5 h-3.5 flex-shrink-0" />
                    <span>Resume saved for AI recommendations: <strong>{form.resume_filename}</strong></span>
                  </div>
                )}

                {/* ── Section: Profile Basics ── */}
                <section className="space-y-6">
                  <div className="flex items-center gap-2">
                    <User className="w-4 h-4 text-lavender" />
                    <h3 className="text-sm font-bold text-text uppercase tracking-widest">Profile Basics</h3>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <label className="block text-[10px] font-bold text-muted uppercase mb-1.5 ml-1">Email (Read-only)</label>
                      <input type="text" value={form.email} className="input-field bg-surfaceAlt" disabled />
                    </div>
                    <div>
                      <label className="block text-[10px] font-bold text-muted uppercase mb-1.5 ml-1">Full Name</label>
                      <input type="text" value={form.full_name} onChange={e=>setField('full_name', e.target.value)} className="input-field" placeholder="Priya Sharma" />
                    </div>
                  </div>
                </section>

                {/* ── Section: Onboarding sync (academic) ── */}
                <section className="space-y-6 pt-6 border-t border-surfaceBorder">
                  <div className="flex items-center gap-2">
                    <GraduationCap className="w-4 h-4 text-lavender" />
                    <h3 className="text-sm font-bold text-text uppercase tracking-widest">Onboarding Academic Fields</h3>
                  </div>

                  <div>
                    <label className="block text-[10px] font-bold text-muted uppercase mb-2 ml-1">Current Degree</label>
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                      {CURRENT_DEGREES.map(deg => (
                        <button
                          key={deg}
                          type="button"
                          onClick={() => setField('current_degree', deg)}
                          className={`py-2 px-3 rounded-lg border text-left text-xs font-semibold transition-all ${form.current_degree === deg ? 'border-lavender bg-lavendLight text-lavender' : 'border-surfaceBorder bg-white text-textSoft hover:border-lavender/50'}`}
                        >
                          {deg}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <label className="block text-[10px] font-bold text-muted uppercase mb-1.5 ml-1">Home University</label>
                      <input type="text" value={form.home_university} onChange={e => setField('home_university', e.target.value)} className="input-field" placeholder="e.g. IIT Delhi" />
                    </div>
                    <div>
                      <label className="block text-[10px] font-bold text-muted uppercase mb-1.5 ml-1">Field of Study</label>
                      <select value={form.field_of_study} onChange={e => setField('field_of_study', e.target.value)} className="input-field">
                        <option value="">Select field</option>
                        {FIELDS_OF_STUDY.map(field => <option key={field} value={field}>{field}</option>)}
                      </select>
                    </div>
                    <div>
                      <label className="block text-[10px] font-bold text-muted uppercase mb-1.5 ml-1">CGPA (out of 10)</label>
                      <input type="number" min="0" max="10" step="0.01" value={form.cgpa} onChange={e => setField('cgpa', e.target.value)} className="input-field" placeholder="8.5" />
                    </div>
                    <div>
                      <label className="block text-[10px] font-bold text-muted uppercase mb-1.5 ml-1">Graduation Year</label>
                      <input type="number" min="2020" max="2040" value={form.graduation_year} onChange={e => setField('graduation_year', e.target.value)} className="input-field" placeholder="2027" />
                    </div>
                  </div>
                </section>

                {/* ── Section: Onboarding sync (scores) ── */}
                <section className="space-y-6 pt-6 border-t border-surfaceBorder">
                  <div className="flex items-center gap-2">
                    <ClipboardList className="w-4 h-4 text-lavender" />
                    <h3 className="text-sm font-bold text-text uppercase tracking-widest">Onboarding Test Fields</h3>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <label className="block text-[10px] font-bold text-muted uppercase mb-1.5 ml-1">English Test</label>
                      <select value={form.english_test} onChange={e => setField('english_test', e.target.value)} className="input-field">
                        <option value="">Select test</option>
                        {ENGLISH_TESTS.map(test => <option key={test} value={test}>{test}</option>)}
                      </select>
                    </div>
                    <div>
                      <label className="block text-[10px] font-bold text-muted uppercase mb-1.5 ml-1">English Score</label>
                      <input type="number" step="0.5" value={form.english_score} onChange={e => setField('english_score', e.target.value)} className="input-field" placeholder="IELTS/PTE/Duolingo score" />
                    </div>
                    <div>
                      <label className="block text-[10px] font-bold text-muted uppercase mb-1.5 ml-1">TOEFL Score</label>
                      <input type="number" min="0" max="120" value={form.toefl_score} onChange={e => setField('toefl_score', e.target.value)} className="input-field" placeholder="105" />
                    </div>
                    <div>
                      <label className="block text-[10px] font-bold text-muted uppercase mb-1.5 ml-1">GRE Score</label>
                      <input type="number" min="260" max="340" value={form.gre_score} onChange={e => setField('gre_score', e.target.value)} className="input-field" placeholder="320" />
                    </div>
                    <div>
                      <label className="block text-[10px] font-bold text-muted uppercase mb-1.5 ml-1">GMAT Score</label>
                      <input type="number" min="200" max="800" value={form.gmat_score} onChange={e => setField('gmat_score', e.target.value)} className="input-field" placeholder="680" />
                    </div>
                    <div>
                      <label className="block text-[10px] font-bold text-muted uppercase mb-1.5 ml-1">Work Experience (Years)</label>
                      <input type="number" min="0" step="0.5" value={form.work_experience_years} onChange={e => setField('work_experience_years', e.target.value)} className="input-field" placeholder="2" />
                    </div>
                  </div>
                </section>

                {/* ── Section: Target Education & ROI ── */}
                <section className="space-y-6 pt-6 border-t border-surfaceBorder">
                  <div className="flex items-center gap-2">
                    <Target className="w-4 h-4 text-lavender" />
                    <h3 className="text-sm font-bold text-text uppercase tracking-widest">Target Education & ROI</h3>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <label className="block text-[10px] font-bold text-muted uppercase mb-1.5 ml-1">Target Degree</label>
                      <select value={form.preferred_degree} onChange={e=>setField('preferred_degree', e.target.value)} className="input-field">
                        <option value="">Select target</option>
                        {TARGET_DEGREES.map(d => <option key={d} value={d}>{d}</option>)}
                      </select>
                    </div>
                    <div>
                      <label className="block text-[10px] font-bold text-muted uppercase mb-1.5 ml-1">Preferred Intake</label>
                      <select value={form.intake_preference} onChange={e=>setField('intake_preference', e.target.value)} className="input-field">
                        <option value="">Select intake</option>
                        {INTAKE_OPTIONS.map(i => <option key={i} value={i}>{i}</option>)}
                      </select>
                    </div>
                    <div>
                      <label className="block text-[10px] font-bold text-muted uppercase mb-1.5 ml-1">Ranking Preference</label>
                      <select value={form.ranking_preference} onChange={e=>setField('ranking_preference', e.target.value)} className="input-field">
                        <option value="">Select preference</option>
                        {RANKING_OPTIONS.map(opt => <option key={opt} value={opt}>{opt}</option>)}
                      </select>
                    </div>
                    <div>
                      <label className="block text-[10px] font-bold text-muted uppercase mb-1.5 ml-1">Annual Budget (₹)</label>
                      <div className="relative">
                        <span className="absolute left-3 top-1/2 -translate-y-1/2 text-[10px] font-bold text-muted">₹</span>
                        <input type="number" value={form.budget_inr} onChange={e=>setField('budget_inr', e.target.value)} className="input-field pl-6" placeholder="3000000" />
                      </div>
                    </div>
                    <div>
                      <label className="block text-[10px] font-bold text-muted uppercase mb-1.5 ml-1">Scholarship Interest</label>
                      <button type="button" onClick={()=>setField('scholarship_interest', !form.scholarship_interest)} className={`w-full py-2.5 rounded-xl border text-[10px] font-bold transition-all ${form.scholarship_interest ? 'bg-mint text-white border-mint shadow-md' : 'bg-white border-surfaceBorder hover:border-mint text-textSoft'}`}>
                        {form.scholarship_interest ? 'Enabled' : 'Disabled'}
                      </button>
                    </div>
                    <div>
                      <label className="block text-[10px] font-bold text-muted uppercase mb-1.5 ml-1">Post-Study Work Interest</label>
                      <button type="button" onClick={()=>setField('work_abroad_interest', !form.work_abroad_interest)} className={`w-full py-2.5 rounded-xl border text-[10px] font-bold transition-all ${form.work_abroad_interest ? 'bg-lavender text-white border-lavender shadow-md' : 'bg-white border-surfaceBorder hover:border-lavender text-textSoft'}`}>
                        {form.work_abroad_interest ? 'Enabled' : 'Disabled'}
                      </button>
                    </div>
                  </div>
                  <div>
                    <label className="block text-[10px] font-bold text-muted uppercase mb-2 ml-1">Target Countries</label>
                    <div className="flex flex-wrap gap-2">
                      {APP_COUNTRIES.map(c => (
                        <button
                          key={c}
                          type="button"
                          onClick={() => toggleCountry(c)}
                          className={`px-3 py-1.5 rounded-lg text-[10px] font-bold border transition-all ${form.target_countries.includes(c) ? 'bg-lavender text-white border-lavender' : 'bg-surfaceAlt text-textSoft border-surfaceBorder hover:border-lavender/50'}`}
                        >
                          {c}
                        </button>
                      ))}
                    </div>
                  </div>
                </section>

                <div className="pt-2 flex justify-end">
                  <SaveChangesButton
                    type="submit"
                    variant="primary"
                    saving={saving}
                    label="Save Profile"
                  />
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
                      <select value={form.career_goal} onChange={e=>setField('career_goal', e.target.value)} className="input-field-peach py-2 font-bold text-xs">
                        <option value="">Select career goal</option>
                        {CAREER_GOALS.map(goal => (
                          <option key={goal.value} value={goal.value}>{goal.label}</option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="block text-[10px] font-bold text-muted uppercase mb-3 ml-1 tracking-widest">Preferred Environment</label>
                      <div className="grid grid-cols-2 gap-2">
                        {ENVIRONMENT_OPTIONS.map(env => (
                          <button key={env.value} type="button" onClick={()=>setField('preferred_environment', env.value)}
                            className={`px-3 py-3 rounded-xl border text-left transition-all ${form.preferred_environment===env.value?'bg-peach text-white border-peach shadow-md':'bg-white border-surfaceBorder hover:border-peach text-textSoft'}`}>
                            <p className="text-[10px] font-bold">{env.label}</p>
                            <p className={`text-[9px] ${form.preferred_environment===env.value ? 'text-white/80' : 'text-muted'}`}>{env.sub}</p>
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>

                  <div className="space-y-6">
                    <div>
                      <label className="block text-[10px] font-bold text-muted uppercase mb-3 ml-1 tracking-widest">Primary Selection Driver</label>
                      <select value={form.study_priority} onChange={e=>setField('study_priority', e.target.value)} className="input-field-peach py-2 font-bold text-xs">
                        <option value="">Select study priority</option>
                        {STUDY_PRIORITIES.map(priority => (
                          <option key={priority.value} value={priority.value}>{priority.label}</option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="block text-[10px] font-bold text-muted uppercase mb-3 ml-1 tracking-widest">Learning Style</label>
                      <div className="grid grid-cols-2 gap-2">
                        {LEARNING_STYLES.map(style => (
                          <button key={style.value} type="button" onClick={()=>setField('learning_style', style.value)}
                            className={`py-3 px-3 rounded-xl border text-left transition-all ${form.learning_style===style.value?'bg-peach text-white border-peach shadow-md':'bg-white border-surfaceBorder hover:border-peach text-textSoft'}`}>
                            <p className="text-[10px] font-bold">{style.label}</p>
                            <p className={`text-[9px] ${form.learning_style===style.value ? 'text-white/80' : 'text-muted'}`}>{style.sub}</p>
                          </button>
                        ))}
                      </div>
                    </div>
                    <div>
                      <label className="block text-[10px] font-bold text-muted uppercase mb-3 ml-1 tracking-widest">Living Preference</label>
                      <div className="grid grid-cols-3 gap-2">
                        {LIVING_OPTIONS.map(option => (
                          <button key={option.value} type="button" onClick={()=>setField('living_preference', option.value)}
                            className={`py-3 px-2 rounded-xl border text-left transition-all ${form.living_preference===option.value?'bg-peach text-white border-peach shadow-md':'bg-white border-surfaceBorder hover:border-peach text-textSoft'}`}>
                            <p className="text-[10px] font-bold">{option.label}</p>
                            <p className={`text-[9px] ${form.living_preference===option.value ? 'text-white/80' : 'text-muted'}`}>{option.sub}</p>
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>

                <div className="pt-2 flex justify-end">
                  <SaveChangesButton
                    onClick={handleUpdateStrategy}
                    variant="peach"
                    saving={saving}
                    label="Save AI Strategy"
                  />
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
                    <label className="block text-[10px] font-bold text-muted uppercase mb-1.5 ml-1">Current Password</label>
                    <input type="password" required value={securityForm.currentPassword} onChange={e=>setSecurityForm({...securityForm, currentPassword: e.target.value})} className="input-field" placeholder="••••••••"/>
                  </div>
                  <div>
                    <label className="block text-[10px] font-bold text-muted uppercase mb-1.5 ml-1">New Password</label>
                    <input type="password" required value={securityForm.newPassword} onChange={e=>setSecurityForm({...securityForm, newPassword: e.target.value})} className="input-field" placeholder="••••••••"/>
                    <p className="mt-1 text-[10px] text-muted">Minimum 8 characters with at least one letter and one number.</p>
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
                    <span className={`uppercase ${form.is_verified ? 'text-mint' : 'text-rose'}`}>
                      {form.is_verified ? 'Email Verified' : 'Email Not Verified'}
                    </span>
                 </div>
                 <div className="flex flex-col gap-2">
                    <div className="flex items-center justify-between text-[9px] font-bold text-muted">
                      <span>Targets: {form.target_countries.length}</span>
                      <span>Budget: {form.budget_inr ? `₹${Number(form.budget_inr).toLocaleString('en-IN')}` : 'Not set'}</span>
                    </div>
                    <div className="w-full h-1.5 bg-surfaceAlt rounded-full overflow-hidden">
                        <div className="h-full bg-mint rounded-full shadow-glow transition-all" style={{ width: `${profileHealthPct}%` }}></div>
                    </div>
                    <div className="text-[9px] font-bold text-muted text-right">{profileHealthPct}% profile completeness</div>
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
                  <span className="text-[10px] font-bold text-teal-800 uppercase tracking-wider">Strategy Coverage</span>
                </div>
                <p className="text-[9px] text-teal-700 leading-relaxed font-medium">
                  {completedSignals}/{strategySignals.length} AI strategy signals saved in database ({strategyCompletionPct}% complete).
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
