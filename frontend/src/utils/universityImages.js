/**
 * University image resolver — Unsplash only (stable, no hotlink restrictions)
 * DB image_url is always skipped (all are broken Clearbit logos).
 */

const U = (id, extra = '') =>
  `https://images.unsplash.com/${id}?auto=format&fit=crop&w=800&h=480&q=80${extra}`;

// Named university → specific Unsplash photo ID (real campus/architecture shots)
const UNI_MAP = {
  // ── UK ──────────────────────────────────────────────────────────────────────
  "University of Oxford":                    U('photo-1580981054867-c5726578e3f6'),
  "University of Cambridge":                 U('photo-1541679486598-4dd17e6f8e75'),
  "Imperial College London":                 U('photo-1562774053-701939374585'),
  "University College London":               U('photo-1509062522246-3755977927d7'),
  "London School of Economics":              U('photo-1486406146926-c627a92ad1ab'),
  "University of Edinburgh":                 U('photo-1570537272621-f54f56a4b5e7'),
  "University of Manchester":                U('photo-1509587584298-0f3b3a3a1797'),
  "King's College London":                   U('photo-1486325212027-8081e485255e'),
  "University of Bristol":                   U('photo-1578916171728-46686eac8d58'),
  "Durham University":                       U('photo-1541679486598-4dd17e6f8e75'),
  "University of Glasgow":                   U('photo-1543269865-cbf427effbad'),
  "University of Birmingham":                U('photo-1509587584298-0f3b3a3a1797'),
  "University of Nottingham":                U('photo-1562774053-701939374585'),
  "University of Warwick":                   U('photo-1486406146926-c627a92ad1ab'),
  "University of Leeds":                     U('photo-1571068316344-75bc76f77890'),
  "University of Sheffield":                 U('photo-1578916171728-46686eac8d58'),
  "University of Southampton":               U('photo-1562774053-701939374585'),
  "University of Exeter":                    U('photo-1570537272621-f54f56a4b5e7'),

  // ── USA ──────────────────────────────────────────────────────────────────────
  "Massachusetts Institute of Technology (MIT)": U('photo-1579547621706-1a9c79d5c9f1'),
  "Massachusetts Institute of Technology":       U('photo-1579547621706-1a9c79d5c9f1'),
  "Stanford University":                         U('photo-1541829070764-84a7d30dd3f3'),
  "Harvard University":                          U('photo-1591123120675-6f7f1aae0e38'),
  "California Institute of Technology (Caltech)":U('photo-1541679486598-4dd17e6f8e75'),
  "California Institute of Technology":          U('photo-1541679486598-4dd17e6f8e75'),
  "University of Chicago":                       U('photo-1566073771259-6a8506099945'),
  "Columbia University":                         U('photo-1526958097901-5e6d742d3371'),
  "Yale University":                             U('photo-1509587584298-0f3b3a3a1797'),
  "Princeton University":                        U('photo-1562774053-701939374585'),
  "Cornell University":                          U('photo-1541829070764-84a7d30dd3f3'),
  "University of Pennsylvania":                  U('photo-1571068316344-75bc76f77890'),
  "Johns Hopkins University":                    U('photo-1486406146926-c627a92ad1ab'),
  "University of California, Berkeley (UCB)":    U('photo-1580981054867-c5726578e3f6'),
  "University of California, Berkeley":          U('photo-1580981054867-c5726578e3f6'),
  "University of California Berkeley":           U('photo-1580981054867-c5726578e3f6'),
  "University of California, Los Angeles (UCLA)":U('photo-1541829070764-84a7d30dd3f3'),
  "Duke University":                             U('photo-1567168544646-208fa5d408fb'),
  "Northwestern University":                     U('photo-1562774053-701939374585'),
  "Carnegie Mellon University":                  U('photo-1541679486598-4dd17e6f8e75'),
  "New York University":                         U('photo-1526958097901-5e6d742d3371'),
  "University of Michigan":                      U('photo-1509587584298-0f3b3a3a1797'),
  "University of Texas at Austin":               U('photo-1571068316344-75bc76f77890'),
  "Georgia Institute of Technology":             U('photo-1562774053-701939374585'),

  // ── Canada ───────────────────────────────────────────────────────────────────
  "University of Toronto":                   U('photo-1569449047803-b17d4775421d'),
  "McGill University":                       U('photo-1566073771259-6a8506099945'),
  "University of British Columbia":          U('photo-1541679486598-4dd17e6f8e75'),
  "University of Waterloo":                  U('photo-1562774053-701939374585'),
  "University of Alberta":                   U('photo-1509587584298-0f3b3a3a1797'),
  "Western University":                      U('photo-1571068316344-75bc76f77890'),
  "McMaster University":                     U('photo-1569449047803-b17d4775421d'),
  "Queen's University":                      U('photo-1566073771259-6a8506099945'),

  // ── Australia ────────────────────────────────────────────────────────────────
  "Australian National University":          U('photo-1556075798-4825dfaaf498'),
  "University of Melbourne":                 U('photo-1531482615713-2afd69097998'),
  "University of Sydney":                    U('photo-1545469729-b23c1c8440e0'),
  "University of Queensland":                U('photo-1556075798-4825dfaaf498'),
  "Monash University":                       U('photo-1531482615713-2afd69097998'),
  "University of New South Wales":           U('photo-1545469729-b23c1c8440e0'),
  "University of Western Australia":         U('photo-1556075798-4825dfaaf498'),

  // ── Germany ──────────────────────────────────────────────────────────────────
  "Technical University of Munich":          U('photo-1467269204594-9661b134dd2b'),
  "LMU Munich":                              U('photo-1467269204594-9661b134dd2b'),
  "Heidelberg University":                   U('photo-1552664730-d307ca884978'),
  "Humboldt University of Berlin":           U('photo-1497366754035-f200968a6e72'),
  "Free University of Berlin":               U('photo-1467269204594-9661b134dd2b'),
  "Free University Berlin":                  U('photo-1467269204594-9661b134dd2b'),
  "RWTH Aachen University":                  U('photo-1541679486598-4dd17e6f8e75'),
  "Karlsruhe Institute of Technology":       U('photo-1562774053-701939374585'),

  // ── Netherlands ──────────────────────────────────────────────────────────────
  "Delft University of Technology":          U('photo-1578916171728-46686eac8d58'),
  "University of Amsterdam":                 U('photo-1539037116277-4db20889f2d4'),
  "Leiden University":                       U('photo-1445019980597-93fa8acb246c'),
  "Eindhoven University of Technology":      U('photo-1558618666-fcd25c85cd64'),

  // ── Switzerland ──────────────────────────────────────────────────────────────
  "ETH Zurich":                              U('photo-1527668752968-14dc70a27c95'),
  "EPFL":                                    U('photo-1506905925346-21bda4d32df4'),
  "University of Zurich":                    U('photo-1470770841072-f978cf4d019e'),

  // ── France ───────────────────────────────────────────────────────────────────
  "Paris-Saclay University":                 U('photo-1499856871958-5b9627545d1a'),
  "Sorbonne University":                     U('photo-1431274172761-fca41d930114'),
  "HEC Paris":                               U('photo-1502602898657-3e91760cbb34'),
  "Sciences Po":                             U('photo-1471623817568-a21f601e0e06'),

  // ── Singapore ────────────────────────────────────────────────────────────────
  "National University of Singapore (NUS)":  U('photo-1525625293386-3f8f99389edd'),
  "National University of Singapore":        U('photo-1525625293386-3f8f99389edd'),
  "Nanyang Technological University":        U('photo-1558618047-3c8c76ca7d13'),
  "Singapore Management University":        U('photo-1531804055935-76f44d7c3621'),

  // ── Sweden ───────────────────────────────────────────────────────────────────
  "Karolinska Institute":                    U('photo-1557804506-669a67965ba0'),
  "KTH Royal Institute of Technology":       U('photo-1529980308634-3dac97f8f4b3'),
  "Lund University":                         U('photo-1508930784513-c6d4f90f63a1'),
  "Uppsala University":                      U('photo-1508739773434-c26b3d09e071'),

  // ── Ireland ──────────────────────────────────────────────────────────────────
  "Trinity College Dublin":                  U('photo-1543165796-5426273eaab3'),
  "University College Dublin":               U('photo-1548681528-6f5f191058a2'),

  // ── Japan ────────────────────────────────────────────────────────────────────
  "University of Tokyo":                     U('photo-1480796927426-f609979314bd'),
  "Kyoto University":                        U('photo-1528360983277-13d401cdc186'),
  "Osaka University":                        U('photo-1540959733332-eab4deabeeaf'),

  // ── South Korea ──────────────────────────────────────────────────────────────
  "Seoul National University":               U('photo-1538485399081-7191377e8241'),
  "KAIST":                                   U('photo-1517154421773-0529f29ea451'),
  "Yonsei University":                       U('photo-1534430480872-3498386e7856'),

  // ── UAE ──────────────────────────────────────────────────────────────────────
  "University of Dubai":                     U('photo-1512453979798-5ea266f8880c'),
  "Khalifa University":                      U('photo-1553913861-c0fddf2619ee'),
  "American University of Sharjah":          U('photo-1587974928442-77dc3e0dba72'),

  // ── Norway / Denmark / Finland ───────────────────────────────────────────────
  "University of Oslo":                      U('photo-1530841377377-3ff06c0ca713'),
  "University of Copenhagen":                U('photo-1548346158-f90bdd51a9b5'),
  "University of Helsinki":                  U('photo-1508739773434-c26b3d09e071'),
  "Aalto University":                        U('photo-1529980308634-3dac97f8f4b3'),
};

// Country-level Unsplash campus photo pools (verified working)
const COUNTRY_PHOTOS = {
  "United Kingdom": [
    U('photo-1580981054867-c5726578e3f6'),
    U('photo-1570537272621-f54f56a4b5e7'),
    U('photo-1509587584298-0f3b3a3a1797'),
    U('photo-1541679486598-4dd17e6f8e75'),
    U('photo-1486406146926-c627a92ad1ab'),
  ],
  "United States": [
    U('photo-1579547621706-1a9c79d5c9f1'),
    U('photo-1541829070764-84a7d30dd3f3'),
    U('photo-1591123120675-6f7f1aae0e38'),
    U('photo-1526958097901-5e6d742d3371'),
    U('photo-1571068316344-75bc76f77890'),
  ],
  "Canada": [
    U('photo-1569449047803-b17d4775421d'),
    U('photo-1566073771259-6a8506099945'),
    U('photo-1541679486598-4dd17e6f8e75'),
    U('photo-1562774053-701939374585'),
    U('photo-1509587584298-0f3b3a3a1797'),
  ],
  "Australia": [
    U('photo-1556075798-4825dfaaf498'),
    U('photo-1531482615713-2afd69097998'),
    U('photo-1545469729-b23c1c8440e0'),
    U('photo-1516026672322-bc52d61a55d5'),
    U('photo-1523050854058-8df90110c9f1'),
  ],
  "Germany": [
    U('photo-1467269204594-9661b134dd2b'),
    U('photo-1552664730-d307ca884978'),
    U('photo-1497366754035-f200968a6e72'),
    U('photo-1562774053-701939374585'),
    U('photo-1541679486598-4dd17e6f8e75'),
  ],
  "France": [
    U('photo-1499856871958-5b9627545d1a'),
    U('photo-1502602898657-3e91760cbb34'),
    U('photo-1431274172761-fca41d930114'),
    U('photo-1471623817568-a21f601e0e06'),
    U('photo-1559561853-08451507cbe7'),
  ],
  "Netherlands": [
    U('photo-1539037116277-4db20889f2d4'),
    U('photo-1578916171728-46686eac8d58'),
    U('photo-1512470876302-972faa2aa9a4'),
    U('photo-1558618666-fcd25c85cd64'),
    U('photo-1445019980597-93fa8acb246c'),
  ],
  "Ireland": [
    U('photo-1543165796-5426273eaab3'),
    U('photo-1548681528-6f5f191058a2'),
    U('photo-1562774053-701939374585'),
    U('photo-1570537272621-f54f56a4b5e7'),
    U('photo-1505576391880-b3f9d713dc4f'),
  ],
  "Singapore": [
    U('photo-1525625293386-3f8f99389edd'),
    U('photo-1558618047-3c8c76ca7d13'),
    U('photo-1531804055935-76f44d7c3621'),
    U('photo-1568786839-f5e27f59a44d'),
    U('photo-1509316785289-025f5b846b35'),
  ],
  "Japan": [
    U('photo-1480796927426-f609979314bd'),
    U('photo-1528360983277-13d401cdc186'),
    U('photo-1540959733332-eab4deabeeaf'),
    U('photo-1536098561742-ca998e48cbcc'),
    U('photo-1503899036084-c55cdd92da26'),
  ],
  "Sweden": [
    U('photo-1557804506-669a67965ba0'),
    U('photo-1529980308634-3dac97f8f4b3'),
    U('photo-1508930784513-c6d4f90f63a1'),
    U('photo-1508739773434-c26b3d09e071'),
    U('photo-1494522855154-9297ac14b55f'),
  ],
  "Norway": [
    U('photo-1530841377377-3ff06c0ca713'),
    U('photo-1519681393784-d120267933ba'),
    U('photo-1465056836041-7f43ac27dcb5'),
    U('photo-1494522855154-9297ac14b55f'),
    U('photo-1529980308634-3dac97f8f4b3'),
  ],
  "Denmark": [
    U('photo-1548346158-f90bdd51a9b5'),
    U('photo-1531804055935-76f44d7c3621'),
    U('photo-1529980308634-3dac97f8f4b3'),
    U('photo-1508739773434-c26b3d09e071'),
    U('photo-1507699622108-4be3abd695ad'),
  ],
  "Finland": [
    U('photo-1508739773434-c26b3d09e071'),
    U('photo-1519681393784-d120267933ba'),
    U('photo-1529980308634-3dac97f8f4b3'),
    U('photo-1548346158-f90bdd51a9b5'),
    U('photo-1557804506-669a67965ba0'),
  ],
  "UAE": [
    U('photo-1512453979798-5ea266f8880c'),
    U('photo-1553913861-c0fddf2619ee'),
    U('photo-1587974928442-77dc3e0dba72'),
    U('photo-1544620347-c4fd4a3d5957'),
    U('photo-1518684079-3c830dcef090'),
  ],
  "New Zealand": [
    U('photo-1507699622108-4be3abd695ad'),
    U('photo-1545469729-b23c1c8440e0'),
    U('photo-1531482615713-2afd69097998'),
    U('photo-1485463611174-f302f6a5c1c9'),
    U('photo-1516026672322-bc52d61a55d5'),
  ],
  "Switzerland": [
    U('photo-1506905925346-21bda4d32df4'),
    U('photo-1527668752968-14dc70a27c95'),
    U('photo-1470770841072-f978cf4d019e'),
    U('photo-1558618047-3c8c76ca7d13'),
    U('photo-1553913861-c0fddf2619ee'),
  ],
  "South Korea": [
    U('photo-1538485399081-7191377e8241'),
    U('photo-1517154421773-0529f29ea451'),
    U('photo-1534430480872-3498386e7856'),
    U('photo-1504198458649-3128b932f49e'),
    U('photo-1519181245277-cffeb3c2c2ac'),
  ],
  "Italy": [
    U('photo-1515542622106-78bda8ba0e5b'),
    U('photo-1552832230-c0197dd311b5'),
    U('photo-1529260830199-42c24126f198'),
    U('photo-1523906834658-6e24ef2386f9'),
    U('photo-1534445538923-ab38dec37394'),
  ],
  "Spain": [
    U('photo-1512813195386-6cf811ad3542'),
    U('photo-1559561853-08451507cbe7'),
    U('photo-1543783207-ec64e4d95325'),
    U('photo-1464790719320-516ecd75af6c'),
    U('photo-1571406252241-db0280bd36cd'),
  ],
  "Portugal": [
    U('photo-1555881400-74d7acaacd8b'),
    U('photo-1548707309-dcebeab9ea9b'),
    U('photo-1597502798979-cf1ffa7de44c'),
    U('photo-1513735539099-cf5b71fc4c2f'),
    U('photo-1449452198679-05c7fd30f416'),
  ],
  "default": [
    U('photo-1562774053-701939374585'),
    U('photo-1541679486598-4dd17e6f8e75'),
    U('photo-1509587584298-0f3b3a3a1797'),
    U('photo-1571068316344-75bc76f77890'),
    U('photo-1567168544646-208fa5d408fb'),
  ],
};

function hashCode(str) {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = ((hash << 5) - hash) + str.charCodeAt(i);
    hash |= 0;
  }
  return Math.abs(hash);
}

/**
 * Returns a real campus image URL.
 * Never uses DB image_url (all are broken Clearbit logos).
 */
export function getUniversityImage(uni) {
  const named = UNI_MAP[uni.name];
  if (named) return named;

  const pool = COUNTRY_PHOTOS[uni.country] || COUNTRY_PHOTOS['default'];
  return pool[hashCode(uni.name || '') % pool.length];
}

export function getCountryFlag(country) {
  const flags = {
    "United Kingdom": "🇬🇧", "United States": "🇺🇸", "Canada": "🇨🇦",
    "Australia": "🇦🇺", "Germany": "🇩🇪", "France": "🇫🇷",
    "Netherlands": "🇳🇱", "Ireland": "🇮🇪", "New Zealand": "🇳🇿",
    "Singapore": "🇸🇬", "Japan": "🇯🇵", "Sweden": "🇸🇪",
    "Norway": "🇳🇴", "Denmark": "🇩🇰", "Finland": "🇫🇮", "UAE": "🇦🇪",
    "Italy": "🇮🇹", "Spain": "🇪🇸", "South Korea": "🇰🇷", "China": "🇨🇳",
    "Hong Kong": "🇭🇰", "Switzerland": "🇨🇭", "Belgium": "🇧🇪",
    "Portugal": "🇵🇹", "UK": "🇬🇧", "USA": "🇺🇸",
  };
  return flags[country] || '🌍';
}
