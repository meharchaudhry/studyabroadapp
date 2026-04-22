import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { authAPI } from '../api/auth';
import { Eye, EyeOff, ArrowRight, GraduationCap, MapPin, FileCheck, TrendingUp, Briefcase } from 'lucide-react';

export default function Login() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: '', password: '' });
  const [showPwd, setShowPwd] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const data = await authAPI.login(form.email, form.password);
      localStorage.setItem('token', data.access_token);
      navigate('/dashboard');
    } catch (err) {
      setError(err.response?.data?.detail || 'Incorrect email or password.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex">
      {/* ── Left brand panel ── */}
      <div className="hidden lg:flex lg:w-[52%] relative overflow-hidden flex-col justify-between p-12"
        style={{ background: 'linear-gradient(135deg, #1E40AF 0%, #2563EB 60%, #3B82F6 100%)' }}>
        {/* Decorative circles */}
        <div className="absolute -top-20 -right-20 w-96 h-96 rounded-full bg-white/10 blur-3xl" />
        <div className="absolute -bottom-20 -left-20 w-80 h-80 rounded-full bg-white/10 blur-3xl" />
        <div className="absolute top-1/2 right-0 w-48 h-48 rounded-full bg-white/5 blur-2xl" />

        {/* Logo */}
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

        {/* Main copy */}
        <div className="relative z-10 flex-1 flex flex-col justify-center">
          <p className="text-white/60 text-xs font-medium tracking-widest uppercase mb-4">the study abroad app for indian students</p>
          <h1 className="font-brand text-white leading-[1.05] mb-5"
            style={{ fontSize: '3.8rem', fontWeight: 700, letterSpacing: '-0.01em' }}>
            Your journey<br />starts here
          </h1>
          <p className="text-white/75 text-base mb-10 leading-relaxed max-w-sm">
            Find your best-fit university, plan your visa, and understand the financial ROI — all in one place.
          </p>

          <div className="space-y-3.5">
            {[
              { icon: GraduationCap, text: "600+ universities across 21 countries, matched to your GPA and field" },
              { icon: FileCheck,     text: "Visa requirements, documents and timelines for every destination" },
              { icon: TrendingUp,    text: "ROI calculator — compare tuition cost against graduate salaries" },
              { icon: Briefcase,     text: "Live job listings and post-study work visa guidance by country" },
              { icon: MapPin,        text: "Student housing, shortlist builder and application timeline" },
            ].map(({ icon: Icon, text }) => (
              <div key={text} className="flex items-start gap-3">
                <div className="w-7 h-7 rounded-lg bg-white/15 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <Icon className="w-3.5 h-3.5 text-white/90" />
                </div>
                <p className="text-white/80 text-sm leading-relaxed">{text}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── Right form panel ── */}
      <div className="flex-1 flex items-center justify-center p-8 bg-[#F8F9FC]">
        <div className="w-full max-w-[400px]">
          {/* Mobile logo */}
          <div className="flex items-center gap-2 mb-8 lg:hidden">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center"
              style={{ background: 'linear-gradient(135deg, #1E40AF, #3B82F6)' }}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                <path d="M12 3 C7 8 3 10 3 16 C7 14 10 13 12 15 C14 13 17 14 21 16 C21 10 17 8 12 3Z" fill="white" fillOpacity="0.95"/>
                <path d="M12 15 L12 21" stroke="white" strokeWidth="2" strokeLinecap="round"/>
              </svg>
            </div>
            <span className="font-brand font-bold text-text" style={{ fontSize: '1.1rem' }}>udaan</span>
          </div>

          <div className="mb-8">
            <h2 className="text-3xl font-black text-text mb-1.5">Welcome back</h2>
            <p className="text-muted text-sm">Sign in to continue planning your future</p>
          </div>

          {error && (
            <div className="mb-5 p-3.5 rounded-xl bg-rose/8 border border-rose/25 text-rose text-sm font-medium">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-semibold text-textSoft mb-1.5">Email address</label>
              <input type="email" required autoComplete="email" className="input-field" placeholder="you@example.com"
                value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} />
            </div>

            <div>
              <label className="block text-sm font-semibold text-textSoft mb-1.5">Password</label>
              <div className="relative">
                <input type={showPwd ? 'text' : 'password'} required autoComplete="current-password"
                  className="input-field pr-11" placeholder="••••••••"
                  value={form.password} onChange={e => setForm({ ...form, password: e.target.value })} />
                <button type="button" onClick={() => setShowPwd(v => !v)}
                  className="absolute right-3.5 top-1/2 -translate-y-1/2 text-muted hover:text-textSoft">
                  {showPwd ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <button type="submit" disabled={loading} className="btn-primary w-full py-3.5 text-[15px] mt-2">
              {loading ? 'Signing in…' : <><span>Sign in</span><ArrowRight className="w-4 h-4" /></>}
            </button>
          </form>

          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-surfaceBorder" /></div>
            <div className="relative flex justify-center"><span className="bg-[#F8F9FC] px-3 text-xs text-muted">New to udaan?</span></div>
          </div>

          <Link to="/register"
            className="flex items-center justify-center gap-2 w-full py-3 rounded-xl border-2 border-lavender/30 text-lavender font-semibold text-sm hover:bg-lavendLight transition-colors">
            Create a free account <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </div>
    </div>
  );
}
