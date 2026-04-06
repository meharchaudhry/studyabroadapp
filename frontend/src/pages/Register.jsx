import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { authAPI } from '../api/auth';
import { Globe, Mail, Lock, User, DollarSign, Flag, Eye, EyeOff, ArrowRight } from 'lucide-react';

const COUNTRIES = ['USA','UK','Germany','France','Netherlands','Australia','Singapore','HongKong','Spain','Switzerland','Finland'];

export default function Register() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: '', password: '', cgpa: '', budget: '' });
  const [selectedCountries, setSelectedCountries] = useState([]);
  const [showPass, setShowPass] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const toggleCountry = (c) => {
    setSelectedCountries(prev =>
      prev.includes(c) ? prev.filter(x => x !== c) : [...prev, c]
    );
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      await authAPI.register({
        email: form.email,
        password: form.password,
        cgpa: parseFloat(form.cgpa) || null,
        budget: parseInt(form.budget, 10) || null,
        target_countries: selectedCountries,
      });
      // After register, navigate to OTP verify with the email
      navigate(`/verify-otp?email=${encodeURIComponent(form.email)}`);
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-surfaceAlt"
      style={{ backgroundImage: 'radial-gradient(ellipse at top right, rgba(124,111,247,0.10) 0%, transparent 60%), radial-gradient(ellipse at bottom left, rgba(78,204,163,0.07) 0%, transparent 60%)' }}>
      
      <div className="w-full max-w-lg animate-scale-in">
        <div className="text-center mb-8">
          <div className="w-12 h-12 bg-lavender rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-card">
            <Globe className="w-6 h-6 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-text">Create your account</h1>
          <p className="text-muted text-sm mt-1">Get personalised university recommendations</p>
        </div>

        <div className="card p-8 shadow-cardHov">
          {error && <div className="bg-rose/10 border border-rose/20 text-rose rounded-xl px-4 py-3 text-sm mb-5">{error}</div>}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-text mb-1.5">Email address</label>
              <div className="relative">
                <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-muted" />
                <input type="email" required value={form.email} onChange={e=>setForm({...form,email:e.target.value})} placeholder="you@example.com" className="input-field pl-10"/>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-text mb-1.5">Password</label>
              <div className="relative">
                <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-muted" />
                <input type={showPass?'text':'password'} required value={form.password} onChange={e=>setForm({...form,password:e.target.value})} placeholder="Min. 8 characters" className="input-field pl-10 pr-10"/>
                <button type="button" onClick={()=>setShowPass(!showPass)} className="absolute right-3.5 top-1/2 -translate-y-1/2 text-muted hover:text-text">
                  {showPass ? <EyeOff className="w-4 h-4"/> : <Eye className="w-4 h-4"/>}
                </button>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-text mb-1.5">CGPA <span className="text-muted">(out of 10)</span></label>
                <input type="number" step="0.1" min="0" max="10" value={form.cgpa} onChange={e=>setForm({...form,cgpa:e.target.value})} placeholder="8.5" className="input-field"/>
              </div>
              <div>
                <label className="block text-sm font-medium text-text mb-1.5">Budget <span className="text-muted">(₹/yr)</span></label>
                <input type="number" value={form.budget} onChange={e=>setForm({...form,budget:e.target.value})} placeholder="4000000" className="input-field"/>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-text mb-2">Target countries <span className="text-muted">(select all that apply)</span></label>
              <div className="flex flex-wrap gap-2">
                {COUNTRIES.map(c => (
                  <button key={c} type="button" onClick={()=>toggleCountry(c)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all ${
                      selectedCountries.includes(c)
                        ? 'bg-lavender text-white border-lavender'
                        : 'bg-surfaceAlt text-textSoft border-surfaceBorder hover:border-lavender hover:text-lavender'
                    }`}>
                    {c}
                  </button>
                ))}
              </div>
            </div>

            <button type="submit" disabled={loading} className="btn-primary w-full mt-2">
              {loading ? (
                <span className="flex items-center gap-2"><span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"/>Creating account…</span>
              ) : (
                <><span>Create Account & Get OTP</span><ArrowRight className="w-4 h-4"/></>
              )}
            </button>
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
