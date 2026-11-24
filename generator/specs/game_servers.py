"""Phase 5A: All 29 Game Server Egg Specifications (13 Minecraft + 16 Other Games)."""

from __future__ import annotations

from generator.models import GHCR_NAMESPACE, EggSpec, VariableSpec
from generator.specs.common import SAFE_DOWNLOAD_HELPER, STEAMCMD_INSTALL_SNIPPET

MC_JAVA_IMAGES = {
    "Java 21 LTS (Official Yolk)": "ghcr.io/pterodactyl/yolks:java_21",
    "Java 25 LTS (Official Yolk)": "ghcr.io/pterodactyl/yolks:java_25",
    "Java 17 LTS (Official Yolk)": "ghcr.io/pterodactyl/yolks:java_17",
    "Java 11 LTS (Official Yolk)": "ghcr.io/pterodactyl/yolks:java_11",
    "Java 8 LTS (Official Yolk)": "ghcr.io/pterodactyl/yolks:java_8",
}

MC_CUSTOM_IMAGES = {
    "Java 21 LTS": f"{GHCR_NAMESPACE}:java_21",
    "Java 25 LTS": f"{GHCR_NAMESPACE}:java_25",
    "Java 17 LTS": f"{GHCR_NAMESPACE}:java_17",
}

MC_SERVER_PROPS_CONFIG = {
    "server.properties": {
        "parser": "properties",
        "find": {
            "server-ip": "0.0.0.0",
            "server-port": "{{server.build.default.port}}",
            "query.port": "{{server.build.default.port}}",
        },
    }
}

MC_JVM_STARTUP = (
    'MEM={{SERVER_MEMORY}}; OVERHEAD=${JVM_OVERHEAD_MB:-512}; '
    'HEAP=$(( MEM - OVERHEAD )); (( HEAP < 512 )) && HEAP=$(( MEM * 80 / 100 )); (( HEAP < 256 )) && HEAP=256; '
    'exec java -Xms256M -Xmx"${HEAP}M" -XX:+UseG1GC -XX:+ParallelRefProcEnabled -XX:MaxGCPauseMillis=200 '
    '-Dterminal.jline=false -Dterminal.ansi=true -jar "${SERVER_JARFILE}" nogui'
)

STEAM_SOURCE_IMAGE = {
    "Source / SteamCMD Runtime (Official Parkervcp Game Image)": "ghcr.io/parkervcp/games:source",
}

STEAM_VARS_BASE = [
    VariableSpec("Steam AppID", "Official Valve Steam Dedicated Server AppID (admin-locked).", "SRCDS_APPID", "0", user_editable=False, rules="required|integer"),
    VariableSpec("Steam Beta Branch", "Optional Steam beta branch name.", "SRCDS_BETAID", "", rules="nullable|string|max:64"),
    VariableSpec("Steam Beta Password", "Optional Steam beta branch password.", "SRCDS_BETAPASS", "", rules="nullable|string|max:128"),
    VariableSpec("Steam Username", "Steam account username (leave blank for anonymous login).", "STEAM_USER", "", rules="nullable|string|max:128"),
    VariableSpec("Steam Password", "Steam account password (leave blank for anonymous login; never logged).", "STEAM_PASS", "", rules="nullable|string|max:128"),
    VariableSpec("Steam Guard Code", "Optional Steam Guard auth code.", "STEAM_AUTH", "", rules="nullable|string|max:32"),
]


def _steam_vars(app_id: int, extra: list[VariableSpec] | None = None) -> list[VariableSpec]:
    base = [
        VariableSpec(v.name, v.description, v.env_variable, str(app_id) if v.env_variable == "SRCDS_APPID" else v.default_value, v.user_viewable, v.user_editable, v.rules, v.field_type)
        for v in STEAM_VARS_BASE
    ]
    if extra:
        base.extend(extra)
    return base


def get_specs() -> list[EggSpec]:
    return [
        # ======================== MINECRAFT (13) ========================
        # 1. Minecraft Vanilla
        EggSpec(
            id="minecraft-vanilla",
            name="Vietnam Hosting — Minecraft Vanilla",
            category="game-servers",
            description="Official Mojang Minecraft Java Edition Vanilla dedicated server downloaded directly from piston-meta.mojang.com with SHA1 integrity check.",
            icon="minecraft",
            supported_versions=["1.20.x", "1.21.x", "latest"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=1024,
            recommended_ram_mb=2048,
            minimum_disk_mb=4096,
            resource_basis="upstream_documented",
            image_source="hybrid_official_and_ghcr",
            dockerfile_path="docker/languages/java/21/Dockerfile",
            features=["eula", "java_version", "pid_limit"],
            docker_images=MC_JAVA_IMAGES,
            custom_docker_images=MC_CUSTOM_IMAGES,
            startup=MC_JVM_STARTUP,
            stop="stop",
            startup_done=") ! For help, type |)! For help, type ",
            config_files=MC_SERVER_PROPS_CONFIG,
            install_body=SAFE_DOWNLOAD_HELPER + r'''
MANIFEST_JSON="$(curl -fsSL --connect-timeout 15 --max-time 30 https://piston-meta.mojang.com/mc/game/version_manifest_v2.json)"
REQ_VER="${VANILLA_VERSION:-latest}"
if [[ "${REQ_VER}" == "latest" ]]; then
    REQ_VER="$(printf '%s' "${MANIFEST_JSON}" | jq -r '.latest.release')"
fi
VER_URL="$(printf '%s' "${MANIFEST_JSON}" | jq -r --arg v "${REQ_VER}" '.versions[] | select(.id == $v) | .url' | head -n1)"
if [[ -z "${VER_URL}" || "${VER_URL}" == "null" ]]; then
    echo "[VNH][INSTALL][ERROR] Minecraft Vanilla version '${REQ_VER}' not found in Mojang manifest." >&2
    exit 1
fi
VER_JSON="$(curl -fsSL --connect-timeout 15 --max-time 30 "${VER_URL}")"
JAR_URL="$(printf '%s' "${VER_JSON}" | jq -r '.downloads.server.url')"
JAR_SHA1="$(printf '%s' "${VER_JSON}" | jq -r '.downloads.server.sha1')"
vnh_download "${JAR_URL}" "/mnt/server/${SERVER_JARFILE}"
if command -v sha1sum >/dev/null 2>&1 && [[ -n "${JAR_SHA1}" && "${JAR_SHA1}" != "null" ]]; then
    GOT_SHA1="$(sha1sum "/mnt/server/${SERVER_JARFILE}" | awk '{print $1}')"
    if [[ "${GOT_SHA1,,}" != "${JAR_SHA1,,}" ]]; then
        echo "[VNH][INSTALL][ERROR] Mojang server JAR SHA1 mismatch!" >&2
        exit 1
    fi
fi
''',
            variables=[
                VariableSpec("Minecraft Version", "Mojang release version or `latest`.", "VANILLA_VERSION", "latest", rules="required|string|max:32"),
                VariableSpec("Server JAR File", "Output server JAR filename.", "SERVER_JARFILE", "server.jar", rules="required|string|max:128"),
                VariableSpec("JVM Off-Heap Reserve (MiB)", "Memory reserved outside JVM heap for OS/Metaspace.", "JVM_OVERHEAD_MB", "512", rules="required|integer|between:128,4096"),
            ],
            upstream_license="Minecraft EULA",
            upstream_url="https://www.minecraft.net/en-us/download/server",
            eula_required=True,
        ),

        # 2. Minecraft Paper
        EggSpec(
            id="minecraft-paper",
            name="Vietnam Hosting — Minecraft Paper",
            category="game-servers",
            description="High-performance PaperMC server downloaded from official PaperMC API with SHA256 verification and Aikar/G1GC tuning.",
            icon="paper",
            supported_versions=["1.20.4", "1.21.x", "latest"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=1024,
            recommended_ram_mb=4096,
            minimum_disk_mb=4096,
            resource_basis="recommended_estimate",
            image_source="hybrid_official_and_ghcr",
            dockerfile_path="docker/languages/java/21/Dockerfile",
            features=["eula", "java_version", "pid_limit"],
            docker_images=MC_JAVA_IMAGES,
            custom_docker_images=MC_CUSTOM_IMAGES,
            startup=MC_JVM_STARTUP,
            stop="stop",
            startup_done=")! For help, type ",
            config_files=MC_SERVER_PROPS_CONFIG,
            install_body=SAFE_DOWNLOAD_HELPER + r'''
UA="VietnamHosting-UniversalEggs/1.0 (+https://vietnam-hosting.net)"
MC_VER="${MINECRAFT_VERSION:-latest}"
if [[ "${MC_VER}" == "latest" ]]; then
    MC_VER="$(curl -fsSL -A "${UA}" https://api.papermc.io/v2/projects/paper | jq -r '.versions[-1]')"
fi
BUILD_NUM="${BUILD_NUMBER:-latest}"
if [[ "${BUILD_NUM}" == "latest" ]]; then
    BUILD_NUM="$(curl -fsSL -A "${UA}" "https://api.papermc.io/v2/projects/paper/versions/${MC_VER}" | jq -r '.builds[-1]')"
fi
META="$(curl -fsSL -A "${UA}" "https://api.papermc.io/v2/projects/paper/versions/${MC_VER}/builds/${BUILD_NUM}")"
JAR_NAME="$(printf '%s' "${META}" | jq -r '.downloads.application.name')"
JAR_SHA256="$(printf '%s' "${META}" | jq -r '.downloads.application.sha256')"
vnh_download "https://api.papermc.io/v2/projects/paper/versions/${MC_VER}/builds/${BUILD_NUM}/downloads/${JAR_NAME}" "/mnt/server/${SERVER_JARFILE}" "${JAR_SHA256}"
''',
            variables=[
                VariableSpec("Minecraft Version", "PaperMC version or `latest`.", "MINECRAFT_VERSION", "latest", rules="required|string|max:32"),
                VariableSpec("Paper Build Number", "Specific build number or `latest`.", "BUILD_NUMBER", "latest", rules="required|string|max:32"),
                VariableSpec("Server JAR File", "Target JAR filename.", "SERVER_JARFILE", "server.jar", rules="required|string|max:128"),
                VariableSpec("JVM Off-Heap Reserve (MiB)", "RAM reserved outside JVM -Xmx.", "JVM_OVERHEAD_MB", "512", rules="required|integer|between:128,4096"),
            ],
            upstream_license="GPL-3.0",
            upstream_url="https://papermc.io",
            eula_required=True,
        ),

        # 3. Minecraft Purpur
        EggSpec(
            id="minecraft-purpur",
            name="Vietnam Hosting — Minecraft Purpur",
            category="game-servers",
            description="PurpurMC drop-in Paper fork with extended gameplay configuration downloaded from official api.purpurmc.org.",
            icon="purpur",
            supported_versions=["1.20.x", "1.21.x", "latest"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=1024,
            recommended_ram_mb=4096,
            minimum_disk_mb=4096,
            image_source="hybrid_official_and_ghcr",
            dockerfile_path="docker/languages/java/21/Dockerfile",
            features=["eula", "java_version", "pid_limit"],
            docker_images=MC_JAVA_IMAGES,
            custom_docker_images=MC_CUSTOM_IMAGES,
            startup=MC_JVM_STARTUP,
            stop="stop",
            startup_done=")! For help, type ",
            config_files=MC_SERVER_PROPS_CONFIG,
            install_body=SAFE_DOWNLOAD_HELPER + r'''
MC_VER="${MINECRAFT_VERSION:-latest}"
if [[ "${MC_VER}" == "latest" ]]; then
    MC_VER="$(curl -fsSL https://api.purpurmc.org/v2/purpur | jq -r '.versions[-1]')"
fi
BUILD_NUM="${BUILD_NUMBER:-latest}"
vnh_download "https://api.purpurmc.org/v2/purpur/${MC_VER}/${BUILD_NUM}/download" "/mnt/server/${SERVER_JARFILE}"
''',
            variables=[
                VariableSpec("Minecraft Version", "Purpur Minecraft version or `latest`.", "MINECRAFT_VERSION", "latest", rules="required|string|max:32"),
                VariableSpec("Purpur Build", "Specific Purpur build number or `latest`.", "BUILD_NUMBER", "latest", rules="required|string|max:32"),
                VariableSpec("Server JAR File", "Target JAR filename.", "SERVER_JARFILE", "server.jar", rules="required|string|max:128"),
                VariableSpec("JVM Off-Heap Reserve (MiB)", "Off-heap memory reserve.", "JVM_OVERHEAD_MB", "512", rules="required|integer|between:128,4096"),
            ],
            upstream_license="MIT",
            upstream_url="https://purpurmc.org",
            eula_required=True,
        ),

        # 4. Minecraft Spigot (Official BuildTools — respects DMCA/GPL distribution rules!)
        EggSpec(
            id="minecraft-spigot",
            name="Vietnam Hosting — Minecraft Spigot (Official BuildTools)",
            category="game-servers",
            description="Official SpigotMC server compiled legally on-demand using SpigotMC BuildTools (never redistributes prebuilt Spigot JARs).",
            icon="spigot",
            supported_versions=["1.20.x", "1.21.x", "latest"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=1536,
            recommended_ram_mb=3072,
            minimum_disk_mb=6144,
            image_source="hybrid_official_and_ghcr",
            dockerfile_path="docker/languages/java/21/Dockerfile",
            install_container="eclipse-temurin:21-jdk-noble",
            features=["eula", "java_version", "pid_limit"],
            docker_images=MC_JAVA_IMAGES,
            custom_docker_images=MC_CUSTOM_IMAGES,
            startup=MC_JVM_STARTUP,
            stop="stop",
            startup_done=")! For help, type ",
            config_files=MC_SERVER_PROPS_CONFIG,
            install_body=SAFE_DOWNLOAD_HELPER + r'''
apt-get update && apt-get install -y --no-install-recommends git curl ca-certificates && rm -rf /var/lib/apt/lists/*
mkdir -p /mnt/server/buildtools
cd /mnt/server/buildtools
vnh_download "https://hub.spigotmc.org/jenkins/job/BuildTools/lastSuccessfulBuild/artifact/target/BuildTools.jar" "/mnt/server/buildtools/BuildTools.jar"
java -Xmx1024M -jar BuildTools.jar --rev "${DL_VERSION}" --output-dir /mnt/server
BUILT_JAR="$(ls -t /mnt/server/spigot-*.jar 2>/dev/null | head -n1 || true)"
if [[ -n "${BUILT_JAR}" ]]; then
    cp -f "${BUILT_JAR}" "/mnt/server/${SERVER_JARFILE}"
fi
''',
            variables=[
                VariableSpec("Spigot Version", "Minecraft revision for BuildTools (e.g. latest or 1.21.4).", "DL_VERSION", "latest", rules="required|string|max:32"),
                VariableSpec("Server JAR File", "Target JAR filename.", "SERVER_JARFILE", "server.jar", rules="required|string|max:128"),
                VariableSpec("JVM Off-Heap Reserve (MiB)", "Off-heap memory reserve.", "JVM_OVERHEAD_MB", "512", rules="required|integer|between:128,4096"),
            ],
            upstream_license="GPL-3.0 / CraftBukkit",
            upstream_url="https://www.spigotmc.org",
            eula_required=True,
        ),

        # 5. Minecraft Fabric
        EggSpec(
            id="minecraft-fabric",
            name="Vietnam Hosting — Minecraft Fabric",
            category="game-servers",
            description="Lightweight modular Minecraft Fabric server installed directly from official meta.fabricmc.net API.",
            icon="fabric",
            supported_versions=["1.20.x", "1.21.x", "latest"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=1536,
            recommended_ram_mb=4096,
            minimum_disk_mb=4096,
            image_source="hybrid_official_and_ghcr",
            dockerfile_path="docker/languages/java/21/Dockerfile",
            features=["eula", "java_version", "pid_limit"],
            docker_images=MC_JAVA_IMAGES,
            custom_docker_images=MC_CUSTOM_IMAGES,
            startup=MC_JVM_STARTUP,
            stop="stop",
            startup_done=")! For help, type ",
            config_files=MC_SERVER_PROPS_CONFIG,
            install_body=SAFE_DOWNLOAD_HELPER + r'''
MC_VER="${MC_VERSION:-latest}"
if [[ "${MC_VER}" == "latest" ]]; then
    MC_VER="$(curl -fsSL https://meta.fabricmc.net/v2/versions/game | jq -r '[.[] | select(.stable == true)][0].version')"
fi
LOADER_VER="${FABRIC_VERSION:-latest}"
if [[ "${LOADER_VER}" == "latest" ]]; then
    LOADER_VER="$(curl -fsSL https://meta.fabricmc.net/v2/versions/loader | jq -r '[.[] | select(.stable == true)][0].version')"
fi
INST_VER="${LOADER_INSTALLER:-latest}"
if [[ "${INST_VER}" == "latest" ]]; then
    INST_VER="$(curl -fsSL https://meta.fabricmc.net/v2/versions/installer | jq -r '[.[] | select(.stable == true)][0].version')"
fi
vnh_download "https://meta.fabricmc.net/v2/versions/loader/${MC_VER}/${LOADER_VER}/${INST_VER}/server/jar" "/mnt/server/${SERVER_JARFILE}"
mkdir -p /mnt/server/mods
''',
            variables=[
                VariableSpec("Minecraft Version", "Minecraft version or `latest`.", "MC_VERSION", "latest", rules="required|string|max:32"),
                VariableSpec("Fabric Loader Version", "Fabric loader version or `latest`.", "FABRIC_VERSION", "latest", rules="required|string|max:32"),
                VariableSpec("Fabric Installer Version", "Fabric installer version or `latest`.", "LOADER_INSTALLER", "latest", rules="required|string|max:32"),
                VariableSpec("Server JAR File", "Target launcher JAR filename.", "SERVER_JARFILE", "fabric-server-launch.jar", rules="required|string|max:128"),
                VariableSpec("JVM Off-Heap Reserve (MiB)", "Off-heap RAM headroom.", "JVM_OVERHEAD_MB", "512", rules="required|integer|between:128,4096"),
            ],
            upstream_license="Apache-2.0",
            upstream_url="https://fabricmc.net",
            eula_required=True,
        ),

        # 6. Minecraft Forge
        EggSpec(
            id="minecraft-forge",
            name="Vietnam Hosting — Minecraft Forge",
            category="game-servers",
            description="Minecraft Forge modded server downloaded from official maven.minecraftforge.net with modern @unix_args.txt support.",
            icon="forge",
            supported_versions=["1.18.x", "1.19.x", "1.20.x", "1.21.x"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=2048,
            recommended_ram_mb=6144,
            minimum_disk_mb=6144,
            image_source="hybrid_official_and_ghcr",
            dockerfile_path="docker/languages/java/21/Dockerfile",
            install_container="eclipse-temurin:21-jdk-noble",
            features=["eula", "java_version", "pid_limit"],
            docker_images=MC_JAVA_IMAGES,
            custom_docker_images=MC_CUSTOM_IMAGES,
            startup=(
                'MEM={{SERVER_MEMORY}}; HEAP=$(( MEM - ${JVM_OVERHEAD_MB:-512} )); (( HEAP < 512 )) && HEAP=512; '
                'echo "-Xms512M -Xmx${HEAP}M -XX:+UseG1GC" > user_jvm_args.txt; '
                'if [[ -f unix_args.txt ]]; then exec java @user_jvm_args.txt @unix_args.txt nogui; '
                'else exec java -Xms512M -Xmx"${HEAP}M" -jar "${SERVER_JARFILE}" nogui; fi'
            ),
            stop="stop",
            startup_done=")! For help, type ",
            config_files=MC_SERVER_PROPS_CONFIG,
            install_body=SAFE_DOWNLOAD_HELPER + r'''
apt-get update && apt-get install -y --no-install-recommends curl jq ca-certificates && rm -rf /var/lib/apt/lists/*
FORGE_FULL="${FORGE_VERSION}"
if [[ -z "${FORGE_FULL}" ]]; then
    PROMO="$(curl -fsSL https://files.minecraftforge.net/net/minecraftforge/forge/promotions_slim.json)"
    FVER="$(printf '%s' "${PROMO}" | jq -r --arg k "${MC_VERSION}-recommended" '.promos[$k] // empty')"
    [[ -z "${FVER}" ]] && FVER="$(printf '%s' "${PROMO}" | jq -r --arg k "${MC_VERSION}-latest" '.promos[$k] // empty')"
    FORGE_FULL="${MC_VERSION}-${FVER}"
fi
vnh_download "https://maven.minecraftforge.net/net/minecraftforge/forge/${FORGE_FULL}/forge-${FORGE_FULL}-installer.jar" "/mnt/server/forge-installer.jar"
java -jar /mnt/server/forge-installer.jar --installServer /mnt/server
rm -f /mnt/server/forge-installer.jar /mnt/server/forge-installer.jar.log
UNIX_ARGS="$(find /mnt/server/libraries/net/minecraftforge/forge -name unix_args.txt 2>/dev/null | head -n1 || true)"
if [[ -n "${UNIX_ARGS}" ]]; then
    ln -sf "${UNIX_ARGS}" /mnt/server/unix_args.txt
fi
mkdir -p /mnt/server/mods
''',
            variables=[
                VariableSpec("Minecraft Version", "Target Minecraft version (e.g. 1.20.1 or 1.21.1).", "MC_VERSION", "1.20.1", rules="required|string|max:32"),
                VariableSpec("Exact Forge Version", "Optional full Forge version (e.g. 1.20.1-47.3.0). Blank selects recommended.", "FORGE_VERSION", "", rules="nullable|string|max:64"),
                VariableSpec("Legacy Server JAR", "Fallback JAR for older Forge < 1.17.", "SERVER_JARFILE", "server.jar", rules="required|string|max:128"),
                VariableSpec("JVM Off-Heap Reserve (MiB)", "Off-heap memory reserve.", "JVM_OVERHEAD_MB", "512", rules="required|integer|between:128,4096"),
            ],
            upstream_license="LGPL-2.1",
            upstream_url="https://files.minecraftforge.net",
            eula_required=True,
        ),

        # 7. Minecraft NeoForge
        EggSpec(
            id="minecraft-neoforge",
            name="Vietnam Hosting — Minecraft NeoForge",
            category="game-servers",
            description="Modern Minecraft NeoForge modded server installed directly from official maven.neoforged.net.",
            icon="neoforge",
            supported_versions=["1.20.4", "1.21.x", "latest"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=2048,
            recommended_ram_mb=6144,
            minimum_disk_mb=6144,
            image_source="hybrid_official_and_ghcr",
            dockerfile_path="docker/languages/java/21/Dockerfile",
            install_container="eclipse-temurin:21-jdk-noble",
            features=["eula", "java_version", "pid_limit"],
            docker_images=MC_JAVA_IMAGES,
            custom_docker_images=MC_CUSTOM_IMAGES,
            startup=(
                'MEM={{SERVER_MEMORY}}; HEAP=$(( MEM - ${JVM_OVERHEAD_MB:-512} )); (( HEAP < 512 )) && HEAP=512; '
                'echo "-Xms512M -Xmx${HEAP}M -XX:+UseG1GC" > user_jvm_args.txt; '
                'exec java @user_jvm_args.txt @unix_args.txt nogui'
            ),
            stop="stop",
            startup_done=")! For help, type ",
            config_files=MC_SERVER_PROPS_CONFIG,
            install_body=SAFE_DOWNLOAD_HELPER + r'''
apt-get update && apt-get install -y --no-install-recommends curl jq ca-certificates && rm -rf /var/lib/apt/lists/*
NF_VER="${NEOFORGE_VERSION:-latest}"
if [[ "${NF_VER}" == "latest" ]]; then
    NF_VER="$(curl -fsSL https://maven.neoforged.net/api/maven/versions/releases/net/neoforged/neoforge | jq -r '.versions[-1]')"
fi
vnh_download "https://maven.neoforged.net/releases/net/neoforged/neoforge/${NF_VER}/neoforge-${NF_VER}-installer.jar" "/mnt/server/neoforge-installer.jar"
java -jar /mnt/server/neoforge-installer.jar --installServer /mnt/server
rm -f /mnt/server/neoforge-installer.jar
UNIX_ARGS="$(find /mnt/server/libraries/net/neoforged/neoforge -name unix_args.txt 2>/dev/null | head -n1 || true)"
if [[ -n "${UNIX_ARGS}" ]]; then
    ln -sf "${UNIX_ARGS}" /mnt/server/unix_args.txt
fi
mkdir -p /mnt/server/mods
''',
            variables=[
                VariableSpec("NeoForge Version", "NeoForge artifact version or `latest`.", "NEOFORGE_VERSION", "latest", rules="required|string|max:64"),
                VariableSpec("JVM Off-Heap Reserve (MiB)", "Off-heap RAM reserve.", "JVM_OVERHEAD_MB", "512", rules="required|integer|between:128,4096"),
            ],
            upstream_license="LGPL-2.1",
            upstream_url="https://neoforged.net",
            eula_required=True,
        ),

        # 8. Minecraft Velocity Proxy
        EggSpec(
            id="minecraft-velocity",
            name="Vietnam Hosting — Minecraft Velocity Proxy",
            category="game-servers",
            description="Modern PaperMC Velocity proxy server with SHA256-verified downloads and forwarding support.",
            icon="velocity",
            supported_versions=["3.3.x", "3.4.x", "latest"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=256,
            recommended_ram_mb=512,
            minimum_disk_mb=1024,
            image_source="hybrid_official_and_ghcr",
            dockerfile_path="docker/languages/java/21/Dockerfile",
            features=["java_version", "pid_limit"],
            docker_images=MC_JAVA_IMAGES,
            custom_docker_images=MC_CUSTOM_IMAGES,
            startup='MEM={{SERVER_MEMORY}}; HEAP=$(( MEM * 75 / 100 )); (( HEAP < 128 )) && HEAP=128; exec java -Xms128M -Xmx"${HEAP}M" -XX:+UseG1GC -jar "${SERVER_JARFILE}"',
            stop="end",
            startup_done="Listening on ",
            config_files={"velocity.toml": {"parser": "file", "find": {"bind =": 'bind = "0.0.0.0:{{server.build.default.port}}"'}}},
            install_body=SAFE_DOWNLOAD_HELPER + r'''
UA="VietnamHosting-UniversalEggs/1.0 (+https://vietnam-hosting.net)"
V_VER="${VELOCITY_VERSION:-latest}"
if [[ "${V_VER}" == "latest" ]]; then
    V_VER="$(curl -fsSL -A "${UA}" https://api.papermc.io/v2/projects/velocity | jq -r '.versions[-1]')"
fi
B_NUM="$(curl -fsSL -A "${UA}" "https://api.papermc.io/v2/projects/velocity/versions/${V_VER}" | jq -r '.builds[-1]')"
META="$(curl -fsSL -A "${UA}" "https://api.papermc.io/v2/projects/velocity/versions/${V_VER}/builds/${B_NUM}")"
JAR_NAME="$(printf '%s' "${META}" | jq -r '.downloads.application.name')"
JAR_SHA256="$(printf '%s' "${META}" | jq -r '.downloads.application.sha256')"
vnh_download "https://api.papermc.io/v2/projects/velocity/versions/${V_VER}/builds/${B_NUM}/downloads/${JAR_NAME}" "/mnt/server/${SERVER_JARFILE}" "${JAR_SHA256}"
''',
            variables=[
                VariableSpec("Velocity Version", "Velocity branch or `latest`.", "VELOCITY_VERSION", "latest", rules="required|string|max:32"),
                VariableSpec("Proxy JAR File", "Velocity JAR filename.", "SERVER_JARFILE", "velocity.jar", rules="required|string|max:128"),
            ],
            upstream_license="GPL-3.0",
            upstream_url="https://papermc.io/software/velocity",
        ),

        # 9. Minecraft BungeeCord
        EggSpec(
            id="minecraft-bungeecord",
            name="Vietnam Hosting — Minecraft BungeeCord",
            category="game-servers",
            description="Official SpigotMC BungeeCord proxy server downloaded directly from ci.md-5.net.",
            icon="bungeecord",
            supported_versions=["latest"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=256,
            recommended_ram_mb=512,
            minimum_disk_mb=1024,
            image_source="hybrid_official_and_ghcr",
            dockerfile_path="docker/languages/java/21/Dockerfile",
            features=["java_version", "pid_limit"],
            docker_images=MC_JAVA_IMAGES,
            custom_docker_images=MC_CUSTOM_IMAGES,
            startup='MEM={{SERVER_MEMORY}}; HEAP=$(( MEM * 75 / 100 )); (( HEAP < 128 )) && HEAP=128; exec java -Xms128M -Xmx"${HEAP}M" -jar "${SERVER_JARFILE}"',
            stop="end",
            startup_done="Listening on ",
            config_files={"config.yml": {"parser": "yaml", "find": {"listeners[0].host": "0.0.0.0:{{server.build.default.port}}"}}},
            install_body=SAFE_DOWNLOAD_HELPER + '\nvnh_download "https://ci.md-5.net/job/BungeeCord/lastSuccessfulBuild/artifact/bootstrap/target/BungeeCord.jar" "/mnt/server/${SERVER_JARFILE}"\n',
            variables=[VariableSpec("BungeeCord JAR File", "Proxy JAR filename.", "SERVER_JARFILE", "BungeeCord.jar", rules="required|string|max:128")],
            upstream_license="BSD-3-Clause",
            upstream_url="https://www.spigotmc.org/wiki/bungeecord/",
        ),

        # 10. Minecraft Waterfall Legacy
        EggSpec(
            id="minecraft-waterfall",
            name="Vietnam Hosting — Minecraft Waterfall (Legacy)",
            category="game-servers",
            description="Legacy PaperMC Waterfall proxy (archived upstream by PaperMC in favor of Velocity; maintained for legacy networks only).",
            icon="waterfall",
            supported_versions=["1.21 (Archived Legacy)"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=256,
            recommended_ram_mb=512,
            minimum_disk_mb=1024,
            status="Legacy",
            image_source="hybrid_official_and_ghcr",
            dockerfile_path="docker/languages/java/21/Dockerfile",
            features=["java_version", "pid_limit"],
            docker_images=MC_JAVA_IMAGES,
            custom_docker_images=MC_CUSTOM_IMAGES,
            startup='MEM={{SERVER_MEMORY}}; HEAP=$(( MEM * 75 / 100 )); (( HEAP < 128 )) && HEAP=128; exec java -Xms128M -Xmx"${HEAP}M" -jar "${SERVER_JARFILE}"',
            stop="end",
            startup_done="Listening on ",
            config_files={"config.yml": {"parser": "yaml", "find": {"listeners[0].host": "0.0.0.0:{{server.build.default.port}}"}}},
            install_body=SAFE_DOWNLOAD_HELPER + r'''
UA="VietnamHosting-UniversalEggs/1.0 (+https://vietnam-hosting.net)"
W_VER="$(curl -fsSL -A "${UA}" https://api.papermc.io/v2/projects/waterfall | jq -r '.versions[-1]')"
B_NUM="$(curl -fsSL -A "${UA}" "https://api.papermc.io/v2/projects/waterfall/versions/${W_VER}" | jq -r '.builds[-1]')"
META="$(curl -fsSL -A "${UA}" "https://api.papermc.io/v2/projects/waterfall/versions/${W_VER}/builds/${B_NUM}")"
JAR_NAME="$(printf '%s' "${META}" | jq -r '.downloads.application.name')"
JAR_SHA256="$(printf '%s' "${META}" | jq -r '.downloads.application.sha256')"
vnh_download "https://api.papermc.io/v2/projects/waterfall/versions/${W_VER}/builds/${B_NUM}/downloads/${JAR_NAME}" "/mnt/server/${SERVER_JARFILE}" "${JAR_SHA256}"
''',
            variables=[VariableSpec("Waterfall JAR File", "Legacy proxy JAR filename.", "SERVER_JARFILE", "waterfall.jar", rules="required|string|max:128")],
            upstream_license="BSD-3-Clause",
            upstream_url="https://papermc.io/software/waterfall",
            notes="Archived upstream by PaperMC; use Velocity for new deployments.",
        ),

        # 11. Minecraft Bedrock Dedicated Server (AMD64 ONLY!)
        EggSpec(
            id="minecraft-bedrock",
            name="Vietnam Hosting — Minecraft Bedrock Dedicated Server",
            category="game-servers",
            description="Official Mojang Minecraft Bedrock Dedicated Server for Linux x86_64 (AMD64 only — Mojang does not ship native ARM64 Linux binaries).",
            icon="minecraft-bedrock",
            supported_versions=["Latest Official Mojang Linux x64"],
            supported_architectures=["amd64"],
            minimum_ram_mb=1024,
            recommended_ram_mb=2048,
            minimum_disk_mb=2048,
            resource_basis="upstream_documented",
            image_source="upstream_official_yolk",
            docker_images={"Debian Official Yolk (AMD64)": "ghcr.io/pterodactyl/yolks:debian"},
            custom_docker_images={"Base Debian 13 (AMD64)": f"{GHCR_NAMESPACE}:base_debian13"},
            startup='LD_LIBRARY_PATH=. exec ./bedrock_server',
            stop="stop",
            startup_done="Server started.",
            config_files={"server.properties": {"parser": "properties", "find": {"server-port": "{{server.build.default.port}}", "server-name": "{{env.SERVER_NAME}}", "gamemode": "{{env.GAMEMODE}}"}}},
            install_body=SAFE_DOWNLOAD_HELPER + r'''
if [[ "$(uname -m)" != "x86_64" ]]; then
    echo "[VNH][INSTALL][ERROR] Minecraft Bedrock Dedicated Server officially supports Linux x86_64 (amd64) only." >&2
    exit 1
fi
DL_URL="${BEDROCK_DOWNLOAD_URL:-}"
if [[ -z "${DL_URL}" ]]; then
    DL_URL="$(curl -fsSL -A "Mozilla/5.0" "https://net-secondary.web.minecraft-services.net/api/v1.0/download/links" | jq -r '.result.links[] | select(.downloadType == "serverBedrockLinux") | .downloadUrl' | head -n1)"
fi
if [[ -z "${DL_URL}" || "${DL_URL}" == "null" ]]; then
    echo "[VNH][INSTALL][ERROR] Could not resolve official Mojang Bedrock download URL. Supply BEDROCK_DOWNLOAD_URL explicitly." >&2
    exit 1
fi
vnh_download "${DL_URL}" "/tmp/bedrock-server.zip"
# Preserve existing server.properties, permissions.json, allowlist.json on reinstall
unzip -n -q /tmp/bedrock-server.zip -d /mnt/server
unzip -o -q /tmp/bedrock-server.zip bedrock_server -d /mnt/server
chmod +x /mnt/server/bedrock_server
rm -f /tmp/bedrock-server.zip
''',
            variables=[
                VariableSpec("Server Name", "Bedrock server MOTD name.", "SERVER_NAME", "Vietnam Hosting Bedrock", rules="required|string|max:64"),
                VariableSpec("Gamemode", "Default gamemode.", "GAMEMODE", "survival", rules="required|string|in:survival,creative,adventure"),
                VariableSpec("Optional Official Zip URL", "Optional direct https://www.minecraft.net/bedrockdedicatedserver/... zip override.", "BEDROCK_DOWNLOAD_URL", "", rules="nullable|string|max:512"),
            ],
            upstream_license="Minecraft EULA",
            upstream_url="https://www.minecraft.net/en-us/download/server/bedrock",
            eula_required=True,
            notes="AMD64 only — Mojang publishes Linux x86_64 binaries exclusively.",
        ),

        # 12. PocketMine-MP
        EggSpec(
            id="minecraft-pocketmine-mp",
            name="Vietnam Hosting — PocketMine-MP",
            category="game-servers",
            description="Open-source PHP-based Bedrock server software (PocketMine-MP) downloaded from official GitHub Releases.",
            icon="pocketmine",
            supported_versions=["5.x (PHP 8.3)"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=512,
            recommended_ram_mb=1024,
            minimum_disk_mb=2048,
            image_source="requires_ghcr_build",
            dockerfile_path="docker/services/pocketmine/Dockerfile",
            docker_images={"PocketMine PHP 8.3 (Vietnam Hosting GHCR)": f"{GHCR_NAMESPACE}:pocketmine_php8.3"},
            custom_docker_images={"PocketMine PHP 8.3": f"{GHCR_NAMESPACE}:pocketmine_php8.3"},
            startup='exec php /home/container/PocketMine-MP.phar --no-wizard --settings.enable-dev-builds=0',
            stop="stop",
            startup_done="Done (",
            config_files={"server.properties": {"parser": "properties", "find": {"server-port": "{{server.build.default.port}}"}}},
            install_body=SAFE_DOWNLOAD_HELPER + r'''
PHAR_URL="$(curl -fsSL https://api.github.com/repos/pmmp/PocketMine-MP/releases/latest | jq -r '.assets[] | select(.name == "PocketMine-MP.phar") | .browser_download_url' | head -n1)"
vnh_download "${PHAR_URL}" "/mnt/server/PocketMine-MP.phar"
mkdir -p /mnt/server/plugins /mnt/server/worlds
''',
            variables=[],
            upstream_license="LGPL-3.0",
            upstream_url="https://pmmp.io",
        ),

        # 13. Nukkit
        EggSpec(
            id="minecraft-nukkit",
            name="Vietnam Hosting — Minecraft Nukkit",
            category="game-servers",
            description="Java-based Bedrock server software (Cloudburst Nukkit) running on Eclipse Temurin JDK 17/21.",
            icon="nukkit",
            supported_versions=["1.0-SNAPSHOT (Java 17/21)"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=512,
            recommended_ram_mb=1024,
            minimum_disk_mb=2048,
            image_source="hybrid_official_and_ghcr",
            dockerfile_path="docker/languages/java/21/Dockerfile",
            features=["java_version", "pid_limit"],
            docker_images=MC_JAVA_IMAGES,
            custom_docker_images=MC_CUSTOM_IMAGES,
            startup='MEM={{SERVER_MEMORY}}; HEAP=$(( MEM * 75 / 100 )); (( HEAP < 256 )) && HEAP=256; exec java -Xms256M -Xmx"${HEAP}M" -jar "${SERVER_JARFILE}"',
            stop="stop",
            startup_done="Done (",
            config_files={"server.properties": {"parser": "properties", "find": {"server-port": "{{server.build.default.port}}"}}},
            install_body=SAFE_DOWNLOAD_HELPER + '\nvnh_download "https://repo.opencollab.dev/api/maven/latest/file/maven-snapshots/cn/nukkit/nukkit/1.0-SNAPSHOT?extension=jar" "/mnt/server/${SERVER_JARFILE}"\n',
            variables=[VariableSpec("Nukkit JAR File", "Target Nukkit JAR filename.", "SERVER_JARFILE", "nukkit.jar", rules="required|string|max:128")],
            upstream_license="GPL-3.0",
            upstream_url="https://github.com/CloudburstMC/Nukkit",
        ),

        # ======================== OTHER GAMES (16) ========================
        # 14. Terraria
        EggSpec(
            id="terraria",
            name="Vietnam Hosting — Terraria Dedicated Server",
            category="game-servers",
            description="Official Terraria dedicated server installed via SteamCMD (AppID 105600, AMD64 Linux native).",
            icon="terraria",
            supported_versions=["1.4.x (SteamCMD 105600)"],
            supported_architectures=["amd64"],
            minimum_ram_mb=512,
            recommended_ram_mb=1024,
            minimum_disk_mb=2048,
            resource_basis="upstream_documented",
            image_source="upstream_official_yolk",
            features=["steam_disk_space"],
            docker_images=STEAM_SOURCE_IMAGE,
            startup='exec ./TerrariaServer.bin.x86_64 -port {{SERVER_PORT}} -maxplayers "${MAX_PLAYERS}" -world "/home/container/saves/${WORLD_NAME}.wld" -autocreate "${WORLD_SIZE}"',
            stop="exit",
            startup_done="Server started",
            install_body=STEAMCMD_INSTALL_SNIPPET + '\nmkdir -p /mnt/server/saves\nchmod +x /mnt/server/TerrariaServer.bin.x86_64 2>/dev/null || true\n',
            variables=_steam_vars(105600, [
                VariableSpec("World Name", "World file prefix inside saves/.", "WORLD_NAME", "world", rules="required|alpha_dash|max:64"),
                VariableSpec("World Size", "1=Small, 2=Medium, 3=Large.", "WORLD_SIZE", "2", rules="required|integer|in:1,2,3"),
                VariableSpec("Max Players", "Maximum concurrent players.", "MAX_PLAYERS", "8", rules="required|integer|between:1,255"),
            ]),
            upstream_license="Re-Logic Terraria EULA",
            upstream_url="https://terraria.org",
            steam_app_id=105600,
            notes="AMD64 only (SteamCMD + x86_64 binary).",
        ),

        # 15. TShock
        EggSpec(
            id="tshock",
            name="Vietnam Hosting — Terraria TShock",
            category="game-servers",
            description="Official Pryaxis TShock Terraria server downloaded from GitHub Releases (Linux x64, AMD64 only).",
            icon="tshock",
            supported_versions=["5.x (Official GitHub Release)"],
            supported_architectures=["amd64"],
            minimum_ram_mb=1024,
            recommended_ram_mb=2048,
            minimum_disk_mb=2048,
            image_source="requires_ghcr_build",
            dockerfile_path="docker/languages/dotnet/8/Dockerfile",
            docker_images={".NET 8.0 (Vietnam Hosting GHCR)": f"{GHCR_NAMESPACE}:dotnet_8"},
            custom_docker_images={".NET 8.0": f"{GHCR_NAMESPACE}:dotnet_8"},
            startup='exec ./TShock.Server -port {{SERVER_PORT}} -maxplayers "${MAX_PLAYERS}" -world "/home/container/worlds/${WORLD_NAME}.wld" -autocreate "${WORLD_SIZE}"',
            stop="exit",
            startup_done="Server started",
            install_body=SAFE_DOWNLOAD_HELPER + r'''
if [[ "$(uname -m)" != "x86_64" ]]; then
    echo "[VNH][INSTALL][ERROR] Official TShock Linux release binaries target x86_64 (amd64)." >&2
    exit 1
fi
REL_URL="$(curl -fsSL https://api.github.com/repos/Pryaxis/TShock/releases/latest | jq -r '.assets[] | select(.name | test("linux-x64.*\\.zip$")) | .browser_download_url' | head -n1)"
vnh_download "${REL_URL}" "/tmp/tshock.zip"
unzip -o -q /tmp/tshock.zip -d /mnt/server
rm -f /tmp/tshock.zip
mkdir -p /mnt/server/worlds
chmod +x /mnt/server/TShock.Server 2>/dev/null || true
''',
            variables=[
                VariableSpec("World Name", "World name under worlds/.", "WORLD_NAME", "tshock_world", rules="required|alpha_dash|max:64"),
                VariableSpec("World Size", "1=Small, 2=Medium, 3=Large.", "WORLD_SIZE", "2", rules="required|integer|in:1,2,3"),
                VariableSpec("Max Players", "Player limit.", "MAX_PLAYERS", "16", rules="required|integer|between:1,255"),
            ],
            upstream_license="GPL-3.0",
            upstream_url="https://github.com/Pryaxis/TShock",
            notes="AMD64 only (official linux-x64 release bundle).",
        ),

        # 16. Factorio
        EggSpec(
            id="factorio",
            name="Vietnam Hosting — Factorio Headless Server",
            category="game-servers",
            description="Official Wube Factorio Headless Linux x64 server downloaded from factorio.com (AMD64 only).",
            icon="factorio",
            supported_versions=["2.0 Stable (Official Headless)"],
            supported_architectures=["amd64"],
            minimum_ram_mb=1024,
            recommended_ram_mb=2048,
            minimum_disk_mb=4096,
            resource_basis="upstream_documented",
            image_source="upstream_official_yolk",
            docker_images={"Debian Official Yolk (AMD64)": "ghcr.io/pterodactyl/yolks:debian"},
            custom_docker_images={"Base Debian 13 (AMD64)": f"{GHCR_NAMESPACE}:base_debian13"},
            startup='if [[ ! -f "saves/${SAVE_NAME}.zip" ]]; then ./bin/x64/factorio --create "saves/${SAVE_NAME}.zip"; fi; exec ./bin/x64/factorio --port {{SERVER_PORT}} --server-settings data/server-settings.json --start-server "saves/${SAVE_NAME}.zip"',
            stop="^C",
            startup_done="Hosting game at IP ADDR",
            install_body=SAFE_DOWNLOAD_HELPER + r'''
if [[ "$(uname -m)" != "x86_64" ]]; then
    echo "[VNH][INSTALL][ERROR] Factorio official headless server is Linux x86_64 (amd64) only." >&2
    exit 1
fi
vnh_download "https://factorio.com/get-download/${FACTORIO_VERSION}/headless/linux64" "/tmp/factorio.tar.xz"
tar -xf /tmp/factorio.tar.xz --strip-components=1 -C /mnt/server
rm -f /tmp/factorio.tar.xz
mkdir -p /mnt/server/saves /mnt/server/mods
if [[ ! -f /mnt/server/data/server-settings.json ]] && [[ -f /mnt/server/data/server-settings.example.json ]]; then
    cp /mnt/server/data/server-settings.example.json /mnt/server/data/server-settings.json
fi
''',
            variables=[
                VariableSpec("Factorio Version", "Release channel (`stable`, `latest`, or explicit version).", "FACTORIO_VERSION", "stable", rules="required|string|max:32"),
                VariableSpec("Save Name", "Save file name inside saves/.", "SAVE_NAME", "vietnam_hosting", rules="required|alpha_dash|max:64"),
            ],
            upstream_license="Factorio EULA",
            upstream_url="https://factorio.com/download",
            eula_required=True,
            notes="AMD64 only (Wube ships x86_64 Linux headless binaries only).",
        ),

        # 17. Valheim
        EggSpec(
            id="valheim",
            name="Vietnam Hosting — Valheim Dedicated Server",
            category="game-servers",
            description="Official Valheim Linux dedicated server via SteamCMD (AppID 896660, AMD64 only).",
            icon="valheim",
            supported_versions=["Latest SteamCMD (AppID 896660)"],
            supported_architectures=["amd64"],
            minimum_ram_mb=2048,
            recommended_ram_mb=4096,
            minimum_disk_mb=4096,
            resource_basis="upstream_documented",
            image_source="upstream_official_yolk",
            features=["steam_disk_space"],
            docker_images=STEAM_SOURCE_IMAGE,
            startup='export LD_LIBRARY_PATH="./linux64:${LD_LIBRARY_PATH:-}"; exec ./valheim_server.x86_64 -nographics -batchmode -name "${SERVER_NAME}" -port {{SERVER_PORT}} -world "${WORLD_NAME}" -password "${SERVER_PASSWORD}" -public "${PUBLIC_SERVER}" -savedir /home/container/saves',
            stop="^C",
            startup_done="Game server connected|DungeonDB Start",
            install_body=STEAMCMD_INSTALL_SNIPPET + '\nmkdir -p /mnt/server/saves\n',
            variables=_steam_vars(896660, [
                VariableSpec("Server Name", "Public Valheim server display name.", "SERVER_NAME", "Vietnam Hosting Valheim", rules="required|string|max:64"),
                VariableSpec("World Name", "Valheim world name.", "WORLD_NAME", "Dedicated", rules="required|alpha_dash|max:64"),
                VariableSpec("Server Password", "Join password (min 5 chars, required by Valheim when public).", "SERVER_PASSWORD", "", rules="required|string|min:5|max:64"),
                VariableSpec("Public Listing", "1 to publish on community server list, 0 for private.", "PUBLIC_SERVER", "0", rules="required|boolean"),
            ]),
            upstream_license="Iron Gate Valheim EULA",
            upstream_url="https://www.valheimgame.com",
            steam_app_id=896660,
            notes="AMD64 only. Uses UDP port {{SERVER_PORT}} and {{SERVER_PORT}}+1.",
        ),

        # 18. Palworld
        EggSpec(
            id="palworld",
            name="Vietnam Hosting — Palworld Dedicated Server",
            category="game-servers",
            description="Official Palworld Linux dedicated server via SteamCMD (AppID 2394010, AMD64 only, high RAM requirement).",
            icon="palworld",
            supported_versions=["Latest SteamCMD (AppID 2394010)"],
            supported_architectures=["amd64"],
            minimum_ram_mb=8192,
            recommended_ram_mb=16384,
            minimum_disk_mb=10240,
            resource_basis="upstream_documented",
            image_source="upstream_official_yolk",
            features=["steam_disk_space"],
            docker_images=STEAM_SOURCE_IMAGE,
            startup='exec ./Pal/Binaries/Linux/PalServer-Linux-Shipping Pal -port={{SERVER_PORT}} -players="${MAX_PLAYERS}" -useperfthreads -NoAsyncLoadingThread -UseMultithreadForDS',
            stop="^C",
            startup_done="Running Palworld dedicated server|Initialized",
            install_body=STEAMCMD_INSTALL_SNIPPET + '\n',
            variables=_steam_vars(2394010, [
                VariableSpec("Max Players", "Maximum concurrent players (1-32).", "MAX_PLAYERS", "16", rules="required|integer|between:1,32"),
            ]),
            upstream_license="Pocketpair EULA",
            upstream_url="https://tech.palworldgame.com/dedicated-server-guide",
            steam_app_id=2394010,
            notes="AMD64 only. Upstream recommends 16 GiB+ RAM for active multiplayer worlds.",
        ),

        # 19. Rust Game Server
        EggSpec(
            id="rust-game",
            name="Vietnam Hosting — Rust Game Server",
            category="game-servers",
            description="Official Facepunch Rust Linux dedicated server via SteamCMD (AppID 258550, AMD64 only).",
            icon="rust-game",
            supported_versions=["Latest SteamCMD (AppID 258550)"],
            supported_architectures=["amd64"],
            minimum_ram_mb=4096,
            recommended_ram_mb=8192,
            minimum_disk_mb=16384,
            resource_basis="upstream_documented",
            image_source="upstream_official_yolk",
            features=["steam_disk_space"],
            docker_images={"Rust Game Image (Official Pterodactyl)": "ghcr.io/pterodactyl/games:rust"},
            startup='exec ./RustDedicated -batchmode +server.port {{SERVER_PORT}} +server.identity "${SERVER_IDENTITY}" +rcon.port "${RCON_PORT}" +rcon.web 1 +server.hostname "${HOSTNAME}" +server.maxplayers "${MAX_PLAYERS}" +server.worldsize "${WORLD_SIZE}" +server.seed "${WORLD_SEED}" -logfile 2>&1',
            stop="quit",
            startup_done="Server startup complete",
            install_body=STEAMCMD_INSTALL_SNIPPET + '\n',
            variables=_steam_vars(258550, [
                VariableSpec("Server Hostname", "Display name in Rust server browser.", "HOSTNAME", "Vietnam Hosting Rust", rules="required|string|max:128"),
                VariableSpec("Server Identity", "Directory identity under server/.", "SERVER_IDENTITY", "rust_vnh", rules="required|alpha_dash|max:64"),
                VariableSpec("Max Players", "Player slot limit.", "MAX_PLAYERS", "50", rules="required|integer|between:1,500"),
                VariableSpec("World Size", "Procedural map size (1000-6000).", "WORLD_SIZE", "3000", rules="required|integer|between:1000,6000"),
                VariableSpec("World Seed", "Procedural map seed.", "WORLD_SEED", "123456", rules="required|integer"),
                VariableSpec("RCON Port", "Dedicated allocation port for WebRCON.", "RCON_PORT", "28016", rules="required|integer|between:1024,65535"),
            ]),
            upstream_license="Facepunch Studios EULA",
            upstream_url="https://wiki.facepunch.com/rust/",
            steam_app_id=258550,
            notes="AMD64 only. Requires high RAM (8 GiB+ recommended for 3500+ maps).",
        ),

        # 20. ARK: Survival Evolved
        EggSpec(
            id="ark",
            name="Vietnam Hosting — ARK: Survival Evolved",
            category="game-servers",
            description="Official ARK: Survival Evolved Linux dedicated server via SteamCMD (AppID 376030, AMD64 only).",
            icon="ark",
            supported_versions=["Latest SteamCMD (AppID 376030)"],
            supported_architectures=["amd64"],
            minimum_ram_mb=6144,
            recommended_ram_mb=10240,
            minimum_disk_mb=24576,
            resource_basis="upstream_documented",
            image_source="upstream_official_yolk",
            features=["steam_disk_space"],
            docker_images=STEAM_SOURCE_IMAGE,
            startup='cd ShooterGame/Binaries/Linux && exec ./ShooterGameServer "${SERVER_MAP}?listen?SessionName=${SESSION_NAME}?Port={{SERVER_PORT}}?QueryPort=${QUERY_PORT}?MaxPlayers=${MAX_PLAYERS}" -server -log',
            stop="^C",
            startup_done="Full Startup:",
            install_body=STEAMCMD_INSTALL_SNIPPET + '\n',
            variables=_steam_vars(376030, [
                VariableSpec("Map Name", "ARK map identifier (e.g. TheIsland, Ragnarok).", "SERVER_MAP", "TheIsland", rules="required|alpha_dash|max:64"),
                VariableSpec("Session Name", "Server name shown in browser.", "SESSION_NAME", "Vietnam Hosting ARK", rules="required|string|max:64"),
                VariableSpec("Query Port", "Steam query UDP allocation port.", "QUERY_PORT", "27015", rules="required|integer|between:1024,65535"),
                VariableSpec("Max Players", "Player slot count.", "MAX_PLAYERS", "20", rules="required|integer|between:1,127"),
            ]),
            upstream_license="Studio Wildcard EULA",
            upstream_url="https://ark.wiki.gg/wiki/Dedicated_server_setup",
            steam_app_id=376030,
            notes="AMD64 only. Note: ARK: Survival Ascended (2430930) requires Wine/Proton and is not included here.",
        ),

        # 21. Counter-Strike 2
        EggSpec(
            id="cs2",
            name="Vietnam Hosting — Counter-Strike 2",
            category="game-servers",
            description="Official Valve Counter-Strike 2 Linux dedicated server via SteamCMD (AppID 730, AMD64 only, requires Steam GSLT).",
            icon="cs2",
            supported_versions=["Latest SteamCMD (AppID 730)"],
            supported_architectures=["amd64"],
            minimum_ram_mb=2048,
            recommended_ram_mb=4096,
            minimum_disk_mb=40960,
            resource_basis="upstream_documented",
            image_source="upstream_official_yolk",
            features=["gsl_token", "steam_disk_space"],
            docker_images=STEAM_SOURCE_IMAGE,
            startup='exec ./game/bin/linuxsteamrt64/cs2 -dedicated -ip 0.0.0.0 -port {{SERVER_PORT}} +map "${SRCDS_MAP}" -maxplayers "${MAX_PLAYERS}" +sv_setsteamaccount "${STEAM_ACC}"',
            stop="quit",
            startup_done="Connection to Steam servers successful|SV:  Spawn Server",
            install_body=STEAMCMD_INSTALL_SNIPPET + '\n',
            variables=_steam_vars(730, [
                VariableSpec("Start Map", "Initial CS2 map (e.g. de_dust2, de_mirage).", "SRCDS_MAP", "de_dust2", rules="required|alpha_dash|max:64"),
                VariableSpec("Max Players", "Maximum players.", "MAX_PLAYERS", "16", rules="required|integer|between:2,64"),
                VariableSpec("Steam GSLT Token", "Valve Game Server Login Token (never logged).", "STEAM_ACC", "", rules="nullable|string|max:128"),
            ]),
            upstream_license="Valve Steam Subscriber Agreement",
            upstream_url="https://developer.valvesoftware.com/wiki/Counter-Strike_2/Dedicated_Servers",
            steam_app_id=730,
            notes="AMD64 only. Requires >= 40 GiB disk space for CS2 depot.",
        ),

        # 22. Project Zomboid
        EggSpec(
            id="project-zomboid",
            name="Vietnam Hosting — Project Zomboid",
            category="game-servers",
            description="Official Project Zomboid Linux dedicated server via SteamCMD (AppID 380870, AMD64 only).",
            icon="zomboid",
            supported_versions=["Latest SteamCMD (AppID 380870)"],
            supported_architectures=["amd64"],
            minimum_ram_mb=2048,
            recommended_ram_mb=4096,
            minimum_disk_mb=8192,
            resource_basis="upstream_documented",
            image_source="upstream_official_yolk",
            features=["steam_disk_space"],
            docker_images=STEAM_SOURCE_IMAGE,
            startup='exec ./start-server.sh -cachedir=/home/container/.cache -servername "${SERVER_NAME}" -port {{SERVER_PORT}} -adminpassword "${ADMIN_PASSWORD}"',
            stop="quit",
            startup_done="SERVER STARTED",
            install_body=STEAMCMD_INSTALL_SNIPPET + '\nmkdir -p /mnt/server/.cache\n',
            variables=_steam_vars(380870, [
                VariableSpec("Server Config Name", "Zomboid server configuration name.", "SERVER_NAME", "servertest", rules="required|alpha_dash|max:64"),
                VariableSpec("Admin Password", "Initial admin password (set strong password; never default).", "ADMIN_PASSWORD", "", rules="required|string|min:8|max:128"),
            ]),
            upstream_license="The Indie Stone EULA",
            upstream_url="https://pzwiki.net/wiki/Dedicated_server",
            steam_app_id=380870,
            notes="AMD64 only. Requires UDP {{SERVER_PORT}} and {{SERVER_PORT}}+1.",
        ),

        # 23. Don't Starve Together
        EggSpec(
            id="dont-starve-together",
            name="Vietnam Hosting — Don't Starve Together",
            category="game-servers",
            description="Official Klei Don't Starve Together dedicated server via SteamCMD (AppID 343050, AMD64 only, requires Klei cluster token).",
            icon="dst",
            supported_versions=["Latest SteamCMD (AppID 343050)"],
            supported_architectures=["amd64"],
            minimum_ram_mb=1024,
            recommended_ram_mb=2048,
            minimum_disk_mb=4096,
            resource_basis="upstream_documented",
            image_source="upstream_official_yolk",
            features=["steam_disk_space"],
            docker_images=STEAM_SOURCE_IMAGE,
            startup='mkdir -p "/home/container/DoNotStarveTogether/${CLUSTER_NAME}"; if [[ -n "${CLUSTER_TOKEN}" ]]; then printf "%s" "${CLUSTER_TOKEN}" > "/home/container/DoNotStarveTogether/${CLUSTER_NAME}/cluster_token.txt"; chmod 600 "/home/container/DoNotStarveTogether/${CLUSTER_NAME}/cluster_token.txt"; fi; cd bin64 && exec ./dontstarve_dedicated_server_nullrenderer_x64 -persistent_storage_root /home/container -conf_dir DoNotStarveTogether -cluster "${CLUSTER_NAME}" -shard "${SHARD_NAME}" -port {{SERVER_PORT}}',
            stop="c_shutdown()",
            startup_done="Sim paused|Your Server Will Not Start|Registering master server",
            install_body=STEAMCMD_INSTALL_SNIPPET + '\nmkdir -p /mnt/server/DoNotStarveTogether/Cluster_1/Master\n',
            variables=_steam_vars(343050, [
                VariableSpec("Cluster Name", "DST cluster folder name.", "CLUSTER_NAME", "Cluster_1", rules="required|alpha_dash|max:64"),
                VariableSpec("Shard Name", "Shard name (Master or Caves).", "SHARD_NAME", "Master", rules="required|string|in:Master,Caves"),
                VariableSpec("Klei Cluster Token", "Cluster token from accounts.klei.com (never logged).", "CLUSTER_TOKEN", "", rules="nullable|string|max:256"),
            ]),
            upstream_license="Klei Entertainment EULA",
            upstream_url="https://accounts.klei.com",
            steam_app_id=343050,
            notes="AMD64 only.",
        ),

        # 24. Team Fortress 2
        EggSpec(
            id="tf2",
            name="Vietnam Hosting — Team Fortress 2",
            category="game-servers",
            description="Official Valve Team Fortress 2 SRCDS Linux server via SteamCMD (AppID 232250, AMD64 only).",
            icon="tf2",
            supported_versions=["Latest SteamCMD (AppID 232250)"],
            supported_architectures=["amd64"],
            minimum_ram_mb=1024,
            recommended_ram_mb=2048,
            minimum_disk_mb=14336,
            resource_basis="upstream_documented",
            image_source="upstream_official_yolk",
            features=["gsl_token", "steam_disk_space"],
            docker_images=STEAM_SOURCE_IMAGE,
            startup='exec ./srcds_run_64 -game tf -console -port {{SERVER_PORT}} +ip 0.0.0.0 +map "${SRCDS_MAP}" +maxplayers "${MAX_PLAYERS}" +sv_setsteamaccount "${STEAM_ACC}" -strictportbind -norestart',
            stop="quit",
            startup_done="VAC secure mode is activated|Connection to Steam servers successful",
            install_body=STEAMCMD_INSTALL_SNIPPET + '\n',
            variables=_steam_vars(232250, [
                VariableSpec("Start Map", "Initial TF2 map.", "SRCDS_MAP", "cp_dustbowl", rules="required|alpha_dash|max:64"),
                VariableSpec("Max Players", "Player slots (2-32).", "MAX_PLAYERS", "24", rules="required|integer|between:2,32"),
                VariableSpec("Steam GSLT Token", "Game Server Login Token (never logged).", "STEAM_ACC", "", rules="nullable|string|max:128"),
            ]),
            upstream_license="Valve Steam Subscriber Agreement",
            upstream_url="https://wiki.teamfortress.com/wiki/Linux_dedicated_server",
            steam_app_id=232250,
            notes="AMD64 only.",
        ),

        # 25. FiveM
        EggSpec(
            id="fivem",
            name="Vietnam Hosting — FiveM (Cfx.re FXServer)",
            category="game-servers",
            description="Official Cfx.re FiveM Linux x86_64 FXServer runtime with txAdmin port option and Cfx.re license key (AMD64 only).",
            icon="fivem",
            supported_versions=["Official Cfx.re Linux Artifacts"],
            supported_architectures=["amd64"],
            minimum_ram_mb=2048,
            recommended_ram_mb=4096,
            minimum_disk_mb=8192,
            resource_basis="recommended_estimate",
            image_source="upstream_official_yolk",
            docker_images={"Debian Official Yolk (AMD64)": "ghcr.io/pterodactyl/yolks:debian"},
            custom_docker_images={"Base Debian 13 (AMD64)": f"{GHCR_NAMESPACE}:base_debian13"},
            startup='exec ./alpine/opt/cfx-server/ld-musl-x86_64.so.1 --library-path "./alpine/usr/lib/v8/:./alpine/lib/:./alpine/usr/lib/" -- ./alpine/opt/cfx-server/FXServer +set citizen_dir /home/container/alpine/opt/cfx-server/citizen/ +set sv_licenseKey "${FIVEM_LICENSE}" +set netPort {{SERVER_PORT}} +exec server.cfg',
            stop="quit",
            startup_done="Started resource|Authenticated with cfx.re Nucleus",
            install_body=SAFE_DOWNLOAD_HELPER + r'''
if [[ "$(uname -m)" != "x86_64" ]]; then
    echo "[VNH][INSTALL][ERROR] Cfx.re FXServer Linux artifacts support x86_64 (amd64) only." >&2
    exit 1
fi
ART_URL="${FIVEM_ARTIFACT_URL:-}"
if [[ -z "${ART_URL}" ]]; then
    CHANGELOG="$(curl -fsSL https://changelogs-live.fivem.net/api/changelog/versions/linux/server)"
    ART_URL="$(printf '%s' "${CHANGELOG}" | jq -r '.recommended_download')"
fi
vnh_download "${ART_URL}" "/tmp/fx.tar.xz"
tar -xf /tmp/fx.tar.xz -C /mnt/server
rm -f /tmp/fx.tar.xz
if [[ ! -f /mnt/server/server.cfg ]]; then
    cat > /mnt/server/server.cfg <<'EOF'
endpoint_add_tcp "0.0.0.0:{{SERVER_PORT}}"
endpoint_add_udp "0.0.0.0:{{SERVER_PORT}}"
sv_hostname "Vietnam Hosting FiveM Server"
sv_maxclients 32
EOF
fi
''',
            variables=[
                VariableSpec("Cfx.re License Key", "Official license key from portal.cfx.re (never logged).", "FIVEM_LICENSE", "", rules="nullable|string|max:128"),
                VariableSpec("Custom Artifact URL", "Optional direct https://runtime.fivem.net/artifacts/... URL.", "FIVEM_ARTIFACT_URL", "", rules="nullable|string|max:512"),
            ],
            upstream_license="Cfx.re Terms of Service",
            upstream_url="https://docs.fivem.net",
            eula_required=True,
            notes="AMD64 only. Requires valid Cfx.re keymaster license key.",
        ),

        # 26. MTA:SA
        EggSpec(
            id="mta-sa",
            name="Vietnam Hosting — MTA:SA Server",
            category="game-servers",
            description="Official Multi Theft Auto: San Andreas Linux x64 server downloaded from linux.multitheftauto.com (AMD64 only).",
            icon="mtasa",
            supported_versions=["1.6.x Linux x64"],
            supported_architectures=["amd64"],
            minimum_ram_mb=512,
            recommended_ram_mb=1024,
            minimum_disk_mb=2048,
            image_source="upstream_official_yolk",
            docker_images={"Debian Official Yolk (AMD64)": "ghcr.io/pterodactyl/yolks:debian"},
            custom_docker_images={"Base Debian 13 (AMD64)": f"{GHCR_NAMESPACE}:base_debian13"},
            startup='exec ./mta-server64 -n -t --port {{SERVER_PORT}} --httpport "${HTTP_PORT}" --maxplayers "${MAX_PLAYERS}"',
            stop="shutdown",
            startup_done="Server started and is ready to accept connections!",
            install_body=SAFE_DOWNLOAD_HELPER + r'''
if [[ "$(uname -m)" != "x86_64" ]]; then
    echo "[VNH][INSTALL][ERROR] MTA:SA Linux server binaries are x86_64 (amd64) only." >&2
    exit 1
fi
vnh_download "https://linux.multitheftauto.com/dl/multitheftauto_linux_x64.tar.gz" "/tmp/mta.tar.gz"
tar -xzf /tmp/mta.tar.gz --strip-components=1 -C /mnt/server
rm -f /tmp/mta.tar.gz
if [[ ! -f /mnt/server/mods/deathmatch/mtaserver.conf ]]; then
    vnh_download "https://linux.multitheftauto.com/dl/baseconfig.tar.gz" "/tmp/mta-cfg.tar.gz"
    mkdir -p /mnt/server/mods/deathmatch
    tar -xzf /tmp/mta-cfg.tar.gz --strip-components=1 -C /mnt/server/mods/deathmatch
    rm -f /tmp/mta-cfg.tar.gz
fi
chmod +x /mnt/server/mta-server64
''',
            variables=[
                VariableSpec("HTTP Download Port", "Additional allocation port for MTA HTTP resource downloads.", "HTTP_PORT", "22005", rules="required|integer|between:1024,65535"),
                VariableSpec("Max Players", "Player slot count.", "MAX_PLAYERS", "32", rules="required|integer|between:1,4096"),
            ],
            upstream_license="GPL-3.0",
            upstream_url="https://multitheftauto.com",
            notes="AMD64 only.",
        ),

        # 27. Unturned
        EggSpec(
            id="unturned",
            name="Vietnam Hosting — Unturned Dedicated Server",
            category="game-servers",
            description="Official Smartly Dressed Games Unturned Linux Dedicated Server via SteamCMD (AppID 1110390, AMD64 only).",
            icon="unturned",
            supported_versions=["Latest SteamCMD (AppID 1110390)"],
            supported_architectures=["amd64"],
            minimum_ram_mb=2048,
            recommended_ram_mb=4096,
            minimum_disk_mb=6144,
            resource_basis="upstream_documented",
            image_source="upstream_official_yolk",
            features=["steam_disk_space"],
            docker_images=STEAM_SOURCE_IMAGE,
            startup='exec ./Unturned_Headless.x86_64 -batchmode -nographics "+InternetServer/${SERVER_ID}" -Port {{SERVER_PORT}}',
            stop="shutdown",
            startup_done="Loading level:|Server is ready",
            install_body=STEAMCMD_INSTALL_SNIPPET + '\nchmod +x /mnt/server/Unturned_Headless.x86_64 2>/dev/null || true\n',
            variables=_steam_vars(1110390, [
                VariableSpec("Server Instance ID", "Unturned server folder name under Servers/.", "SERVER_ID", "VietnamHosting", rules="required|alpha_dash|max:64"),
            ]),
            upstream_license="Smartly Dressed Games EULA",
            upstream_url="https://docs.smartlydressedgames.com",
            steam_app_id=1110390,
            notes="AMD64 only. Uses Dedicated Server AppID 1110390 (not client AppID 304930).",
        ),

        # 28. Mindustry
        EggSpec(
            id="mindustry",
            name="Vietnam Hosting — Mindustry Server",
            category="game-servers",
            description="Open-source Java Mindustry dedicated server downloaded from official Anuken/Mindustry GitHub Releases (AMD64 & ARM64).",
            icon="mindustry",
            supported_versions=["v146+ (Java 17/21)"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=512,
            recommended_ram_mb=1024,
            minimum_disk_mb=1024,
            image_source="hybrid_official_and_ghcr",
            dockerfile_path="docker/languages/java/21/Dockerfile",
            features=["java_version", "pid_limit"],
            docker_images=MC_JAVA_IMAGES,
            custom_docker_images=MC_CUSTOM_IMAGES,
            startup='MEM={{SERVER_MEMORY}}; HEAP=$(( MEM * 75 / 100 )); (( HEAP < 256 )) && HEAP=256; exec java -Xms128M -Xmx"${HEAP}M" -jar server-release.jar "config port {{SERVER_PORT}},host ${MAP_NAME} ${GAMEMODE}"',
            stop="exit",
            startup_done="Opened a server on port",
            install_body=SAFE_DOWNLOAD_HELPER + r'''
JAR_URL="$(curl -fsSL https://api.github.com/repos/Anuken/Mindustry/releases/latest | jq -r '.assets[] | select(.name == "server-release.jar") | .browser_download_url' | head -n1)"
vnh_download "${JAR_URL}" "/mnt/server/server-release.jar"
''',
            variables=[
                VariableSpec("Map Name", "Initial map name to host.", "MAP_NAME", "Ancient_Caldera", rules="required|string|max:64"),
                VariableSpec("Gamemode", "Mindustry gamemode.", "GAMEMODE", "survival", rules="required|string|in:survival,sandbox,attack,pvp"),
            ],
            upstream_license="GPL-3.0",
            upstream_url="https://mindustrygame.github.io",
        ),

        # 29. OpenTTD
        EggSpec(
            id="openttd",
            name="Vietnam Hosting — OpenTTD Dedicated Server",
            category="game-servers",
            description="Open-source OpenTTD dedicated transport simulation server running natively on both AMD64 and ARM64.",
            icon="openttd",
            supported_versions=["14.x (Debian 13 Package)"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=256,
            recommended_ram_mb=512,
            minimum_disk_mb=1024,
            image_source="requires_ghcr_build",
            dockerfile_path="docker/services/openttd/Dockerfile",
            docker_images={"OpenTTD 14 (Vietnam Hosting GHCR)": f"{GHCR_NAMESPACE}:openttd_14"},
            custom_docker_images={"OpenTTD 14": f"{GHCR_NAMESPACE}:openttd_14"},
            startup='mkdir -p /home/container/.openttd; exec openttd -D "0.0.0.0:{{SERVER_PORT}}" -c /home/container/openttd.cfg',
            stop="exit",
            startup_done="Game started|Map generated",
            install_body='mkdir -p /mnt/server/.openttd /mnt/server/save\nif [[ ! -f /mnt/server/openttd.cfg ]]; then printf "[network]\\nserver_name = Vietnam Hosting OpenTTD\\n" > /mnt/server/openttd.cfg; fi\n',
            variables=[],
            upstream_license="GPL-2.0",
            upstream_url="https://www.openttd.org",
        ),
    ]
