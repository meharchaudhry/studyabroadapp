import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { universitiesAPI } from '../api/universities';
import { ArrowLeft, MapPin, Star, BookOpen, ExternalLink, Award, GraduationCap, Calendar, CheckCircle2 } from 'lucide-react';

function formatINR(n) {
  if (!n) return '—';
  if (n >= 100000) return `₹${(n/100000).toFixed(1)}L`;
  return `₹${n.toLocaleString('en-IN')}`;
}

export default function UniversityDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [uni, setUni] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDetail = async () => {
      try {
        const data = await universitiesAPI.getById(id);
        setUni(data);
      } catch (err) {
        setUni(null);
      } finally {
        setLoading(false);
      }
    };
    fetchDetail();
  }, [id]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center p-20 gap-4">
        <div className="w-10 h-10 border-4 border-lavender/30 border-t-lavender rounded-full animate-spin"/>
        <p className="text-muted text-sm font-medium">Loading university profile...</p>
      </div>
    );
  }

  if (!uni) {
    return (
      <div className="card p-12 text-center">
        <h2 className="text-xl font-bold text-text mb-2">University Not Found</h2>
        <p className="text-muted mb-6">The institution you are looking for does not exist or has been removed.</p>
        <button onClick={() => navigate('/universities')} className="btn-primary">Browse All Universities</button>
      </div>
    );
  }

  const FLAG = { USA:'🇺🇸', UK:'🇬🇧', Germany:'🇩🇪', France:'🇫🇷', Netherlands:'🇳🇱', Australia:'🇦🇺', Singapore:'🇸🇬', HongKong:'🇭🇰', Spain:'🇪🇸', Switzerland:'🇨🇭', Finland:'🇫🇮' };

  return (
    <div className="animate-fade-in pb-10">
      <button onClick={() => navigate(-1)} className="btn-ghost text-muted mb-4 group -ml-4">
        <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform"/> Back to Catalog
      </button>

      {/* Hero Section */}
      <div className="card overflow-hidden mb-6 border-none shadow-card">
        <div className="h-64 bg-lavendLight relative">
          {uni.image_url ? (
            <img src={uni.image_url} alt={uni.name} className="w-full h-full object-cover" />
          ) : (
            <div className="w-full h-full flex items-center justify-center bg-gradient-to-r from-lavender/20 to-skyLight"><GraduationCap className="w-20 h-20 text-lavender/40"/></div>
          )}
          <div className="absolute inset-0 bg-gradient-to-t from-text/80 via-text/20 to-transparent"/>
          
          <div className="absolute bottom-0 left-0 right-0 p-8">
            <h1 className="text-4xl font-bold text-white mb-2">{uni.name}</h1>
            <div className="flex flex-wrap items-center gap-4 text-white/90 text-sm font-medium">
              <span className="flex items-center gap-1.5"><MapPin className="w-4 h-4"/>{FLAG[uni.country]} {uni.country}</span>
              {(uni.qs_subject_ranking || uni.ranking) && (
                <span className="flex items-center gap-1.5"><Star className="w-4 h-4 fill-amber-400 text-amber-400"/> QS World Rank #{uni.qs_subject_ranking || uni.ranking}</span>
              )}
              {uni.subject && <span className="flex items-center gap-1.5"><BookOpen className="w-4 h-4 text-sky-300"/> {uni.subject}</span>}
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Requirements */}
        <div className="lg:col-span-2 space-y-6">
          <div className="card p-6">
            <h2 className="text-lg font-bold text-text mb-4 border-b border-surfaceBorder pb-2">Admission Requirements (India)</h2>
            <div className="grid sm:grid-cols-2 gap-4">
              <div className="bg-surfaceAlt p-4 rounded-xl">
                <p className="text-xs text-muted font-semibold mb-1">Academic (CGPA)</p>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-5 h-5 text-mint"/>
                  <span className="text-lg font-bold text-text">{uni.requirements_cgpa || '7.0'}/10 <span className="text-sm font-normal text-muted ml-1">minimum</span></span>
                </div>
              </div>
              <div className="bg-surfaceAlt p-4 rounded-xl">
                <p className="text-xs text-muted font-semibold mb-1">English Proficiency</p>
                <div className="flex items-center gap-3">
                  <span className="text-sm font-bold text-text">IELTS: <span className="text-lavender ml-1">{uni.ielts || '6.5'}</span></span>
                  <span className="w-px h-4 bg-surfaceBorder"/>
                  <span className="text-sm font-bold text-text">TOEFL: <span className="text-sky-600 ml-1">{uni.toefl || '90'}</span></span>
                </div>
              </div>
              <div className="bg-surfaceAlt p-4 rounded-xl">
                <p className="text-xs text-muted font-semibold mb-1">Standardized Tests</p>
                <p className="text-sm font-bold text-text">GRE/GMAT: <span className={uni.gre_required ? 'text-peach' : 'text-teal-600'}>{uni.gre_required ? 'Required' : 'Optional'}</span></p>
              </div>
               <div className="bg-surfaceAlt p-4 rounded-xl">
                <p className="text-xs text-muted font-semibold mb-1">Course Duration</p>
                <p className="text-sm font-bold text-text flex items-center gap-1.5"><Calendar className="w-4 h-4 text-muted"/>{uni.course_duration || 2} Years</p>
              </div>
            </div>
          </div>

           {uni.scholarships && (
            <div className="card p-6 bg-gradient-to-br from-amberLight to-orange-50/50 border-amber/20">
              <h2 className="text-lg font-bold text-amber-900 mb-3 flex items-center gap-2"><Award className="w-5 h-5"/> Available Scholarships</h2>
              <p className="text-sm text-amber-800 leading-relaxed font-medium">{uni.scholarships}</p>
            </div>
          )}
          
          <div className="card p-6">
            <h2 className="text-lg font-bold text-text mb-4 border-b border-surfaceBorder pb-2">Why Study Here?</h2>
            <p className="text-sm text-textSoft leading-relaxed">
              {uni.name} is a premier institution located in {uni.country}. Ranked globally for its excellence in {uni.subject || 'various disciplines'}, it offers extensive opportunities for international students. The campus provides a vibrant community, cutting-edge facilities, and strong industry connections to kickstart your career.
            </p>
          </div>
        </div>

        {/* Right Column: Costs & Actions */}
        <div className="space-y-6">
          <div className="card p-6">
            <h2 className="font-bold text-text mb-4">Cost Estimator / Year</h2>
            <div className="space-y-4">
              <div className="flex justify-between items-center pb-3 border-b border-surfaceBorder border-dashed">
                <span className="text-sm text-muted">Estimated Tuition</span>
                <span className="font-bold text-text">{formatINR(uni.tuition)}</span>
              </div>
              <div className="flex justify-between items-center pb-3 border-b border-surfaceBorder border-dashed">
                <span className="text-sm text-muted">Living Expenses</span>
                <span className="font-bold text-text">{formatINR(uni.living_cost)}</span>
              </div>
              <div className="flex justify-between items-center pt-2">
                <span className="text-sm font-bold text-text">Total Needed</span>
                <span className="text-lg font-black text-teal-600 bg-mintLight px-3 py-1 rounded-lg">
                  {formatINR((uni.tuition || 0) + (uni.living_cost || 0))}
                </span>
              </div>
            </div>
            
            <div className="mt-8 space-y-3">
              <a href={uni.website || '#'} target="_blank" rel="noreferrer" className="btn-primary w-full shadow-cardHov">
                Visit Official Website <ExternalLink className="w-4 h-4"/>
              </a>
              <button className="btn-secondary w-full">Save to Dashboard</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
