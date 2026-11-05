# ============================================================
# APP
# Streamlit interface for the Student Grade Management System.
#
# Design notes (kept short on purpose)
#   Direction : calm, analytical gradebook. Ink blue as the single
#               action colour, amber for warnings, red only for fails.
#   Type      : Bricolage Grotesque (headings, big numbers)
#               Public Sans (body, tables, forms)
#   Shape     : 8px controls, 12px cards, borders instead of shadows.
#   Themes    : Light and Dark are defined once in THEMES and applied
#               through CSS variables, so every widget follows them.
#   Layout    : top navigation (works the same on phone, laptop and
#               desktop), columns stack automatically on small screens.
#
# Run with:  python -m streamlit run app.py
# ============================================================

import json
import re
from datetime import datetime
from html import escape as esc

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from grade_functions import PASS_MARK, get_student_result
from student_manager import (
    add_student,
    delete_student,
    get_student_report,
    search_student,
    update_student,
    view_students,
)

# ------------------------------------------------------------
# SETTINGS
# ------------------------------------------------------------

# Change the subjects here. Keep the names consistent with saved records.
SUBJECTS = [
    "Python",
    "English",
    "Mathematics",
    "Computer Science",
    "Statistics",
]

GRADE_ORDER = ["A", "B", "C", "D", "E", "F"]
GRADE_BANDS = [
    ("A", "90 to 100"),
    ("B", "80 to 89"),
    ("C", "70 to 79"),
    ("D", "60 to 69"),
    ("E", "40 to 59"),
    ("F", "below 40"),
]

PAGES = [
    "Dashboard",
    "Add student",
    "View students",
    "Update student",
    "Delete student",
    "Export data",
]

NEW_CLASS = "Add a new class or course"
ALL_CLASSES = "All classes"

# Sample records, only loaded when the person asks for them.
SAMPLE_RECORDS = [
    ("Anjali Menon", "BSc Computer Science, Year 1", [88, 92, 81, 76, 95]),
    ("Arjun Nair", "BSc Computer Science, Year 1", [72, 68, 75, 70, 79]),
    ("Fathima Rahman", "BSc Computer Science, Year 1", [94, 89, 91, 87, 98]),
    ("Sreejith Kumar", "BSc Computer Science, Year 1", [45, 52, 60, 58, 66]),
    ("Neha Thomas", "BSc Computer Science, Year 1", [81, 77, 85, 90, 72]),
    ("Rahul Varma", "BSc Computer Science, Year 1", [32, 48, 55, 61, 70]),
    ("Divya Prakash", "BSc Computer Science, Year 1", [66, 71, 64, 69, 74]),
    ("Mohammed Sinan", "BSc Computer Science, Year 2", [78, 83, 69, 74, 88]),
    ("Athira Raj", "BSc Computer Science, Year 2", [91, 86, 93, 84, 90]),
    ("Joseph Mathew", "BSc Computer Science, Year 2", [58, 41, 63, 55, 49]),
    ("Lakshmi Pillai", "BSc Computer Science, Year 2", [84, 79, 88, 92, 81]),
    ("Adil Hassan", "BSc Computer Science, Year 2", [29, 38, 44, 52, 61]),
    ("Meera Krishnan", "BSc Computer Science, Year 2", [76, 81, 79, 83, 77]),
    ("Kevin Joseph", "BSc Computer Science, Year 2", [62, 33, 57, 68, 71]),
]

# ------------------------------------------------------------
# THEMES
# ------------------------------------------------------------

THEMES = {
    "Light": {
        "scheme": "light",
        "vars": {
            # Cool blue-grey page and card surfaces (avoid a pure-white look)
            "bg": "#E5EAF3",
            "surface": "#F0F3F9",
            "surface-2": "#DCE4F0",

            # Borders and text
            "border": "#C9D4E5",
            "text": "#17243B",
            "muted": "#596B85",

            # Primary indigo
            "primary-text": "#3D5EDB",
            "primary-fill": "#3D5EDB",
            "primary-soft": "#DCE5FF",

            # Status colours
            "success": "#16845B",
            "warn": "#C58A22",
            "danger": "#C74747",
        },
        # Grade colours: A, B, C, D, E, F
        "grades": [
            "#25B834",
            "#ADCE49",
            "#E0DE82",
            "#D99A27",
            "#E432BD",
            "#C74747",
        ],
        "chart": "#3D5EDB",
        "chart_soft": "#9EAFE0",
        "accent": "#D99A27",
        "box_fill": "rgba(61, 94, 219, 0.12)",
    },
    "Dark": {
        "scheme": "dark",
        "vars": {
            "bg": "#0D1220",
            "surface": "#141B2D",
            "surface-2": "#1C2540",
            "border": "#27324F",
            "text": "#E7EBF5",
            "muted": "#9AA6BF",
            "primary-text": "#8FADFF",
            "primary-fill": "#3A62E0",
            "primary-soft": "#1B2A57",
            "success": "#4FD08E",
            "warn": "#F2B544",
            "danger": "#FF7B72",
        },
        "grades":[
            "#25B834",
            "#ADCE49",
            "#E0DE82",
            "#D99A27",
            "#E432BD",
            "#C74747",
        ],
        "chart": "#6B8FF5",
        "chart_soft": "#41538A",
        "accent": "#F2B544",
        "box_fill": "rgba(107,143,245,0.18)",
    },
}

FONT_IMPORT = (
    "@import url('https://fonts.googleapis.com/css2?"
    "family=Bricolage+Grotesque:opsz,wght@12..96,600;12..96,700"
    "&family=Public+Sans:wght@400;500;600;700&display=swap');"
)

STATIC_CSS = """
html,body,.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
[data-testid="stMainBlockContainer"],
[data-testid="stSidebar"],
[data-testid="stSidebar"] > div:first-child,
header[data-testid="stHeader"]{
  background:var(--bg)!important;
  background-color:var(--bg)!important;
  color:var(--text)!important;
}
[data-testid="stMain"] [data-testid="stVerticalBlock"],
[data-testid="stMainBlockContainer"]{
  color:var(--text)!important;
}
.stApp,.stApp button,.stApp input,.stApp textarea,.stApp [data-baseweb]{
  font-family:'Public Sans',system-ui,-apple-system,'Segoe UI',sans-serif;}
[data-testid="stIconMaterial"]{font-family:'Material Symbols Rounded','Material Symbols Outlined'!important;}
/* Keep Streamlit's native header alive: it contains the sidebar expand
   control. Hiding it makes the sidebar impossible to reopen after collapse. */
header[data-testid="stHeader"]{
  display:block!important;
  visibility:visible!important;
  opacity:1!important;
  background:transparent!important;
  height:2.6rem!important;
  z-index:1000!important;
}
/* The expand-sidebar control lives in Streamlit's header/toolbar.
   Keep the toolbar visible so the sidebar can always be reopened. */
header[data-testid="stHeader"] [data-testid="stToolbar"]{
  display:flex!important;
  visibility:visible!important;
  opacity:1!important;
}
header[data-testid="stHeader"] button[data-testid="stExpandSidebarButton"],
header[data-testid="stHeader"] [data-testid="stExpandSidebarButton"]{
  display:flex!important;
  visibility:visible!important;
  opacity:1!important;
  pointer-events:auto!important;
  color:var(--text)!important;
  background:var(--surface-2)!important;
  border:1px solid var(--border)!important;
  border-radius:9px!important;
}
footer,#MainMenu,[data-testid="stDecoration"]{display:none!important;}
/* Do not hide CSS injection containers: this can prevent theme updates. */
[data-testid="stAppViewContainer"]{background:var(--bg);}
.block-container{max-width:1240px;padding:3.4rem 2rem 4rem!important;}
[data-testid="stMarkdownContainer"]{color:var(--text);}
[data-testid="stCaptionContainer"],[data-testid="stCaptionContainer"] p{color:var(--muted)!important;}
[data-testid="stWidgetLabel"] p,[data-testid="stWidgetLabel"] label{color:var(--text)!important;font-weight:500;font-size:.9rem;}

/* Sidebar navigation and compact theme switch */
[data-testid="stSidebar"]{
  background:var(--surface)!important;
  border-right:1px solid var(--border);
}
[data-testid="stSidebar"] > div:first-child{background:var(--surface)!important;}
[data-testid="stSidebarContent"]{padding:.45rem 1rem 1.2rem!important;}
/* Keep the built-in collapse/expand controls visible and easy to find. */
[data-testid="stSidebarCollapseButton"],
[data-testid="stSidebar"] button[aria-label*="Collapse"],
header[data-testid="stHeader"] [data-testid="stExpandSidebarButton"]{
  display:flex!important;
  visibility:visible!important;
  opacity:1!important;
  pointer-events:auto!important;
  z-index:1001!important;
}
[data-testid="stSidebarCollapseButton"] button,
[data-testid="stExpandSidebarButton"] button{
  color:var(--text)!important;
  background:var(--surface-2)!important;
  border:1px solid var(--border)!important;
  border-radius:10px!important;
}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"]{color:var(--text);}
.brand{display:flex;align-items:center;gap:.7rem;padding:.15rem .35rem 1rem;border-bottom:1px solid var(--border);margin-bottom:1rem;}
.brand-name{font-family:'Bricolage Grotesque',sans-serif;font-weight:700;font-size:1.35rem;letter-spacing:-.02em;line-height:1.1;}
.brand-sub{color:var(--muted);font-size:.8rem;}
.nav-heading{font-size:.72rem;font-weight:700;letter-spacing:.08em;color:var(--muted);padding:.2rem .65rem .65rem;}
/* Real buttons are used instead of a radio widget so every page label
   remains visible across Streamlit versions and screen sizes. */
.st-key-nav_dashboard,.st-key-nav_add_student,.st-key-nav_view_students,
.st-key-nav_update_student,.st-key-nav_delete_student,.st-key-nav_export_data{
  margin:0 0 .68rem!important;
}
.st-key-nav_dashboard button,.st-key-nav_add_student button,
.st-key-nav_view_students button,.st-key-nav_update_student button,
.st-key-nav_delete_student button,.st-key-nav_export_data button{
  width:100%;min-height:54px!important;display:flex!important;
  align-items:center!important;justify-content:center!important;
  text-align:center!important;padding:.7rem 1rem!important;
  border-radius:13px!important;font-size:.93rem!important;font-weight:650!important;
  box-shadow:none!important;transition:background .15s ease,border-color .15s ease;
}
.st-key-nav_dashboard button p,.st-key-nav_add_student button p,
.st-key-nav_view_students button p,.st-key-nav_update_student button p,
.st-key-nav_delete_student button p,.st-key-nav_export_data button p{
  width:100%;text-align:center!important;margin:0!important;
}
.st-key-nav_dashboard button[kind="secondary"],
.st-key-nav_add_student button[kind="secondary"],
.st-key-nav_view_students button[kind="secondary"],
.st-key-nav_update_student button[kind="secondary"],
.st-key-nav_delete_student button[kind="secondary"],
.st-key-nav_export_data button[kind="secondary"]{
  background:var(--primary-soft)!important;color:var(--text)!important;
  border:1px solid transparent!important;
}
.st-key-nav_dashboard button[kind="secondary"]:hover,
.st-key-nav_add_student button[kind="secondary"]:hover,
.st-key-nav_view_students button[kind="secondary"]:hover,
.st-key-nav_update_student button[kind="secondary"]:hover,
.st-key-nav_delete_student button[kind="secondary"]:hover,
.st-key-nav_export_data button[kind="secondary"]:hover{
  background:var(--surface-2)!important;border-color:var(--border)!important;
}
.st-key-nav_dashboard button[kind="primary"],
.st-key-nav_add_student button[kind="primary"],
.st-key-nav_view_students button[kind="primary"],
.st-key-nav_update_student button[kind="primary"],
.st-key-nav_delete_student button[kind="primary"],
.st-key-nav_export_data button[kind="primary"]{
  background:var(--primary-fill)!important;color:#fff!important;
  border:1px solid var(--primary-fill)!important;
}
.st-key-nav_dashboard button[kind="primary"] p,
.st-key-nav_add_student button[kind="primary"] p,
.st-key-nav_view_students button[kind="primary"] p,
.st-key-nav_update_student button[kind="primary"] p,
.st-key-nav_delete_student button[kind="primary"] p,
.st-key-nav_export_data button[kind="primary"] p{color:#fff!important;}
.st-key-nav_dashboard button:focus-visible,.st-key-nav_add_student button:focus-visible,
.st-key-nav_view_students button:focus-visible,.st-key-nav_update_student button:focus-visible,
.st-key-nav_delete_student button:focus-visible,.st-key-nav_export_data button:focus-visible{
  outline:2px solid var(--primary-text)!important;outline-offset:2px!important;
}
.sidebar-guide{
  margin-top:2rem;padding:.9rem .85rem;border-radius:12px;
  background:var(--primary-soft);border:1px solid var(--border);
}
.sidebar-guide-title{font-weight:700;font-size:.9rem;margin-bottom:.35rem;}
.sidebar-guide-text{font-size:.8rem;line-height:1.5;color:var(--muted);}
/* Theme selector: native radio interaction, styled as a compact segmented switch. */
.st-key-theme_radio{display:flex!important;justify-content:flex-end!important;margin:0 0 .45rem!important;position:relative;z-index:1001;}
.st-key-theme_radio [data-testid="stWidgetLabel"]{display:none!important;}
.st-key-theme_radio [role="radiogroup"]{
  display:flex!important;flex-direction:row!important;gap:0!important;
  width:max-content!important;padding:4px!important;
  border:1px solid var(--border)!important;border-radius:999px!important;
  background:var(--surface)!important;
}
.st-key-theme_radio [role="radiogroup"] label{
  margin:0!important;padding:.35rem .95rem!important;border-radius:999px!important;
  cursor:pointer!important;white-space:nowrap!important;
}
.st-key-theme_radio [role="radiogroup"] label > div:first-child{display:none!important;}
.st-key-theme_radio [data-testid="stRadioOption"] > div > div:not([data-testid="stMarkdownContainer"]){display:none!important;}
.st-key-theme_radio [role="radiogroup"] label p{
  color:var(--muted)!important;font-size:.82rem!important;font-weight:650!important;
}
.st-key-theme_radio [role="radiogroup"] label:has(input:checked){background:var(--primary-fill)!important;}
.st-key-theme_radio [role="radiogroup"] label:has(input:checked) p{color:#fff!important;}
.st-key-theme_radio [role="radiogroup"] label:has(input:focus-visible){outline:2px solid var(--primary-text)!important;outline-offset:2px!important;}
.main-theme-row{display:flex;justify-content:flex-end;margin:0 0 .5rem;}
.block-container{max-width:1600px;padding:3.4rem 2rem 4rem!important;}
@media(max-width:800px){
  .block-container{padding:3.4rem 1rem 3rem!important;}
  [data-testid="stSidebarContent"]{padding:.9rem!important;}
}

/* page headings */
.page-title{font-family:'Bricolage Grotesque',sans-serif;font-weight:700;font-size:clamp(1.65rem,3.4vw,2.3rem);letter-spacing:-.025em;line-height:1.12;margin:0 0 .4rem;}
.page-sub{color:var(--muted);max-width:70ch;font-size:1rem;line-height:1.55;margin:0 0 1.4rem;}
.card-title{font-family:'Bricolage Grotesque',sans-serif;font-size:1.1rem;font-weight:600;line-height:1.3;}
.card-sub{color:var(--muted);font-size:.85rem;line-height:1.45;margin:.15rem 0 .7rem;}

/* cards */
[class*="st-key-card_"]{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:1.15rem 1.25rem;}
.st-key-card_preview{background:var(--surface-2);}

/* form controls */
[data-baseweb="input"],[data-baseweb="textarea"],[data-baseweb="select"] > div{
  background:var(--surface)!important;border:1px solid var(--border)!important;border-radius:8px!important;}
[data-baseweb="base-input"],[data-baseweb="input"] input,[data-baseweb="select"] input{background:transparent!important;color:var(--text)!important;}
[data-baseweb="input"]:focus-within,[data-baseweb="select"]:focus-within > div{border-color:var(--primary-text)!important;box-shadow:0 0 0 3px var(--primary-soft);}
input::placeholder,textarea::placeholder{color:var(--muted)!important;opacity:.85!important;}
input:disabled{-webkit-text-fill-color:var(--muted)!important;opacity:1!important;}
[data-baseweb="select"] div,[data-baseweb="select"] span{color:var(--text)!important;}
[data-baseweb="select"] svg{fill:var(--muted)!important;}
[data-testid="stNumberInputStepUp"],[data-testid="stNumberInputStepDown"]{background:var(--surface-2)!important;color:var(--text)!important;}
div[data-baseweb="popover"],div[data-baseweb="popover"] > div,ul[data-baseweb="menu"],ul[role="listbox"],[data-baseweb="menu"] li{
  background-color:var(--surface)!important;color:var(--text)!important;}
div[data-baseweb="popover"] > div{border:1px solid var(--border);border-radius:10px;}
[data-baseweb="menu"] li:hover,li[role="option"]:hover,li[aria-selected="true"]{background-color:var(--surface-2)!important;}
[data-testid="stCheckbox"] label p,[data-testid="stCheckbox"] label span{color:var(--text)!important;}
[data-testid="stCheckbox"] [data-baseweb="checkbox"] > span:first-child{border-color:var(--muted)!important;background-color:transparent!important;}
[data-testid="stCheckbox"] label:has(input:checked) > span:first-child{background-color:var(--primary-fill)!important;border-color:var(--primary-fill)!important;}

/* buttons */
[data-testid^="stBaseButton-"]{border-radius:8px;font-weight:600;min-height:2.7rem;padding:.45rem 1.15rem;}
[data-testid="stBaseButton-secondary"]{background:var(--surface);color:var(--text);border:1px solid var(--border);}
[data-testid="stBaseButton-secondary"]:hover{border-color:var(--primary-text);color:var(--primary-text);}
[data-testid="stBaseButton-primary"]{background:var(--primary-fill);color:#fff;border:1px solid var(--primary-fill);}
[data-testid="stBaseButton-primary"]:hover{filter:brightness(1.12);color:#fff;border-color:var(--primary-fill);}
[data-testid^="stBaseButton-"] p{color:inherit!important;}
[data-testid^="stBaseButton-"]:disabled{opacity:.45;cursor:not-allowed;}
[data-testid^="stBaseButton-"]:focus-visible{outline:2px solid var(--primary-text);outline-offset:2px;}
.st-key-use_id button{background:transparent!important;border:0!important;color:var(--primary-text)!important;padding:0!important;min-height:0!important;font-size:.85rem;text-decoration:underline;}
.st-key-delete_btn button{background:var(--danger)!important;border-color:var(--danger)!important;color:#fff!important;}
.st-key-delete_btn button:disabled{background:transparent!important;color:var(--muted)!important;border-color:var(--border)!important;}

/* kpi strip */
.kpis{display:grid;grid-template-columns:repeat(6,1fr);gap:1px;background:var(--border);border:1px solid var(--border);border-radius:14px;overflow:hidden;margin:0 0 1.1rem;}
.kpi{background:var(--surface);padding:1rem 1.1rem;min-width:0;}
.kpi.lead{background:var(--primary-soft);}
.kpi-label{color:var(--muted);font-size:.85rem;font-weight:500;}
.kpi-value{font-family:'Bricolage Grotesque',sans-serif;font-size:2.05rem;font-weight:700;letter-spacing:-.02em;line-height:1.2;margin:.15rem 0;font-variant-numeric:tabular-nums;}
.kpi-value.sm{font-size:1.2rem;line-height:1.9;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
.kpi-note{color:var(--muted);font-size:.8rem;line-height:1.35;}
.meter{height:6px;border-radius:99px;background:var(--surface-2);margin-top:.55rem;overflow:hidden;}
.meter > span{display:block;height:100%;background:var(--success);border-radius:99px;}

/* stat tiles */
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:var(--border);border:1px solid var(--border);border-radius:10px;overflow:hidden;margin:.2rem 0 1rem;}
.stat{background:var(--surface);padding:.75rem .95rem;min-width:0;}
.st-key-card_preview .stat{background:var(--surface);}
.stat-label{color:var(--muted);font-size:.8rem;}
.stat-value{font-weight:700;font-size:1.15rem;font-variant-numeric:tabular-nums;display:flex;align-items:center;gap:.4rem;flex-wrap:wrap;}
.stat-value .of{color:var(--muted);font-weight:500;font-size:.85rem;}

/* grade chips and status pills */
.grade{display:inline-flex;align-items:center;gap:.35rem;font-weight:700;}
.grade::before{content:"";width:9px;height:9px;border-radius:3px;background:var(--muted);}
.gA::before{background:var(--gA);}.gB::before{background:var(--gB);}.gC::before{background:var(--gC);}
.gD::before{background:var(--gD);}.gE::before{background:var(--gE);}.gF::before{background:var(--gF);}
.pill{display:inline-flex;align-items:center;gap:.4rem;padding:.15rem .65rem;border-radius:99px;font-size:.8rem;font-weight:600;}
.pill::before{content:"";width:6px;height:6px;border-radius:50%;background:currentColor;}
.pill.pass{color:var(--success);background:color-mix(in srgb,var(--success) 15%,transparent);}
.pill.fail{color:var(--danger);background:color-mix(in srgb,var(--danger) 15%,transparent);}
.m-fail{color:var(--danger);font-weight:700;}

/* tables */
.tbl-wrap{overflow-x:auto;border:1px solid var(--border);border-radius:12px;background:var(--surface);}
.tbl{width:100%;border-collapse:separate;border-spacing:0;font-size:.9rem;}
.tbl th{text-align:left;font-weight:600;color:var(--muted);font-size:.82rem;padding:.7rem .9rem;border-bottom:1px solid var(--border);background:var(--surface-2);white-space:nowrap;}
.tbl td{padding:.7rem .9rem;border-bottom:1px solid var(--border);white-space:nowrap;font-variant-numeric:tabular-nums;vertical-align:middle;}
.tbl tr:last-child td{border-bottom:0;}
.tbl tbody tr:hover td{background:color-mix(in srgb,var(--primary-soft) 55%,var(--surface));}
.tbl .first{position:sticky;left:0;background:var(--surface);z-index:1;border-right:1px solid var(--border);}
.tbl th.first{background:var(--surface-2);}
.tbl tbody tr:hover td.first{background:color-mix(in srgb,var(--primary-soft) 55%,var(--surface));}
.tbl .num{text-align:right;}
.tbl .nm{font-weight:600;}
.tbl .sub{color:var(--muted);font-size:.78rem;}
.tbl .of{color:var(--muted);font-size:.8rem;}
.cellmark{display:inline-flex;align-items:center;gap:.5rem;}
.cellmark .grade{font-size:.8rem;}

/* subject rows with bars */
.srows{display:flex;flex-direction:column;gap:.95rem;}
.srow{display:grid;grid-template-columns:1fr auto;gap:.3rem .8rem;align-items:center;}
.sname{font-size:.92rem;}
.sval{display:flex;align-items:center;gap:.65rem;font-weight:600;font-variant-numeric:tabular-nums;}
.sval .grade{font-size:.85rem;}
.sbar{grid-column:1/-1;height:6px;border-radius:99px;background:var(--surface-2);overflow:hidden;}
.st-key-card_preview .sbar{background:var(--border);}
.sbar > span{display:block;height:100%;border-radius:99px;background:var(--primary-fill);}
.sbar.f > span{background:var(--danger);}

/* preview */
.pv-top{display:flex;align-items:flex-end;justify-content:space-between;gap:1rem;flex-wrap:wrap;margin:.1rem 0 .9rem;}
.pv-pct{font-family:'Bricolage Grotesque',sans-serif;font-size:2.7rem;font-weight:700;line-height:1;letter-spacing:-.02em;font-variant-numeric:tabular-nums;}
.pv-label{color:var(--muted);font-size:.85rem;margin-bottom:.2rem;}
.pv-delta{color:var(--muted);font-size:.85rem;margin:-.4rem 0 .9rem;}

/* notices */
.note{padding:.7rem .95rem;border-radius:10px;border:1px solid var(--border);border-left:4px solid var(--primary-text);background:var(--surface);font-size:.9rem;line-height:1.5;margin:.45rem 0;}
.note.ok{border-left-color:var(--success);}
.note.warn{border-left-color:var(--warn);}
.note.err{border-left-color:var(--danger);}
.st-key-card_preview .note{background:var(--surface);}

/* misc */
.bands{display:grid;grid-template-columns:repeat(3,1fr);gap:.55rem .9rem;font-size:.88rem;margin-top:.3rem;}
.bands span{color:var(--muted);}
.empty{border:1px dashed var(--border);border-radius:12px;padding:1.6rem 1.4rem;background:var(--surface);margin-bottom:1rem;}
.empty-title{font-family:'Bricolage Grotesque',sans-serif;font-size:1.2rem;font-weight:600;margin-bottom:.3rem;}
.empty-text{color:var(--muted);max-width:60ch;line-height:1.55;}
.count{color:var(--muted);font-size:.88rem;margin:.2rem 0 .6rem;}
.rc-name{font-family:'Bricolage Grotesque',sans-serif;font-size:1.5rem;font-weight:700;letter-spacing:-.015em;line-height:1.2;}
.rc-meta{color:var(--muted);font-size:.9rem;margin:.2rem 0 .9rem;overflow-wrap:anywhere;}

@media (max-width:1000px){
  .kpis{grid-template-columns:repeat(3,1fr);}
}
@media (max-width:640px){
  .block-container{padding:3.4rem 1rem 3rem!important;}
  .kpis{grid-template-columns:repeat(2,1fr);}
  .stats{grid-template-columns:repeat(2,1fr);}
  .kpi-value{font-size:1.7rem;}
  .bands{grid-template-columns:repeat(2,1fr);}
  [class*="st-key-card_"]{padding:1rem;}
  .brand-sub{display:none;}
}
@media (prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important;}}
"""


def theme_css(theme):
    """Build the CSS variables for the chosen theme and add the shared styles."""
    variables = "".join(f"--{name}:{value};" for name, value in theme["vars"].items())
    grade_vars = "".join(
        f"--g{letter}:{colour};" for letter, colour in zip(GRADE_ORDER, theme["grades"])
    )
    # Set both the app's custom variables and Streamlit's native theme
    # variables. The latter are important because BaseWeb/Streamlit widgets
    # can otherwise keep using the configured dark palette when Light is chosen.
    native_variables = (
        f"--background-color:{theme['vars']['bg']};"
        f"--secondary-background-color:{theme['vars']['surface']};"
        f"--text-color:{theme['vars']['text']};"
        f"--primary-color:{theme['vars']['primary-fill']};"
        f"--border-color:{theme['vars']['border']};"
        f"--code-background-color:{theme['vars']['surface-2']};"
    )
    root = (
        ":root, html, body, .stApp, "
        "[data-testid=\"stAppViewContainer\"], "
        "[data-testid=\"stMain\"], "
        "[data-testid=\"stMainBlockContainer\"], "
        "[data-testid=\"stSidebar\"], "
        "[data-testid=\"stHeader\"]{"
        + variables + grade_vars + native_variables
        + f"color-scheme:{theme['scheme']} !important;"
        + f"background-color:{theme['vars']['bg']} !important;"
        + f"color:{theme['vars']['text']} !important;"
        + "}" 
    )

    # Light-only overrides. Streamlit and BaseWeb use several nested
    # wrappers; style the widget shell, its inner control and its suffix area.
    light_controls = """
    /* Text input, number input and text area shells */
    .stApp [data-testid="stTextInput"] [data-baseweb="input"],
    .stApp [data-testid="stTextInput"] [data-baseweb="base-input"],
    .stApp [data-testid="stNumberInput"] [data-baseweb="input"],
    .stApp [data-testid="stNumberInput"] [data-baseweb="base-input"],
    .stApp [data-testid="stTextArea"] [data-baseweb="textarea"] {
        background: var(--surface) !important;
        background-color: var(--surface) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
        color: var(--text) !important;
        box-shadow: none !important;
    }

    /* Some Streamlit versions put the dark fill on an extra inner wrapper. */
    .stApp [data-testid="stTextInput"] [data-baseweb="input"] > div,
    .stApp [data-testid="stTextInput"] [data-baseweb="base-input"] > div,
    .stApp [data-testid="stNumberInput"] [data-baseweb="input"] > div,
    .stApp [data-testid="stNumberInput"] [data-baseweb="base-input"] > div,
    .stApp [data-testid="stTextArea"] [data-baseweb="textarea"] > div {
        background: transparent !important;
        background-color: transparent !important;
        color: var(--text) !important;
    }

    .stApp [data-testid="stTextInput"] input,
    .stApp [data-testid="stNumberInput"] input,
    .stApp [data-testid="stTextArea"] textarea {
        background: transparent !important;
        background-color: transparent !important;
        color: var(--text) !important;
        -webkit-text-fill-color: var(--text) !important;
        caret-color: var(--primary-text) !important;
        box-shadow: none !important;
    }
    .stApp [data-testid="stTextInput"] input::placeholder,
    .stApp [data-testid="stNumberInput"] input::placeholder,
    .stApp [data-testid="stTextArea"] textarea::placeholder {
        color: var(--muted) !important;
        -webkit-text-fill-color: var(--muted) !important;
        opacity: 1 !important;
    }

    /* Selectbox: colour the complete control, including the arrow section. */
    .stApp [data-testid="stSelectbox"] [data-baseweb="select"] > div {
        background: var(--surface) !important;
        background-color: var(--surface) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
        color: var(--text) !important;
        box-shadow: none !important;
    }
    .stApp [data-testid="stSelectbox"] [data-baseweb="select"] > div > div,
    .stApp [data-testid="stSelectbox"] [data-baseweb="select"] [role="combobox"] {
        background: transparent !important;
        background-color: transparent !important;
        color: var(--text) !important;
    }
    .stApp [data-testid="stSelectbox"] [data-baseweb="select"] input {
        background: transparent !important;
        background-color: transparent !important;
        color: var(--text) !important;
        -webkit-text-fill-color: var(--text) !important;
    }
    .stApp [data-testid="stSelectbox"] [data-baseweb="select"] span,
    .stApp [data-testid="stSelectbox"] [data-baseweb="select"] div {
        color: var(--text) !important;
    }
    .stApp [data-testid="stSelectbox"] [data-baseweb="select"] svg {
        color: var(--muted) !important;
        fill: var(--muted) !important;
    }

    /* Focus treatment for all editable controls. */
    .stApp [data-testid="stTextInput"] [data-baseweb="input"]:focus-within,
    .stApp [data-testid="stNumberInput"] [data-baseweb="input"]:focus-within,
    .stApp [data-testid="stTextArea"] [data-baseweb="textarea"]:focus-within,
    .stApp [data-testid="stSelectbox"] [data-baseweb="select"]:focus-within > div {
        border-color: var(--primary-text) !important;
        box-shadow: 0 0 0 3px var(--primary-soft) !important;
    }

    /* Number input +/- controls */
    .stApp [data-testid="stNumberInput"] button,
    .stApp [data-testid="stNumberInputStepUp"],
    .stApp [data-testid="stNumberInputStepDown"] {
        background: var(--surface-2) !important;
        background-color: var(--surface-2) !important;
        color: var(--text) !important;
        border-color: var(--border) !important;
    }
    .stApp [data-testid="stNumberInput"] button svg {
        color: var(--text) !important;
        fill: var(--text) !important;
    }

    /* Dropdown popup is rendered outside the widget tree. */
    [data-baseweb="popover"],
    [data-baseweb="popover"] > div,
    [data-baseweb="menu"],
    [role="listbox"],
    [role="option"] {
        background: var(--surface) !important;
        background-color: var(--surface) !important;
        color: var(--text) !important;
    }
    [data-baseweb="popover"] > div {
        border: 1px solid var(--border) !important;
        border-radius: 10px !important;
    }
    [role="option"]:hover,
    [role="option"][aria-selected="true"] {
        background: var(--surface-2) !important;
        background-color: var(--surface-2) !important;
        color: var(--text) !important;
    }

    /* Disabled inputs and checkboxes */
    .stApp input:disabled,
    .stApp textarea:disabled {
        color: var(--muted) !important;
        -webkit-text-fill-color: var(--muted) !important;
        opacity: 1 !important;
    }
    .stApp [data-testid="stCheckbox"] input {
        accent-color: var(--primary-fill) !important;
    }
    .stApp [data-testid="stCheckbox"] [data-baseweb="checkbox"] > span:first-child {
        background: var(--surface) !important;
        background-color: var(--surface) !important;
        border-color: var(--muted) !important;
    }
    .stApp [data-testid="stCheckbox"] [data-baseweb="checkbox"] input:checked + span,
    .stApp [data-testid="stCheckbox"] label:has(input:checked) > span:first-child {
        background: var(--primary-fill) !important;
        background-color: var(--primary-fill) !important;
        border-color: var(--primary-fill) !important;
    }

    /*
       Final light-theme override for Streamlit/BaseWeb version differences.
       Some versions apply the dark fill to nested divs that do not carry a
       data-baseweb attribute. These broad widget-scoped rules catch those
       remaining layers without changing cards, tables, charts or the page.
    */
    .stApp [data-testid="stTextInput"] div,
    .stApp [data-testid="stNumberInput"] div,
    .stApp [data-testid="stTextArea"] div,
    .stApp [data-testid="stSelectbox"] div {
        background-color: var(--surface) !important;
        color: var(--text) !important;
    }

    .stApp [data-testid="stTextInput"] input,
    .stApp [data-testid="stNumberInput"] input,
    .stApp [data-testid="stTextArea"] textarea,
    .stApp [data-testid="stSelectbox"] input {
        background-color: transparent !important;
        color: var(--text) !important;
        -webkit-text-fill-color: var(--text) !important;
    }

    /* Keep number stepper buttons a subtly different light surface. */
    .stApp [data-testid="stNumberInput"] button,
    .stApp [data-testid="stNumberInputStepUp"],
    .stApp [data-testid="stNumberInputStepDown"] {
        background-color: var(--surface-2) !important;
        color: var(--text) !important;
    }

    /* Selectbox arrow/suffix area must not keep Streamlit's dark fill. */
    .stApp [data-testid="stSelectbox"] [data-baseweb="select"] > div > div:last-child {
        background-color: var(--surface) !important;
        color: var(--muted) !important;
    }
    .stApp [data-testid="stSelectbox"] [data-baseweb="select"] svg {
        color: var(--muted) !important;
        fill: var(--muted) !important;
    }

    /* Make the checkbox itself use the light palette as well. */
    .stApp [data-testid="stCheckbox"] [data-baseweb="checkbox"] > span {
        background-color: var(--surface) !important;
        border-color: var(--border) !important;
    }
    .stApp [data-testid="stCheckbox"] [data-baseweb="checkbox"] input:checked + span {
        background-color: var(--primary-fill) !important;
        border-color: var(--primary-fill) !important;
    }
    """ if theme["scheme"] == "light" else ""

    return "<style>" + FONT_IMPORT + root + STATIC_CSS + light_controls + "</style>"


# ------------------------------------------------------------
# SMALL HTML HELPERS
# ------------------------------------------------------------

def md(markup):
    """Render trusted HTML. All user text passed in must be escaped first."""
    st.markdown(markup, unsafe_allow_html=True)


def fmt(value):
    """Show whole numbers without .0 and keep decimals short."""
    if isinstance(value, bool) or value is None:
        return "" if value is None else str(value)
    if isinstance(value, (int, float)):
        return f"{value:.2f}".rstrip("0").rstrip(".")
    return str(value)


def join_names(names):
    names = list(names)
    if len(names) <= 1:
        return "".join(names)
    return ", ".join(names[:-1]) + " and " + names[-1]


def grade_chip(grade):
    return f'<span class="grade g{esc(grade)}">{esc(grade)}</span>'


def status_pill(result):
    css = "pass" if result == "Pass" else "fail"
    return f'<span class="pill {css}">{esc(result)}</span>'


def notice(kind, text):
    md(f'<div class="note {kind}">{esc(text)}</div>')


def page_header(title, subtitle=""):
    md(
        f'<div><div class="page-title">{esc(title)}</div>'
        f'<div class="page-sub">{esc(subtitle)}</div></div>'
    )


def card_title(title, subtitle=""):
    md(
        f'<div><div class="card-title">{esc(title)}</div>'
        f'<div class="card-sub">{esc(subtitle)}</div></div>'
    )


def table_html(headers, rows, numeric=()):
    """Build a scrollable table. Cells must already be safe HTML."""
    head = "".join(
        f'<th class="{"first" if i == 0 else ""} {"num" if i in numeric else ""}">{esc(h)}</th>'
        for i, h in enumerate(headers)
    )
    body = ""
    for row in rows:
        cells = "".join(
            f'<td class="{"first" if i == 0 else ""} {"num" if i in numeric else ""}">{cell}</td>'
            for i, cell in enumerate(row)
        )
        body += f"<tr>{cells}</tr>"
    return (
        '<div class="tbl-wrap"><table class="tbl">'
        f"<thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>"
    )


def stats_html(items):
    tiles = "".join(
        f'<div class="stat"><div class="stat-label">{esc(label)}</div>'
        f'<div class="stat-value">{value}</div></div>'
        for label, value in items
    )
    return f'<div class="stats">{tiles}</div>'


def subject_rows_html(subject_marks):
    """Bars for each subject. subject_marks maps subject -> mark."""
    from grade_functions import calculate_grade

    rows = ""
    for subject, mark in subject_marks.items():
        failing = mark < PASS_MARK
        width = max(0, min(100, mark))
        shown = f'<span class="m-fail">{fmt(mark)}</span>' if failing else fmt(mark)
        rows += (
            '<div class="srow">'
            f'<div class="sname">{esc(subject)}</div>'
            f'<div class="sval">{shown}{grade_chip(calculate_grade(mark))}</div>'
            f'<div class="sbar {"f" if failing else ""}"><span style="width:{width}%"></span></div>'
            "</div>"
        )
    return f'<div class="srows">{rows}</div>'


# ------------------------------------------------------------
# DATA HELPERS
# ------------------------------------------------------------

def load_reports():
    """Every saved student combined with the calculated result."""
    reports = []
    for student in view_students():
        try:
            result = get_student_result(student["marks"])
        except (ValueError, KeyError, TypeError, AttributeError):
            continue  # skip a damaged record instead of breaking the page
        report = dict(student)
        report.update(result)
        report.setdefault("class", "")
        reports.append(report)
    return reports


def subject_list(records):
    """Configured subjects first, then any extra subjects found in records."""
    subjects = list(SUBJECTS)
    for record in records:
        for subject in record.get("marks", {}):
            if subject not in subjects:
                subjects.append(subject)
    return subjects


def class_list(records):
    return sorted({r.get("class", "") for r in records if r.get("class", "")})


def clean_mark(value):
    """Turn 78.0 into 78 so saved records stay tidy."""
    if value is None:
        return None
    return int(value) if float(value).is_integer() else round(float(value), 2)


def suggest_next_id(students):
    """Suggest the next ID by continuing the most common pattern, e.g. STU004."""
    pattern = re.compile(r"^([A-Za-z]*)(\d+)$")
    groups = {}
    for student in students:
        match = pattern.match(str(student.get("id", "")).strip())
        if match:
            groups.setdefault(match.group(1).upper(), []).append(
                (int(match.group(2)), len(match.group(2)))
            )
    if not groups:
        return "STU001"
    prefix = max(groups, key=lambda p: len(groups[p]))
    numbers = groups[prefix]
    next_number = max(n for n, _ in numbers) + 1
    width = max(w for _, w in numbers)
    return f"{prefix}{next_number:0{width}d}"


def valid_email(email):
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email))


def valid_name(name):
    """Names may contain only letters, with single or multiple spaces between words."""
    return bool(re.fullmatch(r"[A-Za-z]+(?: +[A-Za-z]+)*", name.strip()))


NAME_ERROR = "The name can contain only letters and spaces. Remove numbers and special characters."


def recommendations(marks):
    """Practical hints shown while marks are being entered."""
    notes = []
    failing = [s for s, m in marks.items() if m < PASS_MARK]
    if failing:
        notes.append(
            (
                "err",
                f"Below the pass mark of {PASS_MARK} in {join_names(failing)}. "
                "The overall result will be Fail.",
            )
        )
    near = [s for s, m in marks.items() if PASS_MARK <= m < PASS_MARK + 5]
    if near:
        verb = "is" if len(near) == 1 else "are"
        notes.append(
            (
                "warn",
                f"{join_names(near)} {verb} only just above the pass mark. "
                "Check the entry before saving.",
            )
        )
    zeros = [s for s, m in marks.items() if m == 0]
    if zeros:
        notes.append(
            (
                "warn",
                f"A mark of 0 is entered for {join_names(zeros)}. "
                "Keep it only if the student scored 0 or was absent.",
            )
        )
    if len(marks) > 1:
        high = max(marks, key=marks.get)
        low = min(marks, key=marks.get)
        if marks[high] - marks[low] >= 40:
            notes.append(
                (
                    "info",
                    f"Marks range from {fmt(marks[low])} in {low} to {fmt(marks[high])} "
                    f"in {high}. Confirm the subjects were not swapped.",
                )
            )
    if not notes:
        notes.append(("ok", "The marks look consistent. This record is ready to save."))
    return notes


# ------------------------------------------------------------
# SESSION HELPERS
# ------------------------------------------------------------

def set_state(key, value):
    st.session_state[key] = value


def go_to(page):
    st.session_state["nav_radio"] = page


def flash(kind, text):
    st.session_state["flash"] = (kind, text)


def show_flash():
    message = st.session_state.pop("flash", None)
    if message:
        notice(*message)


def bump(name):
    st.session_state[name] = st.session_state.get(name, 0) + 1


def safe_select(label, options, key, **kwargs):
    """Selectbox that recovers when a stored choice no longer exists."""
    if key in st.session_state and st.session_state[key] not in options:
        del st.session_state[key]
    return st.selectbox(label, options, key=key, **kwargs)


def default_theme():
    try:
        if st.context.theme.type == "dark":
            return "Dark"
    except Exception:
        pass
    return "Light"


# ------------------------------------------------------------
# CHARTS
# ------------------------------------------------------------

PLOT_CONFIG = {"displayModeBar": False, "responsive": True}


def style_fig(fig, theme, height=300):
    colours = theme["vars"]
    fig.update_layout(
        height=height,
        margin=dict(l=4, r=8, t=10, b=4),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Public Sans, sans-serif", color=colours["muted"], size=12),
        showlegend=False,
        hoverlabel=dict(
            bgcolor=colours["surface"],
            bordercolor=colours["border"],
            font=dict(color=colours["text"], family="Public Sans, sans-serif"),
        ),
    )
    fig.update_xaxes(
        gridcolor=colours["border"],
        linecolor=colours["border"],
        zeroline=False,
        automargin=True,
    )
    fig.update_yaxes(
        gridcolor=colours["border"],
        linecolor=colours["border"],
        zeroline=False,
        automargin=True,
    )
    return fig


def chart_card(slug, title, subtitle, fig):
    with st.container(key=f"card_{slug}"):
        card_title(title, subtitle)
        st.plotly_chart(fig, theme=None, config=PLOT_CONFIG)


def unique_labels(reports):
    """Use the name, and add the ID only when two names are the same."""
    names = [r["name"] for r in reports]
    return [
        f'{r["name"]} ({r["id"]})' if names.count(r["name"]) > 1 else r["name"]
        for r in reports
    ]


def fig_grades(reports, theme):
    counts = [sum(1 for r in reports if r["grade"] == g) for g in GRADE_ORDER]
    fig = go.Figure(
        go.Bar(
            x=GRADE_ORDER,
            y=counts,
            marker_color=theme["grades"],
            text=counts,
            textposition="outside",
            cliponaxis=False,
            width=0.62,
            hovertemplate="Grade %{x}: %{y} students<extra></extra>",
        )
    )
    style_fig(fig, theme)
    fig.update_yaxes(range=[0, max(counts) * 1.2 + 1], tickformat="d")
    fig.update_xaxes(showgrid=False)
    return fig


def fig_pass_fail(passed, failed, theme):
    colours = theme["vars"]
    total = passed + failed
    rate = (passed / total * 100) if total else 0
    fig = go.Figure(
        go.Pie(
            labels=["Passed", "Failed"],
            values=[passed, failed],
            hole=0.7,
            sort=False,
            textinfo="none",
            marker=dict(
                colors=[colours["success"], colours["danger"]],
                line=dict(color=colours["surface"], width=3),
            ),
            hovertemplate="%{label}: %{value} (%{percent})<extra></extra>",
        )
    )
    style_fig(fig, theme)
    fig.update_layout(
        showlegend=True,
        legend=dict(orientation="h", x=0.5, xanchor="center", y=-0.02, font=dict(color=colours["muted"])),
    )
    fig.add_annotation(
        text=f"<b>{rate:.0f}%</b>", x=0.5, y=0.56, showarrow=False,
        font=dict(size=32, color=colours["text"]),
    )
    fig.add_annotation(
        text="pass rate", x=0.5, y=0.42, showarrow=False,
        font=dict(size=13, color=colours["muted"]),
    )
    return fig


def fig_subject_averages(averages, theme):
    items = sorted(averages.items(), key=lambda kv: kv[1])
    names = [k for k, _ in items]
    values = [v for _, v in items]
    colours = [theme["chart_soft"]] * len(values)
    if values:
        colours[-1] = theme["chart"]
        if len(values) > 1:
            colours[0] = theme["accent"]
    fig = go.Figure(
        go.Bar(
            x=values, y=names, orientation="h", marker_color=colours,
            text=[f"{v:.1f}" for v in values], textposition="outside", cliponaxis=False,
            hovertemplate="%{y}: %{x:.1f} average<extra></extra>",
        )
    )
    style_fig(fig, theme, height=300)
    fig.update_xaxes(range=[0, 112], tickvals=[0, 25, 50, 75, 100])
    fig.update_yaxes(showgrid=False)
    fig.add_vline(x=PASS_MARK, line_dash="dot", line_color=theme["vars"]["muted"], line_width=1)
    return fig


def fig_top_students(reports, theme):
    top = sorted(reports, key=lambda r: r["percentage"], reverse=True)[:5]
    labels = unique_labels(top)
    grade_colour = dict(zip(GRADE_ORDER, theme["grades"]))
    fig = go.Figure(
        go.Bar(
            x=[r["percentage"] for r in top], y=labels, orientation="h",
            marker_color=[grade_colour[r["grade"]] for r in top],
            text=[f'{r["percentage"]:.1f}%' for r in top], textposition="outside",
            cliponaxis=False,
            customdata=[r["grade"] for r in top],
            hovertemplate="%{y}: %{x:.1f}% (grade %{customdata})<extra></extra>",
        )
    )
    style_fig(fig, theme, height=300)
    fig.update_xaxes(range=[0, 115], tickvals=[0, 25, 50, 75, 100])
    fig.update_yaxes(autorange="reversed", showgrid=False)
    return fig


def fig_percentage_bands(reports, average, theme):
    labels = [f"{i}-{i + 9}" for i in range(0, 90, 10)] + ["90-100"]
    counts = [0] * 10
    for report in reports:
        counts[min(int(report["percentage"] // 10), 9)] += 1
    fig = go.Figure(
        go.Bar(
            x=labels, y=counts, marker_color=theme["chart"], text=counts,
            textposition="outside", cliponaxis=False, width=0.72,
            hovertemplate="%{x}%: %{y} students<extra></extra>",
        )
    )
    style_fig(fig, theme)
    fig.update_yaxes(range=[0, max(counts) * 1.25 + 1], tickformat="d")
    fig.update_xaxes(showgrid=False, tickangle=0, tickfont=dict(size=11))
    return fig


def fig_subject_pass_rate(reports, subjects, theme):
    rates = {}
    for subject in subjects:
        marks = [r["marks"][subject] for r in reports if subject in r["marks"]]
        if marks:
            rates[subject] = sum(1 for m in marks if m >= PASS_MARK) / len(marks) * 100
    items = sorted(rates.items(), key=lambda kv: kv[1])
    fig = go.Figure(
        go.Bar(
            x=[v for _, v in items], y=[k for k, _ in items], orientation="h",
            marker_color=[theme["chart"] if v == 100 else theme["accent"] for _, v in items],
            text=[f"{v:.0f}%" for _, v in items], textposition="outside", cliponaxis=False,
            hovertemplate="%{y}: %{x:.0f}% of students at or above the pass mark<extra></extra>",
        )
    )
    style_fig(fig, theme, height=300)
    fig.update_xaxes(range=[0, 115], tickvals=[0, 25, 50, 75, 100])
    fig.update_yaxes(showgrid=False)
    return fig


def fig_spread(reports, subjects, theme):
    fig = go.Figure()
    show_points = "all" if len(reports) <= 30 else "outliers"
    for subject in subjects:
        marks = [r["marks"][subject] for r in reports if subject in r["marks"]]
        if not marks:
            continue
        fig.add_trace(
            go.Box(
                y=marks, name=subject, boxpoints=show_points, jitter=0.45, pointpos=0,
                line=dict(color=theme["chart"], width=1.5), fillcolor=theme["box_fill"],
                marker=dict(color=theme["chart"], size=5, opacity=0.75),
                hoverinfo="y+name",
            )
        )
    style_fig(fig, theme, height=320)
    fig.update_yaxes(range=[0, 105], tickvals=[0, 25, 50, 75, 100])
    fig.update_xaxes(showgrid=False)
    fig.add_hline(y=PASS_MARK, line_dash="dot", line_color=theme["vars"]["muted"], line_width=1)
    return fig


def fig_class_compare(reports, theme):
    names, averages, rates = [], [], []
    for class_name in class_list(reports):
        group = [r for r in reports if r["class"] == class_name]
        names.append(class_name)
        averages.append(sum(r["percentage"] for r in group) / len(group))
        rates.append(sum(1 for r in group if r["result"] == "Pass") / len(group) * 100)
    fig = go.Figure()
    fig.add_trace(go.Bar(name="Average percentage", x=names, y=averages, marker_color=theme["chart"],
                         hovertemplate="%{x}: %{y:.1f}% average<extra></extra>"))
    fig.add_trace(go.Bar(name="Pass rate", x=names, y=rates, marker_color=theme["chart_soft"],
                         hovertemplate="%{x}: %{y:.0f}% pass rate<extra></extra>"))
    style_fig(fig, theme, height=300)
    fig.update_layout(
        barmode="group",
        showlegend=True,
        legend=dict(orientation="h", x=0, y=1.12, font=dict(color=theme["vars"]["muted"])),
    )
    fig.update_yaxes(range=[0, 105], tickvals=[0, 25, 50, 75, 100])
    fig.update_xaxes(showgrid=False)
    return fig


# ------------------------------------------------------------
# SHARED BLOCKS
# ------------------------------------------------------------

def empty_state(show_samples=True):
    md(
        '<div class="empty"><div class="empty-title">No student records yet</div>'
        '<div class="empty-text">Add the first student to start building the class picture. '
        "You can also load a small set of sample records to explore the dashboard "
        "and delete them later.</div></div>"
    )
    left, right, _ = st.columns([1, 1.3, 3])
    with left:
        st.button("Add a student", type="primary", on_click=go_to, args=("Add student",), key="empty_add")
    if show_samples:
        with right:
            if st.button("Load sample records", key="empty_samples"):
                load_samples()
                flash("ok", "Sample records loaded. Delete them from the Delete student page when you are done.")
                st.rerun()


def load_samples():
    for index, (name, class_name, marks) in enumerate(SAMPLE_RECORDS, start=1):
        padded = (marks + [60] * len(SUBJECTS))[: len(SUBJECTS)]
        email = name.lower().replace(" ", ".") + "@example.com"
        add_student(f"STU{index:03d}", name, class_name, dict(zip(SUBJECTS, padded)), email)


def class_picker(label, key, classes, default=None):
    """Pick an existing class or type a new one. Returns the class text."""
    if classes:
        options = classes + [NEW_CLASS]
        if default in classes:
            index = options.index(default)
        elif default:
            index = len(options) - 1
        else:
            index = None
        choice = st.selectbox(
            label, options, index=index, key=f"{key}_sel",
            placeholder="Choose a class or add a new one",
        )
        if choice is None:
            return ""
        if choice != NEW_CLASS:
            return choice
        initial = default if default and default not in classes else ""
        return st.text_input(
            "New class or course name", value=initial, key=f"{key}_txt",
            placeholder="e.g. BSc Computer Science, Year 2",
        ).strip()
    return st.text_input(
        label, value=default or "", key=f"{key}_txt",
        placeholder="e.g. BSc Computer Science, Year 2",
    ).strip()


def marks_inputs(subjects, key_prefix, current=None):
    """Number inputs for every subject. Returns subject -> value or None."""
    values = {}
    columns = st.columns(3)
    for index, subject in enumerate(subjects):
        start = None
        if current is not None and subject in current:
            start = float(current[subject])
        with columns[index % 3]:
            values[subject] = st.number_input(
                subject, min_value=0.0, max_value=100.0, value=start, step=1.0,
                format="%g", key=f"{key_prefix}_m_{subject}", placeholder="0 to 100",
            )
    return values


def preview_card(raw_marks, previous=None):
    """Live result preview with hints. raw_marks may contain None values."""
    entered = {s: clean_mark(v) for s, v in raw_marks.items() if v is not None}
    total_subjects = len(raw_marks)
    with st.container(key="card_preview"):
        card_title("Result preview", "Calculated with the same rules the records use.")
        if not entered:
            notice("info", f"Enter marks for all {total_subjects} subjects to see the total, grade and result.")
            return
        md(subject_rows_html(entered))
        if len(entered) < total_subjects:
            missing = total_subjects - len(entered)
            notice("info", f"{missing} more mark{'s' if missing != 1 else ''} needed to calculate the overall result.")
            return
        result = get_student_result(entered)
        md(
            '<div class="pv-top" style="margin-top:1.1rem">'
            f'<div><div class="pv-label">Overall percentage</div><div class="pv-pct">{fmt(result["percentage"])}%</div></div>'
            f'<div>{grade_chip(result["grade"])} &nbsp; {status_pill(result["result"])}</div></div>'
        )
        if previous is not None:
            md(
                f'<div class="pv-delta">Saved record: {fmt(previous["percentage"])}% '
                f'(grade {esc(previous["grade"])}, {esc(previous["result"])})</div>'
            )
        md(stats_html([
            ("Total", f'{fmt(result["total"])}<span class="of">/ {result["maximum_marks"]}</span>'),
            ("Percentage", f'{fmt(result["percentage"])}%'),
            ("Grade", grade_chip(result["grade"])),
            ("Result", status_pill(result["result"])),
        ]))
        for kind, text in recommendations(entered):
            notice(kind, text)


def guidelines_card():
    bands = "".join(f'<div>{grade_chip(g)} <span>{esc(r)}</span></div>' for g, r in GRADE_BANDS)
    with st.container(key="card_guide"):
        card_title("Entry guidelines")
        md(
            '<div class="card-sub" style="margin-bottom:.9rem">'
            f"Marks are out of 100 per subject. A student passes only with {PASS_MARK} or more in every subject. "
            "IDs are saved in capitals and must be unique."
            "</div>"
            f'<div class="bands">{bands}</div>'
        )


# ------------------------------------------------------------
# PAGES
# ------------------------------------------------------------

def page_dashboard(theme):
    reports = load_reports()
    all_classes = class_list(reports)

    options = [ALL_CLASSES] + all_classes
    if st.session_state.get("dash_class") not in options:
        st.session_state["dash_class"] = ALL_CLASSES

    head_left, head_right = st.columns([3, 1.1], gap="large")
    with head_right:
        if reports:
            chosen = st.selectbox("Class", options, key="dash_class")
        else:
            chosen = ALL_CLASSES
    scoped = reports if chosen == ALL_CLASSES else [r for r in reports if r["class"] == chosen]

    subjects = subject_list(scoped)
    averages = {}
    for subject in subjects:
        marks = [r["marks"][subject] for r in scoped if subject in r["marks"]]
        if marks:
            averages[subject] = sum(marks) / len(marks)

    with head_left:
        if scoped:
            passed = sum(1 for r in scoped if r["result"] == "Pass")
            failed = len(scoped) - passed
            summary = f"{len(scoped)} student{'s' if len(scoped) != 1 else ''}"
            summary += f" in {chosen}" if chosen != ALL_CLASSES else f" across {max(len(all_classes), 1)} class{'es' if len(all_classes) != 1 else ''}"
            summary += f": {passed} passed and {failed} did not."
            if len(averages) > 1:
                best = max(averages, key=averages.get)
                worst = min(averages, key=averages.get)
                summary += f" {best} has the highest average and {worst} the lowest."
            page_header("Dashboard", summary)
        else:
            page_header("Dashboard", "Class performance at a glance.")

    show_flash()
    if not reports:
        empty_state()
        return

    # ---- KPI strip ----
    count = len(scoped)
    average = sum(r["percentage"] for r in scoped) / count
    passed = sum(1 for r in scoped if r["result"] == "Pass")
    failed = count - passed
    pass_rate = passed / count * 100
    topper = max(scoped, key=lambda r: r["percentage"])
    overall_grade = None
    from grade_functions import calculate_grade
    overall_grade = calculate_grade(average)

    md(
        '<div class="kpis">'
        f'<div class="kpi"><div class="kpi-label">Total students</div><div class="kpi-value">{count}</div>'
        f'<div class="kpi-note">{len(class_list(scoped))} class{"es" if len(class_list(scoped)) != 1 else ""} in view</div></div>'
        f'<div class="kpi"><div class="kpi-label">Class average</div><div class="kpi-value">{average:.1f}%</div>'
        f'<div class="kpi-note">Grade {overall_grade} on the shared bands</div></div>'
        f'<div class="kpi lead"><div class="kpi-label">Pass rate</div><div class="kpi-value">{pass_rate:.1f}%</div>'
        f'<div class="meter"><span style="width:{pass_rate:.1f}%"></span></div></div>'
        f'<div class="kpi"><div class="kpi-label">Students passed</div><div class="kpi-value">{passed}</div>'
        f'<div class="kpi-note">{PASS_MARK}+ in every subject</div></div>'
        f'<div class="kpi"><div class="kpi-label">Students failed</div><div class="kpi-value">{failed}</div>'
        f'<div class="kpi-note">Below {PASS_MARK} in at least one</div></div>'
        f'<div class="kpi"><div class="kpi-label">Top performer</div><div class="kpi-value sm">{esc(topper["name"])}</div>'
        f'<div class="kpi-note">{topper["percentage"]:.1f}%, grade {esc(topper["grade"])}</div></div>'
        "</div>"
    )

    # ---- Charts ----
    col1, col2 = st.columns(2, gap="medium")
    with col1:
        chart_card("grades", "Grade distribution", "Students per overall grade.", fig_grades(scoped, theme))
    with col2:
        chart_card("passfail", "Pass and fail", f"A pass needs {PASS_MARK} or more in every subject.", fig_pass_fail(passed, failed, theme))

    col3, col4 = st.columns(2, gap="medium")
    with col3:
        if averages:
            ordered = sorted(averages.items(), key=lambda kv: kv[1])
            note = f"Highest: {ordered[-1][0]} ({ordered[-1][1]:.1f}). Lowest: {ordered[0][0]} ({ordered[0][1]:.1f}). Dotted line marks the pass mark."
            chart_card("subjectavg", "Subject averages", note, fig_subject_averages(averages, theme))
    with col4:
        chart_card("top5", "Top 5 students", "Ranked by overall percentage, coloured by grade.", fig_top_students(scoped, theme))

    col5, col6 = st.columns(2, gap="medium")
    with col5:
        chart_card("bands", "Percentage distribution", "How many students fall in each ten-point band.", fig_percentage_bands(scoped, average, theme))
    with col6:
        chart_card("subjectpass", "Subject pass rate", "Share of students at or above the pass mark in each subject.", fig_subject_pass_rate(scoped, subjects, theme))

    # ---- Optional class comparison ----
    # Keep this chart the same height as the other dashboard charts.
    multi_class = chosen == ALL_CLASSES and len(all_classes) > 1
    if multi_class:
        chart_card(
            "classes",
            "Class comparison",
            "Average percentage and pass rate for each class.",
            fig_class_compare(scoped, theme),
        )

    # The support table is intentionally separate and can use its natural height.
    attention_card(scoped)


def attention_card(reports):
    at_risk = []
    for report in reports:
        failing = [(s, m) for s, m in report["marks"].items() if m < PASS_MARK]
        if failing:
            at_risk.append((report, failing))
    at_risk.sort(key=lambda item: item[0]["percentage"])
    with st.container(key="card_attention"):
        card_title("Students needing support", f"Students below {PASS_MARK} in one or more subjects, lowest percentage first.")
        if not at_risk:
            notice("ok", f"Every student in view has {PASS_MARK} or more in each subject.")
            return
        rows = []
        for report, failing in at_risk[:8]:
            subjects_text = ", ".join(f"{esc(s)} {fmt(m)}" for s, m in failing)
            rows.append([
                f'<div class="nm">{esc(report["name"])}</div><div class="sub">{esc(report["id"])}</div>',
                f'{fmt(report["percentage"])}%',
                subjects_text,
            ])
        md(table_html(["Student", "Percentage", "Below the pass mark in"], rows, numeric=(1,)))
        if len(at_risk) > 8:
            st.caption(f"Showing 8 of {len(at_risk)} students.")


def page_add():
    page_header(
        "Add student",
        "Enter the details and subject marks. The result preview and hints update as you type.",
    )
    show_flash()
    students = view_students()
    version = st.session_state.setdefault("add_ver", 0)
    key = lambda name: f"add_{name}_{version}"

    form_col, side_col = st.columns([3, 2], gap="large")

    with form_col:
        with st.container(key="card_add_details"):
            card_title("Student details")
            left, right = st.columns(2)
            with left:
                # The ID is filled in automatically with the next ID in the sequence
                # and cannot be edited, so every new student gets a valid, unique ID.
                suggestion = suggest_next_id(students)
                st.session_state[key("id")] = suggestion
                student_id = st.text_input("Student ID", key=key("id"), disabled=True)
                st.caption("The next ID is assigned automatically.")
            with right:
                name = st.text_input("Full name", key=key("name"), placeholder="e.g. Anjali Menon")
            left, right = st.columns(2)
            with left:
                class_name = class_picker("Class / course", key("class"), class_list(students))
            with right:
                email = st.text_input("Email (optional)", key=key("email"), placeholder="name@example.com")

        with st.container(key="card_add_marks"):
            card_title("Subject marks", f"Out of 100 for each subject. Pass mark is {PASS_MARK}.")
            raw_marks = marks_inputs(SUBJECTS, key("marks"))

        student_id_clean = student_id.strip().upper()
        existing = search_student(student_id_clean) if student_id_clean else None
        if existing:
            notice("err", f'ID {student_id_clean} is already used by {existing["name"]}. Use a different ID.')
        name_bad = bool(name.strip()) and not valid_name(name)
        if name_bad:
            notice("err", NAME_ERROR)
        email_bad = bool(email.strip()) and not valid_email(email.strip())
        if email_bad:
            notice("warn", "The email address does not look complete. Use the form name@example.com or leave it empty.")

        missing = []
        if not student_id_clean:
            missing.append("Student ID")
        if not name.strip():
            missing.append("name")
        if not class_name:
            missing.append("class or course")
        missing += [s for s, v in raw_marks.items() if v is None]
        if missing:
            st.caption("Still needed: " + join_names(missing) + ".")

        if st.button("Save student", type="primary", key="save_add", disabled=bool(missing or existing or email_bad or name_bad)):
            marks = {s: clean_mark(v) for s, v in raw_marks.items()}
            ok, message = add_student(student_id_clean, name, class_name, marks, email)
            if ok:
                flash("ok", f"{name.strip()} ({student_id_clean}) was added.")
                bump("add_ver")
                st.rerun()
            else:
                notice("err", message)

    with side_col:
        preview_card(raw_marks)
        guidelines_card()


def page_view():
    page_header(
        "View students",
        "Search by name, ID or class. Each row shows subject marks with grades, plus the overall result.",
    )
    show_flash()
    reports = load_reports()
    if not reports:
        empty_state()
        return

    subjects = subject_list(reports)
    classes = class_list(reports)

    c1, c2, c3, c4 = st.columns([2.4, 1.6, 1, 1.5], gap="medium")
    with c1:
        query = st.text_input("Search", key="view_q", placeholder="Name, ID or class")
    with c2:
        class_filter = safe_select("Class", [ALL_CLASSES] + classes, key="view_class")
    with c3:
        status_filter = safe_select("Status", ["All", "Pass", "Fail"], key="view_status")
    with c4:
        sort_by = safe_select(
            "Sort by",
            ["Student ID", "Name (A to Z)", "Percentage (high to low)", "Percentage (low to high)"],
            key="view_sort",
        )

    tokens = query.strip().lower().split()
    shown = []
    for report in reports:
        haystack = f'{report["id"]} {report["name"]} {report["class"]}'.lower()
        if tokens and not all(token in haystack for token in tokens):
            continue
        if class_filter != ALL_CLASSES and report["class"] != class_filter:
            continue
        if status_filter != "All" and report["result"] != status_filter:
            continue
        shown.append(report)

    sorters = {
        "Student ID": (lambda r: r["id"].upper(), False),
        "Name (A to Z)": (lambda r: r["name"].lower(), False),
        "Percentage (high to low)": (lambda r: r["percentage"], True),
        "Percentage (low to high)": (lambda r: r["percentage"], False),
    }
    sort_key, reverse = sorters[sort_by]
    shown.sort(key=sort_key, reverse=reverse)

    md(f'<div class="count">Showing {len(shown)} of {len(reports)} students</div>')
    if not shown:
        notice("info", "No student matches these filters. Try a shorter search or set Class and Status back to All.")
        return

    rows = []
    for report in shown:
        cells = [
            f'<div class="nm">{esc(report["name"])}</div><div class="sub">{esc(report["id"])}</div>',
            esc(report["class"]),
        ]
        for subject in subjects:
            result = report["subject_results"].get(subject)
            if result:
                mark = f'<span class="m-fail">{fmt(result["mark"])}</span>' if result["result"] == "Fail" else fmt(result["mark"])
                cells.append(f'<span class="cellmark">{mark}{grade_chip(result["grade"])}</span>')
            else:
                cells.append("")
        cells += [
            f'{fmt(report["total"])}<span class="of"> / {report["maximum_marks"]}</span>',
            f'{fmt(report["percentage"])}%',
            grade_chip(report["grade"]),
            status_pill(report["result"]),
        ]
        rows.append(cells)
    headers = ["Student", "Class"] + subjects + ["Total", "Percentage", "Overall grade", "Status"]
    numeric = (len(subjects) + 2, len(subjects) + 3)
    md(table_html(headers, rows, numeric=numeric))

    # ---- Report card ----
    st.write("")
    ids = [r["id"] for r in shown]
    labels = {r["id"]: f'{r["id"]}  {r["name"]}' for r in shown}
    with st.container(key="card_reportcard"):
        card_title("Report card", "Pick a student from the filtered list for the full breakdown.")
        pick = safe_select("Student", ids, key="view_pick", format_func=lambda i: labels[i])
        report = get_student_report(pick)
        if report is None:
            notice("err", "This record could not be read.")
            return
        md(
            f'<div class="rc-name">{esc(report["name"])}</div>'
            f'<div class="rc-meta">{esc(report["id"])}, {esc(report.get("class", ""))}'
            f'{", " + esc(report["email"]) if report.get("email") else ""}</div>'
        )
        md(stats_html([
            ("Total", f'{fmt(report["total"])}<span class="of">/ {report["maximum_marks"]}</span>'),
            ("Percentage", f'{fmt(report["percentage"])}%'),
            ("Overall grade", grade_chip(report["grade"])),
            ("Status", status_pill(report["result"])),
        ]))
        left, right = st.columns([3, 2], gap="large")
        with left:
            md(subject_rows_html(report["marks"]))
        with right:
            marks = report["marks"]
            strongest = max(marks, key=marks.get)
            weakest = min(marks, key=marks.get)
            notice("ok", f"Strongest subject: {strongest} ({fmt(marks[strongest])}).")
            notice("warn" if marks[weakest] < PASS_MARK + 10 else "info", f"Weakest subject: {weakest} ({fmt(marks[weakest])}).")
            failing = [s for s, m in marks.items() if m < PASS_MARK]
            if failing:
                notice("err", f"Below the pass mark in {join_names(failing)}.")
            st.caption(f'Added {report.get("created_at", "n/a")}. Last updated {report.get("updated_at", "n/a")}.')


def page_update():
    page_header("Update student", "Choose a student, change what needs correcting, then save.")
    show_flash()
    students = view_students()
    if not students:
        empty_state()
        return

    ids = [s["id"] for s in students]
    labels = {s["id"]: f'{s["id"]}  {s["name"]}' for s in students}
    pick = safe_select("Student to edit", ids, key="upd_pick", format_func=lambda i: labels[i])
    student = search_student(pick)
    if student is None:
        notice("err", "This record could not be found.")
        return

    version = st.session_state.setdefault("upd_ver", 0)
    prefix = f"upd_{pick}_{version}"
    subjects = subject_list([student])
    classes = class_list(students)
    old_marks = student.get("marks", {})

    try:
        previous = get_student_result(old_marks)
    except ValueError:
        previous = None

    form_col, side_col = st.columns([3, 2], gap="large")
    with form_col:
        with st.container(key="card_upd_details"):
            card_title("Student details", "The ID cannot be changed. Delete and re-add the student if it is wrong.")
            left, right = st.columns(2)
            with left:
                st.text_input("Student ID", value=student["id"], disabled=True, key=f"{prefix}_id")
            with right:
                name = st.text_input("Full name", value=student.get("name", ""), key=f"{prefix}_name")
            left, right = st.columns(2)
            with left:
                class_name = class_picker("Class / course", f"{prefix}_class", classes, default=student.get("class", ""))
            with right:
                email = st.text_input("Email (optional)", value=student.get("email", ""), key=f"{prefix}_email", placeholder="name@example.com")
        with st.container(key="card_upd_marks"):
            card_title("Subject marks", f"Out of 100 for each subject. Pass mark is {PASS_MARK}.")
            raw_marks = marks_inputs(subjects, f"{prefix}_marks", current=old_marks)

        name_bad = bool(name.strip()) and not valid_name(name)
        if name_bad:
            notice("err", NAME_ERROR)
        email_bad = bool(email.strip()) and not valid_email(email.strip())
        if email_bad:
            notice("warn", "The email address does not look complete. Use the form name@example.com or leave it empty.")

        missing = []
        if not name.strip():
            missing.append("name")
        if not class_name:
            missing.append("class or course")
        missing += [s for s, v in raw_marks.items() if v is None]

        new_marks = {s: clean_mark(v) for s, v in raw_marks.items() if v is not None}
        changed = (
            name.strip() != student.get("name", "")
            or class_name != student.get("class", "")
            or email.strip() != student.get("email", "")
            or new_marks != {s: clean_mark(v) for s, v in old_marks.items()}
        )
        if missing:
            st.caption("Still needed: " + join_names(missing) + ".")
        elif not changed:
            st.caption("No changes yet. Edit a field to enable saving.")

        if st.button("Save changes", type="primary", key="save_upd", disabled=bool(missing or email_bad or name_bad or not changed)):
            ok, message = update_student(pick, name, class_name, new_marks, email)
            if ok:
                flash("ok", f'{name.strip()} ({pick}) was updated.')
                bump("upd_ver")
                st.rerun()
            else:
                notice("err", message)

    with side_col:
        preview_card(raw_marks, previous=previous)
        st.caption(f'Last updated {student.get("updated_at", "n/a")}.')


def page_delete():
    page_header("Delete student", "Removing a record is permanent. Export your data first if you may need it again.")
    show_flash()
    students = view_students()
    if not students:
        empty_state(show_samples=False)
        return

    ids = [s["id"] for s in students]
    labels = {s["id"]: f'{s["id"]}  {s["name"]}' for s in students}
    pick = safe_select("Student to delete", ids, key="del_pick", format_func=lambda i: labels[i])
    student = search_student(pick)
    if student is None:
        notice("err", "This record could not be found.")
        return

    try:
        report = get_student_report(pick)
    except ValueError:
        report = None

    version = st.session_state.setdefault("del_ver", 0)
    left, right = st.columns([3, 2], gap="large")
    with left:
        with st.container(key="card_delete"):
            card_title("Record to delete")
            md(
                f'<div class="rc-name">{esc(student.get("name", ""))}</div>'
                f'<div class="rc-meta">{esc(student["id"])}, {esc(student.get("class", ""))}'
                f'{", " + esc(student["email"]) if student.get("email") else ""}</div>'
            )
            if report:
                md(stats_html([
                    ("Total", f'{fmt(report["total"])}<span class="of">/ {report["maximum_marks"]}</span>'),
                    ("Percentage", f'{fmt(report["percentage"])}%'),
                    ("Overall grade", grade_chip(report["grade"])),
                    ("Status", status_pill(report["result"])),
                ]))
                md(subject_rows_html(report["marks"]))
            confirmed = st.checkbox(
                f'I understand that {student.get("name", "this student")} ({student["id"]}) '
                "will be permanently deleted and this cannot be undone.",
                key=f"del_ok_{pick}_{version}",
            )
            if st.button("Delete student record", key="delete_btn", disabled=not confirmed):
                ok, message = delete_student(pick)
                if ok:
                    flash("ok", f'{student.get("name", "Student")} ({pick}) was deleted.')
                    bump("del_ver")
                    st.rerun()
                else:
                    notice("err", message)
            if not confirmed:
                st.caption("Tick the confirmation to enable the delete button.")
    with right:
        with st.container(key="card_deletehelp"):
            card_title("Before you delete")
            md(
                '<div class="card-sub">Deleting removes the marks, class details and email for this student from '
                "the saved data file. Class statistics and charts update straight away.</div>"
            )
            st.button("Go to Export data", key="del_to_export", on_click=go_to, args=("Export data",))


def export_frame(reports, subjects, include_results):
    rows = []
    for report in reports:
        row = {
            "Student ID": report["id"],
            "Name": report["name"],
            "Class": report["class"],
            "Email": report.get("email", ""),
        }
        for subject in subjects:
            row[f"{subject} mark"] = report["marks"].get(subject)
        if include_results:
            for subject in subjects:
                row[f"{subject} grade"] = report["subject_results"].get(subject, {}).get("grade", "")
            row["Total"] = report["total"]
            row["Maximum marks"] = report["maximum_marks"]
            row["Percentage"] = report["percentage"]
            row["Overall grade"] = report["grade"]
            row["Status"] = report["result"]
        row["Added"] = report.get("created_at", "")
        row["Last updated"] = report.get("updated_at", "")
        rows.append(row)
    return pd.DataFrame(rows)


def page_export():
    page_header("Export data", "Download the saved records as a CSV file that opens in Excel, Google Sheets or any analysis tool.")
    show_flash()
    reports = load_reports()
    if not reports:
        empty_state(show_samples=False)
        return

    classes = class_list(reports)
    left, right = st.columns([3, 2], gap="large")
    with left:
        with st.container(key="card_export"):
            card_title("Export options")
            class_filter = safe_select("Class", [ALL_CLASSES] + classes, key="exp_class")
            include_results = st.checkbox(
                "Include grades, total, percentage and status", value=True, key="exp_results"
            )
            scoped = reports if class_filter == ALL_CLASSES else [r for r in reports if r["class"] == class_filter]
            frame = export_frame(scoped, subject_list(scoped), include_results)
            stamp = datetime.now().strftime("%Y%m%d_%H%M")
            csv_bytes = frame.to_csv(index=False).encode("utf-8-sig")
            md(f'<div class="count">{len(scoped)} student{"s" if len(scoped) != 1 else ""} and {len(frame.columns)} columns ready to download.</div>')
            st.download_button(
                "Download CSV", data=csv_bytes, file_name=f"students_{stamp}.csv",
                mime="text/csv", type="primary", key="dl_csv",
            )
            raw = [s for s in view_students() if s.get("id") in {r["id"] for r in scoped}]
            st.download_button(
                "Download JSON", data=json.dumps(raw, indent=2, ensure_ascii=False).encode("utf-8"),
                file_name=f"students_{stamp}.json", mime="application/json", key="dl_json",
            )
    with right:
        with st.container(key="card_exporthelp"):
            card_title("About the file")
            md(
                '<div class="card-sub">The CSV has one row per student with a column for each subject mark. '
                "It is saved with a byte order mark so accented names open correctly in Excel. "
                "The JSON file keeps the original record structure, which is useful as a backup.</div>"
            )

    st.write("")
    card_title("Preview", "The first five rows of the file.")
    preview = frame.head(5).fillna("")
    headers = list(preview.columns)
    rows = [[esc(fmt(v)) for v in row] for row in preview.itertuples(index=False)]
    md(table_html(headers, rows))


# ------------------------------------------------------------
# APP SHELL
# ------------------------------------------------------------

def main():
    st.set_page_config(
        page_title="Gradebook",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Keep the selected page and theme in Streamlit session state.
    # A radio selection triggers a rerun; the new value is read immediately
    # below before the theme stylesheet and page content are rendered.
    if "theme_radio" not in st.session_state:
        st.session_state["theme_radio"] = default_theme()
    if "nav_radio" not in st.session_state:
        st.session_state["nav_radio"] = PAGES[0]

    # Render the native theme selector first so its latest value is available
    # during this run. This is the same interaction pattern as the known-good
    # previous version, rather than a custom JavaScript/CSS toggle.
    _, theme_col = st.columns([8, 2])
    with theme_col:
        st.radio(
            "Theme",
            ["Light", "Dark"],
            horizontal=True,
            key="theme_radio",
            label_visibility="collapsed",
        )

    theme = THEMES[st.session_state["theme_radio"]]
    md(theme_css(theme))

    # Persistent left navigation: branded sidebar with six clear page buttons.
    with st.sidebar:
        md(
            '<div class="brand">'
            '<svg width="34" height="34" viewBox="0 0 34 34" aria-hidden="true">'
            '<rect x="3" y="17" width="7" height="13" rx="2" fill="var(--gD)"/>'
            '<rect x="13" y="10" width="7" height="20" rx="2" fill="var(--gB)"/>'
            '<rect x="23" y="3" width="7" height="27" rx="2" fill="var(--gA)"/>'
            '</svg>'
            '<div><div class="brand-name">Gradebook</div>'
            '<div class="brand-sub">Student grade management</div></div></div>'
        )
        md('<div class="nav-heading">NAVIGATION</div>')

        nav_items = [
            ("Dashboard", "⌂"),
            ("Add student", "＋"),
            ("View students", "♙"),
            ("Update student", "✎"),
            ("Delete student", "▤"),
            ("Export data", "⇩"),
        ]
        for nav_page, nav_icon in nav_items:
            st.button(
                f"{nav_icon}  {nav_page}",
                key=f"nav_{nav_page.lower().replace(' ', '_')}",
                type="primary" if st.session_state["nav_radio"] == nav_page else "secondary",
                use_container_width=True,
                on_click=lambda selected=nav_page: st.session_state.update({"nav_radio": selected}),
            )

        md(
            '<div class="sidebar-guide">'
            '<div class="sidebar-guide-title">ⓘ &nbsp; Quick guide</div>'
            '<div class="sidebar-guide-text">Use the menu above to manage students, '
            'view results and export data.</div></div>'
        )

    page = st.session_state["nav_radio"]
    if page == "Dashboard":
        page_dashboard(theme)
    elif page == "Add student":
        page_add()
    elif page == "View students":
        page_view()
    elif page == "Update student":
        page_update()
    elif page == "Delete student":
        page_delete()
    else:
        page_export()

main()