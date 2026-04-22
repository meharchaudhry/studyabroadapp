import { useState } from 'react';
import { Calendar as CalendarIcon, Clock, MoveRight, Download, CheckCircle2, Building2 } from 'lucide-react';
import { Link } from 'react-router-dom';

const APPOINTMENT_TYPES = [
  { id: 'visa', name: 'Visa & Immigration Consultancy', duration: 45, slots: ['09:00 AM', '11:00 AM', '02:00 PM', '04:30 PM'] },
  { id: 'uni', name: 'University Admissions Counselor', duration: 30, slots: ['10:00 AM', '01:00 PM', '03:15 PM'] },
];

export default function BookingAppointments() {
  const [selectedTopic, setSelectedTopic] = useState('visa');
  const [selectedDate, setSelectedDate] = useState('');
  const [selectedSlot, setSelectedSlot] = useState('');
  const [bookingSuccess, setBookingSuccess] = useState(false);

  const activeTopic = APPOINTMENT_TYPES.find(t => t.id === selectedTopic);

  const generateICS = () => {
    if (!selectedDate || !selectedSlot) return null;
    
    // Create ICS file simulating a Google Calendar event
    // Using simplistic iCalendar format
    const startDate = selectedDate.replace(/-/g, '');
    const timeMatch = selectedSlot.match(/(\d+):(\d+) (AM|PM)/);
    let hours = parseInt(timeMatch[1]);
    if (timeMatch[3] === 'PM' && hours !== 12) hours += 12;
    if (timeMatch[3] === 'AM' && hours === 12) hours = 0;
    
    const startHourStr = hours.toString().padStart(2, '0');
    const minStr = timeMatch[2];
    
    // Add duration
    let endHours = hours + (activeTopic.duration === 45 ? 1 : 0);
    let endMins = parseInt(minStr) + (activeTopic.duration === 30 ? 30 : 45);
    if(endMins >= 60) {
        endHours += 1;
        endMins -= 60;
    }
    const endHourStr = endHours.toString().padStart(2, '0');
    const endMinStr = endMins.toString().padStart(2, '0');

    const dtStart = `${startDate}T${startHourStr}${minStr}00`;
    const dtEnd = `${startDate}T${endHourStr}${endMinStr}00`;

    const icsContent = `BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
SUMMARY:PathPilot: ${activeTopic.name}
DTSTART;TZID=Asia/Kolkata:${dtStart}
DTEND;TZID=Asia/Kolkata:${dtEnd}
DESCRIPTION:Official Mock Appointment for University & Visa Consultation
LOCATION:Online Meeting (Google Meet link will be generated 1h prior)
END:VEVENT
END:VCALENDAR`;

    return `data:text/calendar;charset=utf-8,${encodeURIComponent(icsContent)}`;
  };

  const handleBooking = () => {
    if (!selectedDate || !selectedSlot) return;
    setBookingSuccess(true);
  };

  return (
    <div className="animate-fade-in space-y-6 max-w-4xl mx-auto pb-10">
      <div className="text-center py-8">
        <div className="w-16 h-16 bg-lavendLight rounded-2xl flex items-center justify-center mx-auto mb-4 scale-110">
          <CalendarIcon className="w-8 h-8 text-lavender"/>
        </div>
        <h1 className="text-3xl font-bold text-text mb-2">Book an Official Appointment</h1>
        <p className="text-muted text-sm max-w-md mx-auto">
          Integrate with live scheduling systems to reserve your spot with university representatives or state visa counselors.
        </p>
      </div>

      {bookingSuccess ? (
        <div className="card p-10 text-center animate-scale-in max-w-xl mx-auto shadow-card border-none bg-gradient-to-b from-white to-mintLight/30">
          <CheckCircle2 className="w-16 h-16 text-mint mx-auto mb-4"/>
          <h2 className="text-2xl font-bold text-text mb-2">Slot Confirmed!</h2>
          <p className="text-textSoft mb-6">
            Your {activeTopic.duration}-minute session on <strong>{selectedDate}</strong> at <strong>{selectedSlot}</strong> is successfully booked.
          </p>
          
          <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
            <a 
              href={generateICS()} 
              download={`PathPilot_${activeTopic.id}_Appointment.ics`}
              className="btn-primary flex items-center gap-2 shadow-soft w-full sm:w-auto"
            >
              <Download className="w-4 h-4"/> Add to Google Calendar (.ics)
            </a>
            <button onClick={() => setBookingSuccess(false)} className="btn-ghost w-full sm:w-auto">Book Another</button>
          </div>
        </div>
      ) : (
        <div className="grid md:grid-cols-5 gap-6">
          
          {/* Left Panel: Topic Selection */}
          <div className="md:col-span-2 space-y-4">
            <h2 className="font-bold text-text ml-1 mb-2">1. Select Service Level</h2>
            {APPOINTMENT_TYPES.map(t => (
              <div 
                key={t.id} 
                onClick={() => { setSelectedTopic(t.id); setSelectedSlot(''); }}
                className={`p-4 rounded-2xl cursor-pointer border-2 transition-all ${selectedTopic === t.id ? 'border-lavender bg-lavendLight/50' : 'border-surfaceBorder hover:border-lavender/30 bg-surface'}`}
              >
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className={`font-bold ${selectedTopic === t.id ? 'text-lavender' : 'text-text'}`}>{t.name}</h3>
                    <div className="flex items-center gap-2 text-xs text-muted mt-2 font-medium">
                      <Clock className="w-3.5 h-3.5"/> {t.duration} Minutes
                    </div>
                  </div>
                  <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center ${selectedTopic === t.id ? 'border-lavender' : 'border-surfaceBorder'}`}>
                    {selectedTopic === t.id && <div className="w-2.5 h-2.5 rounded-full bg-lavender animate-scale-in"/>}
                  </div>
                </div>
              </div>
            ))}
            
            <div className="mt-8 p-6 bg-surfaceAlt rounded-2xl border border-surfaceBorder/60">
                <div className="flex items-center justify-center w-10 h-10 bg-white rounded-xl shadow-sm mb-3">
                    <Building2 className="w-5 h-5 text-muted"/>
                </div>
                <p className="text-sm text-textSoft font-medium leading-relaxed">
                   Syncing dynamically with university external portals to provide the latest real-time slot availability.
                </p>
            </div>
          </div>
          
          {/* Right Panel: Date & Slot */}
          <div className="md:col-span-3 card p-6">
            <h2 className="font-bold text-text mb-4">2. Choose Date & Time</h2>
            
            <div className="mb-6">
              <label className="text-xs font-semibold text-muted block mb-2">Available Date</label>
              <input 
                type="date" 
                value={selectedDate} 
                onChange={(e) => { setSelectedDate(e.target.value); setSelectedSlot(''); }}
                min={new Date().toISOString().split('T')[0]}
                className="input-field w-full py-3"
              />
            </div>
            
            <div className="mb-8">
              <label className="text-xs font-semibold text-muted block mb-2">Live Availability Slots</label>
              {!selectedDate ? (
                <div className="p-8 text-center bg-surfaceAlt border border-surfaceBorder border-dashed rounded-xl text-muted text-sm">
                  Please select a date to fetch live slots.
                </div>
              ) : (
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                  {activeTopic.slots.map(slot => (
                    <button 
                      key={slot}
                      onClick={() => setSelectedSlot(slot)}
                      className={`py-3 px-2 text-sm font-semibold rounded-xl border transition-all ${selectedSlot === slot ? 'bg-mint text-white border-mint shadow-soft' : 'bg-surface border-surfaceBorder hover:border-mint text-text'}`}
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
              className={`w-full py-4 rounded-xl flex items-center justify-center gap-2 font-bold transition-all ${(!selectedDate || !selectedSlot) ? 'bg-surfaceAlt text-textSoft cursor-not-allowed' : 'bg-lavender text-white shadow-cardHov hover:opacity-90'}`}
            >
              Confirm Official Booking <MoveRight className="w-4 h-4"/>
            </button>
          </div>
          
        </div>
      )}
    </div>
  );
}
