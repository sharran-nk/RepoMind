import os
import re
import json
import time

import faiss


# ==========================================
# CACHE LAYOUT
#
# cache/<safe_repo_name>__<short_commit_hash>/
#       index.faiss   -> raw FAISS index (vectors)
#       chunks.json   -> chunk metadata + source code text
#       meta.json     -> repo_url, commit_hash, chunk count, timestamp
# ==========================================

CACHE_DIR = "cache"


def _safe_name(repo_url):
    """
    Turn a repo URL into a filesystem-safe folder name.
    """

    name = repo_url.strip().rstrip("/")

    name = re.sub(r"https?://", "", name)

    name = re.sub(r"[^a-zA-Z0-9_.-]", "_", name)

    return name


def get_cache_dir(repo_url, commit_hash):
    """
    Resolve the cache folder for a given repo + commit.
    """

    safe_repo = _safe_name(repo_url)

    short_hash = commit_hash[:10]

    folder_name = f"{safe_repo}__{short_hash}"

    return os.path.join(CACHE_DIR, folder_name)


def cache_exists(repo_url, commit_hash):
    """
    Check whether a valid cache already exists for this repo + commit.
    """

    folder = get_cache_dir(repo_url, commit_hash)

    index_path = os.path.join(folder, "index.faiss")
    chunks_path = os.path.join(folder, "chunks.json")
    meta_path = os.path.join(folder, "meta.json")

    return (
        os.path.exists(index_path)
        and os.path.exists(chunks_path)
        and os.path.exists(meta_path)
    )


def save_cache(repo_url, commit_hash, index, chunks, manifest=None, metadata_store=None, all_files=None, repo_metadata=None):
    """
    Persist the FAISS index + chunk metadata (+ optional manifest, metadata_store, & repo_metadata) to disk.
    """

    folder = get_cache_dir(repo_url, commit_hash)

    os.makedirs(folder, exist_ok=True)

    index_path = os.path.join(folder, "index.faiss")
    chunks_path = os.path.join(folder, "chunks.json")
    meta_path = os.path.join(folder, "meta.json")

    faiss.write_index(index, index_path)

    with open(chunks_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f)

    # Save manifest and metadata_store
    if manifest is not None:
        manifest_path = os.path.join(folder, "manifest.json")
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f)

    if metadata_store is not None:
        metadata_store_path = os.path.join(folder, "metadata_store.json")
        with open(metadata_store_path, "w", encoding="utf-8") as f:
            json.dump(metadata_store, f)

    meta = {
        "repo_url": repo_url,
        "commit_hash": commit_hash,
        "chunk_count": len(chunks),
        "cached_at": time.time(),
    }
    if all_files is not None:
        meta["all_files"] = all_files
    if repo_metadata is not None:
        meta["repo_metadata"] = repo_metadata

    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f)

    return folder


def load_cache(repo_url, commit_hash):
    """
    Load a previously cached FAISS index + chunk metadata.

    Returns (index, chunks, meta) or raises if the cache is missing/corrupt.
    """

    folder = get_cache_dir(repo_url, commit_hash)

    index_path = os.path.join(folder, "index.faiss")
    chunks_path = os.path.join(folder, "chunks.json")
    meta_path = os.path.join(folder, "meta.json")

    index = faiss.read_index(index_path)

    with open(chunks_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    return index, chunks, meta


def load_cache_extended(repo_url, commit_hash, repo_path=None):
    """
    Load a previously cached FAISS index, chunk metadata, manifest, and metadata store.
    """
    folder = get_cache_dir(repo_url, commit_hash)

    index_path = os.path.join(folder, "index.faiss")
    chunks_path = os.path.join(folder, "chunks.json")
    meta_path = os.path.join(folder, "meta.json")
    manifest_path = os.path.join(folder, "manifest.json")
    metadata_store_path = os.path.join(folder, "metadata_store.json")

    index = faiss.read_index(index_path)

    with open(chunks_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    manifest = None
    if os.path.exists(manifest_path):
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

    metadata_store = None
    if os.path.exists(metadata_store_path):
        with open(metadata_store_path, "r", encoding="utf-8") as f:
            metadata_store = json.load(f)

    # Legacy cache fallback for all_files list
    if "all_files" not in meta:
        if not repo_path:
            repo_name = repo_url.split("/")[-1].replace(".git", "")
            repo_path = os.path.join("temp_repos", repo_name)
            
        if os.path.exists(repo_path):
            from core.repository_explorer import scan_repository_files
            meta["all_files"] = scan_repository_files(repo_path)
        else:
            meta["all_files"] = []

    return index, chunks, meta, manifest, metadata_store


def find_latest_cache(repo_url):
    """
    Find the most recent cache entry for the repository URL.
    Returns (commit_hash, folder_path) or (None, None).
    """
    if not os.path.exists(CACHE_DIR):
        return None, None

    safe_repo = _safe_name(repo_url)
    prefix = f"{safe_repo}__"

    latest_commit = None
    latest_time = -1
    latest_folder = None

    for folder_name in os.listdir(CACHE_DIR):
        if not folder_name.startswith(prefix):
            continue

        folder_path = os.path.join(CACHE_DIR, folder_name)
        meta_path = os.path.join(folder_path, "meta.json")
        if not os.path.exists(meta_path):
            continue

        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
            cached_at = meta.get("cached_at", 0)
            if cached_at > latest_time:
                latest_time = cached_at
                latest_commit = meta.get("commit_hash")
                latest_folder = folder_path
        except Exception:
            continue

    return latest_commit, latest_folder


def list_cached_repos():
    """
    List all cached repo/commit combinations, most recent first.
    Useful for a "recently analyzed" picker in the UI.
    """

    if not os.path.exists(CACHE_DIR):
        return []

    entries = []

    for folder_name in os.listdir(CACHE_DIR):

        meta_path = os.path.join(CACHE_DIR, folder_name, "meta.json")

        if not os.path.exists(meta_path):
            continue

        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)

            entries.append(meta)

        except Exception:
            continue

    entries.sort(key=lambda m: m.get("cached_at", 0), reverse=True)

    return entries


def clear_cache(repo_url=None, commit_hash=None):
    """
    Clear cache. If repo_url + commit_hash are given, clears just that
    entry. Otherwise clears the entire cache directory.
    """

    import shutil

    if repo_url and commit_hash:
        folder = get_cache_dir(repo_url, commit_hash)
        if os.path.exists(folder):
            shutil.rmtree(folder)
    else:
        if os.path.exists(CACHE_DIR):
            shutil.rmtree(CACHE_DIR)
