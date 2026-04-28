import { useState, useEffect } from 'react';
import { Calendar as CalendarIcon, Clock, MoveRight, CheckCircle2, Building2,
         ExternalLink, Loader2, Link2, Link2Off, RefreshCw } from 'lucide-react';
import api from '../api/client';

const APPOINTMENT_TYPES = [
  { id: 'visa', name: 'Visa & Immigration Consultancy', duration: 45, slots: ['09:00 AM', '11:00 AM', '02:00 PM', '04:30 PM'] },
  { id: 'uni',  name: 'University Admissions Counselor', duration: 30, slots: ['10:00 AM', '01:00 PM', '03:15 PM'] },
];

// ── Google Calendar connection banner ──────────────────────────────────────────
function CalendarConnectBanner({ calStatus, onRefresh }) {
  const [connecting, setConnecting] = useState(false);

  const handleConnect = async () => {
    setConnecting(true);
    try {
      const resp = await api.get('/calendar/connect');
      // Open Google OAuth in a new window
      const popup = window.open(resp.data.auth_url, '_blank', 'width=500,height=600');
      // Poll until popup closes, then refresh status
      const timer = setInterval(() => {
        if (popup && popup.closed) {
          clearInterval(timer);
          setConnecting(false);
          onRefresh();
        }
      }, 1000);
    } catch (e) {
      setConnecting(false);
      alert(e?.response?.data?.detail || 'Could not get auth URL. Check backend/data/google_credentials.json exists.');
    }
  };

  const handleDisconnect = async () => {
    await api.get('/calendar/disconnect');
    onRefresh();
  };

  if (calStatus === null) return null;  // still loading

  if (calStatus.status === 'connected') {
    return (
      <div className="flex items-center gap-3 bg-mint/10 border border-mint/30 rounded-xl px-4 py-3 mb-6">
        <div className="w-8 h-8 bg-mint/20 rounded-full flex items-center justify-center">
          <Link2 className="w-4 h-4 text-teal-600" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-teal-700">Google Calendar Connected</p>
          <p className="text-xs text-teal-600 truncate">{calStatus.calendar_name} · {calStatus.email}</p>
        </div>
        <button
          onClick={handleDisconnect}
          className="text-xs text-teal-700 hover:text-rose-600 flex items-center gap-1 transition-colors"
        >
          <Link2Off className="w-3.5 h-3.5" /> Disconnect
        </button>
      </div>
    );
  }

  if (calStatus.status === 'not_configured') {
    return (
      <div className="bg-amber-50 border border-amber-200 rounded-xl px-4 py-3 mb-6 text-sm text-amber-800">
        <strong>Setup required:</strong> Place <code>google_credentials.json</code> in <code>backend/data/</code> to enable Google Calendar.
      </div>
    );
  }

  // not_connected or error
  return (
    <div className="flex items-center gap-3 bg-surfaceAlt border border-surfaceBorder rounded-xl px-4 py-3 mb-6">
      <div className="w-8 h-8 bg-surface rounded-full flex items-center justify-center border border-surfaceBorder">
        <CalendarIcon className="w-4 h-4 text-muted" />
      </div>
      <div className="flex-1">
        <p className="text-sm font-semibold text-text">Connect Google Calendar</p>
        <p className="text-xs text-muted">Add appointments directly to your real Google Calendar</p>
      </div>
      <button
        onClick={handleConnect}
        disabled={connecting}
        className="btn-primary text-xs px-3 py-1.5 flex items-center gap-1.5 disabled:opacity-60"
      >
        {connecting
          ? <><Loader2 className="w-3 h-3 animate-spin"/> Connecting…</>
          : <><Link2 className="w-3 h-3"/> Connect</>}
      </button>
    </div>
  );
}

// ── Main component ─────────────────────────────────────────────────────────────
export default function BookingAppointments() {
  const [selectedTopic,   setSelectedTopic]   = useState('visa');
  const [selectedDate,    setSelectedDate]     = useState('');
  const [selectedSlot,    setSelectedSlot]     = useState('');
  const [bookingSuccess,  setBookingSuccess]   = useState(false);
  const [calendarLoading, setCalendarLoading]  = useState(false);
  const [calendarResult,  setCalendarResult]   = useState(null);
  const [calStatus,       setCalStatus]        = useState(null);  // Google Calendar status

  const activeTopic = APPOINTMENT_TYPES.find(t => t.id === selectedTopic);

  // Load calendar status on mount
  const fetchCalStatus = async () => {
    try {
      const resp = await api.get('/calendar/status');
      setCalStatus(resp.data);
    } catch {
      setCalStatus({ status: 'not_configured' });
    }
  };

  useEffect(() => { fetchCalStatus(); }, []);

  const buildDatetime = () => {
    if (!selectedDate || !selectedSlot) return null;
    const m = selectedSlot.match(/(\d+):(\d+) (AM|PM)/);
    if (!m) return null;
    let h = parseInt(m[1]);
    if (m[3] === 'PM' && h !== 12) h += 12;
    if (m[3] === 'AM' && h === 12) h = 0;
    return `${selectedDate}T${h.toString().padStart(2,'0')}:${m[2]}:00`;
  };

  const addToGoogleCalendar = async () => {
    const dt = buildDatetime();
    if (!dt) return;
    setCalendarLoading(true);
    setCalendarResult(null);
    try {
      const resp = await api.post('/calendar/create-event', {
        title: `udaan: ${activeTopic.name}`,
        start_datetime: dt,
        description: `Consultation booked via udaan.\nType: ${activeTopic.name}\nDuration: ${activeTopic.duration} minutes\nMeeting link will be shared 1 hour prior.`,
        duration_minutes: activeTopic.duration,
        timezone: 'Asia/Kolkata',
      });
      setCalendarResult(resp.data);
      // Refresh status in case it changed
      fetchCalStatus();
    } catch (e) {
      setCalendarResult({ success: false, error: 'Could not connect to server.' });
    } finally {
      setCalendarLoading(false);
    }
  };

  const handleBooking = () => {
    if (!selectedDate || !selectedSlot) return;
    setBookingSuccess(true);
  };

  const isConnected = calStatus?.status === 'connected';

  return (
    <div className="animate-fade-in space-y-6 max-w-4xl mx-auto pb-10">
      <div className="text-center py-8">
        <div className="w-16 h-16 bg-lavendLight rounded-2xl flex items-center justify-center mx-auto mb-4 scale-110">
          <CalendarIcon className="w-8 h-8 text-lavender"/>
        </div>
        <h1 className="text-3xl font-bold text-text mb-2">Book an Appointment</h1>
        <p className="text-muted text-sm max-w-md mx-auto">
          Reserve your spot with a visa counselor or university advisor — events go straight to your Google Calendar.
        </p>
      </div>

      {/* Google Calendar connection banner */}
      <CalendarConnectBanner calStatus={calStatus} onRefresh={fetchCalStatus} />

      {bookingSuccess ? (
        <div className="card p-10 text-center animate-scale-in max-w-xl mx-auto shadow-card border-none bg-gradient-to-b from-white to-mintLight/30">
          <CheckCircle2 className="w-16 h-16 text-mint mx-auto mb-4"/>
          <h2 className="text-2xl font-bold text-text mb-2">Slot Confirmed!</h2>
          <p className="text-textSoft mb-6">
            Your {activeTopic.duration}-minute session on <strong>{selectedDate}</strong> at <strong>{selectedSlot}</strong> is booked.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
            <button
              onClick={addToGoogleCalendar}
              disabled={calendarLoading}
              className="btn-primary flex items-center gap-2 shadow-soft w-full sm:w-auto disabled:opacity-60"
            >
              {calendarLoading
                ? <><Loader2 className="w-4 h-4 animate-spin"/> Adding to Calendar…</>
                : <><CalendarIcon className="w-4 h-4"/>
                    {isConnected ? 'Add to Google Calendar' : 'Add to Google Calendar'}</>}
            </button>
            <button
              onClick={() => { setBookingSuccess(false); setCalendarResult(null); }}
              className="btn-ghost w-full sm:w-auto"
            >
              Book Another
            </button>
          </div>

          {/* Calendar result feedback */}
          {calendarResult && (
            <div className={`mt-4 rounded-xl px-4 py-3 text-sm text-left
              ${calendarResult.success
                ? 'bg-mint/10 text-teal-700 border border-mint/30'
                : 'bg-amber-50 text-amber-800 border border-amber-200'}`}>
              {calendarResult.success ? (
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
                  <span>Event added to your Google Calendar!</span>
                  {calendarResult.event_link && (
                    <a href={calendarResult.event_link} target="_blank" rel="noopener noreferrer"
                      className="underline flex items-center gap-1 font-semibold ml-1">
                      Open <ExternalLink className="w-3 h-3" />
                    </a>
                  )}
                </div>
              ) : (
                <div>
                  <p className="font-semibold mb-1">
                    {calendarResult.status === 'not_connected' || calendarResult.status === 'not_configured'
                      ? 'Google Calendar not connected'
                      : 'Could not add to calendar'}
                  </p>
                  <p className="text-xs opacity-80">{calendarResult.message || calendarResult.error}</p>
                  {calendarResult.auth_url && (
                    <a href={calendarResult.auth_url} target="_blank" rel="noopener noreferrer"
                      className="mt-2 inline-flex items-center gap-1 text-xs font-semibold text-amber-900 underline">
                      Connect Google Calendar <ExternalLink className="w-3 h-3"/>
                    </a>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      ) : (
        <div className="grid md:grid-cols-5 gap-6">

          {/* Left: Topic */}
          <div className="md:col-span-2 space-y-4">
            <h2 className="font-bold text-text ml-1 mb-2">1. Select Service</h2>
            {APPOINTMENT_TYPES.map(t => (
              <div
                key={t.id}
                onClick={() => { setSelectedTopic(t.id); setSelectedSlot(''); }}
                className={`p-4 rounded-2xl cursor-pointer border-2 transition-all
                  ${selectedTopic === t.id
                    ? 'border-lavender bg-lavendLight/50'
                    : 'border-surfaceBorder hover:border-lavender/30 bg-surface'}`}
              >
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className={`font-bold ${selectedTopic === t.id ? 'text-lavender' : 'text-text'}`}>{t.name}</h3>
                    <div className="flex items-center gap-2 text-xs text-muted mt-2 font-medium">
                      <Clock className="w-3.5 h-3.5"/> {t.duration} Minutes
                    </div>
                  </div>
                  <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center
                    ${selectedTopic === t.id ? 'border-lavender' : 'border-surfaceBorder'}`}>
                    {selectedTopic === t.id && <div className="w-2.5 h-2.5 rounded-full bg-lavender animate-scale-in"/>}
                  </div>
                </div>
              </div>
            ))}

            <div className="mt-4 p-5 bg-surfaceAlt rounded-2xl border border-surfaceBorder/60">
              <div className="flex items-center gap-2 mb-2">
                <Building2 className="w-4 h-4 text-muted"/>
                <span className="text-xs font-semibold text-muted uppercase tracking-wide">Real Calendar Integration</span>
              </div>
              <p className="text-sm text-textSoft leading-relaxed">
                {isConnected
                  ? `Connected as ${calStatus?.email || 'your Google account'}. Appointments go straight to your calendar.`
                  : 'Connect Google Calendar above to save appointments directly to your calendar.'}
              </p>
            </div>
          </div>

          {/* Right: Date & Slot */}
          <div className="md:col-span-3 card p-6">
            <h2 className="font-bold text-text mb-4">2. Choose Date & Time</h2>

            <div className="mb-6">
              <label className="text-xs font-semibold text-muted block mb-2">Available Date</label>
              <input
                type="date"
                value={selectedDate}
                onChange={e => { setSelectedDate(e.target.value); setSelectedSlot(''); }}
                min={new Date().toISOString().split('T')[0]}
                className="input-field w-full py-3"
              />
            </div>

            <div className="mb-8">
              <label className="text-xs font-semibold text-muted block mb-2">Available Slots</label>
              {!selectedDate ? (
                <div className="p-8 text-center bg-surfaceAlt border border-surfaceBorder border-dashed rounded-xl text-muted text-sm">
                  Select a date to see available slots.
                </div>
              ) : (
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                  {activeTopic.slots.map(slot => (
                    <button
                      key={slot}
                      onClick={() => setSelectedSlot(slot)}
                      className={`py-3 px-2 text-sm font-semibold rounded-xl border transition-all
                        ${selectedSlot === slot
                          ? 'bg-mint text-white border-mint shadow-soft'
                          : 'bg-surface border-surfaceBorder hover:border-mint text-text'}`}
                    >
                      {slot}
                    </button>
                  ))}
                </div>
              )}
            </div>

            <button
              onClick={handleBooking}
              disabled={!selectedDate || !selectedSlot}
              className={`w-full py-4 rounded-xl flex items-center justify-center gap-2 font-bold transition-all
                ${(!selectedDate || !selectedSlot)
                  ? 'bg-surfaceAlt text-textSoft cursor-not-allowed'
                  : 'bg-lavender text-white shadow-cardHov hover:opacity-90'}`}
            >
              Confirm Booking <MoveRight className="w-4 h-4"/>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
