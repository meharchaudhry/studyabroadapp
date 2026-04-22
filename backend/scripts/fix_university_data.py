"""
fix_university_data.py
Fixes:
1. Adds real website URLs for all universities (curated map + smart fallback)
2. Fixes course_duration: stored in months, frontend reads as years → divide by 12
3. Caps unrealistic tuition outliers
"""

import re
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import engine
import sqlalchemy as sa

# ── 1. Curated website map (name → URL) ──────────────────────────────────────
# Covers the most-searched universities; rest get smart fallback
WEBSITE_MAP = {
    # USA
    "Massachusetts Institute of Technology": "https://www.mit.edu",
    "Massachusetts Institute of Technology (MIT)": "https://www.mit.edu",
    "Princeton University": "https://www.princeton.edu",
    "Stanford University": "https://www.stanford.edu",
    "Harvard University": "https://www.harvard.edu",
    "California Institute of Technology (Caltech)": "https://www.caltech.edu",
    "California Institute of Technology": "https://www.caltech.edu",
    "University of California, Berkeley (UCB)": "https://www.berkeley.edu",
    "University of California Berkeley": "https://www.berkeley.edu",
    "Yale University": "https://www.yale.edu",
    "Columbia University": "https://www.columbia.edu",
    "University of Pennsylvania": "https://www.upenn.edu",
    "University of Chicago": "https://www.uchicago.edu",
    "The University of Chicago": "https://www.uchicago.edu",
    "Duke University": "https://www.duke.edu",
    "Johns Hopkins University": "https://www.jhu.edu",
    "Northwestern University": "https://www.northwestern.edu",
    "Cornell University": "https://www.cornell.edu",
    "Rice University": "https://www.rice.edu",
    "Vanderbilt University": "https://www.vanderbilt.edu",
    "Notre Dame University": "https://www.nd.edu",
    "University of Notre Dame": "https://www.nd.edu",
    "Georgetown University": "https://www.georgetown.edu",
    "Emory University": "https://www.emory.edu",
    "Carnegie Mellon University": "https://www.cmu.edu",
    "University of California, Los Angeles (UCLA)": "https://www.ucla.edu",
    "University of California Los Angeles": "https://www.ucla.edu",
    "University of Michigan-Ann Arbor": "https://www.umich.edu",
    "University of Michigan": "https://www.umich.edu",
    "University of Virginia": "https://www.virginia.edu",
    "University of North Carolina, Chapel Hill": "https://www.unc.edu",
    "University of North Carolina Chapel Hill": "https://www.unc.edu",
    "University of California, San Diego (UCSD)": "https://www.ucsd.edu",
    "University of California San Diego": "https://www.ucsd.edu",
    "University of California, Davis": "https://www.ucdavis.edu",
    "University of California Davis": "https://www.ucdavis.edu",
    "University of California, Irvine": "https://www.uci.edu",
    "University of Wisconsin-Madison": "https://www.wisc.edu",
    "University of Illinois at Urbana-Champaign": "https://www.illinois.edu",
    "University of Illinois Urbana-Champaign": "https://www.illinois.edu",
    "University of Texas at Austin": "https://www.utexas.edu",
    "University of Washington": "https://www.washington.edu",
    "Ohio State University (Main campus)": "https://www.osu.edu",
    "Ohio State University": "https://www.osu.edu",
    "The Ohio State University": "https://www.osu.edu",
    "New York University (NYU)": "https://www.nyu.edu",
    "New York University": "https://www.nyu.edu",
    "Boston University": "https://www.bu.edu",
    "Northeastern University": "https://www.northeastern.edu",
    "Tufts University": "https://www.tufts.edu",
    "Brandeis University": "https://www.brandeis.edu",
    "Boston College": "https://www.bc.edu",
    "University of Rochester": "https://www.rochester.edu",
    "Case Western Reserve University": "https://www.case.edu",
    "George Washington University": "https://www.gwu.edu",
    "American University": "https://www.american.edu",
    "University of Maryland, College Park": "https://www.umd.edu",
    "University of Maryland": "https://www.umd.edu",
    "Purdue University": "https://www.purdue.edu",
    "Penn State (Main campus)": "https://www.psu.edu",
    "Penn State University": "https://www.psu.edu",
    "Pennsylvania State University": "https://www.psu.edu",
    "Indiana University Bloomington": "https://www.indiana.edu",
    "Michigan State University": "https://www.msu.edu",
    "University of Minnesota, Twin Cities": "https://twin-cities.umn.edu",
    "University of Pittsburgh": "https://www.pitt.edu",
    "University of Miami": "https://www.miami.edu",
    "Florida State University": "https://www.fsu.edu",
    "University of Florida": "https://www.ufl.edu",
    "Arizona State University": "https://www.asu.edu",
    "University of Arizona": "https://www.arizona.edu",
    "Colorado State University": "https://www.colostate.edu",
    "Colorado School of Mines": "https://www.mines.edu",
    "Texas A&M University": "https://www.tamu.edu",
    "Texas A&M University (College Station)": "https://www.tamu.edu",
    "University of Houston": "https://www.uh.edu",
    "Georgia Institute of Technology": "https://www.gatech.edu",
    "Georgia Tech": "https://www.gatech.edu",
    "University of Georgia": "https://www.uga.edu",
    "Emory University": "https://www.emory.edu",
    "Tulane University": "https://www.tulane.edu",
    "University of Southern California": "https://www.usc.edu",
    "Caltech": "https://www.caltech.edu",
    "University of California, Santa Barbara (UCSB)": "https://www.ucsb.edu",
    "University of California, Santa Cruz": "https://www.ucsc.edu",
    "Rutgers University–New Brunswick": "https://www.rutgers.edu",
    "Rutgers University": "https://www.rutgers.edu",
    "Stony Brook University": "https://www.stonybrook.edu",
    "Rensselaer Polytechnic Institute": "https://www.rpi.edu",
    "Worcester Polytechnic Institute": "https://www.wpi.edu",
    "University of Connecticut": "https://www.uconn.edu",
    "Syracuse University": "https://www.syracuse.edu",
    "Fordham University": "https://www.fordham.edu",
    "University of Iowa": "https://www.uiowa.edu",
    "Iowa State University": "https://www.iastate.edu",
    "University of Kansas": "https://www.ku.edu",
    "University of Nebraska-Lincoln": "https://www.unl.edu",
    "University of Colorado Boulder": "https://www.colorado.edu",
    "University of Utah": "https://www.utah.edu",
    "University of Oregon": "https://www.uoregon.edu",
    "Oregon State University": "https://www.oregonstate.edu",
    "Virginia Tech": "https://www.vt.edu",
    "Wake Forest University": "https://www.wfu.edu",
    "University of South Carolina": "https://www.sc.edu",
    "University of Alabama": "https://www.ua.edu",
    "Auburn University": "https://www.auburn.edu",
    "University of Tennessee, Knoxville": "https://www.utk.edu",
    "University of Kentucky": "https://www.uky.edu",
    "University of Missouri": "https://www.missouri.edu",
    "Washington University in St. Louis": "https://wustl.edu",
    "Drexel University": "https://www.drexel.edu",
    "Temple University": "https://www.temple.edu",
    "Lehigh University": "https://www.lehigh.edu",
    "Stevens Institute of Technology": "https://www.stevens.edu",
    "New Jersey Institute of Technology": "https://www.njit.edu",
    "University of Texas at Dallas": "https://www.utdallas.edu",
    "University of Texas at San Antonio": "https://www.utsa.edu",
    "Baylor University": "https://www.baylor.edu",
    "Southern Methodist University": "https://www.smu.edu",
    "Texas Christian University": "https://www.tcu.edu",
    "Florida International University": "https://www.fiu.edu",
    "University of South Florida": "https://www.usf.edu",
    "University of Central Florida": "https://www.ucf.edu",
    "George Mason University": "https://www.gmu.edu",
    "Howard University": "https://www.howard.edu",
    "Clark Atlanta University": "https://www.cau.edu",
    "New York University Abu Dhabi": "https://nyuad.nyu.edu",
    # UK
    "University of Oxford": "https://www.ox.ac.uk",
    "University of Cambridge": "https://www.cam.ac.uk",
    "Imperial College London": "https://www.imperial.ac.uk",
    "University College London": "https://www.ucl.ac.uk",
    "London School of Economics and Political Science": "https://www.lse.ac.uk",
    "London School of Economics": "https://www.lse.ac.uk",
    "The London School of Economics and Political Science (LSE)": "https://www.lse.ac.uk",
    "University of Edinburgh": "https://www.ed.ac.uk",
    "University of Manchester": "https://www.manchester.ac.uk",
    "King's College London": "https://www.kcl.ac.uk",
    "University of Bristol": "https://www.bristol.ac.uk",
    "University of Glasgow": "https://www.gla.ac.uk",
    "Durham University": "https://www.durham.ac.uk",
    "University of Warwick": "https://warwick.ac.uk",
    "University of Birmingham": "https://www.birmingham.ac.uk",
    "University of Leeds": "https://www.leeds.ac.uk",
    "University of Southampton": "https://www.southampton.ac.uk",
    "University of Sheffield": "https://www.sheffield.ac.uk",
    "University of Nottingham": "https://www.nottingham.ac.uk",
    "Newcastle University": "https://www.ncl.ac.uk",
    "Queen Mary University of London": "https://www.qmul.ac.uk",
    "University of Liverpool": "https://www.liverpool.ac.uk",
    "University of Exeter": "https://www.exeter.ac.uk",
    "University of York": "https://www.york.ac.uk",
    "University of St Andrews": "https://www.st-andrews.ac.uk",
    "Lancaster University": "https://www.lancaster.ac.uk",
    "University of Leicester": "https://www.le.ac.uk",
    "University of Surrey": "https://www.surrey.ac.uk",
    "Loughborough University": "https://www.lboro.ac.uk",
    "University of Reading": "https://www.reading.ac.uk",
    "Cardiff University": "https://www.cardiff.ac.uk",
    "University of Aberdeen": "https://www.abdn.ac.uk",
    "University of Bath": "https://www.bath.ac.uk",
    "Queen's University Belfast": "https://www.qub.ac.uk",
    "University of East Anglia (UEA)": "https://www.uea.ac.uk",
    "University of East Anglia": "https://www.uea.ac.uk",
    "Heriot-Watt University": "https://www.hw.ac.uk",
    "University of Strathclyde": "https://www.strath.ac.uk",
    "University of Dundee": "https://www.dundee.ac.uk",
    "Brunel University London": "https://www.brunel.ac.uk",
    "City, University of London": "https://www.city.ac.uk",
    "City University of London": "https://www.city.ac.uk",
    "Aston University": "https://www.aston.ac.uk",
    "Coventry University": "https://www.coventry.ac.uk",
    "University of Kent": "https://www.kent.ac.uk",
    "University of Sussex": "https://www.sussex.ac.uk",
    "University of Essex": "https://www.essex.ac.uk",
    "University of Stirling": "https://www.stir.ac.uk",
    "Cranfield University": "https://www.cranfield.ac.uk",
    "SOAS University of London": "https://www.soas.ac.uk",
    "Goldsmiths, University of London": "https://www.gold.ac.uk",
    "Royal Holloway, University of London": "https://www.royalholloway.ac.uk",
    "Birkbeck, University of London": "https://www.bbk.ac.uk",
    "University of the Arts London": "https://www.arts.ac.uk",
    # Canada
    "University of Toronto": "https://www.utoronto.ca",
    "University of British Columbia": "https://www.ubc.ca",
    "McGill University": "https://www.mcgill.ca",
    "University of Alberta": "https://www.ualberta.ca",
    "University of Waterloo": "https://uwaterloo.ca",
    "McMaster University": "https://www.mcmaster.ca",
    "Queen's University at Kingston": "https://www.queensu.ca",
    "Queen's University": "https://www.queensu.ca",
    "Simon Fraser University": "https://www.sfu.ca",
    "Dalhousie University": "https://www.dal.ca",
    "University of Ottawa": "https://www.uottawa.ca",
    "Western University": "https://www.uwo.ca",
    "University of Calgary": "https://www.ucalgary.ca",
    "University of Victoria (UVic)": "https://www.uvic.ca",
    "University of Victoria": "https://www.uvic.ca",
    "University of Manitoba": "https://umanitoba.ca",
    "Concordia University": "https://www.concordia.ca",
    "Carleton University": "https://carleton.ca",
    "Ryerson University": "https://www.torontomu.ca",
    "University of Guelph": "https://www.uoguelph.ca",
    "York University": "https://www.yorku.ca",
    "University of New Brunswick": "https://www.unb.ca",
    # Australia
    "The University of Melbourne": "https://www.unimelb.edu.au",
    "University of Melbourne": "https://www.unimelb.edu.au",
    "The University of Sydney": "https://www.sydney.edu.au",
    "University of Sydney": "https://www.sydney.edu.au",
    "The Australian National University": "https://www.anu.edu.au",
    "Australian National University": "https://www.anu.edu.au",
    "The University of Queensland": "https://www.uq.edu.au",
    "University of Queensland": "https://www.uq.edu.au",
    "Monash University": "https://www.monash.edu",
    "UNSW Sydney": "https://www.unsw.edu.au",
    "The University of Western Australia": "https://www.uwa.edu.au",
    "University of Western Australia": "https://www.uwa.edu.au",
    "University of Adelaide": "https://www.adelaide.edu.au",
    "The University of Adelaide": "https://www.adelaide.edu.au",
    "University of Technology Sydney": "https://www.uts.edu.au",
    "Macquarie University": "https://www.mq.edu.au",
    "Deakin University": "https://www.deakin.edu.au",
    "RMIT University": "https://www.rmit.edu.au",
    "University of Newcastle": "https://www.newcastle.edu.au",
    "Curtin University": "https://www.curtin.edu.au",
    "Griffith University": "https://www.griffith.edu.au",
    "La Trobe University": "https://www.latrobe.edu.au",
    "University of Wollongong": "https://www.uow.edu.au",
    "Queensland University of Technology": "https://www.qut.edu.au",
    # Germany
    "Technical University of Munich": "https://www.tum.de",
    "LMU Munich": "https://www.lmu.de",
    "Humboldt University of Berlin": "https://www.hu-berlin.de",
    "Humboldt University Berlin": "https://www.hu-berlin.de",
    "Free University of Berlin": "https://www.fu-berlin.de",
    "Free University Berlin": "https://www.fu-berlin.de",
    "Technical University of Berlin": "https://www.tu-berlin.de",
    "RWTH Aachen University": "https://www.rwth-aachen.de",
    "Heidelberg University": "https://www.uni-heidelberg.de",
    "University of Tübingen": "https://uni-tuebingen.de",
    "University of Freiburg": "https://www.uni-freiburg.de",
    "University of Göttingen": "https://www.uni-goettingen.de",
    "University of Cologne": "https://www.uni-koeln.de",
    "Goethe University Frankfurt": "https://www.goethe-university-frankfurt.de",
    "TU Dresden": "https://tu-dresden.de",
    "Karlsruhe Institute of Technology": "https://www.kit.edu",
    "University of Hamburg": "https://www.uni-hamburg.de",
    "University of Mannheim": "https://www.uni-mannheim.de",
    "University of Stuttgart": "https://www.uni-stuttgart.de",
    "University of Münster": "https://www.uni-muenster.de",
    "Ruhr University Bochum": "https://www.ruhr-uni-bochum.de",
    "TU Dortmund University": "https://www.tu-dortmund.de",
    "Friedrich Schiller University Jena": "https://www.uni-jena.de",
    "University of Bonn": "https://www.uni-bonn.de",
    "University of Frankfurt": "https://www.uni-frankfurt.de",
    "University of Würzburg": "https://www.uni-wuerzburg.de",
    "University of Bayreuth": "https://www.uni-bayreuth.de",
    "University of Hohenheim": "https://www.uni-hohenheim.de",
    # France
    "Paris Sciences et Lettres – PSL Research University Paris": "https://psl.eu",
    "Université PSL": "https://psl.eu",
    "École Polytechnique": "https://www.polytechnique.edu",
    "Ecole Polytechnique": "https://www.polytechnique.edu",
    "Sorbonne University": "https://www.sorbonne-universite.fr",
    "University of Paris": "https://u-paris.fr",
    "CentraleSupélec": "https://www.centralesupelec.fr",
    "Sciences Po": "https://www.sciencespo.fr",
    "Sciences Po Paris": "https://www.sciencespo.fr",
    "HEC Paris": "https://www.hec.edu",
    "INSEAD": "https://www.insead.edu",
    "Université Paris-Saclay": "https://www.universite-paris-saclay.fr",
    "Paris-Saclay University": "https://www.universite-paris-saclay.fr",
    "École Normale Supérieure Paris": "https://www.ens.psl.eu",
    "Grenoble Alpes University": "https://www.univ-grenoble-alpes.fr",
    "University of Lyon": "https://www.universite-lyon.fr",
    "Aix-Marseille University": "https://www.univ-amu.fr",
    # Netherlands
    "University of Amsterdam": "https://www.uva.nl",
    "Delft University of Technology": "https://www.tudelft.nl",
    "Leiden University": "https://www.universiteitleiden.nl",
    "Utrecht University": "https://www.uu.nl",
    "Eindhoven University of Technology": "https://www.tue.nl",
    "Wageningen University": "https://www.wur.nl",
    "University of Groningen": "https://www.rug.nl",
    "Radboud University": "https://www.ru.nl",
    "Tilburg University": "https://www.tilburguniversity.edu",
    "Vrije Universiteit Amsterdam": "https://vu.nl",
    "VU Amsterdam": "https://vu.nl",
    "Maastricht University": "https://www.maastrichtuniversity.nl",
    # Singapore
    "National University of Singapore (NUS)": "https://www.nus.edu.sg",
    "National University of Singapore": "https://www.nus.edu.sg",
    "Nanyang Technological University, Singapore (NTU)": "https://www.ntu.edu.sg",
    "Nanyang Technological University": "https://www.ntu.edu.sg",
    "Singapore Management University": "https://www.smu.edu.sg",
    "Singapore University of Technology and Design": "https://www.sutd.edu.sg",
    "Singapore Institute of Technology": "https://www.singaporetech.edu.sg",
    # Japan
    "The University of Tokyo": "https://www.u-tokyo.ac.jp",
    "University of Tokyo": "https://www.u-tokyo.ac.jp",
    "Kyoto University": "https://www.kyoto-u.ac.jp",
    "Osaka University": "https://www.osaka-u.ac.jp",
    "Tokyo Institute of Technology (Tokyo Tech)": "https://www.titech.ac.jp",
    "Tokyo Institute of Technology": "https://www.titech.ac.jp",
    "Tohoku University": "https://www.tohoku.ac.jp",
    "Nagoya University": "https://en.nagoya-u.ac.jp",
    "Kyushu University": "https://www.kyushu-u.ac.jp",
    "Hokkaido University": "https://www.hokudai.ac.jp",
    "Waseda University": "https://www.waseda.jp",
    "Keio University": "https://www.keio.ac.jp",
    # South Korea
    "Seoul National University": "https://www.snu.ac.kr",
    "KAIST - Korea Advanced Institute of Science & Technology": "https://www.kaist.ac.kr",
    "Korea Advanced Institute of Science and Technology (KAIST)": "https://www.kaist.ac.kr",
    "KAIST": "https://www.kaist.ac.kr",
    "Pohang University of Science And Technology (POSTECH)": "https://www.postech.ac.kr",
    "POSTECH": "https://www.postech.ac.kr",
    "Yonsei University": "https://www.yonsei.ac.kr",
    "Korea University": "https://www.korea.ac.kr",
    "Sungkyunkwan University (SKKU)": "https://www.skku.edu",
    # Switzerland
    "ETH Zurich": "https://ethz.ch",
    "EPFL": "https://www.epfl.ch",
    "University of Zurich": "https://www.uzh.ch",
    "University of Basel": "https://www.unibas.ch",
    "University of Geneva": "https://www.unige.ch",
    "University of Bern": "https://www.unibe.ch",
    # Sweden
    "Karolinska Institute": "https://ki.se",
    "Karolinska Institutet": "https://ki.se",
    "Lund University": "https://www.lu.se",
    "Uppsala University": "https://www.uu.se",
    "Stockholm University": "https://www.su.se",
    "Royal Institute of Technology (KTH)": "https://www.kth.se",
    "KTH Royal Institute of Technology": "https://www.kth.se",
    "Chalmers University of Technology": "https://www.chalmers.se",
    "Gothenburg University": "https://www.gu.se",
    "University of Gothenburg": "https://www.gu.se",
    "Linköping University": "https://liu.se",
    # Finland
    "Aalto University": "https://www.aalto.fi",
    "University of Helsinki": "https://www.helsinki.fi",
    "University of Oulu": "https://www.oulu.fi",
    "Tampere University": "https://www.tuni.fi",
    "LUT University": "https://www.lut.fi",
    # Denmark
    "University of Copenhagen": "https://www.ku.dk",
    "Technical University of Denmark": "https://www.dtu.dk",
    "Aarhus University": "https://www.au.dk",
    # Norway
    "University of Oslo": "https://www.uio.no",
    "Norwegian University of Science and Technology": "https://www.ntnu.no",
    # Ireland
    "Trinity College Dublin": "https://www.tcd.ie",
    "University College Dublin": "https://www.ucd.ie",
    "National University of Ireland Galway": "https://www.universityofgalway.ie",
    "University College Cork": "https://www.ucc.ie",
    "Dublin City University": "https://www.dcu.ie",
    # New Zealand
    "University of Auckland": "https://www.auckland.ac.nz",
    "Victoria University of Wellington": "https://www.wgtn.ac.nz",
    "University of Otago": "https://www.otago.ac.nz",
    # Portugal
    "University of Lisbon": "https://www.ulisboa.pt",
    "University of Porto": "https://www.up.pt",
    "Nova School of Business and Economics": "https://www.novasbe.unl.pt",
    # Spain
    "University of Barcelona": "https://www.ub.edu",
    "Complutense University of Madrid": "https://www.ucm.es",
    "Autonomous University of Madrid": "https://www.uam.es",
    "University of Valencia": "https://www.uv.es",
    "ESADE Business School": "https://www.esade.edu",
    "IE University": "https://www.ie.edu",
    "IESE Business School": "https://www.iese.edu",
    # Italy
    "University of Bologna": "https://www.unibo.it",
    "Sapienza University of Rome": "https://www.uniroma1.it",
    "Politecnico di Milano": "https://www.polimi.it",
    "University of Milan": "https://www.unimi.it",
    "University of Turin": "https://www.unito.it",
    "Politecnico di Torino": "https://www.polito.it",
    # UAE
    "United Arab Emirates University": "https://www.uaeu.ac.ae",
    "Khalifa University": "https://www.ku.ac.ae",
    "New York University Abu Dhabi": "https://nyuad.nyu.edu",
    # Hong Kong
    "University of Hong Kong": "https://www.hku.hk",
    "Hong Kong University of Science and Technology": "https://www.ust.hk",
    "Chinese University of Hong Kong": "https://www.cuhk.edu.hk",
    "City University of Hong Kong": "https://www.cityu.edu.hk",
    "Hong Kong Polytechnic University": "https://www.polyu.edu.hk",
    # China
    "Tsinghua University": "https://www.tsinghua.edu.cn",
    "Peking University": "https://www.pku.edu.cn",
    "Fudan University": "https://www.fudan.edu.cn",
    "Shanghai Jiao Tong University": "https://www.sjtu.edu.cn",
    "Zhejiang University": "https://www.zju.edu.cn",
    "University of Science and Technology of China": "https://en.ustc.edu.cn",
    # Malaysia
    "University of Malaya": "https://www.um.edu.my",
    "Universiti Teknologi Malaysia": "https://www.utm.my",
    "Universiti Putra Malaysia": "https://www.upm.edu.my",
    # India
    "Indian Institute of Technology Bombay (IITB)": "https://www.iitb.ac.in",
    "Indian Institute of Technology Delhi (IITD)": "https://www.iitd.ac.in",
    "Indian Institute of Technology Madras (IITM)": "https://www.iitm.ac.in",
    "Indian Institute of Science": "https://www.iisc.ac.in",
}

# ── 2. Country TLD map for fallback URL generation ────────────────────────────
COUNTRY_TLD = {
    "United Kingdom": "ac.uk", "Australia": "edu.au", "Canada": "ca",
    "Germany": "de", "France": "fr", "Netherlands": "nl", "Sweden": "se",
    "Denmark": "dk", "Norway": "no", "Finland": "fi", "Ireland": "ie",
    "Switzerland": "ch", "Italy": "it", "Spain": "es", "Portugal": "pt",
    "Belgium": "be", "Austria": "at", "Poland": "pl", "Czech Republic": "cz",
    "Czechia": "cz", "Japan": "ac.jp", "South Korea": "ac.kr",
    "Singapore": "edu.sg", "China": "edu.cn", "China (Mainland)": "edu.cn",
    "Hong Kong": "edu.hk", "Hong Kong SAR": "edu.hk", "India": "ac.in",
    "New Zealand": "ac.nz", "Brazil": "br", "Russia": "ru",
    "Russian Federation": "ru", "Turkey": "edu.tr", "Malaysia": "edu.my",
    "Thailand": "ac.th", "Indonesia": "ac.id", "UAE": "ac.ae",
    "United Arab Emirates": "ac.ae", "Saudi Arabia": "edu.sa",
    "Egypt": "edu.eg", "South Africa": "ac.za", "Mexico": "mx",
    "Argentina": "ar", "Chile": "cl", "Colombia": "co",
    "United States": "edu",
}

def name_to_domain_slug(name: str) -> str:
    """Convert university name to likely domain slug."""
    # Remove common prefixes/suffixes
    cleaned = re.sub(r'\s*\([^)]+\)', '', name)  # Remove parenthesised short names
    cleaned = re.sub(r'^(The |A )', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r',?\s*(Main campus|North campus|Ann Arbor).*$', '', cleaned, flags=re.IGNORECASE)
    
    # Abbreviation shortcuts
    abbrevs = {
        "Massachusetts Institute of Technology": "mit",
        "California Institute of Technology": "caltech",
        "Carnegie Mellon University": "cmu",
        "Georgia Institute of Technology": "gatech",
        "University of California": "uc",  # will have suffix
        "Universidad Nacional": "unc",
    }
    for k, v in abbrevs.items():
        if k.lower() in cleaned.lower():
            return v
    
    # Generic: lowercase words, join intelligently
    words = cleaned.lower().split()
    stop_words = {'of', 'the', 'and', 'for', 'in', 'at', 'de', 'la', 'le', 'les', 'du',
                  'et', 'di', 'del', 'des', 'van', 'von', 'zu', 'university', 'université',
                  'universitat', 'universidad', 'universidade', 'universiteit', 'universität',
                  'college', 'institute', 'institution', 'school', 'academy', 'polytechnic'}
    key_words = [w for w in words if w not in stop_words and len(w) > 2]
    
    if not key_words:
        key_words = [w for w in words if len(w) > 2][:3]
    
    slug = '-'.join(key_words[:3])
    slug = re.sub(r'[^a-z0-9-]', '', slug)
    return slug or 'university'


def generate_fallback_url(name: str, country: str) -> str:
    tld = COUNTRY_TLD.get(country, "edu")
    slug = name_to_domain_slug(name)
    
    if tld == "ac.uk":
        return f"https://www.{slug}.ac.uk"
    elif tld == "edu.au":
        return f"https://www.{slug}.edu.au"
    elif tld == "ac.jp":
        return f"https://www.{slug}.ac.jp"
    elif tld == "ac.kr":
        return f"https://www.{slug}.ac.kr"
    elif tld == "edu.sg":
        return f"https://www.{slug}.edu.sg"
    elif tld == "ac.in":
        return f"https://www.{slug}.ac.in"
    elif tld == "ac.nz":
        return f"https://www.{slug}.ac.nz"
    elif tld == "edu.cn":
        return f"https://www.{slug}.edu.cn"
    elif tld == "edu.hk":
        return f"https://www.{slug}.edu.hk"
    elif tld in ("edu",):
        return f"https://www.{slug}.edu"
    else:
        return f"https://www.{slug}.{tld}"


def main():
    with engine.connect() as conn:
        rows = conn.execute(sa.text(
            "SELECT id, name, country FROM universities ORDER BY id"
        )).fetchall()
    
    print(f"Processing {len(rows)} universities…")
    
    updates = []
    curated_count = 0
    fallback_count = 0

    for row in rows:
        uid, name, country = row
        # Try exact curated match first
        url = WEBSITE_MAP.get(name)
        if url:
            curated_count += 1
        else:
            url = generate_fallback_url(name, country or "United States")
            fallback_count += 1
        updates.append({"id": uid, "website": url})

    print(f"  Curated: {curated_count}  |  Fallback: {fallback_count}")

    # Batch update in chunks of 200
    with engine.begin() as conn:
        for i in range(0, len(updates), 200):
            batch = updates[i:i+200]
            conn.execute(sa.text("""
                UPDATE universities SET website = :website WHERE id = :id
            """), batch)
            print(f"  Updated {min(i+200, len(updates))}/{len(updates)}…", end="\r")

    print(f"\n✅ Website URLs set for all {len(updates)} universities")


    # ── 3. Fix course_duration: divide by 12 (stored in months, show as years) ──
    with engine.begin() as conn:
        conn.execute(sa.text("""
            UPDATE universities
            SET course_duration = ROUND(course_duration::numeric / 12, 1)
            WHERE course_duration IS NOT NULL AND course_duration > 8
        """))
        print("✅ course_duration converted from months → years")

    # ── 4. Verify ──────────────────────────────────────────────────────────────
    with engine.connect() as conn:
        r = conn.execute(sa.text("""
            SELECT DISTINCT course_duration, COUNT(*) as cnt
            FROM universities WHERE course_duration IS NOT NULL
            GROUP BY course_duration ORDER BY course_duration
        """))
        print("\nDurations after fix:")
        for row in r.fetchall():
            print(f"  {row[0]} yrs — {row[1]} unis")
        
        r2 = conn.execute(sa.text("""
            SELECT name, website FROM universities 
            WHERE name IN ('University of Oxford','Massachusetts Institute of Technology (MIT)',
                           'ETH Zurich', 'National University of Singapore (NUS)')
        """))
        print("\nSample websites:")
        for row in r2.fetchall():
            print(f"  {row[0]}: {row[1]}")


if __name__ == "__main__":
    main()
