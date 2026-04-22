import { useState, useRef, useEffect } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { authAPI } from '../api/auth';
import { RefreshCw, CheckCircle, KeyRound } from 'lucide-react';

export default function OTPVerify() {
  const navigate = useNavigate();
  const location  = useLocation();

  // email passed from Register page via navigation state
  const email = location.state?.email || '';

  const [digits, setDigits] = useState(['', '', '', '', '', '']);
  const [loading, setLoading]     = useState(false);
  const [resending, setResending] = useState(false);
  const [error, setError]         = useState('');
  const [success, setSuccess]     = useState(false);
  const inputRefs = useRef([]);

  useEffect(() => {
    inputRefs.current[0]?.focus();
  }, []);

  const handleChange = (i, val) => {
    if (!/^\d?$/.test(val)) return;
    const next = [...digits];
    next[i] = val;
    setDigits(next);
    if (val && i < 5) inputRefs.current[i + 1]?.focus();
  };

  const handleKeyDown = (i, e) => {
    if (e.key === 'Backspace' && !digits[i] && i > 0) inputRefs.current[i - 1]?.focus();
  };

  const handlePaste = (e) => {
    const pasted = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6);
    if (pasted.length === 6) {
      setDigits(pasted.split(''));
      inputRefs.current[5]?.focus();
    }
  };

  const otp = digits.join('');

  const handleSubmit = async (e) => {
    e?.preventDefault();
    if (otp.length < 6) return;
    setLoading(true);
    setError('');
    try {
      const data = await authAPI.verifyOTP(email, otp);
      localStorage.setItem('token', data.access_token);
      setSuccess(true);
      setTimeout(() => navigate('/dashboard'), 1200);
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid OTP. Please try again.');
      setDigits(['', '', '', '', '', '']);
      inputRefs.current[0]?.focus();
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    setResending(true);
    setError('');
    try {
      await authAPI.sendOTP(email);
    } catch {
      setError('Failed to resend OTP. Please try again.');
    } finally {
      setResending(false);
    }
  };

  // Auto-submit once all 6 digits entered
  useEffect(() => {
    if (otp.length === 6 && !loading) handleSubmit();
  }, [otp]);

  if (success) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#F8F9FC]">
        <div className="text-center animate-scale-in">
          <div className="w-20 h-20 bg-mintLight rounded-full flex items-center justify-center mx-auto mb-4">
            <CheckCircle className="w-10 h-10 text-teal-500" />
          </div>
          <h2 className="text-2xl font-black text-text mb-1">Verified!</h2>
          <p className="text-muted text-sm">Taking you to your dashboard…</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#F8F9FC] p-6">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="flex items-center gap-2 mb-10 justify-center">
          <div className="w-9 h-9 rounded-xl flex items-center justify-center"
            style={{ background: 'linear-gradient(135deg, #1E40AF, #3B82F6)' }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
              <path d="M12 3 C7 8 3 10 3 16 C7 14 10 13 12 15 C14 13 17 14 21 16 C21 10 17 8 12 3Z" fill="white" fillOpacity="0.95"/>
              <path d="M12 15 L12 21" stroke="white" strokeWidth="2" strokeLinecap="round"/>
            </svg>
          </div>
          <span className="font-brand font-bold text-text" style={{ fontSize: '1.2rem' }}>udaan</span>
        </div>

        <div className="card p-8 animate-scale-in">
          {/* Header */}
          <div className="flex justify-center mb-6">
            <div className="w-14 h-14 bg-lavendLight rounded-2xl flex items-center justify-center">
              <KeyRound className="w-7 h-7 text-lavender" />
            </div>
          </div>
          <h2 className="text-2xl font-black text-text text-center mb-1">Check your email</h2>
          <p className="text-muted text-sm text-center mb-6">
            We sent a 6-digit code to<br />
            <span className="font-semibold text-text">{email || 'your email'}</span>
          </p>

          {error && (
            <div className="mb-4 p-3 rounded-xl bg-rose/8 border border-rose/25 text-rose text-sm font-medium text-center">
              {error}
            </div>
          )}

          {/* OTP input */}
          <form onSubmit={handleSubmit}>
            <div className="flex gap-2 justify-center mb-6" onPaste={handlePaste}>
              {digits.map((d, i) => (
                <input
                  key={i}
                  ref={el => inputRefs.current[i] = el}
                  type="text"
                  inputMode="numeric"
                  maxLength={1}
                  value={d}
                  onChange={e => handleChange(i, e.target.value)}
                  onKeyDown={e => handleKeyDown(i, e)}
                  className={`w-12 h-14 text-center text-xl font-bold rounded-xl border-2 bg-surfaceAlt outline-none transition-all
                    ${d ? 'border-lavender bg-lavendLight text-lavender' : 'border-surfaceBorder text-text'}
                    focus:border-lavender focus:bg-lavendLight focus:text-lavender`}
                />
              ))}
            </div>

            <button type="submit" disabled={loading || otp.length < 6} className="btn-primary w-full py-3.5 text-[15px]">
              {loading ? 'Verifying…' : 'Verify & Continue'}
            </button>
          </form>

          <div className="flex items-center justify-between mt-5">
            <button onClick={handleResend} disabled={resending}
              className="flex items-center gap-1.5 text-sm text-muted hover:text-lavender transition-colors">
              <RefreshCw className={`w-3.5 h-3.5 ${resending ? 'animate-spin' : ''}`} />
              {resending ? 'Sending…' : 'Resend code'}
            </button>
            <Link to="/register" className="text-sm text-muted hover:text-lavender transition-colors">
              Wrong email?
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
