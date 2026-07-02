import streamlit as st
from ui.overview import render_repository_overview

def render_chat_section():
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

    return question
