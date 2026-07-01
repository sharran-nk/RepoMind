import os
import re
import json

class RepositoryInspector:
    def __init__(self, repo_path: str):
        self.repo_path = os.path.abspath(repo_path)
        self.all_files = []
        self.metadata = {
            "languages": [],
            "frameworks": [],
            "dependencies": [],
            "database": [],
            "authentication": [],
            "payments": [],
            "deployment": [],
            "config_files": [],
            "statistics": {}
        }

    def inspect(self, all_files: list, chunk_count: int = 0) -> dict:
        """
        Scans all files and key configuration files to extract metadata.
        """
        self.all_files = all_files
        
        # 1. Programming Languages
        self._extract_languages()
        
        # 2. Config Files list
        self._extract_config_files()
        
        # 3. Read config contents to detect frameworks, databases, auth, payments, deployment, dependencies
        self._detect_tech_details()
        
        # 4. Statistics
        self._calculate_statistics(chunk_count)
        
        # Clean empty lists with "Not Detected"
        for key in ["languages", "frameworks", "dependencies", "database", "authentication", "payments", "deployment", "config_files"]:
            if not self.metadata[key]:
                self.metadata[key] = ["Not Detected"]
                
        return self.metadata

    def _extract_languages(self):
        ext_map = {
            ".py": "Python",
            ".js": "JavaScript",
            ".jsx": "JavaScript",
            ".ts": "TypeScript",
            ".tsx": "TypeScript",
            ".java": "Java",
            ".cpp": "C++",
            ".cc": "C++",
            ".cxx": "C++",
            ".h": "C/C++ Header",
            ".hpp": "C++ Header",
            ".cs": "C#",
            ".go": "Go",
            ".rs": "Rust",
            ".kt": "Kotlin",
            ".swift": "Swift",
            ".php": "PHP",
            ".html": "HTML",
            ".css": "CSS",
            ".rb": "Ruby",
            ".sh": "Shell"
        }
        
        file_counts = {}
        byte_sizes = {}
        total_bytes = 0
        
        for f in self.all_files:
            ext = os.path.splitext(f)[1].lower()
            if ext in ext_map:
                lang = ext_map[ext]
                full_path = os.path.join(self.repo_path, f)
                try:
                    size = os.path.getsize(full_path)
                except:
                    size = 0
                file_counts[lang] = file_counts.get(lang, 0) + 1
                byte_sizes[lang] = byte_sizes.get(lang, 0) + size
                total_bytes += size
                
        if total_bytes > 0:
            sorted_langs = sorted(byte_sizes.items(), key=lambda x: x[1], reverse=True)
            self.metadata["languages"] = [
                f"{lang} ({file_counts[lang]} file, {(size_bytes/total_bytes)*100:.1f}%)" if file_counts[lang] == 1 else f"{lang} ({file_counts[lang]} files, {(size_bytes/total_bytes)*100:.1f}%)"
                for lang, size_bytes in sorted_langs
            ]
            self.metadata["languages_raw"] = {
                lang: {
                    "count": file_counts[lang],
                    "bytes": size_bytes,
                    "pct": (size_bytes / total_bytes) * 100
                }
                for lang, size_bytes in sorted_langs
            }

    def _extract_config_files(self):
        target_configs = {
            "package.json",
            "readme.md",
            "readme",
            "license",
            "license.txt",
            "license.md",
            "dockerfile",
            "docker-compose.yml",
            "docker-compose.yaml",
            "vite.config.js",
            "vite.config.ts",
            "webpack.config.js",
            "eslint.config.js",
            "tsconfig.json",
            ".env",
            ".env.example",
            "requirements.txt",
            "pyproject.toml",
            "pom.xml",
            "cargo.toml",
            "go.mod",
            ".gitignore"
        }
        
        matched_configs = []
        for f in self.all_files:
            basename = os.path.basename(f).lower()
            if basename in target_configs:
                matched_configs.append(f)
        self.metadata["config_files"] = sorted(matched_configs)

    def _detect_tech_details(self):
        # We will scan for ALL config files in the workspace (supporting monorepos)
        package_json_paths = self._find_all_files_on_disk("package.json")
        requirements_txt_paths = self._find_all_files_on_disk("requirements.txt")
        pyproject_toml_paths = self._find_all_files_on_disk("pyproject.toml")
        go_mod_paths = self._find_all_files_on_disk("go.mod")
        cargo_toml_paths = self._find_all_files_on_disk("Cargo.toml")
        pom_xml_paths = self._find_all_files_on_disk("pom.xml")
        
        package_contents = []
        requirements_contents = []
        pyproject_contents = []
        go_mod_contents = []
        cargo_toml_contents = []
        pom_xml_contents = []
        
        for p in package_json_paths:
            try:
                with open(p, "r", encoding="utf-8", errors="ignore") as f:
                    package_contents.append(f.read())
            except:
                pass
                
        for p in requirements_txt_paths:
            try:
                with open(p, "r", encoding="utf-8", errors="ignore") as f:
                    requirements_contents.append(f.read().lower())
            except:
                pass

        for p in pyproject_toml_paths:
            try:
                with open(p, "r", encoding="utf-8", errors="ignore") as f:
                    pyproject_contents.append(f.read().lower())
            except:
                pass

        for p in go_mod_paths:
            try:
                with open(p, "r", encoding="utf-8", errors="ignore") as f:
                    go_mod_contents.append(f.read().lower())
            except:
                pass

        for p in cargo_toml_paths:
            try:
                with open(p, "r", encoding="utf-8", errors="ignore") as f:
                    cargo_toml_contents.append(f.read().lower())
            except:
                pass

        for p in pom_xml_paths:
            try:
                with open(p, "r", encoding="utf-8", errors="ignore") as f:
                    pom_xml_contents.append(f.read().lower())
            except:
                pass

        # 1. FRAMEWORKS DETECTION
        frameworks = set()
        
        # Check Node / JavaScript Frameworks across all package.json files
        for content in package_contents:
            try:
                pkg = json.loads(content)
                deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
                
                if "next" in deps: frameworks.add("Next.js")
                if "react" in deps: frameworks.add("React")
                if "vue" in deps: frameworks.add("Vue")
                if "@angular/core" in deps: frameworks.add("Angular")
                if "express" in deps: frameworks.add("Express")
                if "@nestjs/core" in deps: frameworks.add("NestJS")
            except:
                pass
                
        # Check Python Frameworks
        for content in (requirements_contents + pyproject_contents):
            if content:
                if "fastapi" in content: frameworks.add("FastAPI")
                if "flask" in content: frameworks.add("Flask")
                if "django" in content: frameworks.add("Django")
                
        # Check Go Frameworks
        for content in go_mod_contents:
            if "github.com/gin-gonic/gin" in content: frameworks.add("Gin")
            if "github.com/gofiber/fiber" in content: frameworks.add("Fiber")
            if "github.com/astaxie/beego" in content: frameworks.add("Beego")
            if "github.com/labstack/echo" in content: frameworks.add("Echo")

        # Check Rust Frameworks
        for content in cargo_toml_contents:
            if "actix-web" in content: frameworks.add("Actix Web")
            if "axum" in content: frameworks.add("Axum")
            if "rocket" in content: frameworks.add("Rocket")

        # Check Java Frameworks
        for content in pom_xml_contents:
            if "spring-boot" in content: frameworks.add("Spring Boot")
            
        # Check Laravel
        for f in self.all_files:
            if "artisan" in os.path.basename(f).lower():
                frameworks.add("Laravel")
                break
                
        self.metadata["frameworks"] = sorted(list(frameworks))

        # 2. DEPENDENCIES CATEGORIZATION
        dependencies = []
        
        # package.json deps
        for p in package_json_paths:
            rel_dir = os.path.dirname(os.path.relpath(p, self.repo_path)).replace("\\", "/")
            prefix = f"{rel_dir}/" if rel_dir else ""
            try:
                with open(p, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                pkg = json.loads(content)
                prod_deps = pkg.get("dependencies", {})
                dev_deps = pkg.get("devDependencies", {})
                
                if prod_deps:
                    prod_list = [f"{k}: {v}" for k, v in prod_deps.items()]
                    dependencies.append(f"Node Production Dependencies ({prefix}package.json):")
                    dependencies.extend([f"  • {item}" for item in sorted(prod_list)])
                    
                if dev_deps:
                    dev_list = [f"{k}: {v}" for k, v in dev_deps.items()]
                    dependencies.append(f"Node Development Dependencies ({prefix}package.json):")
                    dependencies.extend([f"  • {item}" for item in sorted(dev_list)])
            except:
                pass
                
        # requirements.txt deps
        for p in requirements_txt_paths:
            rel_dir = os.path.dirname(os.path.relpath(p, self.repo_path)).replace("\\", "/")
            prefix = f"{rel_dir}/" if rel_dir else ""
            try:
                with open(p, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                req_list = []
                for line in content.split("\n"):
                    line = line.strip()
                    if line and not line.startswith("#"):
                        req_list.append(line)
                if req_list:
                    dependencies.append(f"Python Dependencies ({prefix}requirements.txt):")
                    dependencies.extend([f"  • {item}" for item in sorted(req_list)])
            except:
                pass
                
        # pyproject.toml deps
        for p in pyproject_toml_paths:
            rel_dir = os.path.dirname(os.path.relpath(p, self.repo_path)).replace("\\", "/")
            prefix = f"{rel_dir}/" if rel_dir else ""
            try:
                with open(p, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read().lower()
                toml_deps = []
                lines = content.split("\n")
                in_deps_section = False
                for line in lines:
                    line = line.strip()
                    if line.startswith("[") and "dependencies" in line:
                        in_deps_section = True
                        continue
                    if in_deps_section and line.startswith("["):
                        in_deps_section = False
                    if in_deps_section and "=" in line:
                        toml_deps.append(line)
                if toml_deps:
                    dependencies.append(f"Python Dependencies ({prefix}pyproject.toml):")
                    dependencies.extend([f"  • {item}" for item in sorted(toml_deps)])
            except:
                pass
                
        self.metadata["dependencies"] = dependencies

        # 3. DATABASES
        databases = set()
        
        all_configs_combined = ""
        for content in (package_contents + requirements_contents + pyproject_contents + go_mod_contents + cargo_toml_contents + pom_xml_contents):
            all_configs_combined += content.lower() + "\n"
        
        if "mongodb" in all_configs_combined or "mongoose" in all_configs_combined: databases.add("MongoDB")
        if "pg" in all_configs_combined or "postgresql" in all_configs_combined or "psycopg2" in all_configs_combined: databases.add("PostgreSQL")
        if "mysql" in all_configs_combined or "mysql2" in all_configs_combined or "pymysql" in all_configs_combined: databases.add("MySQL")
        if "sqlite" in all_configs_combined or "sqlite3" in all_configs_combined: databases.add("SQLite")
        if "redis" in all_configs_combined: databases.add("Redis")
        if "firebase" in all_configs_combined: databases.add("Firebase")
        if "supabase" in all_configs_combined: databases.add("Supabase")
        if "prisma" in all_configs_combined: databases.add("Prisma")
        if "typeorm" in all_configs_combined: databases.add("TypeORM")
        
        # Also check file names
        for f in self.all_files:
            basename = os.path.basename(f).lower()
            if "prisma" in basename: databases.add("Prisma")
            if "mongoose" in basename: databases.add("Mongoose")
            if "sqlite" in basename: databases.add("SQLite")
            
        self.metadata["database"] = sorted(list(databases))

        # 4. AUTHENTICATION
        auth = set()
        if "jsonwebtoken" in all_configs_combined or "pyjwt" in all_configs_combined or "jwt" in all_configs_combined: auth.add("JWT")
        if "oauth" in all_configs_combined or "authlib" in all_configs_combined or "oauthlib" in all_configs_combined: auth.add("OAuth")
        if "passport" in all_configs_combined: auth.add("Passport")
        if "bcrypt" in all_configs_combined or "bcryptjs" in all_configs_combined: auth.add("bcrypt")
        if "clerk" in all_configs_combined: auth.add("Clerk")
        if "firebase-auth" in all_configs_combined or "firebase_auth" in all_configs_combined: auth.add("Firebase Auth")
        if "next-auth" in all_configs_combined or "nextauth" in all_configs_combined: auth.add("NextAuth")
        
        self.metadata["authentication"] = sorted(list(auth))

        # 5. PAYMENTS
        payments = set()
        if "stripe" in all_configs_combined: payments.add("Stripe")
        if "razorpay" in all_configs_combined: payments.add("Razorpay")
        if "paypal" in all_configs_combined: payments.add("PayPal")
        if "braintree" in all_configs_combined: payments.add("Braintree")
        
        self.metadata["payments"] = sorted(list(payments))

        # 6. DEPLOYMENT
        deployment = set()
        # Check files presence
        dockerfile_present = any("dockerfile" in os.path.basename(f).lower() for f in self.all_files)
        docker_compose_present = any("docker-compose" in os.path.basename(f).lower() for f in self.all_files)
        vercel_present = any("vercel.json" in os.path.basename(f).lower() for f in self.all_files)
        netlify_present = any("netlify" in os.path.basename(f).lower() for f in self.all_files)
        railway_present = any("railway.json" in os.path.basename(f).lower() for f in self.all_files)
        render_present = any("render.yaml" in os.path.basename(f).lower() for f in self.all_files)
        
        if dockerfile_present: deployment.add("Docker")
        if docker_compose_present: deployment.add("Docker Compose")
        if vercel_present: deployment.add("Vercel")
        if netlify_present: deployment.add("Netlify")
        if railway_present: deployment.add("Railway")
        if render_present: deployment.add("Render")
        
        if "aws" in all_configs_combined or "boto3" in all_configs_combined: deployment.add("AWS")
        if "azure" in all_configs_combined: deployment.add("Azure")
        if "google-cloud" in all_configs_combined or "@google-cloud" in all_configs_combined: deployment.add("GCP")
        
        self.metadata["deployment"] = sorted(list(deployment))

    def _find_all_files_on_disk(self, filename: str) -> list:
        paths = []
        for f in self.all_files:
            if os.path.basename(f).lower() == filename.lower():
                paths.append(os.path.join(self.repo_path, f))
        return paths

    def _calculate_statistics(self, chunk_count: int):
        source_exts = {
            ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".cpp", ".cc", ".cxx", 
            ".h", ".hpp", ".cs", ".go", ".rs", ".kt", ".swift", ".php", ".rb", ".sh"
        }
        
        source_files = sum(1 for f in self.all_files if os.path.splitext(f)[1].lower() in source_exts)
        
        # Calculate folders
        folders = set()
        for f in self.all_files:
            dirname = os.path.dirname(f)
            if dirname:
                folders.add(dirname)
                # add parent folders
                parts = dirname.split("/")
                for i in range(1, len(parts)):
                    folders.add("/".join(parts[:i]))
                    
        readme_present = "No"
        license_present = "No"
        gitignore_present = "No"
        
        for f in self.all_files:
            base = os.path.basename(f).lower()
            if base.startswith("readme"): readme_present = "Yes"
            if base.startswith("license"): license_present = "Yes"
            if base == ".gitignore": gitignore_present = "Yes"
            
        self.metadata["statistics"] = {
            "total_files": len(self.all_files),
            "source_files": source_files,
            "folders": len(folders),
            "code_chunks": chunk_count,
            "readme_present": readme_present,
            "license_present": license_present,
            "gitignore_present": gitignore_present
        }


# ======================================================
# QUESTION ROUTING
# ======================================================

def parse_inspector_query(query: str) -> str:
    """
    Checks if a query is asking for codebase metadata, stack info, dependencies, etc.
    Returns the string representing the category of query (e.g. 'frameworks'),
    or None if not a metadata query.
    """
    clean_q = query.strip().lower()
    
    # Exclude deep explanation/semantic queries
    semantic_keywords = ["explain", "how to", "how do", "implement", "connect", "flow", "architecture", "setup", "configure", "integrate", "run", "start"]
    if any(re.search(r"\b" + re.escape(kw) + r"\b", clean_q) for kw in semantic_keywords):
        return None
        
    # Keywords for routing
    db_keywords = ["database", "databases", "postgresql", "mysql", "sqlite", "mongodb", "redis", "firebase", "supabase", "prisma", "mongoose", "typeorm"]
    auth_keywords = ["authentication", "auth method", "auth system", "login method", "jwt", "oauth", "passport", "bcrypt", "clerk", "nextauth"]
    payment_keywords = ["payment", "payments", "stripe", "razorpay", "paypal", "braintree"]
    deploy_keywords = ["deployment", "deploy", "docker", "dockerfile", "docker-compose", "vercel", "netlify", "render", "railway", "aws", "azure", "gcp"]
    
    if "tech stack" in clean_q or "what stack" in clean_q or "technology stack" in clean_q or "what technologies" in clean_q:
        return "tech_stack"
    elif "framework" in clean_q or "frameworks" in clean_q:
        return "frameworks"
    elif "dependency" in clean_q or "dependencies" in clean_q or "package.json" in clean_q or "requirements.txt" in clean_q:
        return "dependencies"
    elif any(re.search(r"\b" + re.escape(db) + r"\b", clean_q) for db in db_keywords):
        return "database"
    elif any(re.search(r"\b" + re.escape(auth) + r"\b", clean_q) for auth in auth_keywords):
        return "authentication"
    elif any(re.search(r"\b" + re.escape(pay) + r"\b", clean_q) for pay in payment_keywords):
        return "payments"
    elif any(re.search(r"\b" + re.escape(dep) + r"\b", clean_q) for dep in deploy_keywords):
        return "deployment"
    elif "config files" in clean_q or "configuration files" in clean_q or "show configs" in clean_q:
        return "config_files"
    elif "language" in clean_q or "languages" in clean_q:
        return "languages"
    elif "statistics" in clean_q or "total files" in clean_q or "folders" in clean_q or "how many files" in clean_q or "chunk count" in clean_q:
        return "statistics"
        
    return None


def format_inspector_response(category: str, metadata: dict) -> str:
    """
    Formats the metadata output cleanly into markdown.
    """
    if category == "tech_stack":
        lines = [
            "## 📊 Repository Technology Stack",
            "",
            "### 📂 Programming Languages",
            "\n".join([f"• {item}" for item in metadata["languages"]]),
            "",
            "### 🚀 Frameworks",
            "\n".join([f"• {item}" for item in metadata["frameworks"]]),
            "",
            "### 💾 Databases",
            "\n".join([f"• {item}" for item in metadata["database"]]),
            "",
            "### 🛡️ Authentication",
            "\n".join([f"• {item}" for item in metadata["authentication"]]),
            "",
            "### 🚀 Deployment",
            "\n".join([f"• {item}" for item in metadata["deployment"]])
        ]
        return "\n".join(lines)
        
    elif category == "languages":
        return "## 📂 Programming Languages\n" + "\n".join([f"• {item}" for item in metadata["languages"]])
        
    elif category == "frameworks":
        return "## 🚀 Frameworks Detected\n" + "\n".join([f"• {item}" for item in metadata["frameworks"]])
        
    elif category == "dependencies":
        if not metadata["dependencies"] or metadata["dependencies"] == ["Not Detected"]:
            return "## 📦 Dependencies\n• Not Detected"
        return "## 📦 Categorized Dependencies\n" + "\n".join(metadata["dependencies"])
        
    elif category == "database":
        return "## 💾 Databases Detected\n" + "\n".join([f"• {item}" for item in metadata["database"]])
        
    elif category == "authentication":
        return "## 🛡️ Authentication Methods Detected\n" + "\n".join([f"• {item}" for item in metadata["authentication"]])
        
    elif category == "payments":
        return "## 💳 Payment Integrations Detected\n" + "\n".join([f"• {item}" for item in metadata["payments"]])
        
    elif category == "deployment":
        return "## 🚀 Deployment Platforms & Containerization\n" + "\n".join([f"• {item}" for item in metadata["deployment"]])
        
    elif category == "config_files":
        return "## ⚙️ Configuration Files Found\n" + "\n".join([f"• {item}" for item in metadata["config_files"]])
        
    elif category == "statistics":
        stats = metadata["statistics"]
        lines = [
            "## 📈 Repository Statistics",
            f"• **Total Files:** {stats.get('total_files', 0)}",
            f"• **Source Code Files:** {stats.get('source_files', 0)}",
            f"• **Directories:** {stats.get('folders', 0)}",
            f"• **Parsed Code Chunks:** {stats.get('code_chunks', 0)}",
            f"• **README Present:** {stats.get('readme_present', 'No')}",
            f"• **LICENSE Present:** {stats.get('license_present', 'No')}",
            f"• **.gitignore Present:** {stats.get('gitignore_present', 'No')}"
        ]
        return "\n".join(lines)
        
    return "Not Detected"
