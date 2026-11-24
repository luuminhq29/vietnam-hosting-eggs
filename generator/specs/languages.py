"""Phase 2: All 26 Programming Language Egg Specifications."""

from __future__ import annotations

from generator.models import GHCR_NAMESPACE, EggSpec, VariableSpec
from generator.specs.common import GIT_DEPLOY_VARS, GIT_INSTALL_SNIPPET


def get_specs() -> list[EggSpec]:
    return [
        # 1. Python Hosting (3.10 - 3.14)
        EggSpec(
            id="python",
            name="Vietnam Hosting — Python Hosting",
            category="languages",
            description=(
                "Production Python runtime (3.10–3.14) with Virtual Environment, pip, pipx, Poetry, uv, "
                "automatic requirements.txt & pyproject.toml detection, Git deployment, and support for "
                "discord.py, Flask, Django, and FastAPI."
            ),
            icon="python",
            supported_versions=["3.10", "3.11", "3.12", "3.13", "3.14"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=256,
            recommended_ram_mb=512,
            minimum_disk_mb=1024,
            image_source="hybrid_official_and_ghcr",
            dockerfile_path="docker/languages/python/3.13/Dockerfile",
            docker_images={
                "Python 3.13 (Official Yolk)": "ghcr.io/pterodactyl/yolks:python_3.13",
                "Python 3.12 (Official Yolk)": "ghcr.io/pterodactyl/yolks:python_3.12",
                "Python 3.11 (Official Yolk)": "ghcr.io/pterodactyl/yolks:python_3.11",
                "Python 3.10 Legacy (Official Yolk)": "ghcr.io/pterodactyl/yolks:python_3.10",
                "Python 3.14 (Vietnam Hosting GHCR - Build Required)": f"{GHCR_NAMESPACE}:python_3.14",
            },
            custom_docker_images={
                "Python 3.14": f"{GHCR_NAMESPACE}:python_3.14",
                "Python 3.13": f"{GHCR_NAMESPACE}:python_3.13",
                "Python 3.12": f"{GHCR_NAMESPACE}:python_3.12",
                "Python 3.11": f"{GHCR_NAMESPACE}:python_3.11",
                "Python 3.10 (Legacy)": f"{GHCR_NAMESPACE}:python_3.10",
            },
            startup=(
                'if [[ ! -d .venv ]]; then python3 -m venv .venv; fi; '
                'source .venv/bin/activate; '
                'if [[ "${INSTALL_DEPS}" == "1" ]]; then '
                '  if [[ -f pyproject.toml ]] && command -v uv >/dev/null 2>&1; then uv pip install -e .; '
                '  elif [[ -f pyproject.toml ]] && command -v poetry >/dev/null 2>&1; then poetry config virtualenvs.create false && poetry install --no-interaction --only main; '
                '  elif [[ -f "${REQUIREMENTS_FILE}" ]]; then pip install --no-cache-dir -r "${REQUIREMENTS_FILE}"; fi; '
                'fi; '
                'exec python3 "${PY_FILE}"'
            ),
            stop="^C",
            startup_done="Application startup complete|Running on|Uvicorn running|Logged in as|Starting development server|VIETNAM HOSTING",
            install_body=GIT_INSTALL_SNIPPET + r'''
mkdir -p /mnt/server/.local/bin /mnt/server/logs
if [[ ! -f /mnt/server/app.py ]] && [[ -z "${GIT_ADDRESS:-}" ]]; then
    cat > /mnt/server/app.py <<'PYEOF'
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = int(os.environ.get("SERVER_PORT", "8080"))

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"Vietnam Hosting Python Runtime Ready\n")

if __name__ == "__main__":
    print(f"VIETNAM HOSTING Python Ready on 0.0.0.0:{PORT}", flush=True)
    HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
PYEOF
fi
''',
            variables=[
                VariableSpec("Python Entrypoint File", "Relative path to the main Python script inside /home/container.", "PY_FILE", "app.py", rules="required|string|max:128"),
                VariableSpec("Requirements File", "Path to requirements.txt when pyproject.toml is not used.", "REQUIREMENTS_FILE", "requirements.txt", rules="nullable|string|max:128"),
                VariableSpec("Auto Install Dependencies", "Set to 1 to install requirements.txt / pyproject.toml into .venv on boot.", "INSTALL_DEPS", "1", rules="required|boolean"),
                *GIT_DEPLOY_VARS,
            ],
            upstream_license="PSF-2.0",
            upstream_url="https://www.python.org",
            example_files={
                "app.py": (
                    'import os\nfrom http.server import BaseHTTPRequestHandler, HTTPServer\n\n'
                    'PORT = int(os.environ.get("SERVER_PORT", "8080"))\n\n'
                    'class Handler(BaseHTTPRequestHandler):\n'
                    '    def do_GET(self):\n'
                    '        self.send_response(200)\n'
                    '        self.end_headers()\n'
                    '        self.wfile.write(b"Hello from Vietnam Hosting Python!\\n")\n\n'
                    'if __name__ == "__main__":\n'
                    '    print(f"Running on 0.0.0.0:{PORT}", flush=True)\n'
                    '    HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()\n'
                ),
                "requirements.txt": "# Add your Python dependencies here (e.g., fastapi, uvicorn, discord.py)\n",
            },
        ),

        # 2. Node.js Hosting (20, 22, 24, 26)
        EggSpec(
            id="nodejs",
            name="Vietnam Hosting — Node.js Hosting",
            category="languages",
            description=(
                "Production Node.js runtime (20/22/24/26) supporting NPM, Yarn, PNPM, JavaScript/TypeScript, "
                "Discord.js, Express, NestJS, Next.js, Nuxt.js, lockfiles, native addons, and build commands without nodemon."
            ),
            icon="nodejs",
            supported_versions=["20 (Legacy)", "22 LTS", "24 LTS", "26 Active LTS"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=256,
            recommended_ram_mb=512,
            minimum_disk_mb=1024,
            image_source="hybrid_official_and_ghcr",
            dockerfile_path="docker/languages/nodejs/24/Dockerfile",
            docker_images={
                "Node.js 24 LTS (Official Yolk)": "ghcr.io/pterodactyl/yolks:nodejs_24",
                "Node.js 22 LTS (Official Yolk)": "ghcr.io/pterodactyl/yolks:nodejs_22",
                "Node.js 20 Legacy (Official Yolk)": "ghcr.io/pterodactyl/yolks:nodejs_20",
                "Node.js 26 LTS (Vietnam Hosting GHCR - Build Required)": f"{GHCR_NAMESPACE}:nodejs_26",
            },
            custom_docker_images={
                "Node.js 26 Active LTS": f"{GHCR_NAMESPACE}:nodejs_26",
                "Node.js 24 LTS": f"{GHCR_NAMESPACE}:nodejs_24",
                "Node.js 22 LTS": f"{GHCR_NAMESPACE}:nodejs_22",
                "Node.js 20 (Legacy)": f"{GHCR_NAMESPACE}:nodejs_20",
            },
            startup=(
                'export NODE_ENV="${NODE_ENV:-production}"; '
                'if [[ -f package.json ]] && [[ "${INSTALL_DEPS}" == "1" ]]; then '
                '  if [[ "${PACKAGE_MANAGER}" == "pnpm" ]] || { [[ "${PACKAGE_MANAGER}" == "auto" ]] && [[ -f pnpm-lock.yaml ]]; }; then pnpm install --frozen-lockfile || pnpm install; '
                '  elif [[ "${PACKAGE_MANAGER}" == "yarn" ]] || { [[ "${PACKAGE_MANAGER}" == "auto" ]] && [[ -f yarn.lock ]]; }; then yarn install --frozen-lockfile || yarn install; '
                '  elif [[ -f package-lock.json ]]; then npm ci --omit=dev || npm install --omit=dev; '
                '  else npm install --omit=dev; fi; '
                'fi; '
                'if [[ -n "${BUILD_SCRIPT}" ]] && [[ -f package.json ]]; then npm run "${BUILD_SCRIPT}"; fi; '
                'if [[ -n "${START_SCRIPT}" ]] && [[ -f package.json ]]; then exec npm run "${START_SCRIPT}"; else exec node "${MAIN_FILE}"; fi'
            ),
            stop="^C",
            startup_done="Listening on|Ready in|Server running|Logged in as|VIETNAM HOSTING",
            install_body=GIT_INSTALL_SNIPPET + r'''
if [[ ! -f /mnt/server/package.json ]] && [[ ! -f /mnt/server/index.js ]] && [[ -z "${GIT_ADDRESS:-}" ]]; then
    cat > /mnt/server/index.js <<'JSEOF'
const http = require("http");
const port = Number(process.env.SERVER_PORT || 8080);
http.createServer((_req, res) => {
  res.writeHead(200, { "Content-Type": "text/plain" });
  res.end("Vietnam Hosting Node.js Runtime Ready\n");
}).listen(port, "0.0.0.0", () => {
  console.log(`VIETNAM HOSTING Node.js Listening on 0.0.0.0:${port}`);
});
JSEOF
fi
''',
            variables=[
                VariableSpec("Main JS File", "Entrypoint JS file when START_SCRIPT is empty.", "MAIN_FILE", "index.js", rules="required|string|max:128"),
                VariableSpec("Package Manager", "Package manager: auto, npm, yarn, or pnpm.", "PACKAGE_MANAGER", "auto", rules="required|string|in:auto,npm,yarn,pnpm"),
                VariableSpec("NPM Build Script", "Optional package.json script name to run before start (e.g. build).", "BUILD_SCRIPT", "", rules="nullable|string|max:64"),
                VariableSpec("NPM Start Script", "Optional package.json script name to execute (e.g. start). Leave blank to run MAIN_FILE.", "START_SCRIPT", "", rules="nullable|string|max:64"),
                VariableSpec("Install Dependencies on Boot", "Set to 1 to install dependencies from lockfile/package.json.", "INSTALL_DEPS", "1", rules="required|boolean"),
                VariableSpec("Node Environment", "Runtime NODE_ENV (production recommended; never uses nodemon).", "NODE_ENV", "production", rules="required|string|in:production,staging,development"),
                *GIT_DEPLOY_VARS,
            ],
            upstream_license="MIT",
            upstream_url="https://nodejs.org",
            example_files={
                "package.json": '{\n  "name": "vnh-node-example",\n  "version": "1.0.0",\n  "private": true,\n  "scripts": { "start": "node index.js" }\n}\n',
                "index.js": 'const http = require("http");\nconst port = Number(process.env.SERVER_PORT || 8080);\nhttp.createServer((_q, s) => s.end("Hello from Vietnam Hosting Node.js\\n")).listen(port, "0.0.0.0", () => console.log(`Listening on ${port}`));\n',
            },
        ),

        # 3. Bun Hosting
        EggSpec(
            id="bun",
            name="Vietnam Hosting — Bun Hosting",
            category="languages",
            description="High-performance Bun JavaScript & TypeScript runtime with built-in Bun package manager.",
            icon="bun",
            supported_versions=["1.2"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=256,
            recommended_ram_mb=512,
            minimum_disk_mb=1024,
            image_source="requires_ghcr_build",
            dockerfile_path="docker/languages/bun/1.2/Dockerfile",
            docker_images={"Bun 1.2 (Vietnam Hosting GHCR)": f"{GHCR_NAMESPACE}:bun_1.2"},
            custom_docker_images={"Bun 1.2": f"{GHCR_NAMESPACE}:bun_1.2"},
            startup='if [[ -f package.json ]] && [[ "${INSTALL_DEPS}" == "1" ]]; then bun install --frozen-lockfile || bun install; fi; exec bun run "${MAIN_FILE}"',
            stop="^C",
            startup_done="Listening on|Ready|VIETNAM HOSTING",
            install_body=GIT_INSTALL_SNIPPET + r'''
if [[ ! -f /mnt/server/index.ts ]] && [[ -z "${GIT_ADDRESS:-}" ]]; then
    cat > /mnt/server/index.ts <<'EOF'
const port = Number(process.env.SERVER_PORT || 8080);
Bun.serve({
  hostname: "0.0.0.0",
  port,
  fetch() { return new Response("Vietnam Hosting Bun Runtime Ready\n"); },
});
console.log(`VIETNAM HOSTING Bun Listening on 0.0.0.0:${port}`);
EOF
fi
''',
            variables=[
                VariableSpec("Main File or Script", "Entrypoint .ts/.js file or package.json script for `bun run`.", "MAIN_FILE", "index.ts", rules="required|string|max:128"),
                VariableSpec("Auto Install Dependencies", "Run `bun install` when package.json is present.", "INSTALL_DEPS", "1", rules="required|boolean"),
                *GIT_DEPLOY_VARS,
            ],
            upstream_license="MIT",
            upstream_url="https://bun.sh",
            example_files={"index.ts": 'const port = Number(process.env.SERVER_PORT || 8080);\nBun.serve({ hostname: "0.0.0.0", port, fetch: () => new Response("Hello Bun!\\n") });\nconsole.log(`Listening on ${port}`);\n'},
        ),

        # 4. Deno Hosting
        EggSpec(
            id="deno",
            name="Vietnam Hosting — Deno Hosting",
            category="languages",
            description="Secure-by-default Deno JavaScript & TypeScript runtime with configurable filesystem/network permission flags.",
            icon="deno",
            supported_versions=["2.2"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=256,
            recommended_ram_mb=512,
            minimum_disk_mb=1024,
            image_source="requires_ghcr_build",
            dockerfile_path="docker/languages/deno/2/Dockerfile",
            docker_images={"Deno 2.2 (Vietnam Hosting GHCR)": f"{GHCR_NAMESPACE}:deno_2"},
            custom_docker_images={"Deno 2.2": f"{GHCR_NAMESPACE}:deno_2"},
            startup='IFS=" " read -r -a DENO_FLAGS <<< "${DENO_PERMISSIONS}"; exec deno run "${DENO_FLAGS[@]}" "${MAIN_FILE}"',
            stop="^C",
            startup_done="Listening on|Ready|VIETNAM HOSTING",
            install_body=GIT_INSTALL_SNIPPET + r'''
if [[ ! -f /mnt/server/main.ts ]] && [[ -z "${GIT_ADDRESS:-}" ]]; then
    cat > /mnt/server/main.ts <<'EOF'
const port = Number(Deno.env.get("SERVER_PORT") ?? "8080");
console.log(`VIETNAM HOSTING Deno Listening on 0.0.0.0:${port}`);
Deno.serve({ hostname: "0.0.0.0", port }, () => new Response("Vietnam Hosting Deno Ready\n"));
EOF
fi
''',
            variables=[
                VariableSpec("Main File", "Entrypoint TypeScript or JavaScript file.", "MAIN_FILE", "main.ts", rules="required|string|max:128"),
                VariableSpec("Deno Permission Flags", "Explicit Deno permission flags (least privilege by default).", "DENO_PERMISSIONS", "--allow-net --allow-env=SERVER_PORT,NODE_ENV --allow-read=.", rules="required|string|max:256"),
                *GIT_DEPLOY_VARS,
            ],
            upstream_license="MIT",
            upstream_url="https://deno.com",
            example_files={"main.ts": 'const port = Number(Deno.env.get("SERVER_PORT") ?? "8080");\nDeno.serve({ hostname: "0.0.0.0", port }, () => new Response("Hello Deno!\\n"));\n'},
        ),

        # 5. Java Hosting (8, 11, 17, 21, 25)
        EggSpec(
            id="java",
            name="Vietnam Hosting — Java Hosting",
            category="languages",
            description=(
                "Multi-version Java hosting (Eclipse Temurin / OpenJDK 8, 11, 17, 21, 25) with Maven/Gradle support, "
                "Spring Boot compatibility, and automatic JVM heap tuning reserving off-heap/metaspace headroom."
            ),
            icon="java",
            supported_versions=["8", "11", "17", "21 LTS", "25 LTS"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=512,
            recommended_ram_mb=1024,
            minimum_disk_mb=2048,
            image_source="hybrid_official_and_ghcr",
            dockerfile_path="docker/languages/java/21/Dockerfile",
            features=["java_version", "pid_limit"],
            docker_images={
                "Java 25 LTS (Official Yolk)": "ghcr.io/pterodactyl/yolks:java_25",
                "Java 21 LTS (Official Yolk)": "ghcr.io/pterodactyl/yolks:java_21",
                "Java 17 LTS (Official Yolk)": "ghcr.io/pterodactyl/yolks:java_17",
                "Java 11 LTS (Official Yolk)": "ghcr.io/pterodactyl/yolks:java_11",
                "Java 8 LTS (Official Yolk)": "ghcr.io/pterodactyl/yolks:java_8",
            },
            custom_docker_images={
                "Java 25 LTS (Temurin)": f"{GHCR_NAMESPACE}:java_25",
                "Java 21 LTS (Temurin)": f"{GHCR_NAMESPACE}:java_21",
                "Java 17 LTS (Temurin)": f"{GHCR_NAMESPACE}:java_17",
                "Java 11 LTS (Temurin)": f"{GHCR_NAMESPACE}:java_11",
                "Java 8 LTS (Temurin)": f"{GHCR_NAMESPACE}:java_8",
            },
            startup=(
                'MEM={{SERVER_MEMORY}}; OVERHEAD=${JVM_OVERHEAD_MB:-256}; PCT=${JVM_HEAP_PERCENT:-75}; '
                'HEAP_PCT=$(( MEM * PCT / 100 )); HEAP_SUB=$(( MEM - OVERHEAD )); '
                'HEAP=$(( HEAP_SUB < HEAP_PCT ? HEAP_SUB : HEAP_PCT )); (( HEAP < 128 )) && HEAP=128; '
                'if [[ "${BUILD_TOOL}" == "maven" ]] && [[ -f pom.xml ]]; then mvn -B -DskipTests package; '
                'elif [[ "${BUILD_TOOL}" == "gradle" ]] && [[ -x ./gradlew ]]; then ./gradlew bootJar --no-daemon || ./gradlew build -x test --no-daemon; fi; '
                'exec java -Xms128M -Xmx"${HEAP}M" -XX:+UseG1GC -Dserver.address=0.0.0.0 -Dserver.port={{SERVER_PORT}} -jar "${SERVER_JARFILE}"'
            ),
            stop="^C",
            startup_done="Started |Listening on|Done|VIETNAM HOSTING",
            install_body=GIT_INSTALL_SNIPPET + r'''
mkdir -p /mnt/server/config /mnt/server/logs
echo "[VNH][INSTALL] Place your application JAR (default: app.jar) or configure GIT_ADDRESS + BUILD_TOOL."
''',
            variables=[
                VariableSpec("Application JAR File", "Path to the executable JAR file inside /home/container.", "SERVER_JARFILE", "app.jar", rules="required|string|max:191"),
                VariableSpec("Build Tool", "Optional pre-start build tool: none, maven, or gradle.", "BUILD_TOOL", "none", rules="required|string|in:none,maven,gradle"),
                VariableSpec("Off-Heap Reserved RAM (MiB)", "RAM reserved for Metaspace, CodeCache, and OS overhead.", "JVM_OVERHEAD_MB", "256", rules="required|integer|between:64,4096"),
                VariableSpec("Max Heap Percentage", "Maximum percentage of SERVER_MEMORY allocated to JVM -Xmx.", "JVM_HEAP_PERCENT", "75", rules="required|integer|between:30,85"),
                *GIT_DEPLOY_VARS,
            ],
            upstream_license="GPL-2.0-with-classpath-exception",
            upstream_url="https://adoptium.net",
        ),

        # 6. Rust Hosting
        EggSpec(
            id="rust",
            name="Vietnam Hosting — Rust Hosting",
            category="languages",
            description="Rust Stable & Nightly hosting with Cargo.toml auto-detection, release compilation, and CPU-safe CARGO_BUILD_JOBS throttling.",
            icon="rust",
            supported_versions=["Stable (1.86)", "Nightly"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=1024,
            recommended_ram_mb=2048,
            minimum_disk_mb=2048,
            image_source="requires_ghcr_build",
            dockerfile_path="docker/languages/rust/stable/Dockerfile",
            docker_images={
                "Rust Stable 1.86 (Vietnam Hosting GHCR)": f"{GHCR_NAMESPACE}:rust_stable",
                "Rust Nightly (Vietnam Hosting GHCR)": f"{GHCR_NAMESPACE}:rust_nightly",
            },
            custom_docker_images={
                "Rust Stable 1.86": f"{GHCR_NAMESPACE}:rust_stable",
                "Rust Nightly": f"{GHCR_NAMESPACE}:rust_nightly",
            },
            startup=(
                'export CARGO_BUILD_JOBS="${BUILD_JOBS}"; '
                'if [[ -f Cargo.toml ]] && [[ "${AUTO_BUILD}" == "1" ]]; then cargo build --release --jobs "${BUILD_JOBS}"; fi; '
                'exec "./target/release/${BIN_NAME}"'
            ),
            stop="^C",
            startup_done="Listening on|Ready|VIETNAM HOSTING",
            install_body=GIT_INSTALL_SNIPPET + r'''
mkdir -p /mnt/server/target/release
echo "[VNH][INSTALL] Upload a Cargo.toml project or set GIT_ADDRESS; release build uses CARGO_BUILD_JOBS limit."
''',
            variables=[
                VariableSpec("Binary Name", "Compiled binary filename under target/release/.", "BIN_NAME", "app", rules="required|string|max:128"),
                VariableSpec("Auto Build Release", "Set to 1 to run `cargo build --release` on startup.", "AUTO_BUILD", "1", rules="required|boolean"),
                VariableSpec("Cargo Build Jobs Limit", "Maximum parallel rustc jobs to avoid node CPU/RAM exhaustion.", "BUILD_JOBS", "2", rules="required|integer|between:1,4"),
                *GIT_DEPLOY_VARS,
            ],
            upstream_license="MIT OR Apache-2.0",
            upstream_url="https://www.rust-lang.org",
            example_files={
                "Cargo.toml": '[package]\nname = "app"\nversion = "0.1.0"\nedition = "2021"\n',
                "src/main.rs": 'use std::net::TcpListener;\nuse std::io::Write;\nfn main() {\n    let port = std::env::var("SERVER_PORT").unwrap_or_else(|_| "8080".into());\n    let listener = TcpListener::bind(format!("0.0.0.0:{port}")).unwrap();\n    println!("Listening on 0.0.0.0:{port}");\n    for stream in listener.incoming().flatten() {\n        let mut s = stream;\n        let _ = s.write_all(b"HTTP/1.1 200 OK\\r\\nContent-Length: 23\\r\\n\\r\\nVietnam Hosting Rust!\\n");\n    }\n}\n',
            },
        ),

        # 7. Go Hosting
        EggSpec(
            id="go",
            name="Vietnam Hosting — Go Hosting",
            category="languages",
            description="Golang runtime with Go Modules (`go.mod`) auto-detection, static binary compilation, and web/API/bot support.",
            icon="go",
            supported_versions=["1.23", "1.24", "1.25"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=256,
            recommended_ram_mb=512,
            minimum_disk_mb=1024,
            image_source="hybrid_official_and_ghcr",
            dockerfile_path="docker/languages/go/1.25/Dockerfile",
            docker_images={
                "Go 1.23 (Official Yolk)": "ghcr.io/pterodactyl/yolks:go_1.23",
                "Go 1.25 (Vietnam Hosting GHCR - Build Required)": f"{GHCR_NAMESPACE}:go_1.25",
                "Go 1.24 (Vietnam Hosting GHCR - Build Required)": f"{GHCR_NAMESPACE}:go_1.24",
            },
            custom_docker_images={
                "Go 1.25": f"{GHCR_NAMESPACE}:go_1.25",
                "Go 1.24": f"{GHCR_NAMESPACE}:go_1.24",
            },
            startup=(
                'if [[ -f go.mod ]] && [[ "${AUTO_BUILD}" == "1" ]]; then '
                '  go mod download && go build -trimpath -ldflags="-s -w" -o "./${BIN_NAME}" "${BUILD_PKG}"; '
                'fi; exec "./${BIN_NAME}"'
            ),
            stop="^C",
            startup_done="Listening on|Ready|VIETNAM HOSTING",
            install_body=GIT_INSTALL_SNIPPET + r'''
if [[ ! -f /mnt/server/go.mod ]] && [[ -z "${GIT_ADDRESS:-}" ]]; then
    cat > /mnt/server/go.mod <<'EOF'
module vnh-app

go 1.23
EOF
    cat > /mnt/server/main.go <<'EOF'
package main

import (
	"fmt"
	"net/http"
	"os"
)

func main() {
	port := os.Getenv("SERVER_PORT")
	if port == "" {
		port = "8080"
	}
	http.HandleFunc("/", func(w http.ResponseWriter, _ *http.Request) {
		fmt.Fprintln(w, "Vietnam Hosting Go Runtime Ready")
	})
	fmt.Printf("VIETNAM HOSTING Go Listening on 0.0.0.0:%s\n", port)
	if err := http.ListenAndServe("0.0.0.0:"+port, nil); err != nil {
		panic(err)
	}
}
EOF
fi
''',
            variables=[
                VariableSpec("Output Binary Name", "Compiled executable filename in /home/container.", "BIN_NAME", "server", rules="required|string|max:128"),
                VariableSpec("Go Build Package", "Target package path for `go build` (e.g. `.` or `./cmd/server`).", "BUILD_PKG", ".", rules="required|string|max:128"),
                VariableSpec("Auto Build on Boot", "Set to 1 to compile with `go build` before running.", "AUTO_BUILD", "1", rules="required|boolean"),
                *GIT_DEPLOY_VARS,
            ],
            upstream_license="BSD-3-Clause",
            upstream_url="https://go.dev",
            example_files={
                "go.mod": "module example\n\ngo 1.23\n",
                "main.go": 'package main\nimport ("fmt"; "net/http"; "os")\nfunc main() { p := os.Getenv("SERVER_PORT"); if p == "" { p = "8080" }; http.HandleFunc("/", func(w http.ResponseWriter, _ *http.Request) { fmt.Fprintln(w, "Hello Go!") }); fmt.Println("Listening on :" + p); _ = http.ListenAndServe("0.0.0.0:"+p, nil) }\n',
            },
        ),

        # 8. C/C++ Hosting
        EggSpec(
            id="c-cpp",
            name="Vietnam Hosting — C/C++ Hosting",
            category="languages",
            description="C and C++ build/runtime environment with GCC, G++, Clang, Make, CMake, and parallel job throttling.",
            icon="cpp",
            supported_versions=["GCC 14 / Clang 19 (Debian 13)"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=512,
            recommended_ram_mb=1024,
            minimum_disk_mb=1024,
            image_source="requires_ghcr_build",
            dockerfile_path="docker/languages/c-cpp/Dockerfile",
            docker_images={"C/C++ Debian 13 (Vietnam Hosting GHCR)": f"{GHCR_NAMESPACE}:ccpp_debian13"},
            custom_docker_images={"C/C++ Debian 13": f"{GHCR_NAMESPACE}:ccpp_debian13"},
            startup=(
                'export MAKEFLAGS="-j${BUILD_JOBS}" CMAKE_BUILD_PARALLEL_LEVEL="${BUILD_JOBS}"; '
                'if [[ "${AUTO_BUILD}" == "1" ]]; then '
                '  if [[ -f CMakeLists.txt ]]; then cmake -S . -B build -DCMAKE_BUILD_TYPE=Release && cmake --build build -j "${BUILD_JOBS}"; '
                '  elif [[ -f Makefile ]]; then make -j "${BUILD_JOBS}"; '
                '  elif [[ -f "${SOURCE_FILE}" ]]; then "${COMPILER}" -O2 "${SOURCE_FILE}" -o "./${BIN_NAME}"; fi; '
                'fi; exec "./${BIN_NAME}"'
            ),
            stop="^C",
            startup_done="Listening on|Ready|VIETNAM HOSTING",
            install_body=GIT_INSTALL_SNIPPET + r'''
if [[ ! -f /mnt/server/main.cpp ]] && [[ ! -f /mnt/server/Makefile ]] && [[ ! -f /mnt/server/CMakeLists.txt ]] && [[ -z "${GIT_ADDRESS:-}" ]]; then
    cat > /mnt/server/main.cpp <<'EOF'
#include <iostream>
int main() {
    std::cout << "VIETNAM HOSTING C/C++ Runtime Ready" << std::endl;
    return 0;
}
EOF
fi
''',
            variables=[
                VariableSpec("Compiler", "Compiler binary when building single-file source: g++, gcc, or clang++.", "COMPILER", "g++", rules="required|string|in:g++,gcc,clang,clang++"),
                VariableSpec("Source File", "Single source file fallback if no CMakeLists.txt or Makefile exists.", "SOURCE_FILE", "main.cpp", rules="nullable|string|max:128"),
                VariableSpec("Executable Path", "Compiled executable relative path to run.", "BIN_NAME", "app", rules="required|string|max:128"),
                VariableSpec("Build Jobs Limit", "Maximum parallel compile threads.", "BUILD_JOBS", "2", rules="required|integer|between:1,4"),
                VariableSpec("Auto Build on Boot", "Set to 1 to build before executing.", "AUTO_BUILD", "1", rules="required|boolean"),
                *GIT_DEPLOY_VARS,
            ],
            upstream_license="GPL-3.0 / Apache-2.0",
            upstream_url="https://gcc.gnu.org",
        ),

        # 9. C#/.NET Hosting
        EggSpec(
            id="dotnet",
            name="Vietnam Hosting — C#/.NET Hosting",
            category="languages",
            description=".NET 8/9/10 LTS/11 STS runtime with ASP.NET Core, .NET Console, NuGet restore, and Release publish.",
            icon="dotnet",
            supported_versions=["8.0 (Legacy)", "9.0 (Legacy)", "10.0 LTS", "11.0 STS"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=512,
            recommended_ram_mb=1024,
            minimum_disk_mb=2048,
            image_source="requires_ghcr_build",
            dockerfile_path="docker/languages/dotnet/10/Dockerfile",
            docker_images={
                ".NET 10.0 LTS (Vietnam Hosting GHCR)": f"{GHCR_NAMESPACE}:dotnet_10",
                ".NET 11.0 STS (Vietnam Hosting GHCR)": f"{GHCR_NAMESPACE}:dotnet_11",
                ".NET 9.0 (Vietnam Hosting GHCR)": f"{GHCR_NAMESPACE}:dotnet_9",
                ".NET 8.0 (Vietnam Hosting GHCR)": f"{GHCR_NAMESPACE}:dotnet_8",
            },
            custom_docker_images={
                ".NET 10.0 LTS": f"{GHCR_NAMESPACE}:dotnet_10",
                ".NET 11.0 STS": f"{GHCR_NAMESPACE}:dotnet_11",
                ".NET 9.0": f"{GHCR_NAMESPACE}:dotnet_9",
                ".NET 8.0": f"{GHCR_NAMESPACE}:dotnet_8",
            },
            startup=(
                'export ASPNETCORE_URLS="http://0.0.0.0:{{SERVER_PORT}}"; '
                'if [[ "${AUTO_PUBLISH}" == "1" ]] && [[ -n "${PROJECT_FILE}" ]] && [[ -f "${PROJECT_FILE}" ]]; then '
                '  dotnet publish "${PROJECT_FILE}" -c Release -o ./out --nologo; '
                'fi; '
                'if [[ -f "./out/${APP_DLL}" ]]; then exec dotnet "./out/${APP_DLL}"; else exec dotnet "./${APP_DLL}"; fi'
            ),
            stop="^C",
            startup_done="Now listening on:|Application started|VIETNAM HOSTING",
            install_body=GIT_INSTALL_SNIPPET + r'''
mkdir -p /mnt/server/out
echo "[VNH][INSTALL] Upload your .NET project or published DLL, or specify GIT_ADDRESS + PROJECT_FILE."
''',
            variables=[
                VariableSpec("Project File (.csproj)", "Optional .csproj path to publish before launch.", "PROJECT_FILE", "", rules="nullable|string|max:191"),
                VariableSpec("Application DLL", "Compiled .NET assembly filename to execute.", "APP_DLL", "App.dll", rules="required|string|max:191"),
                VariableSpec("Auto Publish on Boot", "Set to 1 to run `dotnet publish -c Release` when PROJECT_FILE exists.", "AUTO_PUBLISH", "1", rules="required|boolean"),
                VariableSpec("ASP.NET Core Environment", "ASPNETCORE_ENVIRONMENT value.", "ASPNETCORE_ENVIRONMENT", "Production", rules="required|string|in:Production,Staging,Development"),
                *GIT_DEPLOY_VARS,
            ],
            upstream_license="MIT",
            upstream_url="https://dotnet.microsoft.com",
        ),

        # 10. PHP Hosting (8.2 - 8.5 + Composer + PHP-FPM + Nginx)
        EggSpec(
            id="php",
            name="Vietnam Hosting — PHP Hosting (Nginx + PHP-FPM)",
            category="languages",
            description="Production PHP 8.2–8.5 hosting with Composer, rootless Nginx + PHP-FPM, common extensions, Laravel, Symfony, and WordPress readiness.",
            icon="php",
            supported_versions=["8.2", "8.3", "8.4", "8.5"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=256,
            recommended_ram_mb=512,
            minimum_disk_mb=1024,
            image_source="requires_ghcr_build",
            dockerfile_path="docker/languages/php/8.4/Dockerfile",
            docker_images={
                "PHP 8.5 + Nginx (Vietnam Hosting GHCR)": f"{GHCR_NAMESPACE}:php_8.5",
                "PHP 8.4 + Nginx (Vietnam Hosting GHCR)": f"{GHCR_NAMESPACE}:php_8.4",
                "PHP 8.3 + Nginx (Vietnam Hosting GHCR)": f"{GHCR_NAMESPACE}:php_8.3",
                "PHP 8.2 + Nginx (Vietnam Hosting GHCR)": f"{GHCR_NAMESPACE}:php_8.2",
            },
            custom_docker_images={
                "PHP 8.5": f"{GHCR_NAMESPACE}:php_8.5",
                "PHP 8.4": f"{GHCR_NAMESPACE}:php_8.4",
                "PHP 8.3": f"{GHCR_NAMESPACE}:php_8.3",
                "PHP 8.2": f"{GHCR_NAMESPACE}:php_8.2",
            },
            startup=(
                'mkdir -p /home/container/tmp /home/container/logs; '
                'if [[ -f composer.json ]] && [[ "${COMPOSER_INSTALL}" == "1" ]]; then composer install --no-dev --optimize-autoloader --no-interaction; fi; '
                'sed "s|__PORT__|{{SERVER_PORT}}|g; s|__DOCROOT__|/home/container/${WEBROOT}|g" /home/container/nginx/nginx.conf.tpl > /home/container/tmp/nginx.conf; '
                'php-fpm --fpm-config /home/container/php/php-fpm.conf --daemonize; '
                'echo "VIETNAM HOSTING PHP-FPM + Nginx Ready on 0.0.0.0:{{SERVER_PORT}}"; '
                'exec nginx -c /home/container/tmp/nginx.conf -g "daemon off;"'
            ),
            stop="^C",
            startup_done="VIETNAM HOSTING PHP-FPM|Ready",
            install_body=GIT_INSTALL_SNIPPET + r'''
mkdir -p /mnt/server/public /mnt/server/nginx /mnt/server/php /mnt/server/tmp /mnt/server/logs
if [[ ! -f /mnt/server/nginx/nginx.conf.tpl ]]; then
cat > /mnt/server/nginx/nginx.conf.tpl <<'NGINXEOF'
worker_processes auto;
pid /home/container/tmp/nginx.pid;
error_log /home/container/logs/nginx-error.log warn;
events { worker_connections 1024; }
http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    access_log /home/container/logs/nginx-access.log;
    client_body_temp_path /home/container/tmp/body;
    proxy_temp_path /home/container/tmp/proxy;
    fastcgi_temp_path /home/container/tmp/fastcgi;
    uwsgi_temp_path /home/container/tmp/uwsgi;
    scgi_temp_path /home/container/tmp/scgi;
    sendfile on;
    keepalive_timeout 65;
    server {
        listen 0.0.0.0:__PORT__;
        root __DOCROOT__;
        index index.php index.html;
        location / { try_files $uri $uri/ /index.php?$query_string; }
        location ~ \.php$ {
            include /etc/nginx/fastcgi_params;
            fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
            fastcgi_pass unix:/home/container/tmp/php-fpm.sock;
        }
        location ~ /\.(?!well-known).* { deny all; }
    }
}
NGINXEOF
fi
if [[ ! -f /mnt/server/php/php-fpm.conf ]]; then
cat > /mnt/server/php/php-fpm.conf <<'FPMEOF'
[global]
pid = /home/container/tmp/php-fpm.pid
error_log = /home/container/logs/php-fpm.log
[www]
listen = /home/container/tmp/php-fpm.sock
pm = dynamic
pm.max_children = 10
pm.start_servers = 2
pm.min_spare_servers = 1
pm.max_spare_servers = 4
clear_env = no
FPMEOF
fi
if [[ ! -f /mnt/server/public/index.php ]]; then
    printf '<?php header("Content-Type: text/plain"); echo "Vietnam Hosting PHP " . PHP_VERSION . " Ready\\n";\n' > /mnt/server/public/index.php
fi
''',
            variables=[
                VariableSpec("Web Root Directory", "Document root relative to /home/container (e.g. public or .).", "WEBROOT", "public", rules="required|string|max:128"),
                VariableSpec("Auto Composer Install", "Run `composer install --no-dev` when composer.json exists.", "COMPOSER_INSTALL", "1", rules="required|boolean"),
                *GIT_DEPLOY_VARS,
            ],
            upstream_license="PHP-3.01",
            upstream_url="https://www.php.net",
        ),

        # 11. Ruby
        EggSpec(
            id="ruby",
            name="Vietnam Hosting — Ruby Hosting",
            category="languages",
            description="Ruby 3.4 runtime with Bundler and automatic Gemfile installation for Rails, Sinatra, and bots.",
            icon="ruby",
            supported_versions=["3.4"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=256,
            recommended_ram_mb=512,
            minimum_disk_mb=1024,
            image_source="requires_ghcr_build",
            dockerfile_path="docker/languages/ruby/Dockerfile",
            docker_images={"Ruby 3.4 (Vietnam Hosting GHCR)": f"{GHCR_NAMESPACE}:ruby_3.4"},
            custom_docker_images={"Ruby 3.4": f"{GHCR_NAMESPACE}:ruby_3.4"},
            startup='if [[ -f Gemfile ]] && [[ "${BUNDLE_INSTALL}" == "1" ]]; then bundle install --jobs=2; fi; if [[ -f Gemfile ]]; then exec bundle exec ruby "${MAIN_FILE}"; else exec ruby "${MAIN_FILE}"; fi',
            stop="^C",
            startup_done="Listening|Puma starting|VIETNAM HOSTING",
            install_body=GIT_INSTALL_SNIPPET + '\nif [[ ! -f /mnt/server/app.rb ]] && [[ -z "${GIT_ADDRESS:-}" ]]; then printf \'puts "VIETNAM HOSTING Ruby #{RUBY_VERSION} Ready"\\n\' > /mnt/server/app.rb; fi\n',
            variables=[
                VariableSpec("Main Ruby File", "Entrypoint .rb file.", "MAIN_FILE", "app.rb", rules="required|string|max:128"),
                VariableSpec("Run Bundle Install", "Auto-run `bundle install` when Gemfile exists.", "BUNDLE_INSTALL", "1", rules="required|boolean"),
                *GIT_DEPLOY_VARS,
            ],
            upstream_license="BSD-2-Clause",
            upstream_url="https://www.ruby-lang.org",
        ),

        # 12. Lua
        EggSpec(
            id="lua",
            name="Vietnam Hosting — Lua Hosting",
            category="languages",
            description="Lua 5.4 runtime with LuaRocks package manager for scripts, automation, and lightweight services.",
            icon="lua",
            supported_versions=["5.4"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=128,
            recommended_ram_mb=256,
            minimum_disk_mb=512,
            image_source="requires_ghcr_build",
            dockerfile_path="docker/languages/lua/Dockerfile",
            docker_images={"Lua 5.4 (Vietnam Hosting GHCR)": f"{GHCR_NAMESPACE}:lua_5.4"},
            custom_docker_images={"Lua 5.4": f"{GHCR_NAMESPACE}:lua_5.4"},
            startup='exec lua "${MAIN_FILE}"',
            stop="^C",
            startup_done="Ready|VIETNAM HOSTING",
            install_body=GIT_INSTALL_SNIPPET + '\nif [[ ! -f /mnt/server/main.lua ]] && [[ -z "${GIT_ADDRESS:-}" ]]; then printf \'print("VIETNAM HOSTING Lua Ready")\\n\' > /mnt/server/main.lua; fi\n',
            variables=[VariableSpec("Main Lua File", "Entrypoint .lua file.", "MAIN_FILE", "main.lua", rules="required|string|max:128"), *GIT_DEPLOY_VARS],
            upstream_license="MIT",
            upstream_url="https://www.lua.org",
        ),

        # 13. LuaJIT
        EggSpec(
            id="luajit",
            name="Vietnam Hosting — LuaJIT Hosting",
            category="languages",
            description="High-speed LuaJIT 2.1 JIT-compiled Lua runtime with LuaRocks and FFI support.",
            icon="luajit",
            supported_versions=["2.1"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=128,
            recommended_ram_mb=256,
            minimum_disk_mb=512,
            image_source="requires_ghcr_build",
            dockerfile_path="docker/languages/luajit/Dockerfile",
            docker_images={"LuaJIT 2.1 (Vietnam Hosting GHCR)": f"{GHCR_NAMESPACE}:luajit_2.1"},
            custom_docker_images={"LuaJIT 2.1": f"{GHCR_NAMESPACE}:luajit_2.1"},
            startup='exec luajit "${MAIN_FILE}"',
            stop="^C",
            startup_done="Ready|VIETNAM HOSTING",
            install_body=GIT_INSTALL_SNIPPET + '\nif [[ ! -f /mnt/server/main.lua ]] && [[ -z "${GIT_ADDRESS:-}" ]]; then printf \'print("VIETNAM HOSTING LuaJIT Ready")\\n\' > /mnt/server/main.lua; fi\n',
            variables=[VariableSpec("Main Lua File", "Entrypoint .lua file for LuaJIT.", "MAIN_FILE", "main.lua", rules="required|string|max:128"), *GIT_DEPLOY_VARS],
            upstream_license="MIT",
            upstream_url="https://luajit.org",
        ),

        # 14. Perl
        EggSpec(
            id="perl",
            name="Vietnam Hosting — Perl Hosting",
            category="languages",
            description="Perl 5.40 runtime with cpanm and local::lib user-space module management.",
            icon="perl",
            supported_versions=["5.40"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=128,
            recommended_ram_mb=256,
            minimum_disk_mb=512,
            image_source="requires_ghcr_build",
            dockerfile_path="docker/languages/perl/Dockerfile",
            docker_images={"Perl 5.40 (Vietnam Hosting GHCR)": f"{GHCR_NAMESPACE}:perl_5.40"},
            custom_docker_images={"Perl 5.40": f"{GHCR_NAMESPACE}:perl_5.40"},
            startup='if [[ -f cpanfile ]] && [[ "${INSTALL_DEPS}" == "1" ]]; then cpanm --notest --local-lib=/home/container/local --installdeps .; fi; exec perl "${MAIN_FILE}"',
            stop="^C",
            startup_done="Ready|VIETNAM HOSTING",
            install_body=GIT_INSTALL_SNIPPET + '\nif [[ ! -f /mnt/server/main.pl ]] && [[ -z "${GIT_ADDRESS:-}" ]]; then printf \'use strict; use warnings; print "VIETNAM HOSTING Perl Ready\\n";\\n\' > /mnt/server/main.pl; fi\n',
            variables=[
                VariableSpec("Main Perl Script", "Entrypoint .pl file.", "MAIN_FILE", "main.pl", rules="required|string|max:128"),
                VariableSpec("Install cpanfile Deps", "Install CPAN modules from cpanfile into local/.", "INSTALL_DEPS", "1", rules="required|boolean"),
                *GIT_DEPLOY_VARS,
            ],
            upstream_license="Artistic-1.0-Perl OR GPL-1.0-or-later",
            upstream_url="https://www.perl.org",
        ),

        # 15. Kotlin
        EggSpec(
            id="kotlin",
            name="Vietnam Hosting — Kotlin Hosting",
            category="languages",
            description="Kotlin 2.1 JVM runtime with kotlinc, Gradle, and automatic JVM heap calculation.",
            icon="kotlin",
            supported_versions=["2.1 (JDK 21)"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=512,
            recommended_ram_mb=1024,
            minimum_disk_mb=2048,
            image_source="requires_ghcr_build",
            dockerfile_path="docker/languages/kotlin/Dockerfile",
            docker_images={"Kotlin 2.1 + JDK 21 (Vietnam Hosting GHCR)": f"{GHCR_NAMESPACE}:kotlin_2.1"},
            custom_docker_images={"Kotlin 2.1 + JDK 21": f"{GHCR_NAMESPACE}:kotlin_2.1"},
            startup=(
                'MEM={{SERVER_MEMORY}}; HEAP=$(( MEM * 75 / 100 )); (( HEAP < 128 )) && HEAP=128; '
                'if [[ -f build.gradle.kts ]] && [[ -x ./gradlew ]]; then ./gradlew shadowJar --no-daemon || ./gradlew build -x test --no-daemon; '
                'elif [[ -f "${SOURCE_FILE}" ]] && [[ ! -f "${APP_JAR}" ]]; then kotlinc "${SOURCE_FILE}" -include-runtime -d "${APP_JAR}"; fi; '
                'exec java -Xms128M -Xmx"${HEAP}M" -jar "${APP_JAR}"'
            ),
            stop="^C",
            startup_done="Listening|Started|Ready|VIETNAM HOSTING",
            install_body=GIT_INSTALL_SNIPPET + '\nif [[ ! -f /mnt/server/Main.kt ]] && [[ -z "${GIT_ADDRESS:-}" ]]; then printf \'fun main() { println("VIETNAM HOSTING Kotlin Ready") }\\n\' > /mnt/server/Main.kt; fi\n',
            variables=[
                VariableSpec("Kotlin Source File", "Fallback .kt file if Gradle is not used.", "SOURCE_FILE", "Main.kt", rules="nullable|string|max:128"),
                VariableSpec("Output JAR", "Executable JAR filename.", "APP_JAR", "app.jar", rules="required|string|max:128"),
                *GIT_DEPLOY_VARS,
            ],
            upstream_license="Apache-2.0",
            upstream_url="https://kotlinlang.org",
        ),

        # 16. Scala
        EggSpec(
            id="scala",
            name="Vietnam Hosting — Scala Hosting",
            category="languages",
            description="Scala 3 & sbt runtime on Eclipse Temurin JDK 21 with memory-capped JVM execution.",
            icon="scala",
            supported_versions=["3.6 (JDK 21)"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=512,
            recommended_ram_mb=1024,
            minimum_disk_mb=2048,
            image_source="requires_ghcr_build",
            dockerfile_path="docker/languages/scala/Dockerfile",
            docker_images={"Scala 3 + sbt (Vietnam Hosting GHCR)": f"{GHCR_NAMESPACE}:scala_3"},
            custom_docker_images={"Scala 3 + sbt": f"{GHCR_NAMESPACE}:scala_3"},
            startup='MEM={{SERVER_MEMORY}}; HEAP=$(( MEM * 75 / 100 )); (( HEAP < 256 )) && HEAP=256; if [[ -f "${APP_JAR}" ]]; then exec java -Xmx"${HEAP}M" -jar "${APP_JAR}"; else exec sbt -J-Xmx"${HEAP}M" run; fi',
            stop="^C",
            startup_done="Listening|Started|Ready|VIETNAM HOSTING",
            install_body=GIT_INSTALL_SNIPPET + '\necho "[VNH][INSTALL] Upload build.sbt or fat JAR (app.jar)."\n',
            variables=[VariableSpec("Application JAR", "Pre-assembled JAR file (falls back to `sbt run` if absent).", "APP_JAR", "app.jar", rules="required|string|max:128"), *GIT_DEPLOY_VARS],
            upstream_license="Apache-2.0",
            upstream_url="https://www.scala-lang.org",
        ),

        # 17. Dart
        EggSpec(
            id="dart",
            name="Vietnam Hosting — Dart Hosting",
            category="languages",
            description="Dart 3.7 SDK hosting with pubspec.yaml dependency resolution and optional native AOT compilation.",
            icon="dart",
            supported_versions=["3.7"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=256,
            recommended_ram_mb=512,
            minimum_disk_mb=1024,
            image_source="requires_ghcr_build",
            dockerfile_path="docker/languages/dart/Dockerfile",
            docker_images={"Dart 3.7 (Vietnam Hosting GHCR)": f"{GHCR_NAMESPACE}:dart_3.7"},
            custom_docker_images={"Dart 3.7": f"{GHCR_NAMESPACE}:dart_3.7"},
            startup='if [[ -f pubspec.yaml ]]; then dart pub get; fi; if [[ "${AOT_COMPILE}" == "1" ]]; then dart compile exe "${MAIN_FILE}" -o ./app.exe && exec ./app.exe; else exec dart run "${MAIN_FILE}"; fi',
            stop="^C",
            startup_done="Listening|Ready|VIETNAM HOSTING",
            install_body=GIT_INSTALL_SNIPPET + '\nif [[ ! -f /mnt/server/bin/main.dart ]] && [[ -z "${GIT_ADDRESS:-}" ]]; then mkdir -p /mnt/server/bin; printf \'void main() { print("VIETNAM HOSTING Dart Ready"); }\\n\' > /mnt/server/bin/main.dart; fi\n',
            variables=[
                VariableSpec("Main Dart File", "Entrypoint .dart file.", "MAIN_FILE", "bin/main.dart", rules="required|string|max:128"),
                VariableSpec("AOT Compile Native Binary", "Set to 1 to compile with `dart compile exe` before running.", "AOT_COMPILE", "0", rules="required|boolean"),
                *GIT_DEPLOY_VARS,
            ],
            upstream_license="BSD-3-Clause",
            upstream_url="https://dart.dev",
        ),

        # 18. Elixir
        EggSpec(
            id="elixir",
            name="Vietnam Hosting — Elixir Hosting",
            category="languages",
            description="Elixir 1.18 (Erlang/OTP 27) runtime with Mix, Hex, and Phoenix web/bot application support.",
            icon="elixir",
            supported_versions=["1.18 (OTP 27)"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=256,
            recommended_ram_mb=512,
            minimum_disk_mb=1024,
            image_source="requires_ghcr_build",
            dockerfile_path="docker/languages/elixir/Dockerfile",
            docker_images={"Elixir 1.18 OTP 27 (Vietnam Hosting GHCR)": f"{GHCR_NAMESPACE}:elixir_1.18"},
            custom_docker_images={"Elixir 1.18 OTP 27": f"{GHCR_NAMESPACE}:elixir_1.18"},
            startup='export MIX_ENV="${MIX_ENV}" PORT="{{SERVER_PORT}}"; if [[ -f mix.exs ]]; then mix local.hex --force && mix local.rebar --force && mix deps.get && exec mix "${MIX_TASK}"; else exec elixir "${MAIN_FILE}"; fi',
            stop="^C",
            startup_done="Running|Listening|Ready|VIETNAM HOSTING",
            install_body=GIT_INSTALL_SNIPPET + '\nif [[ ! -f /mnt/server/main.exs ]] && [[ -z "${GIT_ADDRESS:-}" ]]; then printf \'IO.puts("VIETNAM HOSTING Elixir Ready")\\n\' > /mnt/server/main.exs; fi\n',
            variables=[
                VariableSpec("Mix Task", "Mix task when mix.exs exists (e.g. `phx.server` or `run --no-halt`).", "MIX_TASK", "run --no-halt", rules="required|string|max:128"),
                VariableSpec("MIX_ENV", "Elixir environment (prod, dev, test).", "MIX_ENV", "prod", rules="required|string|in:prod,dev,test"),
                VariableSpec("Fallback Script", "Elixir script when mix.exs is absent.", "MAIN_FILE", "main.exs", rules="required|string|max:128"),
                *GIT_DEPLOY_VARS,
            ],
            upstream_license="Apache-2.0",
            upstream_url="https://elixir-lang.org",
        ),

        # 19. Erlang
        EggSpec(
            id="erlang",
            name="Vietnam Hosting — Erlang Hosting",
            category="languages",
            description="Erlang/OTP 27 runtime with rebar3 for concurrent distributed services and messaging backends.",
            icon="erlang",
            supported_versions=["OTP 27"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=256,
            recommended_ram_mb=512,
            minimum_disk_mb=1024,
            image_source="requires_ghcr_build",
            dockerfile_path="docker/languages/erlang/Dockerfile",
            docker_images={"Erlang/OTP 27 (Vietnam Hosting GHCR)": f"{GHCR_NAMESPACE}:erlang_27"},
            custom_docker_images={"Erlang/OTP 27": f"{GHCR_NAMESPACE}:erlang_27"},
            startup='if [[ -f rebar.config ]]; then rebar3 compile && exec rebar3 shell --no-halt; else exec escript "${MAIN_FILE}"; fi',
            stop="^C",
            startup_done="Ready|VIETNAM HOSTING",
            install_body=GIT_INSTALL_SNIPPET + '\nif [[ ! -f /mnt/server/main.escript ]] && [[ -z "${GIT_ADDRESS:-}" ]]; then printf \'#!/usr/bin/env escript\\nmain(_) -> io:format("VIETNAM HOSTING Erlang Ready~n").\\n\' > /mnt/server/main.escript; fi\n',
            variables=[VariableSpec("Main Escript File", "Fallback escript when rebar.config is absent.", "MAIN_FILE", "main.escript", rules="required|string|max:128"), *GIT_DEPLOY_VARS],
            upstream_license="Apache-2.0",
            upstream_url="https://www.erlang.org",
        ),

        # 20. Haskell
        EggSpec(
            id="haskell",
            name="Vietnam Hosting — Haskell Hosting",
            category="languages",
            description="Haskell GHC 9.10 + Cabal runtime with bounded compile parallelism for compiled executables and services.",
            icon="haskell",
            supported_versions=["GHC 9.10"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=512,
            recommended_ram_mb=1024,
            minimum_disk_mb=2048,
            image_source="requires_ghcr_build",
            dockerfile_path="docker/languages/haskell/Dockerfile",
            docker_images={"Haskell GHC 9.10 (Vietnam Hosting GHCR)": f"{GHCR_NAMESPACE}:haskell_9.10"},
            custom_docker_images={"Haskell GHC 9.10": f"{GHCR_NAMESPACE}:haskell_9.10"},
            startup='if ls *.cabal >/dev/null 2>&1; then cabal update && cabal build -j"${BUILD_JOBS}" && exec cabal run; else ghc -O2 "${MAIN_FILE}" -o ./app && exec ./app; fi',
            stop="^C",
            startup_done="Ready|Listening|VIETNAM HOSTING",
            install_body=GIT_INSTALL_SNIPPET + '\nif [[ ! -f /mnt/server/Main.hs ]] && [[ -z "${GIT_ADDRESS:-}" ]]; then printf \'main :: IO ()\\nmain = putStrLn "VIETNAM HOSTING Haskell Ready"\\n\' > /mnt/server/Main.hs; fi\n',
            variables=[
                VariableSpec("Main Haskell File", "Fallback .hs file when no .cabal project exists.", "MAIN_FILE", "Main.hs", rules="required|string|max:128"),
                VariableSpec("Build Jobs", "Max parallel Cabal jobs.", "BUILD_JOBS", "2", rules="required|integer|between:1,4"),
                *GIT_DEPLOY_VARS,
            ],
            upstream_license="BSD-3-Clause",
            upstream_url="https://www.haskell.org",
        ),

        # 21. Swift
        EggSpec(
            id="swift",
            name="Vietnam Hosting — Swift Hosting",
            category="languages",
            description="Server-side Swift 6.1 hosting (Vapor/Hummingbird ready) with Swift Package Manager and release builds.",
            icon="swift",
            supported_versions=["6.1"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=1024,
            recommended_ram_mb=2048,
            minimum_disk_mb=2048,
            image_source="requires_ghcr_build",
            dockerfile_path="docker/languages/swift/Dockerfile",
            docker_images={"Swift 6.1 (Vietnam Hosting GHCR)": f"{GHCR_NAMESPACE}:swift_6.1"},
            custom_docker_images={"Swift 6.1": f"{GHCR_NAMESPACE}:swift_6.1"},
            startup='if [[ -f Package.swift ]] && [[ "${AUTO_BUILD}" == "1" ]]; then swift build -c release -j "${BUILD_JOBS}"; fi; if [[ -x ".build/release/${BIN_NAME}" ]]; then exec ".build/release/${BIN_NAME}"; else exec swift "${MAIN_FILE}"; fi',
            stop="^C",
            startup_done="Server starting|Listening|Ready|VIETNAM HOSTING",
            install_body=GIT_INSTALL_SNIPPET + '\nif [[ ! -f /mnt/server/main.swift ]] && [[ -z "${GIT_ADDRESS:-}" ]]; then printf \'print("VIETNAM HOSTING Swift Ready")\\n\' > /mnt/server/main.swift; fi\n',
            variables=[
                VariableSpec("Executable Name", "SwiftPM release binary name under .build/release/.", "BIN_NAME", "App", rules="required|string|max:128"),
                VariableSpec("Fallback Swift File", "Swift script when Package.swift is absent.", "MAIN_FILE", "main.swift", rules="required|string|max:128"),
                VariableSpec("Auto Build Release", "Compile with `swift build -c release` on boot.", "AUTO_BUILD", "1", rules="required|boolean"),
                VariableSpec("Build Jobs", "Maximum parallel Swift compilation jobs.", "BUILD_JOBS", "2", rules="required|integer|between:1,4"),
                *GIT_DEPLOY_VARS,
            ],
            upstream_license="Apache-2.0",
            upstream_url="https://www.swift.org",
        ),

        # 22. Zig
        EggSpec(
            id="zig",
            name="Vietnam Hosting — Zig Hosting",
            category="languages",
            description="Zig 0.14 systems programming runtime with `zig build` ReleaseSafe support.",
            icon="zig",
            supported_versions=["0.14.0"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=512,
            recommended_ram_mb=1024,
            minimum_disk_mb=1024,
            image_source="requires_ghcr_build",
            dockerfile_path="docker/languages/zig/Dockerfile",
            docker_images={"Zig 0.14 (Vietnam Hosting GHCR)": f"{GHCR_NAMESPACE}:zig_0.14"},
            custom_docker_images={"Zig 0.14": f"{GHCR_NAMESPACE}:zig_0.14"},
            startup='if [[ -f build.zig ]]; then zig build -Doptimize=ReleaseSafe && exec "./zig-out/bin/${BIN_NAME}"; else exec zig run "${MAIN_FILE}"; fi',
            stop="^C",
            startup_done="Listening|Ready|VIETNAM HOSTING",
            install_body=GIT_INSTALL_SNIPPET + '\nif [[ ! -f /mnt/server/main.zig ]] && [[ -z "${GIT_ADDRESS:-}" ]]; then printf \'const std = @import("std");\\npub fn main() !void { std.debug.print("VIETNAM HOSTING Zig Ready\\n", .{}); }\\n\' > /mnt/server/main.zig; fi\n',
            variables=[
                VariableSpec("Output Binary Name", "Compiled binary under zig-out/bin/ when build.zig exists.", "BIN_NAME", "app", rules="required|string|max:128"),
                VariableSpec("Main Zig File", "Fallback .zig file when build.zig is absent.", "MAIN_FILE", "main.zig", rules="required|string|max:128"),
                *GIT_DEPLOY_VARS,
            ],
            upstream_license="MIT",
            upstream_url="https://ziglang.org",
        ),

        # 23. Julia
        EggSpec(
            id="julia",
            name="Vietnam Hosting — Julia Hosting",
            category="languages",
            description="Julia 1.11 scientific computing and web/API runtime with Project.toml environment isolation.",
            icon="julia",
            supported_versions=["1.11"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=512,
            recommended_ram_mb=1024,
            minimum_disk_mb=2048,
            image_source="requires_ghcr_build",
            dockerfile_path="docker/languages/julia/Dockerfile",
            docker_images={"Julia 1.11 (Vietnam Hosting GHCR)": f"{GHCR_NAMESPACE}:julia_1.11"},
            custom_docker_images={"Julia 1.11": f"{GHCR_NAMESPACE}:julia_1.11"},
            startup='if [[ -f Project.toml ]]; then julia --project=. -e "using Pkg; Pkg.instantiate()"; exec julia --project=. "${MAIN_FILE}"; else exec julia "${MAIN_FILE}"; fi',
            stop="^C",
            startup_done="Listening|Ready|VIETNAM HOSTING",
            install_body=GIT_INSTALL_SNIPPET + '\nif [[ ! -f /mnt/server/main.jl ]] && [[ -z "${GIT_ADDRESS:-}" ]]; then printf \'println("VIETNAM HOSTING Julia ", VERSION, " Ready")\\n\' > /mnt/server/main.jl; fi\n',
            variables=[VariableSpec("Main Julia File", "Entrypoint .jl script.", "MAIN_FILE", "main.jl", rules="required|string|max:128"), *GIT_DEPLOY_VARS],
            upstream_license="MIT",
            upstream_url="https://julialang.org",
        ),

        # 24. R Language
        EggSpec(
            id="r-lang",
            name="Vietnam Hosting — R Language Hosting",
            category="languages",
            description="R 4.4 statistical computing and Shiny/Plumber API runtime with user-space package library under ~/R/library.",
            icon="r",
            supported_versions=["4.4"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=512,
            recommended_ram_mb=1024,
            minimum_disk_mb=1024,
            image_source="requires_ghcr_build",
            dockerfile_path="docker/languages/r-lang/Dockerfile",
            docker_images={"R 4.4 (Vietnam Hosting GHCR)": f"{GHCR_NAMESPACE}:r_4.4"},
            custom_docker_images={"R 4.4": f"{GHCR_NAMESPACE}:r_4.4"},
            startup='mkdir -p /home/container/R/library; exec Rscript "${MAIN_FILE}"',
            stop="^C",
            startup_done="Running|Listening|Ready|VIETNAM HOSTING",
            install_body=GIT_INSTALL_SNIPPET + '\nmkdir -p /mnt/server/R/library\nif [[ ! -f /mnt/server/main.R ]] && [[ -z "${GIT_ADDRESS:-}" ]]; then printf \'cat("VIETNAM HOSTING R Runtime Ready\\n")\\n\' > /mnt/server/main.R; fi\n',
            variables=[VariableSpec("Main R Script", "Entrypoint .R file.", "MAIN_FILE", "main.R", rules="required|string|max:128"), *GIT_DEPLOY_VARS],
            upstream_license="GPL-2.0-or-later",
            upstream_url="https://www.r-project.org",
        ),

        # 25. Bash Shell
        EggSpec(
            id="bash",
            name="Vietnam Hosting — Bash Shell Hosting",
            category="languages",
            description="Unprivileged GNU Bash automation and scripting runtime on Debian 13 with curl, jq, rsync, and OpenSSL.",
            icon="bash",
            supported_versions=["Bash 5.2 (Debian 13)"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=128,
            recommended_ram_mb=256,
            minimum_disk_mb=512,
            image_source="hybrid_official_and_ghcr",
            dockerfile_path="docker/languages/bash/Dockerfile",
            docker_images={
                "Debian Official Yolk": "ghcr.io/pterodactyl/yolks:debian",
                "Bash Debian 13 (Vietnam Hosting GHCR - Build Required)": f"{GHCR_NAMESPACE}:bash_debian13",
            },
            custom_docker_images={"Bash Debian 13": f"{GHCR_NAMESPACE}:bash_debian13"},
            startup='exec /bin/bash "${MAIN_FILE}"',
            stop="^C",
            startup_done="Ready|VIETNAM HOSTING",
            install_body=GIT_INSTALL_SNIPPET + '\nif [[ ! -f /mnt/server/main.sh ]] && [[ -z "${GIT_ADDRESS:-}" ]]; then printf \'#!/usr/bin/env bash\\nset -euo pipefail\\necho "VIETNAM HOSTING Bash Ready"\\n\' > /mnt/server/main.sh; chmod +x /mnt/server/main.sh; fi\n',
            variables=[VariableSpec("Main Shell Script", "Relative path to the Bash script to execute.", "MAIN_FILE", "main.sh", rules="required|string|max:128"), *GIT_DEPLOY_VARS],
            upstream_license="GPL-3.0-or-later",
            upstream_url="https://www.gnu.org/software/bash/",
            requires_inbound_port=False,
        ),

        # 26. PowerShell
        EggSpec(
            id="powershell",
            name="Vietnam Hosting — PowerShell Hosting",
            category="languages",
            description="Cross-platform PowerShell 7.5 runtime for automation scripts, API integrations, and scheduled DevOps jobs.",
            icon="powershell",
            supported_versions=["7.5"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=256,
            recommended_ram_mb=512,
            minimum_disk_mb=1024,
            image_source="requires_ghcr_build",
            dockerfile_path="docker/languages/powershell/Dockerfile",
            docker_images={"PowerShell 7.5 (Vietnam Hosting GHCR)": f"{GHCR_NAMESPACE}:powershell_7.5"},
            custom_docker_images={"PowerShell 7.5": f"{GHCR_NAMESPACE}:powershell_7.5"},
            startup='exec pwsh -NoLogo -NoProfile -File "${MAIN_FILE}"',
            stop="^C",
            startup_done="Ready|VIETNAM HOSTING",
            install_body=GIT_INSTALL_SNIPPET + '\nif [[ ! -f /mnt/server/main.ps1 ]] && [[ -z "${GIT_ADDRESS:-}" ]]; then printf \'Write-Output "VIETNAM HOSTING PowerShell $($PSVersionTable.PSVersion) Ready"\\n\' > /mnt/server/main.ps1; fi\n',
            variables=[VariableSpec("Main PowerShell Script", "Entrypoint .ps1 file.", "MAIN_FILE", "main.ps1", rules="required|string|max:128"), *GIT_DEPLOY_VARS],
            upstream_license="MIT",
            upstream_url="https://github.com/PowerShell/PowerShell",
            requires_inbound_port=False,
        ),
    ]
