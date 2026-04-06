import { useState, useEffect } from 'react';
import { Sparkles, Calendar, TrendingUp, Download, ArrowRight, Building2, MapPin, FileCheck } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function Dashboard() {
  const [profile, setProfile] = useState({
    name: 'Student',
    targetCountry: 'USA, UK',
    cgpa: 8.5,
    completion: 85
  });

  return (
    <div className="space-y-6 animate-fade-in">
      
      {/* ── Welcome Banner ── */}
      <div className="relative card overflow-hidden bg-gradient-to-br from-lavender to-[#5C4DDF] p-8 text-white border-none pb-12">
        <div className="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2" />
        <div className="absolute bottom-0 right-10 w-48 h-48 bg-white/10 rounded-full blur-2xl translate-y-1/4" />
        
        <div className="relative z-10 flex items-start justify-between">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <div className="p-2 bg-white/20 rounded-xl backdrop-blur-sm"><Sparkles className="w-6 h-6 text-white"/></div>
              <h1 className="text-3xl font-bold">Welcome back, {profile.name}!</h1>
            </div>
            <p className="text-white/80 max-w-lg mt-2 text-sm leading-relaxed">
              Your personalized admission timeline is on track. You have highly competitive matches based on your {profile.cgpa} CGPA. Keep your momentum going!
            </p>
          </div>
        </div>
      </div>

      {/* ── Core Widgets ── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 -mt-8 relative z-10 px-4">
        
        {/* Next Steps Card */}
        <div className="card p-6 flex flex-col gap-4">
          <div className="flex items-center gap-2 mb-2">
            <div className="w-8 h-8 rounded-lg bg-roseLight text-rose flex items-center justify-center"><Calendar className="w-4 h-4"/></div>
            <h2 className="font-bold text-text">Upcoming Deadlines</h2>
          </div>
          <div className="space-y-3">
            <div className="bg-surfaceAlt p-3 rounded-xl border border-surfaceBorder">
              <div className="flex justify-between items-start mb-1">
                <span className="text-xs font-semibold text-rose">In 4 Days</span>
                <span className="text-[10px] text-muted">Fall Intake</span>
              </div>
              <h3 className="text-sm font-bold text-text">UK Visa Application Submission</h3>
            </div>
            <div className="bg-surfaceAlt p-3 rounded-xl border border-surfaceBorder">
              <div className="flex justify-between items-start mb-1">
                <span className="text-xs font-semibold text-amber-600">In 2 Weeks</span>
                <span className="text-[10px] text-muted">Regular Decision</span>
              </div>
              <h3 className="text-sm font-bold text-text">Submit SOP to Target Universities</h3>
            </div>
          </div>
          <Link to="/appointments" className="btn-ghost mt-auto pt-2 text-xs text-lavender justify-center w-full">Manage Calendar & Bookings <ArrowRight className="w-3 h-3"/></Link>
        </div>

        {/* Profile Strength */}
        <div className="card p-6 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-mintLight text-teal-600 flex items-center justify-center"><TrendingUp className="w-4 h-4"/></div>
                <h2 className="font-bold text-text">Profile Strength</h2>
              </div>
              <span className="text-lg font-black text-teal-600">{profile.completion}%</span>
            </div>
            
            <div className="w-full bg-surfaceAlt rounded-full h-3 mb-6 overflow-hidden">
              <div className="bg-gradient-to-r from-mint to-teal-500 h-3 rounded-full relative" style={{width: `${profile.completion}%`}}>
                <div className="absolute inset-0 bg-white/20 animate-pulse"></div>
              </div>
            </div>
            
            <ul className="space-y-2 text-sm text-textSoft">
              <li className="flex items-center gap-2"><div className="w-1.5 h-1.5 rounded-full bg-mint"/> Transcripts Uploaded</li>
              <li className="flex items-center gap-2"><div className="w-1.5 h-1.5 rounded-full bg-mint"/> Language Test (IELTS) Submitted</li>
              <li className="flex items-center gap-2"><div className="w-1.5 h-1.5 rounded-full bg-surfaceBorder"/> Upload Financial Proof </li>
            </ul>
          </div>
        </div>

        {/* Action Center */}
        <div className="card p-6 border-lavender/30 bg-lavendLight/30 flex flex-col gap-3">
           <h2 className="font-bold text-text mb-2">Fast Actions</h2>
           
           <Link to="/universities" className="flex items-center justify-between p-3 bg-white rounded-xl shadow-soft hover:shadow-cardHov transition-all group">
             <div className="flex items-center gap-3">
               <div className="w-8 h-8 bg-skyLight text-blue-600 rounded-lg flex items-center justify-center"><Building2 className="w-4 h-4"/></div>
               <span className="font-semibold text-sm text-text">Browse 500+ Universities</span>
             </div>
             <ArrowRight className="w-4 h-4 text-muted group-hover:text-lavender transition-colors"/>
           </Link>

           <Link to="/housing" className="flex items-center justify-between p-3 bg-white rounded-xl shadow-soft hover:shadow-cardHov transition-all group">
             <div className="flex items-center gap-3">
               <div className="w-8 h-8 bg-peachLight text-peach rounded-lg flex items-center justify-center"><MapPin className="w-4 h-4"/></div>
               <span className="font-semibold text-sm text-text">Live Housing Search</span>
             </div>
             <ArrowRight className="w-4 h-4 text-muted group-hover:text-peach transition-colors"/>
           </Link>

           <Link to="/visa-chat" className="flex items-center justify-between p-3 bg-white rounded-xl shadow-soft hover:shadow-cardHov transition-all group">
             <div className="flex items-center gap-3">
               <div className="w-8 h-8 bg-amberLight text-amber-600 rounded-lg flex items-center justify-center"><FileCheck className="w-4 h-4"/></div>
               <span className="font-semibold text-sm text-text">Visa AI & Guidance</span>
             </div>
             <ArrowRight className="w-4 h-4 text-muted group-hover:text-amber-600 transition-colors"/>
           </Link>

        </div>
      </div>
    </div>
  );
}
