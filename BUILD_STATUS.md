# Vietnam Hosting Universal Eggs — Build Status

> **Project:** Vietnam Hosting Universal Pterodactyl Egg System  
> **Website:** https://vietnam-hosting.net  
> **Target Panel Schema:** `PTDL_v1` & `PTDL_v2` (Pterodactyl Panel 1.0–1.12+ & Wings)  
> **Last Updated:** 2026-11-24

## Phase Progress

| Phase | Description | Status | Notes |
| :--- | :--- | :--- | :--- |
| **Phase 1** | Architecture, JSON Schemas, Templates, Core Runtime (`core/`), `vnh-egg` CLI Generator | `COMPLETED` | Strict PTDL_v2/metadata/catalog schemas, 6 core runtime scripts, 10-command CLI |
| **Phase 2** | Programming Language Eggs (26 languages) + Dockerfiles + Examples | `COMPLETED` | Python 3.10–3.14, Node 20–26, Bun, Deno, Java 8–25, Rust, Go, C/C++, .NET 8–11, PHP 8.2–8.5 + 16 languages |
| **Phase 3** | Linux Operating System Eggs (15 distros) + NAT Linux Hosting Module | `COMPLETED` | Unprivileged Dropbear/OpenSSH, persistent keys, Wings SFTP, strict Container vs KVM VPS documentation |
| **Phase 4** | Discord Bot & Automation (17), Web Hosting (22), Database Hosting (14) Eggs | `COMPLETED` | Total 53 service eggs with secret redaction, strong random passwords, SQLite workspace honesty |
| **Phase 5** | Game Server Eggs (29: 13 Minecraft + 16 Other Games) + Application & Utility Eggs (24) | `COMPLETED` | Verified SteamCMD AppIDs, official Mojang/PaperMC/Purpur/Fabric/NeoForge/Spigot BuildTools APIs, accurate AMD64/ARM64 matrix |
| **Phase 6** | GitHub Actions CI/CD (6 workflows), Security Policies, Catalog API & Static Filter UI/API | `COMPLETED` | `validate`, `build-images`, `security-scan`, `test-eggs`, `release`, `check-updates`, Trivy, Wings hardening, Catalog API |
| **Phase 7** | Automated Validation, Test Reports, Vietnamese Documentation, Packaging (`vietnam-hosting-universal-eggs.zip`) | `COMPLETED` | All 147 eggs & 90 Dockerfiles validated (`0 errors, 0 warnings`); live Docker/Pterodactyl checks honestly marked `UNVERIFIED` |

## Inventory Summary

- **Total Eggs Generated:** 147 (`languages`: 26, `operating-systems`: 15, `discord-bots`: 17, `web-hosting`: 22, `databases`: 14, `game-servers`: 29, `applications`: 19, `utilities`: 5)
- **Total Pinned Dockerfiles Generated:** 90 (`docker/base`, `docker/installers`, `docker/languages`, `docker/linux`, `docker/services`)
- **Architecture Matrix:** 147 AMD64 supported / 131 ARM64 supported / 16 AMD64-only
- **Release Package:** `dist/vietnam-hosting-universal-eggs.zip` (+ `.sha256` + `package-manifest.json` + exported `dist/eggs/`)
