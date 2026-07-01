import streamlit as st

import time


from core.repo_loader import (
    clone_repository,
    get_python_files,
    get_commit_hash
)

from core.parser import (
    parse_python_file
)

from core import cache_manager

from retrieval.embeddings import (
    generate_embedding
)

from retrieval.vector_store import (
    VectorStore
)

from retrieval.hybrid_search import (
    HybridSearch
)

from retrieval.reranker import (
    Reranker
)

from llm.llm_engine import (
    generate_answer
)



# =====================================================
# CACHED RESOURCES
#
# Reranker loads a sentence-transformers model from disk. Without
# this it gets reloaded on every single "Analyze Repository" click,
# even when re-analyzing a repo whose embeddings are already cached.
# st.cache_resource keeps it alive for the lifetime of the server
# process instead.
# =====================================================


@st.cache_resource
def load_reranker():

    return Reranker()



# =====================================================
# PAGE CONFIG
# =====================================================


st.set_page_config(

    page_title="RepoMind",

    page_icon="🤖",

    layout="wide"

)

# Injected Notification System via Iframe Component
st.components.v1.html(
    """
    <script>
    // Request permission once on load
    if ("Notification" in window) {
        if (Notification.permission !== "granted" && Notification.permission !== "denied") {
            Notification.requestPermission();
        }
    }
    
    // Bind focus event listener to parent document to restore title
    try {
        window.parent.addEventListener('focus', function() {
            window.parent.document.title = "RepoMind";
        });
        window.parent.document.addEventListener('visibilitychange', function() {
            if (!window.parent.document.hidden) {
                window.parent.document.title = "RepoMind";
            }
        });
    } catch(e) {
        console.log("Could not bind parent document focus hooks:", e);
    }
    </script>
    """,
    height=0,
    width=0
)

if "notification_state" not in st.session_state:
    st.session_state.notification_state = "idle"

if st.session_state.notification_state == "ready":
    st.components.v1.html(
        """
        <script>
        try {
            window.parent.document.title = '✅ RepoMind • Answer Ready';
        } catch(e) {
            console.log("Could not set parent document title:", e);
        }
        
        // Play premium synth double-chime chime locally inside iframe
        try {
            const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            const osc1 = audioCtx.createOscillator();
            const gain1 = audioCtx.createGain();
            osc1.type = 'sine';
            osc1.frequency.setValueAtTime(587.33, audioCtx.currentTime);
            gain1.gain.setValueAtTime(0.08, audioCtx.currentTime);
            gain1.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.15);
            osc1.connect(gain1);
            gain1.connect(audioCtx.destination);
            osc1.start();
            osc1.stop(audioCtx.currentTime + 0.15);
            
            const osc2 = audioCtx.createOscillator();
            const gain2 = audioCtx.createGain();
            osc2.type = 'sine';
            osc2.frequency.setValueAtTime(880, audioCtx.currentTime + 0.1);
            gain2.gain.setValueAtTime(0.08, audioCtx.currentTime + 0.1);
            gain2.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.35);
            osc2.connect(gain2);
            gain2.connect(audioCtx.destination);
            osc2.start(audioCtx.currentTime + 0.1);
            osc2.stop(audioCtx.currentTime + 0.35);
        } catch(e) {
            console.log("Chime fail:", e);
        }
        
        // Show desktop notification via parent/iframe
        if ("Notification" in window && Notification.permission === "granted") {
            try {
                new Notification("RepoMind", {
                    body: "Your answer is ready.",
                    icon: "https://cdn-icons-png.flaticon.com/512/8643/8643881.png"
                });
            } catch(e) {
                console.log("Notification raise failed:", e);
            }
        }
        </script>
        """,
        height=0,
        width=0
    )
    st.session_state.notification_state = "idle"


st.markdown(
    """
    <style>
        :root {
            --bg-main: #09090b;
            --bg-panel: #18181b;
            --bg-panel-soft: #27272a;
            --border: rgba(255, 255, 255, 0.06);
            --border-active: rgba(255, 255, 255, 0.15);
            --text-main: #f4f4f5;
            --text-muted: #a1a1aa;
            --accent-color: #3b82f6;
            --font-sans: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            --font-mono: SFMono-Regular, Consolas, "Liberation Mono", Menlo, Courier, monospace;
        }

        /* Base Application Layout */
        .stApp {
            background-color: var(--bg-main);
            color: var(--text-main);
            font-family: var(--font-sans) !important;
        }

        [data-testid="stSidebar"] {
            background-color: #09090b !important;
            border-right: 1px solid rgba(255, 255, 255, 0.05) !important;
        }

        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
        [data-testid="stSidebar"] label p {
            color: #a1a1aa !important;
            font-family: var(--font-sans) !important;
            font-size: 0.74rem !important;
            font-weight: 500 !important;
            margin-bottom: 4px !important;
        }

        [data-testid="stSidebar"] label p {
            font-weight: 600 !important;
            letter-spacing: 0.02em !important;
            text-transform: uppercase !important;
        }

        /* Modernized Text Inputs & Selectboxes inside Sidebar */
        [data-testid="stSidebar"] .stTextInput input {
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            background-color: #1e1e22 !important;
            border-radius: 8px !important;
            color: #ffffff !important;
            font-family: var(--font-sans) !important;
            font-size: 0.78rem !important;
            padding: 8px 12px !important;
            transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
        }

        [data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] > div {
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            background-color: #1e1e22 !important;
            border-radius: 8px !important;
            color: #ffffff !important;
            font-family: var(--font-sans) !important;
            font-size: 0.78rem !important;
            transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
        }
        
        [data-testid="stSidebar"] .stTextInput input:focus,
        [data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] > div:focus-within {
            border-color: rgba(59, 130, 246, 0.4) !important;
            box-shadow: 0 0 8px rgba(59, 130, 246, 0.15) !important;
        }

        /* Ensure all text inside sidebar inputs and dropdowns is white */
        [data-testid="stSidebar"] input,
        [data-testid="stSidebar"] select,
        [data-testid="stSidebar"] div[data-baseweb="select"] *,
        [data-testid="stSidebar"] div[data-baseweb="select"] span,
        [data-testid="stSidebar"] div[role="listbox"] * {
            color: #ffffff !important;
        }

        /* Checkboxes as Sleek Glass Cards */
        [data-testid="stSidebar"] [data-testid="stCheckbox"] {
            border: 1px solid rgba(255, 255, 255, 0.04) !important;
            background-color: rgba(255, 255, 255, 0.01) !important;
            border-radius: 8px !important;
            padding: 8px 12px !important;
            margin-bottom: 8px !important;
            transition: all 0.2s ease !important;
        }
        
        [data-testid="stSidebar"] [data-testid="stCheckbox"]:hover {
            border-color: rgba(255, 255, 255, 0.08) !important;
            background-color: rgba(255, 255, 255, 0.03) !important;
        }

        /* Category Headers with Vertical Blue Indicator Strip */
        [data-testid="stSidebar"] .control-panel-section-header {
            color: #3b82f6 !important;
            border-left: 2.5px solid #3b82f6 !important;
            border-bottom: none !important;
            padding-left: 8px !important;
            font-weight: 700 !important;
            font-size: 0.65rem !important;
            letter-spacing: 0.08em !important;
            margin-top: 24px !important;
            margin-bottom: 12px !important;
            text-transform: uppercase !important;
            font-family: var(--font-sans) !important;
        }

        /* Sidebar Buttons (Primary & Secondary overrides) */
        [data-testid="stSidebar"] button[data-testid="baseButton-primary"] {
            background-color: #3b82f6 !important;
            border: 1px solid #3b82f6 !important;
            color: #ffffff !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            font-size: 0.8rem !important;
            min-height: 38px !important;
            width: 100% !important;
            transition: all 0.2s ease !important;
        }

        [data-testid="stSidebar"] button[data-testid="baseButton-primary"] *,
        [data-testid="stSidebar"] button[data-testid="baseButton-primary"] p {
            color: #ffffff !important;
        }
        
        [data-testid="stSidebar"] button[data-testid="baseButton-primary"]:hover {
            background-color: #2563eb !important;
            border-color: #2563eb !important;
            transform: translateY(-1px) !important;
        }

        [data-testid="stSidebar"] button[data-testid="baseButton-secondary"] {
            background-color: rgba(255, 255, 255, 0.03) !important;
            border: 1px solid rgba(255, 255, 255, 0.06) !important;
            color: #e4e4e7 !important;
            border-radius: 8px !important;
            font-weight: 500 !important;
            font-size: 0.78rem !important;
            min-height: 36px !important;
            width: 100% !important;
            transition: all 0.2s ease !important;
        }

        [data-testid="stSidebar"] button[data-testid="baseButton-secondary"] *,
        [data-testid="stSidebar"] button[data-testid="baseButton-secondary"] p {
            color: #e4e4e7 !important;
            transition: color 0.2s ease !important;
        }
        
        [data-testid="stSidebar"] button[data-testid="baseButton-secondary"]:hover {
            background-color: rgba(239, 68, 68, 0.08) !important;
            border-color: rgba(239, 68, 68, 0.2) !important;
        }

        [data-testid="stSidebar"] button[data-testid="baseButton-secondary"]:hover *,
        [data-testid="stSidebar"] button[data-testid="baseButton-secondary"]:hover p {
            color: #ef4444 !important;
        }

        .block-container {
            max-width: 1000px;
            padding-top: 3.5rem;
            padding-bottom: 5rem;
        }

        /* Lucide SVG Icons */
        .lucide-icon {
            width: 16px;
            height: 16px;
            stroke: var(--accent-color) !important;
            stroke-width: 2.2;
            stroke-linecap: round;
            stroke-linejoin: round;
            fill: none;
            display: inline-block;
            vertical-align: middle;
            margin-right: 6px;
        }

        /* Hero Banner */
        .repomind-hero {
            padding: 16px 0px 32px 0px;
            margin-bottom: 24px;
            background: transparent;
            border-bottom: 1px solid var(--border);
        }

        .repomind-kicker-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 10px;
        }

        .repomind-kicker {
            color: var(--accent-color);
            font-family: var(--font-sans);
            font-size: 0.74rem;
            font-weight: 600;
            letter-spacing: 0.05em;
            text-transform: uppercase;
        }

        .system-status-indicator {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 8px;
            background: rgba(16, 185, 129, 0.06);
            border: 1px solid rgba(16, 185, 129, 0.15);
            border-radius: 12px;
            font-family: var(--font-sans);
            font-size: 0.68rem;
            color: #34d399;
            font-weight: 500;
        }

        .status-pulse-dot {
            width: 6px;
            height: 6px;
            background-color: #34d399;
            border-radius: 50%;
            display: inline-block;
        }

        .repomind-title {
            color: #ffffff;
            font-family: var(--font-sans);
            font-size: 2.8rem;
            font-weight: 700;
            line-height: 1.15;
            margin: 0 0 12px 0;
            letter-spacing: -0.022em;
        }

        .repomind-subtitle {
            color: var(--text-muted);
            font-family: var(--font-sans);
            font-size: 1.02rem;
            max-width: 780px;
            line-height: 1.45;
            margin-bottom: 20px;
            letter-spacing: -0.01em;
        }

        .repomind-badges {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }

        .repomind-badge {
            border: 1px solid var(--border);
            border-radius: 6px;
            color: var(--text-main);
            background: rgba(255, 255, 255, 0.02);
            font-family: var(--font-sans);
            padding: 6px 12px;
            font-size: 0.76rem;
            font-weight: 500;
            transition: background-color 0.2s ease, border-color 0.2s ease;
        }
        
        .repomind-badge:hover {
            background: rgba(255, 255, 255, 0.05);
            border-color: var(--border-active);
        }

        /* Metric Cards */
        div[data-testid="stMetric"] {
            border: 1px solid var(--border) !important;
            border-radius: 6px !important;
            padding: 14px 18px !important;
            background: rgba(255, 255, 255, 0.02) !important;
            transition: border-color 0.2s ease, background-color 0.2s ease;
        }
        
        div[data-testid="stMetric"]:hover {
            border-color: var(--border-active) !important;
            background-color: rgba(255, 255, 255, 0.04) !important;
        }

        div[data-testid="stMetric"] label {
            color: var(--text-muted) !important;
            font-family: var(--font-sans) !important;
            font-weight: 500 !important;
            font-size: 0.76rem !important;
        }

        div[data-testid="stMetricValue"] {
            color: #ffffff !important;
            font-family: var(--font-sans) !important;
            font-weight: 600 !important;
            font-size: 1.6rem !important;
            letter-spacing: -0.02em;
        }

        /* Buttons */
        .stButton > button {
            border: 1px solid var(--accent-color) !important;
            border-radius: 6px !important;
            background-color: var(--accent-color) !important;
            color: #ffffff !important;
            font-family: var(--font-sans) !important;
            font-weight: 600 !important;
            min-height: 38px;
            font-size: 0.84rem !important;
            transition: background-color 0.2s ease, border-color 0.2s ease, transform 0.2s ease !important;
            width: 100%;
        }

        .stButton > button:hover {
            background-color: #2563eb !important;
            border-color: #2563eb !important;
            color: #ffffff !important;
        }

        .stButton > button:active {
            transform: scale(0.99) !important;
        }

        /* Column Specific Buttons (Quick Start Prompts) */
        div[data-testid="column"] .stButton > button {
            border: 1px solid var(--border) !important;
            border-radius: 6px !important;
            background-color: rgba(255, 255, 255, 0.02) !important;
            color: var(--text-main) !important;
            font-family: var(--font-sans) !important;
            font-size: 0.78rem !important;
            min-height: 52px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            text-align: center !important;
            line-height: 1.35 !important;
            padding: 8px 12px !important;
            white-space: normal !important;
            word-break: break-word !important;
            transition: border-color 0.2s ease, background-color 0.2s ease, transform 0.2s ease !important;
        }

        div[data-testid="column"] .stButton > button:hover {
            border-color: var(--border-active) !important;
            background-color: rgba(255, 255, 255, 0.06) !important;
            transform: translateY(-1px) !important;
        }

        /* Inputs & Selectboxes */
        .stTextInput input,
        .stSelectbox div[data-baseweb="select"] > div {
            border-radius: 6px !important;
            border: 1px solid var(--border) !important;
            background-color: rgba(255, 255, 255, 0.02) !important;
            color: var(--text-main) !important;
            font-family: var(--font-sans) !important;
            font-size: 0.8rem !important;
            transition: border-color 0.2s ease !important;
        }
        
        .stTextInput input:focus,
        .stSelectbox div[data-baseweb="select"] > div:focus-within {
            border-color: var(--border-active) !important;
            box-shadow: none !important;
        }

        /* Control Panel Section Headers */
        .control-panel-section-header {
            font-family: var(--font-sans);
            font-size: 0.7rem;
            letter-spacing: 0.05em;
            color: var(--text-main);
            font-weight: 600;
            margin-top: 22px;
            margin-bottom: 10px;
            border-bottom: 1px solid var(--border);
            padding-bottom: 6px;
            text-transform: uppercase;
        }

        /* Chat Layout */
        [data-testid="stChatMessage"] {
            border: 1px solid var(--border) !important;
            border-radius: 8px !important;
            padding: 16px 20px !important;
            margin-bottom: 16px !important;
            background-color: rgba(255, 255, 255, 0.02) !important;
        }

        [data-testid="stChatMessageContent-user"] {
            background: transparent !important;
        }

        [data-testid="stChatMessageContent-assistant"] {
            background: transparent !important;
        }

        [data-testid="stChatMessage"] code {
            color: #34d399 !important;
            background: rgba(52, 211, 153, 0.06) !important;
            border: 1px solid rgba(52, 211, 153, 0.12) !important;
            border-radius: 4px !important;
            padding: 2px 5px !important;
            font-size: 0.88em !important;
            font-family: var(--font-mono) !important;
        }

        /* Custom Chat Input Bar (Cursor/ChatGPT Styled) - Sticky bottom bar */
        div.block-container div[data-testid="stHorizontalBlock"]:has(input[placeholder="Ask RepoMind..."]) {
            position: sticky !important;
            bottom: 16px !important;
            width: 100% !important;
            background-color: rgba(30, 30, 34, 0.95) !important;
            backdrop-filter: blur(12px) !important;
            border: 1px solid rgba(255, 255, 255, 0.12) !important;
            border-radius: 12px !important;
            padding: 4px 10px !important;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25) !important;
            z-index: 99999 !important;
            margin-top: 24px !important;
            display: flex !important;
            align-items: center !important;
        }

        /* Remove default borders and paddings from the columns wrapper inside the custom bar */
        div.block-container div[data-testid="stHorizontalBlock"]:has(input[placeholder="Ask RepoMind..."]) div[data-testid="column"] {
            background-color: transparent !important;
            border: none !important;
            padding: 0 !important;
            display: flex !important;
            align-items: center !important;
        }

        /* Zero out default Streamlit widget margins inside the chat bar */
        div.block-container div[data-testid="stHorizontalBlock"]:has(input[placeholder="Ask RepoMind..."]) .stTextInput,
        div.block-container div[data-testid="stHorizontalBlock"]:has(input[placeholder="Ask RepoMind..."]) .stButton {
            margin-bottom: 0 !important;
            margin-top: 0 !important;
            width: 100% !important;
        }

        /* Borderless and transparent background input element */
        div.block-container div[data-testid="stHorizontalBlock"]:has(input[placeholder="Ask RepoMind..."]) input {
            border: none !important;
            background-color: transparent !important;
            color: #ffffff !important;
            font-size: 0.85rem !important;
            padding: 6px 0 !important;
            box-shadow: none !important;
        }

        /* Compact Send button next to the input */
        div.block-container div[data-testid="stHorizontalBlock"]:has(input[placeholder="Ask RepoMind..."]) button {
            background-color: var(--accent-color) !important;
            border: none !important;
            border-radius: 8px !important;
            color: #ffffff !important;
            width: 28px !important;
            height: 28px !important;
            min-height: 28px !important;
            max-height: 28px !important;
            padding: 0 !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            margin: 0 !important;
            transition: all 0.2s ease !important;
        }

        div.block-container div[data-testid="stHorizontalBlock"]:has(input[placeholder="Ask RepoMind..."]) button:hover {
            background-color: #2563eb !important;
            transform: scale(1.04) !important;
        }

        div.block-container div[data-testid="stHorizontalBlock"]:has(input[placeholder="Ask RepoMind..."]) button:active {
            transform: scale(0.96) !important;
        }

        .repomind-prompt-strip {
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 14px 18px;
            margin: 8px 0 20px 0;
            background: rgba(255, 255, 255, 0.02);
        }

        .repomind-prompt-strip b {
            color: #ffffff;
            font-size: 0.82rem;
            font-family: var(--font-sans);
        }

        .repomind-prompt-strip span {
            display: inline-block;
            margin: 6px 6px 0 0;
            padding: 4px 10px;
            border-radius: 4px;
            color: var(--text-main);
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--border);
            font-family: var(--font-sans);
            font-size: 0.74rem;
            font-weight: 500;
        }

        /* System Status Readout */
        .system-status-readout {
            border: 1px solid var(--border);
            border-radius: 6px;
            background: rgba(255, 255, 255, 0.01);
            font-family: var(--font-sans);
            padding: 12px;
            margin-top: 10px;
        }

        .readout-header {
            color: var(--text-muted);
            font-size: 0.65rem;
            letter-spacing: 0.05em;
            border-bottom: 1px solid var(--border);
            padding-bottom: 6px;
            margin-bottom: 8px;
            font-weight: 600;
            text-transform: uppercase;
        }

        .readout-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 8px 12px;
        }

        .readout-item {
            display: flex;
            flex-direction: column;
            gap: 2px;
        }

        .readout-key {
            font-size: 0.65rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.02em;
        }

        .readout-val {
            font-size: 0.78rem;
            color: var(--text-main);
            font-weight: 500;
        }

        /* =====================================
           Expander Card Redesign
        ===================================== */
        /* Collapsed state (Indigo tint cards) */
        div[data-testid="stExpander"] {
            border: 1px solid rgba(59, 130, 246, 0.16) !important;
            background-color: #10121a !important;
            border-radius: 8px !important;
            margin-bottom: 14px !important;
            transition: all 0.25s ease !important;
        }

        div[data-testid="stExpander"] summary p {
            color: #93c5fd !important;
            font-weight: 600 !important;
            transition: color 0.25s ease !important;
        }

        div[data-testid="stExpander"]:hover {
            border-color: rgba(59, 130, 246, 0.35) !important;
            background-color: #141724 !important;
        }

        /* Expanded state (looks normal/default canvas panel when opened) */
        div[data-testid="stExpander"]:has(details[open]) {
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            background-color: #161619 !important;
        }

        div[data-testid="stExpander"]:has(details[open]) summary p {
            color: #ffffff !important;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# =====================================================
# HEADER & ARCHITECTURE
# =====================================================

st.markdown(
    """
    <div class="repomind-hero">
        <div class="repomind-kicker-row">
            <div class="repomind-kicker">Local Repository RAG Engine</div>
            <div class="system-status-indicator">
                <span class="status-pulse-dot"></span>
                <span>PIPELINE READY</span>
            </div>
        </div>
        <h1 class="repomind-title">RepoMind</h1>
        <div class="repomind-subtitle">
            Explore and understand complex codebases locally. Query codebase architecture, trace dependencies, locate specific feature implementations, and generate explanations with private local models.
        </div>
        <div class="repomind-badges">
            <span class="repomind-badge">FAISS + BM25 Hybrid Retrieval</span>
            <span class="repomind-badge">MS-MARCO Reranker</span>
            <span class="repomind-badge">Ollama Local LLM</span>
            <span class="repomind-badge">100% Private</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

with st.expander("🏗️ System Architecture & Data Flow"):
    st.markdown(
        """<div style="background: var(--bg-panel); padding: 20px; border-radius: 8px; border: 1px solid var(--border); overflow-x: auto; margin-top: 8px;">
<svg viewBox="0 0 920 120" width="100%" height="100%" style="min-width: 820px; background: transparent; font-family: var(--font-sans);">
<defs>
<filter id="glow-effect" x="-20%" y="-20%" width="140%" height="140%">
<feGaussianBlur stdDeviation="3" result="blur" />
<feMerge>
<feMergeNode in="blur" />
<feMergeNode in="SourceGraphic" />
</feMerge>
</filter>
<style>
@keyframes strokeGlow {
0% { stroke-opacity: 0.4; }
50% { stroke-opacity: 1; }
100% { stroke-opacity: 0.4; }
}
.pulse-node {
stroke: var(--accent-color) !important;
stroke-width: 1.5px !important;
animation: strokeGlow 2.5s infinite ease-in-out;
}
</style>
</defs>
<g transform="translate(10, 15)">
<rect width="105" height="60" rx="6" fill="#1c1c1e" stroke="var(--border)" stroke-width="1" />
<text x="52.5" y="28" fill="#ffffff" font-size="11" font-weight="600" text-anchor="middle">📂 Source Repo</text>
<text x="52.5" y="44" fill="var(--text-muted)" font-size="9" font-family="var(--font-mono)" text-anchor="middle">Git / GitHub</text>
</g>
<!-- Connection 1 -->
<path d="M 115 45 L 140 45" stroke="var(--border)" stroke-width="1.5" />
<circle r="2" fill="var(--accent-color)">
<animateMotion dur="2.5s" repeatCount="indefinite" path="M 115 45 L 140 45" />
</circle>
<g transform="translate(140, 15)">
<rect width="115" height="60" rx="6" fill="#1c1c1e" stroke="var(--border)" stroke-width="1" />
<text x="57.5" y="28" fill="#ffffff" font-size="11" font-weight="600" text-anchor="middle">⚙️ AST Parser</text>
<text x="57.5" y="44" fill="var(--text-muted)" font-size="9" font-family="var(--font-mono)" text-anchor="middle">code_parsing</text>
</g>
<!-- Connection 2 -->
<path d="M 255 45 L 280 45" stroke="var(--border)" stroke-width="1.5" />
<circle r="2" fill="var(--accent-color)">
<animateMotion dur="2.2s" repeatCount="indefinite" path="M 255 45 L 280 45" />
</circle>
<g transform="translate(280, 15)">
<rect width="120" height="60" rx="6" fill="#1c1c1e" stroke="var(--border)" stroke-width="1" />
<text x="60" y="28" fill="#ffffff" font-size="11" font-weight="600" text-anchor="middle">🧠 Embeddings</text>
<text x="60" y="44" fill="var(--text-muted)" font-size="9" font-family="var(--font-mono)" text-anchor="middle">nomic-embed</text>
</g>
<!-- Connection 3 -->
<path d="M 400 45 L 425 45" stroke="var(--border)" stroke-width="1.5" />
<circle r="2" fill="var(--accent-color)">
<animateMotion dur="1.8s" repeatCount="indefinite" path="M 400 45 L 425 45" />
</circle>
<g transform="translate(425, 15)">
<rect width="130" height="60" rx="6" fill="#1c1c1e" stroke="var(--accent-color)" stroke-width="1" class="pulse-node" filter="url(#glow-effect)" />
<text x="65" y="28" fill="var(--accent-color)" font-size="11" font-weight="700" text-anchor="middle">🔍 Hybrid Search</text>
<text x="65" y="44" fill="#ffffff" font-size="9" font-family="var(--font-mono)" text-anchor="middle">FAISS + BM25</text>
</g>
<!-- Connection 4 -->
<path d="M 555 45 L 580 45" stroke="var(--border)" stroke-width="1.5" />
<circle r="2" fill="var(--accent-color)">
<animateMotion dur="2s" repeatCount="indefinite" path="M 555 45 L 580 45" />
</circle>
<g transform="translate(580, 15)">
<rect width="120" height="60" rx="6" fill="#1c1c1e" stroke="var(--border)" stroke-width="1" />
<text x="60" y="28" fill="#ffffff" font-size="11" font-weight="600" text-anchor="middle">🎯 MiniLM Rerank</text>
<text x="60" y="44" fill="var(--text-muted)" font-size="9" font-family="var(--font-mono)" text-anchor="middle">cross_encoder</text>
</g>
<!-- Connection 5 -->
<path d="M 700 45 L 735 45" stroke="var(--border)" stroke-width="1.5" />
<circle r="2" fill="var(--accent-color)">
<animateMotion dur="1.6s" repeatCount="indefinite" path="M 700 45 L 735 45" />
</circle>
<g transform="translate(735, 15)">
<rect width="145" height="60" rx="6" fill="#1c1c1e" stroke="var(--accent-color)" stroke-width="1" class="pulse-node" filter="url(#glow-effect)" />
<text x="72.5" y="28" fill="var(--accent-color)" font-size="11" font-weight="700" text-anchor="middle">🤖 Local LLM</text>
<text x="72.5" y="44" fill="#ffffff" opacity="0.85" font-size="9" font-family="var(--font-mono)" text-anchor="middle">Qwen2.5-Coder (Ollama)</text>
</g>
</svg>
</div>""",
        unsafe_allow_html=True
    )

def render_repository_overview(metadata: dict):
    if not metadata:
        st.info("No repository metadata available. Please index a repository first.")
        return

    # Statistics row
    stats = metadata.get("statistics", {})
    if stats:
        st.markdown("<h4 style='margin: 0 0 10px 0; font-size: 0.95rem; font-weight: 600; color: #ffffff;'>📈 Repository Stats</h4>", unsafe_allow_html=True)
        s1, s2, s3, s4 = st.columns(4)
        s1.metric("Total Files", stats.get("total_files", 0))
        s2.metric("Source Files", stats.get("source_files", 0))
        s3.metric("Directories", stats.get("folders", 0))
        s4.metric("Code Chunks", stats.get("code_chunks", 0))
        
        # Mini checklist row
        readme = stats.get("readme_present", "No")
        license = stats.get("license_present", "No")
        gitignore = stats.get("gitignore_present", "No")
        
        st.markdown(
            f"""
            <div style="display: flex; gap: 15px; margin-bottom: 20px; font-size: 0.78rem; color: var(--text-muted);">
                <span>📝 README: <b style="color: {'#34d399' if readme == 'Yes' else '#f87171'}">{readme}</b></span>
                <span>⚖️ LICENSE: <b style="color: {'#34d399' if license == 'Yes' else '#f87171'}">{license}</b></span>
                <span>🚫 .gitignore: <b style="color: {'#34d399' if gitignore == 'Yes' else '#f87171'}">{gitignore}</b></span>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Core tech details grid
    st.markdown("<h4 style='margin: 15px 0 10px 0; font-size: 0.95rem; font-weight: 600; color: #ffffff;'>🛠️ Tech Stack & Architecture</h4>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    
    with c1:
        # Languages
        langs = metadata.get("languages", [])
        lang_str = "".join([f"<div style='background: rgba(255,255,255,0.02); border: 1px solid var(--border); border-radius: 6px; padding: 6px 12px; margin-bottom: 6px; font-size: 0.76rem; color: var(--text-main);'>🔹 {l}</div>" for l in langs])
        st.markdown(f"**Languages**\n{lang_str if langs else 'None Detected'}", unsafe_allow_html=True)
        
        # Database
        dbs = metadata.get("database", [])
        db_str = "".join([f"<span style='background: rgba(59, 130, 246, 0.08); border: 1px solid rgba(59, 130, 246, 0.2); border-radius: 4px; padding: 3px 8px; margin-right: 6px; margin-bottom: 6px; display: inline-block; font-size: 0.72rem; color: var(--accent-color); font-weight: 500;'>{d}</span>" for d in dbs])
        st.markdown(f"<div style='margin-top: 15px;'><b>Database</b></div><div style='margin-top: 6px;'>{db_str if dbs and dbs != ['Not Detected'] else '<span style=color:var(--text-muted)>None Detected</span>'}</div>", unsafe_allow_html=True)

    with c2:
        # Frameworks
        fws = metadata.get("frameworks", [])
        fw_str = "".join([f"<span style='background: rgba(52, 211, 153, 0.08); border: 1px solid rgba(52, 211, 153, 0.2); border-radius: 4px; padding: 3px 8px; margin-right: 6px; margin-bottom: 6px; display: inline-block; font-size: 0.72rem; color: #34d399; font-weight: 500;'>{f}</span>" for f in fws])
        st.markdown(f"**Frameworks**\n<div style='margin-top: 6px;'>{fw_str if fws and fws != ['Not Detected'] else '<span style=color:var(--text-muted)>None Detected</span>'}</div>", unsafe_allow_html=True)
        
        # Authentication
        auths = metadata.get("authentication", [])
        auth_str = "".join([f"<span style='background: rgba(168, 85, 247, 0.08); border: 1px solid rgba(168, 85, 247, 0.2); border-radius: 4px; padding: 3px 8px; margin-right: 6px; margin-bottom: 6px; display: inline-block; font-size: 0.72rem; color: #c084fc; font-weight: 500;'>{a}</span>" for a in auths])
        st.markdown(f"<div style='margin-top: 15px;'><b>Authentication</b></div><div style='margin-top: 6px;'>{auth_str if auths and auths != ['Not Detected'] else '<span style=color:var(--text-muted)>None Detected</span>'}</div>", unsafe_allow_html=True)

    # Deployment & Payments
    st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
    c3, c4 = st.columns(2)
    with c3:
        # Deployment
        deploys = metadata.get("deployment", [])
        deploy_str = "".join([f"<span style='background: rgba(239, 68, 68, 0.08); border: 1px solid rgba(239, 68, 68, 0.2); border-radius: 4px; padding: 3px 8px; margin-right: 6px; margin-bottom: 6px; display: inline-block; font-size: 0.72rem; color: #f87171; font-weight: 500;'>{d}</span>" for d in deploys])
        st.markdown(f"<b>Deployment & Ops</b>\n<div style='margin-top: 6px;'>{deploy_str if deploys and deploys != ['Not Detected'] else '<span style=color:var(--text-muted)>None Detected</span>'}</div>", unsafe_allow_html=True)
        
    with c4:
        # Payments
        pays = metadata.get("payments", [])
        pay_str = "".join([f"<span style='background: rgba(245, 158, 11, 0.08); border: 1px solid rgba(245, 158, 11, 0.2); border-radius: 4px; padding: 3px 8px; margin-right: 6px; margin-bottom: 6px; display: inline-block; font-size: 0.72rem; color: #fbbf24; font-weight: 500;'>{p}</span>" for p in pays])
        st.markdown(f"<b>Payment Gateways</b>\n<div style='margin-top: 6px;'>{pay_str if pays and pays != ['Not Detected'] else '<span style=color:var(--text-muted)>None Detected</span>'}</div>", unsafe_allow_html=True)

    # Config files row
    st.markdown("<div style='margin-top: 20px;'><b>Configuration Files</b></div>", unsafe_allow_html=True)
    configs = metadata.get("config_files", [])
    if configs and configs != ["Not Detected"]:
        config_list = "".join([f"<span style='font-family: var(--font-mono); font-size: 0.74rem; background: rgba(255,255,255,0.02); border: 1px solid var(--border); border-radius: 4px; padding: 2px 6px; margin-right: 6px; margin-bottom: 6px; display: inline-block; color: var(--text-main);'>{c}</span>" for c in configs])
        st.markdown(f"<div style='margin-top: 6px;'>{config_list}</div>", unsafe_allow_html=True)
    else:
        st.markdown("<span style='color: var(--text-muted); font-size: 0.78rem;'>None Detected</span>", unsafe_allow_html=True)

    # Dependencies section
    deps = metadata.get("dependencies", [])
    if deps and deps != ["Not Detected"]:
        with st.expander("📦 View Dependencies List", expanded=False):
            # Format nicely as monospace code lines
            dep_text = "\n".join(deps)
            st.code(dep_text, language="text")

# =====================================================
# SESSION STATE
# =====================================================

if "ready" not in st.session_state:
    st.session_state.ready = False

if "repo_metadata" not in st.session_state:
    st.session_state.repo_metadata = None

if "messages" not in st.session_state:
    st.session_state.messages = []

if st.session_state.get("clear_chat_input_on_start"):
    st.session_state.chat_text_input = ""
    st.session_state.clear_chat_input_on_start = False

# =====================================================
# SIDEBAR
# =====================================================

with st.sidebar:
    st.markdown(
        """
        <h2 style="font-size: 1.1rem; margin-top: 10px; margin-bottom: 15px; color: var(--text-primary); display: flex; align-items: center; font-family: var(--font-sans); font-weight: 700;">
            <svg class="lucide-icon" viewBox="0 0 24 24"><path d="M4 20h16a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.93a2 2 0 0 1-1.66-.9l-.82-1.2A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2z"/></svg>
            Workspace Control
        </h2>
        """,
        unsafe_allow_html=True
    )

    st.markdown("<div class='control-panel-section-header'>[01] REPOSITORY INITIALIZATION</div>", unsafe_allow_html=True)
    
    repo_url = st.text_input(
        "GitHub Repository URL"
    )

    force_reindex = st.checkbox(
        "Force re-index (ignore cache)",
        value=False
    )

    st.markdown("<div class='control-panel-section-header'>[02] INFERENCE SETTINGS</div>", unsafe_allow_html=True)

    answer_mode = st.selectbox(
        "Answer detail",
        [
            "Balanced",
            "Fast",
            "Deep"
        ],
        index=0
    )

    analyze = st.button(
        "Analyze Repository 🚀",
        type="primary",
        use_container_width=True
    )

    cached_repos = cache_manager.list_cached_repos()

    if cached_repos:
        with st.expander(
            f"🗄️ Cached repos ({len(cached_repos)})"
        ):
            for entry in cached_repos[:10]:
                repo_name = entry['repo_url'].split('/')[-1].replace('.git', '')
                st.markdown(
                    f"""
                    <div style="background: var(--bg-panel-soft); border: 1px solid var(--border); border-radius: 6px; padding: 10px; margin-bottom: 8px;">
                        <div style="color: #ffffff; font-weight: 600; font-size: 0.76rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; margin-bottom: 2px; font-family: var(--font-sans);">
                            📦 {repo_name}
                        </div>
                        <div style="color: var(--text-muted); font-size: 0.68rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; margin-bottom: 6px; font-family: var(--font-mono);">
                            {entry['repo_url']}
                        </div>
                        <div style="display: flex; gap: 6px; flex-wrap: wrap;">
                            <span style="background: rgba(255, 255, 255, 0.04); color: var(--text-primary); border: 1px solid var(--border); border-radius: 4px; padding: 2px 6px; font-size: 0.62rem; font-family: var(--font-mono);">
                                {entry['chunk_count']} chunks
                            </span>
                            <span style="background: var(--accent-glow); color: var(--accent-blue); border: 1px solid var(--border-active); border-radius: 4px; padding: 2px 6px; font-size: 0.62rem; font-family: var(--font-mono);">
                                {entry['commit_hash'][:7]}
                            </span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

    # Show Repository Insights in sidebar if index is loaded and ready
    if st.session_state.get("ready"):
        st.sidebar.divider()
        if st.sidebar.button("🗑️ Clear Chat History", use_container_width=True):
            st.session_state.messages = []
            st.session_state.clicked_prompt = None
            st.sidebar.success("Chat history cleared!")
            st.rerun()
        
        import os
        all_files = st.session_state.get("all_files", [])
        if all_files:
            # Map extensions to languages and colors (matching GitHub palette)
            lang_colors = {
                "Python": "#3572A5",
                "JavaScript": "#f1e05a",
                "TypeScript": "#3178c6",
                "HTML": "#e34c26",
                "CSS": "#563d7c",
                "C++": "#f34b7d",
                "Java": "#b07219",
                "Go": "#00ADD8",
                "Rust": "#dea584",
                "Markdown": "#083fa1",
                "Text": "#8e8e93",
                "Config/Data": "#a2a2a6"
            }
            
            repo_metadata = st.session_state.get("repo_metadata") or {}
            langs_raw = repo_metadata.get("languages_raw")
            
            sorted_langs = []
            
            if langs_raw:
                # Use accurate byte-based percentages from RepositoryInspector
                sorted_langs = sorted(
                    [(lang, data["pct"]) for lang, data in langs_raw.items()],
                    key=lambda x: x[1],
                    reverse=True
                )
            else:
                # Fallback to file count mapping if inspector details are not cached
                langs = {}
                for f in all_files:
                    ext = os.path.splitext(f)[1].lower()
                    if ext in [".js", ".jsx"]:
                        langs["JavaScript"] = langs.get("JavaScript", 0) + 1
                    elif ext in [".ts", ".tsx"]:
                        langs["TypeScript"] = langs.get("TypeScript", 0) + 1
                    elif ext == ".py":
                        langs["Python"] = langs.get("Python", 0) + 1
                    elif ext in [".cpp", ".cc", ".cxx", ".h", ".hpp"]:
                        langs["C++"] = langs.get("C++", 0) + 1
                    elif ext == ".java":
                        langs["Java"] = langs.get("Java", 0) + 1
                    elif ext == ".go":
                        langs["Go"] = langs.get("Go", 0) + 1
                    elif ext == ".rs":
                        langs["Rust"] = langs.get("Rust", 0) + 1
                    elif ext == ".md":
                        langs["Markdown"] = langs.get("Markdown", 0) + 1
                    elif ext == ".txt":
                        langs["Text"] = langs.get("Text", 0) + 1
                    elif ext in [".json", ".yml", ".yaml", ".config", ".ini", ".toml"]:
                        langs["Config/Data"] = langs.get("Config/Data", 0) + 1
                    elif ext in [".html", ".htm"]:
                        langs["HTML"] = langs.get("HTML", 0) + 1
                    elif ext == ".css":
                        langs["CSS"] = langs.get("CSS", 0) + 1
                
                total_count = sum(langs.values())
                if total_count > 0:
                    sorted_langs = sorted(
                        [(lang, (count / total_count) * 100) for lang, count in langs.items()],
                        key=lambda x: x[1],
                        reverse=True
                    )
            
            if sorted_langs:
                st.markdown(
                    """<h2 style="font-size: 1.1rem; margin-top: 20px; margin-bottom: 5px; color: var(--text-primary); display: flex; align-items: center; font-family: var(--font-sans); font-weight: 700;">
<svg class="lucide-icon" viewBox="0 0 24 24"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>
Codebase Insights
</h2>""",
                    unsafe_allow_html=True
                )
                
                # HTML flex segments
                bar_html = "<div style='display: flex; height: 8px; border-radius: 4px; overflow: hidden; margin: 10px 0 14px 0; background: rgba(255,255,255,0.05);'>"
                legend_html = "<div style='display: grid; grid-template-columns: 1fr 1fr; gap: 8px 12px; margin-bottom: 5px;'>"
                
                for idx, (lang, pct) in enumerate(sorted_langs[:6]): # top 6
                    color = lang_colors.get(lang, "#8e8e93")
                    
                    bar_html += f"<div style='width: {pct}%; background: {color};'></div>"
                    
                    legend_html += (
                        f"<div style='display: flex; align-items: center; gap: 6px; font-size: 0.72rem; color: var(--text-muted); font-family: var(--font-sans);'>"
                        f"<span style='width: 6px; height: 6px; border-radius: 50%; background: {color}; display: inline-block;'></span>"
                        f"<strong style='color: #f5f5f7; font-weight: 500;'>{lang}</strong>"
                        f"<span>{pct:.1f}%</span>"
                        f"</div>"
                    )
                
                bar_html += "</div>"
                legend_html += "</div>"
                
                st.markdown(bar_html + legend_html, unsafe_allow_html=True)

    st.divider()

    st.markdown(
        """
        <h2 style="font-size: 1.1rem; margin-top: 15px; margin-bottom: 5px; color: var(--text-primary); display: flex; align-items: center; font-family: var(--font-sans); font-weight: 700;">
            <svg class="lucide-icon" viewBox="0 0 24 24"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>
            Engine Details
        </h2>
        <div class="system-status-readout">
            <div class="readout-header">HARDWARE & RETRIEVAL CONFIG</div>
            <div class="readout-grid">
                <div class="readout-item">
                    <span class="readout-key">EMBEDDING</span>
                    <span class="readout-val">nomic-embed</span>
                </div>
                <div class="readout-item">
                    <span class="readout-key">VECTOR_DB</span>
                    <span class="readout-val">FAISS_ID_MAP</span>
                </div>
                <div class="readout-item">
                    <span class="readout-key">RETRIEVER</span>
                    <span class="readout-val">Hybrid_RAG</span>
                </div>
                <div class="readout-item">
                    <span class="readout-key">RERANKER</span>
                    <span class="readout-val">MiniLM-L-6</span>
                </div>
                <div class="readout-item">
                    <span class="readout-key">LOCAL_LLM</span>
                    <span class="readout-val">Qwen2.5_Coder</span>
                </div>
                <div class="readout-item">
                    <span class="readout-key">RUNTIME</span>
                    <span class="readout-val">Ollama_Local</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )




# =====================================================
# ANALYZE REPOSITORY
# =====================================================


if analyze:

    if not repo_url.strip():

        st.sidebar.error(
            "Please enter a GitHub repository URL."
        )

        st.stop()


    with st.spinner(
        "🔍 Cloning Repository..."
    ):

        repo_path = clone_repository(
            repo_url
        )

        commit_hash = get_commit_hash(
            repo_path
        )


    use_cache = (
        not force_reindex
        and cache_manager.cache_exists(
            repo_url,
            commit_hash
        )
    )


    with st.spinner("🔍 Indexing Repository..."):
        from core.incremental_index import analyze_repo
        
        progress_bar = st.progress(0)
        def progress_cb(current, total):
            if total > 0:
                progress_bar.progress((current + 1) / total)
                
        store, chunks, status, all_files, repo_metadata = analyze_repo(
            repo_path=repo_path,
            repo_url=repo_url,
            commit_hash=commit_hash,
            force_reindex=force_reindex,
            progress_callback=progress_cb
        )
        st.session_state.all_files = all_files
        st.session_state.repo_metadata = repo_metadata
        
        progress_bar.progress(1.0)
        
        if status == "cache_hit":
            st.sidebar.success(
                f"⚡ Loaded from cache — skipped re-embedding "
                f"{len(chunks)} chunks (commit {commit_hash[:7]})"
            )
        elif status == "incremental_success":
            st.sidebar.success(
                f"✅ Incremental index update completed! "
                f"{len(chunks)} total chunks cached."
            )
        else:
            st.sidebar.success(
                f"✅ Full index build completed! "
                f"{len(chunks)} total chunks cached."
            )
            
        # Define variables expected by the report section
        files = list({chunk["file"] for chunk in chunks})
        embeddings = chunks


    with st.spinner(
        "⚡ Loading Retrieval Engine..."
    ):


        hybrid = HybridSearch(

            store,

            chunks

        )



        reranker = load_reranker()




    st.session_state.hybrid = hybrid

    st.session_state.reranker = reranker

    st.session_state.ready = True







    # ===============================
    # REPORT
    # ===============================


    st.success(

        "🟢 Repository Indexed Successfully"

    )




    st.subheader(

        "📊 Repository Analysis Report"

    )




    c1,c2,c3,c4 = st.columns(4)



    c1.metric(

        "📁 Files Indexed",

        len(files)

    )



    c2.metric(

        "🧩 Code Chunks",

        len(chunks)

    )



    c3.metric(

        "🧠 Embeddings",

        len(embeddings)

    )



    c4.metric(

        "🔎 Retrieval",

        "Hybrid"

    )



    st.markdown(
        """
        <h3 style="font-size: 0.9rem; font-weight: 600; margin-top: 30px; margin-bottom: 12px; color: var(--text-primary); font-family: var(--font-mono); letter-spacing: 0.05em;">[03] PIPELINE COMPILATION STAGES</h3>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 8px; margin-bottom: 20px;">
            <div style="background: var(--bg-panel); border: 1px solid var(--border); border-radius: 6px; padding: 10px 14px; display: flex; align-items: center; gap: 8px;">
                <span style="color: var(--success); font-family: var(--font-mono); font-size: 0.76rem; font-weight: bold;">[✓]</span>
                <span style="color: var(--text-primary); font-family: var(--font-mono); font-size: 0.74rem; font-weight: 500;">code_parsed</span>
            </div>
            <div style="background: var(--bg-panel); border: 1px solid var(--border); border-radius: 6px; padding: 10px 14px; display: flex; align-items: center; gap: 8px;">
                <span style="color: var(--success); font-family: var(--font-mono); font-size: 0.76rem; font-weight: bold;">[✓]</span>
                <span style="color: var(--text-primary); font-family: var(--font-mono); font-size: 0.74rem; font-weight: 500;">chunks_created</span>
            </div>
            <div style="background: var(--bg-panel); border: 1px solid var(--border); border-radius: 6px; padding: 10px 14px; display: flex; align-items: center; gap: 8px;">
                <span style="color: var(--success); font-family: var(--font-mono); font-size: 0.76rem; font-weight: bold;">[✓]</span>
                <span style="color: var(--text-primary); font-family: var(--font-mono); font-size: 0.74rem; font-weight: 500;">embeddings_ready</span>
            </div>
            <div style="background: var(--bg-panel); border: 1px solid var(--border); border-radius: 6px; padding: 10px 14px; display: flex; align-items: center; gap: 8px;">
                <span style="color: var(--success); font-family: var(--font-mono); font-size: 0.76rem; font-weight: bold;">[✓]</span>
                <span style="color: var(--text-primary); font-family: var(--font-mono); font-size: 0.74rem; font-weight: 500;">faiss_indexed</span>
            </div>
            <div style="background: var(--bg-panel); border: 1px solid var(--border); border-radius: 6px; padding: 10px 14px; display: flex; align-items: center; gap: 8px;">
                <span style="color: var(--success); font-family: var(--font-mono); font-size: 0.76rem; font-weight: bold;">[✓]</span>
                <span style="color: var(--text-primary); font-family: var(--font-mono); font-size: 0.74rem; font-weight: 500;">bm25_prepared</span>
            </div>
            <div style="background: var(--bg-panel); border: 1px solid var(--border); border-radius: 6px; padding: 10px 14px; display: flex; align-items: center; gap: 8px;">
                <span style="color: var(--success); font-family: var(--font-mono); font-size: 0.76rem; font-weight: bold;">[✓]</span>
                <span style="color: var(--text-primary); font-family: var(--font-mono); font-size: 0.74rem; font-weight: 500;">reranker_loaded</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )









# =====================================================
# CHAT SECTION
# =====================================================


st.divider()

if st.session_state.get("ready"):
    with st.expander("🔍 Repository Overview", expanded=False):
        render_repository_overview(st.session_state.get("repo_metadata"))

st.markdown(
    """
    <h1 style="font-size: 1.6rem; font-weight: 600; margin-top: 10px; margin-bottom: 12px; color: #ffffff; display: flex; align-items: center; font-family: var(--font-sans); letter-spacing: -0.015em;">
        <svg class="lucide-icon" style="width: 22px; height: 22px;" viewBox="0 0 24 24"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
        Chat With Repository
    </h1>
    """,
    unsafe_allow_html=True
)

# Handle Quick-Start Prompt selection
if "clicked_prompt" in st.session_state and st.session_state.clicked_prompt:
    question = st.session_state.clicked_prompt
    del st.session_state.clicked_prompt
else:
    question = None

st.markdown(
    """
    <div style="font-family: var(--font-mono); font-size: 0.68rem; color: var(--text-muted); margin-bottom: 8px; font-weight: 600; letter-spacing: 0.05em;">
        [04] QUICK START SUGGESTIONS
    </div>
    """,
    unsafe_allow_html=True
)
c_ex1, c_ex2, c_ex3, c_ex4 = st.columns(4)

ex1_val = "Explain repository structure"
ex2_val = "Trace the execution flow"
ex3_val = "Explain project architecture"
ex4_val = "Find important functions"

if c_ex1.button(ex1_val, key="ex_btn_1", use_container_width=True):
    st.session_state.clicked_prompt = ex1_val
    st.rerun()

if c_ex2.button(ex2_val, key="ex_btn_2", use_container_width=True):
    st.session_state.clicked_prompt = ex2_val
    st.rerun()

if c_ex3.button(ex3_val, key="ex_btn_3", use_container_width=True):
    st.session_state.clicked_prompt = ex3_val
    st.rerun()

if c_ex4.button(ex4_val, key="ex_btn_4", use_container_width=True):
    st.session_state.clicked_prompt = ex4_val
    st.rerun()

st.divider()

# Render completed questions as collapsible expanders (newest at the top)

completed_pairs = []
user_message = None
for msg in st.session_state.messages:
    if msg["role"] == "user":
        user_message = msg
    elif msg["role"] == "assistant" and user_message is not None:
        completed_pairs.append((user_message, msg))
        user_message = None

for q_msg, a_msg in reversed(completed_pairs):
    q_text = q_msg["content"]
    a_text = a_msg["content"]
    report = a_msg.get("retrieval_report")
    
    with st.expander(f"📄 {q_text}", expanded=False):
        st.markdown(f"**Original Question:**\n{q_text}")
        st.divider()
        st.markdown(f"**Answer:**\n{a_text}")
        
        if report:
            st.divider()
            st.markdown("### 📚 Retrieval Report")
            st.markdown(
                f"**Timing:** total `{report.get('total_seconds', 0.0):.1f}s` | "
                f"embedding `{report.get('embed_seconds', 0.0):.1f}s` | "
                f"retrieval `{report.get('retrieval_seconds', 0.0):.1f}s` | "
                f"rerank `{report.get('rerank_seconds', 0.0):.1f}s` | "
                f"generation `{report.get('generation_seconds', 0.0):.1f}s`"
            )
            
            sources = report.get("sources", [])
            if sources:
                st.markdown("**Retrieved Sources:**")
                for idx, s in enumerate(sources):
                    with st.expander(f"📄 Source #{idx+1}: {s['file'].split('/')[-1]} (Lines {s['start_line']}-{s['end_line']})"):
                        st.markdown(f"**Full Path:** `{s['file']}`")
                        st.code(s["code"], language="python" if s["file"].endswith(".py") else "text")

if not question:
    # Custom Chat Input Layout (Cursor/ChatGPT styled)
    col1, col2 = st.columns([12, 1])
    with col1:
        user_query = st.text_input(
            "Ask RepoMind...",
            placeholder="Ask RepoMind...",
            label_visibility="collapsed",
            key="chat_text_input"
        )
    with col2:
        st.button("➜", key="chat_send_button", use_container_width=True)

    # Parse submitted question from text input or send button click
    if user_query:
        question = user_query
    elif st.session_state.get("chat_send_button") and st.session_state.get("chat_text_input"):
        question = st.session_state.get("chat_text_input")

if question:

    if not st.session_state.ready:

        st.warning(

            "Analyze a repository first."

        )

    else:
        st.session_state.clear_chat_input_on_start = True



        st.session_state.messages.append(

            {

                "role":"user",

                "content":question

            }

        )



        st.components.v1.html(
            """
            <script>
            try {
                window.parent.document.title = '⏳ RepoMind • Thinking...';
            } catch(e) {
                console.log("Title set failed:", e);
            }
            </script>
            """,
            height=0,
            width=0
        )


        with st.chat_message(
            "user"
        ):


            st.write(
                question
            )


        # INTERCEPT METADATA QUERY
        from core.repository_inspector import parse_inspector_query, format_inspector_response
        inspect_cat = parse_inspector_query(question)
        if inspect_cat is not None:
            repo_metadata = st.session_state.get("repo_metadata", {})
            response = format_inspector_response(inspect_cat, repo_metadata)
            
            with st.chat_message("assistant"):
                st.markdown(response)
                
            st.session_state.messages.append({
                "role": "assistant",
                "content": response
            })
            st.session_state.notification_state = "ready"
            st.rerun()

        # INTERCEPT STRUCTURE QUERY
        from core.repository_explorer import parse_structure_query, format_structure_response
        query_info = parse_structure_query(question)
        if query_info is not None:
            all_files = st.session_state.get("all_files", [])
            response = format_structure_response(query_info, all_files)
            
            with st.chat_message("assistant"):
                st.markdown(response)
                
            st.session_state.messages.append({
                "role": "assistant",
                "content": response
            })
            st.session_state.notification_state = "ready"
            st.rerun()







        with st.spinner(

            "🤖 Analyzing repository..."

        ):




            total_start = time.perf_counter()

            embed_start = time.perf_counter()

            query_embedding = generate_embedding(

                question

            )

            embed_seconds = time.perf_counter() - embed_start







            # =====================================
            # ADAPTIVE CONTEXT SELECTION
            # =====================================

            large_context_keywords = [

                "flow",

                "architecture",

                "system",

                "process",

                "working",

                "explain",

                "complete",

                "overview",

                "structure",

                "how"

            ]



            if any(

                word in question.lower()

                for word in large_context_keywords

            ):


                if answer_mode == "Deep":

                    retrieval_k = 30

                    rerank_k = 12


                elif answer_mode == "Fast":

                    retrieval_k = 8

                    rerank_k = 3


                else:

                    retrieval_k = 24

                    rerank_k = 8



            else:


                if answer_mode == "Deep":

                    retrieval_k = 20

                    rerank_k = 8


                elif answer_mode == "Fast":

                    retrieval_k = 6

                    rerank_k = 3


                else:

                    retrieval_k = 16

                    rerank_k = 5


            # =====================================
            # HYBRID RETRIEVAL
            # =====================================

            retrieval_start = time.perf_counter()

            retrieved = st.session_state.hybrid.search(

                question,

                query_embedding,

                top_k=retrieval_k

            )

            retrieval_seconds = time.perf_counter() - retrieval_start



            # =====================================
            # CROSS ENCODER RERANKING
            # =====================================

            rerank_start = time.perf_counter()

            results = st.session_state.reranker.rerank(

                question,

                retrieved,

                top_k=rerank_k

            )

            rerank_seconds = time.perf_counter() - rerank_start







            generation_start = time.perf_counter()

            answer = generate_answer(

                question,

                results,

                answer_mode

            )

            generation_seconds = time.perf_counter() - generation_start

            total_seconds = time.perf_counter() - total_start








        with st.chat_message(
            "assistant"
        ):



            st.markdown(

                answer

            )







            with st.expander(

                f"📚 Retrieval Report ({len(results)} chunks used)"

            ):



                st.markdown(

                    f"""

**Mode:** `{answer_mode}`

**Timing:** total `{total_seconds:.1f}s` | embedding `{embed_seconds:.1f}s` | retrieval `{retrieval_seconds:.1f}s` | rerank `{rerank_seconds:.1f}s` | generation `{generation_seconds:.1f}s`

"""

                )



                st.divider()




                for idx, r in enumerate(results):
                    with st.expander(f"📄 Source #{idx+1}: {r['file'].split('/')[-1]} (Lines {r['start_line']}-{r['end_line']})"):
                        st.markdown(f"**Full Path:** `{r['file']}`")
                        st.code(r['code'], language="python" if r['file'].endswith('.py') else "text")







        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": answer,
                "retrieval_report": {
                    "total_seconds": total_seconds,
                    "embed_seconds": embed_seconds,
                    "retrieval_seconds": retrieval_seconds,
                    "rerank_seconds": rerank_seconds,
                    "generation_seconds": generation_seconds,
                    "sources": [
                        {
                            "file": r["file"],
                            "start_line": r["start_line"],
                            "end_line": r["end_line"],
                            "code": r["code"]
                        }
                        for r in results
                    ]
                }
            }
        )
        st.session_state.notification_state = "ready"
        st.rerun()
