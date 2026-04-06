import { useState, useEffect } from 'react';
import { housingAPI } from '../api/visa';
import { Home, ExternalLink, MapPin, CheckCircle2, ChevronRight, Check } from 'lucide-react';

const ALL_COUNTRIES = ['All','USA','UK','Germany','France','Netherlands','Australia','Singapore','Hong Kong','Spain','Switzerland','Finland'];
const BUDGET_TIERS = [
  { label: 'All Budgets', min: null, max: null },
  { label: 'Below ₹40k/mo', min: null, max: 40000 },
  { label: '₹40k - ₹80k/mo', min: 40000, max: 80000 },
  { label: 'Above ₹80k/mo', min: 80000, max: null },
];

const FLAG = { 'United States':'🇺🇸', 'United Kingdom':'🇬🇧', 'Germany':'🇩🇪', 'France':'🇫🇷', 'Netherlands':'🇳🇱', 'Australia':'🇦🇺', 'Singapore':'🇸🇬', 'Hong Kong':'🇭🇰', 'Spain':'🇪🇸', 'Switzerland':'🇨🇭', 'Finland':'🇫🇮' };

export default function Housing() {
  const [country, setCountry] = useState('United Kingdom');
  const [budgetTier, setBudgetTier] = useState(0);
  const [studentFriendly, setStudentFriendly] = useState(false);
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchListings = async () => {
    setLoading(true);
    try {
      const params = {};
      const cName = country === 'All' ? 'All' : (country === 'UK' ? 'United Kingdom' : (country === 'USA' ? 'United States' : country));
      if (cName !== 'All') params.country = cName;
      
      const selectedTier = BUDGET_TIERS[budgetTier];
      if (selectedTier.min) params.min_price = selectedTier.min;
      if (selectedTier.max) params.max_price = selectedTier.max;
      
      if (studentFriendly) params.student_friendly = true;
      const res = await housingAPI.getListings(params);
      setData(res.results || []);
    } catch {
      setData([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchListings(); }, [country, budgetTier, studentFriendly]);

  return (
    <div className="animate-fade-in space-y-6 pb-10">
      <div className="page-header border-b border-surfaceBorder pb-6">
        <div className="page-icon bg-mintLight"><Home className="w-5 h-5 text-teal-600"/></div>
        <div>
          <h1 className="text-2xl font-bold text-text">Live Housing Map</h1>
          <p className="text-muted text-sm mt-0.5">Explore 600+ verified student accommodations worldwide</p>
        </div>
      </div>

      {/* Filters */}
      <div className="card p-5 flex flex-wrap items-end gap-5 bg-gradient-to-r from-surface to-mintLight/30 border-mint/20">
        <div>
          <label className="text-xs font-semibold text-muted block mb-1">Target Dimension</label>
          <select value={country} onChange={e=>setCountry(e.target.value)} className="input-field py-2 text-sm min-w-[160px] font-medium border-mint/20 bg-white">
            {ALL_COUNTRIES.map(c=><option key={c}>{c}</option>)}
          </select>
        </div>
        <div>
          <label className="text-xs font-semibold text-muted block mb-1">Monthly Budget (INR)</label>
          <select value={budgetTier} onChange={e=>setBudgetTier(Number(e.target.value))} className="input-field py-2 text-sm min-w-[160px] font-medium border-mint/20 bg-white">
            {BUDGET_TIERS.map((t, idx)=><option key={idx} value={idx}>{t.label}</option>)}
          </select>
        </div>
        <label className="flex items-center gap-2 cursor-pointer pb-2 self-end">
          <div className={`w-10 h-5 rounded-full transition-colors relative ${studentFriendly?'bg-mint':'bg-surfaceBorder'}`}
            onClick={()=>setStudentFriendly(!studentFriendly)}>
            <div className={`absolute top-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform ${studentFriendly?'translate-x-5':'translate-x-0.5'}`}/>
          </div>
          <span className="text-sm font-medium text-text">Exclude non-student rentals</span>
        </label>
      </div>

      {/* Results Title */}
      {!loading && (
        <h2 className="text-lg font-bold text-text flex items-center gap-2 mt-2">
          {data.length} Properties found <span className="text-muted font-normal text-sm">matching your criteria</span>
        </h2>
      )}

      {/* Results Grid */}
      {loading ? (
        <div className="py-24 flex flex-col items-center justify-center gap-3 text-muted">
          <div className="w-10 h-10 border-4 border-mint/30 border-t-teal-500 rounded-full animate-spin"/>
          <span className="text-sm font-medium">Scanning live property databases…</span>
        </div>
      ) : data.length === 0 ? (
        <div className="card p-16 text-center shadow-soft">
          <Home className="w-12 h-12 text-surfaceBorder mx-auto mb-4"/>
          <h3 className="text-lg font-bold text-text mb-1">No properties found</h3>
          <p className="text-muted text-sm">Try adjusting your budget or selecting a different country.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {data.map(prop => (
            <div key={prop.id} className="card-hover overflow-hidden group flex flex-col cursor-pointer border-surfaceBorder/80">
              <div className="h-44 relative overflow-hidden bg-surfaceAlt border-b border-surfaceBorder/50">
                {prop.image_url ? (
                   <img src={prop.image_url} alt="Housing" className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" />
                ) : (
                   <div className="w-full h-full flex items-center justify-center"><Home className="w-10 h-10 text-muted/30"/></div>
                )}
                {prop.student_friendly && (
                  <div className="absolute top-3 left-3 bg-white/90 backdrop-blur px-2.5 py-1 rounded-full text-[10px] font-bold text-teal-700 shadow flex items-center gap-1">
                    <CheckCircle2 className="w-3 h-3 fill-mint text-white"/> Student Recommended
                  </div>
                )}
                 <div className="absolute bottom-3 right-3 bg-text/90 backdrop-blur px-3 py-1.5 rounded-xl text-xs font-bold text-white shadow-lg">
                    ₹{prop.price_inr.toLocaleString('en-IN')}<span className="text-white/60 font-medium font-sans">/mo</span>
                </div>
              </div>
              
              <div className="p-5 flex-1 flex flex-col">
                <div className="flex items-start justify-between mb-2">
                  <h3 className="font-bold text-text text-base leading-tight group-hover:text-mint transition-colors pr-2">{prop.title}</h3>
                </div>
                <div className="flex items-center gap-1.5 text-xs text-muted mb-4 font-medium">
                  <MapPin className="w-3.5 h-3.5 text-mint"/> {FLAG[prop.country]} {prop.country} · {prop.distance_km}km from campus
                </div>
                
                <div className="flex flex-wrap gap-1.5 mb-5 mt-auto">
                  {prop.amenities?.slice(0,4).map(am => (
                    <span key={am} className="badge bg-surfaceAlt text-textSoft border border-surfaceBorder text-[10px] font-medium px-2 py-0.5">
                      {am}
                    </span>
                  ))}
                  {prop.amenities?.length > 4 && <span className="text-[10px] text-muted font-medium self-center">+{prop.amenities.length - 4} more</span>}
                </div>
                
                <div className="pt-4 border-t border-surfaceBorder/50 flex items-center justify-between mt-auto">
                   <div className="flex items-center gap-1 text-xs font-semibold text-textSoft">
                      <Check className="w-3.5 h-3.5 text-lavender"/> Available {prop.available_from}
                   </div>
                   <button className="text-mint text-sm font-bold flex items-center gap-0.5 group-hover:translate-x-1 transition-transform">
                      View details <ChevronRight className="w-4 h-4"/>
                   </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
