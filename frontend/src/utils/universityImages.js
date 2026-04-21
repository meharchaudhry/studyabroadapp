/**
 * University image resolver
 * Priority: DB image_url → named mapping → country campus pool (deterministic hash)
 */

// Top universities → stable Unsplash photo IDs (beautiful campus shots)
const UNI_MAP = {
  // UK
  "University of Oxford":           "photo-1580981054867-c5726578e3f6",
  "University of Cambridge":         "photo-1541679486598-4dd17e6f8e75",
  "Imperial College London":         "photo-1562774053-701939374585",
  "University College London":       "photo-1509062522246-3755977927d7",
  "London School of Economics":      "photo-1486406146926-c627a92ad1ab",
  "University of Edinburgh":         "photo-1570537272621-f54f56a4b5e7",
  "University of Manchester":        "photo-1509587584298-0f3b3a3a1797",
  "King's College London":           "photo-1486325212027-8081e485255e",
  "University of Bristol":           "photo-1578916171728-46686eac8d58",
  "University of Warwick":           "photo-1562774053-701939374585",
  "Durham University":               "photo-1541679486598-4dd17e6f8e75",
  "University of Glasgow":           "photo-1543269865-cbf427effbad",
  "University of Birmingham":        "photo-1509587584298-0f3b3a3a1797",
  "University of Nottingham":        "photo-1562774053-701939374585",
  "University of Leeds":             "photo-1486406146926-c627a92ad1ab",
  "University of Sheffield":         "photo-1578916171728-46686eac8d58",
  "University of Southampton":       "photo-1562774053-701939374585",
  "University of Exeter":            "photo-1570537272621-f54f56a4b5e7",

  // USA
  "Massachusetts Institute of Technology": "photo-1579547621706-1a9c79d5c9f1",
  "Stanford University":             "photo-1541829070764-84a7d30dd3f3",
  "Harvard University":              "photo-1591123120675-6f7f1aae0e38",
  "California Institute of Technology": "photo-1541679486598-4dd17e6f8e75",
  "University of Chicago":           "photo-1566073771259-6a8506099945",
  "Columbia University":             "photo-1526958097901-5e6d742d3371",
  "Yale University":                 "photo-1509587584298-0f3b3a3a1797",
  "Princeton University":            "photo-1562774053-701939374585",
  "Cornell University":              "photo-1541829070764-84a7d30dd3f3",
  "University of Pennsylvania":      "photo-1571068316344-75bc76f77890",
  "Johns Hopkins University":        "photo-1486406146926-c627a92ad1ab",
  "University of California, Berkeley": "photo-1580981054867-c5726578e3f6",
  "University of California, Los Angeles": "photo-1541829070764-84a7d30dd3f3",
  "Duke University":                 "photo-1567168544646-208fa5d408fb",
  "Northwestern University":         "photo-1562774053-701939374585",
  "Carnegie Mellon University":      "photo-1541679486598-4dd17e6f8e75",
  "New York University":             "photo-1526958097901-5e6d742d3371",
  "University of Michigan":          "photo-1509587584298-0f3b3a3a1797",
  "University of Texas at Austin":   "photo-1571068316344-75bc76f77890",
  "Georgia Institute of Technology": "photo-1562774053-701939374585",

  // Canada
  "University of Toronto":           "photo-1569449047803-b17d4775421d",
  "McGill University":               "photo-1566073771259-6a8506099945",
  "University of British Columbia":  "photo-1541679486598-4dd17e6f8e75",
  "University of Waterloo":          "photo-1562774053-701939374585",
  "University of Alberta":           "photo-1509587584298-0f3b3a3a1797",
  "Western University":              "photo-1571068316344-75bc76f77890",
  "McMaster University":             "photo-1569449047803-b17d4775421d",
  "Queen's University":              "photo-1566073771259-6a8506099945",

  // Australia
  "Australian National University":  "photo-1556075798-4825dfaaf498",
  "University of Melbourne":         "photo-1531482615713-2afd69097998",
  "University of Sydney":            "photo-1545469729-b23c1c8440e0",
  "University of Queensland":        "photo-1556075798-4825dfaaf498",
  "Monash University":               "photo-1531482615713-2afd69097998",
  "University of New South Wales":   "photo-1545469729-b23c1c8440e0",
  "University of Western Australia": "photo-1556075798-4825dfaaf498",

  // Germany
  "Technical University of Munich":  "photo-1467269204594-9661b134dd2b",
  "LMU Munich":                      "photo-1467269204594-9661b134dd2b",
  "Heidelberg University":           "photo-1562774053-701939374585",
  "Humboldt University of Berlin":   "photo-1467269204594-9661b134dd2b",
  "Free University of Berlin":       "photo-1467269204594-9661b134dd2b",
  "RWTH Aachen University":          "photo-1541679486598-4dd17e6f8e75",
  "Karlsruhe Institute of Technology": "photo-1562774053-701939374585",

  // Netherlands
  "Delft University of Technology":  "photo-1578916171728-46686eac8d58",
  "University of Amsterdam":         "photo-1539037116277-4db20889f2d4",
  "Leiden University":               "photo-1539037116277-4db20889f2d4",
  "Eindhoven University of Technology": "photo-1578916171728-46686eac8d58",
  "Utrecht University":              "photo-1539037116277-4db20889f2d4",

  // Singapore
  "National University of Singapore": "photo-1525625293386-3f8f99389edd",
  "Nanyang Technological University": "photo-1525625293386-3f8f99389edd",

  // Japan
  "University of Tokyo":             "photo-1480796927426-f609979314bd",
  "Kyoto University":                "photo-1480796927426-f609979314bd",
  "Osaka University":                "photo-1480796927426-f609979314bd",
  "Tohoku University":               "photo-1480796927426-f609979314bd",

  // France
  "Paris Sciences et Lettres":       "photo-1499856871958-5b9627545d1a",
  "Sorbonne University":             "photo-1499856871958-5b9627545d1a",
  "École Polytechnique":             "photo-1499856871958-5b9627545d1a",

  // Sweden
  "KTH Royal Institute of Technology": "photo-1557804506-669a67965ba0",
  "Stockholm University":            "photo-1557804506-669a67965ba0",
  "Lund University":                 "photo-1557804506-669a67965ba0",
  "Uppsala University":              "photo-1557804506-669a67965ba0",

  // Ireland
  "Trinity College Dublin":          "photo-1562774053-701939374585",
  "University College Dublin":       "photo-1570537272621-f54f56a4b5e7",

  // New Zealand
  "University of Auckland":          "photo-1507699622108-4be3abd695ad",
  "University of Otago":             "photo-1507699622108-4be3abd695ad",
};

// Beautiful campus photos per country (Unsplash photo IDs)
const COUNTRY_PHOTOS = {
  "United Kingdom": ["photo-1580981054867-c5726578e3f6","photo-1541679486598-4dd17e6f8e75","photo-1509062522246-3755977927d7","photo-1486406146926-c627a92ad1ab","photo-1562774053-701939374585"],
  "United States":  ["photo-1579547621706-1a9c79d5c9f1","photo-1541829070764-84a7d30dd3f3","photo-1591123120675-6f7f1aae0e38","photo-1526958097901-5e6d742d3371","photo-1571068316344-75bc76f77890"],
  // Old aliases — kept for backwards compat
  "UK":          ["photo-1580981054867-c5726578e3f6","photo-1541679486598-4dd17e6f8e75","photo-1509062522246-3755977927d7","photo-1486406146926-c627a92ad1ab","photo-1562774053-701939374585"],
  "USA":         ["photo-1579547621706-1a9c79d5c9f1","photo-1541829070764-84a7d30dd3f3","photo-1591123120675-6f7f1aae0e38","photo-1526958097901-5e6d742d3371","photo-1571068316344-75bc76f77890"],
  "Canada":      ["photo-1569449047803-b17d4775421d","photo-1566073771259-6a8506099945","photo-1541679486598-4dd17e6f8e75","photo-1562774053-701939374585","photo-1509587584298-0f3b3a3a1797"],
  "Australia":   ["photo-1556075798-4825dfaaf498","photo-1531482615713-2afd69097998","photo-1545469729-b23c1c8440e0","photo-1516026672322-bc52d61a55d5","photo-1523050854058-8df90110c9f1"],
  "Germany":     ["photo-1467269204594-9661b134dd2b","photo-1562774053-701939374585","photo-1541679486598-4dd17e6f8e75","photo-1552664730-d307ca884978","photo-1497366754035-f200968a6e72"],
  "France":      ["photo-1499856871958-5b9627545d1a","photo-1502602898657-3e91760cbb34","photo-1431274172761-fca41d930114","photo-1471623817568-a21f601e0e06","photo-1559561853-08451507cbe7"],
  "Netherlands": ["photo-1539037116277-4db20889f2d4","photo-1578916171728-46686eac8d58","photo-1512470876302-972faa2aa9a4","photo-1558618666-fcd25c85cd64","photo-1445019980597-93fa8acb246c"],
  "Ireland":     ["photo-1562774053-701939374585","photo-1570537272621-f54f56a4b5e7","photo-1543165796-5426273eaab3","photo-1548681528-6f5f191058a2","photo-1505576391880-b3f9d713dc4f"],
  "Singapore":   ["photo-1525625293386-3f8f99389edd","photo-1558618047-3c8c76ca7d13","photo-1531804055935-76f44d7c3621","photo-1568786839-f5e27f59a44d","photo-1509316785289-025f5b846b35"],
  "Japan":       ["photo-1480796927426-f609979314bd","photo-1528360983277-13d401cdc186","photo-1540959733332-eab4deabeeaf","photo-1536098561742-ca998e48cbcc","photo-1503899036084-c55cdd92da26"],
  "Sweden":      ["photo-1557804506-669a67965ba0","photo-1529980308634-3dac97f8f4b3","photo-1508930784513-c6d4f90f63a1","photo-1508739773434-c26b3d09e071","photo-1494522855154-9297ac14b55f"],
  "Norway":      ["photo-1530841377377-3ff06c0ca713","photo-1558618047-3c8c76ca7d13","photo-1519681393784-d120267933ba","photo-1465056836041-7f43ac27dcb5","photo-1494522855154-9297ac14b55f"],
  "Denmark":     ["photo-1548346158-f90bdd51a9b5","photo-1531804055935-76f44d7c3621","photo-1529980308634-3dac97f8f4b3","photo-1508739773434-c26b3d09e071","photo-1507699622108-4be3abd695ad"],
  "Finland":     ["photo-1508739773434-c26b3d09e071","photo-1519681393784-d120267933ba","photo-1529980308634-3dac97f8f4b3","photo-1548346158-f90bdd51a9b5","photo-1557804506-669a67965ba0"],
  "UAE":         ["photo-1512453979798-5ea266f8880c","photo-1553913861-c0fddf2619ee","photo-1587974928442-77dc3e0dba72","photo-1544620347-c4fd4a3d5957","photo-1518684079-3c830dcef090"],
  "New Zealand": ["photo-1507699622108-4be3abd695ad","photo-1545469729-b23c1c8440e0","photo-1531482615713-2afd69097998","photo-1485463611174-f302f6a5c1c9","photo-1516026672322-bc52d61a55d5"],
  "default":     ["photo-1562774053-701939374585","photo-1541679486598-4dd17e6f8e75","photo-1509587584298-0f3b3a3a1797","photo-1571068316344-75bc76f77890","photo-1567168544646-208fa5d408fb"],
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
 * Returns a full Unsplash image URL for a university.
 * Width 800×480 for cards.
 */
export function getUniversityImage(uni) {
  if (uni.image_url) return uni.image_url;

  const photoId = UNI_MAP[uni.name];
  if (photoId) {
    return `https://images.unsplash.com/${photoId}?auto=format&fit=crop&w=800&h=480&q=80`;
  }

  const pool = COUNTRY_PHOTOS[uni.country] || COUNTRY_PHOTOS["default"];
  const idx = hashCode(uni.name || "") % pool.length;
  return `https://images.unsplash.com/${pool[idx]}?auto=format&fit=crop&w=800&h=480&q=80`;
}

export function getCountryFlag(country) {
  const flags = {
    // Full names (canonical — matches DB)
    "United Kingdom": "🇬🇧", "United States": "🇺🇸", "Canada": "🇨🇦",
    "Australia": "🇦🇺", "Germany": "🇩🇪", "France": "🇫🇷",
    "Netherlands": "🇳🇱", "Ireland": "🇮🇪", "New Zealand": "🇳🇿",
    "Singapore": "🇸🇬", "Japan": "🇯🇵", "Sweden": "🇸🇪",
    "Norway": "🇳🇴", "Denmark": "🇩🇰", "Finland": "🇫🇮", "UAE": "🇦🇪",
    "Italy": "🇮🇹", "Spain": "🇪🇸", "South Korea": "🇰🇷", "China": "🇨🇳",
    "Hong Kong": "🇭🇰", "Switzerland": "🇨🇭", "Belgium": "🇧🇪",
    "Portugal": "🇵🇹",
    // Short aliases for backwards compat
    "UK": "🇬🇧", "USA": "🇺🇸",
  };
  return flags[country] || "🌍";
}
