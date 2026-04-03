"""
PharmAssist — Medication Management Difficulty Risk Screener
Compact single-page layout — 4 columns, no scrolling
"""

import streamlit as st
import numpy as np
import pandas as pd
import joblib
from datetime import datetime
import io
import urllib.parse

# ReportLab for PDF generation
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                 TableStyle, HRFlowable, PageBreak)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

# ── PAGE CONFIG ───────────────────────────────────────────────────
st.set_page_config(
    page_title="PharmAssist — Medication Risk Screener",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── CSS ───────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* ── Animated background ───────────────────────────────── */
    @keyframes bgShift {
        0%   { background-position: 0% 50%; }
        50%  { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    .stApp {
        background: linear-gradient(135deg,
            #E8F4FD, #EEF2FF, #E0F7FA, #F3E5F5, #E8F5E9, #FFF8E1);
        background-size: 400% 400%;
        animation: bgShift 18s ease infinite;
    }

    /* ── Global spacing ─────────────────────────────────────── */
    .block-container { padding: 0.5rem 1.0rem 0.3rem 1.0rem !important; }
    div[data-testid="stVerticalBlock"] > div { gap: 0.18rem; }
    .element-container { margin-bottom: 0 !important; }

    /* ── Header ─────────────────────────────────────────────── */
    .header {
        background: linear-gradient(135deg, #1F4E79, #2E75B6, #1565C0);
        background-size: 200% 200%;
        animation: bgShift 8s ease infinite;
        padding: 8px 18px; border-radius: 8px;
        margin-bottom: 8px; color: white;
        display: flex; align-items: center; gap: 12px;
        box-shadow: 0 2px 12px rgba(31,78,121,0.25);
    }
    .header h1 { color: white; font-size: 1.3rem; margin: 0; }
    .header p  { color: #CCE4F7; font-size: 0.72rem; margin: 0; }

    /* ── Section labels ─────────────────────────────────────── */
    .sec-label {
        font-size: 0.72rem; font-weight: 700; color: #1F4E79;
        text-transform: uppercase; letter-spacing: 0.5px;
        border-bottom: 2px solid #DDEEFF; padding-bottom: 2px;
        margin-bottom: 3px; margin-top: 5px;
    }

    /* ── Risk card (inline: icon + label + prob in one row) ─── */
    .risk-card {
        border-radius: 9px; padding: 8px 12px; margin-bottom: 5px;
        display: flex; align-items: center; justify-content: space-between;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    }
    .risk-high     { background: linear-gradient(135deg,#B71C1C,#E53935); color:white; }
    .risk-moderate { background: linear-gradient(135deg,#E65100,#FB8C00); color:white; }
    .risk-low      { background: linear-gradient(135deg,#1B5E20,#43A047); color:white; }
    .risk-left  { display:flex; align-items:center; gap:7px; }
    .risk-emoji { font-size:1.3rem; }
    .risk-label { font-size:0.9rem; font-weight:800; line-height:1.1; }
    .risk-sub   { font-size:0.62rem; opacity:0.85; font-weight:500; }
    .risk-pct   { font-size:1.15rem; font-weight:800; white-space:nowrap; }

    /* ── Compact factor row (single line) ───────────────────── */
    .frow {
        display:flex; align-items:center; gap:5px;
        background:#F0F6FF; border-radius:5px;
        padding:3px 7px; margin:2px 0; font-size:0.71rem;
    }
    .frow-dir  { font-size:0.75rem; flex-shrink:0; }
    .frow-name { font-weight:700; color:#1F4E79; flex:1 1 auto; white-space:nowrap;
                 overflow:hidden; text-overflow:ellipsis; }
    .frow-val  { color:#666; flex-shrink:0; white-space:nowrap; }
    .frow-bar-wrap { width:40px; height:4px; border-radius:2px;
                     flex-shrink:0; overflow:hidden; }
    .frow-bar-red   { background:#FFD0D0; }
    .frow-bar-green { background:#C8F0D0; }
    .frow-bar-fill-red   { background:#C00000; height:4px; border-radius:2px; }
    .frow-bar-fill-green { background:#2E7D32; height:4px; border-radius:2px; }

    /* ── Compact rec rows (single line each) ────────────────── */
    .rrow {
        display:flex; align-items:center; gap:6px;
        border-radius:5px; padding:4px 7px; margin:2px 0;
        font-size:0.70rem; color:#333;
    }
    .rrow-urgent   { background:#FFF0F0; border-left:3px solid #C00000; }
    .rrow-standard { background:#EFF6FF; border-left:3px solid #2E75B6; }
    .rrow-monitor  { background:#F0FFF4; border-left:3px solid #2E7D32; }
    .rrow-icon  { font-size:0.85rem; flex-shrink:0; }
    .rrow-title { font-weight:700; flex-shrink:0; margin-right:3px; }
    .rrow-body  { color:#555; }

    /* ── Disclaimer strip ───────────────────────────────────── */
    .disclaimer {
        background:rgba(255,253,230,0.85); border:1px solid #F9A825;
        border-radius:5px; padding:4px 8px;
        font-size:0.63rem; color:#666; margin-top:4px;
    }

    /* ── Inputs ─────────────────────────────────────────────── */
    .stSlider { padding-top:0 !important; padding-bottom:0 !important; }
    .stSlider > label { font-size:0.74rem !important; margin-bottom:0 !important; }
    .stNumberInput > label { font-size:0.74rem !important; }
    .stSelectbox > label   { font-size:0.74rem !important; }
    .stTextInput > label   { font-size:0.74rem !important; }

    /* ── Assess button ──────────────────────────────────────── */
    .stButton > button {
        background: linear-gradient(135deg,#1F4E79,#2E75B6);
        color:white; border:none; border-radius:7px;
        padding:7px 0; font-size:0.85rem; font-weight:700;
        width:100%; margin-top:4px;
        box-shadow: 0 2px 8px rgba(31,78,121,0.3);
        transition: transform 0.1s;
    }
    .stButton > button:hover { transform: translateY(-1px); }

    footer { visibility:hidden; }
    #MainMenu { visibility:hidden; }
    header[data-testid="stHeader"] { visibility:hidden; }
    [data-testid="stToolbar"] { display:none; }
    .stToolbar { display:none; }
</style>
""", unsafe_allow_html=True)

# ── LOAD MODEL ────────────────────────────────────────────────────
@st.cache_resource
def load_model():
    try:
        return joblib.load('lr_model.pkl'), joblib.load('scaler.pkl'), True
    except FileNotFoundError:
        return None, None, False

model, scaler, model_loaded = load_model()

PREDICTORS = [
    'NumRx','NumOTC','NumHerbal','NumHealthProb','RateHealth','HospLastYear',
    'Fin_Hardship','Transport','Side_Effects','Social_Support','Fam_Friend',
    'Age','Education','HouseIncome','RuralUrban',
    'Total_Meds','Barrier_Score','Support_Score','Health_Score'
]
LABEL_MAP = {
    'NumRx':'Prescription Drugs','NumOTC':'OTC Medications',
    'NumHerbal':'Herbal Supplements','NumHealthProb':'Health Problems',
    'RateHealth':'Self-Rated Health','HospLastYear':'Hospitalized/Year',
    'Fin_Hardship':'Financial Hardship','Transport':'Transportation Barrier',
    'Side_Effects':'Side Effects','Social_Support':'Social Support',
    'Fam_Friend':'Family/Friend Reliance','Age':'Age',
    'Education':'Education','HouseIncome':'Household Income',
    'RuralUrban':'Geographic Area','Total_Meds':'Total Medication Burden',
    'Barrier_Score':'Combined Barrier Score','Support_Score':'Combined Support Score',
    'Health_Score':'Combined Health Score',
}

# ── AVERAGE RISK BENCHMARKS (from 2021 NCSME dataset, N=1,521) ────
# These represent the sample-wide prevalence/mean for each input
AVG_RISK_PCT = 42.3   # % of sample classified as High Risk (Med_Difficult=1)

VARIABLE_DEFINITIONS = {
    "Prescription Drugs":     "The number of prescription medications the patient takes daily as ordered by a licensed healthcare provider.",
    "OTC Medications":        "Over-the-counter medications taken daily without a prescription (e.g., pain relievers, antacids, antihistamines).",
    "Herbal Supplements":     "Daily use of herbal or dietary supplements (e.g., vitamins, fish oil, herbal teas with medicinal intent).",
    "No. of Health Problems": "Total number of current diagnosed health conditions the patient is actively managing.",
    "Self-Rated Health":      "Patient's subjective overall health rating: 1=Excellent, 2=Good, 3=Fair, 4=Poor. Higher scores indicate poorer perceived health.",
    "Hospitalized Last Year": "Whether the patient was admitted to a hospital at any point during the past 12 months (Yes=1, No=0).",
    "Financial Hardship":     "Degree to which purchasing medications causes financial difficulty (1=Strongly Disagree to 7=Strongly Agree). Higher = greater barrier.",
    "Transportation Barrier": "Degree to which lack of transportation is a challenge for obtaining healthcare (1=Strongly Disagree to 7=Strongly Agree).",
    "Side Effects Concern":   "Degree to which the patient suffers from adverse reactions or side effects from medications (1=Strongly Disagree to 7=Strongly Agree).",
    "Social Support":         "Degree to which the patient has adequate social support for meeting healthcare needs (1=Strongly Disagree to 7=Strongly Agree).",
    "Family/Friend Reliance": "Degree to which the patient relies on family/friends over professionals for healthcare decisions (1=Strongly Disagree to 7=Strongly Agree).",
    "Year of Birth":          "Patient's birth year (1932–2003). Age is computed as 2021 minus Year of Birth to match the 2021 NCSME survey reference year.",
    "Education Level":        "Highest level of formal education completed, from 1 (High School/GED) to 7 (Doctoral Degree).",
    "Household Income":       "Total household income from all sources in 2020, coded 1 ($20,000 or less) through 8 (More than $140,000).",
    "Geographic Area":        "Whether the patient resides in an urban area (population ≥20,000) or a rural area/town (population <20,000).",
}

REC_DEFINITIONS = {
    "MTM within 48–72 hrs":   "Medication Therapy Management (MTM) is a pharmacist-led service involving a comprehensive review of all medications to optimize therapeutic outcomes, resolve drug-related problems, and improve adherence. High Risk patients should be prioritized within 2–3 business days.",
    "Follow-up in 2 weeks":   "A structured check-in (phone or in-person) to confirm the patient understands their medication regimen, address emerging adherence concerns, and reinforce education before problems escalate.",
    "Routine monitoring":     "Standard care with re-screening at next dispensing visit. No urgent intervention indicated based on current risk profile.",
    "Financial Barrier":      "Assess eligibility for patient assistance programs (PAPs), generic substitutions, 340B drug pricing (if applicable), GoodRx, NeedyMeds, or Medicare Extra Help. High medication costs are among the strongest predictors of non-adherence.",
    "Transport Barrier":      "Explore options including pharmacy home delivery, mail-order pharmacy services, rideshare health programs (Lyft/Uber Health), or community transportation assistance. Transportation barriers disproportionately affect rural and low-income patients.",
    "Side Effects Concern":   "Conduct a thorough adverse drug reaction (ADR) review. Consider alternative formulations (extended-release, topical, etc.), dosing schedule modifications, or therapeutic substitutions. Document all reported adverse effects for the prescriber.",
    "Family/Friend Reliance": "Engage the patient's primary caregiver or family member in the counseling session. Provide written medication schedules, pill organizers, and clear adherence aids. Ensure caregiver understands each medication's purpose and instructions.",
    "Poly-pharmacy":          "A total medication burden of 7+ daily medications significantly increases the risk of drug interactions, ADRs, and regimen complexity-driven non-adherence. Conduct a comprehensive medication review for deprescribing opportunities and duplicate therapies. Recommend medication synchronization to align all refills to a single pickup date.",
    "Younger Patient":        "Patients aged 18–44 in this dataset showed higher perceived medication management difficulty despite lower comorbidity burdens. Provide targeted health literacy education, digital adherence tools (apps, pill reminders), and motivational counseling.",
}


# ── PDF REPORT GENERATOR ──────────────────────────────────────────
def generate_pdf_report(patient_name, date_str, tier, pct, raw, raw_display,
                        pos_factors, neg_factors, recs_list, year_born, age,
                        num_rx, num_otc, num_herbal, num_health, rate_health,
                        hosp, fin_hardship, transport, side_effects,
                        social_support, fam_friend, education, income, rural,
                        total_meds, barrier_score, support_score, health_score):

    buffer = io.BytesIO()
    W = 7.2 * inch
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                            topMargin=0.5*inch, bottomMargin=0.5*inch,
                            leftMargin=0.65*inch, rightMargin=0.65*inch)

    DARK_BLUE  = colors.HexColor('#1F4E79')
    MED_BLUE   = colors.HexColor('#2E75B6')
    HIGH_RED   = colors.HexColor('#C00000')
    MOD_ORANGE = colors.HexColor('#E65100')
    LOW_GREEN  = colors.HexColor('#1B5E20')
    LIGHT_GREY = colors.HexColor('#F5F5F5')
    WARN_YELLOW= colors.HexColor('#FFF9C4')
    WARN_BORDER= colors.HexColor('#F9A825')
    risk_color = HIGH_RED if tier=="HIGH RISK" else (MOD_ORANGE if tier=="MODERATE RISK" else LOW_GREEN)

    S = {
        'title':   ParagraphStyle('title2',  fontSize=16, textColor=colors.white,
                                  fontName='Helvetica-Bold', alignment=TA_LEFT),
        'sub':     ParagraphStyle('sub2',    fontSize=8.5,textColor=colors.HexColor('#CCE4F7'),
                                  fontName='Helvetica', alignment=TA_LEFT),
        'h1':      ParagraphStyle('h1_2',    fontSize=11, textColor=DARK_BLUE,
                                  fontName='Helvetica-Bold', spaceBefore=6, spaceAfter=3),
        'h2':      ParagraphStyle('h2_2',    fontSize=9,  textColor=DARK_BLUE,
                                  fontName='Helvetica-Bold', spaceBefore=3, spaceAfter=2),
        'body':    ParagraphStyle('body2',   fontSize=8,  textColor=colors.black,
                                  fontName='Helvetica', spaceAfter=2, leading=12),
        'small':   ParagraphStyle('small2',  fontSize=7.5,textColor=colors.HexColor('#444444'),
                                  fontName='Helvetica', spaceAfter=1, leading=11),
        'risk_lbl':ParagraphStyle('rlbl',    fontSize=13, textColor=colors.white,
                                  fontName='Helvetica-Bold', alignment=TA_LEFT),
        'risk_pct':ParagraphStyle('rpct',    fontSize=24, textColor=colors.white,
                                  fontName='Helvetica-Bold', alignment=TA_RIGHT),
        'risk_sub':ParagraphStyle('rsub',    fontSize=7.5,textColor=colors.HexColor('#E8F4FD'),
                                  fontName='Helvetica', alignment=TA_LEFT),
        'warn':    ParagraphStyle('warn2',   fontSize=7.5,textColor=colors.HexColor('#7B3F00'),
                                  fontName='Helvetica', leading=10),
    }

    def CP(txt, bold=False, color=None):
        return Paragraph(str(txt), ParagraphStyle('cp2', fontSize=7.5,
            fontName='Helvetica-Bold' if bold else 'Helvetica',
            textColor=color or colors.black, leading=10))

    def IV(txt, bold=False):
        return Paragraph(str(txt), ParagraphStyle('iv2', fontSize=7.5,
            fontName='Helvetica-Bold' if bold else 'Helvetica',
            textColor=DARK_BLUE if bold else colors.black, leading=10))

    def FP(txt, color=None, bold=False):
        return Paragraph(str(txt), ParagraphStyle('fp2', fontSize=7.5,
            fontName='Helvetica-Bold' if bold else 'Helvetica',
            textColor=color or colors.black, leading=10))

    LABEL_MAP_LOCAL = {
        'NumRx':'Prescription Drugs','NumOTC':'OTC Medications',
        'NumHerbal':'Herbal Supplements','NumHealthProb':'Health Problems',
        'RateHealth':'Self-Rated Health','HospLastYear':'Hospitalized/Year',
        'Fin_Hardship':'Financial Hardship','Transport':'Transportation Barrier',
        'Side_Effects':'Side Effects','Social_Support':'Social Support',
        'Fam_Friend':'Family/Friend Reliance','Age':'Age',
        'Education':'Education','HouseIncome':'Household Income',
        'RuralUrban':'Geographic Area','Total_Meds':'Total Medication Burden',
        'Barrier_Score':'Combined Barrier Score','Support_Score':'Combined Support Score',
        'Health_Score':'Combined Health Score',
    }

    rate_health_labels = {1:"Excellent",2:"Good",3:"Fair",4:"Poor"}
    edu_full = {1:"High School/GED",2:"Some College",3:"Associate Degree",
                4:"Bachelor's Degree",5:"Master's Degree",
                6:"Professional Degree",7:"Doctoral Degree"}
    inc_full = {1:"$20,000 or less",2:"$20,001-$40,000",3:"$40,001-$60,000",
                4:"$60,001-$80,000",5:"$80,001-$100,000",6:"$100,001-$120,000",
                7:"$120,001-$140,000",8:"More than $140,000"}

    story = []

    # HEADER
    header_table = Table([[
        Paragraph('<b>PharmAssist</b>', S['title']),
        Paragraph('Medication Management Difficulty Risk Report', S['sub']),
    ]], colWidths=[2.5*inch, 4.7*inch])
    header_table.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,-1),DARK_BLUE),('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('TOPPADDING',(0,0),(-1,-1),10),('BOTTOMPADDING',(0,0),(-1,-1),10),
        ('LEFTPADDING',(0,0),(0,-1),14),('RIGHTPADDING',(-1,0),(-1,-1),14),
    ]))
    story.append(header_table)
    story.append(Spacer(1,5))

    # META ROW
    meta_t = Table([
        [Paragraph('<b>Patient:</b>', S['small']), Paragraph(patient_name, S['small']),
         Paragraph('<b>Date:</b>', S['small']),    Paragraph(date_str, S['small'])],
        [Paragraph('<b>Model:</b>', S['small']),
         Paragraph('Logistic Regression (Recall=81.0%, ROC-AUC=0.867)', S['small']),
         Paragraph('<b>Dataset:</b>', S['small']),
         Paragraph('2021 NCSME Survey (N=1,521)', S['small'])],
    ], colWidths=[0.85*inch, 2.8*inch, 0.75*inch, 2.8*inch])
    meta_t.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,-1),colors.HexColor('#F0F4F8')),
        ('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4),
        ('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),4),
        ('BOX',(0,0),(-1,-1),0.5,colors.HexColor('#CCCCCC')),
        ('INNERGRID',(0,0),(-1,-1),0.3,colors.HexColor('#DDDDDD')),
    ]))
    story.append(meta_t)
    story.append(Spacer(1,7))

    # RISK BANNER
    risk_t = Table([
        [Paragraph(f'<b>{tier}</b>', S['risk_lbl']),
         Paragraph(f'<b>{pct:.1f}%</b>', S['risk_pct'])],
        [Paragraph('MEDICATION MANAGEMENT DIFFICULTY RISK PROBABILITY', S['risk_sub']),
         Paragraph(f'Sample Average: {AVG_RISK_PCT}%',
                   ParagraphStyle('rsub2r',fontSize=7.5,textColor=colors.HexColor('#E8F4FD'),
                                  fontName='Helvetica',alignment=TA_RIGHT))],
    ], colWidths=[4.5*inch, 2.7*inch])
    risk_t.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,-1),risk_color),('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8),
        ('LEFTPADDING',(0,0),(-1,-1),14),('RIGHTPADDING',(-1,0),(-1,-1),14),
    ]))
    story.append(risk_t)
    story.append(Spacer(1,8))

    # RISK ASSESSMENT SUMMARY
    story.append(Paragraph('Risk Assessment Summary', S['h1']))
    story.append(HRFlowable(width=W, thickness=1.2, color=DARK_BLUE, spaceAfter=4))
    cmp_interp = [
        ('HIGH' if tier=='HIGH RISK' else ('MODERATE' if tier=='MODERATE RISK' else 'LOW'),
         HIGH_RED if tier=='HIGH RISK' else (MOD_ORANGE if tier=='MODERATE RISK' else LOW_GREEN), True),
        ('Above avg' if pct>AVG_RISK_PCT else 'Below avg',
         HIGH_RED if pct>AVG_RISK_PCT else LOW_GREEN, True),
        ('High burden' if total_meds>=7 else ('Moderate' if total_meds>=4 else 'Low'),
         HIGH_RED if total_meds>=7 else (MOD_ORANGE if total_meds>=4 else LOW_GREEN), False),
        ('High barriers' if barrier_score>=12 else ('Moderate' if barrier_score>=8 else 'Low'),
         HIGH_RED if barrier_score>=12 else (MOD_ORANGE if barrier_score>=8 else LOW_GREEN), False),
        ('Strong support' if support_score>=10 else ('Moderate' if support_score>=6 else 'Low'),
         LOW_GREEN if support_score>=10 else (MOD_ORANGE if support_score>=6 else HIGH_RED), False),
        ('Poor/Fair' if rate_health>=3 else 'Excellent/Good',
         HIGH_RED if rate_health>=3 else LOW_GREEN, False),
        ('Increases risk' if hosp==1 else 'No recent hospitalization',
         HIGH_RED if hosp==1 else LOW_GREEN, hosp==1),
        ('Rural - access barrier' if rural==0 else 'Urban area',
         MOD_ORANGE if rural==0 else LOW_GREEN, False),
    ]
    cmp_labels = [
        ('Risk Classification',       tier,                             'Based on >=50% threshold'),
        ('Probability of Difficulty',  f'{pct:.1f}%',                  f'{AVG_RISK_PCT}%'),
        ('Total Daily Medications',    str(total_meds),                  '4.2 (sample mean)'),
        ('Barrier Score (3-21)',       str(barrier_score),               '7.1 (sample mean)'),
        ('Support Score (2-14)',       str(support_score),               '8.4 (sample mean)'),
        ('Self-Rated Health',          rate_health_labels.get(rate_health,'—'), 'Good (sample mode)'),
        ('Hospitalized Last Year',     'Yes' if hosp==1 else 'No',      '18.3% of sample'),
        ('Geographic Area',            'Urban' if rural==1 else 'Rural', '63% Urban / 37% Rural'),
    ]
    comparison_rows = [[CP('Outcome',bold=True),CP('Patient Profile',bold=True),
                        CP('Sample Reference',bold=True),CP('Interpretation',bold=True)]]
    for (lbl,val,ref),(interp,icolor,ibold) in zip(cmp_labels,cmp_interp):
        comparison_rows.append([
            CP(lbl,bold=True,color=DARK_BLUE), CP(val), CP(ref),
            CP(interp,bold=ibold,color=icolor),
        ])
    cmp_tbl = Table(comparison_rows, colWidths=[1.8*inch,1.5*inch,1.7*inch,2.2*inch], repeatRows=1)
    cmp_tbl.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),DARK_BLUE),('TEXTCOLOR',(0,0),(-1,0),colors.white),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,LIGHT_GREY]),
        ('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4),
        ('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),
        ('VALIGN',(0,0),(-1,-1),'TOP'),('BOX',(0,0),(-1,-1),0.8,DARK_BLUE),
        ('INNERGRID',(0,0),(-1,-1),0.3,colors.HexColor('#CCCCCC')),
    ]))
    story.append(cmp_tbl)
    story.append(Spacer(1,8))

    # PATIENT INPUTS
    story.append(Paragraph('Patient Inputs', S['h1']))
    story.append(HRFlowable(width=W, thickness=1.2, color=DARK_BLUE, spaceAfter=4))
    inputs_data = [
        [IV('Variable',True),IV('Patient Value',True),IV('Variable',True),IV('Patient Value',True)],
        [IV('Prescription Drugs (Rx)',True),IV(num_rx),IV('OTC Medications',True),IV(num_otc)],
        [IV('Herbal Supplements',True),IV(num_herbal),IV('No. Health Problems',True),IV(num_health)],
        [IV('Self-Rated Health',True),IV(rate_health_labels.get(rate_health,'—')),
         IV('Hospitalized Last Year',True),IV('Yes' if hosp==1 else 'No')],
        [IV('Financial Hardship',True),IV(f'{fin_hardship}/7'),
         IV('Transportation Barrier',True),IV(f'{transport}/7')],
        [IV('Side Effects Concern',True),IV(f'{side_effects}/7'),
         IV('Social Support',True),IV(f'{social_support}/7')],
        [IV('Family/Friend Reliance',True),IV(f'{fam_friend}/7'),
         IV('Year of Birth',True),IV(f'{year_born} (Age: {age})')],
        [IV('Education Level',True),IV(edu_full.get(education,'—')),
         IV('Household Income (2020)',True),IV(inc_full.get(income,'—'))],
        [IV('Geographic Area',True),IV('Urban' if rural==1 else 'Rural'),IV(''),IV('')],
        [IV('COMPOSITE SCORES',True),IV(''),IV(''),IV('')],
        [IV('Total Medications',True),IV(total_meds),IV('Barrier Score',True),IV(f'{barrier_score}/21')],
        [IV('Support Score',True),IV(f'{support_score}/14'),IV('Health Score',True),IV(health_score)],
    ]
    inp_tbl = Table(inputs_data, colWidths=[1.9*inch,1.7*inch,1.9*inch,1.7*inch], repeatRows=1)
    inp_tbl.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),DARK_BLUE),('TEXTCOLOR',(0,0),(-1,0),colors.white),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,LIGHT_GREY]),
        ('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4),
        ('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),
        ('VALIGN',(0,0),(-1,-1),'TOP'),('BOX',(0,0),(-1,-1),0.8,DARK_BLUE),
        ('INNERGRID',(0,0),(-1,-1),0.3,colors.HexColor('#CCCCCC')),
        ('BACKGROUND',(0,9),(-1,9),colors.HexColor('#D6E4F0')),
        ('SPAN',(0,9),(-1,9)),('ALIGN',(0,9),(-1,9),'CENTER'),
    ]))
    story.append(inp_tbl)
    story.append(Spacer(1,8))

    # TOP RISK FACTORS
    story.append(Paragraph('Top Contributing Risk Factors', S['h1']))
    story.append(HRFlowable(width=W, thickness=1.2, color=DARK_BLUE, spaceAfter=4))
    factor_rows = [[FP('#',bold=True),FP('Factor',bold=True),FP('Direction',bold=True),
                    FP('Patient Value',bold=True),FP('Risk Contribution',bold=True)]]
    for i,(feat,contrib) in enumerate(pos_factors[:3],1):
        val = raw_display.get(feat, raw.get(feat,'—'))
        factor_rows.append([FP(str(i),bold=True,color=DARK_BLUE),
            FP(LABEL_MAP_LOCAL.get(feat,feat),bold=True,color=DARK_BLUE),
            FP('Increases Risk',color=HIGH_RED), FP(str(val)),
            FP(f'+{contrib:.3f}',bold=True,color=HIGH_RED)])
    for feat,contrib in neg_factors[:2]:
        val = raw_display.get(feat, raw.get(feat,'—'))
        factor_rows.append([FP('—',color=colors.grey),
            FP(LABEL_MAP_LOCAL.get(feat,feat),bold=True,color=DARK_BLUE),
            FP('Protective',color=LOW_GREEN), FP(str(val)),
            FP(f'{contrib:.3f}',bold=True,color=LOW_GREEN)])
    fac_tbl = Table(factor_rows, colWidths=[0.35*inch,2.2*inch,1.4*inch,1.55*inch,1.7*inch], repeatRows=1)
    fac_tbl.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),DARK_BLUE),('TEXTCOLOR',(0,0),(-1,0),colors.white),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,LIGHT_GREY]),
        ('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4),
        ('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),
        ('VALIGN',(0,0),(-1,-1),'TOP'),('BOX',(0,0),(-1,-1),0.8,DARK_BLUE),
        ('INNERGRID',(0,0),(-1,-1),0.3,colors.HexColor('#CCCCCC')),
    ]))
    story.append(fac_tbl)
    story.append(Spacer(1,8))

    # RECOMMENDED ACTIONS
    story.append(Paragraph('Recommended Pharmacist Actions', S['h1']))
    story.append(HRFlowable(width=W, thickness=1.2, color=DARK_BLUE, spaceAfter=4))
    for i,rec in enumerate(recs_list,1):
        rec_def = ''
        for key,defn in REC_DEFINITIONS.items():
            if key.lower() in rec.lower() or any(w in rec.lower() for w in key.lower().split()):
                rec_def = defn; break
        is_urgent = any(kw in rec for kw in ['MTM','Financial','Transport'])
        rec_bg    = colors.HexColor('#FFF0F0') if is_urgent else colors.HexColor('#EFF6FF')
        rec_bdr   = HIGH_RED if is_urgent else MED_BLUE
        rec_tbl   = Table([[Paragraph(f'<b>{i}. {rec}</b>', S['h2'])],
                            [Paragraph(rec_def or '—', S['small'])]], colWidths=[W])
        rec_tbl.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,-1),rec_bg),
            ('LEFTPADDING',(0,0),(-1,-1),10),('RIGHTPADDING',(0,0),(-1,-1),8),
            ('TOPPADDING',(0,0),(-1,0),5),('BOTTOMPADDING',(0,-1),(-1,-1),5),
            ('LINEBEFORE',(0,0),(0,-1),4,rec_bdr),
            ('BOX',(0,0),(-1,-1),0.5,colors.HexColor('#CCCCCC')),
        ]))
        story.append(rec_tbl)
        story.append(Spacer(1,4))

    # DEFINITIONS - flows naturally, no page break
    story.append(Spacer(1,8))
    story.append(Paragraph('Variable Definitions & Clinical Notes', S['h1']))
    story.append(HRFlowable(width=W, thickness=1.2, color=DARK_BLUE, spaceAfter=4))
    story.append(Paragraph(
        'The following definitions describe each input variable used in the PharmAssist '
        'risk model and how to interpret them clinically. These align with items from the '
        '2021 National Community Survey on Medication Experiences (NCSME), N=1,521.', S['body']))
    story.append(Spacer(1,4))
    def_rows = [[Paragraph('Variable',S['h2']),Paragraph('Clinical Definition',S['h2'])]]
    for var,defn in VARIABLE_DEFINITIONS.items():
        def_rows.append([
            Paragraph(var,  ParagraphStyle('dv2',fontSize=7.5,fontName='Helvetica-Bold',
                                           textColor=DARK_BLUE,leading=10)),
            Paragraph(defn, ParagraphStyle('dd2',fontSize=7.5,fontName='Helvetica',
                                           textColor=colors.HexColor('#333333'),leading=11)),
        ])
    def_tbl = Table(def_rows, colWidths=[1.8*inch,5.4*inch], repeatRows=1)
    def_tbl.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),DARK_BLUE),('TEXTCOLOR',(0,0),(-1,0),colors.white),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,LIGHT_GREY]),
        ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),
        ('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),
        ('VALIGN',(0,0),(-1,-1),'TOP'),('BOX',(0,0),(-1,-1),0.8,DARK_BLUE),
        ('INNERGRID',(0,0),(-1,-1),0.3,colors.HexColor('#CCCCCC')),
    ]))
    story.append(def_tbl)
    story.append(Spacer(1,8))

    # PHARMACIST ACTION DEFINITIONS
    story.append(Paragraph('Pharmacist Action Definitions', S['h1']))
    story.append(HRFlowable(width=W, thickness=1.2, color=DARK_BLUE, spaceAfter=4))
    rec_def_rows = [[Paragraph('Action',S['h2']),Paragraph('Clinical Rationale & Guidance',S['h2'])]]
    for action,defn in REC_DEFINITIONS.items():
        rec_def_rows.append([
            Paragraph(action, ParagraphStyle('ra2',fontSize=7.5,fontName='Helvetica-Bold',
                                             textColor=DARK_BLUE,leading=10)),
            Paragraph(defn,   ParagraphStyle('rd2',fontSize=7.5,fontName='Helvetica',
                                             textColor=colors.HexColor('#333333'),leading=11)),
        ])
    rec_def_tbl = Table(rec_def_rows, colWidths=[1.5*inch,5.7*inch], repeatRows=1)
    rec_def_tbl.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),DARK_BLUE),('TEXTCOLOR',(0,0),(-1,0),colors.white),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,LIGHT_GREY]),
        ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),
        ('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),
        ('VALIGN',(0,0),(-1,-1),'TOP'),('BOX',(0,0),(-1,-1),0.8,DARK_BLUE),
        ('INNERGRID',(0,0),(-1,-1),0.3,colors.HexColor('#CCCCCC')),
    ]))
    story.append(rec_def_tbl)
    story.append(Spacer(1,10))

    # DISCLAIMER
    disc_text = (
        '<b>DISCLAIMER:</b> The PharmAssist Medication Management Difficulty Risk Screener '
        'estimates the likelihood that a patient will experience difficulty using medications '
        'as instructed, based on self-reported data. The risk estimate is derived from a logistic '
        'regression model trained on 1,521 respondents of the 2021 National Community Survey on '
        'Medication Experiences (NCSME). <b>This tool is intended for clinical screening purposes '
        'only and is NOT a diagnostic instrument.</b> The model has a Recall of 81.0%, meaning '
        'approximately 19% of truly High Risk patients may not be identified. Results should be '
        'interpreted by a qualified pharmacist or licensed clinician in the context of the '
        "patient's full clinical history. Estimates are not a guarantee of outcomes. PharmAssist "
        'should not replace clinical judgment. The information in this report is privileged '
        'patient health information and may be subject to HIPAA protections.'
    )
    disc_tbl = Table([[Paragraph(disc_text,S['warn'])]], colWidths=[W])
    disc_tbl.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,-1),WARN_YELLOW),('BOX',(0,0),(-1,-1),1.2,WARN_BORDER),
        ('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8),
        ('LEFTPADDING',(0,0),(-1,-1),10),('RIGHTPADDING',(0,0),(-1,-1),10),
    ]))
    story.append(disc_tbl)
    story.append(Spacer(1,6))
    story.append(Paragraph(
        f'PharmAssist  |  2021 NCSME Survey (N=1,521)  |  Generated: {date_str}  |  For clinical use only',
        ParagraphStyle('footer2',fontSize=7,textColor=colors.grey,alignment=TA_CENTER,fontName='Helvetica')))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()
st.markdown(
    '<div style="border-radius:10px;overflow:hidden;margin-top:55px;margin-bottom:10px;box-shadow:0 3px 16px rgba(31,78,121,0.2);">'
    '<div style="background:linear-gradient(135deg,#1F4E79,#2563A8,#1565C0);padding:18px 22px;display:flex;align-items:center;justify-content:center;flex-wrap:wrap;gap:16px;">'
    '<div style="display:flex;align-items:center;gap:11px;">'
    '<div style="width:38px;height:38px;border-radius:50%;background:rgba(255,255,255,0.15);border:1.5px solid rgba(255,255,255,0.3);display:flex;align-items:center;justify-content:center;font-size:1.25rem;flex-shrink:0;">&#128138;</div>'
    '<div>'
    '<div style="color:#fff;font-size:1.25rem;font-weight:800;letter-spacing:0.2px;line-height:1.15;margin:0;">PharmAssist</div>'
    '<div style="color:rgba(255,255,255,0.72);font-size:0.76rem;font-weight:400;margin-top:1px;">Medication Management Difficulty Risk Screener</div>'
    '</div></div>'
    '<div style="display:flex;gap:6px;align-items:center;flex-wrap:wrap;">'
    '<span style="background:rgba(255,255,255,0.13);color:rgba(255,255,255,0.93);border:1px solid rgba(255,255,255,0.28);border-radius:20px;padding:3px 10px;font-size:0.67rem;font-weight:600;white-space:nowrap;">Recall 81.0%</span>'
    '<span style="background:rgba(255,255,255,0.13);color:rgba(255,255,255,0.93);border:1px solid rgba(255,255,255,0.28);border-radius:20px;padding:3px 10px;font-size:0.67rem;font-weight:600;white-space:nowrap;">ROC-AUC 0.867</span>'
    '<span style="background:rgba(255,255,255,0.13);color:rgba(255,255,255,0.93);border:1px solid rgba(255,255,255,0.28);border-radius:20px;padding:3px 10px;font-size:0.67rem;font-weight:600;white-space:nowrap;">N = 1,521</span>'
    '</div></div>'
    '<div style="background:#EBF3FB;border-top:1px solid #C8DDEF;padding:5px 22px;display:flex;align-items:center;gap:18px;flex-wrap:wrap;">'
    '<span style="font-size:0.70rem;color:#1F4E79;font-weight:500;">&#9679; 2021 NCSME Survey</span>'
    '<span style="font-size:0.70rem;color:#1F4E79;font-weight:500;">&#9679; Logistic Regression</span>'
    '<span style="font-size:0.70rem;color:#1F4E79;font-weight:500;">&#9679; 19 Predictors</span>'
    '</div></div>',
    unsafe_allow_html=True
)

if not model_loaded:
    st.error("⚠️ **Model files not found!** Run in your notebook: `joblib.dump(lr_best,'lr_model.pkl')` and `joblib.dump(scaler,'scaler.pkl')`")
    st.stop()

# ── 4-COLUMN LAYOUT ───────────────────────────────────────────────
c1, c2, c3, c4 = st.columns([1.1, 1.1, 1.1, 1.5])

# ════════════════════════════════════════
# COLUMN 1 — MEDICATION + HEALTH
# ════════════════════════════════════════
with c1:
    st.markdown('<div class="sec-label"> Medication Complexity</div>', unsafe_allow_html=True)
    num_rx     = st.number_input("Prescription Drugs",  0, 20, 3, help="Daily prescription meds")
    num_otc    = st.number_input("OTC Medications",     0, 10, 1, help="Daily OTC medications")
    num_herbal = st.number_input("Herbal Supplements",  0, 10, 0, help="Daily herbal supplements")

    st.markdown('<div class="sec-label"> Health Burden</div>', unsafe_allow_html=True)
    num_health  = st.number_input("No. of Health Problems", 0, 15, 2)
    rate_health = st.selectbox("Self-Rated Health",
                   [1,2,3,4], index=1,
                   format_func=lambda x:{1:"Excellent",2:"Good",3:"Fair",4:"Poor"}[x])
    hosp = st.selectbox("Hospitalized Last Year?",
                   [1,0], index=1, format_func=lambda x:{1:"Yes",0:"No"}[x])

# ════════════════════════════════════════
# COLUMN 2 — BARRIERS + SUPPORT
# ════════════════════════════════════════
with c2:
    st.markdown('<div class="sec-label"> Barriers  (1=Low · 7=High)</div>', unsafe_allow_html=True)
    fin_hardship = st.slider("Financial Hardship",    1, 7, 2)
    transport    = st.slider("Transportation Barrier",1, 7, 2)
    side_effects = st.slider("Side Effects Concern",  1, 7, 2)

    st.markdown('<div class="sec-label"> Support Systems  (1=Low · 7=High)</div>', unsafe_allow_html=True)
    social_support = st.slider("Social Support",           1, 7, 4)
    fam_friend     = st.slider("Family/Friend Reliance",   1, 7, 3)

# ════════════════════════════════════════
# COLUMN 3 — DEMOGRAPHICS + BUTTON
# ════════════════════════════════════════
with c3:
    st.markdown('<div class="sec-label"> Demographics</div>', unsafe_allow_html=True)
    year_born = st.number_input("Year of Birth", 1932, 2003, 1966,
                    help="Year patient was born (1932–2003). Age = 2021 − Year of Birth.")
    age = 2021 - year_born   # Feature engineering: Age computed as 2021 - YearBorn
    education = st.selectbox("Education Level", [1,2,3,4,5,6,7], index=1,
                  format_func=lambda x:{
                    1:"High School / GED",2:"Some College (no degree)",3:"Associate Degree",
                    4:"Bachelor's Degree",5:"Master's Degree",6:"Professional Degree",7:"Doctoral Degree"}[x])
    income    = st.selectbox("Household Income (2020)", list(range(1,9)), index=2,
                  format_func=lambda x:{
                    1:"$20,000 or less",2:"$20,001–$40,000",3:"$40,001–$60,000",
                    4:"$60,001–$80,000",5:"$80,001–$100,000",6:"$100,001–$120,000",
                    7:"$120,001–$140,000",8:"More than $140,000"}[x])
    rural     = st.selectbox("Geographic Area", [1,0], index=0,
                  format_func=lambda x:{1:"Urban (≥20,000 pop.)",0:"Rural (<20,000 pop.)"}[x])

    patient_name = st.text_input("Patient Name / ID (optional)",
                                  placeholder="e.g. Patient #1042")

    st.markdown("<br>", unsafe_allow_html=True)
    assess = st.button("  Assess Patient Risk", use_container_width=True)

# ════════════════════════════════════════
# COLUMN 4 — RESULTS PANEL
# ════════════════════════════════════════
with c4:
    if not assess:
        st.markdown("""
        <div style="text-align:center;padding:40px 10px;color:#AAA;">
            <div style="font-size:2.5rem;">💊</div>
            <div style="font-size:0.95rem;font-weight:600;margin:8px 0 4px;">
                Fill in patient details</div>
            <div style="font-size:0.82rem;">
                then click <strong>Assess Patient Risk</strong></div>
        </div>
        """, unsafe_allow_html=True)

    else:
        # ── COMPUTE ──────────────────────────────────────────────
        total_meds    = num_rx + num_otc + num_herbal
        barrier_score = fin_hardship + transport + side_effects
        support_score = social_support + fam_friend
        health_score  = num_health + rate_health + hosp

        raw = {
            'NumRx':num_rx,'NumOTC':num_otc,'NumHerbal':num_herbal,
            'NumHealthProb':num_health,'RateHealth':rate_health,'HospLastYear':hosp,
            'Fin_Hardship':fin_hardship,'Transport':transport,'Side_Effects':side_effects,
            'Social_Support':social_support,'Fam_Friend':fam_friend,
            'Age':age,'Education':education,'HouseIncome':income,'RuralUrban':rural,
            'Total_Meds':total_meds,'Barrier_Score':barrier_score,
            'Support_Score':support_score,'Health_Score':health_score,
        }
        # Display-friendly labels for factor cards
        raw_display = dict(raw)
        raw_display['HospLastYear'] = 'Yes' if hosp == 1 else 'No'
        raw_display['RuralUrban']   = 'Urban' if rural == 1 else 'Rural'
        raw_display['Age']          = f"{age} (born {year_born})"
        X_df     = pd.DataFrame([raw])[PREDICTORS]
        X_sc     = scaler.transform(X_df)
        prob     = model.predict_proba(X_sc)[0][1]
        pct      = prob * 100
        coefs    = model.coef_[0]

        if prob >= 0.50:
            tier, cls, emoji = "HIGH RISK",     "risk-high",     "🔴"
        elif prob >= 0.30:
            tier, cls, emoji = "MODERATE RISK", "risk-moderate", "🟠"
        else:
            tier, cls, emoji = "LOW RISK",      "risk-low",      "🟢"

        # ── RISK CARD (inline single row) ─────────────────────────
        st.markdown(f"""
        <div class="risk-card {cls}">
          <div class="risk-left">
            <span class="risk-emoji">{emoji}</span>
            <div>
              <div class="risk-label">{tier}</div>
              <div class="risk-sub">MEDICATION DIFFICULTY RISK</div>
            </div>
          </div>
          <div class="risk-pct">{pct:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)

        st.progress(int(prob * 100))

        # ── TOP FACTORS (compact single-line rows) ────────────────
        contribs = {f: float(X_sc[0][i] * coefs[i]) for i, f in enumerate(PREDICTORS)}
        pos = sorted([(f,c) for f,c in contribs.items() if c>0], key=lambda x:-x[1])[:3]
        neg = sorted([(f,c) for f,c in contribs.items() if c<0], key=lambda x:x[1])[:2]
        max_pos = max((abs(c) for _,c in pos), default=1)
        max_neg = max((abs(c) for _,c in neg), default=1)

        st.markdown('<div class="sec-label">🔍 Key Risk Factors</div>', unsafe_allow_html=True)
        for feat, contrib in pos:
            bp = int(abs(contrib)/max_pos*100)
            st.markdown(f"""<div class="frow">
              <span class="frow-dir">⬆</span>
              <span class="frow-name">{LABEL_MAP[feat]}</span>
              <span class="frow-val">{raw_display[feat]} &nbsp;+{contrib:.3f}</span>
              <div class="frow-bar-wrap frow-bar-red">
                <div class="frow-bar-fill-red" style="width:{bp}%"></div></div>
            </div>""", unsafe_allow_html=True)
        for feat, contrib in neg:
            bp = int(abs(contrib)/max_neg*100)
            st.markdown(f"""<div class="frow">
              <span class="frow-dir">⬇</span>
              <span class="frow-name">{LABEL_MAP[feat]} ✦</span>
              <span class="frow-val">{raw_display[feat]} &nbsp;{contrib:.3f}</span>
              <div class="frow-bar-wrap frow-bar-green">
                <div class="frow-bar-fill-green" style="width:{bp}%"></div></div>
            </div>""", unsafe_allow_html=True)

        # ── RECOMMENDATIONS (compact single-line) ─────────────────
        st.markdown('<div class="sec-label">💼 Pharmacist Actions</div>', unsafe_allow_html=True)

        def rrow(style, icon, title, body):
            st.markdown(f'<div class="rrow rrow-{style}"><span class="rrow-icon">{icon}</span>'
                        f'<span class="rrow-title">{title}</span>'
                        f'<span class="rrow-body">{body}</span></div>', unsafe_allow_html=True)

        if tier == "HIGH RISK":
            rrow("urgent",  "🚨", "MTM within 48–72 hrs:", "Immediate Medication Therapy Management consult.")
        elif tier == "MODERATE RISK":
            rrow("standard","⚠️", "Follow-up in 2 weeks:", "Adherence education & confirm medication understanding.")
        else:
            rrow("monitor", "✅", "Routine monitoring:", "Re-screen at next dispensing visit.")

        if fin_hardship >= 4:
            rrow("urgent",  "💰", "Financial Barrier:", "Patient assistance programs, generics, 340B, or GoodRx.")
        if transport >= 4:
            rrow("urgent",  "🚗", "Transport Barrier:", "Home delivery, mail-order, or community transport.")
        if side_effects >= 4:
            rrow("standard","⚗️", "Side Effects:", "Review regimen; consider alternative formulations.")
        if fam_friend >= 5:
            rrow("standard","👨‍👩‍👧", "Family Reliance:", "Include caregiver; provide written adherence aids.")
        if total_meds >= 7:
            rrow("standard","💊", "Poly-pharmacy:", "Review for deprescribing, duplicates & interactions.")
        if age < 45:
            rrow("standard","🧑", "Younger Patient:", "Tailored health literacy education recommended.")

        # ── DOWNLOAD PDF + EMAIL ─────────────────────────────────
        name_str  = patient_name.strip() if patient_name.strip() else "Not provided"
        date_str  = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        recs_list = []
        if tier == "HIGH RISK":   recs_list.append("Schedule MTM within 48–72 hours")
        if tier == "MODERATE RISK": recs_list.append("Follow-up call within 2 weeks")
        if tier == "LOW RISK":    recs_list.append("Routine monitoring at next visit")
        if fin_hardship >= 4:  recs_list.append("Address Financial Barrier — patient assistance programs")
        if transport    >= 4:  recs_list.append("Address Transport Barrier — delivery/transport options")
        if side_effects >= 4:  recs_list.append("Review regimen for Side Effects concerns")
        if fam_friend   >= 5:  recs_list.append("High Family/Friend Reliance — include caregiver in counseling")
        if total_meds   >= 7:  recs_list.append("Poly-pharmacy — medication review / deprescribing")
        if age < 45:           recs_list.append("Younger Patient — health literacy education")

        # Generate PDF
        pdf_bytes = generate_pdf_report(
            patient_name=name_str, date_str=date_str, tier=tier,
            pct=pct, raw=raw, raw_display=raw_display,
            pos_factors=pos, neg_factors=neg,
            recs_list=recs_list, year_born=year_born, age=age,
            num_rx=num_rx, num_otc=num_otc, num_herbal=num_herbal,
            num_health=num_health, rate_health=rate_health, hosp=hosp,
            fin_hardship=fin_hardship, transport=transport, side_effects=side_effects,
            social_support=social_support, fam_friend=fam_friend,
            education=education, income=income, rural=rural,
            total_meds=total_meds, barrier_score=barrier_score,
            support_score=support_score, health_score=health_score
        )

        st.markdown('<div class="sec-label">📄 Report & Communication</div>', unsafe_allow_html=True)

        # PDF Download
        st.download_button(
            label     = "⬇️  Download Clinical PDF Report",
            data      = pdf_bytes,
            file_name = f"PharmAssist_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
            mime      = "application/pdf",
            use_container_width=True,
            help="Full 2-page clinical report with definitions, risk comparison, and recommendations"
        )

        # Email section
        recipient_email = st.text_input("📧 Email report to (optional)",
                                         placeholder="patient@email.com or pharmacist@clinic.com",
                                         key="email_field")
        if recipient_email:
            # Build email body summary
            email_subject = urllib.parse.quote(
                f"PharmAssist Risk Report — {name_str} — {tier}")
            email_body = urllib.parse.quote(
                f"PharmAssist — Medication Management Difficulty Risk Report\n"
                f"{'='*55}\n"
                f"Patient:         {name_str}\n"
                f"Date:            {date_str}\n"
                f"Risk Level:      {tier}\n"
                f"Probability:     {pct:.1f}%\n"
                f"Sample Average:  {AVG_RISK_PCT}%\n"
                f"{'='*55}\n\n"
                f"TOP RISK FACTORS:\n"
                + "\n".join([f"  {i+1}. {LABEL_MAP.get(f,f)}: +{c:.3f}" for i,(f,c) in enumerate(pos[:3])])
                + f"\n\n"
                f"RECOMMENDED ACTIONS:\n"
                + "\n".join([f"  {i+1}. {r}" for i,r in enumerate(recs_list)])
                + f"\n\n"
                f"{'='*55}\n"
                f"DISCLAIMER: This is a clinical screening tool only.\n"
                f"Not a diagnostic instrument. Recall=81.0%, ROC-AUC=0.867.\n"
                f"Results must be interpreted by a qualified pharmacist.\n"
                f"Based on 2021 NCSME Survey (N=1,521).\n"
                f"{'='*55}\n\n"
                f"Please download and attach the full PDF report from PharmAssist."
            )
            mailto_link = f"mailto:{recipient_email}?subject={email_subject}&body={email_body}"
            st.markdown(
                f'<a href="{mailto_link}" target="_blank">'
                f'<div style="background:linear-gradient(135deg,#1F4E79,#2E75B6);'
                f'color:white;text-align:center;padding:7px;border-radius:7px;'
                f'font-size:0.82rem;font-weight:700;margin-top:3px;'
                f'box-shadow:0 2px 8px rgba(31,78,121,0.3);">'
                f'✉️ Open Email Client with Report Summary</div></a>',
                unsafe_allow_html=True
            )
            st.markdown(
                '<div style="font-size:0.63rem;color:#888;margin-top:2px;">'
                '⚠️ Attach the PDF above for the full clinical report. '
                'Email body contains a text summary only.</div>',
                unsafe_allow_html=True
            )

        st.markdown("""
        <div class="disclaimer">
        ⚠️ <strong>Clinical Disclaimer:</strong> PharmAssist is a research-based screening tool
        (2021 NCSME, N=1,521). Recall=81% — ~19% of High Risk patients may not be identified.
        Not a substitute for clinical judgment. Results must be interpreted by a qualified pharmacist.
        </div>
        """, unsafe_allow_html=True)
