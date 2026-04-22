import { useState, useEffect, useCallback } from 'react';
import { housingAPI } from '../api/visa';
import {
  Home, MapPin, ExternalLink, Loader2, RefreshCw,
  IndianRupee, AlertCircle, GraduationCap, Globe,
  Search, TrendingUp, Info, Lightbulb
} from 'lucide-react';

// ─────────────────────────────────────────────────────────────────────────────
// COUNTRY CONFIG
// ─────────────────────────────────────────────────────────────────────────────
const COUNTRIES = [
  { name:'United Kingdom',    apiName:'United Kingdom',       flag:'🇬🇧', scraped:true,  currency:'GBP', symbol:'£',   cities:['London','Manchester','Edinburgh','Birmingham','Bristol','Leeds','Glasgow','Liverpool','Nottingham','Sheffield','Newcastle','Coventry'] },
  { name:'Germany',           apiName:'Germany',              flag:'🇩🇪', scraped:true,  currency:'EUR', symbol:'€',   cities:['Munich','Berlin','Hamburg','Frankfurt','Cologne','Heidelberg','Stuttgart','Dusseldorf'] },
  { name:'Australia',         apiName:'Australia',            flag:'🇦🇺', scraped:false, currency:'AUD', symbol:'A$',  cities:['Sydney','Melbourne','Brisbane','Perth','Adelaide'] },
  { name:'Canada',            apiName:'Canada',               flag:'🇨🇦', scraped:false, currency:'CAD', symbol:'C$',  cities:['Toronto','Vancouver','Montreal','Ottawa','Calgary'] },
  { name:'United States',     apiName:'United States',        flag:'🇺🇸', scraped:false, currency:'USD', symbol:'$',   cities:['New York','Boston','Chicago','Los Angeles','San Francisco','Seattle','Austin','Houston','Atlanta'] },
  { name:'Ireland',           apiName:'Ireland',              flag:'🇮🇪', scraped:false, currency:'EUR', symbol:'€',   cities:['Dublin','Cork','Galway','Limerick'] },
  { name:'Netherlands',       apiName:'Netherlands',          flag:'🇳🇱', scraped:false, currency:'EUR', symbol:'€',   cities:['Amsterdam','Rotterdam','The Hague','Eindhoven','Utrecht'] },
  { name:'France',            apiName:'France',               flag:'🇫🇷', scraped:false, currency:'EUR', symbol:'€',   cities:['Paris','Lyon','Marseille','Bordeaux','Toulouse'] },
  { name:'Spain',             apiName:'Spain',                flag:'🇪🇸', scraped:false, currency:'EUR', symbol:'€',   cities:['Madrid','Barcelona','Valencia','Seville','Bilbao'] },
  { name:'Singapore',         apiName:'Singapore',            flag:'🇸🇬', scraped:false, currency:'SGD', symbol:'S$',  cities:['Singapore'] },
  { name:'Japan',             apiName:'Japan',                flag:'🇯🇵', scraped:false, currency:'JPY', symbol:'¥',   cities:['Tokyo','Osaka','Kyoto','Nagoya','Fukuoka'] },
  { name:'Sweden',            apiName:'Sweden',               flag:'🇸🇪', scraped:false, currency:'SEK', symbol:'kr',  cities:['Stockholm','Gothenburg','Malmö','Uppsala'] },
  { name:'Denmark',           apiName:'Denmark',              flag:'🇩🇰', scraped:false, currency:'DKK', symbol:'kr',  cities:['Copenhagen','Aarhus','Odense'] },
  { name:'UAE',               apiName:'United Arab Emirates', flag:'🇦🇪', scraped:false, currency:'AED', symbol:'AED', cities:['Dubai','Abu Dhabi','Sharjah'] },
  { name:'New Zealand',       apiName:'New Zealand',          flag:'🇳🇿', scraped:false, currency:'NZD', symbol:'NZ$', cities:['Auckland','Wellington','Christchurch'] },
  { name:'South Korea',       apiName:'South Korea',          flag:'🇰🇷', scraped:false, currency:'KRW', symbol:'₩',   cities:['Seoul','Busan','Daejeon','Incheon'] },
  { name:'Norway',            apiName:'Norway',               flag:'🇳🇴', scraped:false, currency:'NOK', symbol:'kr',  cities:['Oslo','Bergen','Trondheim'] },
  { name:'Italy',             apiName:'Italy',                flag:'🇮🇹', scraped:false, currency:'EUR', symbol:'€',   cities:['Rome','Milan','Bologna','Florence','Turin'] },
];

// ─────────────────────────────────────────────────────────────────────────────
// COUNTRY INFO  — avg rent (INR) + student hubs per city + housing tip
// All rent figures are monthly room/flat-share rates in INR (2024–25 data)
// ─────────────────────────────────────────────────────────────────────────────
const COUNTRY_INFO = {
  'United Kingdom': {
    tip: 'Apply for university accommodation on offer-day — private rooms fill up within days of Results.',
    cities: {
      London:       { min:85000,  max:160000, hubs:['Hackney','Stratford','Bethnal Green','Elephant & Castle','Tooting','Brixton'] },
      Manchester:   { min:48000,  max:90000,  hubs:['Fallowfield','Withington','Rusholme','Hulme','Didsbury'] },
      Edinburgh:    { min:60000,  max:107000, hubs:['Marchmont','Morningside','Newington','Leith','Gorgie'] },
      Birmingham:   { min:40000,  max:74000,  hubs:['Selly Oak','Edgbaston','Harborne','Bournbrook','Moseley'] },
      Bristol:      { min:50000,  max:90000,  hubs:['Clifton','Redland','Bedminster','Easton','Cotham'] },
      Leeds:        { min:40000,  max:72000,  hubs:['Hyde Park','Headingley','Burley','Woodhouse','Meanwood'] },
      Glasgow:      { min:40000,  max:72000,  hubs:['West End','Hillhead','Shawlands','Partick','Finnieston'] },
      Liverpool:    { min:36000,  max:65000,  hubs:['Kensington','Wavertree','Edge Hill','Toxteth','Kirkdale'] },
      Nottingham:   { min:36000,  max:65000,  hubs:['Lenton','Beeston','Radford','Forest Fields','Dunkirk'] },
      Sheffield:    { min:35000,  max:62000,  hubs:['Broomhill','Crookes','Ecclesall Road','Walkley','Hillsborough'] },
      Newcastle:    { min:36000,  max:65000,  hubs:['Jesmond','Heaton','Sandyford','Fenham','Arthurs Hill'] },
      Coventry:     { min:32000,  max:58000,  hubs:['Earlsdon','Canley','Tile Hill','Radford','Stivichall'] },
    },
  },
  'Germany': {
    tip: 'Register at your Studierendenwerk (student union) housing office the moment you receive your admission letter — waitlists are long.',
    cities: {
      Munich:     { min:72000,  max:126000, hubs:['Maxvorstadt','Schwabing','Neuhausen','Giesing','Au-Haidhausen'] },
      Berlin:     { min:45000,  max:81000,  hubs:['Mitte','Prenzlauer Berg','Friedrichshain','Kreuzberg','Neukölln'] },
      Hamburg:    { min:54000,  max:90000,  hubs:['Altona','Eimsbüttel','Winterhude','Barmbek','Harburg'] },
      Frankfurt:  { min:63000,  max:108000, hubs:['Sachsenhausen','Bockenheim','Nordend','Bornheim','Sachsenhausen Ost'] },
      Cologne:    { min:49000,  max:85000,  hubs:['Ehrenfeld','Nippes','Sülz','Lindenthal','Kalk'] },
      Heidelberg: { min:54000,  max:90000,  hubs:['Altstadt','Neuenheim','Handschuhsheim','Bergheim','Kirchheim'] },
      Stuttgart:  { min:63000,  max:108000, hubs:['Mitte','West','Vaihingen','Degerloch','Bad Cannstatt'] },
      Dusseldorf: { min:54000,  max:90000,  hubs:['Unterbilk','Oberbilk','Pempelfort','Flingern','Bilk'] },
    },
  },
  'Australia': {
    tip: 'Apply for university accommodation immediately on admission — some waitlists are 6+ months. UniLodge and Campus Living Villages are good PBSA options.',
    cities: {
      Sydney:     { min:49000,  max:88000,  hubs:['Newtown','Glebe','Chippendale','Ultimo','Randwick','Kensington'] },
      Melbourne:  { min:38000,  max:71000,  hubs:['Carlton','Fitzroy','Brunswick','Footscray','Clayton','Parkville'] },
      Brisbane:   { min:33000,  max:60000,  hubs:['St Lucia','Toowong','Kelvin Grove','South Bank','Woolloongabba'] },
      Perth:      { min:33000,  max:60000,  hubs:['Crawley','Nedlands','Subiaco','Fremantle','Mount Lawley'] },
      Adelaide:   { min:27000,  max:49000,  hubs:['North Adelaide','Glenelg','Prospect','Parkside','St Peters'] },
    },
  },
  'Canada': {
    tip: 'Use Kijiji (not Craigslist) for reliable Canadian room listings. Join your university\'s Facebook housing group as soon as you get admission.',
    cities: {
      Toronto:   { min:74000,  max:124000, hubs:['Annex','Kensington Market','Little Portugal','Scarborough','Mississauga'] },
      Vancouver: { min:86000,  max:136000, hubs:['Kitsilano','Commercial Drive','East Van','Burnaby','New Westminster'] },
      Montreal:  { min:55000,  max:90000,  hubs:['Plateau-Mont-Royal','Mile End','Rosemont','NDG','Côte-des-Neiges'] },
      Ottawa:    { min:62000,  max:99000,  hubs:['Sandy Hill','Centretown','Vanier','Glebe','Westboro'] },
      Calgary:   { min:62000,  max:99000,  hubs:['Beltline','Kensington','Inglewood','Capitol Hill','Sunnyside'] },
    },
  },
  'United States': {
    tip: 'Check your university\'s off-campus housing board — it\'s the safest option. Avoid Craigslist; use Apartments.com or Padmapper instead.',
    cities: {
      'New York':      { min:149000, max:290000, hubs:['Astoria (Queens)','Crown Heights','Washington Heights','Flushing','Bushwick'] },
      Boston:          { min:124000, max:232000, hubs:['Allston','Brighton','Somerville','Jamaica Plain','Roxbury'] },
      Chicago:         { min:74000,  max:132000, hubs:['Lincoln Park','Wicker Park','Hyde Park','Rogers Park','Pilsen'] },
      'Los Angeles':   { min:116000, max:207000, hubs:['Koreatown','Silver Lake','Westwood','Palms','Culver City'] },
      'San Francisco': { min:141000, max:249000, hubs:['Richmond','Sunset','Mission','Daly City','Oakland'] },
      Seattle:         { min:83000,  max:149000, hubs:['Capitol Hill','University District','Fremont','Beacon Hill','Georgetown'] },
      Austin:          { min:83000,  max:140000, hubs:['West Campus','Hyde Park','South Congress','Mueller','East Austin'] },
      Houston:         { min:62000,  max:110000, hubs:['Midtown','Montrose','Museum District','Third Ward','Heights'] },
      Atlanta:         { min:66000,  max:110000, hubs:['Midtown','Virginia Highland','Grant Park','East Atlanta','Reynoldstown'] },
    },
  },
  'Ireland': {
    tip: 'Dublin housing is severely scarce — start searching 4–5 months before your course. Daft.ie is essential; set up email alerts immediately.',
    cities: {
      Dublin:  { min:72000,  max:126000, hubs:['Rathmines','Ranelagh','Drumcondra','Stoneybatter','Phibsborough','Ringsend'] },
      Cork:    { min:45000,  max:81000,  hubs:['Sunday\'s Well','Douglas','Wilton','Bishopstown','Ballincollig'] },
      Galway:  { min:45000,  max:81000,  hubs:['Westside','Knocknacarra','Salthill','Shantalla','Renmore'] },
      Limerick:{ min:36000,  max:63000,  hubs:['City Centre','Castletroy','Raheen','Mungret','Dooradoyle'] },
    },
  },
  'Netherlands': {
    tip: 'Dutch housing is extremely competitive — apply to Kamernet and HousingAnywhere 3–6 months before arrival. Bring proof of enrollment to viewings.',
    cities: {
      Amsterdam:   { min:81000,  max:144000, hubs:['De Pijp','Jordaan','Oost','Oud-West','Noord'] },
      Rotterdam:   { min:54000,  max:90000,  hubs:['Kralingen','Hillegersberg','Centrum','Noord','Delfshaven'] },
      'The Hague': { min:63000,  max:99000,  hubs:['Centrum','Scheveningen','Ypenburg','Laak','Bezuidenhout'] },
      Eindhoven:   { min:49000,  max:81000,  hubs:['Centrum','Woensel','Stratum','Tongelre','Gestel'] },
      Utrecht:     { min:63000,  max:99000,  hubs:['Oost','Wijk C','Overvecht','Zuilen','Leidsche Rijn'] },
    },
  },
  'France': {
    tip: 'Apply to CROUS (official French student housing) the same day you accept your offer — places are cheap (₹18–35k/mo) but very limited.',
    cities: {
      Paris:     { min:63000,  max:117000, hubs:['Latin Quarter (5e)','Marais (4e)','Montparnasse (14e)','Belleville (20e)','Bastille (11e)'] },
      Lyon:      { min:36000,  max:63000,  hubs:['Presqu\'île','Croix-Rousse','Confluence','Villeurbanne','Part-Dieu'] },
      Marseille: { min:27000,  max:54000,  hubs:['Cours Julien','Noailles','La Plaine','Cinq Avenues','Belsunce'] },
      Bordeaux:  { min:36000,  max:63000,  hubs:['Saint-Michel','Chartrons','Victoire','Saint-Pierre','Meriadeck'] },
      Toulouse:  { min:32000,  max:58000,  hubs:['Capitole','Saint-Cyprien','Rangueil','Les Minimes','Compans-Caffarelli'] },
    },
  },
  'Spain': {
    tip: 'Apply to RESA (student residences) or your university\'s Colegio Mayor early. Badi and Spotahome are reliable for room searches from India.',
    cities: {
      Madrid:    { min:36000,  max:72000,  hubs:['Argüelles','Moncloa (near Complutense)','Cuatro Caminos','Lavapiés','Malasaña','Carabanchel'] },
      Barcelona: { min:40000,  max:81000,  hubs:['Gràcia','Poble Sec','Eixample','El Raval','Sant Martí','Horta-Guinardó'] },
      Valencia:  { min:27000,  max:54000,  hubs:['Ruzafa','Benimaclet','Cabanyal','El Carmen','Jesús','Campanar'] },
      Seville:   { min:27000,  max:54000,  hubs:['Triana','Alfalfa','La Macarena','Los Remedios','Nervión'] },
      Bilbao:    { min:32000,  max:58000,  hubs:['Casco Viejo','San Francisco','Basurto','Deusto','Rekalde'] },
    },
  },
  'Singapore': {
    tip: 'Apply for NUS/NTU/SMU on-campus housing immediately — it\'s subsidised (₹18–35k/mo) and fills up the moment allocation opens.',
    cities: {
      Singapore: { min:49000,  max:93000,  hubs:['Clementi (NUS area)','Jurong East (NTU area)','City Hall (SMU area)','Buona Vista','Queenstown','Boon Lay'] },
    },
  },
  'Japan': {
    tip: 'Look for "gaijin-friendly" or "foreigner-welcome" share houses. Many Japanese landlords require a Japanese guarantor — Sakura House and Borderless House waive this.',
    cities: {
      Tokyo:  { min:28000,  max:56000,  hubs:['Shinjuku','Shibuya','Ikebukuro','Koenji','Shimokitazawa','Nakameguro'] },
      Osaka:  { min:22000,  max:45000,  hubs:['Namba','Shinsaibashi','Umeda','Tennoji','Tanimachi'] },
      Kyoto:  { min:22000,  max:45000,  hubs:['Shimogyo','Fushimi','Sakyo (Kyoto Univ area)','Kita','Yamashina'] },
      Nagoya: { min:20000,  max:39000,  hubs:['Sakae','Fushimi','Kanayama','Ikaeshima','Chikusa'] },
      Fukuoka:{ min:18000,  max:35000,  hubs:['Hakata','Tenjin','Ohori','Nishijin','Momochi'] },
    },
  },
  'Sweden': {
    tip: 'Register at AF Bostäder (Lund) or SSSB (Stockholm) on day 1 of admission — waitlists are 1–2 years. Samtrygg is the best bet for short-term.',
    cities: {
      Stockholm:  { min:40000,  max:72000,  hubs:['Södermalm','Vasastan','Kungsholmen','Älvsjö','Hammarby'] },
      Gothenburg: { min:32000,  max:64000,  hubs:['Haga','Linné','Majorna','Gamlestaden','Guldheden'] },
      'Malmö':    { min:28000,  max:56000,  hubs:['Möllevången','Husie','Limhamn','Västra Hamnen','Husietorp'] },
      Uppsala:    { min:32000,  max:60000,  hubs:['Centrum','Fålhagen','Norby','Luthagen','Rickomberga'] },
    },
  },
  'Denmark': {
    tip: 'Contact Ungdomsboliger and KKIK (Copenhagen) immediately — subsidised student housing fills within hours of allocation.',
    cities: {
      Copenhagen: { min:60000,  max:108000, hubs:['Nørrebro','Vesterbro','Frederiksberg','Østerbro','Amager'] },
      Aarhus:     { min:48000,  max:84000,  hubs:['Trøjborg','Botanisk Have','Frederiksbjerg','Viby J','Skejby'] },
      Odense:     { min:36000,  max:60000,  hubs:['Odense C','Dalum','Tarup','Vollsmose','Bolbro'] },
    },
  },
  'UAE': {
    tip: 'Many UAE universities offer subsidised on-campus housing. International City and Al Nahda in Dubai are popular with Indian students for affordable rooms.',
    cities: {
      Dubai:       { min:44000,  max:110000, hubs:['International City','Al Nahda','Deira','Discovery Gardens','Al Quoz'] },
      'Abu Dhabi': { min:55000,  max:110000, hubs:['Khalidiyah','Muroor','Madinat Zayed','Al Reef','Khalifa City'] },
      Sharjah:     { min:27000,  max:55000,  hubs:['Al Majaz','Muweilah (near SHARJAH UNI)','Al Khan','Rolla','Industrial Area'] },
    },
  },
  'New Zealand': {
    tip: 'Auckland housing is in short supply. Search TradeMe and join your NZ university Facebook housing group the same day you get admission.',
    cities: {
      Auckland:     { min:35000,  max:65000,  hubs:['Mount Eden','Ponsonby','Grey Lynn','Newmarket','Kingsland','Sandringham'] },
      Wellington:   { min:35000,  max:65000,  hubs:['Kelburn','Newtown','Aro Valley','Te Aro','Karori','Thorndon'] },
      Christchurch: { min:25000,  max:50000,  hubs:['Riccarton','Ilam','Addington','Merivale','Spreydon'] },
    },
  },
  'South Korea': {
    tip: 'A goshiwon (고시원) is cheapest at ₹12–25k/mo but tiny. Gositel (고시텔) are slightly bigger. University dormitories fill fastest — apply the day you\'re admitted.',
    cities: {
      Seoul:   { min:24000,  max:49000,  hubs:['Hongdae (near Hongik)','Sinchon (near Yonsei)','Anam (Korea Univ)','Gwanak (SNU)','Mapo'] },
      Busan:   { min:18000,  max:37000,  hubs:['Haeundae','Seomyeon','Millak','Jangsanno','Dongbaek'] },
      Daejeon: { min:15000,  max:30000,  hubs:['Yuseong (KAIST area)','Dunsan','Junggu','Eunhaengdong','Banbuk'] },
      Incheon: { min:18000,  max:37000,  hubs:['Songdo (POSTECH area)','Guwol','Bupyeong','Namdong','Yeonsu'] },
    },
  },
  'Norway': {
    tip: 'SiO Bolig (Oslo) and SiT Bolig (Trondheim) are official student housing — affordable at ₹28–55k/mo but fill up fast. Apply on day 1.',
    cities: {
      Oslo:       { min:55000,  max:100000, hubs:['Grünerløkka','St. Hanshaugen','Sagene','Majorstuen','Bislett'] },
      Bergen:     { min:45000,  max:81000,  hubs:['Nygårdshøyden (UiB area)','Sentrum','Sandviken','Laksevåg','Landås'] },
      Trondheim:  { min:40000,  max:72000,  hubs:['Elgeseter','Lerkendal','Nedre Elvehavn','Ila','Øya (NTNU area)'] },
    },
  },
  'Italy': {
    tip: 'Apply to DiSU (Regional Authority for the Right to Study) for heavily subsidised student housing (₹9–22k/mo). Deadlines are usually in May for September intake.',
    cities: {
      Rome:     { min:36000,  max:72000,  hubs:['Pigneto','Testaccio','Trastevere','Prati','San Lorenzo','Garbatella'] },
      Milan:    { min:45000,  max:90000,  hubs:['Isola','Navigli','Porta Romana','Lambrate','Crescenzago','Città Studi'] },
      Bologna:  { min:36000,  max:65000,  hubs:['Bolognina','San Donato','Santo Stefano','Navile','Porto'] },
      Florence: { min:40000,  max:72000,  hubs:['Oltrarno','Campo di Marte','Rifredi','Cure','Sorgane'] },
      Turin:    { min:32000,  max:58000,  hubs:['Crocetta','Lingotto','San Salvario','Borgo Po','Pozzo Strada'] },
    },
  },
};

// ─────────────────────────────────────────────────────────────────────────────
const FX = { GBP:107, EUR:90, CAD:62, USD:83, AUD:55, JPY:0.56, SGD:62, AED:22, NZD:50, KRW:0.062, SEK:8, DKK:12, NOK:7 };

const BUDGET_TIERS = [
  { label:'Any budget',      max:null    },
  { label:'Under ₹60k/mo',  max:60000   },
  { label:'Under ₹1L/mo',   max:100000  },
  { label:'Under ₹1.5L/mo', max:150000  },
  { label:'Under ₹2.5L/mo', max:250000  },
];

const TYPE_STYLES = {
  rooms:      'bg-teal-50  text-teal-700  border-teal-200',
  apartments: 'bg-blue-50  text-blue-700  border-blue-200',
  student:    'bg-purple-50 text-purple-700 border-purple-200',
};

const fmtInr = (n) => n ? '₹' + Math.round(n).toLocaleString('en-IN') : '₹0';

// ─────────────────────────────────────────────────────────────────────────────
// COMPONENTS
// ─────────────────────────────────────────────────────────────────────────────
function SiteLogo({ domain, name, color = '#6B7280' }) {
  const [err, setErr] = useState(false);
  if (err || !domain) return (
    <div className="w-10 h-10 rounded-xl flex items-center justify-center text-white font-bold text-sm flex-shrink-0" style={{ backgroundColor: color }}>
      {name?.[0]?.toUpperCase() || '?'}
    </div>
  );
  return (
    <img src={`https://logo.clearbit.com/${domain}`} alt={name}
      className="w-10 h-10 rounded-xl object-contain bg-white border border-gray-100 p-1 flex-shrink-0"
      onError={() => setErr(true)} />
  );
}

function CountryInfoBar({ country, city }) {
  const info = COUNTRY_INFO[country.apiName];
  if (!info) return null;
  const cityData = info.cities?.[city];
  if (!cityData) return null;

  return (
    <div className="rounded-2xl border border-surfaceBorder bg-gradient-to-r from-surfaceAlt to-white p-4 space-y-3">
      {/* Price range */}
      <div className="flex flex-wrap items-center gap-4">
        <div className="flex items-center gap-2">
          <IndianRupee className="w-4 h-4 text-teal-500 flex-shrink-0" />
          <div>
            <p className="text-[10px] text-muted font-semibold uppercase tracking-wide">Avg monthly rent in {city}</p>
            <p className="font-black text-text text-base leading-none">
              {fmtInr(cityData.min)}
              <span className="text-muted font-normal text-sm"> – </span>
              {fmtInr(cityData.max)}
              <span className="text-muted font-normal text-xs"> /mo</span>
            </p>
          </div>
        </div>
        <div className="hidden sm:block w-px h-8 bg-surfaceBorder" />
        <div className="flex items-center gap-2 flex-1 min-w-0">
          <TrendingUp className="w-4 h-4 text-lavender flex-shrink-0" />
          <div className="min-w-0">
            <p className="text-[10px] text-muted font-semibold uppercase tracking-wide">Student neighbourhoods</p>
            <div className="flex flex-wrap gap-1 mt-0.5">
              {cityData.hubs.map(h => (
                <span key={h} className="text-[10px] font-semibold bg-lavendLight text-lavender border border-lavender/20 px-2 py-0.5 rounded-full whitespace-nowrap">
                  {h}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Tip */}
      {info.tip && (
        <div className="flex items-start gap-2 pt-2 border-t border-surfaceBorder">
          <Lightbulb className="w-3.5 h-3.5 text-amber-500 flex-shrink-0 mt-0.5" />
          <p className="text-xs text-muted leading-relaxed">{info.tip}</p>
        </div>
      )}
    </div>
  );
}

function PropertyCard({ prop }) {
  return (
    <div className="card overflow-hidden flex flex-col group hover:shadow-cardHov transition-shadow">
      <div className="h-44 relative overflow-hidden bg-surfaceAlt">
        {prop.image_url ? (
          <img src={prop.image_url} alt={prop.title}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
            onError={e => { e.target.style.display = 'none'; }} />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <Home className="w-10 h-10 text-muted/20" />
          </div>
        )}
        <div className="absolute top-2 left-2">
          <span className="text-[9px] font-bold bg-white/90 backdrop-blur text-teal-700 px-2 py-0.5 rounded-full shadow-sm">{prop.source}</span>
        </div>
        {prop.bills_inc && (
          <div className="absolute top-2 right-2">
            <span className="text-[9px] font-bold bg-teal-500 text-white px-2 py-0.5 rounded-full">Bills incl.</span>
          </div>
        )}
        <div className="absolute bottom-0 inset-x-0 bg-gradient-to-t from-black/70 to-transparent p-3 pt-8">
          <div className="flex items-end justify-between">
            <div>
              <p className="text-white/70 text-[10px]">Monthly rent</p>
              <p className="text-white font-black text-lg leading-none">{fmtInr(prop.price_inr)}</p>
            </div>
            <p className="text-white/60 text-xs font-medium">{prop.price_label}</p>
          </div>
        </div>
      </div>
      <div className="p-4 flex-1 flex flex-col">
        <h3 className="font-bold text-text text-sm line-clamp-2 group-hover:text-teal-600 transition-colors mb-2">{prop.title}</h3>
        <div className="flex items-center gap-1.5 text-xs text-muted mb-3">
          <MapPin className="w-3 h-3 text-teal-500 flex-shrink-0" />
          <span className="truncate">{prop.area || prop.country}</span>
        </div>
        <a href={prop.listing_url} target="_blank" rel="noopener noreferrer"
          className="mt-auto flex items-center justify-between pt-3 border-t border-surfaceBorder text-sm font-bold text-teal-600 hover:text-teal-700 transition-colors">
          <span>View listing</span>
          <ExternalLink className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
        </a>
      </div>
    </div>
  );
}

function PlatformCard({ platform }) {
  return (
    <div className="card p-4 flex flex-col gap-3 hover:shadow-cardHov transition-shadow">
      <div className="flex items-start gap-3">
        <SiteLogo domain={platform.logo_domain} name={platform.name} color={platform.logo_color} />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <h3 className="font-bold text-text text-sm">{platform.name}</h3>
            {platform.student_friendly && (
              <span className="inline-flex items-center gap-0.5 text-[9px] font-bold text-green-700 bg-green-50 border border-green-200 px-1.5 py-0.5 rounded-full">
                <GraduationCap className="w-2.5 h-2.5" />Student
              </span>
            )}
          </div>
          {platform.type && (
            <span className={`mt-1 inline-block text-[9px] font-semibold px-1.5 py-0.5 rounded-full border capitalize ${TYPE_STYLES[platform.type] || TYPE_STYLES.rooms}`}>
              {platform.type}
            </span>
          )}
        </div>
      </div>
      <p className="text-xs text-muted leading-relaxed flex-1">{platform.desc}</p>
      <a href={platform.url} target="_blank" rel="noopener noreferrer"
        className="flex items-center justify-between text-sm font-bold text-teal-600 hover:text-teal-700 pt-2 border-t border-surfaceBorder transition-colors group">
        <span>Open site</span>
        <ExternalLink className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
      </a>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// MAIN PAGE
// ─────────────────────────────────────────────────────────────────────────────
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
      const params = { country: country.apiName, city };
      const budget = BUDGET_TIERS[budgetIdx];
      if (budget.max) params.max_budget_inr = budget.max;
      const res = await housingAPI.getListings(params);
      setData(res);
    } catch {
      setError('Could not load housing data. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [country, city, budgetIdx]);

  useEffect(() => { fetchListings(); }, [country, city, budgetIdx]);

  const handleCountryChange = (c) => {
    setCountry(c);
    setCity(c.cities[0]);
    setData(null);
  };

  const listings       = data?.results || [];
  const platformGuides = data?.platform_guides || [];

  return (
    <div className="animate-fade-in space-y-5 pb-12">

      {/* Header */}
      <div className="page-header">
        <div className="page-icon bg-mintLight"><Home className="w-5 h-5 text-teal-600" /></div>
        <div>
          <h1 className="text-2xl font-bold text-text">Student Housing Hub</h1>
          <p className="text-muted text-sm mt-0.5">
            Live listings + exhaustive platform guides · Real avg rent data · All prices in ₹
          </p>
        </div>
      </div>

      {/* Country tabs */}
      <div className="flex gap-2 overflow-x-auto pb-1 scrollbar-hide snap-x">
        {COUNTRIES.map(c => (
          <button key={c.name} onClick={() => handleCountryChange(c)}
            className={`snap-start flex-shrink-0 flex flex-col items-center gap-1 px-3 py-2.5 rounded-xl border text-center transition-all
              ${country.name === c.name ? 'border-teal-400 bg-mintLight shadow-sm' : 'border-surfaceBorder bg-white hover:border-teal-300'}`}>
            <span className="text-2xl leading-none">{c.flag}</span>
            <span className={`text-[10px] font-semibold leading-none mt-0.5 whitespace-nowrap
              ${country.name === c.name ? 'text-teal-700' : 'text-textSoft'}`}>
              {c.name.split(' ')[0]}
            </span>
            {c.scraped
              ? <span className="text-[8px] font-bold text-teal-600 bg-teal-50 px-1.5 py-0.5 rounded-full border border-teal-200">LIVE</span>
              : <span className="text-[8px] font-medium text-muted bg-surfaceAlt px-1.5 py-0.5 rounded-full border border-surfaceBorder">GUIDE</span>
            }
          </button>
        ))}
      </div>

      {/* Country info bar — always shown */}
      <CountryInfoBar country={country} city={city} />

      {/* Filters */}
      <div className="card p-4 flex flex-wrap gap-4 items-end">
        {country.cities.length > 1 && (
          <div>
            <label className="text-xs font-semibold text-muted block mb-1.5">City</label>
            <select value={city} onChange={e => setCity(e.target.value)}
              className="input-field py-2 text-sm min-w-[160px]">
              {country.cities.map(c => <option key={c}>{c}</option>)}
            </select>
          </div>
        )}
        {country.scraped && (
          <div>
            <label className="text-xs font-semibold text-muted block mb-1.5">Max monthly rent</label>
            <div className="flex gap-1.5 flex-wrap">
              {BUDGET_TIERS.map((t, i) => (
                <button key={i} onClick={() => setBudgetIdx(i)}
                  className={`px-2.5 py-1.5 text-xs rounded-lg border font-semibold transition-all
                    ${budgetIdx === i ? 'bg-teal-500 text-white border-teal-500' : 'bg-white text-textSoft border-surfaceBorder hover:border-teal-400'}`}>
                  {t.label}
                </button>
              ))}
            </div>
          </div>
        )}
        {country.scraped && (
          <button onClick={fetchListings} disabled={loading}
            className="ml-auto flex items-center gap-1.5 px-4 py-2 rounded-xl border border-teal-300 text-teal-700 text-sm font-semibold hover:bg-mintLight transition-all disabled:opacity-50">
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        )}
      </div>

      {/* Loading */}
      {loading && (
        <div className="py-16 flex flex-col items-center gap-3 text-muted">
          <Loader2 className="w-8 h-8 text-teal-500 animate-spin" />
          <p className="text-sm font-medium">
            {country.scraped ? `Scraping live listings for ${city}…` : `Loading housing guide for ${country.name}…`}
          </p>
          <p className="text-xs">This may take 10–15 seconds for live listings</p>
        </div>
      )}

      {/* Error */}
      {error && !loading && (
        <div className="card p-4 border-rose-200 bg-rose-50 flex items-center gap-3 text-rose-600 text-sm">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />{error}
        </div>
      )}

      {!loading && (
        <>
          {/* ── Live listings ──────────────────────────────────────────── */}
          {listings.length > 0 && (
            <section className="space-y-4">
              <div className="flex items-center gap-3 flex-wrap">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-teal-400 rounded-full animate-pulse" />
                  <h2 className="font-bold text-text">Live Listings in {city}</h2>
                </div>
                <span className="text-xs font-bold bg-teal-100 text-teal-700 px-2.5 py-0.5 rounded-full">
                  {listings.length} found
                </span>
                <span className="text-xs text-muted ml-auto">
                  via <strong className="text-text">{data?.source}</strong> ·
                  1 {country.currency} ≈ ₹{FX[country.currency] ?? 83}
                </span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                {[...listings]
                  .sort((a, b) => (a.price_inr || 0) - (b.price_inr || 0))
                  .map(prop => <PropertyCard key={prop.id || prop.listing_url} prop={prop} />)}
              </div>
            </section>
          )}

          {/* ── Empty state for scraped countries ─────────────────────── */}
          {country.scraped && data && listings.length === 0 && !error && (
            <div className="card p-8 text-center border-dashed">
              <Search className="w-8 h-8 text-muted/40 mx-auto mb-3" />
              <p className="font-semibold text-text">No live listings found</p>
              <p className="text-sm text-muted mt-1">Try a higher budget or different city. Browse the platforms below.</p>
            </div>
          )}

          {/* ── Platform guide ─────────────────────────────────────────── */}
          {data && (
            <section className="space-y-4">
              <div className="flex items-center gap-3 flex-wrap">
                <Globe className="w-4 h-4 text-lavender" />
                <h2 className="font-bold text-text">
                  {country.scraped ? `More places to search in ${country.name}` : `Housing platforms for ${country.name}`}
                </h2>
                <span className="text-xs text-muted bg-surfaceAlt border border-surfaceBorder px-2 py-0.5 rounded-full">
                  {platformGuides.length} sites
                </span>
              </div>

              {!country.scraped && (
                <div className="rounded-xl bg-amber-50 border border-amber-200 px-4 py-3 text-sm text-amber-800 flex items-start gap-2">
                  <Info className="w-4 h-4 flex-shrink-0 mt-0.5" />
                  <span>
                    Live scraping isn't available for {country.name} yet. The platforms below are curated and verified — several let you book from India before your visa arrives.
                  </span>
                </div>
              )}

              {platformGuides.length > 0 ? (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                  {platformGuides.map(p => <PlatformCard key={p.name} platform={p} />)}
                </div>
              ) : (
                <div className="card p-6 text-center text-muted text-sm">
                  Platform guide not yet available for {country.name}.
                </div>
              )}

              {/* Budget reference */}
              <div className="rounded-xl bg-surfaceAlt border border-surfaceBorder px-4 py-3 text-xs text-muted flex items-start gap-2">
                <IndianRupee className="w-3.5 h-3.5 text-teal-500 flex-shrink-0 mt-0.5" />
                <span>
                  <strong className="text-text">Currency note:</strong>{' '}
                  1 {country.symbol} ({country.currency}) ≈ ₹{FX[country.currency] ?? '?'}. All rental figures above are converted using live-ish exchange rates (mid-2025).
                  Always verify current rates before budgeting.
                </span>
              </div>
            </section>
          )}
        </>
      )}
    </div>
  );
}
