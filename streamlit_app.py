import streamlit as st
import time

from core.repo_loader import (
    clone_repository,
    get_commit_hash
)

from core import cache_manager

from retrieval.embeddings import (
    generate_embedding
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

from ui.styles import (
    inject_custom_css,
    inject_notification_system,
    trigger_ready_notification,
    render_header,
    render_architecture_section
)

from ui.sidebar import render_sidebar
from ui.chat import render_chat_section
from ui.overview import render_pipeline_report


# =====================================================
# CACHED RESOURCES
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

# Inject custom styling and notification system
inject_notification_system()

if "notification_state" not in st.session_state:
    st.session_state.notification_state = "idle"

if st.session_state.notification_state == "ready":
    trigger_ready_notification()
    st.session_state.notification_state = "idle"

inject_custom_css()

# =====================================================
# HEADER & ARCHITECTURE
# =====================================================

render_header()
render_architecture_section()


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

repo_url, force_reindex, answer_mode, analyze = render_sidebar()


# =====================================================
# ANALYZE REPOSITORY
# =====================================================

if analyze:
    if not repo_url.strip():
        st.sidebar.error("Please enter a GitHub repository URL.")
        st.stop()

    with st.spinner("🔍 Cloning Repository..."):
        repo_path = clone_repository(repo_url)
        commit_hash = get_commit_hash(repo_path)

    use_cache = (
        not force_reindex
        and cache_manager.cache_exists(repo_url, commit_hash)
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

    with st.spinner("⚡ Loading Retrieval Engine..."):
        hybrid = HybridSearch(store, chunks)
        reranker = load_reranker()

    st.session_state.hybrid = hybrid
    st.session_state.reranker = reranker
    st.session_state.ready = True

    # Render Report
    render_pipeline_report(files, chunks, embeddings)


# =====================================================
# CHAT SECTION
# =====================================================

question = render_chat_section()

if question:
    if not st.session_state.ready:
        st.warning("Analyze a repository first.")
    else:
        st.session_state.clear_chat_input_on_start = True
        st.session_state.messages.append(
            {
                "role": "user",
                "content": question
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

        with st.chat_message("user"):
            st.write(question)

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

        # RUN CHAT PIPELINE
        with st.spinner("🤖 Analyzing repository..."):
            total_start = time.perf_counter()
            embed_start = time.perf_counter()
            query_embedding = generate_embedding(question)
            embed_seconds = time.perf_counter() - embed_start

            # =====================================
            # ADAPTIVE CONTEXT SELECTION
            # =====================================
            large_context_keywords = [
                "flow", "architecture", "system", "process", 
                "working", "explain", "complete", "overview", 
                "structure", "how"
            ]

            if any(word in question.lower() for word in large_context_keywords):
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

            # =====================================
            # GENERATION
            # =====================================
            generation_start = time.perf_counter()
            answer = generate_answer(
                question,
                results,
                answer_mode
            )
            generation_seconds = time.perf_counter() - generation_start
            total_seconds = time.perf_counter() - total_start

        with st.chat_message("assistant"):
            st.markdown(answer)

            with st.expander(f"📚 Retrieval Report ({len(results)} chunks used)"):
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
