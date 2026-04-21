import { useState, useEffect, useCallback } from 'react';
import { housingAPI } from '../api/visa';
import {
  Home, MapPin, CheckCircle2, ChevronRight, ExternalLink,
  Loader2, RefreshCw, Wifi, IndianRupee, Info, AlertCircle
} from 'lucide-react';

// ── Country config ────────────────────────────────────────────────────────────
const COUNTRIES = [
  { name: 'United Kingdom', flag: '🇬🇧', scraped: true,  currency: 'GBP', symbol: '£',  cities: ['London','Manchester','Edinburgh','Birmingham','Bristol','Leeds','Glasgow','Liverpool'] },
  { name: 'Germany',        flag: '🇩🇪', scraped: true,  currency: 'EUR', symbol: '€',  cities: ['Munich','Berlin','Hamburg','Frankfurt','Cologne','Heidelberg'] },
  { name: 'Netherlands',    flag: '🇳🇱', scraped: true,  currency: 'EUR', symbol: '€',  cities: ['Amsterdam','Rotterdam'] },
  { name: 'France',         flag: '🇫🇷', scraped: true,  currency: 'EUR', symbol: '€',  cities: ['Paris','Lyon'] },
  { name: 'Singapore',      flag: '🇸🇬', scraped: true,  currency: 'EUR', symbol: '€',  cities: ['Singapore'] },
  { name: 'Canada',         flag: '🇨🇦', scraped: true,  currency: 'CAD', symbol: 'C$', cities: ['Toronto','Vancouver','Montreal','Ottawa'] },
  { name: 'United States',  flag: '🇺🇸', scraped: false, currency: 'USD', symbol: '$',  cities: ['New York','Boston','Chicago','Los Angeles','San Francisco'], site: 'Craigslist', siteUrl: 'https://craigslist.org' },
  { name: 'Ireland',        flag: '🇮🇪', scraped: false, currency: 'EUR', symbol: '€',  cities: ['Dublin','Cork','Galway'], site: 'Daft.ie', siteUrl: 'https://www.daft.ie/dublin/rooms-to-rent' },
  { name: 'Japan',          flag: '🇯🇵', scraped: false, currency: 'JPY', symbol: '¥',  cities: ['Tokyo','Osaka','Kyoto'], site: 'Sakura House', siteUrl: 'https://www.sakura-house.com/en/type/share-house' },
  { name: 'Australia',      flag: '🇦🇺', scraped: false, currency: 'AUD', symbol: 'A$', cities: ['Sydney','Melbourne','Brisbane','Perth','Adelaide'], site: 'Flatmates.com.au', siteUrl: 'https://flatmates.com.au' },
];

const BUDGET_TIERS = [
  { label: 'Any budget',        max: null    },
  { label: 'Under ₹60,000/mo', max: 60000   },
  { label: 'Under ₹1,00,000/mo',max: 100000  },
  { label: 'Under ₹1,50,000/mo',max: 150000  },
  { label: 'Under ₹2,50,000/mo',max: 250000  },
];

const formatInr = (n) => {
  if (!n) return '₹0';
  return '₹' + n.toLocaleString('en-IN');
};

export default function Housing() {
  const [country, setCountry]     = useState(COUNTRIES[0]);
  const [city, setCity]           = useState(COUNTRIES[0].cities[0]);
  const [budgetIdx, setBudgetIdx] = useState(0);
  const [data, setData]           = useState(null);
  const [loading, setLoading]     = useState(false);
  const [error, setError]         = useState('');

  const fetchListings = useCallback(async () => {
    setLoading(true);
    setError('');
    setData(null);
    try {
      const params = { country: country.name, city };
      const budget = BUDGET_TIERS[budgetIdx];
      if (budget.max) params.max_budget_inr = budget.max;

      const res = await housingAPI.getListings(params);
      setData(res);
    } catch (e) {
      setError('Could not fetch listings. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [country, city, budgetIdx]);

  useEffect(() => {
    if (country.scraped) fetchListings();
    else setData(null);
  }, [country, city, budgetIdx]);

  const handleCountryChange = (c) => {
    setCountry(c);
    setCity(c.cities[0]);
    setData(null);
  };

  const listings = data?.results || [];
  const searchLink = data?.search_link;
  const source = data?.source;

  return (
    <div className="animate-fade-in space-y-5 pb-10">

      {/* Header */}
      <div className="page-header">
        <div className="page-icon bg-mintLight"><Home className="w-5 h-5 text-teal-600" /></div>
        <div>
          <h1 className="text-2xl font-bold text-text">Student Housing</h1>
          <p className="text-muted text-sm mt-0.5">Real listings from SpareRoom, WG-Gesucht & more · All prices in ₹</p>
        </div>
      </div>

      {/* Country selector */}
      <div className="grid grid-cols-5 sm:grid-cols-10 gap-2">
        {COUNTRIES.map(c => (
          <button key={c.name}
            onClick={() => handleCountryChange(c)}
            className={`flex flex-col items-center gap-1 p-2 rounded-xl border text-center transition-all
              ${country.name === c.name
                ? 'border-teal-400 bg-mintLight shadow-sm'
                : 'border-surfaceBorder bg-white hover:border-teal-300'}`}>
            <span className="text-2xl">{c.flag}</span>
            <span className={`text-[10px] font-semibold leading-tight ${country.name === c.name ? 'text-teal-700' : 'text-textSoft'}`}>
              {c.name.split(' ')[0]}
            </span>
            {c.scraped && (
              <span className="text-[8px] font-bold text-teal-500 bg-mintLight px-1 rounded">LIVE</span>
            )}
          </button>
        ))}
      </div>

      {/* City + budget filters */}
      <div className="card p-4 flex flex-wrap gap-4 items-end">
        <div>
          <label className="text-xs font-semibold text-muted block mb-1">City</label>
          <select
            value={city}
            onChange={e => setCity(e.target.value)}
            className="input-field py-2 text-sm min-w-[160px]"
          >
            {country.cities.map(c => <option key={c}>{c}</option>)}
          </select>
        </div>
        <div>
          <label className="text-xs font-semibold text-muted block mb-1">Max monthly budget</label>
          <div className="flex gap-2 flex-wrap">
            {BUDGET_TIERS.map((t, i) => (
              <button key={i} onClick={() => setBudgetIdx(i)}
                className={`px-3 py-1.5 text-xs rounded-lg border font-semibold transition-all
                  ${budgetIdx === i ? 'bg-teal-500 text-white border-teal-500' : 'bg-white text-textSoft border-surfaceBorder hover:border-teal-400'}`}>
                {t.label}
              </button>
            ))}
          </div>
        </div>
        {country.scraped && (
          <button onClick={fetchListings} disabled={loading}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl border border-teal-300 text-teal-700 text-sm font-semibold hover:bg-mintLight transition-all disabled:opacity-50 ml-auto">
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        )}
      </div>

      {/* Source badge */}
      {source && source !== 'redirect' && (
        <div className="flex items-center gap-2 text-xs text-teal-700 font-semibold">
          <div className="w-2 h-2 bg-teal-400 rounded-full animate-pulse" />
          Live listings from <span className="underline">{source}</span> ·
          Prices converted to INR (1 {country.currency} ≈ ₹{{
            GBP: 107, EUR: 90, USD: 83, CAD: 62, SGD: 62, JPY: 0.56, AUD: 55
          }[country.currency] || 83})
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="py-24 flex flex-col items-center gap-3 text-muted">
          <Loader2 className="w-8 h-8 text-teal-500 animate-spin" />
          <p className="text-sm font-medium">Fetching real listings from {source || '...'}…</p>
          <p className="text-xs text-muted">This may take a few seconds</p>
        </div>
      )}

      {/* Error */}
      {error && !loading && (
        <div className="card p-4 border-rose/30 bg-rose/5 flex items-center gap-3 text-rose text-sm">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          {error}
        </div>
      )}

      {/* Redirect card for non-scraped countries */}
      {!country.scraped && !loading && (
        <div className="card p-8 text-center space-y-4">
          <div className="text-5xl">{country.flag}</div>
          <div>
            <h3 className="font-bold text-text text-lg">{country.name} Housing</h3>
            <p className="text-muted text-sm mt-1">
              We recommend <strong>{country.site}</strong> for student rooms in {country.name}.
              Click below to search with your preferred city and budget.
            </p>
          </div>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <a href={country.siteUrl} target="_blank" rel="noopener noreferrer"
              className="btn-primary inline-flex items-center gap-2 justify-center px-6">
              Search on {country.site} <ExternalLink className="w-4 h-4" />
            </a>
          </div>
          <p className="text-xs text-muted">
            Budget tip: {country.symbol}500–{country.symbol}1,500/mo is typical for student rooms.
            In INR that's approx{' '}
            {formatInr(500 * (country.currency === 'GBP' ? 107 : country.currency === 'EUR' ? 90 : country.currency === 'AUD' ? 55 : 83))}–
            {formatInr(1500 * (country.currency === 'GBP' ? 107 : country.currency === 'EUR' ? 90 : country.currency === 'AUD' ? 55 : 83))}/mo
          </p>
        </div>
      )}

      {/* Real listing grid */}
      {!loading && listings.length > 0 && (
        <>
          <p className="text-sm text-muted font-medium">
            <span className="font-black text-text">{listings.length}</span> real listings in {city} ·
            sorted by price
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {listings
              .sort((a, b) => (a.price_inr || 0) - (b.price_inr || 0))
              .map(prop => (
                <PropertyCard key={prop.id || prop.listing_url} prop={prop} />
              ))}
          </div>
        </>
      )}

      {/* Empty state */}
      {!loading && !error && country.scraped && data && listings.length === 0 && (
        <div className="card p-12 text-center">
          <Home className="w-10 h-10 text-surfaceBorder mx-auto mb-3" />
          <p className="font-semibold text-text">No listings found</p>
          <p className="text-sm text-muted mt-1">Try a higher budget or a different city.</p>
        </div>
      )}
    </div>
  );
}

function PropertyCard({ prop }) {
  return (
    <div className="card overflow-hidden flex flex-col group hover:shadow-cardHov transition-shadow">
      {/* Image */}
      <div className="h-44 relative overflow-hidden bg-surfaceAlt">
        {prop.image_url ? (
          <img
            src={prop.image_url}
            alt={prop.title}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
            onError={e => { e.target.style.display = 'none'; }}
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <Home className="w-10 h-10 text-muted/20" />
          </div>
        )}

        {/* Source badge */}
        <div className="absolute top-2 left-2">
          <span className="text-[9px] font-bold bg-white/90 backdrop-blur text-teal-700 px-2 py-0.5 rounded-full">
            {prop.source}
          </span>
        </div>

        {/* Bills included */}
        {prop.bills_inc && (
          <div className="absolute top-2 right-2">
            <span className="text-[9px] font-bold bg-teal-500 text-white px-2 py-0.5 rounded-full">
              Bills incl.
            </span>
          </div>
        )}

        {/* Price overlay */}
        <div className="absolute bottom-0 inset-x-0 bg-gradient-to-t from-black/70 to-transparent p-3 pt-8">
          <div className="flex items-end justify-between">
            <div>
              <p className="text-white/70 text-[10px]">Monthly rent</p>
              <p className="text-white font-black text-lg leading-none">
                {formatInr(prop.price_inr)}
              </p>
            </div>
            <p className="text-white/60 text-xs font-medium">{prop.price_label}</p>
          </div>
        </div>
      </div>

      {/* Body */}
      <div className="p-4 flex-1 flex flex-col">
        <h3 className="font-bold text-text text-sm line-clamp-2 group-hover:text-teal-600 transition-colors mb-2">
          {prop.title}
        </h3>

        <div className="flex items-center gap-1.5 text-xs text-muted mb-3">
          <MapPin className="w-3 h-3 text-teal-500 flex-shrink-0" />
          <span className="truncate">{prop.area || prop.country}</span>
        </div>

        {/* Amenities if any */}
        {prop.amenities?.length > 0 && (
          <div className="flex flex-wrap gap-1 mb-3">
            {prop.amenities.slice(0, 3).map(a => (
              <span key={a} className="text-[10px] bg-surfaceAlt text-textSoft px-2 py-0.5 rounded-full border border-surfaceBorder">{a}</span>
            ))}
          </div>
        )}

        <a
          href={prop.listing_url}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-auto flex items-center justify-between pt-3 border-t border-surfaceBorder text-sm font-bold text-teal-600 hover:text-teal-700 transition-colors"
        >
          <span>View on {prop.source}</span>
          <ExternalLink className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
        </a>
      </div>
    </div>
  );
}

