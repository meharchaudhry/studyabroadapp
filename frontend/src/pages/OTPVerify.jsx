import { useState, useRef, useEffect } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { authAPI } from '../api/auth';
import { Globe, RefreshCw, CheckCircle, Mail, KeyRound, AlertCircle } from 'lucide-react';

export default function OTPVerify() {
  const navigate = useNavigate();
  const location  = useLocation();

  // email and optional dev OTP passed from Register page via navigation state
  const email  = location.state?.email  || '';
  const devOtp = location.state?.devOtp || null;

  const [digits, setDigits] = useState(['', '', '', '', '', '']);
  const [loading, setLoading]   = useState(false);
  const [resending, setResending] = useState(false);
  const [error, setError]   = useState('');
  const [success, setSuccess] = useState(false);
  const [devOtpVisible, setDevOtpVisible] = useState(false);
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
      const res = await authAPI.sendOTP(email);
      if (res.dev_otp) {
        // Update dev OTP if a new one was issued
        location.state.devOtp = res.dev_otp;
      }
    } catch {
      setError('Failed to resend OTP.');
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
          <div className="w-9 h-9 bg-lavender rounded-xl flex items-center justify-center">
            <Globe className="w-4.5 h-4.5 text-white w-[18px] h-[18px]" />
          </div>
          <span className="font-bold text-text text-lg">StudyPathway</span>
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

          {/* Dev mode banner */}
          {devOtp && (
            <div className="mb-5 p-3.5 rounded-xl bg-amberLight border border-amber/30">
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center gap-1.5">
                  <AlertCircle className="w-3.5 h-3.5 text-amber-600" />
                  <span className="text-xs font-semibold text-amber-700">Dev mode — no email configured</span>
                </div>
                <button onClick={() => setDevOtpVisible(v => !v)}
                  className="text-xs text-amber-600 font-medium hover:underline">
                  {devOtpVisible ? 'Hide' : 'Show OTP'}
                </button>
              </div>
              {devOtpVisible && (
                <div className="mt-2 text-center">
                  <span className="text-2xl font-black tracking-[0.3em] text-amber-700 font-mono">{devOtp}</span>
                </div>
              )}
            </div>
          )}

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
