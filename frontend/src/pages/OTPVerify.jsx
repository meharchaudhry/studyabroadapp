import { useState, useRef, useEffect } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { authAPI } from '../api/auth';
import { Globe, Mail, RefreshCw, CheckCircle } from 'lucide-react';

export default function OTPVerify() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const email = searchParams.get('email') || '';

  const [otp, setOtp] = useState(['', '', '', '', '', '']);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [resending, setResending] = useState(false);
  const [resent, setResent] = useState(false);
  const refs = useRef([]);

  useEffect(() => { refs.current[0]?.focus(); }, []);

  const handleChange = (i, val) => {
    if (!/^\d?$/.test(val)) return;
    const next = [...otp];
    next[i] = val;
    setOtp(next);
    if (val && i < 5) refs.current[i + 1]?.focus();
  };

  const handleKeyDown = (i, e) => {
    if (e.key === 'Backspace' && !otp[i] && i > 0) refs.current[i - 1]?.focus();
  };

  const handlePaste = (e) => {
    const text = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6);
    if (text.length === 6) {
      setOtp(text.split(''));
      refs.current[5]?.focus();
    }
    e.preventDefault();
  };

  const handleVerify = async () => {
    const code = otp.join('');
    if (code.length !== 6) return setError('Please enter all 6 digits.');
    setLoading(true);
    setError('');
    try {
      const res = await authAPI.verifyOTP(email, code);
      localStorage.setItem('token', res.access_token);
      navigate('/dashboard');
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid OTP. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    setResending(true);
    setError('');
    try {
      await authAPI.sendOTP(email);
      setResent(true);
      setTimeout(() => setResent(false), 4000);
    } catch (err) {
      setError('Could not resend OTP. Please try again.');
    } finally {
      setResending(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-surfaceAlt"
      style={{ backgroundImage: 'radial-gradient(ellipse at top right, rgba(124,111,247,0.10) 0%, transparent 60%)' }}>
      
      <div className="w-full max-w-sm animate-scale-in">
        <div className="text-center mb-8">
          <div className="w-12 h-12 bg-lavender rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-card">
            <Mail className="w-6 h-6 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-text">Check your email</h1>
          <p className="text-muted text-sm mt-1">We sent a 6-digit code to</p>
          <p className="text-lavender font-semibold text-sm mt-0.5">{email}</p>
        </div>

        <div className="card p-8 shadow-cardHov">
          {error && <div className="bg-rose/10 border border-rose/20 text-rose rounded-xl px-4 py-3 text-sm mb-5">{error}</div>}
          {resent && (
            <div className="bg-mint/10 border border-mint/20 text-teal-700 rounded-xl px-4 py-3 text-sm mb-5 flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-mint" /> New OTP sent to your email!
            </div>
          )}

          <div className="flex gap-2 justify-center mb-6">
            {otp.map((d, i) => (
              <input
                key={i}
                ref={el => refs.current[i] = el}
                type="text"
                inputMode="numeric"
                maxLength={1}
                value={d}
                onChange={e => handleChange(i, e.target.value)}
                onKeyDown={e => handleKeyDown(i, e)}
                onPaste={handlePaste}
                className={`w-11 h-14 text-center text-2xl font-bold rounded-xl border-2 bg-surfaceAlt text-text
                  focus:outline-none focus:border-lavender focus:bg-lavendLight transition-all
                  ${d ? 'border-lavender bg-lavendLight' : 'border-surfaceBorder'}`}
              />
            ))}
          </div>

          <button onClick={handleVerify} disabled={loading} className="btn-primary w-full">
            {loading ? (
              <span className="flex items-center gap-2"><span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"/>Verifying…</span>
            ) : 'Verify & Continue'}
          </button>

          <button onClick={handleResend} disabled={resending} className="btn-ghost w-full mt-3 text-sm">
            <RefreshCw className={`w-3.5 h-3.5 ${resending ? 'animate-spin' : ''}`} />
            {resending ? 'Sending…' : 'Resend code'}
          </button>

          <p className="text-center text-xs text-muted mt-4">
            <Link to="/login" className="hover:text-lavender transition-colors">← Back to sign in</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
