import streamlit as st

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

def render_pipeline_report(files, chunks, embeddings):
    st.success(
        "🟢 Repository Indexed Successfully"
    )

    st.subheader(
        "📊 Repository Analysis Report"
    )

    c1, c2, c3, c4 = st.columns(4)

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

