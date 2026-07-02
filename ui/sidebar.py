import streamlit as st
import os
from core import cache_manager

def render_sidebar():
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
    return repo_url, force_reindex, answer_mode, analyze
