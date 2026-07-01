import os
import hashlib
import json
import time
from filelock import FileLock
from core.repo_loader import get_python_files
from core.parser import parse_python_file
from retrieval.embeddings import generate_embedding
from retrieval.vector_store import VectorStore
from core import cache_manager
from core.repository_explorer import scan_repository_files


def get_repo_relative_path(file_path: str, repo_path: str) -> str:
    """
    Get the relative path of a file with respect to the repository root.
    Normalized with forward slashes for OS independence.
    """
    abs_file = os.path.abspath(file_path)
    abs_repo = os.path.abspath(repo_path)
    rel = os.path.relpath(abs_file, abs_repo)
    return rel.replace("\\", "/")


def calculate_md5(file_path: str) -> str:
    """
    Calculate MD5 hash of a file to check for modifications.
    """
    hasher = hashlib.md5()
    with open(file_path, "rb") as f:
        buf = f.read(65536)
        while len(buf) > 0:
            hasher.update(buf)
            buf = f.read(65536)
    return hasher.hexdigest()


def get_vector_id(file_path: str, chunk_index: int) -> int:
    """
    Generate a deterministic vector ID (int64 compatible) based on relative file path and chunk index.
    """
    normalized_path = file_path.replace("\\", "/")
    key = f"{normalized_path}:{chunk_index}"
    return int(hashlib.md5(key.encode()).hexdigest()[:8], 16)


def analyze_repo(repo_path: str, repo_url: str, commit_hash: str, force_reindex: bool = False, progress_callback=None):
    """
    Performs repository analysis with incremental indexing.
    
    1. Tracks file MD5 hashes in manifest.json.
    2. Compares hashes to detect CHANGED, NEW, and DELETED files.
    3. Selectively generates embeddings for CHANGED and NEW files.
    4. Removes old vectors of CHANGED/DELETED files and inserts new ones into FAISS.
    5. Saves updated index, chunks list, manifest, and metadata store.
    
    Returns (store, chunks, status, all_files, repo_metadata) where status is "incremental_success", "full_success", or "cache_hit".
    """
    # Simple file lock to prevent concurrent writing of manifest/index
    os.makedirs(cache_manager.CACHE_DIR, exist_ok=True)
    lock_path = os.path.join(cache_manager.CACHE_DIR, "indexing.lock")
    lock = FileLock(lock_path)
    
    with lock:
        # Check if cache exists for this exact commit and we are not forcing re-index
        if not force_reindex and cache_manager.cache_exists(repo_url, commit_hash):
            print(f"Cache hit for commit {commit_hash[:7]}. Loading index...")
            index, chunks, meta, manifest, metadata_store = cache_manager.load_cache_extended(repo_url, commit_hash)
            store = VectorStore.from_index(index, chunks)
            all_files = meta.get("all_files")
            if not all_files:
                if os.path.exists(repo_path):
                    all_files = scan_repository_files(repo_path)
                else:
                    all_files = []
            
            repo_metadata = meta.get("repo_metadata")
            if not repo_metadata and os.path.exists(repo_path):
                from core.repository_inspector import RepositoryInspector
                inspector = RepositoryInspector(repo_path)
                repo_metadata = inspector.inspect(all_files, len(chunks))
            elif not repo_metadata:
                repo_metadata = {}
                
            return store, chunks, "cache_hit", all_files, repo_metadata
        
        # Check if there is any previous commit cache for this repository url
        prev_commit, prev_folder = None, None
        if not force_reindex:
            prev_commit, prev_folder = cache_manager.find_latest_cache(repo_url)
        
        if prev_commit and prev_folder:
            print(f"Found existing cache from commit {prev_commit[:7]}. Starting incremental indexing...")
            index, old_chunks, old_meta, old_manifest, old_metadata_store = cache_manager.load_cache_extended(repo_url, prev_commit)
            store = VectorStore.from_index(index, old_chunks)
            manifest = old_manifest or {}
            metadata_store = old_metadata_store or {}
            is_incremental = True
        else:
            print("No previous cache found (or forced re-index). Building full index...")
            store = VectorStore()
            old_chunks = []
            manifest = {}
            metadata_store = {}
            is_incremental = False
            
        # Get all programming files in the current workspace
        all_files = scan_repository_files(repo_path)
        code_files = get_python_files(repo_path)
        
        # Calculate current hashes and build relative path mapping
        current_manifest = {}
        file_path_map = {}
        for file_info in code_files:
            full_path = file_info["file_path"]
            rel_path = get_repo_relative_path(full_path, repo_path)
            current_manifest[rel_path] = calculate_md5(full_path)
            file_path_map[rel_path] = full_path
            
        # Diff Detection
        changed_files = []
        new_files = []
        deleted_files = []
        unchanged_files = []
        
        # Detect Changed, Unchanged, Deleted
        for rel_path, old_hash in manifest.items():
            if rel_path not in current_manifest:
                deleted_files.append(rel_path)
            else:
                new_hash = current_manifest[rel_path]
                if new_hash != old_hash:
                    changed_files.append(rel_path)
                else:
                    unchanged_files.append(rel_path)
                    
        # Detect New
        for rel_path in current_manifest:
            if rel_path not in manifest:
                new_files.append(rel_path)
                
        print(f"Incremental Indexing Summary:")
        print(f"{len(unchanged_files)} files skipped, {len(changed_files) + len(new_files)} files re-embedded, {len(deleted_files)} files removed")
        
        # Step 3 & 4: Partial FAISS Update and Metadata Cleanup
        # Identify vector IDs of changed or deleted files
        vector_ids_to_delete = []
        keys_to_remove_from_store = []
        
        for v_id_str, val in list(metadata_store.items()):
            vec_id = int(v_id_str)
            file_rel = val["file_path"]
            if file_rel in changed_files or file_rel in deleted_files:
                vector_ids_to_delete.append(vec_id)
                keys_to_remove_from_store.append(v_id_str)
                
        # Remove old vectors from the index and update metadata store
        if vector_ids_to_delete:
            print(f"Removing {len(vector_ids_to_delete)} old vectors from the index...")
            store.remove_vectors(vector_ids_to_delete)
            for k in keys_to_remove_from_store:
                metadata_store.pop(k)
                
        # Embed changed and new files
        files_to_embed = changed_files + new_files
        new_chunks = []
        
        for rel_path in files_to_embed:
            full_path = file_path_map[rel_path]
            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                code = f.read()
            file_data = {
                "file_path": rel_path,  # Use relative path inside chunk so it is cache portable
                "code": code
            }
            parsed = parse_python_file(file_data)
            new_chunks.extend(parsed)
            
        new_embeddings = []
        for i, chunk in enumerate(new_chunks):
            if progress_callback:
                progress_callback(i, len(new_chunks))
            
            emb = generate_embedding(chunk["code"])
            new_embeddings.append(emb)
            
            # Record vector ID in metadata store
            v_id = get_vector_id(chunk["file"], chunk["chunk_index"])
            metadata_store[str(v_id)] = {
                "file_path": chunk["file"],
                "chunk_index": chunk["chunk_index"]
            }
            
        # Add the new vectors and chunks to VectorStore
        if new_embeddings:
            print(f"Adding {len(new_embeddings)} new/updated vectors to the index...")
            store.add_vectors(new_embeddings, new_chunks)
            
        # Run repository inspector
        from core.repository_inspector import RepositoryInspector
        inspector = RepositoryInspector(repo_path)
        repo_metadata = inspector.inspect(all_files, len(store.chunks))
        
        # Save manifest + metadata_store + index (save manifest + metadata_store AFTER index)
        # Note: cache_manager.save_cache writes the index first, then chunks, and then manifest/metadata_store.
        cache_manager.save_cache(
            repo_url=repo_url,
            commit_hash=commit_hash,
            index=store.index,
            chunks=store.chunks,
            manifest=current_manifest,
            metadata_store=metadata_store,
            all_files=all_files,
            repo_metadata=repo_metadata
        )
        
        status = "incremental_success" if is_incremental else "full_success"
        return store, store.chunks, status, all_files, repo_metadata
