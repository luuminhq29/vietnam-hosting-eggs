"""Phase 4A: All 17 Discord Bot & Automation Worker Egg Specifications."""

from __future__ import annotations

from generator.models import GHCR_NAMESPACE, EggSpec, VariableSpec
from generator.specs.common import GIT_DEPLOY_VARS, GIT_INSTALL_SNIPPET

BOT_SECURITY_VI = (
    "- **Bảo vệ Token / API Key:** Token Bot (`DISCORD_TOKEN` / `TELEGRAM_BOT_TOKEN` / `BOT_TOKEN`) được truyền qua biến môi trường và tuyệt đối không được in ra console.\n"
    "- **Tuân thủ Rate Limit & Chính sách nền tảng:** Không tự động đổi IP để né lệnh cấm API; áp dụng cơ chế reconnect với exponential backoff chống vòng lặp lỗi.\n"
    "- **Outbound-Only:** Không yêu cầu mở port inbound bổ sung nếu bot chỉ kết nối outbound tới Discord/Telegram Gateway."
)


def _py_bot_egg(egg_id: str, title: str, pkg: str, token_env: str, token_label: str, upstream: str, lic: str) -> EggSpec:
    return EggSpec(
        id=egg_id,
        name=f"Vietnam Hosting — {title}",
        category="discord-bots",
        description=(
            f"Dedicated {title} hosting with isolated Python .venv, automatic dependency install, "
            f"Git deployment, secret-safe token handling, and exponential-backoff supervision."
        ),
        icon=egg_id,
        supported_versions=["Python 3.11", "Python 3.12", "Python 3.13", "Python 3.14"],
        supported_architectures=["amd64", "arm64"],
        minimum_ram_mb=128,
        recommended_ram_mb=256,
        minimum_disk_mb=512,
        image_source="hybrid_official_and_ghcr",
        dockerfile_path="docker/languages/python/3.13/Dockerfile",
        docker_images={
            "Python 3.13 (Official Yolk)": "ghcr.io/pterodactyl/yolks:python_3.13",
            "Python 3.12 (Official Yolk)": "ghcr.io/pterodactyl/yolks:python_3.12",
            "Python 3.14 (Vietnam Hosting GHCR - Build Required)": f"{GHCR_NAMESPACE}:python_3.14",
        },
        custom_docker_images={"Python 3.13": f"{GHCR_NAMESPACE}:python_3.13", "Python 3.14": f"{GHCR_NAMESPACE}:python_3.14"},
        startup=(
            'export VNH_SUPERVISE="${ENABLE_BACKOFF}"; '
            'if [[ ! -d .venv ]]; then python3 -m venv .venv; fi; source .venv/bin/activate; '
            'if [[ "${INSTALL_DEPS}" == "1" ]] && [[ -f "${REQUIREMENTS_FILE}" ]]; then pip install --no-cache-dir -r "${REQUIREMENTS_FILE}"; fi; '
            'exec python3 "${BOT_FILE}"'
        ),
        stop="^C",
        startup_done="Logged in as|Bot started|Application started|Ready|VIETNAM HOSTING",
        install_body=GIT_INSTALL_SNIPPET + f'''
if [[ ! -f /mnt/server/requirements.txt ]] && [[ -z "${{GIT_ADDRESS:-}}" ]]; then
    printf '{pkg}\\npython-dotenv\\n' > /mnt/server/requirements.txt
fi
if [[ ! -f /mnt/server/bot.py ]] && [[ -z "${{GIT_ADDRESS:-}}" ]]; then
    cat > /mnt/server/bot.py <<'EOF'
import os, sys
token = os.environ.get("{token_env}", "")
if not token:
    print("VIETNAM HOSTING Bot Ready — configure {token_env} in Startup variables (never commit tokens).", flush=True)
    sys.exit(0)
print("VIETNAM HOSTING {title} bootstrap ready. Replace bot.py with your bot code.", flush=True)
EOF
fi
''',
        variables=[
            VariableSpec("Bot Entrypoint File", "Main Python script path inside /home/container.", "BOT_FILE", "bot.py", rules="required|string|max:128"),
            VariableSpec(token_label, "Bot authentication token passed as environment variable (never logged).", token_env, "", rules="nullable|string|max:256"),
            VariableSpec("Requirements File", "Python dependencies file.", "REQUIREMENTS_FILE", "requirements.txt", rules="nullable|string|max:128"),
            VariableSpec("Auto Install Dependencies", "Install requirements.txt into .venv before starting.", "INSTALL_DEPS", "1", rules="required|boolean"),
            VariableSpec("Exponential Backoff Supervisor", "Restart gracefully with exponential backoff (capped at 5/min).", "ENABLE_BACKOFF", "1", rules="required|boolean"),
            *GIT_DEPLOY_VARS,
        ],
        requires_inbound_port=False,
        upstream_license=lic,
        upstream_url=upstream,
        security_notes_vi=BOT_SECURITY_VI,
    )


def _node_bot_egg(egg_id: str, title: str, pkg: str, token_env: str, token_label: str, upstream: str, lic: str) -> EggSpec:
    return EggSpec(
        id=egg_id,
        name=f"Vietnam Hosting — {title}",
        category="discord-bots",
        description=(
            f"Dedicated {title} hosting on Node.js LTS with NPM/Yarn/PNPM lockfile support, "
            f"Git deployment, secret-safe token environment handling, and clean SIGTERM shutdown."
        ),
        icon=egg_id,
        supported_versions=["Node.js 22 LTS", "Node.js 24 LTS", "Node.js 26 LTS"],
        supported_architectures=["amd64", "arm64"],
        minimum_ram_mb=256,
        recommended_ram_mb=512,
        minimum_disk_mb=1024,
        image_source="hybrid_official_and_ghcr",
        dockerfile_path="docker/languages/nodejs/24/Dockerfile",
        docker_images={
            "Node.js 24 LTS (Official Yolk)": "ghcr.io/pterodactyl/yolks:nodejs_24",
            "Node.js 22 LTS (Official Yolk)": "ghcr.io/pterodactyl/yolks:nodejs_22",
            "Node.js 26 LTS (Vietnam Hosting GHCR - Build Required)": f"{GHCR_NAMESPACE}:nodejs_26",
        },
        custom_docker_images={"Node.js 24 LTS": f"{GHCR_NAMESPACE}:nodejs_24", "Node.js 26 LTS": f"{GHCR_NAMESPACE}:nodejs_26"},
        startup=(
            'export NODE_ENV=production VNH_SUPERVISE="${ENABLE_BACKOFF}"; '
            'if [[ -f package.json ]] && [[ "${INSTALL_DEPS}" == "1" ]]; then '
            '  if [[ -f pnpm-lock.yaml ]]; then pnpm install --frozen-lockfile || pnpm install; '
            '  elif [[ -f yarn.lock ]]; then yarn install --frozen-lockfile || yarn install; '
            '  elif [[ -f package-lock.json ]]; then npm ci --omit=dev || npm install --omit=dev; '
            '  else npm install --omit=dev; fi; '
            'fi; '
            'if [[ -n "${BUILD_SCRIPT}" ]] && [[ -f package.json ]]; then npm run "${BUILD_SCRIPT}"; fi; '
            'exec node "${BOT_FILE}"'
        ),
        stop="^C",
        startup_done="Logged in as|Bot ready|Ready|VIETNAM HOSTING",
        install_body=GIT_INSTALL_SNIPPET + f'''
if [[ ! -f /mnt/server/package.json ]] && [[ -z "${{GIT_ADDRESS:-}}" ]]; then
    cat > /mnt/server/package.json <<'EOF'
{{
  "name": "vnh-{egg_id}",
  "version": "1.0.0",
  "private": true,
  "dependencies": {{ "{pkg}": "latest" }}
}}
EOF
fi
if [[ ! -f /mnt/server/index.js ]] && [[ -z "${{GIT_ADDRESS:-}}" ]]; then
    printf 'console.log("VIETNAM HOSTING {title} Ready — set {token_env} and upload your bot code.");\\n' > /mnt/server/index.js
fi
''',
        variables=[
            VariableSpec("Bot Entrypoint File", "Main JS entrypoint inside /home/container.", "BOT_FILE", "index.js", rules="required|string|max:128"),
            VariableSpec(token_label, "Bot token supplied via environment variable (never logged).", token_env, "", rules="nullable|string|max:256"),
            VariableSpec("Build Script", "Optional TypeScript/package.json build script name.", "BUILD_SCRIPT", "", rules="nullable|string|max:64"),
            VariableSpec("Auto Install Dependencies", "Install npm/yarn/pnpm dependencies on boot.", "INSTALL_DEPS", "1", rules="required|boolean"),
            VariableSpec("Exponential Backoff Supervisor", "Enable bounded exponential backoff restarts.", "ENABLE_BACKOFF", "1", rules="required|boolean"),
            *GIT_DEPLOY_VARS,
        ],
        requires_inbound_port=False,
        upstream_license=lic,
        upstream_url=upstream,
        security_notes_vi=BOT_SECURITY_VI,
    )


def get_specs() -> list[EggSpec]:
    return [
        # 1-3 Python Discord bots
        _py_bot_egg("discord-py", "Discord.py Bot", "discord.py>=2.4.0", "DISCORD_TOKEN", "Discord Bot Token", "https://github.com/Rapptz/discord.py", "MIT"),
        _py_bot_egg("pycord", "Pycord Bot", "py-cord>=2.6.0", "DISCORD_TOKEN", "Discord Bot Token", "https://github.com/Pycord-Development/pycord", "MIT"),
        _py_bot_egg("nextcord", "Nextcord Bot", "nextcord>=2.6.0", "DISCORD_TOKEN", "Discord Bot Token", "https://github.com/nextcord/nextcord", "MIT"),
        # 4-5 Node.js Discord bots
        _node_bot_egg("discord-js", "Discord.js Bot", "discord.js", "DISCORD_TOKEN", "Discord Bot Token", "https://discord.js.org", "Apache-2.0"),
        _node_bot_egg("eris", "Eris Discord Bot", "eris", "DISCORD_TOKEN", "Discord Bot Token", "https://abal.moe/Eris/", "MIT"),
        # 6. JDA (Java)
        EggSpec(
            id="jda",
            name="Vietnam Hosting — JDA Discord Bot (Java)",
            category="discord-bots",
            description="Java Discord API (JDA) bot hosting with automatic JVM heap headroom, Maven/Gradle build, and Git deployment.",
            icon="jda",
            supported_versions=["Java 17", "Java 21 LTS", "Java 25 LTS"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=512,
            recommended_ram_mb=1024,
            minimum_disk_mb=1024,
            image_source="hybrid_official_and_ghcr",
            dockerfile_path="docker/languages/java/21/Dockerfile",
            features=["java_version", "pid_limit"],
            docker_images={
                "Java 21 LTS (Official Yolk)": "ghcr.io/pterodactyl/yolks:java_21",
                "Java 25 LTS (Official Yolk)": "ghcr.io/pterodactyl/yolks:java_25",
                "Java 17 LTS (Official Yolk)": "ghcr.io/pterodactyl/yolks:java_17",
            },
            custom_docker_images={"Java 21 LTS": f"{GHCR_NAMESPACE}:java_21", "Java 25 LTS": f"{GHCR_NAMESPACE}:java_25"},
            startup='MEM={{SERVER_MEMORY}}; HEAP=$(( MEM * 75 / 100 )); (( HEAP < 128 )) && HEAP=128; exec java -Xms128M -Xmx"${HEAP}M" -XX:+UseG1GC -jar "${BOT_JAR}"',
            stop="^C",
            startup_done="Finished Loading!|Login Successful|Ready|VIETNAM HOSTING",
            install_body=GIT_INSTALL_SNIPPET + '\necho "[VNH][INSTALL] Upload your shaded JDA JAR (bot.jar) and configure DISCORD_TOKEN."\n',
            variables=[
                VariableSpec("Bot JAR File", "Executable JDA JAR filename.", "BOT_JAR", "bot.jar", rules="required|string|max:128"),
                VariableSpec("Discord Bot Token", "Bot token passed to JVM via DISCORD_TOKEN env var.", "DISCORD_TOKEN", "", rules="nullable|string|max:256"),
                *GIT_DEPLOY_VARS,
            ],
            requires_inbound_port=False,
            upstream_license="Apache-2.0",
            upstream_url="https://github.com/discord-jda/JDA",
            security_notes_vi=BOT_SECURITY_VI,
        ),
        # 7. Discord.NET
        EggSpec(
            id="discord-net",
            name="Vietnam Hosting — Discord.NET Bot",
            category="discord-bots",
            description="Discord.NET C# bot hosting on .NET LTS/STS with Release publish and secure token env injection.",
            icon="dotnet",
            supported_versions=[".NET 8.0", ".NET 10.0 LTS", ".NET 11.0 STS"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=256,
            recommended_ram_mb=512,
            minimum_disk_mb=1024,
            image_source="requires_ghcr_build",
            dockerfile_path="docker/languages/dotnet/10/Dockerfile",
            docker_images={
                ".NET 10.0 LTS (Vietnam Hosting GHCR)": f"{GHCR_NAMESPACE}:dotnet_10",
                ".NET 8.0 (Vietnam Hosting GHCR)": f"{GHCR_NAMESPACE}:dotnet_8",
            },
            custom_docker_images={".NET 10.0 LTS": f"{GHCR_NAMESPACE}:dotnet_10"},
            startup='if [[ -n "${PROJECT_FILE}" ]] && [[ -f "${PROJECT_FILE}" ]]; then dotnet publish "${PROJECT_FILE}" -c Release -o ./out --nologo; fi; if [[ -f "./out/${BOT_DLL}" ]]; then exec dotnet "./out/${BOT_DLL}"; else exec dotnet "./${BOT_DLL}"; fi',
            stop="^C",
            startup_done="Connected|Ready|Gateway|VIETNAM HOSTING",
            install_body=GIT_INSTALL_SNIPPET + '\nmkdir -p /mnt/server/out\n',
            variables=[
                VariableSpec("Project File", "Optional .csproj file to build on start.", "PROJECT_FILE", "", rules="nullable|string|max:191"),
                VariableSpec("Bot Assembly DLL", "Compiled .NET DLL filename.", "BOT_DLL", "Bot.dll", rules="required|string|max:191"),
                VariableSpec("Discord Bot Token", "Bot token via DISCORD_TOKEN env var.", "DISCORD_TOKEN", "", rules="nullable|string|max:256"),
                *GIT_DEPLOY_VARS,
            ],
            requires_inbound_port=False,
            upstream_license="MIT",
            upstream_url="https://github.com/discord-net/Discord.Net",
            security_notes_vi=BOT_SECURITY_VI,
        ),
        # 8. DSharpPlus
        EggSpec(
            id="dsharpplus",
            name="Vietnam Hosting — DSharpPlus Bot",
            category="discord-bots",
            description="DSharpPlus C#/.NET Discord bot hosting with Release publish and secret-safe token injection.",
            icon="dotnet",
            supported_versions=[".NET 8.0", ".NET 10.0 LTS", ".NET 11.0 STS"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=256,
            recommended_ram_mb=512,
            minimum_disk_mb=1024,
            image_source="requires_ghcr_build",
            dockerfile_path="docker/languages/dotnet/10/Dockerfile",
            docker_images={".NET 10.0 LTS (Vietnam Hosting GHCR)": f"{GHCR_NAMESPACE}:dotnet_10"},
            custom_docker_images={".NET 10.0 LTS": f"{GHCR_NAMESPACE}:dotnet_10"},
            startup='if [[ -n "${PROJECT_FILE}" ]] && [[ -f "${PROJECT_FILE}" ]]; then dotnet publish "${PROJECT_FILE}" -c Release -o ./out --nologo; fi; if [[ -f "./out/${BOT_DLL}" ]]; then exec dotnet "./out/${BOT_DLL}"; else exec dotnet "./${BOT_DLL}"; fi',
            stop="^C",
            startup_done="Session resumed|Ready|Connected|VIETNAM HOSTING",
            install_body=GIT_INSTALL_SNIPPET + '\nmkdir -p /mnt/server/out\n',
            variables=[
                VariableSpec("Project File", "Optional .csproj file to build.", "PROJECT_FILE", "", rules="nullable|string|max:191"),
                VariableSpec("Bot Assembly DLL", "Compiled DSharpPlus DLL.", "BOT_DLL", "Bot.dll", rules="required|string|max:191"),
                VariableSpec("Discord Bot Token", "Bot token via DISCORD_TOKEN env var.", "DISCORD_TOKEN", "", rules="nullable|string|max:256"),
                *GIT_DEPLOY_VARS,
            ],
            requires_inbound_port=False,
            upstream_license="MIT",
            upstream_url="https://dsharpplus.github.io",
            security_notes_vi=BOT_SECURITY_VI,
        ),
        # 9. Serenity Rust
        EggSpec(
            id="serenity-rust",
            name="Vietnam Hosting — Serenity Rust Discord Bot",
            category="discord-bots",
            description="Serenity Rust Discord bot hosting with bounded CARGO_BUILD_JOBS compilation and native release binary execution.",
            icon="rust",
            supported_versions=["Rust Stable 1.86"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=1024,
            recommended_ram_mb=2048,
            minimum_disk_mb=2048,
            image_source="requires_ghcr_build",
            dockerfile_path="docker/languages/rust/stable/Dockerfile",
            docker_images={"Rust Stable 1.86 (Vietnam Hosting GHCR)": f"{GHCR_NAMESPACE}:rust_stable"},
            custom_docker_images={"Rust Stable 1.86": f"{GHCR_NAMESPACE}:rust_stable"},
            startup='export CARGO_BUILD_JOBS="${BUILD_JOBS}"; if [[ -f Cargo.toml ]] && [[ "${AUTO_BUILD}" == "1" ]]; then cargo build --release --jobs "${BUILD_JOBS}"; fi; exec "./target/release/${BIN_NAME}"',
            stop="^C",
            startup_done="is connected|Ready|VIETNAM HOSTING",
            install_body=GIT_INSTALL_SNIPPET + '\nmkdir -p /mnt/server/target/release\n',
            variables=[
                VariableSpec("Binary Name", "Compiled Serenity binary under target/release/.", "BIN_NAME", "bot", rules="required|string|max:128"),
                VariableSpec("Discord Bot Token", "Token injected as DISCORD_TOKEN.", "DISCORD_TOKEN", "", rules="nullable|string|max:256"),
                VariableSpec("Auto Build Release", "Compile with `cargo build --release` on boot.", "AUTO_BUILD", "1", rules="required|boolean"),
                VariableSpec("Cargo Build Jobs", "Max parallel compile threads.", "BUILD_JOBS", "2", rules="required|integer|between:1,4"),
                *GIT_DEPLOY_VARS,
            ],
            requires_inbound_port=False,
            upstream_license="ISC",
            upstream_url="https://github.com/serenity-rs/serenity",
            security_notes_vi=BOT_SECURITY_VI,
        ),
        # 10. Twilight Rust
        EggSpec(
            id="twilight-rust",
            name="Vietnam Hosting — Twilight Rust Discord Bot",
            category="discord-bots",
            description="Twilight modular Rust Discord bot hosting with release compilation and CPU-bounded Cargo jobs.",
            icon="rust",
            supported_versions=["Rust Stable 1.86"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=1024,
            recommended_ram_mb=2048,
            minimum_disk_mb=2048,
            image_source="requires_ghcr_build",
            dockerfile_path="docker/languages/rust/stable/Dockerfile",
            docker_images={"Rust Stable 1.86 (Vietnam Hosting GHCR)": f"{GHCR_NAMESPACE}:rust_stable"},
            custom_docker_images={"Rust Stable 1.86": f"{GHCR_NAMESPACE}:rust_stable"},
            startup='export CARGO_BUILD_JOBS="${BUILD_JOBS}"; if [[ -f Cargo.toml ]] && [[ "${AUTO_BUILD}" == "1" ]]; then cargo build --release --jobs "${BUILD_JOBS}"; fi; exec "./target/release/${BIN_NAME}"',
            stop="^C",
            startup_done="Shard ready|Connected|Ready|VIETNAM HOSTING",
            install_body=GIT_INSTALL_SNIPPET + '\nmkdir -p /mnt/server/target/release\n',
            variables=[
                VariableSpec("Binary Name", "Compiled Twilight binary under target/release/.", "BIN_NAME", "bot", rules="required|string|max:128"),
                VariableSpec("Discord Bot Token", "Token injected as DISCORD_TOKEN.", "DISCORD_TOKEN", "", rules="nullable|string|max:256"),
                VariableSpec("Auto Build Release", "Compile with `cargo build --release` on boot.", "AUTO_BUILD", "1", rules="required|boolean"),
                VariableSpec("Cargo Build Jobs", "Max parallel compile threads.", "BUILD_JOBS", "2", rules="required|integer|between:1,4"),
                *GIT_DEPLOY_VARS,
            ],
            requires_inbound_port=False,
            upstream_license="ISC",
            upstream_url="https://twilight.rs",
            security_notes_vi=BOT_SECURITY_VI,
        ),
        # 11. DiscordGo
        EggSpec(
            id="discordgo",
            name="Vietnam Hosting — DiscordGo Bot",
            category="discord-bots",
            description="Lightweight Go Discord bot hosting using DiscordGo with go.mod builds and minimal RAM footprint.",
            icon="go",
            supported_versions=["Go 1.23", "Go 1.25"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=128,
            recommended_ram_mb=256,
            minimum_disk_mb=512,
            image_source="hybrid_official_and_ghcr",
            dockerfile_path="docker/languages/go/1.25/Dockerfile",
            docker_images={
                "Go 1.23 (Official Yolk)": "ghcr.io/pterodactyl/yolks:go_1.23",
                "Go 1.25 (Vietnam Hosting GHCR - Build Required)": f"{GHCR_NAMESPACE}:go_1.25",
            },
            custom_docker_images={"Go 1.25": f"{GHCR_NAMESPACE}:go_1.25"},
            startup='if [[ -f go.mod ]] && [[ "${AUTO_BUILD}" == "1" ]]; then go build -trimpath -ldflags="-s -w" -o "./${BIN_NAME}" .; fi; exec "./${BIN_NAME}"',
            stop="^C",
            startup_done="Bot is now running|Ready|VIETNAM HOSTING",
            install_body=GIT_INSTALL_SNIPPET + '\necho "[VNH][INSTALL] Upload your DiscordGo module and configure DISCORD_TOKEN."\n',
            variables=[
                VariableSpec("Binary Name", "Compiled DiscordGo binary name.", "BIN_NAME", "bot", rules="required|string|max:128"),
                VariableSpec("Discord Bot Token", "Bot token injected via DISCORD_TOKEN.", "DISCORD_TOKEN", "", rules="nullable|string|max:256"),
                VariableSpec("Auto Build", "Compile Go binary before running.", "AUTO_BUILD", "1", rules="required|boolean"),
                *GIT_DEPLOY_VARS,
            ],
            requires_inbound_port=False,
            upstream_license="BSD-3-Clause",
            upstream_url="https://github.com/bwmarrin/discordgo",
            security_notes_vi=BOT_SECURITY_VI,
        ),
        # 12-13. Telegram Bots (Python & Node.js)
        _py_bot_egg("telegram-bot-python", "Telegram Bot (Python)", "python-telegram-bot>=21.0", "TELEGRAM_BOT_TOKEN", "Telegram Bot Token", "https://python-telegram-bot.org", "LGPL-3.0"),
        _node_bot_egg("telegram-bot-nodejs", "Telegram Bot (Node.js)", "grammy", "TELEGRAM_BOT_TOKEN", "Telegram Bot Token", "https://grammy.dev", "MIT"),
        # 14. Generic Bot Hosting
        EggSpec(
            id="generic-bot",
            name="Vietnam Hosting — Generic Bot Hosting",
            category="discord-bots",
            description="Multi-runtime outbound bot container supporting Python, Node.js, or compiled binaries with restart-loop protection.",
            icon="robot",
            supported_versions=["Debian 13 / Python / Node.js"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=256,
            recommended_ram_mb=512,
            minimum_disk_mb=1024,
            image_source="hybrid_official_and_ghcr",
            dockerfile_path="docker/base/debian-13/Dockerfile",
            docker_images={
                "Python 3.13 (Official Yolk)": "ghcr.io/pterodactyl/yolks:python_3.13",
                "Node.js 24 LTS (Official Yolk)": "ghcr.io/pterodactyl/yolks:nodejs_24",
                "Debian Official Yolk": "ghcr.io/pterodactyl/yolks:debian",
            },
            custom_docker_images={"Base Debian 13": f"{GHCR_NAMESPACE}:base_debian13"},
            startup='export VNH_SUPERVISE=1; exec /bin/bash "${START_SCRIPT}"',
            stop="^C",
            startup_done="Ready|Started|VIETNAM HOSTING",
            install_body=GIT_INSTALL_SNIPPET + '\nif [[ ! -f /mnt/server/start.sh ]]; then printf \'#!/usr/bin/env bash\\nset -euo pipefail\\necho "VIETNAM HOSTING Generic Bot Ready"\\n\' > /mnt/server/start.sh; chmod +x /mnt/server/start.sh; fi\n',
            variables=[
                VariableSpec("Start Script", "Relative startup shell script inside /home/container.", "START_SCRIPT", "start.sh", rules="required|string|max:128"),
                VariableSpec("Bot API Token", "Secret token exported as BOT_TOKEN (never printed).", "BOT_TOKEN", "", rules="nullable|string|max:256"),
                *GIT_DEPLOY_VARS,
            ],
            requires_inbound_port=False,
            upstream_license="MIT",
            upstream_url="https://vietnam-hosting.net",
            security_notes_vi=BOT_SECURITY_VI,
        ),
        # 15. Automation Worker
        EggSpec(
            id="automation-worker",
            name="Vietnam Hosting — Automation Worker",
            category="discord-bots",
            description="Outbound automation worker for API polling, ETL syncs, and webhooks using Python .venv with exponential backoff.",
            icon="workflow",
            supported_versions=["Python 3.12", "Python 3.13", "Python 3.14"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=256,
            recommended_ram_mb=512,
            minimum_disk_mb=1024,
            image_source="hybrid_official_and_ghcr",
            dockerfile_path="docker/languages/python/3.13/Dockerfile",
            docker_images={"Python 3.13 (Official Yolk)": "ghcr.io/pterodactyl/yolks:python_3.13"},
            custom_docker_images={"Python 3.13": f"{GHCR_NAMESPACE}:python_3.13"},
            startup='export VNH_SUPERVISE=1; if [[ ! -d .venv ]]; then python3 -m venv .venv; fi; source .venv/bin/activate; if [[ -f requirements.txt ]]; then pip install --no-cache-dir -r requirements.txt; fi; exec python3 "${WORKER_FILE}"',
            stop="^C",
            startup_done="Worker ready|Listening|VIETNAM HOSTING",
            install_body=GIT_INSTALL_SNIPPET + '\nif [[ ! -f /mnt/server/worker.py ]] && [[ -z "${GIT_ADDRESS:-}" ]]; then printf \'import time\\nprint("VIETNAM HOSTING Automation Worker Ready", flush=True)\\nwhile True: time.sleep(60)\\n\' > /mnt/server/worker.py; fi\n',
            variables=[
                VariableSpec("Worker Entrypoint", "Main Python worker script.", "WORKER_FILE", "worker.py", rules="required|string|max:128"),
                VariableSpec("API Key", "Optional outbound service API key (never logged).", "API_KEY", "", rules="nullable|string|max:256"),
                *GIT_DEPLOY_VARS,
            ],
            requires_inbound_port=False,
            upstream_license="MIT",
            upstream_url="https://vietnam-hosting.net",
            security_notes_vi=BOT_SECURITY_VI,
        ),
        # 16. Background Worker
        EggSpec(
            id="background-worker",
            name="Vietnam Hosting — Background Worker",
            category="discord-bots",
            description="Long-running background job consumer (Celery, BullMQ, Dramatiq, or custom worker) with graceful SIGTERM drain.",
            icon="cogs",
            supported_versions=["Python 3.13", "Node.js 24 LTS"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=256,
            recommended_ram_mb=512,
            minimum_disk_mb=1024,
            image_source="hybrid_official_and_ghcr",
            dockerfile_path="docker/languages/python/3.13/Dockerfile",
            docker_images={
                "Python 3.13 (Official Yolk)": "ghcr.io/pterodactyl/yolks:python_3.13",
                "Node.js 24 LTS (Official Yolk)": "ghcr.io/pterodactyl/yolks:nodejs_24",
            },
            custom_docker_images={"Python 3.13": f"{GHCR_NAMESPACE}:python_3.13", "Node.js 24 LTS": f"{GHCR_NAMESPACE}:nodejs_24"},
            startup='exec /bin/bash "${WORKER_SCRIPT}"',
            stop="^C",
            startup_done="Worker ready|Connected|VIETNAM HOSTING",
            install_body=GIT_INSTALL_SNIPPET + '\nif [[ ! -f /mnt/server/run-worker.sh ]]; then printf \'#!/usr/bin/env bash\\nset -euo pipefail\\necho "VIETNAM HOSTING Background Worker Ready"\\nexec sleep infinity\\n\' > /mnt/server/run-worker.sh; chmod +x /mnt/server/run-worker.sh; fi\n',
            variables=[
                VariableSpec("Worker Launch Script", "Shell script starting your worker process via `exec`.", "WORKER_SCRIPT", "run-worker.sh", rules="required|string|max:128"),
                VariableSpec("Broker URL", "Queue broker connection URI (redacted in logs).", "BROKER_URL", "", rules="nullable|string|max:512"),
                *GIT_DEPLOY_VARS,
            ],
            requires_inbound_port=False,
            upstream_license="MIT",
            upstream_url="https://vietnam-hosting.net",
            security_notes_vi=BOT_SECURITY_VI,
        ),
        # 17. Scheduled Script Hosting
        EggSpec(
            id="scheduled-script",
            name="Vietnam Hosting — Scheduled Script Hosting",
            category="discord-bots",
            description="Container-native interval task runner executing Bash/Python/Node scripts on a schedule without root crond/systemd.",
            icon="clock",
            supported_versions=["Debian 13 / Python 3.13 / Node.js 24"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=128,
            recommended_ram_mb=256,
            minimum_disk_mb=512,
            image_source="hybrid_official_and_ghcr",
            dockerfile_path="docker/base/debian-13/Dockerfile",
            docker_images={
                "Debian Official Yolk": "ghcr.io/pterodactyl/yolks:debian",
                "Python 3.13 (Official Yolk)": "ghcr.io/pterodactyl/yolks:python_3.13",
                "Node.js 24 LTS (Official Yolk)": "ghcr.io/pterodactyl/yolks:nodejs_24",
            },
            custom_docker_images={"Base Debian 13": f"{GHCR_NAMESPACE}:base_debian13"},
            startup=(
                'echo "VIETNAM HOSTING Scheduled Script Runner Ready (interval=${INTERVAL_SECONDS}s)"; '
                'trap "exit 0" TERM INT; '
                'while true; do /bin/bash "${JOB_SCRIPT}" || echo "[VNH][WARN] Job exited non-zero"; sleep "${INTERVAL_SECONDS}"; done'
            ),
            stop="^C",
            startup_done="VIETNAM HOSTING Scheduled Script Runner Ready",
            install_body=GIT_INSTALL_SNIPPET + '\nif [[ ! -f /mnt/server/job.sh ]]; then printf \'#!/usr/bin/env bash\\nset -euo pipefail\\ndate -u +"%%Y-%%m-%%dT%%H:%%M:%%SZ — scheduled task executed"\\n\' > /mnt/server/job.sh; chmod +x /mnt/server/job.sh; fi\n',
            variables=[
                VariableSpec("Job Script Path", "Script executed each interval.", "JOB_SCRIPT", "job.sh", rules="required|string|max:128"),
                VariableSpec("Interval Seconds", "Delay in seconds between executions (minimum 10).", "INTERVAL_SECONDS", "300", rules="required|integer|between:10,86400"),
                *GIT_DEPLOY_VARS,
            ],
            requires_inbound_port=False,
            upstream_license="MIT",
            upstream_url="https://vietnam-hosting.net",
            security_notes_vi=BOT_SECURITY_VI,
        ),
    ]
