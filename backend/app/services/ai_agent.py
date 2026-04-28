"""
StudyPathway AI Agent — Gemini-Primary
======================================
Google Gemini is the PRIMARY AI model for all features.
Falls back to rule-based static data if Gemini is unavailable.

Architecture: Structured-prompt engineering.
  Gemini receives dense country-specific context + student profile
  and returns structured JSON for all features.

NOT a RAG system — all document/visa knowledge is embedded as static
context in the prompts. This is intentional: visa requirements change
slowly, static data is faster and more reliable than vector retrieval.
"""

import json
import logging
import os
import re
from typing import Any, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# VISA DOCUMENT DATA — 15 countries, accurate requirements for Indian students
# ═══════════════════════════════════════════════════════════════════════════════

VISA_DOCUMENTS: dict = {
    "United Kingdom": {
        "visa_type": "UK Student Visa (Tier 4 / Student Route)",
        "visa_fee_usd": 490,
        "timeline_weeks": 8,
        "categories": {
            "Identity": [
                "Valid passport (min 6 months beyond intended stay)",
                "Two recent passport-size photographs (45mm×35mm, white background)",
                "Biometric Residence Permit (BRP) — collected after arrival",
                "UK Student visa vignette sticker (applied at VFS/embassy)",
            ],
            "Admission": [
                "Confirmation of Acceptance for Studies (CAS) — issued by university",
                "Official offer letter from UKVI-registered university",
                "Academic transcripts (all years, with official seal)",
                "Degree certificates / final marksheets",
                "IELTS UKVI 6.0+ overall (or TOEFL iBT 60+, PTE 51+)",
            ],
            "Financial": [
                "Bank statement: £1,334/month for London OR £1,023/month elsewhere (held 28 consecutive days)",
                "Bank statement dated within 31 days of application",
                "Immigration Health Surcharge (IHS) payment confirmation (~£470/year)",
                "Scholarship/sponsorship letter + bank guarantee (if sponsored)",
                "Tuition fee payment confirmation OR financial commitment letter",
            ],
            "Health & Other": [
                "TB test certificate (mandatory for Indian passport holders, <6 months old)",
                "ATAS clearance certificate (for STEM/defence-related masters/PhD subjects)",
                "Academic Technology Approval Scheme (ATAS) — check GOV.UK if required",
                "Travel insurance for journey (recommended)",
                "Accommodation confirmation or university letter",
            ],
        },
        "key_tips": [
            "TB test (Chest X-Ray) must be done at IOM-approved clinic — allow 2 weeks",
            "CAS is issued by university after paying deposit — request it 6–8 weeks before visa deadline",
            "IHS fee must be paid ONLINE as part of visa application — cannot pay at embassy",
            "UK visa processing: 3 weeks standard. Apply at VFS Global centres in India",
            "Post-study: Graduate Visa allows 2 years work after graduation",
        ],
    },
    "USA": {
        "visa_type": "F-1 Student Visa",
        "visa_fee_usd": 185,
        "timeline_weeks": 12,
        "categories": {
            "Identity": [
                "Valid US passport (or home country passport with ≥6 months validity)",
                "DS-160 online application form — completed and printed confirmation",
                "SEVIS I-901 fee payment receipt ($350 — mandatory)",
                "F-1 visa stamp (applied at US Embassy/Consulate in India)",
            ],
            "Admission": [
                "I-20 form (Certificate of Eligibility) — issued by the university's DSO",
                "Official offer/acceptance letter from SEVP-approved US university",
                "TOEFL iBT 80+ OR IELTS 6.5+ OR Duolingo 110+ (varies by school)",
                "GRE General Test scores (required by most graduate programs)",
                "GMAT scores (required for MBA programs)",
                "Academic transcripts — notarised English translation if not in English",
                "WES/ECE evaluation of Indian transcripts (required by most US universities)",
            ],
            "Financial": [
                "Bank statement: $10,000–$25,000+ for first year (varies by university cost)",
                "I-20 shows total estimated cost — match or exceed this in bank proof",
                "Affidavit of Financial Support (Form I-134) if sponsored by US citizen/PR",
                "Scholarship/assistantship award letter (reduces financial requirement)",
                "Sponsorship letter + guarantor's bank statement (if parents sponsoring)",
            ],
            "Interview Prep": [
                "Visa interview at US Embassy (Mumbai/Delhi/Chennai/Kolkata/Hyderabad)",
                "Statement of Purpose (SOP) — be prepared to discuss it",
                "Proof of strong ties to India (family, property deed, job offer after study)",
                "Research about your program, university, and career goals",
                "DS-160 confirmation page (print and bring)",
                "Previous US visa (if any) or refusal documentation",
            ],
        },
        "key_tips": [
            "Schedule visa interview EARLY — appointments at Indian consulates book out 4–6 months ahead",
            "SEVIS fee MUST be paid 3+ business days before interview",
            "F-1 holders can work on campus (20hrs/week), OPT (1-3 years post-graduation)",
            "Apply to US universities August–December for Fall admission (September)",
            "WES evaluation takes 7–10 business days (premium) or 3–5 weeks standard",
        ],
    },
    "Canada": {
        "visa_type": "Canadian Study Permit",
        "visa_fee_usd": 150,
        "timeline_weeks": 16,
        "categories": {
            "Identity": [
                "Valid passport (min 6 months beyond study period)",
                "Study Permit application — IRCC online portal (preferred) or paper",
                "Two recent passport-size photographs",
                "Biometrics appointment (INR ~7,000 fee — mandatory for India)",
                "Temporary Resident Visa (TRV) included with study permit for India",
            ],
            "Admission": [
                "Letter of Acceptance (LOA) from a Designated Learning Institution (DLI)",
                "IELTS 6.0+ overall (or TOEFL iBT 80+, PTE 58+, CELPIP)",
                "Official academic transcripts",
                "Provincial Attestation Letter (PAL) — mandatory from most provinces since 2024",
                "Quebec Acceptance Certificate (CAQ) — required for Quebec institutions only",
            ],
            "Financial": [
                "GIC (Guaranteed Investment Certificate): CAD 20,635 in approved Canadian bank",
                "GIC enrollment: Scotiabank or BMO (takes 2–3 weeks to set up from India)",
                "Bank statement: tuition + CAD 10,000 living (in addition to GIC)",
                "Scholarship / funding letter (reduces bank requirement)",
                "Sponsorship letter + parents' bank statement showing steady income",
            ],
            "Health & Other": [
                "Medical examination — by IRCC-designated physician (upfront IME for India)",
                "Police Clearance Certificate (PCC) from local police, apostilled",
                "Statement of Purpose / Study plan (explain why Canada, why this program)",
                "Travel insurance for journey",
                "Proof of intention to leave Canada after studies",
            ],
        },
        "key_tips": [
            "PAL is now required — your province-based institution gets it from the province. Allow 4–6 weeks",
            "Medical exam (IME) for India — book with IRCC-designated doctor, takes 2–4 weeks",
            "GIC must be from Scotiabank or BMO — open online from India, takes 2 weeks",
            "Processing time: 8–16 weeks from biometrics. Apply EARLY",
            "Post-study: PGWP allows up to 3 years work after graduation. Excellent pathway to PR",
            "Canada caps international student intake — apply to programs with PAL allocation only",
        ],
    },
    "Germany": {
        "visa_type": "German Student Visa (Nationales Visum)",
        "visa_fee_usd": 80,
        "timeline_weeks": 20,
        "categories": {
            "Identity": [
                "Valid passport (min 6 months beyond stay)",
                "Completed national visa application form (German Embassy website)",
                "Two recent biometric passport photos (35mm×45mm, ICAO standard)",
                "Residence Permit (Aufenthaltserlaubnis) — obtained within 3 months of arrival",
            ],
            "Admission": [
                "Admission letter from German university (Zulassungsbescheid)",
                "APS certificate from APS India (Akademische Prüfstelle) — MANDATORY for Indian students",
                "Transcripts + degree certificates (official, sometimes notarised translation)",
                "German language proof: B1/B2 (TestDaF, Goethe) for German-taught programs",
                "English proficiency: IELTS 6.5+ or TOEFL 90+ for English-taught programs",
                "Statement of Motivation (SOP equivalent)",
            ],
            "Financial": [
                "Blocked account (Sperrkonto): €11,208/year (€934/month) — mandatory",
                "Open via Fintiba, Expatrio, or Deutsche Bank from India (takes 2–3 weeks)",
                "Proof of blocked account deposit certificate",
                "DAAD scholarship letter / university stipend (if applicable)",
                "Scholarship reduces blocked account requirement — clarify with university",
            ],
            "Health & Other": [
                "Health insurance proof: German statutory insurance (TK, AOK) or private equivalent",
                "Enroll in German health insurance BEFORE arrival (can be done online)",
                "Accommodation confirmation OR university hostel reservation letter",
                "Proof of enrollment or semester contribution payment",
                "APS interview appointment (Delhi office — 6+ month wait — apply EARLY)",
            ],
        },
        "key_tips": [
            "⚠️ APS INDIA CERTIFICATE IS THE SINGLE BIGGEST BOTTLENECK — apply immediately. Processing: 6–8 months from Delhi office",
            "Blocked account via Fintiba or Expatrio: open online from India, takes 2–3 weeks, no German bank visit needed",
            "Many German universities are tuition-FREE (only semester fee €200–€350)",
            "German health insurance: enroll in Techniker Krankenkasse (TK) online — provides European coverage",
            "Post-study: 18-month job-seeker visa. Strong manufacturing/engineering job market",
            "Apply to German programs: December–March for Summer semester, April–July for Winter semester",
        ],
    },
    "Australia": {
        "visa_type": "Student Visa (Subclass 500)",
        "visa_fee_usd": 620,
        "timeline_weeks": 8,
        "categories": {
            "Identity": [
                "Valid passport (min 6 months validity)",
                "Student visa (Subclass 500) — applied online via ImmiAccount",
                "ImmiAccount profile creation — linked to Australian Government myGovID",
            ],
            "Admission": [
                "Confirmation of Enrolment (CoE) — issued by CRICOS-registered institution",
                "IELTS 6.0+ / TOEFL 64+ / PTE 50+ (varies by institution and course)",
                "Academic transcripts and degree certificates",
                "English-language school completion (if bridging course required)",
            ],
            "Financial": [
                "Proof of AUD 24,505 for first year living costs (2024 requirement)",
                "Tuition fee payment receipt OR scholarship evidence",
                "Bank statements: past 3–6 months (personal or parents)",
                "Travel costs: AUD 2,000+ (flights + initial setup)",
                "School-age dependants: AUD 8,574/year per child",
            ],
            "Health & Other": [
                "Overseas Student Health Cover (OSHC) — mandatory, arranged by institution",
                "Health examination — panel physician examination if required (upfront or on request)",
                "Genuine Student (GS) statement — replacing old GTE statement from 2024",
                "English-language test results (certified copies)",
                "Character requirements: no serious criminal record",
            ],
        },
        "key_tips": [
            "Genuine Student (GS) statement replaced GTE — write an honest 1–2 page statement of why you want to study in Australia",
            "OSHC is arranged by your institution — cost is included in or alongside tuition",
            "Visa processing: 4–6 weeks. Can be faster with health checks done upfront",
            "Post-study: Graduate Temporary visa (Subclass 485) — 2–4 years depending on qualification and location",
            "Australia caps international student intake per institution — some courses fill fast",
        ],
    },
    "Netherlands": {
        "visa_type": "MVV + Residence Permit (via IND)",
        "visa_fee_usd": 210,
        "timeline_weeks": 12,
        "categories": {
            "Identity": [
                "Valid passport",
                "MVV (Machtiging tot Voorlopig Verblijf) — authorisation for temporary stay",
                "Residence Permit (Verblijfsvergunning) via IND — applied within 3 days of arrival",
                "Your Dutch institution may apply for MVV on your behalf (Highly Skilled Migrant route)",
            ],
            "Admission": [
                "Admission letter from Dutch institution (TU Delft, Wageningen, UvA, etc.)",
                "IELTS 6.0–7.5+ or TOEFL iBT 80–100+ (varies by program)",
                "Academic transcripts and degree certificates (notarised translation if not English)",
                "Apostille on Indian documents (from MEA India, 3–5 days)",
                "Proof of diploma equivalence (checked by institution)",
            ],
            "Financial": [
                "Bank statement: €900–€1,100/month (€10,800–€13,200 for the year)",
                "Scholarship letter (Holland Scholarship, institution scholarship)",
                "Tuition fee payment or guarantee letter",
            ],
            "Health & Other": [
                "Dutch health insurance (mandatory, arranged after arrival — within 4 months)",
                "Housing confirmation — extremely important, student housing in Netherlands is scarce",
                "DigiD application (Dutch digital identity number — after arrival, within weeks)",
                "BSN registration at local municipality (within 5 days of arrival)",
            ],
        },
        "key_tips": [
            "⚠️ Housing in Netherlands is VERY difficult — apply for university housing immediately on admission (waiting lists are 6+ months)",
            "Most programmes taught in English — IELTS 6.5+ usually sufficient",
            "MVV takes 2–3 months to process in India — your university usually sponsors this",
            "Dutch tuition: €2,300–€18,000/year depending on programme and EU/non-EU status",
            "Post-study: Orientation Year (Zoekjaar) visa — 1 year to find skilled work after graduation",
        ],
    },
    "Ireland": {
        "visa_type": "Irish Study Visa (D/Study)",
        "visa_fee_usd": 60,
        "timeline_weeks": 10,
        "categories": {
            "Identity": [
                "Valid passport",
                "D/Study Visa application — submitted to Irish Embassy/VFS India",
                "Biometric data collection at Irish Embassy",
                "IRP (Irish Residence Permit) — register at GNIB/Burgh Quay within 90 days of arrival",
            ],
            "Admission": [
                "Letter of Offer from QQI-accredited Irish institution",
                "IELTS 6.0+ or TOEFL iBT 80+ (higher for research programmes)",
                "Official academic transcripts and degree certificates",
            ],
            "Financial": [
                "Bank statement showing €10,000+ minimum for the year",
                "Tuition fee FULL PAYMENT receipt — most Irish institutions require tuition paid upfront",
                "Scholarship letter if applicable",
                "Private health insurance proof",
            ],
            "Health & Other": [
                "Private health insurance (public health system not available to students initially)",
                "Police clearance certificate (from home country if requested)",
                "Evidence of accommodation arrangements in Ireland",
            ],
        },
        "key_tips": [
            "Irish institutions typically require tuition paid BEFORE visa application — different from UK/USA",
            "IRP must be registered within 90 days of arrival (online or at local Garda station)",
            "Strong tech sector (Google, Meta, LinkedIn EU HQs) — great for CS/Engineering graduates",
            "Post-study: Stamp 1G — 12–24 months to seek employment after masters",
        ],
    },
    "Singapore": {
        "visa_type": "Student's Pass (ICA SOLAR system)",
        "visa_fee_usd": 30,
        "timeline_weeks": 8,
        "categories": {
            "Identity": [
                "Valid passport (min 6 months validity)",
                "Student's Pass — applied online via ICA SOLAR system",
                "In-Principle Approval (IPA) letter — collect Student's Pass within 2 months of arrival",
            ],
            "Admission": [
                "Official offer letter from NUS / NTU / SMU / SUTD or other approved institution",
                "Academic transcripts and degree certificates",
                "IELTS or TOEFL scores (if requested — many top universities waive for strong profiles)",
                "GRE scores (required by NUS CS/Engineering graduate programs)",
            ],
            "Financial": [
                "Bank statement: SGD 10,000+ (approximately USD 7,500)",
                "Tuition Grant agreement (if awarded — reduces tuition to subsidised rate, requires 3-year Singapore work commitment)",
                "Scholarship/MOE Tuition Grant letter",
            ],
            "Health & Other": [
                "Medical examination at ICA-approved clinic (required before Student's Pass issuance)",
                "Compulsory student insurance (arranged by institution)",
                "Mandatory Personal Accident Insurance (PAI) through institution",
            ],
        },
        "key_tips": [
            "NUS and NTU rank in QS Top 15 globally — highly competitive admission",
            "Tuition Grant from MOE reduces fees significantly but requires 3-year Singapore work bond after graduation",
            "Singapore is very safe, English-speaking, excellent for tech careers",
            "Post-study work: Employment Pass or S Pass available — very competitive job market",
        ],
    },
    "Japan": {
        "visa_type": "College Student Visa",
        "visa_fee_usd": 25,
        "timeline_weeks": 20,
        "categories": {
            "Identity": [
                "Valid passport",
                "Certificate of Eligibility (CoE) — applied for BY the university in Japan",
                "College Student Visa — applied at Japanese Embassy/Consulate in India after CoE",
            ],
            "Admission": [
                "Letter of Admission from Japanese university",
                "JLPT N2/N1 for Japanese-medium programs",
                "English proficiency: IELTS 6.0+ or TOEFL 72+ for English programs",
                "Academic transcripts and certificates (official Japanese/English translation)",
                "Research Plan (for graduate programs) — detailed 2–5 page document",
            ],
            "Financial": [
                "Bank statement: JPY 2,000,000+ (~₹11L) recommended",
                "MEXT scholarship letter (waives many requirements)",
                "JASSO scholarship or university stipend letter",
                "Proof of regular monthly income (guarantor's documentation)",
            ],
            "Health & Other": [
                "National Health Insurance enrollment (compulsory after arrival, ¥1,000–3,000/month)",
                "Residence Card (My Number Card) — register within 14 days of arrival",
                "Health certificate (required by some universities)",
            ],
        },
        "key_tips": [
            "CoE is applied by the university — takes 3–4 months minimum. Start early",
            "MEXT scholarship covers tuition, living, airfare — extremely competitive, apply 1+ year ahead",
            "Japan visa processing: 5 business days once CoE received — not the bottleneck",
            "JLPT N2 is minimum for daily life; N1 preferred for career in Japan",
            "Post-study work: Japan has eased work visa rules, strong demand for engineers/IT graduates",
        ],
    },
    "France": {
        "visa_type": "Long-Stay Student Visa (VLS-TS)",
        "visa_fee_usd": 99,
        "timeline_weeks": 10,
        "categories": {
            "Identity": [
                "Valid passport (min 3 months beyond visa validity)",
                "VLS-TS (Visa de Long Séjour valant Titre de Séjour) — student category",
                "Register on Campus France India portal (MANDATORY pre-visa step for India)",
                "Campus France interview letter",
            ],
            "Admission": [
                "Admission/offer letter from French institution (accredited by Ministry of Higher Education)",
                "DELF/DALF B2+ for French-taught programs",
                "IELTS 6.5+ or TOEFL 90+ for English-taught programs (grandes écoles)",
                "Academic transcripts — official + translation by certified translator",
                "Prior degree certificates (apostilled if requested)",
            ],
            "Financial": [
                "Bank statement: €615/month minimum (€7,380/year — CAF housing aid available)",
                "Proof of accommodation (university CROUS housing or private rental)",
                "Scholarship letter: Eiffel Excellence, DAAD equivalent, institution scholarship",
                "Proof of tuition fee payment or university invoice",
            ],
            "Health & Other": [
                "Social security registration (CPAM) after arrival — French national health cover",
                "CVEC (Student Life Contribution): €103 annual fee paid before enrollment",
                "Accommodation proof essential for visa (university or rental agreement)",
            ],
        },
        "key_tips": [
            "Campus France India interview is MANDATORY — register at campusfrance.org/en/india, takes 2–3 weeks",
            "Public French universities: tuition €170–€380/year (grandes écoles: €3,000–€15,000+)",
            "VLS-TS allows living and working (964 hours/year) in France",
            "Post-study: APS (Autorisation Provisoire de Séjour) — 1-year post-study work permit",
        ],
    },
    "Sweden": {
        "visa_type": "Swedish Residence Permit for Studies",
        "visa_fee_usd": 120,
        "timeline_weeks": 12,
        "categories": {
            "Identity": [
                "Valid passport",
                "Residence Permit for Studies — applied online at Migrationsverket",
                "Biometrics at Swedish Embassy in New Delhi",
            ],
            "Admission": [
                "Conditional or unconditional admission letter from Swedish university",
                "IELTS 6.5+ or TOEFL iBT 90+ (most Swedish programs taught in English)",
                "Academic transcripts",
                "Proof of previous degrees/qualifications",
            ],
            "Financial": [
                "Bank statement: SEK 8,514/month (approx. €730/month) — 10 months minimum shown",
                "Scholarship letter (SISS — Swedish Institute Study Scholarship)",
                "University tuition fee payment confirmation (non-EU fees: SEK 75,000–200,000/year)",
            ],
            "Health & Other": [
                "Personal number (personnummer) — obtained after arrival via Skatteverket",
                "Swedish public healthcare accessible once registered",
            ],
        },
        "key_tips": [
            "Swedish Institute Scholarships (SISS): extremely competitive, covers tuition + living. Apply in October",
            "Residence permit processing: 8–12 weeks — apply as soon as you receive admission",
            "Sweden has high quality of life but also high cost — budget SEK 8,000–10,000/month",
            "Post-study: Job-seeker permit available after graduation for 6 months",
        ],
    },
    "Switzerland": {
        "visa_type": "Swiss Student Visa (Type D)",
        "visa_fee_usd": 80,
        "timeline_weeks": 10,
        "categories": {
            "Identity": [
                "Valid passport (Swiss D visa)",
                "Schengen residence permit — issued by Cantonal authority after arrival",
            ],
            "Admission": [
                "Letter of admission from ETH Zurich / EPFL / Swiss university",
                "IELTS 7.0+ or TOEFL 100+ (ETH Zurich and EPFL are very competitive)",
                "Academic transcripts, GRE scores (often required)",
                "Proof of prior degree equivalence",
            ],
            "Financial": [
                "Bank statement: CHF 1,400–1,800/month (one of the most expensive cities in the world)",
                "Scholarship letter (Excellence Scholarship, ETH Excellence Scholarship)",
                "Proof of tuition payment (ETH Zurich: CHF 730/semester)",
            ],
            "Health & Other": [
                "Mandatory health insurance in Switzerland (KVG/LAMal) — must enroll within 3 months",
                "Health insurance is compulsory and paid privately (~CHF 300–500/month)",
                "Cantonal registration within 14 days of arrival",
            ],
        },
        "key_tips": [
            "ETH Zurich and EPFL are QS Top 10 globally — admission is very competitive",
            "Switzerland is not EU — separate visa process from Schengen countries",
            "Health insurance is expensive and mandatory — budget CHF 350–500/month",
            "Strong pharma, finance, and engineering job market",
        ],
    },
    "South Korea": {
        "visa_type": "D-2 Student Visa",
        "visa_fee_usd": 60,
        "timeline_weeks": 8,
        "categories": {
            "Identity": [
                "Valid passport",
                "D-2 Student Visa application at Korean Embassy/VFS in India",
                "Alien Registration Card (ARC) — register within 90 days of arrival",
            ],
            "Admission": [
                "Certificate of Admission from Korean university (KAIST, SNU, POSTECH, Yonsei, Korea University)",
                "TOPIK Level 3+ for Korean-medium programs",
                "IELTS 6.0+ or TOEFL 80+ for English-medium programs",
                "Academic transcripts and degree certificates (apostilled)",
                "GRE scores (some graduate programs)",
            ],
            "Financial": [
                "Bank statement: KRW 20,000,000+ (~₹12L) for the year",
                "GKS (Korean Government Scholarship) letter — covers tuition + living",
                "University/KOICA scholarship letter if applicable",
            ],
            "Health & Other": [
                "National Health Insurance (NHIS) enrollment after arrival",
                "Health certificate (required by some programs)",
                "Apostilled documents from MEA India",
            ],
        },
        "key_tips": [
            "GKS (Global Korea Scholarship) — fully funded scholarship. Apply in March for fall intake",
            "KAIST, POSTECH offer tuition waivers + stipends for graduate students",
            "Korean language skills (TOPIK 3+) significantly boost employability",
            "Post-study: D-10 job-seeker visa for 6 months to 2 years",
        ],
    },
    "New Zealand": {
        "visa_type": "Student Visa (NZeTA + Student Visa)",
        "visa_fee_usd": 330,
        "timeline_weeks": 8,
        "categories": {
            "Identity": [
                "Valid passport",
                "New Zealand Student Visa — applied online at Immigration NZ",
                "NZeTA (NZ Electronic Travel Authority) if transiting via NZ",
            ],
            "Admission": [
                "Offer of Place (enrollment confirmation) from NZ institution",
                "IELTS 5.5–6.5+ (varies by provider and course level)",
                "Academic transcripts",
            ],
            "Financial": [
                "Bank statement: NZD 15,000–20,000+ for first year",
                "Tuition fee payment or payment plan with institution",
                "Scholarship evidence (NZ Excellence Awards, etc.)",
            ],
            "Health & Other": [
                "Medical and chest X-ray (required for Indian passport holders — 24-month validity)",
                "Police clearance certificate",
                "Comprehensive travel and health insurance",
            ],
        },
        "key_tips": [
            "Medical exam required for Indian passport holders — book EARLY with NZIAP-approved clinic",
            "NZ Post-study Work Visa (Open): 1–3 years depending on qualification level and location",
            "Strong agriculture, healthcare, and IT sectors",
            "Pathway to NZ Skilled Migrant Category (SMC) PR",
        ],
    },
    "UAE": {
        "visa_type": "UAE Student Residence Visa",
        "visa_fee_usd": 90,
        "timeline_weeks": 6,
        "categories": {
            "Identity": [
                "Valid passport (min 6 months validity)",
                "UAE Student Residence Visa — sponsored by university",
                "Emirates ID — applied after arrival within 30 days",
                "Medical fitness test (blood test + chest X-ray) at UAE Ministry-approved clinics",
            ],
            "Admission": [
                "Offer letter from UAE institution (BITS Pilani Dubai, University of Dubai, AUS, etc.)",
                "IELTS 5.5–6.5+ or TOEFL 72+ (varies by institution)",
                "Academic transcripts (attested by MEA India + UAE Embassy)",
                "Equivalency certificate from UAE Ministry of Education (for prior degrees)",
            ],
            "Financial": [
                "Bank statement: AED 3,000–5,000/month",
                "Scholarship letter if applicable",
                "Tuition fee payment receipt",
            ],
            "Health & Other": [
                "Mandatory UAE health insurance (DHA for Dubai, HAAD for Abu Dhabi)",
                "Attestation of Indian documents: MEA → UAE Embassy in India (allow 2–3 weeks)",
                "Good Conduct Certificate from Indian police (for residence visa)",
            ],
        },
        "key_tips": [
            "Document attestation (MEA + UAE Embassy) is critical — factor in 2–4 weeks",
            "UAE is very expensive: AED 4,000–8,000/month for living depending on city",
            "Tax-free income if you work part-time (limited for students)",
            "Strong networking hub — MENA region career opportunities",
        ],
    },
}

# Shorter alias mapping (frontend may send short names)
COUNTRY_ALIASES = {
    "UK": "United Kingdom",
    "USA": "United States",
    "US": "United States",
    "United States": "United States",
    "UAE": "UAE",
    "South Korea": "South Korea",
    "Korea": "South Korea",
    "NZ": "New Zealand",
}

def _resolve_country(name: str) -> str:
    return COUNTRY_ALIASES.get(name, name)


# ═══════════════════════════════════════════════════════════════════════════════
# PROFILE SCORING — rule-based multi-dimensional scoring (no AI needed)
# ═══════════════════════════════════════════════════════════════════════════════

def compute_profile_score(profile: dict) -> dict:
    """
    Compute a multi-dimensional profile strength score.
    Returns {dimensions: {...}, total: int, grade: str}
    """
    scores = {}

    # 1. Academic strength (30 pts)
    cgpa = float(profile.get("cgpa") or 0)
    if cgpa >= 9.0:   scores["academic"] = 30
    elif cgpa >= 8.5: scores["academic"] = 27
    elif cgpa >= 8.0: scores["academic"] = 24
    elif cgpa >= 7.5: scores["academic"] = 20
    elif cgpa >= 7.0: scores["academic"] = 15
    elif cgpa >= 6.5: scores["academic"] = 11
    elif cgpa >= 6.0: scores["academic"] = 7
    elif cgpa > 0:    scores["academic"] = 3
    else:             scores["academic"] = 0

    # 2. English proficiency (20 pts)
    test  = (profile.get("english_test") or "").upper()
    escore = float(profile.get("english_score") or 0)
    toefl  = float(profile.get("toefl_score") or 0)
    if "IELTS" in test and escore:
        if escore >= 8.0:   scores["english"] = 20
        elif escore >= 7.5: scores["english"] = 18
        elif escore >= 7.0: scores["english"] = 15
        elif escore >= 6.5: scores["english"] = 11
        elif escore >= 6.0: scores["english"] = 7
        else:               scores["english"] = 3
    elif "TOEFL" in test and toefl:
        if toefl >= 110:   scores["english"] = 20
        elif toefl >= 100: scores["english"] = 16
        elif toefl >= 90:  scores["english"] = 12
        elif toefl >= 80:  scores["english"] = 8
        else:              scores["english"] = 4
    elif "DUOLINGO" in test and escore:
        if escore >= 130: scores["english"] = 18
        elif escore >= 115: scores["english"] = 14
        else: scores["english"] = 8
    elif test in ("WAIVED", "NATIVE", "EXEMPT"):
        scores["english"] = 20
    else:
        scores["english"] = 0  # Not taken — major gap

    # 3. Standardised test — GRE/GMAT (10 pts)
    gre  = float(profile.get("gre_score") or 0)
    gmat = float(profile.get("gmat_score") or 0)
    degree = (profile.get("preferred_degree") or "").lower()
    if gre >= 330:    scores["standardized_test"] = 10
    elif gre >= 320:  scores["standardized_test"] = 8
    elif gre >= 310:  scores["standardized_test"] = 6
    elif gre >= 300:  scores["standardized_test"] = 4
    elif gre > 0:     scores["standardized_test"] = 2
    elif gmat >= 700: scores["standardized_test"] = 10
    elif gmat >= 650: scores["standardized_test"] = 7
    elif gmat >= 600: scores["standardized_test"] = 4
    elif gmat > 0:    scores["standardized_test"] = 2
    elif "phd" in degree or "doctor" in degree:
        scores["standardized_test"] = 5  # PhD may not need GRE
    elif "llm" in degree or "law" in degree:
        scores["standardized_test"] = 7  # Law usually no GRE
    elif "medicine" in (profile.get("field_of_study") or "").lower():
        scores["standardized_test"] = 7  # Medicine uses USMLE/PLAB not GRE
    else:
        scores["standardized_test"] = 0  # Not taken — moderate gap

    # 4. Work / research experience (15 pts)
    work = float(profile.get("work_experience_years") or 0)
    if work >= 5:    scores["experience"] = 15
    elif work >= 3:  scores["experience"] = 12
    elif work >= 2:  scores["experience"] = 9
    elif work >= 1:  scores["experience"] = 7
    elif work > 0:   scores["experience"] = 5
    else:
        # Fresh graduate — partial credit
        if profile.get("current_degree"):
            scores["experience"] = 3
        else:
            scores["experience"] = 2

    # 5. Financial preparedness (10 pts)
    has_budget  = bool(profile.get("budget") or profile.get("budget_inr"))
    scholarship = bool(profile.get("scholarship_interest"))
    if has_budget and scholarship:   scores["financial"] = 10
    elif has_budget:                 scores["financial"] = 7
    elif scholarship:                scores["financial"] = 4
    else:                            scores["financial"] = 0

    # 6. Profile completeness (10 pts)
    key_fields = [
        "full_name", "cgpa", "field_of_study", "preferred_degree",
        "graduation_year", "target_countries", "intake_preference",
        "current_degree"
    ]
    filled = sum(1 for f in key_fields if profile.get(f))
    scores["completeness"] = round((filled / len(key_fields)) * 10)

    # 7. Planning & career clarity (5 pts)
    has_field   = bool(profile.get("field_of_study"))
    has_degree  = bool(profile.get("preferred_degree"))
    has_country = bool(profile.get("target_countries"))
    has_intake  = bool(profile.get("intake_preference"))
    clarity = sum([has_field, has_degree, has_country, has_intake])
    scores["clarity"] = min(5, clarity + 1) if clarity >= 3 else clarity

    total = sum(scores.values())
    grade = "Excellent" if total >= 80 else "Good" if total >= 60 else "Fair" if total >= 40 else "Needs Work"

    return {"dimensions": scores, "total": min(100, total), "grade": grade}


# ═══════════════════════════════════════════════════════════════════════════════
# AI CLIENT SETUP — Gemini is PRIMARY
# ═══════════════════════════════════════════════════════════════════════════════

class _GeminiWrapper:
    """
    Thin wrapper around the new google.genai Client so all call sites
    can keep using `.generate_content(prompt)` unchanged.
    """
    def __init__(self, client, model: str, temperature: float, max_tokens: int):
        self._client      = client
        self._model       = model
        self._temperature = temperature
        self._max_tokens  = max_tokens

    def generate_content(self, prompt: str):
        from google.genai import types
        return self._client.models.generate_content(
            model=self._model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=self._temperature,
                max_output_tokens=self._max_tokens,
            ),
        )


def _get_gemini() -> Optional["_GeminiWrapper"]:
    """Return a Gemini wrapper (primary AI). Returns None if unconfigured."""
    try:
        from google import genai
        key = settings.GOOGLE_API_KEY or os.getenv("GOOGLE_API_KEY", "")
        if not key:
            return None
        client = genai.Client(api_key=key)
        return _GeminiWrapper(client, "gemini-2.5-flash", temperature=0.3, max_tokens=8192)
    except Exception as e:
        logger.error(f"Gemini init error: {e}")
        return None


def _get_anthropic_client():
    """Return Anthropic client if ANTHROPIC_API_KEY is configured (optional fallback)."""
    try:
        import anthropic
        key = settings.ANTHROPIC_API_KEY or os.getenv("ANTHROPIC_API_KEY", "")
        if not key or "your_" in key:
            return None
        return anthropic.Anthropic(api_key=key)
    except ImportError:
        return None


def _extract_json(text: str) -> Optional[dict]:
    """
    Robustly extract JSON from Gemini output.
    Handles ```json blocks, bare JSON, and minor formatting issues.
    """
    if not text:
        return None

    # Strategy 1: ```json ... ``` block
    m = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", text)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass

    # Strategy 2: First { to last }
    start = text.find("{")
    end   = text.rfind("}")
    if start != -1 and end > start:
        candidate = text[start : end + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            # Fix trailing commas (common in Gemini output)
            cleaned = re.sub(r",\s*([}\]])", r"\1", candidate)
            try:
                return json.loads(cleaned)
            except json.JSONDecodeError:
                pass

    return None


# ═══════════════════════════════════════════════════════════════════════════════
# PROFILE HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def _profile_summary(profile: dict) -> str:
    """Convert profile dict to compact text for prompts."""
    parts = []
    if profile.get("full_name"):       parts.append(f"Name: {profile['full_name']}")
    if profile.get("cgpa"):            parts.append(f"CGPA: {profile['cgpa']}/10")
    if profile.get("field_of_study"):  parts.append(f"Field: {profile['field_of_study']}")
    if profile.get("preferred_degree"): parts.append(f"Target degree: {profile['preferred_degree']}")
    if profile.get("current_degree"):  parts.append(f"Current degree: {profile['current_degree']}")
    if profile.get("graduation_year"): parts.append(f"Graduating: {profile['graduation_year']}")
    if profile.get("english_test"):
        score = profile.get("english_score") or profile.get("toefl_score", "not taken")
        parts.append(f"English: {profile['english_test']} {score}")
    else:
        parts.append("English test: NOT YET TAKEN")
    if profile.get("gre_score"):       parts.append(f"GRE: {profile['gre_score']}")
    elif profile.get("gmat_score"):    parts.append(f"GMAT: {profile['gmat_score']}")
    else:                              parts.append("GRE/GMAT: not taken")
    if profile.get("work_experience_years"):
        parts.append(f"Work experience: {profile['work_experience_years']} years")
    else:
        parts.append("Work experience: fresher/student")
    if profile.get("budget_inr"):      parts.append(f"Annual budget: ₹{profile['budget_inr']:,}")
    elif profile.get("budget"):        parts.append(f"Annual budget (USD): ${profile['budget']:,}")
    else:                              parts.append("Budget: not specified")
    if profile.get("intake_preference"): parts.append(f"Target intake: {profile['intake_preference']}")
    if profile.get("target_countries"):  parts.append(f"Target countries: {', '.join(profile['target_countries'])}")
    if profile.get("ranking_preference"): parts.append(f"Ranking preference: {profile['ranking_preference']}")
    if profile.get("scholarship_interest"): parts.append("Interested in scholarships: YES")
    if profile.get("work_abroad_interest"):  parts.append("Post-study work: YES (interested)")
    return "\n".join(parts) or "No profile data available"


def _country_doc_context(country: str) -> str:
    """Inject structured document requirements into the prompt context."""
    key  = _resolve_country(country)
    data = VISA_DOCUMENTS.get(key) or VISA_DOCUMENTS.get(country, {})
    if not data:
        return f"No pre-loaded requirements for {country} — use your knowledge."

    lines = [f"=== OFFICIAL REQUIREMENTS FOR {country.upper()} ===",
             f"Visa type: {data.get('visa_type', 'Student Visa')}",
             f"Typical visa fee: ${data.get('visa_fee_usd', '?')} USD",
             f"Recommended preparation lead time: {data.get('timeline_weeks', '?')} weeks before intake",
             ""]
    for cat, docs in data.get("categories", {}).items():
        lines.append(f"{cat}:")
        for d in docs:
            lines.append(f"  • {d}")
        lines.append("")
    if data.get("key_tips"):
        lines.append("KEY TIPS FOR INDIAN STUDENTS:")
        for tip in data["key_tips"]:
            lines.append(f"  ⚡ {tip}")
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# PUBLIC API FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def generate_checklist(country: str, profile: dict) -> dict:
    """
    Generate a personalised, prioritised document checklist for studying in `country`.
    Gemini is called with full country context + student profile for personalisation.
    Falls back to static VISA_DOCUMENTS data if Gemini is unavailable.
    """
    resolved    = _resolve_country(country)
    profile_txt = _profile_summary(profile)
    doc_ctx     = _country_doc_context(resolved)
    gemini      = _get_gemini()

    if gemini:
        prompt = f"""You are StudyPathway's expert visa advisor for Indian students.
Generate a COMPLETE, PERSONALISED document checklist for an Indian student going to {resolved}.

STUDENT PROFILE:
{profile_txt}

{doc_ctx}

Return ONLY a valid JSON object with this exact structure (no markdown, no extra text):
{{
  "country": "{resolved}",
  "visa_type": "exact visa type name",
  "visa_fee_usd": <number>,
  "timeline_weeks": <number>,
  "summary": "2-3 sentences about key requirements and critical things to know for {resolved}",
  "checklist": [
    {{
      "id": "1",
      "category": "Identity",
      "task": "Exact document name / action required",
      "priority": "critical",
      "done": false,
      "note": "Specific tip for THIS student based on their profile",
      "deadline": "When to have this ready (e.g. '10 weeks before intake')"
    }}
  ]
}}

Priority rules:
- "critical": Without this, visa WILL be rejected (passport, CAS/I-20/CoE, bank statement)
- "high": Required but not immediately rejecting (TB test, transcripts, insurance)
- "medium": Important but secondary (accommodation proof, travel insurance)

Personalise notes based on: CGPA={profile.get('cgpa','?')}, English={profile.get('english_test','not taken')} {profile.get('english_score','')}, GRE={profile.get('gre_score','not taken')}, Budget={profile.get('budget_inr','not specified')}.

Include ALL documents from the requirements above PLUS any extras specific to this student's profile.
Return minimum 15 checklist items covering all categories."""

        try:
            resp   = gemini.generate_content(prompt)
            result = _extract_json(resp.text)
            if result and result.get("checklist"):
                logger.info(f"Gemini checklist generated: {len(result['checklist'])} items for {resolved}")
                return result
        except Exception as e:
            logger.error(f"Gemini checklist error: {e}")

    # Static fallback
    return _static_checklist_fallback(resolved)


def _static_checklist_fallback(country: str) -> dict:
    key  = _resolve_country(country)
    data = VISA_DOCUMENTS.get(key) or VISA_DOCUMENTS.get(country, {})
    if not data:
        return {
            "country": country, "checklist": [], "visa_fee_usd": 0, "timeline_weeks": 8,
            "summary": f"Please consult the official embassy website for {country} requirements.",
        }
    items = []
    priority_map = {
        "Identity": "critical", "Admission": "critical", "Financial": "high",
        "Health & Other": "medium", "Interview Prep": "high", "Health": "medium"
    }
    for cat, docs in data.get("categories", {}).items():
        for i, doc in enumerate(docs):
            items.append({
                "id": str(len(items) + 1), "category": cat, "task": doc,
                "priority": priority_map.get(cat, "medium"), "done": False,
                "note": "", "deadline": f"Before {data.get('timeline_weeks', 8)} weeks of intake",
            })
    return {
        "country": country, "visa_type": data.get("visa_type", "Student Visa"),
        "visa_fee_usd": data.get("visa_fee_usd", 0), "timeline_weeks": data.get("timeline_weeks", 8),
        "checklist": items,
        "summary": f"Essential documents for {country} student visa. {' '.join(data.get('key_tips', [''])[:2])}",
    }


def generate_timeline(intake: str, countries: list, profile: dict, current_status: dict = None) -> dict:
    """
    Generate a month-by-month personalised application timeline.
    current_status: dict from the questionnaire (tests done, apps stage, etc.)
    """
    profile_txt = _profile_summary(profile)
    gemini      = _get_gemini()
    countries_str = ", ".join(countries) if countries else "UK, Canada, Australia"

    # Build status context from questionnaire answers
    status_lines = []
    if current_status:
        s = current_status
        if s.get("ielts_done"):   status_lines.append(f"✅ IELTS done — score: {s.get('ielts_score', 'provided')}")
        elif s.get("ielts_when"): status_lines.append(f"⏳ IELTS planned: {s.get('ielts_when')}")
        else:                     status_lines.append("❌ IELTS not started")

        if s.get("gre_done"):     status_lines.append(f"✅ GRE done — score: {s.get('gre_score', 'provided')}")
        elif s.get("gre_not_needed"): status_lines.append("ℹ️ GRE not required for target programs")
        elif s.get("gre_when"):   status_lines.append(f"⏳ GRE planned: {s.get('gre_when')}")
        else:                     status_lines.append("❌ GRE not started")

        checks = {
            "shortlisted":        "Universities shortlisted",
            "sop_started":        "SOP/personal statement started",
            "lors_arranged":      "References/LORs arranged",
            "transcripts_ready":  "Official transcripts ordered/ready",
            "budget_confirmed":   "Funding/budget confirmed",
            "offer_received":     "Offer letter received",
            "deposit_paid":       "Tuition deposit paid",
            "visa_started":       "Visa application started",
        }
        for key, label in checks.items():
            status_lines.append(f"{'✅' if s.get(key) else '❌'} {label}")

        if s.get("months_until_intake"):
            status_lines.append(f"Months until intake: {s['months_until_intake']}")

    status_block = "\n".join(status_lines) if status_lines else "No current status provided"

    # Determine exact number of months to generate
    months_count = 12
    if current_status:
        m = current_status.get("months_until_intake")
        if m:
            try:
                months_count = max(2, min(int(float(m)), 12))
            except (ValueError, TypeError):
                pass

    if months_count <= 3:
        urgency_block = (
            f"⚠️ EXTREME URGENCY: Student has only {months_count} MONTHS until intake. "
            "Compress ALL tasks ruthlessly. Flag what is now impossible (e.g. if tests not done "
            "and intake is 2 months away, note that tests may need to be deferred). "
            "Prioritise: 1) visa docs, 2) offer letter/CAS, 3) financial proof. "
            "Every month entry must have 5+ dense, specific tasks."
        )
    elif months_count <= 6:
        urgency_block = (
            f"⚠️ TIGHT TIMELINE: Only {months_count} months available. "
            "Be aggressive with task scheduling — stack multiple tasks per month. "
            "Flag any country-specific risks that are now time-critical."
        )
    else:
        urgency_block = f"Student has {months_count} months — use the full window wisely."

    if gemini:
        prompt = f"""You are StudyPathway's application timeline expert for Indian students.
Generate a detailed, PERSONALISED month-by-month application timeline.

TARGET INTAKE: {intake}
TARGET COUNTRIES: {countries_str}
MONTHS AVAILABLE UNTIL INTAKE: {months_count}

STUDENT PROFILE:
{profile_txt}

CURRENT STATUS (what's already done):
{status_block}

TIMELINE URGENCY:
{urgency_block}

RULES:
- Generate EXACTLY {months_count} month entries — no more, no less.
- Skip tasks already completed (marked ✅ above) — do not repeat them.
- Each month must have 4–6 SPECIFIC tasks tailored to THIS student's actual profile.
- Use the student's real test scores, countries, degree goal, and current status in task descriptions.
- Country-specific lead times to respect:
  • Canada: study permit + PAL = 8–16 weeks — flag if < 4 months left
  • Germany: APS India certificate = 6–8 MONTHS — flag as IMPOSSIBLE if < 7 months left
  • USA: visa interview slots = 4–6 months lead time — flag if < 5 months left
  • UK: CAS + visa = 6–8 weeks minimum
  • Australia: CoE + visa = 4–6 weeks
- Mark milestone: true for: test dates, application deadlines, offer decisions, visa application, departure.

Return ONLY valid JSON (no markdown, no extra text):
{{
  "intake": "{intake}",
  "countries": "{countries_str}",
  "urgent_warnings": ["Specific time-critical warning if any — be direct and actionable"],
  "months": [
    {{
      "month": "Month 1 — [actual calendar month + year]",
      "label": "Short action phase label (e.g. 'IELTS Registration & SOP Draft')",
      "tasks": [
        "Specific task with detail (e.g. 'Register for IELTS at British Council — target 7.0+ for UK programs')",
        "Specific task 2",
        "Specific task 3",
        "Specific task 4"
      ],
      "milestone": false,
      "country_specific": "Country-specific note if any (e.g. 'Germany: apply for APS India certificate THIS WEEK')"
    }}
  ]
}}

Make every task ultra-specific — use the student's actual CGPA, test scores, and target countries in the task text."""

        try:
            resp   = gemini.generate_content(prompt)
            result = _extract_json(resp.text)
            if result and result.get("months"):
                logger.info(f"Gemini timeline generated: {len(result['months'])} months")
                return result
        except Exception as e:
            logger.error(f"Gemini timeline error: {e}")

    return _static_timeline(intake, countries, current_status)


def _static_timeline(intake: str, countries: list = None, status: dict = None) -> dict:
    """Rule-based fallback timeline."""
    countries = countries or ["UK", "Canada"]
    warnings  = []
    if "Germany" in countries or "Germany" in str(countries):
        warnings.append("⚠️ URGENT: APS India certificate for Germany takes 6–8 months. Apply immediately at APS India (Delhi).")
    if "Canada" in countries:
        warnings.append("⚠️ Canada study permit + PAL: Allow 16+ weeks total. Open GIC account now if not done.")
    if "USA" in countries:
        warnings.append("⚠️ US visa interview slots in India book out 4–6 months. Schedule ASAP after receiving I-20.")

    months = [
        {"month": "Now", "label": "Research & Assessment", "milestone": False,
         "tasks": ["Finalise university shortlist (8–12 programs)", "Confirm GRE/IELTS test plans", "Request official transcripts from college"]},
        {"month": "Month 1", "label": "Standardised Tests", "milestone": True,
         "tasks": ["Register for IELTS/TOEFL if not done", "Register for GRE/GMAT if required", "Start SOP draft"]},
        {"month": "Month 2", "label": "Test Preparation", "milestone": False,
         "tasks": ["Intensive test preparation", "Arrange 2–3 Letter of Recommendation (LOR) writers", "Research scholarships and deadlines"]},
        {"month": "Month 3", "label": "Take Tests & Shortlist", "milestone": True,
         "tasks": ["Appear for IELTS/TOEFL", "Appear for GRE/GMAT", "Finalise program shortlist by score"]},
        {"month": "Month 4", "label": "Applications Open", "milestone": True,
         "tasks": ["Submit applications to 3–4 reach universities", "Pay application fees", "Submit SOP + LOR via portals"]},
        {"month": "Month 5", "label": "Complete All Applications", "milestone": False,
         "tasks": ["Submit remaining applications", "Track all application portals", "Prepare financial documents (bank statements, GIC/blocked account)"]},
        {"month": "Month 6", "label": "Offers & Decisions", "milestone": True,
         "tasks": ["Compare offer letters and scholarships", "Accept preferred offer + pay deposit", "Request CAS/I-20/CoE/LoA from university"]},
        {"month": "Month 7", "label": "Visa Application", "milestone": True,
         "tasks": ["Book visa appointment (US: ASAP, UK: 3 weeks processing)", "Prepare all visa documents", "Open GIC/blocked account if not done", "Pay IHS/SEVIS fee"]},
        {"month": "Month 8", "label": "Pre-Departure Prep", "milestone": False,
         "tasks": ["Book flights (early = cheaper)", "Arrange accommodation", "Purchase travel insurance + forex", "Attend pre-departure briefing"]},
        {"month": "Month 9", "label": "Arrival & Orientation", "milestone": True,
         "tasks": ["Fly to destination", "Attend university orientation", "Register with local immigration (IRP/BRP/ARC)"]},
    ]
    return {"intake": intake or "Fall", "countries": ", ".join(countries), "urgent_warnings": warnings, "months": months}


def analyze_profile(profile: dict) -> dict:
    """
    Comprehensive profile analysis.
    Combines rule-based dimension scoring with Gemini-generated insights.
    """
    profile_txt = _profile_summary(profile)
    scores      = compute_profile_score(profile)
    gemini      = _get_gemini()

    dim = scores["dimensions"]
    dim_text = "\n".join([
        f"  Academic (CGPA): {dim.get('academic',0)}/30",
        f"  English test: {dim.get('english',0)}/20",
        f"  GRE/GMAT: {dim.get('standardized_test',0)}/10",
        f"  Work/research experience: {dim.get('experience',0)}/15",
        f"  Financial preparedness: {dim.get('financial',0)}/10",
        f"  Profile completeness: {dim.get('completeness',0)}/10",
        f"  Career clarity & planning: {dim.get('clarity',0)}/5",
    ])

    target_countries = profile.get("target_countries") or ["UK", "USA", "Canada", "Australia", "Germany"]

    if gemini:
        prompt = f"""You are StudyPathway's expert career counsellor for Indian students going abroad.

Analyse this student's study-abroad profile and return a comprehensive JSON analysis.

STUDENT PROFILE:
{profile_txt}

COMPUTED DIMENSION SCORES (use these numbers exactly):
{dim_text}
TOTAL SCORE: {scores['total']}/100 ({scores['grade']})

Return ONLY valid JSON (no markdown):
{{
  "overall_score": {scores['total']},
  "grade": "{scores['grade']}",
  "dimension_scores": {{
    "academic": {dim.get('academic',0)},
    "english": {dim.get('english',0)},
    "standardized_test": {dim.get('standardized_test',0)},
    "experience": {dim.get('experience',0)},
    "financial": {dim.get('financial',0)},
    "completeness": {dim.get('completeness',0)},
    "clarity": {dim.get('clarity',0)}
  }},
  "strengths": [
    "Specific strength 1 with exact numbers (e.g., 'Strong CGPA of 8.4/10 — above median for top-100 programs')",
    "Specific strength 2",
    "Specific strength 3"
  ],
  "gaps": [
    "Specific gap 1 with concrete impact (e.g., 'No IELTS score — blocks all UK/Canada applications')",
    "Specific gap 2",
    "Specific gap 3"
  ],
  "actions": [
    {{
      "action": "Specific action with exact target (e.g., 'Book IELTS at British Council — aim for 7.0+')",
      "impact": "high",
      "effort": "high",
      "deadline": "Within 2 months",
      "why": "One sentence explaining impact"
    }}
  ],
  "match_countries": [
    {{
      "country": "{target_countries[0] if target_countries else 'UK'}",
      "fit": 75,
      "reason": "Specific reason based on profile"
    }}
  ],
  "verdict": "One encouraging paragraph (3-4 sentences) summarising the student's position, being honest but motivating. Mention their actual CGPA and strongest aspects."
}}

CRITICAL RULES:
- Use the student's EXACT numbers from the profile above — never generic advice.
- Every strength/gap must contain a specific number or fact from the profile.
- Every action must have a concrete target (e.g. "Aim for IELTS 7.0+" not just "take IELTS").
- Country fit must reflect THIS student's actual CGPA/test scores/budget vs that country's requirements.
- Generate 4-5 strengths, 4-5 gaps, 5-6 actions, country fit for ALL target countries: {', '.join(target_countries[:6])}.
- Verdict must mention the student's actual CGPA and their single biggest competitive advantage."""

        try:
            resp   = gemini.generate_content(prompt)
            result = _extract_json(resp.text)
            if result and result.get("overall_score") is not None:
                # Ensure dimension scores use our computed values (not AI hallucinations)
                result["dimension_scores"] = scores["dimensions"]
                result["overall_score"]    = scores["total"]
                result["grade"]            = scores["grade"]
                logger.info(f"Gemini profile analysis done: score={scores['total']}")
                return result
        except Exception as e:
            logger.error(f"Gemini profile analysis error: {e}")

    # Rule-based fallback
    return _static_profile_analysis(profile, scores)


def _static_profile_analysis(profile: dict, scores: dict) -> dict:
    dim = scores["dimensions"]
    cgpa = float(profile.get("cgpa") or 0)
    strengths, gaps, actions = [], [], []

    if dim["academic"] >= 24:
        strengths.append(f"Strong academic record — CGPA {cgpa}/10 is above the median for competitive programs")
    elif dim["academic"] >= 15:
        strengths.append(f"Solid CGPA of {cgpa}/10 — competitive for most top-100 programs")
    else:
        gaps.append(f"CGPA {cgpa}/10 is below median for top universities — consider explaining grade trends in SOP")

    if dim["english"] >= 15:
        strengths.append(f"Strong English proficiency — {profile.get('english_test')} {profile.get('english_score','')}")
    elif dim["english"] == 0:
        gaps.append("No English test score — this blocks applications to all major study destinations")
        actions.append({"action": "Register for IELTS immediately (target 7.0+)", "impact": "high", "effort": "high", "deadline": "Within 3 months", "why": "Without IELTS/TOEFL, no application can be submitted"})

    if dim["experience"] >= 9:
        strengths.append(f"Valuable work experience of {profile.get('work_experience_years')} years")
    elif dim["experience"] <= 3:
        gaps.append("Limited work/research experience — build via internships or research projects")

    countries = profile.get("target_countries") or ["UK", "Canada", "Australia"]
    match_countries = [{"country": c, "fit": min(95, scores["total"] + 5), "reason": f"Aligns with your profile"} for c in countries[:5]]

    verdict = f"Your profile scores {scores['total']}/100 ({scores['grade']}). "
    if scores["total"] >= 70:
        verdict += "You are well-positioned for competitive programs — focus on completing outstanding test scores and applications."
    elif scores["total"] >= 50:
        verdict += "A solid foundation exists. Prioritise IELTS/GRE completion and strengthen your SOP to reach your target universities."
    else:
        verdict += "There is significant room to improve your profile. Start with English tests and boosting the completeness of your profile before applying."

    return {
        "overall_score": scores["total"], "grade": scores["grade"],
        "dimension_scores": dim, "strengths": strengths or ["Academic foundation in place"],
        "gaps": gaps or ["Continue building your profile"], "actions": actions or [],
        "match_countries": match_countries, "verdict": verdict,
    }


def ai_coach_chat(message: str, profile: dict, history: list) -> str:
    """
    AI study coach: answers any study-abroad question personalised to the student.
    Gemini is the primary model.
    """
    gemini      = _get_gemini()
    profile_txt = _profile_summary(profile)

    system = (
        "You are StudyPathway's AI Study Coach — the world's best advisor for Indian students planning to study abroad.\n\n"
        "You are an expert on: UK/USA/Canada/Germany/Australia/Netherlands/Singapore/Ireland/Japan/France/Sweden visa requirements, "
        "university applications, IELTS/TOEFL/GRE/GMAT preparation strategies, scholarships (Chevening, Fulbright, DAAD, MEXT, GKS, Commonwealth), "
        "financial planning, on-campus jobs, post-study work rights, housing, and Indian student life abroad.\n\n"
        f"STUDENT PROFILE:\n{profile_txt}\n\n"
        "RESPONSE STYLE:\n"
        "- Be warm, specific, and actionable\n"
        "- Always tailor advice to THIS student's profile (use their actual CGPA, test scores, countries, budget)\n"
        "- Use bullet points and **bold** for key terms\n"
        "- Give concrete numbers: fees, timelines, score requirements\n"
        "- When you don't know something specific, say so and suggest where to verify\n"
        "- Keep responses focused — 200–400 words maximum unless the question requires detail\n"
    )

    # Build conversation
    convo_parts = [f"[SYSTEM CONTEXT]\n{system}\n\n[CONVERSATION]"]
    for h in history[-8:]:
        role = "Student" if h["role"] == "user" else "Coach"
        convo_parts.append(f"{role}: {h['content']}")
    convo_parts.append(f"Student: {message}")
    convo_parts.append("Coach:")

    full_prompt = "\n\n".join(convo_parts)

    if gemini:
        try:
            resp = gemini.generate_content(full_prompt)
            return resp.text
        except Exception as e:
            logger.error(f"Gemini chat error: {e}")

    # Anthropic fallback
    client = _get_anthropic_client()
    if client:
        try:
            messages = [{"role": h["role"], "content": h["content"]} for h in history[-8:]]
            messages.append({"role": "user", "content": message})
            resp = client.messages.create(
                model="claude-haiku-4-5", max_tokens=800,
                system=system, messages=messages,
            )
            return resp.content[0].text
        except Exception as e:
            logger.error(f"Claude chat fallback error: {e}")

    return (
        "I'm sorry, the AI service is temporarily unavailable. "
        "Please check that your GOOGLE_API_KEY is configured in the .env file."
    )


# ── University → Country lookup ────────────────────────────────────────────────
# Maps common university names (lowercase, partial) → actual country
_UNI_COUNTRY_LOOKUP: dict = {
    # Spain
    "ie university": "Spain", "ie business school": "Spain",
    "esade": "Spain", "iese": "Spain", "esic": "Spain",
    "universidad de navarra": "Spain", "universidad complutense": "Spain",
    "universidad de barcelona": "Spain", "pompeu fabra": "Spain",
    "autonomous university of barcelona": "Spain", "uab": "Spain",

    # Italy
    "bocconi": "Italy", "università bocconi": "Italy",
    "politecnico di milano": "Italy", "polimi": "Italy",
    "university of milan": "Italy", "sapienza": "Italy",
    "luiss": "Italy", "scuola normale superiore": "Italy",

    # France
    "hec paris": "France", "insead": "France",
    "sciences po": "France", "école polytechnique": "France",
    "ecole polytechnique": "France", "sorbonne": "France",
    "paris-saclay": "France", "ens paris": "France",
    "em lyon": "France", "essec": "France", "edhec": "France",
    "grenoble école de management": "France",

    # Germany
    "technical university of munich": "Germany", "tum": "Germany",
    "lmu munich": "Germany", "lmu münchen": "Germany",
    "heidelberg university": "Germany", "heidelberg": "Germany",
    "humboldt": "Germany", "free university of berlin": "Germany",
    "rwth aachen": "Germany", "karlsruhe": "Germany",
    "goethe university": "Germany", "mannheim": "Germany",
    "whu": "Germany", "esmt berlin": "Germany",

    # Netherlands
    "delft university": "Netherlands", "tu delft": "Netherlands",
    "university of amsterdam": "Netherlands", "erasmus": "Netherlands",
    "eindhoven": "Netherlands", "leiden": "Netherlands",
    "tilburg": "Netherlands", "vrije universiteit": "Netherlands",
    "vu amsterdam": "Netherlands", "maastricht": "Netherlands",

    # Switzerland
    "eth zurich": "Switzerland", "eth zürich": "Switzerland",
    "epfl": "Switzerland", "university of zurich": "Switzerland",
    "university of geneva": "Switzerland", "university of st. gallen": "Switzerland",
    "st gallen": "Switzerland", "hsg": "Switzerland", "imd lausanne": "Switzerland",

    # United Kingdom
    "oxford": "United Kingdom", "cambridge": "United Kingdom",
    "imperial college": "United Kingdom", "ucl": "United Kingdom",
    "university college london": "United Kingdom",
    "london school of economics": "United Kingdom", "lse": "United Kingdom",
    "king's college london": "United Kingdom", "kcl": "United Kingdom",
    "edinburgh": "United Kingdom", "manchester": "United Kingdom",
    "warwick": "United Kingdom", "bristol": "United Kingdom",
    "glasgow": "United Kingdom", "nottingham": "United Kingdom",
    "southampton": "United Kingdom", "exeter": "United Kingdom",
    "durham": "United Kingdom", "birmingham": "United Kingdom",
    "leeds": "United Kingdom", "sheffield": "United Kingdom",
    "london business school": "United Kingdom", "lbs": "United Kingdom",
    "said business school": "United Kingdom", "judge business school": "United Kingdom",
    "cranfield": "United Kingdom", "bath": "United Kingdom",
    "strathclyde": "United Kingdom",

    # United States
    "mit": "United States", "massachusetts institute of technology": "United States",
    "stanford": "United States", "harvard": "United States",
    "caltech": "United States", "uchicago": "United States",
    "university of chicago": "United States", "columbia": "United States",
    "yale": "United States", "princeton": "United States",
    "cornell": "United States", "upenn": "United States",
    "university of pennsylvania": "United States",
    "johns hopkins": "United States", "duke": "United States",
    "northwestern": "United States", "dartmouth": "United States",
    "brown": "United States", "vanderbilt": "United States",
    "rice": "United States", "notre dame": "United States",
    "uc berkeley": "United States", "berkeley": "United States",
    "ucla": "United States", "michigan": "United States",
    "carnegie mellon": "United States", "cmu": "United States",
    "nyu": "United States", "new york university": "United States",
    "georgia tech": "United States", "purdue": "United States",
    "illinois": "United States", "texas": "United States",
    "usc": "United States", "tufts": "United States",
    "boston university": "United States", "northeastern": "United States",
    "wharton": "United States", "booth": "United States",
    "kellogg": "United States", "sloan": "United States",
    "haas": "United States", "fuqua": "United States",

    # Canada
    "university of toronto": "Canada", "toronto": "Canada",
    "mcgill": "Canada", "ubc": "Canada",
    "university of british columbia": "Canada",
    "waterloo": "Canada", "alberta": "Canada",
    "western university": "Canada", "mcmaster": "Canada",
    "queen's university": "Canada", "montreal": "Canada",
    "hec montréal": "Canada", "ivey": "Canada",
    "rotman": "Canada", "schulich": "Canada",

    # Australia
    "australian national university": "Australia", "anu": "Australia",
    "university of melbourne": "Australia", "melbourne": "Australia",
    "university of sydney": "Australia",
    "university of queensland": "Australia", "uq": "Australia",
    "monash": "Australia", "unsw": "Australia",
    "university of new south wales": "Australia",
    "university of western australia": "Australia",
    "macquarie": "Australia", "rmit": "Australia",
    "university of adelaide": "Australia",

    # Singapore
    "nus": "Singapore", "national university of singapore": "Singapore",
    "ntu": "Singapore", "nanyang technological": "Singapore",
    "smu": "Singapore", "singapore management university": "Singapore",
    "insead asia": "Singapore",

    # Japan
    "university of tokyo": "Japan", "todai": "Japan",
    "kyoto university": "Japan", "osaka university": "Japan",
    "waseda": "Japan", "keio": "Japan",

    # South Korea
    "seoul national university": "South Korea", "snu": "South Korea",
    "kaist": "South Korea", "yonsei": "South Korea", "korea university": "South Korea",

    # Sweden
    "karolinska": "Sweden", "kth": "Sweden",
    "lund university": "Sweden", "stockholm school of economics": "Sweden",
    "chalmers": "Sweden",

    # Denmark
    "copenhagen business school": "Denmark", "cbs": "Denmark",
    "university of copenhagen": "Denmark", "dtu": "Denmark",

    # Norway / Finland
    "university of oslo": "Norway", "ntnu": "Norway",
    "aalto": "Finland", "helsinki": "Finland",

    # Ireland
    "trinity college dublin": "Ireland", "tcd": "Ireland",
    "university college dublin": "Ireland", "ucd": "Ireland",
    "national university of ireland": "Ireland",

    # UAE
    "khalifa university": "UAE", "university of dubai": "UAE",
    "american university of sharjah": "UAE", "american university in dubai": "UAE",

    # China / Hong Kong
    "peking university": "China", "tsinghua": "China",
    "hkust": "Hong Kong", "hku": "Hong Kong",
    "university of hong kong": "Hong Kong",
    "chinese university of hong kong": "Hong Kong", "cuhk": "Hong Kong",
    "city university of hong kong": "Hong Kong",

    # Portugal
    "nova school of business": "Portugal", "nova sbe": "Portugal",
    "universidade de lisboa": "Portugal", "católica lisbon": "Portugal",

    # Belgium
    "ku leuven": "Belgium", "vlerick": "Belgium", "solvay": "Belgium",
    "ghent university": "Belgium",
}


def resolve_university_country(university: str, user_country: str = "") -> dict:
    """
    Returns the best-known country for a university.
    Priority: our lookup dict > user-provided value > unknown.
    Returns dict: {country, source, note}
    """
    if not university:
        return {"country": user_country or "", "source": "user", "note": ""}

    key = university.lower().strip()
    # Exact match first
    if key in _UNI_COUNTRY_LOOKUP:
        actual = _UNI_COUNTRY_LOOKUP[key]
        note   = ""
        if user_country and user_country != actual:
            note = f"{university} is in {actual}, not {user_country}. SOP tailored to {actual} requirements."
        return {"country": actual, "source": "lookup", "note": note}

    # Partial match — check if any key is contained in the university name
    for lookup_key, lookup_country in _UNI_COUNTRY_LOOKUP.items():
        if lookup_key in key or key in lookup_key:
            actual = lookup_country
            note   = ""
            if user_country and user_country != actual:
                note = f"{university} appears to be in {actual}, not {user_country}. SOP tailored to {actual}."
            return {"country": actual, "source": "lookup", "note": note}

    # Not found — trust user input
    if user_country:
        return {"country": user_country, "source": "user", "note": ""}

    return {"country": "", "source": "unknown", "note": "Country not identified — provide country-specific guidance manually."}


def generate_sop_outline(profile: dict, university: str, program: str, country: str = "") -> str:
    """Generate a personalised SOP outline. Gemini primary, no hallucination."""
    gemini      = _get_gemini()
    profile_txt = _profile_summary(profile)

    field        = profile.get("field_of_study", "")
    cgpa         = profile.get("cgpa", "")
    work_years   = profile.get("work_experience_years", 0) or 0
    career_goal  = profile.get("career_goal", "")
    eng_test     = profile.get("english_test", "")
    eng_score    = profile.get("english_score", "")
    gre_score    = profile.get("gre_score", "")
    gmat_score   = profile.get("gmat_score", "")
    budget       = profile.get("budget_inr") or profile.get("budget", "")
    home_uni     = profile.get("home_university", "")
    current_deg  = profile.get("current_degree", "")
    grad_year    = profile.get("graduation_year", "")
    ranking_pref = profile.get("ranking_preference", "")
    scholarship  = profile.get("scholarship_interest", False)
    work_abroad  = profile.get("work_abroad_interest", False)

    # Build a rich "what we know" block from the profile
    known_data_lines = []
    if home_uni:        known_data_lines.append(f"Current institution: {home_uni}")
    if current_deg:     known_data_lines.append(f"Current degree: {current_deg}")
    if grad_year:       known_data_lines.append(f"Graduation year: {grad_year}")
    if cgpa:            known_data_lines.append(f"CGPA: {cgpa}/10")
    if field:           known_data_lines.append(f"Field of study: {field}")
    if career_goal:     known_data_lines.append(f"Career goal: {career_goal}")
    if work_years:      known_data_lines.append(f"Work/internship experience: {work_years} years")
    if eng_test and eng_score: known_data_lines.append(f"English: {eng_test} {eng_score}")
    if gre_score:       known_data_lines.append(f"GRE: {gre_score}")
    if gmat_score:      known_data_lines.append(f"GMAT: {gmat_score}")
    if scholarship:     known_data_lines.append("Interested in scholarships: YES")
    if work_abroad:     known_data_lines.append("Plans to work abroad post-study: YES")
    if ranking_pref:    known_data_lines.append(f"University ranking preference: {ranking_pref}")
    known_data = "\n".join(known_data_lines) if known_data_lines else "Limited profile data — use placeholders"

    # Country-specific SOP notes
    country_note = ""
    country_notes_map = {
        "United Kingdom": (
            "UK universities want a focused academic SOP (600-800 words). Emphasise academic curiosity, "
            "specific research interests, and why THIS programme. Avoid career-focused language — "
            "UK personal statements are about intellectual passion, not job outcomes."
        ),
        "United States": (
            "US graduate programmes want 1-2 pages. Cover academic background, research experience, "
            "specific faculty you want to work with, and career goals. Mention GRE/GMAT scores in context. "
            "Show fit with the programme's research strengths."
        ),
        "Canada": (
            "Canadian SOPs are similar to US (1-2 pages). Emphasise research potential, academic fit, "
            "and how the programme supports your long-term career in Canada or globally. "
            "Mention if you're open to co-op/internship opportunities."
        ),
        "Germany": (
            "German universities (especially TU9) want a formal Motivationsschreiben. Emphasise "
            "academic and technical skills. Keep it structured and formal — less storytelling, more "
            "competence demonstration. Mention German language skills if any. APS certificate required."
        ),
        "Australia": (
            "Australian SOPs are typically 500-1000 words. Cover academic background, career goals, "
            "and why Australia/this institution. Emphasise post-study work intentions if relevant."
        ),
        "Netherlands": (
            "Dutch universities want a motivation letter (500-800 words). Focus on academic motivation, "
            "research interests, and why the Netherlands/this specific programme. Many programmes are "
            "in English — highlight language proficiency."
        ),
        "Singapore": (
            "NUS/NTU SOPs should be concise (500-800 words). Emphasise academic excellence, "
            "research background, and alignment with Singapore's tech/finance/research ecosystem. "
            "Competition is intense — highlight what sets you apart."
        ),
        "Ireland": (
            "Irish university SOPs are typically 500-700 words. Similar to UK style — focus on "
            "academic fit and genuine interest in the programme. Ireland's post-study visa is attractive "
            "— you can mention interest in staying post-graduation."
        ),
    }
    if country in country_notes_map:
        country_note = f"\nCOUNTRY-SPECIFIC GUIDANCE FOR {country.upper()}:\n{country_notes_map[country]}\n"

    prompt = f"""You are an expert study-abroad SOP advisor helping an Indian student craft a compelling Statement of Purpose.

University: {university or "[University Name]"}
Programme: {program or "[Programme Name]"}
Country: {country or "[Country]"}

CONFIRMED STUDENT DATA (only use what is listed — never invent):
{known_data}
{country_note}
WRITING RULES (strictly enforced):
1. NEVER invent internships, projects, publications, awards, or experiences not in the data above.
2. NO asterisks (*) anywhere. Use plain numbered lists and dashes only.
3. Where data is missing, write a clear placeholder: [Add your own: ...]
4. Every sentence must be grounded in a real data point from the profile above.
5. Be specific — use the actual CGPA number, the actual test score, the actual work years.
6. Write in first-person prose for each section, not bullet points — this is a narrative document.
7. After each section heading, give the actual draft text (not just advice about what to write).

---

Write a complete 7-section SOP outline WITH draft text for each section:

Section 1: Opening Hook  (50-80 words)
Write an actual opening paragraph that hooks the reader using the student's real field ({field or "their field of study"}) and a genuine motivation rooted in their background. If career goal is known ({career_goal or "not specified"}), tie it in. No cliches like "since childhood I dreamed". End with: [Tip: personalise with a specific moment or project you encountered at {home_uni or "your university"}]

Section 2: Academic Background  (150-200 words)
Draft prose covering their CGPA of {cgpa or "X"}/10 from {home_uni or "their institution"} in {field or "their field"}, graduating {grad_year or "their graduation year"}. Acknowledge if CGPA is below 8.0 and suggest framing (upward trend, strong final years, relevant coursework). Mention their {eng_test + " score of " + str(eng_score) if eng_test and eng_score else "English proficiency test"} as evidence of readiness for {country or "the target country"}'s academic environment. End with: [Tip: add 2-3 relevant courses or a capstone project name here]

Section 3: Research, Projects & Work Experience  (150-200 words)
Draft prose for {work_years} year(s) of experience. If work_years is 0, frame academic projects, internships, or thesis work instead. Connect this experience directly to {program or "the target programme"}. End with: [Tip: describe your most relevant project/role in 2-3 sentences — what problem you solved, what you built, what you learned]

Section 4: Why {program or "This Programme"} at {university or "This University"}  (100-150 words)
Draft prose with 2-3 specific, verifiable reasons this student chose {university or "this university"} and {program or "this programme"}. Connect to their career goal ({career_goal or "stated career goals"}). Reference the institution's known strengths in their field. End with: [Tip: name a specific faculty member, research lab, or course from the university website]

Section 5: Short-term and Long-term Career Goals  (100-150 words)
Draft prose for career goals in {country or "the destination country"} and beyond. Short-term (0-2 years post-graduation): specific role in {field or "their field"}. Long-term (5+ years): leadership/impact goal. Ground everything in their career goal: "{career_goal or "not specified"}". {"Mention post-study work interest explicitly." if work_abroad else ""} End with: [Tip: mention a specific industry trend or company you want to contribute to]

Section 6: Why You Will Succeed  (100-150 words)
Draft prose making the case using ONLY real evidence: CGPA {cgpa or "X"}/10{", " + eng_test + " " + str(eng_score) if eng_test else ""}{", GRE " + str(gre_score) if gre_score else ""}{", " + str(work_years) + " years work experience" if work_years else ""}. Frame any weaknesses positively. Show self-awareness and a learning mindset. End with: [Tip: add one specific example of overcoming a challenge — academic or professional]

Section 7: Closing Statement  (50-80 words)
Draft a confident, enthusiastic close. Reference the university by name, the specific programme, and one concrete contribution you will make. Avoid generic sentences. Must end on a forward-looking, confident note. End with: [Tip: reference how this degree connects to your vision for {career_goal or "your career"} specifically]

---

After all 7 sections, add:

OVERALL WORD COUNT TARGET: 800-1000 words for {country or "this country"}'s application standard.
STRONGEST ELEMENTS OF THIS PROFILE: [list 2-3 genuine strengths from the data above]
AREAS TO STRENGTHEN BEFORE SUBMITTING: [list 2-3 honest gaps and how to address them]"""

    if gemini:
        try:
            resp = gemini.generate_content(prompt)
            return resp.text
        except Exception as e:
            logger.error(f"Gemini SOP error: {e}")

    client = _get_anthropic_client()
    if client:
        try:
            resp = client.messages.create(
                model="claude-haiku-4-5", max_tokens=2000,
                messages=[{"role": "user", "content": prompt}],
            )
            return resp.content[0].text
        except Exception as e:
            logger.error(f"Claude SOP fallback error: {e}")

    return "SOP generation unavailable. Please ensure GOOGLE_API_KEY is configured in your .env file."
