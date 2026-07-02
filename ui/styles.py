import streamlit as st

def inject_notification_system():
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

def trigger_ready_notification():
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

def inject_custom_css():
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

def render_header():
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

def render_architecture_section():
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
