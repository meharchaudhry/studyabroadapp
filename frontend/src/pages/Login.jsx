import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { authAPI } from '../api/auth';
import { Eye, EyeOff, ArrowRight, Globe, GraduationCap, Sparkles, TrendingUp } from 'lucide-react';

const FEATURES = [
  { icon: GraduationCap, label: "600+ Universities",    sub: "ranked by your profile"         },
  { icon: Globe,          label: "16 Countries",         sub: "AI visa guidance"                },
  { icon: Sparkles,       label: "5-Agent AI",           sub: "personalised decision dashboard" },
  { icon: TrendingUp,     label: "ROI Calculator",       sub: "financial break-even analysis"   },
];

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
        style={{ background: 'linear-gradient(135deg, #4C3BCF 0%, #7C6FF7 50%, #9B8FF7 100%)' }}>
        {/* Decorative circles */}
        <div className="absolute -top-20 -right-20 w-96 h-96 rounded-full bg-white/10 blur-3xl" />
        <div className="absolute -bottom-20 -left-20 w-80 h-80 rounded-full bg-white/10 blur-3xl" />
        <div className="absolute top-1/2 right-0 w-48 h-48 rounded-full bg-white/5 blur-2xl" />

        {/* Logo */}
        <div className="relative z-10 flex items-center gap-3">
          <div className="w-10 h-10 bg-white/20 backdrop-blur-sm rounded-xl flex items-center justify-center border border-white/30">
            <Globe className="w-5 h-5 text-white" />
          </div>
          <span className="text-white font-bold text-xl tracking-tight">StudyPathway</span>
        </div>

        {/* Main copy */}
        <div className="relative z-10 flex-1 flex flex-col justify-center">
          <div className="inline-flex items-center gap-2 bg-white/15 backdrop-blur-sm border border-white/20 rounded-full px-4 py-1.5 mb-6 w-fit">
            <Sparkles className="w-3.5 h-3.5 text-white/80" />
            <span className="text-white/80 text-xs font-medium">AI-Powered Study Abroad Platform</span>
          </div>
          <h1 className="text-5xl font-black text-white leading-[1.1] mb-5">
            Your global<br />education<br />journey starts<br />here
          </h1>
          <p className="text-white/70 text-lg mb-10 leading-relaxed max-w-sm">
            Built exclusively for Indian students. Smart. Fast. Personalised.
          </p>

          <div className="grid grid-cols-2 gap-3">
            {FEATURES.map(({ icon: Icon, label, sub }) => (
              <div key={label} className="bg-white/10 backdrop-blur-sm border border-white/15 rounded-xl p-4">
                <div className="w-8 h-8 bg-white/20 rounded-lg flex items-center justify-center mb-2">
                  <Icon className="w-4 h-4 text-white" />
                </div>
                <p className="text-white font-semibold text-sm">{label}</p>
                <p className="text-white/60 text-xs mt-0.5">{sub}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Testimonial */}
        <div className="relative z-10 bg-white/10 backdrop-blur-sm border border-white/20 rounded-2xl p-5 mt-8">
          <p className="text-white/90 text-sm leading-relaxed mb-4">
            "Got into TU Munich with a full scholarship. The 5-agent AI recommendation was spot-on and the visa guide saved me weeks of research!"
          </p>
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-full bg-gradient-to-br from-mint to-teal-400 flex items-center justify-center text-white font-bold text-sm flex-shrink-0">P</div>
            <div>
              <p className="text-white font-semibold text-sm">Priya Sharma</p>
              <p className="text-white/55 text-xs">MS Computer Science · TU Munich 2024</p>
            </div>
          </div>
        </div>
      </div>

      {/* ── Right form panel ── */}
      <div className="flex-1 flex items-center justify-center p-8 bg-[#F8F9FC]">
        <div className="w-full max-w-[400px]">
          {/* Mobile logo */}
          <div className="flex items-center gap-2 mb-8 lg:hidden">
            <div className="w-8 h-8 bg-lavender rounded-lg flex items-center justify-center">
              <Globe className="w-4 h-4 text-white" />
            </div>
            <span className="font-bold text-text">StudyPathway</span>
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
            <div className="relative flex justify-center"><span className="bg-[#F8F9FC] px-3 text-xs text-muted">New to StudyPathway?</span></div>
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
