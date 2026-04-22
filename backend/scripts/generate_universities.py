"""
Generate a comprehensive universities.csv with 200+ universities.
Columns: name,country,ranking,qs_subject_ranking,subject,tuition,living_cost,
         image_url,website,requirements_cgpa,ielts,toefl,gre_required,
         scholarships,course_duration,description,acceptance_rate
"""

import csv
import os

OUTPUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "universities.csv")
OUTPUT_PATH = os.path.normpath(OUTPUT_PATH)

COLUMNS = [
    "name", "country", "ranking", "qs_subject_ranking", "subject",
    "tuition", "living_cost", "image_url", "website",
    "requirements_cgpa", "ielts", "toefl", "gre_required",
    "scholarships", "course_duration", "description", "acceptance_rate"
]

# ─────────────────────────────────────────────────────────────────────────────
# Helper
# ─────────────────────────────────────────────────────────────────────────────
def u(name, country, ranking, qs_subject_ranking, subject,
      tuition, living_cost, domain, website,
      cgpa, ielts, toefl, gre, scholarships, duration,
      description, acceptance_rate):
    return {
        "name": name,
        "country": country,
        "ranking": ranking,
        "qs_subject_ranking": qs_subject_ranking,
        "subject": subject,
        "tuition": tuition,
        "living_cost": living_cost,
        "image_url": f"https://logo.clearbit.com/{domain}",
        "website": website,
        "requirements_cgpa": cgpa,
        "ielts": ielts,
        "toefl": toefl,
        "gre_required": gre,
        "scholarships": scholarships,
        "course_duration": duration,
        "description": description,
        "acceptance_rate": acceptance_rate,
    }


UNIVERSITIES = [

    # ──────────────────────────────────────────────────────────────────────────
    # UNITED KINGDOM (38 universities)
    # ──────────────────────────────────────────────────────────────────────────
    u("University of Oxford", "United Kingdom", 3, 1,
      "Computer Science|Mathematics|Physics|Economics|Law|Medicine|Engineering|Philosophy|History|Social Science|Public Health|Environmental|Arts|Business|Data Science",
      35000, 18000, "ox.ac.uk", "https://www.ox.ac.uk",
      8.0, 7.5, 110, False, "Rhodes Scholarship", 12,
      "The University of Oxford is one of the world's oldest and most prestigious universities, consistently ranked in the global top 5. It offers world-class teaching and research across virtually every academic discipline.",
      0.17),

    u("University of Cambridge", "United Kingdom", 2, 2,
      "Computer Science|Mathematics|Physics|Economics|Engineering|Law|Medicine|Architecture|Social Science|Environmental|Arts|History|Philosophy|Data Science",
      35000, 18000, "cam.ac.uk", "https://www.cam.ac.uk",
      8.0, 7.5, 110, False, "Cambridge Trust Scholarship", 12,
      "The University of Cambridge is a world-leading research university with a rich 800-year history. Its collegiate system and rigorous academic culture have produced over 100 Nobel laureates.",
      0.21),

    u("Imperial College London", "United Kingdom", 6, 3,
      "Computer Science|Engineering|Physics|Mathematics|Medicine|Data Science|Environmental|Business|Bioengineering|Chemical Engineering",
      36000, 18000, "imperial.ac.uk", "https://www.imperial.ac.uk",
      7.5, 7.0, 100, False, "President's PhD Scholarship", 12,
      "Imperial College London is a science-focused university in the heart of London, renowned for its engineering, medicine, and natural sciences programmes. It is consistently ranked among the world's top 10 universities.",
      0.14),

    u("University College London", "United Kingdom", 9, 8,
      "Computer Science|Engineering|Economics|Law|Medicine|Architecture|Arts|Social Science|Public Health|Environmental|Data Science|Mathematics|Business",
      30000, 18000, "ucl.ac.uk", "https://www.ucl.ac.uk",
      7.5, 7.0, 100, False, "UCL Global Masters Scholarship", 12,
      "UCL is London's leading multidisciplinary university, with more than 16,000 staff and 50,000 students from 150 countries. It is known for its commitment to research, innovation and global impact.",
      0.63),

    u("London School of Economics", "United Kingdom", 45, 5,
      "Economics|Finance|Business|Law|Social Science|Public Health|Data Science|Political Science|International Relations|Sociology|Management",
      28000, 18000, "lse.ac.uk", "https://www.lse.ac.uk",
      7.5, 7.0, 107, False, "LSE Postgraduate Support Scheme", 12,
      "The London School of Economics and Political Science is a world-leading social science university, specialising in economics, finance, law, and the social and political sciences. LSE's alumni include heads of state, Nobel laureates, and business leaders.",
      0.16),

    u("King's College London", "United Kingdom", 40, 22,
      "Law|Medicine|Engineering|Business|Social Science|Arts|Public Health|Nursing|Computer Science|Mathematics|Economics|International Relations",
      28000, 18000, "kcl.ac.uk", "https://www.kcl.ac.uk",
      7.0, 7.0, 100, False, "King's India Scholarship", 12,
      "King's College London is one of the UK's oldest and most prestigious universities, with a strong reputation in law, medicine, and the humanities. Situated in the centre of London, it offers students a vibrant academic and cultural experience.",
      0.28),

    u("University of Edinburgh", "United Kingdom", 22, 15,
      "Computer Science|Engineering|Medicine|Law|Business|Economics|Arts|Social Science|Mathematics|Data Science|Environmental|Architecture|Philosophy",
      28000, 15000, "ed.ac.uk", "https://www.ed.ac.uk",
      7.0, 6.5, 92, False, "Edinburgh Global Online Learning Scholarship", 12,
      "The University of Edinburgh is one of the UK's oldest and most prestigious universities, founded in 1583. It is a global research leader and a top destination for students in arts, medicine, and technology.",
      0.43),

    u("University of Manchester", "United Kingdom", 32, 20,
      "Computer Science|Engineering|Business|Economics|Medicine|Physics|Mathematics|Law|Social Science|Data Science|Arts|Environmental|Architecture",
      26000, 14000, "manchester.ac.uk", "https://www.manchester.ac.uk",
      7.0, 6.5, 90, False, "President's Doctoral Scholar Award", 12,
      "The University of Manchester is a major research university and member of the prestigious Russell Group. It is home to a vibrant student community and has strong connections with industry, making it ideal for career-focused study.",
      0.54),

    u("University of Bristol", "United Kingdom", 55, 30,
      "Computer Science|Engineering|Economics|Law|Medicine|Arts|Social Science|Mathematics|Physics|Environmental|Architecture|Data Science|Business",
      25000, 15000, "bristol.ac.uk", "https://www.bristol.ac.uk",
      7.0, 6.5, 90, False, "Think Big Scholarship", 12,
      "The University of Bristol is a leading UK research university known for its excellence in science, engineering, arts, and social sciences. It has a strong research culture and a vibrant student community.",
      0.61),

    u("University of Warwick", "United Kingdom", 69, 35,
      "Computer Science|Economics|Business|Engineering|Mathematics|Law|Arts|Social Science|Finance|Data Science|Physics|Statistics",
      27000, 14000, "warwick.ac.uk", "https://www.warwick.ac.uk",
      7.5, 6.5, 92, False, "Warwick Chancellors International Scholarship", 12,
      "The University of Warwick is a leading UK research university renowned for its strengths in business, economics, engineering, and the sciences. It consistently ranks among the top universities in the UK and globally.",
      0.78),

    u("Durham University", "United Kingdom", 92, 55,
      "Computer Science|Engineering|Business|Economics|Law|Arts|Social Science|Mathematics|Physics|Finance|Environmental|Medicine|Archaeology",
      25000, 13000, "durham.ac.uk", "https://www.durham.ac.uk",
      7.0, 6.5, 90, False, "Durham Global Support Scholarship", 12,
      "Durham University is one of the UK's most prestigious universities, known for its collegiate system and strong academic tradition. It excels in the arts and humanities, sciences, and social sciences.",
      0.66),

    u("University of Bath", "United Kingdom", 158, 70,
      "Engineering|Business|Computer Science|Mathematics|Economics|Social Science|Architecture|Data Science|Chemistry|Physics",
      25000, 14000, "bath.ac.uk", "https://www.bath.ac.uk",
      7.0, 6.5, 90, False, "", 12,
      "The University of Bath is consistently ranked among the top universities in the UK and is renowned for its excellence in engineering, science, and management. Its strong industry links provide excellent graduate employment prospects.",
      0.72),

    u("University of Birmingham", "United Kingdom", 84, 50,
      "Computer Science|Engineering|Business|Economics|Law|Medicine|Arts|Social Science|Mathematics|Environmental|Finance|Architecture|Data Science",
      24000, 13000, "birmingham.ac.uk", "https://www.birmingham.ac.uk",
      7.0, 6.5, 88, False, "Global Excellence Scholarship", 12,
      "The University of Birmingham is a leading UK research university and member of the Russell Group. It is known for its strength in engineering, business, and medicine, and its global research partnerships.",
      0.66),

    u("University of Nottingham", "United Kingdom", 99, 60,
      "Computer Science|Engineering|Business|Economics|Medicine|Law|Arts|Social Science|Mathematics|Environmental|Data Science|Finance|Architecture|Pharmacy",
      23000, 12000, "nottingham.ac.uk", "https://www.nottingham.ac.uk",
      7.0, 6.5, 88, False, "Nottingham Global Impact Scholarship", 12,
      "The University of Nottingham is a Russell Group university with a strong international presence and campuses in Malaysia and China. It is known for its research excellence and innovation-friendly environment.",
      0.69),

    u("University of Leeds", "United Kingdom", 86, 45,
      "Computer Science|Engineering|Business|Economics|Law|Medicine|Arts|Social Science|Mathematics|Environmental|Data Science|Architecture|Education|Finance",
      23000, 13000, "leeds.ac.uk", "https://www.leeds.ac.uk",
      7.0, 6.5, 88, False, "Leeds International Scholarship", 12,
      "The University of Leeds is a leading UK research university and Russell Group member, known for its excellence in engineering, business, medicine, and the arts. It is one of the UK's largest universities with a vibrant student community.",
      0.69),

    u("University of Sheffield", "United Kingdom", 105, 65,
      "Computer Science|Engineering|Business|Economics|Medicine|Law|Arts|Social Science|Mathematics|Environmental|Architecture|Data Science|Finance",
      23000, 13000, "sheffield.ac.uk", "https://www.sheffield.ac.uk",
      7.0, 6.5, 88, False, "Sheffield Merit Scholarship", 12,
      "The University of Sheffield is a Russell Group university widely recognised for research excellence in engineering, science, and medicine. It has a strong student satisfaction record and excellent graduate employment outcomes.",
      0.72),

    u("University of Glasgow", "United Kingdom", 73, 42,
      "Computer Science|Engineering|Business|Economics|Medicine|Law|Arts|Social Science|Mathematics|Environmental|Data Science|Architecture|Veterinary",
      24000, 13000, "gla.ac.uk", "https://www.gla.ac.uk",
      7.0, 6.5, 90, False, "Glasgow Caledonian Scholarship", 12,
      "The University of Glasgow is one of the UK's oldest universities and a member of the Russell Group. It is renowned for research excellence in medicine, science, engineering, and the arts.",
      0.74),

    u("University of St Andrews", "United Kingdom", 100, 58,
      "Computer Science|Mathematics|Physics|Economics|Arts|Social Science|History|Philosophy|Environmental|Medicine|Law|International Relations",
      26000, 13000, "st-andrews.ac.uk", "https://www.st-andrews.ac.uk",
      7.5, 7.0, 100, False, "St Andrews Scholarship", 12,
      "The University of St Andrews is Scotland's oldest university and one of the most ancient in the English-speaking world. It is celebrated for its academic excellence, historic campus, and strong student community.",
      0.30),

    u("University of Exeter", "United Kingdom", 153, 75,
      "Computer Science|Engineering|Business|Economics|Law|Arts|Social Science|Mathematics|Environmental|Data Science|Finance|Education|Biosciences",
      23000, 13000, "exeter.ac.uk", "https://www.exeter.ac.uk",
      7.0, 6.5, 88, False, "Global Excellence Scholarship", 12,
      "The University of Exeter is a research-intensive university in the Russell Group, known for its beautiful campuses and strengths in sustainability, business, and the humanities. It ranks highly for student satisfaction.",
      0.70),

    u("University of Southampton", "United Kingdom", 81, 48,
      "Computer Science|Engineering|Business|Economics|Medicine|Law|Arts|Social Science|Mathematics|Environmental|Data Science|Oceanography|Architecture|Finance",
      24000, 13000, "southampton.ac.uk", "https://www.southampton.ac.uk",
      7.0, 6.5, 88, False, "Southampton Excellence Scholarship", 12,
      "The University of Southampton is a leading UK research university and a member of the Russell Group, with particular strengths in engineering, electronics, oceanography, and medicine. It is home to world-class research facilities.",
      0.68),

    u("University of York", "United Kingdom", 175, 80,
      "Computer Science|Business|Economics|Arts|Social Science|Mathematics|Environmental|Law|Health Sciences|Education|History|Philosophy|Data Science",
      22000, 13000, "york.ac.uk", "https://www.york.ac.uk",
      7.0, 6.5, 88, False, "", 12,
      "The University of York is a Russell Group university known for its teaching quality, research impact, and beautiful campus. It has particular strengths in health sciences, social sciences, arts, and computer science.",
      0.74),

    u("Queen Mary University of London", "United Kingdom", 150, 72,
      "Computer Science|Engineering|Business|Economics|Law|Medicine|Arts|Social Science|Mathematics|Environmental|Data Science|Finance",
      24000, 18000, "qmul.ac.uk", "https://www.qmul.ac.uk",
      7.0, 6.5, 90, False, "Principal's Postgraduate Research Scholarship", 12,
      "Queen Mary University of London is a leading UK research university and member of the Russell Group. Based in vibrant East London, it is known for its strength in medicine, law, engineering, and the humanities.",
      0.71),

    u("Lancaster University", "United Kingdom", 163, 78,
      "Computer Science|Business|Economics|Arts|Social Science|Mathematics|Environmental|Law|Management|Finance|Data Science",
      21000, 12000, "lancaster.ac.uk", "https://www.lancaster.ac.uk",
      7.0, 6.5, 88, False, "Lancaster Global Scholarship", 12,
      "Lancaster University is a highly ranked UK university known for its collegiate campus environment and research excellence in business, management, and the social sciences. It consistently scores highly in national teaching quality surveys.",
      0.69),

    u("University of Liverpool", "United Kingdom", 176, 82,
      "Computer Science|Engineering|Business|Economics|Law|Medicine|Arts|Social Science|Mathematics|Environmental|Architecture|Data Science|Finance",
      22000, 13000, "liverpool.ac.uk", "https://www.liverpool.ac.uk",
      7.0, 6.5, 88, False, "", 12,
      "The University of Liverpool is a Russell Group research university with strong programmes in engineering, science, medicine, and the arts. Its vibrant city campus offers an outstanding student experience.",
      0.72),

    u("Newcastle University", "United Kingdom", 178, 84,
      "Computer Science|Engineering|Business|Economics|Law|Medicine|Arts|Social Science|Mathematics|Environmental|Architecture|Data Science|Finance",
      23000, 13000, "ncl.ac.uk", "https://www.ncl.ac.uk",
      7.0, 6.5, 88, False, "", 12,
      "Newcastle University is a Russell Group institution known for its research excellence in engineering, medicine, and the arts. It is located in one of the UK's most vibrant and affordable student cities.",
      0.72),

    u("Cardiff University", "United Kingdom", 183, 88,
      "Computer Science|Engineering|Business|Economics|Law|Medicine|Arts|Social Science|Mathematics|Environmental|Architecture|Data Science|Finance|Pharmacy",
      22000, 12000, "cardiff.ac.uk", "https://www.cardiff.ac.uk",
      7.0, 6.5, 88, False, "", 12,
      "Cardiff University is Wales's leading research university and a member of the Russell Group, known for its vibrant capital city campus and strengths in medicine, engineering, and the social sciences.",
      0.73),

    u("Loughborough University", "United Kingdom", 222, 95,
      "Engineering|Business|Computer Science|Mathematics|Social Science|Sports Science|Architecture|Data Science|Economics|Design",
      22000, 12000, "lboro.ac.uk", "https://www.lboro.ac.uk",
      7.0, 6.5, 88, False, "", 12,
      "Loughborough University is a leading UK university renowned for engineering, design, and sports science. It consistently tops rankings for student experience and graduate employability.",
      0.74),

    u("University of Aberdeen", "United Kingdom", 238, 100,
      "Computer Science|Engineering|Business|Economics|Law|Medicine|Arts|Social Science|Mathematics|Environmental|Energy|Data Science",
      20000, 12000, "abdn.ac.uk", "https://www.abdn.ac.uk",
      7.0, 6.5, 88, False, "", 12,
      "The University of Aberdeen is one of the UK's oldest universities, founded in 1495, with particular strengths in energy, medicine, and the physical sciences. It offers a friendly campus environment in one of Scotland's most vibrant cities.",
      0.78),

    u("Heriot-Watt University", "United Kingdom", 354, 115,
      "Engineering|Computer Science|Business|Mathematics|Environmental|Architecture|Data Science|Economics|Energy|Finance",
      20000, 13000, "hw.ac.uk", "https://www.hw.ac.uk",
      7.0, 6.5, 88, False, "", 12,
      "Heriot-Watt University is a specialist institution with a strong focus on science, engineering, and business. It has campuses in Edinburgh, Dubai, and Malaysia, making it a truly global university.",
      0.75),

    u("University of Reading", "United Kingdom", 278, 108,
      "Business|Economics|Law|Arts|Social Science|Environmental|Agriculture|Computer Science|Data Science|Mathematics|Education|Finance",
      22000, 14000, "reading.ac.uk", "https://www.reading.ac.uk",
      7.0, 6.5, 88, False, "", 12,
      "The University of Reading is a research-intensive university known for its strengths in meteorology, agriculture, business, and the arts. It has a beautiful campus and strong links to industry.",
      0.76),

    u("University of Leicester", "United Kingdom", 296, 112,
      "Computer Science|Engineering|Business|Economics|Law|Medicine|Arts|Social Science|Mathematics|Data Science|Finance|Archaeology|Space Science",
      22000, 12000, "le.ac.uk", "https://www.le.ac.uk",
      7.0, 6.5, 88, False, "", 12,
      "The University of Leicester is a research-led university known for pioneering discoveries in genetics, space science, and medieval history. It has a strong focus on widening participation and student wellbeing.",
      0.76),

    u("University of Sussex", "United Kingdom", 327, 120,
      "Computer Science|Business|Economics|Law|Arts|Social Science|Environmental|Mathematics|Data Science|Education|Psychology|Finance",
      22000, 15000, "sussex.ac.uk", "https://www.sussex.ac.uk",
      7.0, 6.5, 88, False, "", 12,
      "The University of Sussex is a research university in Brighton, known for its progressive values and strengths in social sciences, arts, and environmental studies. It has a beautiful campus close to the South Downs.",
      0.76),

    u("University of Stirling", "United Kingdom", 401, 135,
      "Business|Economics|Law|Arts|Social Science|Environmental|Computer Science|Data Science|Finance|Education|Nursing",
      20000, 12000, "stir.ac.uk", "https://www.stir.ac.uk",
      7.0, 6.5, 85, False, "", 12,
      "The University of Stirling is a campus university in Scotland known for its strengths in sports science, business, and social sciences. It has a picturesque loch-side campus and a strong research profile.",
      0.78),

    u("Coventry University", "United Kingdom", 601, 180,
      "Engineering|Business|Computer Science|Arts|Social Science|Economics|Law|Data Science|Architecture|Finance|Design",
      18000, 12000, "coventry.ac.uk", "https://www.coventry.ac.uk",
      6.5, 6.0, 85, False, "", 12,
      "Coventry University is a dynamic, modern university in the Midlands known for its strong industry connections and career-focused programmes. It is one of the most popular destinations for international students in the UK.",
      0.85),

    u("Aston University", "United Kingdom", 551, 165,
      "Engineering|Business|Computer Science|Mathematics|Economics|Law|Data Science|Pharmacy|Social Science|Finance|Optometry",
      22000, 12000, "aston.ac.uk", "https://www.aston.ac.uk",
      7.0, 6.5, 88, False, "", 12,
      "Aston University is a leading university in Birmingham known for its focus on business, engineering, and health sciences. It has strong ties to industry and an impressive graduate employment record.",
      0.76),

    u("City University of London", "United Kingdom", 533, 160,
      "Business|Economics|Law|Computer Science|Engineering|Finance|Social Science|Data Science|Arts|Journalism|Optometry",
      24000, 18000, "city.ac.uk", "https://www.city.ac.uk",
      7.0, 6.5, 90, False, "", 12,
      "City, University of London is a leading global university committed to academic excellence and practical impact. It is particularly known for its programmes in law, business, finance, and journalism.",
      0.78),

    u("Brunel University London", "United Kingdom", 596, 178,
      "Engineering|Computer Science|Business|Economics|Arts|Social Science|Law|Design|Data Science|Mathematics|Finance",
      21000, 18000, "brunel.ac.uk", "https://www.brunel.ac.uk",
      7.0, 6.0, 85, False, "", 12,
      "Brunel University London is a research university in West London known for its applied research and strong connections to industry and government. It offers an excellent student experience with a focus on employability.",
      0.78),

    u("University of Surrey", "United Kingdom", 435, 140,
      "Engineering|Computer Science|Business|Economics|Arts|Social Science|Environmental|Data Science|Mathematics|Finance|Veterinary",
      24000, 15000, "surrey.ac.uk", "https://www.surrey.ac.uk",
      7.0, 6.5, 88, False, "", 12,
      "The University of Surrey is a leading research university in Guildford, known for its strengths in engineering, business, and the life sciences. It has a beautiful campus and a strong graduate employment record.",
      0.73),


    # ──────────────────────────────────────────────────────────────────────────
    # UNITED STATES (42 universities)
    # ──────────────────────────────────────────────────────────────────────────
    u("Massachusetts Institute of Technology", "United States", 1, 1,
      "Computer Science|Engineering|Physics|Mathematics|Data Science|Business|Architecture|Economics|Chemistry|Bioengineering|Aerospace|Mechanical Engineering",
      59000, 22000, "mit.edu", "https://www.mit.edu",
      9.0, 7.5, 100, True, "MIT Fellowship", 12,
      "MIT is the world's foremost science and technology university, consistently ranked #1 globally. Its cutting-edge research and innovation culture have produced 98 Nobel laureates and countless transformative technologies.",
      0.04),

    u("Stanford University", "United States", 5, 4,
      "Computer Science|Engineering|Business|Medicine|Law|Economics|Education|Environmental|Data Science|Physics|Mathematics|Social Science",
      58000, 22000, "stanford.edu", "https://www.stanford.edu",
      9.0, 7.5, 100, True, "Stanford Fellowship", 12,
      "Stanford University is a world-leading research university at the heart of Silicon Valley, renowned for innovation, entrepreneurship, and excellence across engineering, business, and the humanities.",
      0.04),

    u("Harvard University", "United States", 4, 3,
      "Computer Science|Engineering|Business|Medicine|Law|Economics|Education|Environmental|Data Science|Physics|Mathematics|Social Science|Public Health|Arts|History",
      55000, 22000, "harvard.edu", "https://www.harvard.edu",
      9.0, 7.5, 100, False, "Harvard Financial Aid", 12,
      "Harvard University is one of the world's most iconic and prestigious institutions, with strengths across every academic discipline from law and medicine to science and the humanities. Its global alumni network is unparalleled.",
      0.03),

    u("California Institute of Technology", "United States", 6, 2,
      "Computer Science|Engineering|Physics|Mathematics|Data Science|Chemistry|Astronomy|Bioengineering|Aerospace",
      60000, 22000, "caltech.edu", "https://www.caltech.edu",
      9.0, 7.5, 100, True, "Caltech Fellowship", 12,
      "Caltech is a world-renowned science and engineering institution in Pasadena, California. With one of the highest faculty-to-student ratios in the world, it offers an incredibly intense and rewarding academic experience.",
      0.04),

    u("Yale University", "United States", 16, 10,
      "Computer Science|Engineering|Business|Medicine|Law|Economics|Education|Environmental|Arts|History|Philosophy|Social Science|Architecture|Data Science",
      64000, 22000, "yale.edu", "https://www.yale.edu",
      9.0, 7.5, 100, False, "Yale Graduate Fellowship", 12,
      "Yale University is one of the Ivy League's most celebrated institutions, known for its outstanding programmes in law, medicine, arts, and the humanities. It combines rigorous scholarship with a vibrant cultural life.",
      0.05),

    u("Princeton University", "United States", 17, 11,
      "Computer Science|Engineering|Physics|Mathematics|Economics|Social Science|Arts|History|Philosophy|Data Science|Environmental|Public Policy",
      58000, 22000, "princeton.edu", "https://www.princeton.edu",
      9.0, 7.5, 100, True, "Princeton Graduate Fellowship", 12,
      "Princeton University is an Ivy League institution renowned for its undergraduate focus, world-class research, and famous alumni in politics, business, and the sciences. It consistently ranks among the world's top universities.",
      0.04),

    u("Columbia University", "United States", 22, 14,
      "Computer Science|Engineering|Business|Medicine|Law|Economics|Education|Environmental|Arts|History|Philosophy|Social Science|Architecture|Data Science|Public Health|Journalism",
      67000, 22000, "columbia.edu", "https://www.columbia.edu",
      8.5, 7.0, 100, True, "Columbia University Fellowship", 12,
      "Columbia University is an Ivy League research university in New York City, offering a uniquely urban and cosmopolitan academic environment. It excels in journalism, law, business, and the sciences.",
      0.05),

    u("Cornell University", "United States", 20, 12,
      "Computer Science|Engineering|Business|Medicine|Law|Economics|Architecture|Environmental|Arts|Social Science|Data Science|Agriculture|Hotel Management",
      61000, 22000, "cornell.edu", "https://www.cornell.edu",
      8.5, 7.0, 100, True, "Cornell Graduate Fellowship", 12,
      "Cornell University is an Ivy League research university in Ithaca, New York, known for its diverse range of programmes and research excellence. It is one of the few Ivy League universities with a college of engineering.",
      0.10),

    u("University of Chicago", "United States", 11, 7,
      "Computer Science|Economics|Business|Law|Social Science|Arts|History|Philosophy|Mathematics|Data Science|Public Policy|Physics",
      61000, 22000, "uchicago.edu", "https://www.uchicago.edu",
      8.5, 7.0, 102, False, "UChicago Merit Award", 12,
      "The University of Chicago is a world-renowned research university known for its rigorous academic culture and pioneering work in economics, law, and the social sciences. It has been home to 100 Nobel laureates.",
      0.06),

    u("University of Pennsylvania", "United States", 12, 8,
      "Computer Science|Engineering|Business|Medicine|Law|Economics|Social Science|Arts|Architecture|Data Science|Nursing|Education|Finance",
      62000, 22000, "upenn.edu", "https://www.upenn.edu",
      8.5, 7.0, 100, True, "Penn Provost Fellowship", 12,
      "The University of Pennsylvania is an Ivy League institution in Philadelphia, home to the Wharton School, one of the world's top business schools. It excels in medicine, law, business, and engineering.",
      0.07),

    u("Duke University", "United States", 67, 38,
      "Computer Science|Engineering|Business|Medicine|Law|Economics|Environmental|Arts|Social Science|Data Science|Public Policy|Mathematics",
      62000, 22000, "duke.edu", "https://www.duke.edu",
      8.5, 7.0, 100, False, "Duke Graduate Fellowship", 12,
      "Duke University is a leading research university in Durham, North Carolina, known for its excellence in medicine, law, business, and environmental science. It combines a vibrant campus life with rigorous academic standards.",
      0.08),

    u("Johns Hopkins University", "United States", 31, 18,
      "Medicine|Public Health|Engineering|Computer Science|Social Science|Arts|Economics|Data Science|Environmental|Bioengineering|Nursing|International Studies",
      60000, 22000, "jhu.edu", "https://www.jhu.edu",
      8.5, 7.0, 100, True, "JHU Graduate Fellowship", 12,
      "Johns Hopkins University is a world-leader in medicine, public health, and engineering research. It is renowned for producing pioneering research and fostering a culture of discovery and scientific inquiry.",
      0.11),

    u("Northwestern University", "United States", 46, 28,
      "Computer Science|Engineering|Business|Medicine|Law|Economics|Social Science|Arts|Data Science|Journalism|Education|Finance|Mathematics",
      62000, 22000, "northwestern.edu", "https://www.northwestern.edu",
      8.5, 7.0, 100, True, "Northwestern Graduate Fellowship", 12,
      "Northwestern University is a leading private research university in Evanston, Illinois, known for its strengths in business, journalism, engineering, and the performing arts.",
      0.07),

    u("Dartmouth College", "United States", 240, 102,
      "Economics|Business|Arts|History|Philosophy|Social Science|Engineering|Computer Science|Environmental|Law|Medicine|Data Science",
      62000, 22000, "dartmouth.edu", "https://www.dartmouth.edu",
      8.5, 7.0, 100, False, "Dartmouth Fellowship", 12,
      "Dartmouth College is an Ivy League institution known for its emphasis on undergraduate education and a tight-knit community. It excels in business (Tuck School), engineering, and the liberal arts.",
      0.07),

    u("Brown University", "United States", 198, 88,
      "Computer Science|Engineering|Economics|Arts|History|Philosophy|Social Science|Medicine|Data Science|Environmental|Mathematics|Business",
      65000, 22000, "brown.edu", "https://www.brown.edu",
      8.5, 7.0, 100, False, "Brown Graduate Fellowship", 12,
      "Brown University is an Ivy League research university in Providence, Rhode Island, known for its open curriculum and emphasis on student autonomy. It excels in computer science, engineering, and the liberal arts.",
      0.05),

    u("Rice University", "United States", 165, 75,
      "Computer Science|Engineering|Physics|Mathematics|Economics|Arts|Architecture|Social Science|Data Science|Business|Bioengineering",
      55000, 20000, "rice.edu", "https://www.rice.edu",
      8.5, 7.0, 100, True, "Rice Graduate Fellowship", 12,
      "Rice University is a small, highly selective research university in Houston, Texas, known for its strong programmes in engineering, natural sciences, and architecture. Its low student-to-faculty ratio ensures an exceptional learning experience.",
      0.09),

    u("Vanderbilt University", "United States", 186, 86,
      "Computer Science|Engineering|Business|Medicine|Law|Economics|Education|Arts|Social Science|Data Science|Nursing|Mathematics",
      61000, 20000, "vanderbilt.edu", "https://www.vanderbilt.edu",
      8.0, 7.0, 100, True, "Vanderbilt Graduate Fellowship", 12,
      "Vanderbilt University is a leading private research university in Nashville, Tennessee, known for its excellence in medicine, education, and the arts. It combines a friendly, collaborative community with rigorous academic standards.",
      0.09),

    u("University of Notre Dame", "United States", 216, 93,
      "Computer Science|Engineering|Business|Law|Economics|Arts|History|Philosophy|Social Science|Data Science|Theology|Finance",
      60000, 20000, "nd.edu", "https://www.nd.edu",
      8.0, 7.0, 100, False, "Notre Dame Graduate Fellowship", 12,
      "The University of Notre Dame is a leading Catholic research university in South Bend, Indiana, renowned for its law school, business school, and strong sense of community and tradition.",
      0.13),

    u("Georgetown University", "United States", 264, 108,
      "Computer Science|Business|Law|Economics|Social Science|International Relations|Arts|History|Medicine|Data Science|Public Policy|Finance",
      60000, 22000, "georgetown.edu", "https://www.georgetown.edu",
      8.0, 7.0, 100, False, "Georgetown Graduate Fellowship", 12,
      "Georgetown University is a leading Jesuit research university in Washington D.C., known for its programmes in law, international relations, business, and public policy. Its location makes it a hub for politics and government.",
      0.12),

    u("Emory University", "United States", 278, 112,
      "Business|Medicine|Law|Economics|Computer Science|Social Science|Arts|Public Health|Data Science|Environmental|Finance|Nursing",
      58000, 20000, "emory.edu", "https://www.emory.edu",
      8.0, 7.0, 100, False, "Emory Graduate Fellowship", 12,
      "Emory University is a top research university in Atlanta, Georgia, known for its outstanding programmes in medicine, public health, business, and the arts. It has strong connections with the Centers for Disease Control and Prevention.",
      0.17),

    u("Carnegie Mellon University", "United States", 53, 30,
      "Computer Science|Engineering|Business|Arts|Social Science|Data Science|Architecture|Mathematics|Robotics|Design|Public Policy|Economics",
      62000, 22000, "cmu.edu", "https://www.cmu.edu",
      8.5, 7.0, 100, True, "CMU Graduate Fellowship", 12,
      "Carnegie Mellon University is a world-leading research university in Pittsburgh, Pennsylvania, consistently ranked among the top institutions globally for computer science, engineering, and the arts. It is a hub for technology and innovation.",
      0.15),

    u("University of Michigan", "United States", 23, 16,
      "Computer Science|Engineering|Business|Medicine|Law|Economics|Education|Arts|Social Science|Data Science|Architecture|Environmental|Public Policy|Finance",
      52000, 20000, "umich.edu", "https://www.umich.edu",
      8.0, 6.5, 100, True, "Rackham Graduate School Fellowship", 12,
      "The University of Michigan is one of the world's top public universities, renowned for its research output and comprehensive range of programmes. Its Ross School of Business and College of Engineering are among the best in the United States.",
      0.20),

    u("University of North Carolina Chapel Hill", "United States", 64, 37,
      "Business|Medicine|Law|Economics|Computer Science|Social Science|Arts|Public Health|Data Science|Environmental|Education|Pharmacy|Nursing",
      35000, 18000, "unc.edu", "https://www.unc.edu",
      8.0, 6.5, 100, False, "UNC Graduate School Fellowship", 12,
      "UNC Chapel Hill is one of the oldest public universities in the United States, known for its excellence in medicine, public health, and the social sciences. It is a flagship institution of North Carolina's renowned Research Triangle.",
      0.18),

    u("University of California Los Angeles", "United States", 44, 27,
      "Computer Science|Engineering|Business|Medicine|Law|Economics|Arts|Social Science|Data Science|Architecture|Environmental|Film|Public Health|Finance|Mathematics",
      44000, 22000, "ucla.edu", "https://www.ucla.edu",
      8.0, 7.0, 100, True, "UCLA Graduate Division Fellowship", 12,
      "UCLA is one of the world's top public research universities, located in the vibrant Westside of Los Angeles. It excels in medicine, engineering, law, and the arts, and has produced more Olympic athletes than any other university.",
      0.12),

    u("University of California Berkeley", "United States", 10, 6,
      "Computer Science|Engineering|Business|Economics|Law|Arts|Social Science|Data Science|Architecture|Environmental|Physics|Mathematics|Chemistry|Public Policy",
      45000, 22000, "berkeley.edu", "https://www.berkeley.edu",
      8.5, 7.0, 100, True, "Berkeley Fellowship", 12,
      "UC Berkeley is the world's leading public research university, renowned for its Nobel laureates, pioneering research, and innovative spirit. It excels across virtually every academic discipline and is a driving force in technology and public policy.",
      0.14),

    u("University of Illinois Urbana-Champaign", "United States", 35, 22,
      "Computer Science|Engineering|Business|Economics|Law|Arts|Social Science|Data Science|Architecture|Environmental|Physics|Mathematics|Agriculture|Education",
      36000, 18000, "illinois.edu", "https://www.illinois.edu",
      8.0, 6.5, 103, True, "Illinois Graduate College Fellowship", 12,
      "UIUC is one of the world's top research universities, renowned for its engineering and computer science programmes. It is a major hub for technology innovation and has produced an extraordinary number of Fortune 500 CEOs.",
      0.45),

    u("Georgia Institute of Technology", "United States", 97, 56,
      "Computer Science|Engineering|Business|Economics|Architecture|Data Science|Mathematics|Physics|Environmental|Design|Public Policy|Computing",
      32000, 18000, "gatech.edu", "https://www.gatech.edu",
      8.0, 6.5, 100, True, "Georgia Tech Graduate Fellowship", 12,
      "Georgia Tech is a world-class technology and engineering university in Atlanta, consistently ranked among the top public universities in the United States. It has strong industry partnerships and an outstanding innovation ecosystem.",
      0.18),

    u("University of Texas at Austin", "United States", 71, 42,
      "Computer Science|Engineering|Business|Law|Economics|Arts|Social Science|Data Science|Architecture|Environmental|Public Policy|Education|Finance",
      38000, 18000, "utexas.edu", "https://www.utexas.edu",
      7.5, 6.5, 100, True, "UT Austin Graduate School Fellowship", 12,
      "UT Austin is one of the largest and most prestigious public universities in the United States, known for its research excellence in engineering, business, and law. It sits at the heart of Austin's thriving tech and startup ecosystem.",
      0.31),

    u("Purdue University", "United States", 106, 62,
      "Engineering|Computer Science|Agriculture|Business|Economics|Arts|Social Science|Data Science|Mathematics|Physics|Pharmacy|Education",
      30000, 16000, "purdue.edu", "https://www.purdue.edu",
      7.5, 6.5, 88, True, "Purdue Graduate School Fellowship", 12,
      "Purdue University is a leading public research university in West Lafayette, Indiana, renowned for its engineering, agriculture, and business programmes. It has a strong tradition of astronaut graduates and aerospace research.",
      0.58),

    u("Ohio State University", "United States", 171, 80,
      "Engineering|Computer Science|Business|Medicine|Law|Economics|Arts|Social Science|Data Science|Architecture|Education|Agriculture|Public Health|Finance",
      35000, 17000, "osu.edu", "https://www.osu.edu",
      7.5, 6.5, 88, False, "OSU Graduate Scholarship", 12,
      "Ohio State University is one of the largest and most comprehensive public universities in the United States. It excels in business, medicine, engineering, and the social sciences, with top-ranked programmes across many disciplines.",
      0.54),

    u("University of Minnesota", "United States", 185, 85,
      "Engineering|Computer Science|Business|Medicine|Law|Economics|Arts|Social Science|Data Science|Architecture|Education|Agriculture|Public Health|Environmental",
      34000, 17000, "umn.edu", "https://www.umn.edu",
      7.5, 6.5, 88, False, "UMN Graduate School Fellowship", 12,
      "The University of Minnesota is a major research university with strengths in engineering, medicine, and the natural sciences. It is classified as a very high research activity university and is known for its innovations in agriculture and medicine.",
      0.54),

    u("University of Wisconsin-Madison", "United States", 100, 58,
      "Engineering|Computer Science|Business|Medicine|Law|Economics|Arts|Social Science|Data Science|Architecture|Agriculture|Environmental|Education|Public Health",
      36000, 17000, "wisc.edu", "https://www.wisc.edu",
      7.5, 6.5, 92, False, "UW-Madison Graduate Fellowship", 12,
      "The University of Wisconsin-Madison is a world-class public research university known for the Wisconsin Idea — the principle that education should improve people's lives beyond the classroom. It excels in biological sciences, engineering, and the social sciences.",
      0.57),

    u("University of Florida", "United States", 170, 78,
      "Engineering|Computer Science|Business|Medicine|Law|Economics|Arts|Social Science|Data Science|Architecture|Agriculture|Environmental|Education|Pharmacy",
      30000, 16000, "ufl.edu", "https://www.ufl.edu",
      7.5, 6.5, 88, False, "UF Graduate School Scholarship", 12,
      "The University of Florida is a leading public research university and the flagship institution of Florida's state university system. It is known for its strengths in agriculture, engineering, and health sciences.",
      0.31),

    u("University of Southern California", "United States", 113, 66,
      "Computer Science|Engineering|Business|Law|Cinema|Arts|Social Science|Data Science|Architecture|Environmental|Education|Public Policy|Economics|Communication",
      66000, 22000, "usc.edu", "https://www.usc.edu",
      8.0, 6.5, 100, True, "USC Graduate Scholarship", 12,
      "The University of Southern California is a leading private research university in Los Angeles, known for its strengths in film, business, engineering, and the arts. Its location in Hollywood makes it the top choice for aspiring filmmakers.",
      0.16),

    u("New York University", "United States", 39, 25,
      "Computer Science|Business|Law|Arts|Social Science|Data Science|Economics|Finance|Education|Public Health|Architecture|Environmental|Nursing|Medicine",
      58000, 22000, "nyu.edu", "https://www.nyu.edu",
      8.0, 7.0, 100, False, "NYU Graduate Fellowship", 12,
      "New York University is a leading private research university in the heart of New York City, known for its strengths in business, law, and the arts. Its urban setting provides unparalleled access to internships, cultural events, and professional networks.",
      0.16),

    u("Boston University", "United States", 113, 66,
      "Computer Science|Engineering|Business|Law|Arts|Social Science|Data Science|Economics|Finance|Education|Public Health|Architecture|Medicine|Communications",
      62000, 22000, "bu.edu", "https://www.bu.edu",
      7.5, 6.5, 100, True, "BU Dean's Fellowship", 12,
      "Boston University is a large, comprehensive research university in the heart of Boston, with strengths in engineering, medicine, business, and communications. Its location in Boston's academic hub provides excellent networking and career opportunities.",
      0.57),

    u("Northeastern University", "United States", 344, 128,
      "Computer Science|Engineering|Business|Law|Arts|Social Science|Data Science|Economics|Finance|Health Sciences|Architecture|Design|Public Health",
      58000, 22000, "northeastern.edu", "https://www.northeastern.edu",
      7.5, 6.5, 100, False, "Northeastern Merit Scholarship", 12,
      "Northeastern University in Boston is renowned for its cooperative education programme, which integrates classroom study with professional work experience. It is a top destination for students in computer science, engineering, and business.",
      0.20),

    u("Tufts University", "United States", 278, 112,
      "Computer Science|Engineering|Business|Law|Arts|Social Science|Data Science|Economics|International Relations|Medicine|Architecture|Environmental|Education",
      67000, 22000, "tufts.edu", "https://www.tufts.edu",
      8.0, 7.0, 100, False, "Tufts Graduate School Scholarship", 12,
      "Tufts University is a top research university near Boston, known for its strengths in international relations, engineering, veterinary medicine, and the liberal arts. It has a strong focus on civic engagement and global citizenship.",
      0.11),

    u("Case Western Reserve University", "United States", 306, 118,
      "Engineering|Computer Science|Medicine|Law|Business|Economics|Arts|Social Science|Data Science|Nursing|Dentistry|Environmental|Mathematics",
      55000, 20000, "case.edu", "https://www.case.edu",
      8.0, 6.5, 100, True, "CWRU Provost Fellowship", 12,
      "Case Western Reserve University in Cleveland, Ohio, is a leading private research university with particular strengths in medicine, engineering, and law. It has one of the highest funded research budgets among private US universities.",
      0.30),

    u("Washington University in St. Louis", "United States", 55, 32,
      "Computer Science|Engineering|Business|Medicine|Law|Economics|Arts|Social Science|Data Science|Architecture|Environmental|Education|Biomedical Engineering|Finance",
      62000, 20000, "wustl.edu", "https://www.wustl.edu",
      8.5, 7.0, 100, False, "WashU Graduate Fellowship", 12,
      "Washington University in St. Louis is a leading private research university known for its strength in medicine, business, engineering, and the arts. It consistently ranks among the top 15 universities in the United States.",
      0.13),

    u("University of Washington", "United States", 85, 50,
      "Computer Science|Engineering|Medicine|Business|Law|Economics|Arts|Social Science|Data Science|Environmental|Public Health|Education|Architecture|Nursing",
      37000, 20000, "washington.edu", "https://www.washington.edu",
      7.5, 6.5, 92, True, "UW Graduate School Fellowship", 12,
      "The University of Washington is a world-class public research university in Seattle, renowned for its computer science and engineering programmes. Its location in the Pacific Northwest puts it at the centre of the global tech industry.",
      0.52),

    u("University of California San Diego", "United States", 62, 36,
      "Computer Science|Engineering|Medicine|Business|Economics|Arts|Social Science|Data Science|Environmental|Mathematics|Physics|Bioengineering|Public Health",
      44000, 22000, "ucsd.edu", "https://www.ucsd.edu",
      8.0, 7.0, 100, True, "UCSD Graduate Fellowship", 12,
      "UC San Diego is a world-class research university in La Jolla, California, renowned for its strengths in science, engineering, and medicine. It is ranked among the top 20 public universities globally.",
      0.30),

    u("University of California Davis", "United States", 149, 72,
      "Engineering|Computer Science|Medicine|Business|Economics|Arts|Social Science|Data Science|Environmental|Agriculture|Veterinary|Law|Education",
      33000, 18000, "ucdavis.edu", "https://www.ucdavis.edu",
      7.5, 6.5, 88, False, "UC Davis Graduate Fellowship", 12,
      "UC Davis is a leading public research university in the Sacramento Valley, renowned for its programmes in agriculture, veterinary medicine, and environmental science. It has strong ties to California's agricultural and food industries.",
      0.46),


    # ──────────────────────────────────────────────────────────────────────────
    # CANADA (13 universities)
    # ──────────────────────────────────────────────────────────────────────────
    u("University of Toronto", "Canada", 21, 13,
      "Computer Science|Engineering|Medicine|Business|Law|Economics|Arts|Social Science|Data Science|Architecture|Environmental|Education|Finance|Mathematics|Public Health",
      40000, 16000, "utoronto.ca", "https://www.utoronto.ca",
      7.5, 6.5, 100, False, "University of Toronto Fellowship", 12,
      "The University of Toronto is Canada's top university and a world leader in research and innovation. It is consistently ranked among the global top 25 and excels across every academic discipline.",
      0.43),

    u("University of British Columbia", "Canada", 38, 24,
      "Computer Science|Engineering|Medicine|Business|Law|Economics|Arts|Social Science|Data Science|Architecture|Environmental|Education|Finance|Forestry|Nursing",
      36000, 18000, "ubc.ca", "https://www.ubc.ca",
      7.5, 6.5, 100, False, "UBC International Leader of Tomorrow Award", 12,
      "The University of British Columbia is Canada's second-ranked university and a globally recognised research institution. Located in Vancouver, it is known for its stunning campus, diverse community, and strength in science and sustainability.",
      0.52),

    u("McGill University", "Canada", 46, 28,
      "Computer Science|Engineering|Medicine|Business|Law|Economics|Arts|Social Science|Data Science|Architecture|Environmental|Music|Dentistry|Nursing",
      28000, 16000, "mcgill.ca", "https://www.mcgill.ca",
      7.5, 6.5, 100, False, "McGill Scholarship and Student Aid", 12,
      "McGill University is Canada's most internationally recognised university, with a bilingual campus in Montreal. It is known for its rigorous academic standards and has produced the most Nobel laureates of any Canadian institution.",
      0.46),

    u("University of Waterloo", "Canada", 149, 72,
      "Computer Science|Engineering|Mathematics|Business|Economics|Environmental|Data Science|Quantum Computing|Architecture|Arts|Science",
      36000, 14000, "uwaterloo.ca", "https://www.uwaterloo.ca",
      7.5, 7.0, 100, True, "Waterloo Graduate Scholarship", 12,
      "The University of Waterloo is Canada's top engineering and technology university, renowned for the world's largest post-secondary cooperative education programme. It is considered Canada's MIT and has strong ties to Silicon Valley.",
      0.53),

    u("McMaster University", "Canada", 176, 82,
      "Engineering|Computer Science|Medicine|Business|Economics|Arts|Social Science|Data Science|Environmental|Health Sciences|Nursing|Mathematics",
      32000, 14000, "mcmaster.ca", "https://www.mcmaster.ca",
      7.0, 6.5, 88, False, "McMaster Graduate Scholarship", 12,
      "McMaster University in Hamilton, Ontario, is a leading research-intensive university with a particular strength in health sciences, engineering, and business. It pioneered problem-based learning in medical education.",
      0.60),

    u("Queen's University", "Canada", 209, 90,
      "Engineering|Computer Science|Business|Economics|Law|Arts|Social Science|Data Science|Environmental|Health Sciences|Education|Mathematics|Finance",
      38000, 14000, "queensu.ca", "https://www.queensu.ca",
      7.5, 7.0, 100, False, "Queen's University Awards", 12,
      "Queen's University in Kingston, Ontario, is one of Canada's most respected universities, known for its collegiate atmosphere and excellence in business, engineering, and the social sciences. Its Smith School of Business is highly regarded.",
      0.42),

    u("Western University", "Canada", 258, 105,
      "Computer Science|Engineering|Business|Medicine|Law|Economics|Arts|Social Science|Data Science|Education|Dentistry|Nursing|Finance",
      30000, 14000, "uwo.ca", "https://www.uwo.ca",
      7.0, 6.5, 88, False, "Western Graduate Research Scholarship", 12,
      "Western University in London, Ontario, is a leading Canadian research university known for its Ivey Business School, medical school, and strong campus community. It provides an exceptional student experience in a mid-sized city.",
      0.58),

    u("University of Calgary", "Canada", 242, 103,
      "Engineering|Computer Science|Business|Medicine|Law|Economics|Arts|Social Science|Data Science|Environmental|Education|Nursing|Finance|Architecture",
      28000, 14000, "ucalgary.ca", "https://www.ucalgary.ca",
      7.0, 6.5, 88, False, "Graduate Award Competition", 12,
      "The University of Calgary is a leading Canadian research university located in the heart of Calgary's growing energy and technology sector. It excels in engineering, business, medicine, and environmental studies.",
      0.60),

    u("University of Alberta", "Canada", 111, 64,
      "Engineering|Computer Science|Business|Medicine|Law|Economics|Arts|Social Science|Data Science|Environmental|Agriculture|Nursing|Education|Pharmacy",
      28000, 14000, "ualberta.ca", "https://www.ualberta.ca",
      7.0, 6.5, 88, False, "Alberta Graduate Excellence Scholarship", 12,
      "The University of Alberta is one of Canada's top research universities, consistently ranked in the global top 150. It is a flagship institution for engineering, computing, and oil-sands research.",
      0.58),

    u("Dalhousie University", "Canada", 298, 115,
      "Engineering|Computer Science|Business|Medicine|Law|Economics|Arts|Social Science|Data Science|Environmental|Agriculture|Nursing|Architecture|Dentistry",
      24000, 14000, "dal.ca", "https://www.dal.ca",
      7.0, 6.5, 88, False, "Dalhousie International Scholarship", 12,
      "Dalhousie University in Halifax, Nova Scotia, is one of Canada's leading research universities with a beautiful coastal setting. It has particular strengths in ocean sciences, medicine, and engineering.",
      0.65),

    u("Simon Fraser University", "Canada", 339, 126,
      "Computer Science|Engineering|Business|Economics|Arts|Social Science|Data Science|Environmental|Education|Mathematics|Science",
      22000, 18000, "sfu.ca", "https://www.sfu.ca",
      7.0, 6.5, 88, False, "SFU Graduate Scholarship", 12,
      "Simon Fraser University in Burnaby, British Columbia, is a leading Canadian research university known for its innovative programmes in computing, engineering, and the social sciences. Its campuses in metropolitan Vancouver provide excellent career opportunities.",
      0.60),

    u("University of Ottawa", "Canada", 292, 113,
      "Computer Science|Engineering|Business|Law|Economics|Arts|Social Science|Data Science|Environmental|Medicine|Education|Nursing|Public Health",
      26000, 15000, "uottawa.ca", "https://www.uottawa.ca",
      7.0, 6.5, 88, False, "Excellence Scholarship", 12,
      "The University of Ottawa is Canada's largest bilingual university, situated in the heart of the nation's capital. It excels in law, social sciences, and health sciences, with strong connections to the federal government.",
      0.63),


    # ──────────────────────────────────────────────────────────────────────────
    # AUSTRALIA (13 universities)
    # ──────────────────────────────────────────────────────────────────────────
    u("Australian National University", "Australia", 30, 19,
      "Computer Science|Engineering|Medicine|Business|Law|Economics|Arts|Social Science|Data Science|Environmental|Public Policy|Mathematics|Physics",
      42000, 18000, "anu.edu.au", "https://www.anu.edu.au",
      7.5, 7.0, 100, False, "ANU Chancellor's International Scholarship", 12,
      "ANU is Australia's top-ranked university and a world leader in research and policy, located in the national capital Canberra. It excels in the social sciences, science, and public policy.",
      0.35),

    u("University of Melbourne", "Australia", 14, 9,
      "Computer Science|Engineering|Medicine|Business|Law|Economics|Arts|Social Science|Data Science|Architecture|Environmental|Education|Veterinary|Dentistry|Finance",
      40000, 20000, "unimelb.edu.au", "https://www.unimelb.edu.au",
      7.5, 7.0, 100, False, "Melbourne International Undergraduate Scholarship", 12,
      "The University of Melbourne is Australia's second-ranked university and a member of the Group of Eight, known for its research excellence and comprehensive range of programmes. It is the highest ranked university in the southern hemisphere.",
      0.70),

    u("University of Sydney", "Australia", 18, 11,
      "Computer Science|Engineering|Medicine|Business|Law|Economics|Arts|Social Science|Data Science|Architecture|Environmental|Education|Veterinary|Dentistry|Nursing",
      42000, 20000, "sydney.edu.au", "https://www.sydney.edu.au",
      7.5, 7.0, 100, False, "Sydney Scholars Award", 12,
      "The University of Sydney is Australia's oldest university, founded in 1850, and a member of the prestigious Group of Eight. It is consistently ranked among the world's top 20 universities.",
      0.30),

    u("UNSW Sydney", "Australia", 19, 12,
      "Computer Science|Engineering|Medicine|Business|Law|Economics|Arts|Social Science|Data Science|Architecture|Environmental|Education|Finance|Mathematics",
      42000, 20000, "unsw.edu.au", "https://www.unsw.edu.au",
      7.5, 7.0, 100, False, "UNSW Scientia Scholarship", 12,
      "UNSW Sydney is a member of the Group of Eight and a world leader in engineering, business, and law. It is located in the vibrant coastal city of Sydney and has strong connections with industry and government.",
      0.36),

    u("Monash University", "Australia", 42, 26,
      "Computer Science|Engineering|Medicine|Business|Law|Economics|Arts|Social Science|Data Science|Architecture|Environmental|Education|Pharmacy|Nursing",
      36000, 18000, "monash.edu", "https://www.monash.edu",
      7.5, 6.5, 100, False, "Monash International Merit Scholarship", 12,
      "Monash University is a leading Australian research university and member of the Group of Eight, with campuses in Australia, Malaysia, and South Africa. It is known for its innovations in medicine, engineering, and pharmacy.",
      0.51),

    u("University of Queensland", "Australia", 43, 27,
      "Computer Science|Engineering|Medicine|Business|Law|Economics|Arts|Social Science|Data Science|Environmental|Agriculture|Veterinary|Pharmacy|Education",
      36000, 16000, "uq.edu.au", "https://www.uq.edu.au",
      7.0, 6.5, 92, False, "UQ International Scholarship", 12,
      "The University of Queensland is a member of the Group of Eight and one of Australia's most prestigious research institutions. It excels in environmental science, medicine, and business in Brisbane's subtropical setting.",
      0.51),

    u("University of Adelaide", "Australia", 89, 52,
      "Engineering|Computer Science|Medicine|Business|Economics|Arts|Social Science|Data Science|Environmental|Agriculture|Law|Education|Dentistry",
      36000, 14000, "adelaide.edu.au", "https://www.adelaide.edu.au",
      7.0, 6.5, 88, False, "Adelaide Scholarship International", 12,
      "The University of Adelaide is one of Australia's oldest and most prestigious universities, a member of the Group of Eight. It is known for its research into sustainable agriculture, engineering, and health sciences.",
      0.54),

    u("University of Western Australia", "Australia", 72, 43,
      "Engineering|Computer Science|Medicine|Business|Economics|Arts|Social Science|Data Science|Environmental|Agriculture|Law|Education|Dentistry",
      36000, 16000, "uwa.edu.au", "https://www.uwa.edu.au",
      7.0, 6.5, 88, False, "UWA International Scholarship", 12,
      "The University of Western Australia is a member of the Group of Eight and Perth's leading research university. It is known for its stunning campus on the Swan River and excellence in mining, engineering, and the sciences.",
      0.52),

    u("Macquarie University", "Australia", 195, 87,
      "Computer Science|Engineering|Business|Economics|Arts|Social Science|Data Science|Environmental|Law|Education|Finance|Media|Actuarial Studies",
      32000, 20000, "mq.edu.au", "https://www.mq.edu.au",
      7.0, 6.5, 88, False, "Macquarie Vice-Chancellor's International Scholarship", 12,
      "Macquarie University in Sydney is a dynamic research university known for its innovative programmes in business, linguistics, and cognitive science. It has a strong focus on professional development and industry engagement.",
      0.60),

    u("University of Technology Sydney", "Australia", 148, 71,
      "Computer Science|Engineering|Business|Economics|Design|Data Science|Law|Education|Finance|Architecture|Health Sciences|Nursing",
      34000, 20000, "uts.edu.au", "https://www.uts.edu.au",
      7.0, 6.5, 88, False, "UTS President's Scholarship", 12,
      "UTS is one of Australia's leading universities of technology, known for its industry-facing curriculum and state-of-the-art city campus. It excels in engineering, design, and business.",
      0.60),

    u("RMIT University", "Australia", 224, 97,
      "Engineering|Computer Science|Business|Design|Architecture|Arts|Data Science|Social Science|Education|Environmental|Health Sciences",
      32000, 20000, "rmit.edu.au", "https://www.rmit.edu.au",
      7.0, 6.5, 88, False, "", 12,
      "RMIT University in Melbourne is a global university of technology, design, and enterprise, known for its strong focus on applied learning and industry connections. It is the largest university in Australia by enrolment.",
      0.70),

    u("Curtin University", "Australia", 218, 94,
      "Engineering|Computer Science|Business|Economics|Arts|Social Science|Data Science|Environmental|Law|Education|Architecture|Health Sciences|Mining",
      28000, 16000, "curtin.edu.au", "https://www.curtin.edu.au",
      7.0, 6.5, 85, False, "Curtin International Scholarship", 12,
      "Curtin University in Perth is Australia's largest university in the west, known for its strengths in engineering, mining, and health sciences. It has strong industry ties to Western Australia's resources sector.",
      0.70),


    # ──────────────────────────────────────────────────────────────────────────
    # GERMANY (13 universities)
    # ──────────────────────────────────────────────────────────────────────────
    u("Technical University of Munich", "Germany", 37, 23,
      "Engineering|Computer Science|Mathematics|Physics|Business|Economics|Data Science|Architecture|Environmental|Bioengineering|Aerospace|Mechanical Engineering",
      3000, 14000, "tum.de", "https://www.tum.de",
      7.5, 7.0, 95, True, "TUM Global Incentive Fund", 12,
      "TU Munich is Germany's top technical university and consistently one of Europe's leading research institutions. It has strong connections with global industry and is a hub for technology and innovation in the Munich region.",
      0.10),

    u("LMU Munich", "Germany", 54, 31,
      "Medicine|Computer Science|Physics|Economics|Law|Arts|Social Science|Mathematics|Environmental|Philosophy|Data Science|Business",
      3000, 14000, "lmu.de", "https://www.lmu.de",
      7.5, 7.0, 95, False, "LMU International Scholarship", 12,
      "LMU Munich is one of Europe's most prestigious universities, with strengths in medicine, natural sciences, and the humanities. It is a gateway to Germany's vibrant research and innovation ecosystem.",
      0.20),

    u("Heidelberg University", "Germany", 47, 29,
      "Medicine|Computer Science|Physics|Economics|Law|Arts|Social Science|Mathematics|Environmental|Philosophy|Data Science|Chemistry|Biology",
      3000, 12000, "uni-heidelberg.de", "https://www.uni-heidelberg.de",
      7.5, 7.0, 95, False, "Heidelberg University Scholarship", 12,
      "Heidelberg University, founded in 1386, is Germany's oldest university and one of Europe's most storied academic institutions. It has produced numerous Nobel laureates and excels in medicine, natural sciences, and the humanities.",
      0.25),

    u("Humboldt University Berlin", "Germany", 120, 68,
      "Arts|Social Science|Economics|Law|Medicine|Computer Science|Mathematics|Physics|History|Philosophy|Education|Environmental",
      3000, 15000, "hu-berlin.de", "https://www.hu-berlin.de",
      7.0, 7.0, 95, False, "Humboldt Foundation Scholarship", 12,
      "Humboldt University Berlin is one of Germany's most important research universities, with a 200-year history of pioneering academic excellence. It is known for its contributions to philosophy, economics, and the natural sciences.",
      0.30),

    u("Free University Berlin", "Germany", 98, 57,
      "Arts|Social Science|Economics|Law|Medicine|Computer Science|Mathematics|Physics|History|Philosophy|Environmental|Political Science",
      3000, 15000, "fu-berlin.de", "https://www.fu-berlin.de",
      7.0, 7.0, 95, False, "Dahlem Research School Scholarship", 12,
      "The Free University of Berlin is a leading German research university known for its excellence in the humanities, social sciences, and natural sciences. It has a vibrant, cosmopolitan campus community in western Berlin.",
      0.30),

    u("RWTH Aachen University", "Germany", 106, 62,
      "Engineering|Computer Science|Mathematics|Physics|Business|Economics|Data Science|Architecture|Environmental|Mechanical Engineering|Bioengineering",
      3000, 12000, "rwth-aachen.de", "https://www.rwth-aachen.de",
      7.5, 7.0, 95, True, "RWTH Scholarship", 12,
      "RWTH Aachen is Germany's largest technical university and one of Europe's most prestigious engineering schools. It has exceptionally strong ties to major German and international industry partners.",
      0.20),

    u("Karlsruhe Institute of Technology", "Germany", 116, 67,
      "Engineering|Computer Science|Mathematics|Physics|Business|Economics|Data Science|Architecture|Environmental|Mechanical Engineering|Electrical Engineering",
      3000, 12000, "kit.edu", "https://www.kit.edu",
      7.5, 7.0, 95, True, "KIT Scholarship", 12,
      "KIT (Karlsruhe Institute of Technology) is one of Germany's top research universities and a major centre for engineering, natural sciences, and business. It was created from a merger of the University of Karlsruhe and a national research centre.",
      0.22),

    u("University of Stuttgart", "Germany", 296, 115,
      "Engineering|Computer Science|Mathematics|Physics|Business|Economics|Data Science|Architecture|Environmental|Aerospace|Mechanical Engineering|Automotive Engineering",
      3000, 12000, "uni-stuttgart.de", "https://www.uni-stuttgart.de",
      7.0, 7.0, 90, True, "", 12,
      "The University of Stuttgart is a leading technical university in the heart of Baden-Württemberg's high-tech corridor. It is famous for its engineering programmes and close links to companies like Daimler, Bosch, and Porsche.",
      0.35),

    u("University of Hamburg", "Germany", 176, 82,
      "Arts|Social Science|Economics|Law|Medicine|Computer Science|Mathematics|Physics|Environmental|Business|Data Science|Education",
      3000, 14000, "uni-hamburg.de", "https://www.uni-hamburg.de",
      7.0, 7.0, 90, False, "", 12,
      "The University of Hamburg is one of Germany's largest and most prestigious universities, with particular strengths in climate research, natural sciences, and the humanities. It is situated in one of Europe's most vibrant port cities.",
      0.35),

    u("University of Cologne", "Germany", 232, 99,
      "Arts|Social Science|Economics|Law|Medicine|Computer Science|Mathematics|Physics|Environmental|Business|Data Science|Education|Philosophy",
      3000, 12000, "uni-koeln.de", "https://www.uni-koeln.de",
      7.0, 7.0, 90, False, "", 12,
      "The University of Cologne, founded in 1388, is one of Germany's oldest and largest universities, with a broad range of programmes in the natural and social sciences. Its business school is one of the most prestigious in Germany.",
      0.35),

    u("Technical University of Berlin", "Germany", 154, 74,
      "Engineering|Computer Science|Mathematics|Physics|Business|Economics|Data Science|Architecture|Environmental|Mechanical Engineering|Electrical Engineering",
      3000, 15000, "tu-berlin.de", "https://www.tu-berlin.de",
      7.0, 7.0, 90, True, "TU Berlin Scholarship", 12,
      "TU Berlin is one of Germany's most important technical universities, located in the heart of the capital. It has a strong focus on engineering and natural sciences and is closely connected to Berlin's thriving start-up ecosystem.",
      0.30),

    u("University of Freiburg", "Germany", 165, 77,
      "Medicine|Computer Science|Physics|Economics|Law|Arts|Social Science|Mathematics|Environmental|Philosophy|Data Science|Biology|Chemistry",
      3000, 12000, "uni-freiburg.de", "https://www.uni-freiburg.de",
      7.0, 7.0, 90, False, "Freiburg University Scholarship", 12,
      "The University of Freiburg is one of Germany's oldest and most distinguished universities, situated in the beautiful Black Forest region. It is known for its excellence in medicine, natural sciences, and the humanities.",
      0.30),


    # ──────────────────────────────────────────────────────────────────────────
    # NETHERLANDS (9 universities)
    # ──────────────────────────────────────────────────────────────────────────
    u("Delft University of Technology", "Netherlands", 47, 29,
      "Engineering|Computer Science|Architecture|Mathematics|Physics|Data Science|Environmental|Aerospace|Mechanical Engineering|Electrical Engineering|Business",
      18000, 14000, "tudelft.nl", "https://www.tudelft.nl",
      7.5, 7.0, 100, False, "TU Delft Excellence Scholarship", 12,
      "TU Delft is the Netherlands' leading technical university and one of Europe's best. It is globally recognised for its research in aerospace, hydraulic engineering, and computer science.",
      0.30),

    u("University of Amsterdam", "Netherlands", 61, 35,
      "Computer Science|Business|Economics|Law|Arts|Social Science|Data Science|Environmental|Medicine|Mathematics|Philosophy|Political Science|Finance",
      18000, 14000, "uva.nl", "https://www.uva.nl",
      7.5, 7.0, 100, False, "UvA Scholarship", 12,
      "The University of Amsterdam is the Netherlands' largest research university, situated at the cultural heart of one of Europe's most cosmopolitan cities. It excels in social sciences, economics, law, and the humanities.",
      0.35),

    u("Leiden University", "Netherlands", 128, 72,
      "Computer Science|Business|Economics|Law|Arts|Social Science|Data Science|Environmental|Medicine|Mathematics|History|International Relations|Science",
      18000, 14000, "universiteitleiden.nl", "https://www.universiteitleiden.nl",
      7.5, 7.0, 100, False, "Leiden University Excellence Scholarship", 12,
      "Leiden University, the Netherlands' oldest university, has a rich 450-year history of groundbreaking research and a Nobel Prize tradition. It is particularly renowned for its law school and social sciences.",
      0.35),

    u("Erasmus University Rotterdam", "Netherlands", 172, 81,
      "Business|Economics|Law|Social Science|Data Science|Environmental|Medicine|Mathematics|Finance|Management|Public Health|International Relations",
      16000, 14000, "eur.nl", "https://www.eur.nl",
      7.0, 7.0, 100, False, "Erasmus Trustfonds Scholarship", 12,
      "Erasmus University Rotterdam is a world-leading research university named after the great Dutch humanist scholar. It is renowned for its Erasmus School of Economics and Rotterdam School of Management.",
      0.40),

    u("Utrecht University", "Netherlands", 87, 51,
      "Computer Science|Business|Economics|Law|Arts|Social Science|Data Science|Environmental|Medicine|Mathematics|Veterinary|Pharmacy|Education",
      18000, 14000, "uu.nl", "https://www.uu.nl",
      7.5, 7.0, 100, False, "Utrecht Excellence Scholarship", 12,
      "Utrecht University is the Netherlands' largest university and a top global research institution with a rich 380-year history. It has particular strengths in life sciences, social sciences, and the humanities.",
      0.35),

    u("Radboud University", "Netherlands", 200, 89,
      "Computer Science|Business|Economics|Law|Arts|Social Science|Data Science|Environmental|Medicine|Mathematics|Philosophy|Theology|Natural Sciences",
      16000, 13000, "ru.nl", "https://www.ru.nl",
      7.0, 7.0, 95, False, "Radboud Scholarship Programme", 12,
      "Radboud University in Nijmegen is one of the leading academic communities in the Netherlands, known for its cutting-edge research in the neurosciences, social sciences, and philosophy.",
      0.40),

    u("Eindhoven University of Technology", "Netherlands", 149, 73,
      "Engineering|Computer Science|Mathematics|Physics|Data Science|Architecture|Environmental|Mechanical Engineering|Electrical Engineering|Business|Design",
      18000, 13000, "tue.nl", "https://www.tue.nl",
      7.5, 7.0, 100, True, "TU/e Excellence Scholarship", 12,
      "Eindhoven University of Technology (TU/e) is a world-class technical university in the heart of the Brainport Eindhoven region, Europe's top innovation hub. It has close ties to Philips, ASML, and other global tech leaders.",
      0.28),

    u("VU Amsterdam", "Netherlands", 245, 104,
      "Computer Science|Business|Economics|Law|Arts|Social Science|Data Science|Environmental|Medicine|Mathematics|Philosophy|Education|Theology",
      17000, 14000, "vu.nl", "https://www.vu.nl",
      7.0, 7.0, 95, False, "VU Fellowship Programme", 12,
      "VU Amsterdam (Vrije Universiteit) is a research university at the heart of Amsterdam, known for its open and diverse community. It has particular strengths in the life sciences, social sciences, and business.",
      0.45),


    # ──────────────────────────────────────────────────────────────────────────
    # FRANCE (9 universities)
    # ──────────────────────────────────────────────────────────────────────────
    u("Sciences Po Paris", "France", 244, 103,
      "Economics|Finance|Business|Law|Social Science|Public Health|Data Science|Political Science|International Relations|Sociology|Management|Arts",
      18000, 16000, "sciencespo.fr", "https://www.sciencespo.fr",
      7.5, 7.0, 100, False, "Émile Boutmy Scholarship", 12,
      "Sciences Po Paris is one of France's most prestigious grandes écoles, known worldwide for its excellence in political science, law, international affairs, and economics. It is the breeding ground for France's political elite.",
      0.25),

    u("HEC Paris", "France", 69, 40,
      "Business|Finance|Economics|Management|Data Science|Social Science|Law|Marketing|Entrepreneurship|Strategy",
      50000, 16000, "hec.edu", "https://www.hec.edu",
      8.0, 7.0, 105, True, "HEC Foundation Scholarship", 12,
      "HEC Paris is Europe's top-ranked business school and a global leader in management education. It produces graduates who lead major corporations and institutions across the world.",
      0.12),

    u("Sorbonne University", "France", 59, 34,
      "Arts|Social Science|Economics|Law|Medicine|Computer Science|Mathematics|Physics|History|Philosophy|Environmental|Literature|Linguistics",
      6000, 16000, "sorbonne-universite.fr", "https://www.sorbonne-universite.fr",
      7.0, 7.0, 95, False, "Sorbonne Scholarship", 12,
      "Sorbonne University is one of the world's oldest and most prestigious institutions, with a legacy of academic excellence dating back to 1257. It is a leading European research university renowned for the sciences, humanities, and medicine.",
      0.30),

    u("Paris-Saclay University", "France", 15, 10,
      "Engineering|Computer Science|Mathematics|Physics|Business|Economics|Data Science|Environmental|Chemistry|Biology|Medicine",
      4000, 14000, "universite-paris-saclay.fr", "https://www.universite-paris-saclay.fr",
      7.5, 7.0, 100, False, "Paris-Saclay International Master's Scholarship", 12,
      "Paris-Saclay University is a world-class research university located south of Paris, formed from a merger of some of France's most prestigious grandes écoles. It ranks among the world's top 15 in the natural sciences.",
      0.30),

    u("Ecole Polytechnique", "France", 42, 26,
      "Engineering|Computer Science|Mathematics|Physics|Data Science|Environmental|Economics|Architecture|Aerospace|Applied Mathematics",
      16000, 16000, "polytechnique.edu", "https://www.polytechnique.edu",
      8.0, 7.0, 100, True, "Polytechnique International Scholarship", 12,
      "École Polytechnique (X) is France's most elite grande école, known for its rigorous scientific education and producing some of the world's most influential engineers and scientists. It has a long military tradition and close ties to the French state.",
      0.08),

    u("University of Paris", "France", 262, 107,
      "Arts|Social Science|Economics|Law|Medicine|Computer Science|Mathematics|Physics|Environmental|Philosophy|Education|Neuroscience",
      4000, 16000, "u-paris.fr", "https://www.u-paris.fr",
      7.0, 7.0, 95, False, "", 12,
      "Université Paris Cité is a leading French research university situated at the heart of Paris, formed from the merger of Paris Descartes and Paris Diderot. It excels in medicine, health sciences, and social sciences.",
      0.35),

    u("Grenoble Alpes University", "France", 351, 130,
      "Engineering|Computer Science|Mathematics|Physics|Business|Economics|Data Science|Environmental|Social Science|Arts|Architecture",
      4000, 12000, "univ-grenoble-alpes.fr", "https://www.univ-grenoble-alpes.fr",
      7.0, 6.5, 90, False, "Grenoble Excellence Scholarship", 12,
      "Grenoble Alpes University is a leading French research university, particularly strong in engineering and the natural sciences. Its location in the Alps makes it a centre for environmental research and innovation.",
      0.40),

    u("CentraleSupélec", "France", 333, 122,
      "Engineering|Computer Science|Mathematics|Physics|Data Science|Environmental|Business|Economics|Electrical Engineering|Mechanical Engineering",
      15000, 15000, "centralesupelec.fr", "https://www.centralesupelec.fr",
      8.0, 7.0, 100, True, "CS International Scholarship", 12,
      "CentraleSupélec is one of France's most prestigious engineering grandes écoles, produced from the merger of Centrale Paris and Supélec. It is renowned for producing highly versatile engineers with strong mathematical and scientific foundations.",
      0.15),


    # ──────────────────────────────────────────────────────────────────────────
    # IRELAND (5 universities)
    # ──────────────────────────────────────────────────────────────────────────
    u("Trinity College Dublin", "Ireland", 87, 51,
      "Computer Science|Engineering|Business|Economics|Law|Arts|Social Science|Data Science|Environmental|Medicine|Philosophy|Mathematics|Finance",
      25000, 15000, "tcd.ie", "https://www.tcd.ie",
      7.5, 6.5, 100, False, "TCD Ussher Scholarship", 12,
      "Trinity College Dublin is Ireland's oldest and most prestigious university, founded in 1592. It combines centuries of tradition with cutting-edge research, and is known for its exceptional arts, humanities, and science programmes.",
      0.30),

    u("University College Dublin", "Ireland", 181, 83,
      "Computer Science|Engineering|Business|Economics|Law|Arts|Social Science|Data Science|Environmental|Medicine|Agriculture|Architecture|Finance|Education",
      22000, 15000, "ucd.ie", "https://www.ucd.ie",
      7.0, 6.5, 88, False, "UCD Global Scholarship", 12,
      "University College Dublin is Ireland's largest and most internationally engaged university, a member of the prestigious Russell Group equivalent. It is known for its strengths in business, engineering, and the life sciences.",
      0.42),

    u("University of Galway", "Ireland", 250, 106,
      "Computer Science|Engineering|Business|Economics|Law|Arts|Social Science|Data Science|Environmental|Medicine|Marine Science|Education",
      20000, 14000, "universityofgalway.ie", "https://www.universityofgalway.ie",
      7.0, 6.5, 88, False, "Galway International Excellence Scholarship", 12,
      "University of Galway (formerly NUI Galway) is a research-led university on Ireland's Wild Atlantic Way, renowned for its Celtic studies, marine research, and biomedical engineering programmes.",
      0.50),

    u("University College Cork", "Ireland", 303, 118,
      "Computer Science|Engineering|Business|Economics|Law|Arts|Social Science|Data Science|Environmental|Medicine|Food Science|Education|Pharmacy",
      20000, 14000, "ucc.ie", "https://www.ucc.ie",
      7.0, 6.5, 88, False, "", 12,
      "University College Cork is a leading Irish research university known for its strengths in food science, environmental research, and the humanities. It is set in the charming city of Cork.",
      0.52),

    u("University of Limerick", "Ireland", 601, 180,
      "Engineering|Computer Science|Business|Economics|Arts|Social Science|Data Science|Environmental|Education|Law|Health Sciences|Music",
      18000, 14000, "ul.ie", "https://www.ul.ie",
      7.0, 6.5, 85, False, "UL Scholarship", 12,
      "The University of Limerick is a dynamic, industry-focused university renowned for its innovative programmes and strong cooperative education system. It has become a significant centre for technology and medical devices companies in Ireland.",
      0.60),


    # ──────────────────────────────────────────────────────────────────────────
    # SWITZERLAND (5 universities)
    # ──────────────────────────────────────────────────────────────────────────
    u("ETH Zurich", "Switzerland", 7, 5,
      "Engineering|Computer Science|Mathematics|Physics|Data Science|Environmental|Architecture|Chemistry|Biology|Bioengineering|Aerospace|Economics",
      1600, 22000, "ethz.ch", "https://www.ethz.ch",
      8.0, 7.0, 100, True, "ETH Excellence Scholarship", 12,
      "ETH Zurich is Europe's leading science and technology university and consistently one of the world's top 10 institutions. It has produced 22 Nobel laureates and is known for its exceptional research in science, technology, engineering, and mathematics.",
      0.10),

    u("EPFL", "Switzerland", 17, 11,
      "Engineering|Computer Science|Mathematics|Physics|Data Science|Environmental|Architecture|Chemistry|Biology|Bioengineering|Electrical Engineering",
      1600, 22000, "epfl.ch", "https://www.epfl.ch",
      8.0, 7.0, 100, True, "EPFL Excellence Fellowship", 12,
      "EPFL (École Polytechnique Fédérale de Lausanne) is a world-class technical university on the shores of Lake Geneva. It is among Europe's top universities for engineering, computer science, and the natural sciences.",
      0.17),

    u("University of Zurich", "Switzerland", 86, 51,
      "Medicine|Computer Science|Economics|Law|Arts|Social Science|Mathematics|Environmental|Philosophy|Data Science|Business|Veterinary",
      2000, 22000, "uzh.ch", "https://www.uzh.ch",
      7.5, 7.0, 100, False, "UZH Fellowship", 12,
      "The University of Zurich is Switzerland's largest university and a leading European research institution. It is particularly strong in medicine, natural sciences, and the social sciences.",
      0.25),

    u("University of Geneva", "Switzerland", 111, 64,
      "Economics|Law|Arts|Social Science|Medicine|Computer Science|Mathematics|Environmental|Philosophy|International Relations|Data Science|Business",
      2000, 22000, "unige.ch", "https://www.unige.ch",
      7.5, 7.0, 100, False, "University of Geneva Excellence Master Grant", 12,
      "The University of Geneva is Switzerland's second-largest university, situated at the centre of international diplomacy near the UN headquarters. It excels in international law, economics, and the sciences.",
      0.30),

    u("University of Basel", "Switzerland", 149, 73,
      "Medicine|Computer Science|Economics|Law|Arts|Social Science|Mathematics|Environmental|Philosophy|Data Science|Chemistry|Biology|Pharmacy",
      2000, 20000, "unibas.ch", "https://www.unibas.ch",
      7.5, 7.0, 100, False, "Basel Excellence Scholarship", 12,
      "The University of Basel is Switzerland's oldest university, founded in 1460, and a leading institution in the natural sciences, medicine, and the humanities. Its historic setting in one of Europe's great cultural cities makes it a unique place to study.",
      0.35),


    # ──────────────────────────────────────────────────────────────────────────
    # SINGAPORE (5 universities)
    # ──────────────────────────────────────────────────────────────────────────
    u("National University of Singapore", "Singapore", 8, 6,
      "Computer Science|Engineering|Business|Economics|Law|Medicine|Architecture|Arts|Social Science|Data Science|Environmental|Design|Dentistry|Pharmacy|Finance",
      24000, 14000, "nus.edu.sg", "https://www.nus.edu.sg",
      8.0, 7.0, 100, True, "NUS Research Scholarship", 12,
      "NUS is Asia's top-ranked university and consistently one of the world's best, known for its exceptional research and education across engineering, business, law, and medicine. It is at the heart of Singapore's knowledge-based economy.",
      0.17),

    u("Nanyang Technological University", "Singapore", 26, 17,
      "Engineering|Computer Science|Business|Economics|Data Science|Environmental|Mathematics|Physics|Social Science|Arts|Education|Finance|Bioengineering",
      24000, 14000, "ntu.edu.sg", "https://www.ntu.edu.sg",
      8.0, 7.0, 100, True, "NTU Research Scholarship", 12,
      "NTU is one of Asia's leading research-intensive universities and consistently ranked in the global top 30. It is particularly known for engineering, computer science, and business education in a futuristic campus setting.",
      0.22),

    u("Singapore Management University", "Singapore", 511, 165,
      "Business|Economics|Finance|Law|Data Science|Social Science|Management|Accountancy|Marketing|Information Systems",
      30000, 14000, "smu.edu.sg", "https://www.smu.edu.sg",
      7.5, 7.0, 100, False, "SMU Master's Scholarship", 12,
      "Singapore Management University is Singapore's premier business and management university, modelled after the Wharton School. It is known for its practical, real-world focused education and strong industry partnerships.",
      0.25),

    u("Singapore University of Technology and Design", "Singapore", 601, 180,
      "Engineering|Computer Science|Architecture|Design|Data Science|Mathematics|Physics|Environmental|Bioengineering",
      24000, 14000, "sutd.edu.sg", "https://www.sutd.edu.sg",
      7.5, 7.0, 100, True, "SUTD Scholarship", 12,
      "SUTD is Singapore's youngest university and a unique institution that integrates design thinking with engineering and architecture. It was established in collaboration with MIT and has a strong focus on innovation and entrepreneurship.",
      0.20),


    # ──────────────────────────────────────────────────────────────────────────
    # SWEDEN (5 universities)
    # ──────────────────────────────────────────────────────────────────────────
    u("KTH Royal Institute of Technology", "Sweden", 98, 57,
      "Engineering|Computer Science|Mathematics|Physics|Data Science|Architecture|Environmental|Mechanical Engineering|Electrical Engineering|Business|Economics",
      15000, 14000, "kth.se", "https://www.kth.se",
      7.5, 7.0, 100, True, "KTH Scholarship", 12,
      "KTH Royal Institute of Technology is Sweden's largest and most respected technical university. It is consistently ranked among Europe's top technical universities and has strong ties to Sweden's technology industry.",
      0.30),

    u("Lund University", "Sweden", 103, 60,
      "Engineering|Computer Science|Business|Economics|Law|Arts|Social Science|Data Science|Environmental|Medicine|Mathematics|Architecture|Education",
      16000, 14000, "lu.se", "https://www.lu.se",
      7.5, 7.0, 100, False, "Lund University Global Scholarship", 12,
      "Lund University is Sweden's most internationally celebrated university, with 8 faculties and almost 45,000 students from 130 countries. It excels in the sciences, social sciences, and medicine.",
      0.35),

    u("Stockholm University", "Sweden", 167, 79,
      "Computer Science|Business|Economics|Law|Arts|Social Science|Data Science|Environmental|Medicine|Mathematics|Education|Philosophy|History",
      15000, 15000, "su.se", "https://www.su.se",
      7.0, 7.0, 95, False, "Stockholm University Scholarship", 12,
      "Stockholm University is Sweden's third-largest institution and a hub for world-class research, particularly in the natural and social sciences. Located in one of Europe's greenest capitals, it offers a rich student experience.",
      0.40),

    u("Uppsala University", "Sweden", 118, 67,
      "Engineering|Computer Science|Business|Economics|Law|Arts|Social Science|Data Science|Environmental|Medicine|Mathematics|Philosophy|History|Pharmacy",
      16000, 14000, "uu.se", "https://www.uu.se",
      7.5, 7.0, 100, False, "Uppsala University Scholarship", 12,
      "Uppsala University, founded in 1477, is Scandinavia's oldest university and one of Northern Europe's most prestigious research institutions. It has produced generations of leading scholars and has particularly strong medicine, law, and social sciences faculties.",
      0.35),


    # ──────────────────────────────────────────────────────────────────────────
    # JAPAN (5 universities)
    # ──────────────────────────────────────────────────────────────────────────
    u("University of Tokyo", "Japan", 28, 18,
      "Engineering|Computer Science|Medicine|Economics|Law|Arts|Social Science|Data Science|Environmental|Mathematics|Physics|Agriculture|Education",
      8000, 12000, "u-tokyo.ac.jp", "https://www.u-tokyo.ac.jp",
      8.0, 6.5, 88, True, "MEXT Scholarship", 12,
      "The University of Tokyo is Japan's foremost academic institution and one of Asia's top universities. It produces a disproportionate share of Japan's scientific leaders, Nobel laureates, and business executives.",
      0.35),

    u("Kyoto University", "Japan", 46, 28,
      "Engineering|Computer Science|Medicine|Economics|Law|Arts|Social Science|Data Science|Environmental|Mathematics|Physics|Agriculture|Philosophy",
      8000, 11000, "kyoto-u.ac.jp", "https://www.kyoto-u.ac.jp",
      8.0, 6.5, 88, True, "Kyoto University Scholarship", 12,
      "Kyoto University is Japan's second most prestigious university and one of Asia's foremost research institutions. It is known for its free academic culture, creativity, and excellence in the sciences and humanities.",
      0.35),

    u("Osaka University", "Japan", 80, 48,
      "Engineering|Computer Science|Medicine|Economics|Law|Arts|Social Science|Data Science|Environmental|Mathematics|Physics|Dentistry|Pharmacy",
      8000, 11000, "osaka-u.ac.jp", "https://www.osaka-u.ac.jp",
      7.5, 6.5, 85, True, "MEXT Scholarship", 12,
      "Osaka University is a leading Japanese research university with particular strengths in engineering, science, and medicine. It is known for its strong industrial connections and its vibrant, international research community.",
      0.40),

    u("Tokyo Institute of Technology", "Japan", 91, 54,
      "Engineering|Computer Science|Mathematics|Physics|Data Science|Environmental|Mechanical Engineering|Electrical Engineering|Bioengineering|Architecture",
      8000, 12000, "titech.ac.jp", "https://www.titech.ac.jp",
      8.0, 6.5, 88, True, "Tokyo Tech Scholarship", 12,
      "Tokyo Institute of Technology (Tokyo Tech) is Japan's most prestigious technical university, specialising in science and engineering. It is known for producing many of Japan's leading engineers and scientists and for its significant research output.",
      0.25),


    # ──────────────────────────────────────────────────────────────────────────
    # SOUTH KOREA (4 universities)
    # ──────────────────────────────────────────────────────────────────────────
    u("KAIST", "South Korea", 65, 38,
      "Engineering|Computer Science|Mathematics|Physics|Data Science|Environmental|Business|Economics|Bioengineering|Electrical Engineering",
      8000, 12000, "kaist.ac.kr", "https://www.kaist.ac.kr",
      8.0, 7.0, 90, True, "KAIST Scholarship", 12,
      "KAIST (Korea Advanced Institute of Science and Technology) is South Korea's leading science and technology university, consistently ranked among the world's top 100 institutions. It is a hub for research in artificial intelligence, robotics, and bioengineering.",
      0.25),

    u("Seoul National University", "South Korea", 31, 20,
      "Engineering|Computer Science|Business|Economics|Law|Medicine|Arts|Social Science|Data Science|Environmental|Mathematics|Physics|Agriculture|Education",
      7000, 12000, "snu.ac.kr", "https://www.snu.ac.kr",
      8.0, 7.0, 95, True, "SNU Scholarship", 12,
      "Seoul National University is the most prestigious and selective university in South Korea, often called the Harvard of Korea. Its alumni lead Korea's top corporations, government institutions, and research centres.",
      0.15),

    u("POSTECH", "South Korea", 134, 76,
      "Engineering|Computer Science|Mathematics|Physics|Data Science|Environmental|Bioengineering|Mechanical Engineering|Chemical Engineering|Materials Science",
      6000, 11000, "postech.ac.kr", "https://www.postech.ac.kr",
      8.0, 7.0, 90, True, "POSTECH Scholarship", 12,
      "POSTECH (Pohang University of Science and Technology) is South Korea's most research-intensive university, founded by POSCO with a strong focus on science and engineering. It has an extraordinary research-to-student ratio.",
      0.25),

    u("Yonsei University", "South Korea", 56, 33,
      "Engineering|Computer Science|Business|Economics|Law|Medicine|Arts|Social Science|Data Science|Environmental|Mathematics|Education|Theology",
      12000, 12000, "yonsei.ac.kr", "https://www.yonsei.ac.kr",
      7.5, 6.5, 88, False, "Yonsei Scholarship", 12,
      "Yonsei University is one of South Korea's most prestigious private universities and the oldest in the country. It is part of the elite SKY university group and excels in medicine, business, and the humanities.",
      0.20),


    # ──────────────────────────────────────────────────────────────────────────
    # UAE (4 universities)
    # ──────────────────────────────────────────────────────────────────────────
    u("Khalifa University", "UAE", 201, 90,
      "Engineering|Computer Science|Mathematics|Physics|Data Science|Environmental|Aerospace|Bioengineering|Nuclear Engineering|Business",
      14000, 20000, "ku.ac.ae", "https://www.ku.ac.ae",
      7.5, 6.5, 92, True, "Khalifa University Scholarship", 12,
      "Khalifa University is the UAE's leading research-intensive university in science and engineering, established to be at the forefront of Abu Dhabi's knowledge economy. It has strong research ties to global defence and energy sectors.",
      0.30),

    u("American University of Sharjah", "UAE", 601, 180,
      "Engineering|Computer Science|Business|Economics|Law|Arts|Social Science|Architecture|Data Science|Mathematics|Education|Design",
      18000, 18000, "aus.edu", "https://www.aus.edu",
      7.0, 6.0, 85, False, "AUS Scholarship", 12,
      "The American University of Sharjah is a leading comprehensive university in the UAE following the American model of liberal arts education. It is known for its diverse student body and strong engineering and business programmes.",
      0.40),

    u("University of Sharjah", "UAE", 801, 250,
      "Engineering|Computer Science|Business|Economics|Law|Arts|Social Science|Architecture|Data Science|Medicine|Education|Dentistry",
      14000, 18000, "sharjah.ac.ae", "https://www.sharjah.ac.ae",
      7.0, 6.0, 80, False, "", 12,
      "The University of Sharjah is a leading Emirati university offering programmes in Arabic and English. It provides a unique Arab-Islamic educational environment with a strong focus on engineering, medicine, and Islamic studies.",
      0.50),

    u("New York University Abu Dhabi", "UAE", 185, 86,
      "Computer Science|Engineering|Business|Economics|Law|Arts|Social Science|Data Science|Environmental|Mathematics|Physics|Social Research|Humanities",
      58000, 20000, "nyuad.nyu.edu", "https://nyuad.nyu.edu",
      8.5, 7.5, 100, False, "NYUAD Scholarship", 12,
      "NYU Abu Dhabi is a world-class liberal arts and research university in the heart of Abu Dhabi. It offers all students a full-ride scholarship and provides an extraordinary global educational experience.",
      0.04),


    # ──────────────────────────────────────────────────────────────────────────
    # NORWAY (2 universities)
    # ──────────────────────────────────────────────────────────────────────────
    u("Norwegian University of Science and Technology", "Norway", 433, 140,
      "Engineering|Computer Science|Mathematics|Physics|Business|Economics|Data Science|Architecture|Environmental|Medicine|Social Science|Arts",
      3000, 16000, "ntnu.no", "https://www.ntnu.no",
      7.0, 6.5, 90, False, "NTNU Scholarship", 12,
      "NTNU (Norwegian University of Science and Technology) is Norway's largest university and its primary institution for educating the country's engineers and scientists. Located in Trondheim, it has strong industry partnerships with the energy and maritime sectors.",
      0.45),

    u("University of Oslo", "Norway", 171, 80,
      "Computer Science|Business|Economics|Law|Arts|Social Science|Data Science|Environmental|Medicine|Mathematics|History|Philosophy|Education",
      3000, 16000, "uio.no", "https://www.uio.no",
      7.0, 6.5, 90, False, "", 12,
      "The University of Oslo is Norway's oldest and most prestigious university, with a rich tradition of research excellence. It has produced five Nobel Peace Prize laureates and excels in the humanities, social sciences, and natural sciences.",
      0.45),


    # ──────────────────────────────────────────────────────────────────────────
    # DENMARK (3 universities)
    # ──────────────────────────────────────────────────────────────────────────
    u("Technical University of Denmark", "Denmark", 165, 77,
      "Engineering|Computer Science|Mathematics|Physics|Data Science|Environmental|Architecture|Bioengineering|Mechanical Engineering|Electrical Engineering|Food Science",
      18000, 16000, "dtu.dk", "https://www.dtu.dk",
      7.5, 7.0, 100, True, "DTU Scholarship", 12,
      "DTU (Technical University of Denmark) is a world-class technical university near Copenhagen, known for its excellence in wind energy, pharmaceuticals, and food science. It is a leading institution for engineering in Scandinavia.",
      0.30),

    u("University of Copenhagen", "Denmark", 101, 59,
      "Medicine|Computer Science|Economics|Law|Arts|Social Science|Mathematics|Physics|Environmental|Pharmacy|Data Science|Education|Philosophy",
      14000, 16000, "ku.dk", "https://www.ku.dk",
      7.5, 7.0, 100, False, "University of Copenhagen Scholarship", 12,
      "The University of Copenhagen is Scandinavia's largest university and a world leader in natural sciences, medicine, and the humanities. It has produced six Nobel laureates and is Denmark's foremost research institution.",
      0.35),

    u("Aarhus University", "Denmark", 148, 71,
      "Computer Science|Engineering|Business|Economics|Law|Arts|Social Science|Data Science|Environmental|Medicine|Agriculture|Education|Philosophy",
      14000, 14000, "au.dk", "https://www.au.dk",
      7.0, 7.0, 95, False, "Aarhus University Scholarship", 12,
      "Aarhus University is Denmark's second-largest research university, known for its strengths in natural sciences, social sciences, and health. It is a major centre for European humanities and social science research.",
      0.40),


    # ──────────────────────────────────────────────────────────────────────────
    # FINLAND (3 universities)
    # ──────────────────────────────────────────────────────────────────────────
    u("Aalto University", "Finland", 109, 63,
      "Engineering|Computer Science|Business|Economics|Arts|Design|Architecture|Data Science|Environmental|Mathematics|Physics|Electrical Engineering",
      15000, 14000, "aalto.fi", "https://www.aalto.fi",
      7.5, 7.0, 100, True, "Aalto University Scholarship", 12,
      "Aalto University is Finland's leading innovation university, formed from the merger of three top Finnish universities. It is known globally for design, technology, and business education and is a major driver of Finland's startup ecosystem.",
      0.30),

    u("University of Helsinki", "Finland", 109, 63,
      "Computer Science|Business|Economics|Law|Arts|Social Science|Data Science|Environmental|Medicine|Mathematics|Pharmacy|Education|Veterinary",
      15000, 14000, "helsinki.fi", "https://www.helsinki.fi",
      7.0, 7.0, 95, False, "University of Helsinki Scholarship", 12,
      "The University of Helsinki is Finland's largest and oldest university, and the only comprehensive research university in Finland. It is ranked among the world's top 100 universities and excels in the natural sciences, medicine, and the humanities.",
      0.35),

    u("Tampere University", "Finland", 401, 135,
      "Engineering|Computer Science|Business|Economics|Arts|Social Science|Data Science|Environmental|Medicine|Architecture|Education",
      15000, 13000, "tuni.fi", "https://www.tuni.fi",
      7.0, 7.0, 90, False, "", 12,
      "Tampere University is one of Finland's leading research universities, formed from a merger of the University of Tampere and the Tampere University of Technology. It focuses on applied research and strong industry partnerships.",
      0.40),


    # ──────────────────────────────────────────────────────────────────────────
    # NEW ZEALAND (3 universities)
    # ──────────────────────────────────────────────────────────────────────────
    u("University of Auckland", "New Zealand", 65, 38,
      "Computer Science|Engineering|Business|Economics|Law|Arts|Social Science|Data Science|Environmental|Medicine|Architecture|Education|Dentistry|Pharmacy",
      34000, 18000, "auckland.ac.nz", "https://www.auckland.ac.nz",
      7.0, 6.5, 92, False, "Auckland International Student Excellence Scholarship", 12,
      "The University of Auckland is New Zealand's leading research university and the country's only university in the QS Top 100. It is known for its comprehensive range of programmes and vibrant campus life in a beautiful harbour city.",
      0.45),

    u("University of Otago", "New Zealand", 178, 83,
      "Medicine|Computer Science|Business|Economics|Law|Arts|Social Science|Data Science|Environmental|Dentistry|Pharmacy|Education|Science",
      34000, 15000, "otago.ac.nz", "https://www.otago.ac.nz",
      7.0, 6.5, 88, False, "University of Otago Scholarship", 12,
      "The University of Otago is New Zealand's oldest university, founded in 1869, and is known for its excellent medical, dental, and health sciences schools. Its charming campus in Dunedin offers a classic university experience.",
      0.50),

    u("Victoria University of Wellington", "New Zealand", 262, 107,
      "Computer Science|Business|Economics|Law|Arts|Social Science|Data Science|Environmental|Architecture|Education|Public Policy|Design",
      30000, 17000, "wgtn.ac.nz", "https://www.wgtn.ac.nz",
      7.0, 6.5, 88, False, "Victoria Masters by Thesis Scholarship", 12,
      "Victoria University of Wellington is New Zealand's capital city university and a leading institution in law, public policy, and the social sciences. Its Wellington location provides excellent access to government and cultural organisations.",
      0.55),


    # ──────────────────────────────────────────────────────────────────────────
    # SPAIN (4 universities)
    # ──────────────────────────────────────────────────────────────────────────
    u("University of Barcelona", "Spain", 148, 71,
      "Computer Science|Business|Economics|Law|Medicine|Arts|Social Science|Data Science|Environmental|Mathematics|History|Philosophy|Education|Chemistry",
      4000, 12000, "ub.edu", "https://www.ub.edu",
      7.0, 6.5, 88, False, "", 12,
      "The University of Barcelona is Spain's leading comprehensive research university, with a rich tradition of academic excellence spanning over 500 years. It excels in science, medicine, and the humanities in one of Europe's most vibrant cities.",
      0.45),

    u("Autonomous University of Madrid", "Spain", 197, 88,
      "Computer Science|Business|Economics|Law|Medicine|Arts|Social Science|Data Science|Environmental|Mathematics|History|Philosophy|Education|Physics",
      4000, 13000, "uam.es", "https://www.uam.es",
      7.0, 6.5, 88, False, "UAM Excellence Scholarship", 12,
      "The Autonomous University of Madrid is one of Spain's most prestigious research universities, created in 1968 as a modern research-focused institution. It has strong science, social science, and business faculties.",
      0.45),

    u("IE University", "Spain", 601, 180,
      "Business|Finance|Economics|Law|Data Science|Computer Science|Architecture|Arts|Design|Management|International Relations|Social Science",
      42000, 14000, "ie.edu", "https://www.ie.edu",
      7.5, 7.0, 100, False, "IE Foundation Scholarship", 12,
      "IE University is one of Europe's most innovative and internationally recognised universities, known for its outstanding business school and its focus on entrepreneurship, technology, and global leadership. It has campuses in Madrid and Segovia.",
      0.20),

    u("ESADE Business School", "Spain", 601, 180,
      "Business|Finance|Economics|Law|Management|Data Science|Social Science|International Relations|Marketing|Entrepreneurship",
      48000, 14000, "esade.edu", "https://www.esade.edu",
      7.5, 7.0, 100, False, "ESADE Foundation Scholarship", 12,
      "ESADE is one of Europe's top-ranked business and law schools, part of Ramon Llull University in Barcelona. It is known for producing globally minded business leaders and has one of the world's most active alumni networks.",
      0.30),


    # ──────────────────────────────────────────────────────────────────────────
    # ITALY (3 universities)
    # ──────────────────────────────────────────────────────────────────────────
    u("Politecnico di Milano", "Italy", 123, 71,
      "Engineering|Computer Science|Architecture|Mathematics|Physics|Data Science|Design|Environmental|Mechanical Engineering|Electrical Engineering|Business",
      4000, 12000, "polimi.it", "https://www.polimi.it",
      7.5, 6.5, 90, True, "PoliMi Scholarship", 12,
      "Politecnico di Milano is Italy's largest and most prestigious technical university, consistently ranked among Europe's top engineering schools. Its design programmes are world-famous, producing graduates who lead global fashion and industrial design houses.",
      0.30),

    u("University of Bologna", "Italy", 154, 74,
      "Computer Science|Business|Economics|Law|Medicine|Arts|Social Science|Data Science|Environmental|Mathematics|History|Philosophy|Architecture|Agriculture",
      4000, 11000, "unibo.it", "https://www.unibo.it",
      7.0, 6.5, 88, False, "Unibo Scholarship", 12,
      "The University of Bologna, founded in 1088, is the world's oldest university in continuous operation and a major European research institution. It is known for its rich academic tradition and strengths in law, medicine, and the humanities.",
      0.45),

    u("Politecnico di Torino", "Italy", 316, 120,
      "Engineering|Computer Science|Architecture|Mathematics|Physics|Data Science|Design|Environmental|Mechanical Engineering|Electrical Engineering|Aerospace",
      4000, 11000, "polito.it", "https://www.polito.it",
      7.5, 6.5, 88, True, "Polito Scholarship", 12,
      "Politecnico di Torino is one of Italy's leading technical universities and a major centre for engineering and architecture research. Located in Turin, the heart of Italian industry, it has strong connections with major automotive and aerospace companies.",
      0.35),


    # ──────────────────────────────────────────────────────────────────────────
    # PORTUGAL (2 universities)
    # ──────────────────────────────────────────────────────────────────────────
    u("University of Lisbon", "Portugal", 235, 100,
      "Computer Science|Engineering|Business|Economics|Law|Medicine|Arts|Social Science|Data Science|Environmental|Architecture|Education|Veterinary",
      4000, 10000, "ulisboa.pt", "https://www.ulisboa.pt",
      7.0, 6.5, 88, False, "", 12,
      "The University of Lisbon is the largest Portuguese university and the country's foremost research institution. It excels in engineering, economics, and the social sciences, set in one of Europe's most beautiful and affordable capitals.",
      0.45),

    u("Nova School of Business and Economics", "Portugal", 601, 180,
      "Business|Finance|Economics|Management|Data Science|Social Science|International Relations|Marketing|Entrepreneurship|Law",
      20000, 10000, "novasbe.pt", "https://www.novasbe.pt",
      7.5, 7.0, 100, False, "Nova Merit Scholarship", 12,
      "Nova School of Business and Economics in Lisbon is one of Europe's fastest-rising business schools, ranked among the Financial Times top European business schools. It is known for its international community and innovative, career-focused programmes.",
      0.30),

    # ──────────────────────────────────────────────────────────────────────────
    # ADDITIONAL UNIVERSITIES (to reach 200+)
    # ──────────────────────────────────────────────────────────────────────────

    # Additional United States
    u("University of Rochester", "United States", 306, 118,
      "Computer Science|Engineering|Business|Economics|Arts|Social Science|Data Science|Medicine|Optics|Mathematics|Education|Nursing",
      62000, 20000, "rochester.edu", "https://www.rochester.edu",
      8.0, 6.5, 100, True, "Rochester Graduate Merit Award", 12,
      "The University of Rochester is a leading private research university in upstate New York, known for its music conservatory, optics research, and strong medical school. It has a distinctive interdisciplinary curriculum.",
      0.32),

    u("Rensselaer Polytechnic Institute", "United States", 401, 135,
      "Engineering|Computer Science|Mathematics|Physics|Data Science|Architecture|Business|Environmental|Bioengineering|Design",
      60000, 18000, "rpi.edu", "https://www.rpi.edu",
      8.0, 6.5, 100, True, "RPI Grant", 12,
      "Rensselaer Polytechnic Institute is America's oldest technological research university, founded in 1824. It excels in engineering, computer science, and the natural sciences, with a strong focus on innovation and entrepreneurship.",
      0.43),

    u("University of Pittsburgh", "United States", 148, 71,
      "Medicine|Engineering|Computer Science|Business|Economics|Law|Arts|Social Science|Data Science|Public Health|Pharmacy|Education|Nursing|Environmental",
      38000, 18000, "pitt.edu", "https://www.pitt.edu",
      7.5, 6.5, 90, False, "Pitt Scholarship", 12,
      "The University of Pittsburgh is a leading public research university and a member of the prestigious Association of American Universities. It is particularly known for its medical school, health sciences, and engineering programmes.",
      0.56),

    u("University of Maryland", "United States", 155, 75,
      "Computer Science|Engineering|Business|Economics|Law|Arts|Social Science|Data Science|Architecture|Public Policy|Education|Agriculture|Environmental|Finance",
      38000, 20000, "umd.edu", "https://www.umd.edu",
      7.5, 6.5, 100, True, "UMD Graduate School Fellowship", 12,
      "The University of Maryland is the flagship research university of the state and a major centre for technology, government, and international research. Its location near Washington D.C. provides unique access to federal research laboratories and policy centres.",
      0.44),

    u("Rutgers University", "United States", 204, 91,
      "Computer Science|Engineering|Business|Economics|Law|Medicine|Arts|Social Science|Data Science|Pharmacy|Education|Environmental|Public Policy|Agriculture",
      34000, 20000, "rutgers.edu", "https://www.rutgers.edu",
      7.0, 6.5, 88, False, "Rutgers Graduate Fellowship", 12,
      "Rutgers, The State University of New Jersey, is one of America's top public research universities with a comprehensive range of programmes. It is a founding member of the Big Ten Academic Alliance and has strong STEM and business schools.",
      0.65),

    u("Penn State University", "United States", 148, 71,
      "Engineering|Computer Science|Business|Economics|Law|Medicine|Arts|Social Science|Data Science|Architecture|Agriculture|Education|Environmental|Finance",
      37000, 17000, "psu.edu", "https://www.psu.edu",
      7.5, 6.5, 88, False, "Penn State Graduate Scholarship", 12,
      "Penn State University is one of America's largest and most well-known public research universities, known for its comprehensive programmes in engineering, business, and the sciences. It has one of the largest alumni networks in the world.",
      0.49),

    u("University of Virginia", "United States", 183, 85,
      "Computer Science|Engineering|Business|Economics|Law|Medicine|Arts|Social Science|Data Science|Architecture|Education|Environmental|Public Policy|Nursing",
      55000, 20000, "virginia.edu", "https://www.virginia.edu",
      8.0, 7.0, 100, False, "UVA Graduate School Scholarship", 12,
      "The University of Virginia is one of America's most prestigious public universities, founded by Thomas Jefferson in 1819. Its Darden School of Business and School of Law are among the nation's finest.",
      0.21),

    # Additional United Kingdom
    u("University of East Anglia", "United Kingdom", 601, 180,
      "Computer Science|Business|Economics|Law|Arts|Social Science|Environmental|Data Science|Education|Finance|Media|Health Sciences",
      22000, 13000, "uea.ac.uk", "https://www.uea.ac.uk",
      6.5, 6.0, 85, False, "UEA International Development Scholarship", 12,
      "The University of East Anglia in Norwich is a leading UK research university known for its creative writing programme, environmental sciences, and health research. It consistently scores highly in student satisfaction surveys.",
      0.75),

    u("University of Kent", "United Kingdom", 601, 180,
      "Computer Science|Business|Economics|Law|Arts|Social Science|Environmental|Data Science|Education|Finance|Architecture|Social Policy",
      20000, 13000, "kent.ac.uk", "https://www.kent.ac.uk",
      6.5, 6.0, 85, False, "", 12,
      "The University of Kent is known as the UK's European university, with campuses in Canterbury and Brussels. It offers excellent programmes in law, social sciences, and the arts.",
      0.80),

    # Additional Canada
    u("Concordia University", "Canada", 601, 180,
      "Computer Science|Engineering|Business|Economics|Arts|Social Science|Data Science|Environmental|Design|Education|Finance|Architecture",
      22000, 14000, "concordia.ca", "https://www.concordia.ca",
      6.5, 6.5, 85, False, "Concordia International Award", 12,
      "Concordia University is a dynamic university in Montreal offering over 300 programmes in French and English. It is known for its arts, technology, and business programmes in one of Canada's most vibrant cities.",
      0.70),

    u("University of Victoria", "Canada", 601, 180,
      "Computer Science|Engineering|Business|Economics|Law|Arts|Social Science|Data Science|Environmental|Education|Health Sciences|Mathematics",
      24000, 16000, "uvic.ca", "https://www.uvic.ca",
      7.0, 6.5, 88, False, "UVic Excellence Award", 12,
      "The University of Victoria is a research-intensive university on beautiful Vancouver Island, known for its oceanography, environmental studies, and strong cooperative education programmes. It offers a unique combination of academic excellence and Pacific lifestyle.",
      0.65),

    # Additional Australia
    u("Griffith University", "Australia", 335, 123,
      "Engineering|Computer Science|Business|Economics|Law|Arts|Social Science|Data Science|Environmental|Medicine|Education|Health Sciences|Criminology",
      28000, 16000, "griffith.edu.au", "https://www.griffith.edu.au",
      7.0, 6.5, 85, False, "Griffith Remarkable Scholarship", 12,
      "Griffith University is a research-intensive Australian university with campuses in the Gold Coast and Brisbane. It is known for its innovative programmes in environmental science, criminology, and business.",
      0.70),

    # Additional Germany
    u("University of Mannheim", "Germany", 501, 162,
      "Business|Economics|Law|Social Science|Computer Science|Data Science|Mathematics|Finance|Management|Sociology",
      4000, 12000, "uni-mannheim.de", "https://www.uni-mannheim.de",
      7.5, 7.0, 95, False, "Mannheim Scholarship", 12,
      "The University of Mannheim is widely regarded as Germany's best business and economics university. Its Graduate School of Economic and Social Sciences and the prestigious Mannheim Business School attract top talent from across Europe.",
      0.30),

    # Additional Japan
    u("Tohoku University", "Japan", 90, 53,
      "Engineering|Computer Science|Medicine|Economics|Law|Arts|Social Science|Data Science|Environmental|Mathematics|Physics|Agriculture|Pharmacy",
      8000, 11000, "tohoku.ac.jp", "https://www.tohoku.ac.jp",
      7.5, 6.5, 85, True, "MEXT Scholarship", 12,
      "Tohoku University in Sendai is one of Japan's seven imperial universities and a world leader in materials science, physics, and medicine. It was the first Japanese university to admit female students.",
      0.40),

    # Additional South Korea
    u("Korea University", "South Korea", 74, 44,
      "Engineering|Computer Science|Business|Economics|Law|Medicine|Arts|Social Science|Data Science|Environmental|Mathematics|Education|International Studies",
      12000, 12000, "korea.ac.kr", "https://www.korea.ac.kr",
      7.5, 6.5, 88, False, "Korea University Scholarship", 12,
      "Korea University is one of South Korea's most prestigious private universities and part of the elite SKY group. Founded in 1905, it has a strong tradition in law, business, and engineering.",
      0.25),

    # Additional Singapore
    u("Singapore Institute of Technology", "Singapore", 801, 250,
      "Engineering|Computer Science|Business|Health Sciences|Design|Data Science|Environmental|Education",
      20000, 14000, "singaporetech.edu.sg", "https://www.singaporetech.edu.sg",
      7.0, 6.0, 85, False, "", 12,
      "Singapore Institute of Technology (SIT) is a public university that focuses on applied degree education with a strong emphasis on industry collaboration. It partners with leading overseas universities to offer diverse degree programmes.",
      0.55),

    # Additional Ireland
    u("Dublin City University", "Ireland", 601, 180,
      "Computer Science|Engineering|Business|Economics|Law|Arts|Social Science|Data Science|Environmental|Education|Journalism|Nursing|Health Sciences",
      18000, 15000, "dcu.ie", "https://www.dcu.ie",
      6.5, 6.0, 85, False, "DCU Scholarship", 12,
      "Dublin City University is Ireland's youngest research university and a leading institution for technology, science, engineering, and business. It is deeply embedded in Dublin's thriving tech and media industries.",
      0.60),

    # Additional Netherlands
    u("Tilburg University", "Netherlands", 401, 135,
      "Business|Economics|Law|Social Science|Data Science|Management|Finance|Cognitive Science|Psychology",
      16000, 13000, "tilburguniversity.edu", "https://www.tilburguniversity.edu",
      7.0, 7.0, 95, False, "Tilburg University Scholarship", 12,
      "Tilburg University is a leading Dutch university specialising in social and behavioural sciences, economics, law, and business. It consistently ranks among the top European business and economics schools.",
      0.40),

]


def main():
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    # Deduplicate by name
    seen = set()
    deduped = []
    for uni in UNIVERSITIES:
        if uni["name"] not in seen:
            seen.add(uni["name"])
            deduped.append(uni)

    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(deduped)

    print(f"Written {len(deduped)} universities to {OUTPUT_PATH}")

    # Quick stats
    from collections import Counter
    countries = Counter(u["country"] for u in deduped)
    print("\nUniversities per country:")
    for country, count in sorted(countries.items(), key=lambda x: -x[1]):
        print(f"  {country}: {count}")

    # UK + Economics filter check
    uk_econ = [u for u in deduped
               if u["country"] == "United Kingdom" and "Economics" in u["subject"]]
    print(f"\nUK universities with 'Economics' in subject field: {len(uk_econ)}")
    for u in uk_econ[:5]:
        print(f"  - {u['name']}")


if __name__ == "__main__":
    main()
