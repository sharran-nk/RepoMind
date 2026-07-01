import os
import re
import hashlib


# Folders to ignore completely when scanning the repository
IGNORED_FOLDERS = {
    ".git",
    "node_modules",
    "venv",
    "__pycache__",
    ".next",
    "dist",
    "build",
    ".cache"
}

# Mapping of file extensions to their user-friendly language names
EXT_TO_LANG_NAME = {
    ".py": "Python",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".jsx": "React (JSX)",
    ".tsx": "React (TSX)",
    ".java": "Java",
    ".cpp": "C++",
    ".cs": "C#",
    ".go": "Go",
    ".rs": "Rust",
    ".kt": "Kotlin",
    ".swift": "Swift",
    ".html": "HTML",
    ".css": "CSS",
    ".json": "JSON",
    ".yml": "YAML",
    ".yaml": "YAML",
    ".txt": "Text",
    ".md": "Markdown"
}

# List of standard config filenames to look out for
CONFIG_FILENAMES = [
    "package.json",
    "requirements.txt",
    "pyproject.toml",
    "Dockerfile",
    "docker-compose.yml",
    "vite.config.js",
    "webpack.config.js",
    "tsconfig.json",
    "eslint.config.js",
    ".env",
    ".env.example"
]


def scan_repository_files(repo_path: str) -> list:
    """
    Recursively walk the repo directory and collect relative Unix-style file paths,
    completely ignoring defined ignore folders.
    """
    all_files = []
    abs_repo = os.path.abspath(repo_path)
    
    for root, dirs, files in os.walk(abs_repo):
        # Modify dirs in-place to avoid entering ignored folders
        dirs[:] = [d for d in dirs if d not in IGNORED_FOLDERS]
        
        for file in files:
            full_path = os.path.join(root, file)
            # Compute relative path and normalize separator to Unix-style (/)
            rel_path = os.path.relpath(full_path, abs_repo)
            all_files.append(rel_path.replace("\\", "/"))
            
    return sorted(all_files)


def parse_structure_query(query: str) -> dict:
    """
    Parses a user query to see if it is purely a repository structure query.
    If the query asks to explain, describe, understand, or analyze code/flow,
    this function returns None so the hybrid RAG pipeline takes over.
    
    Returns a dict with query details, or None if not a strict structure query.
    """
    query_clean = query.strip().lower()
    
    # Check if the query is a simple "what is/are [target] file(s)" query (e.g. "what are txt files?")
    # If so, we bypass the mixed-query keywords check to allow structure listing.
    is_simple_what = bool(re.match(r"^what\s+(is|are)\s+(the\s+)?([a-zA-Z0-9_\-\.\+]+)\s+files?\??$", query_clean))
    
    # Critical mixed-query keywords. If any of these are present, bypass structure queries.
    mixed_keywords = [
        "explain", "describe", "understand", "how does", "how do", "why",
        "what does", "working", "flow", "architecture", "process",
        "functionality", "logic", "implement", "code", "use", "using", "run", "do",
        "about", "format", "tell", "what is", "what are"
    ]
    
    if not is_simple_what:
        for kw in mixed_keywords:
            # Check if the keyword exists as a word in the query
            if re.search(r"\b" + re.escape(kw) + r"\b", query_clean):
                return None

    # README query check
    if "readme" in query_clean:
        return {"type": "readme", "value": "readme"}

    # All Configuration files query check
    config_phrases = ["list config", "show config", "all config", "configuration files", "config files"]
    if any(phrase in query_clean for phrase in config_phrases):
        return {"type": "config", "value": "config"}

    # Specific Configuration filenames check (exact case-insensitive match)
    for fname in CONFIG_FILENAMES:
        if re.search(r"\b" + re.escape(fname.lower()) + r"\b", query_clean):
            return {"type": "filename", "value": fname}

    # Extension queries check (.txt, .md, .py, etc.)
    extensions = [
        ".txt", ".md", ".py", ".js", ".ts", ".jsx", ".tsx", ".java",
        ".cpp", ".cs", ".go", ".rs", ".kt", ".swift", ".html", ".css",
        ".json", ".yml", ".yaml"
    ]
    for ext in extensions:
        if ext in query_clean:
            return {"type": "extension", "value": ext}

    # Check word alternatives for markdown files
    if re.search(r"\bmarkdown\b", query_clean) or re.search(r"\bmd\b", query_clean):
        return {"type": "extension", "value": ".md"}

    # Check word alternatives for text files
    if re.search(r"\btext\b", query_clean) or re.search(r"\btxt\b", query_clean):
        return {"type": "extension", "value": ".txt"}

    # Language queries mapping (match as word boundaries to prevent matching subsets like "go" inside "good")
    lang_map = {
        "python": ".py",
        "javascript": ".js",
        "typescript": ".ts",
        "java": ".java",
        "c++": ".cpp",
        "cpp": ".cpp",
        "c#": ".cs",
        "csharp": ".cs",
        "golang": ".go",
        "go": ".go",
        "rust": ".rs",
        "kotlin": ".kt",
        "swift": ".swift"
    }
    for lang, ext in lang_map.items():
        if re.search(r"\b" + re.escape(lang) + r"\b", query_clean):
            return {"type": "language", "value": ext}

    return None


def format_structure_response(query_info: dict, all_files: list) -> str:
    """
    Filters repository files based on query type and formats them into
    clean markdown output. Returns 'No matching files found.' if no matches.
    """
    if not all_files:
        return "No matching files found."

    q_type = query_info.get("type")
    val = query_info.get("value")
    
    matched = []
    
    if q_type in ("extension", "language"):
        # Match files ending with target extension (case-insensitive)
        matched = [f for f in all_files if f.lower().endswith(val.lower())]
        if not matched:
            return "No matching files found."
            
        label = EXT_TO_LANG_NAME.get(val, val.upper())
        lines = [f"## {label} Files"]
        for f in matched:
            lines.append(f"• {f}")
        return "\n".join(lines)
        
    elif q_type == "filename":
        # Match files whose basename exactly equals the target filename (case-insensitive)
        matched = [f for f in all_files if os.path.basename(f).lower() == val.lower()]
        if not matched:
            return "No matching files found."
            
        if len(matched) == 1:
            return f"## {val}\n**Path:** {matched[0]}"
        else:
            lines = [f"## {val}", "**Paths:**"]
            for f in matched:
                lines.append(f"• {f}")
            return "\n".join(lines)
            
    elif q_type == "readme":
        # Match files whose basename starts with "readme" (case-insensitive)
        matched = [f for f in all_files if os.path.basename(f).lower().startswith("readme")]
        if not matched:
            return "No matching files found."
            
        lines = [f"## README Files"]
        for f in matched:
            lines.append(f"• {f}")
        return "\n".join(lines)
        
    elif q_type == "config":
        # Match files whose basename is in the predefined CONFIG_FILENAMES list
        matched = [f for f in all_files if os.path.basename(f).lower() in [c.lower() for c in CONFIG_FILENAMES]]
        if not matched:
            return "No matching files found."
            
        lines = [f"## Configuration Files"]
        for f in matched:
            lines.append(f"• {f}")
        return "\n".join(lines)

    return "No matching files found."
