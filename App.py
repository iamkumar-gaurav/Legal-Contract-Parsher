"""
app.py  —  Contract Parser  |  Streamlit UI
Run: python -m streamlit run app.py
"""

import os, json, glob, time
from io import BytesIO
import streamlit as st

from config import PDF_FOLDER, OUTPUT_FOLDER
from pdf_loader import get_pdf_files, load_pdf, extract_text
from text_parser import format_structure, parse_to_dict
from openai_client import send_to_openai
from excel_exporter import export
from utils import extract_json_blocks, append_text_to_file, save_json_file, safe_remove

RAW_TXT_PATH  = "tmp_raw_output.txt"
JSON_TMP_PATH = "tmp_parsed.json"

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Contract Parser", page_icon="⚖️", layout="wide")

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: #0d0f14;
    color: #e8e6e0;
}

/* Hide default streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 2rem 3rem 4rem 3rem; max-width: 1300px; }

/* ── Hero banner ── */
.hero {
    background: linear-gradient(135deg, #0d1117 0%, #131820 50%, #0d1117 100%);
    border: 1px solid #1e2533;
    border-radius: 20px;
    padding: 3rem 3.5rem;
    margin-bottom: 2.5rem;
    position: relative;
    overflow: hidden;
}
.hero::before {
    content: '';
    position: absolute;
    top: -60px; right: -60px;
    width: 280px; height: 280px;
    background: radial-gradient(circle, rgba(99,179,237,0.12) 0%, transparent 70%);
    border-radius: 50%;
}
.hero::after {
    content: '';
    position: absolute;
    bottom: -40px; left: 100px;
    width: 200px; height: 200px;
    background: radial-gradient(circle, rgba(154,230,180,0.07) 0%, transparent 70%);
    border-radius: 50%;
}
.hero-logo {
    font-family: 'Syne', sans-serif;
    font-size: 3rem;
    font-weight: 800;
    letter-spacing: -1px;
    background: linear-gradient(90deg, #63b3ed, #9ae6b4, #63b3ed);
    background-size: 200%;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    animation: shimmer 4s linear infinite;
    line-height: 1.1;
    margin-bottom: 0.4rem;
}
@keyframes shimmer { 0%{background-position:0%} 100%{background-position:200%} }
.hero-sub {
    color: #718096;
    font-size: 1rem;
    font-weight: 300;
    letter-spacing: 0.5px;
}
.hero-badge {
    display: inline-block;
    background: rgba(99,179,237,0.1);
    border: 1px solid rgba(99,179,237,0.3);
    color: #63b3ed;
    border-radius: 20px;
    padding: 3px 12px;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-bottom: 1rem;
}

/* ── Stat cards ── */
.stat-row { display: flex; gap: 1rem; margin-bottom: 2rem; }
.stat-card {
    flex: 1;
    background: #131820;
    border: 1px solid #1e2533;
    border-radius: 14px;
    padding: 1.2rem 1.5rem;
    position: relative;
    overflow: hidden;
    transition: border-color 0.2s;
}
.stat-card:hover { border-color: #2d3748; }
.stat-card .accent { width: 3px; height: 100%; position: absolute; left: 0; top: 0; border-radius: 14px 0 0 14px; }
.stat-card .s-label { font-size: 0.72rem; color: #4a5568; font-weight: 600; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 0.4rem; }
.stat-card .s-value { font-family: 'Syne', sans-serif; font-size: 1.8rem; font-weight: 700; line-height: 1; }
.stat-card .s-unit  { font-size: 0.8rem; color: #718096; margin-top: 0.2rem; }

/* ── Section headers ── */
.section-head {
    font-family: 'Syne', sans-serif;
    font-size: 1.1rem;
    font-weight: 700;
    color: #e2e8f0;
    letter-spacing: 0.5px;
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
.section-head span { color: #4a5568; font-weight: 400; font-size: 0.85rem; font-family: 'DM Sans', sans-serif; }

/* ── PDF file cards ── */
.pdf-card {
    background: #131820;
    border: 1px solid #1e2533;
    border-radius: 12px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.6rem;
    display: flex;
    align-items: center;
    gap: 1rem;
    transition: border-color 0.2s, background 0.2s;
}
.pdf-card:hover { border-color: #2d3748; background: #161d27; }
.pdf-icon { font-size: 1.6rem; }
.pdf-name { font-weight: 500; font-size: 0.9rem; color: #e2e8f0; }
.pdf-meta { font-size: 0.75rem; color: #4a5568; margin-top: 2px; }
.pdf-badge {
    margin-left: auto;
    background: rgba(154,230,180,0.1);
    border: 1px solid rgba(154,230,180,0.25);
    color: #9ae6b4;
    border-radius: 20px;
    padding: 2px 10px;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.5px;
}

/* ── Progress log ── */
.log-box {
    background: #0a0d12;
    border: 1px solid #1a2030;
    border-radius: 12px;
    padding: 1.2rem 1.5rem;
    font-family: 'DM Mono', 'Courier New', monospace;
    font-size: 0.8rem;
    color: #a0aec0;
    min-height: 120px;
    max-height: 280px;
    overflow-y: auto;
    line-height: 1.8;
}
.log-step { color: #63b3ed; }
.log-ok   { color: #9ae6b4; }
.log-warn { color: #f6ad55; }
.log-err  { color: #fc8181; }

/* ── Result card ── */
.result-card {
    background: linear-gradient(135deg, #0f1a0f, #131820);
    border: 1px solid rgba(154,230,180,0.2);
    border-radius: 14px;
    padding: 1.5rem 2rem;
    margin-top: 1rem;
}
.result-title {
    font-family: 'Syne', sans-serif;
    font-size: 1rem;
    font-weight: 700;
    color: #9ae6b4;
    margin-bottom: 1rem;
}
.result-grid { display: flex; gap: 1.5rem; flex-wrap: wrap; }
.result-metric { text-align: center; }
.result-metric .rm-val { font-family: 'Syne', sans-serif; font-size: 1.6rem; font-weight: 800; color: #e2e8f0; }
.result-metric .rm-lbl { font-size: 0.72rem; color: #4a5568; text-transform: uppercase; letter-spacing: 1px; margin-top: 2px; }

/* ── Run button ── */
div[data-testid="stButton"] > button {
    background: linear-gradient(135deg, #2b6cb0, #2c7a5c) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    font-size: 1rem !important;
    padding: 0.75rem 2rem !important;
    letter-spacing: 0.5px !important;
    transition: opacity 0.2s !important;
    width: 100% !important;
}
div[data-testid="stButton"] > button:hover { opacity: 0.88 !important; }

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #0d0f14 !important;
    border-right: 1px solid #1e2533 !important;
}
section[data-testid="stSidebar"] .stTextInput input,
section[data-testid="stSidebar"] .stSelectbox select {
    background: #131820 !important;
    border: 1px solid #1e2533 !important;
    color: #e2e8f0 !important;
    border-radius: 8px !important;
}
.stMultiSelect > div { background: #131820 !important; border: 1px solid #1e2533 !important; border-radius: 10px !important; }
.stProgress > div > div { background: linear-gradient(90deg, #63b3ed, #9ae6b4) !important; border-radius: 4px !important; }
hr { border-color: #1e2533 !important; }
</style>
""", unsafe_allow_html=True)

# ── Session state init ─────────────────────────────────────────────────────────
for key, val in {
    "total_calls": 0,
    "total_tokens": 0,
    "total_time": 0.0,
    "total_clauses": 0,
    "total_pdfs": 0,
}.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='padding:1rem 0 0.5rem 0'>
        <div style='font-family:Syne,sans-serif;font-size:1.3rem;font-weight:800;
                    background:linear-gradient(90deg,#63b3ed,#9ae6b4);
                    -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                    background-clip:text;margin-bottom:0.2rem'>⚖️ Contract Parser</div>
        <div style='font-size:0.72rem;color:#4a5568;letter-spacing:1px;text-transform:uppercase'>Configuration</div>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

    st.markdown("<div style='font-size:0.75rem;color:#718096;font-weight:600;letter-spacing:1px;text-transform:uppercase;margin-bottom:0.5rem'>📁 Folders</div>", unsafe_allow_html=True)
    pdf_folder    = st.text_input("PDF Input Folder",  value=PDF_FOLDER,    label_visibility="collapsed", placeholder="PDF Input Folder")
    output_folder = st.text_input("Output Folder",     value=OUTPUT_FOLDER, label_visibility="collapsed", placeholder="Output Folder")
    st.caption(f"📥 Input: `{os.path.basename(pdf_folder)}`  |  📤 Output: `{os.path.basename(output_folder)}`")

    st.divider()
    st.markdown("<div style='font-size:0.75rem;color:#718096;font-weight:600;letter-spacing:1px;text-transform:uppercase;margin-bottom:0.5rem'>🤖 AI Model</div>", unsafe_allow_html=True)
    model_choice = st.selectbox("Model", options=[
        "openai/gpt-oss-120b:free",
        "meta-llama/llama-3.3-70b-instruct:free",
        "mistralai/mixtral-8x7b-instruct:free",
        "google/gemini-2.0-flash-exp:free",
        "deepseek/deepseek-chat:free",
    ], label_visibility="collapsed")
    model_colors = {
        "openai/gpt-oss-120b:free":                  ("#9ae6b4", "Best for legal text"),
        "meta-llama/llama-3.3-70b-instruct:free":    ("#63b3ed", "Strong open-source model"),
        "mistralai/mixtral-8x7b-instruct:free":      ("#f6ad55", "Large context window"),
        "google/gemini-2.0-flash-exp:free":          ("#fc8181", "Fast Google model"),
        "deepseek/deepseek-chat:free":               ("#b794f4", "Strong reasoning"),
    }
    mc, ml = model_colors[model_choice]
    st.markdown(f"<div style='font-size:0.75rem;color:{mc};margin-top:0.3rem'>● {ml}</div>", unsafe_allow_html=True)

    st.divider()
    st.markdown("<div style='font-size:0.75rem;color:#4a5568;letter-spacing:0.5px'>Get a free key at <a href='https://openrouter.ai/keys' style='color:#63b3ed'>openrouter.ai/keys</a></div>", unsafe_allow_html=True)

    st.divider()
    if st.button("🗑️ Reset Session Stats"):
        for k in ["total_calls","total_tokens","total_time","total_clauses","total_pdfs"]:
            st.session_state[k] = 0
        st.rerun()


# ── Hero ───────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <div class="hero-badge">⚖️ AI-Powered Legal Parser</div>
    <div class="hero-logo">Contract Parser</div>
    <div class="hero-sub">Transform dense legal PDFs into structured, actionable Excel reports — powered by Groq's blazing-fast inference.</div>
</div>
""", unsafe_allow_html=True)

# ── Session Stats ──────────────────────────────────────────────────────────────
st.markdown("""
<div class="section-head">📊 Session Statistics <span>resets on browser refresh</span></div>
<div class="stat-row">
    <div class="stat-card">
        <div class="accent" style="background:#63b3ed"></div>
        <div class="s-label">PDFs Processed</div>
        <div class="s-value" style="color:#63b3ed">{pdfs}</div>
        <div class="s-unit">files this session</div>
    </div>
    <div class="stat-card">
        <div class="accent" style="background:#9ae6b4"></div>
        <div class="s-label">Clauses Extracted</div>
        <div class="s-value" style="color:#9ae6b4">{clauses}</div>
        <div class="s-unit">total JSON blocks</div>
    </div>
    <div class="stat-card">
        <div class="accent" style="background:#f6ad55"></div>
        <div class="s-label">API Calls Made</div>
        <div class="s-value" style="color:#f6ad55">{calls}</div>
        <div class="s-unit">to Groq endpoint</div>
    </div>
    <div class="stat-card">
        <div class="accent" style="background:#fc8181"></div>
        <div class="s-label">Time Elapsed</div>
        <div class="s-value" style="color:#fc8181">{time}s</div>
        <div class="s-unit">total processing</div>
    </div>
</div>
""".format(
    pdfs   = st.session_state.total_pdfs,
    clauses= st.session_state.total_clauses,
    calls  = st.session_state.total_calls,
    time   = f"{st.session_state.total_time:.1f}",
), unsafe_allow_html=True)

st.divider()

# ── PDF Selector ───────────────────────────────────────────────────────────────
st.markdown('<div class="section-head">📂 Select PDFs to Process</div>', unsafe_allow_html=True)

try:
    pdf_files = get_pdf_files(pdf_folder)
    pdf_names = [os.path.basename(f) for f in pdf_files]
except FileNotFoundError as e:
    st.error(f"❌ {e}")
    st.info("Update the PDF Input Folder in the sidebar.")
    st.stop()

selected_names = st.multiselect(
    "Choose files:",
    options=pdf_names,
    default=pdf_names,
    placeholder="Select one or more PDFs...",
    label_visibility="collapsed",
)
selected_paths = [os.path.join(pdf_folder, n) for n in selected_names]

# File preview cards
if selected_names:
    for name in selected_names:
        path    = os.path.join(pdf_folder, name)
        size_kb = os.path.getsize(path) / 1024
        size_str= f"{size_kb/1024:.2f} MB" if size_kb > 1024 else f"{size_kb:.1f} KB"
        st.markdown(f"""
        <div class="pdf-card">
            <div class="pdf-icon">📄</div>
            <div>
                <div class="pdf-name">{name}</div>
                <div class="pdf-meta">{size_str}  ·  {pdf_folder}</div>
            </div>
            <div class="pdf-badge">READY</div>
        </div>
        """, unsafe_allow_html=True)

st.divider()

# ── Run ────────────────────────────────────────────────────────────────────────
if not selected_paths:
    st.warning("⚠️ Select at least one PDF above to continue.")
    st.stop()

run = st.button(f"⚡ Parse {len(selected_paths)} PDF{'s' if len(selected_paths)>1 else ''} with {model_choice.split('-')[0].upper()}")

if run:
    import config, excel_exporter
    config.OPENROUTER_MODEL      = model_choice
    excel_exporter.OUTPUT_FOLDER = output_folder
    os.makedirs(output_folder, exist_ok=True)

    all_results = []
    session_start = time.time()

    for pdf_path in selected_paths:
        pdf_name  = os.path.splitext(os.path.basename(pdf_path))[0]
        pdf_start = time.time()

        st.markdown(f'<div class="section-head">⚙️ Processing <span>{pdf_name}</span></div>', unsafe_allow_html=True)
        progress_bar = st.progress(0)
        log_slot     = st.empty()
        logs         = []

        def render_log(logs):
            log_slot.markdown(
                '<div class="log-box">' +
                "".join(f'<div class="{c}">{m}</div>' for c, m in logs) +
                '</div>', unsafe_allow_html=True
            )

        try:
            # 1 Extract
            logs.append(("log-step","▶  Extracting text from PDF..."))
            render_log(logs)
            pdf_data = load_pdf(pdf_path)
            raw_text = extract_text(pdf_data)
            progress_bar.progress(15)
            logs.append(("log-ok", f"✓  Text extracted — {len(raw_text):,} characters"))
            render_log(logs)

            # 2 Parse
            logs.append(("log-step","▶  Parsing sections & subsections..."))
            render_log(logs)
            structured   = format_structure(raw_text)
            content      = parse_to_dict(structured)
            section_count = len(content)
            progress_bar.progress(30)
            logs.append(("log-ok", f"✓  Found {section_count} sections"))
            render_log(logs)

            # 3 Groq
            safe_remove(RAW_TXT_PATH)
            all_subsections = [
                (sec, sub if sub != "No Subsection" else sec, det)
                for sec, subs in content.items() if isinstance(subs, dict)
                for sub, det in subs.items() if det
            ]
            total_subs   = len(all_subsections)
            total_blocks = 0
            api_calls    = 0

            logs.append(("log-step", f"▶  Sending {total_subs} subsections to Groq ({model_choice})..."))
            render_log(logs)

            debug_slot = st.empty()

            for idx, (section, subsection, details) in enumerate(all_subsections):
                bullets  = "\n".join(f"- {i}" for i in details)
                prompt   = f"section_name: {section}\nsubsection_name: {subsection}\nbulletpoints:\n{bullets}\n"
                response = send_to_openai(prompt)
                api_calls += 1

                if response:
                    if idx == 0:
                        preview = response[:1500].replace("<","&lt;").replace(">","&gt;")
                        debug_slot.markdown(
                            f"<details><summary style=\'color:#718096;font-size:0.8rem;cursor:pointer\'>🔍 Debug: Raw Groq response (first call)</summary>"
                            f"<pre style=\'background:#0a0d12;color:#9ae6b4;padding:1rem;border-radius:8px;font-size:0.75rem;overflow:auto;max-height:200px\'>{preview}</pre>"
                            f"</details>", unsafe_allow_html=True
                        )
                    blocks = extract_json_blocks(response)
                    if blocks:
                        for b in blocks:
                            append_text_to_file(RAW_TXT_PATH, json.dumps(b))
                        total_blocks += len(blocks)
                    else:
                        logs.append(("log-warn", f"  ⚠  Sub {idx+1}: response received but no valid JSON parsed"))
                        render_log(logs)
                else:
                    logs.append(("log-warn", f"  ⚠  Sub {idx+1}: no response from Groq"))
                    render_log(logs)

                pct = 30 + int((idx + 1) / max(total_subs, 1) * 55)
                progress_bar.progress(pct)

                if (idx + 1) % 5 == 0 or idx == total_subs - 1:
                    logs.append(("log-ok", f"  ✓  {idx+1}/{total_subs} processed  ·  {total_blocks} clauses extracted"))
                    render_log(logs)

            # 4 Export
            logs.append(("log-step","▶  Building Excel file..."))
            render_log(logs)

            all_data = []
            if os.path.exists(RAW_TXT_PATH):
                with open(RAW_TXT_PATH, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try: all_data.append(json.loads(line))
                            except: pass

            save_json_file(JSON_TMP_PATH, all_data)
            output_path = export(all_data, pdf_name)
            safe_remove(RAW_TXT_PATH, JSON_TMP_PATH)

            elapsed = time.time() - pdf_start
            progress_bar.progress(100)
            logs.append(("log-ok", f"✓  Done! → {output_path}"))
            logs.append(("log-ok", f"   {total_blocks} clauses  ·  {api_calls} API calls  ·  {elapsed:.1f}s"))
            render_log(logs)

            # Update session stats
            st.session_state.total_pdfs    += 1
            st.session_state.total_clauses += total_blocks
            st.session_state.total_calls   += api_calls
            st.session_state.total_time    += elapsed

            all_results.append({
                "name": pdf_name,
                "path": output_path,
                "clauses": total_blocks,
                "calls": api_calls,
                "elapsed": elapsed,
                "data": all_data,
            })

        except Exception as e:
            logs.append(("log-err", f"✗  Error: {e}"))
            render_log(logs)
            safe_remove(RAW_TXT_PATH, JSON_TMP_PATH)

    # ── Results ────────────────────────────────────────────────────────────────
    if all_results:
        st.divider()
        st.markdown('<div class="section-head">✅ Results</div>', unsafe_allow_html=True)

        for r in all_results:
            st.markdown(f"""
            <div class="result-card">
                <div class="result-title">📊 formatted_{r['name']}.xlsx</div>
                <div class="result-grid">
                    <div class="result-metric"><div class="rm-val">{r['clauses']}</div><div class="rm-lbl">Clauses</div></div>
                    <div class="result-metric"><div class="rm-val">{r['calls']}</div><div class="rm-lbl">API Calls</div></div>
                    <div class="result-metric"><div class="rm-val">{r['elapsed']:.1f}s</div><div class="rm-lbl">Time</div></div>
                    <div class="result-metric"><div class="rm-val">{round(r['elapsed']/max(r['calls'],1),1)}s</div><div class="rm-lbl">Avg/Call</div></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            with open(r["path"], "rb") as f:
                st.download_button(
                    label=f"⬇️  Download  formatted_{r['name']}.xlsx",
                    data=f,
                    file_name=f"formatted_{r['name']}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key=f"dl_{r['name']}",
                )

        st.rerun()   # refresh session stats at top