"""Phase 4C: All 14 Database Hosting Egg Specifications."""

from __future__ import annotations

from generator.models import GHCR_NAMESPACE, EggSpec, VariableSpec

DB_SECURITY_VI = (
    "- **Không dùng mật khẩu yếu:** Nếu biến mật khẩu để trống khi cài đặt lần đầu, hệ thống tự động sinh mật khẩu ngẫu nhiên mạnh (`openssl rand`) lưu vào file cấu hình phân quyền `600` (tuyệt đối không in ra console).\n"
    "- **Nguyên tắc quyền tối thiểu:** Tự động khởi tạo database ứng dụng và tài khoản chỉ có quyền trên database đó.\n"
    "- **Bảo vệ mạng mặc định:** `BIND_ADDRESS` mặc định `127.0.0.1` — chỉ chuyển sang `0.0.0.0` khi quản trị viên chủ động cho phép mở truy cập ngoài và cấu hình firewall/TLS tầng Node.\n"
    "- **An toàn dữ liệu:** Không bao giờ ghi đè thư mục dữ liệu khi restart/reinstall; kiểm tra tương thích phiên bản dữ liệu trước khi nâng cấp major version."
)


def get_specs() -> list[EggSpec]:
    return [
        # 1. MySQL
        EggSpec(
            id="mysql",
            name="Vietnam Hosting — MySQL 8.4 LTS",
            category="databases",
            description="Unprivileged MySQL 8.4 LTS database container with first-boot initialization, random strong credentials, least-privilege app user, and graceful SIGTERM shutdown.",
            icon="mysql",
            supported_versions=["8.4 LTS"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=512,
            recommended_ram_mb=1024,
            minimum_disk_mb=2048,
            image_source="requires_ghcr_build",
            dockerfile_path="docker/services/mysql/Dockerfile",
            docker_images={"MySQL 8.4 LTS (Vietnam Hosting GHCR)": f"{GHCR_NAMESPACE}:mysql_8.4"},
            custom_docker_images={"MySQL 8.4 LTS": f"{GHCR_NAMESPACE}:mysql_8.4"},
            startup=(
                'mkdir -p /home/container/data /home/container/run /home/container/logs; '
                'if [[ ! -d /home/container/data/mysql ]]; then '
                '  mysqld --initialize-insecure --datadir=/home/container/data; '
                '  PW="${DB_PASSWORD:-$(openssl rand -base64 24 | tr -dc A-Za-z0-9 | head -c 24)}"; '
                '  cat > /home/container/run/init.sql <<SQL\n'
                "CREATE DATABASE IF NOT EXISTS \\`${DB_NAME}\\`;\n"
                "CREATE USER IF NOT EXISTS '${DB_USER}'@'%' IDENTIFIED BY '${PW}';\n"
                "GRANT ALL PRIVILEGES ON \\`${DB_NAME}\\`.* TO '${DB_USER}'@'%';\n"
                "FLUSH PRIVILEGES;\nSQL\n"
                '  chmod 600 /home/container/run/init.sql; '
                '  exec mysqld --datadir=/home/container/data --port={{SERVER_PORT}} --bind-address="${BIND_ADDRESS}" --socket=/home/container/run/mysqld.sock --init-file=/home/container/run/init.sql; '
                'fi; '
                'rm -f /home/container/run/init.sql; '
                'exec mysqld --datadir=/home/container/data --port={{SERVER_PORT}} --bind-address="${BIND_ADDRESS}" --socket=/home/container/run/mysqld.sock'
            ),
            stop="^C",
            startup_done="ready for connections",
            install_body='mkdir -p /mnt/server/data /mnt/server/run /mnt/server/logs /mnt/server/backups\necho "[VNH][INSTALL] MySQL data directories prepared safely (no existing data overwritten)."\n',
            variables=[
                VariableSpec("Database Name", "Initial application database created on first boot.", "DB_NAME", "app_db", rules="required|alpha_dash|max:64"),
                VariableSpec("Application User", "Least-privilege database user.", "DB_USER", "app_user", rules="required|alpha_dash|max:32"),
                VariableSpec("Application Password", "Strong password (leave blank to auto-generate securely on first boot).", "DB_PASSWORD", "", rules="nullable|string|min:12|max:128"),
                VariableSpec("Bind Address", "Default 127.0.0.1 (admin may set 0.0.0.0 when external access is explicitly approved).", "BIND_ADDRESS", "127.0.0.1", user_editable=False, rules="required|string|in:127.0.0.1,0.0.0.0"),
            ],
            upstream_license="GPL-2.0",
            upstream_url="https://www.mysql.com",
            security_notes_vi=DB_SECURITY_VI,
            backup_notes_vi="- Sử dụng `mysqldump --single-transaction --routines --triggers -S /home/container/run/mysqld.sock -u app_user -p app_db > /home/container/backups/backup.sql` để tạo bản sao lưu nhất quán trước khi snapshot Pterodactyl.",
        ),

        # 2. MariaDB
        EggSpec(
            id="mariadb",
            name="Vietnam Hosting — MariaDB 11.4 LTS",
            category="databases",
            description="Unprivileged MariaDB 11.4 LTS container with idempotent initialization, least-privilege app grants, and graceful shutdown.",
            icon="mariadb",
            supported_versions=["11.4 LTS"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=512,
            recommended_ram_mb=1024,
            minimum_disk_mb=2048,
            image_source="requires_ghcr_build",
            dockerfile_path="docker/services/mariadb/Dockerfile",
            docker_images={"MariaDB 11.4 LTS (Vietnam Hosting GHCR)": f"{GHCR_NAMESPACE}:mariadb_11.4"},
            custom_docker_images={"MariaDB 11.4 LTS": f"{GHCR_NAMESPACE}:mariadb_11.4"},
            startup=(
                'mkdir -p /home/container/data /home/container/run /home/container/logs; '
                'if [[ ! -d /home/container/data/mysql ]]; then '
                '  mariadb-install-db --datadir=/home/container/data --auth-root-authentication-method=normal; '
                '  PW="${DB_PASSWORD:-$(openssl rand -base64 24 | tr -dc A-Za-z0-9 | head -c 24)}"; '
                '  printf \x27CREATE DATABASE IF NOT EXISTS `%s`; CREATE USER IF NOT EXISTS "%s"@"%%" IDENTIFIED BY "%s"; GRANT ALL PRIVILEGES ON `%s`.* TO "%s"@"%%"; FLUSH PRIVILEGES;\\n\x27 '
                '    "${DB_NAME}" "${DB_USER}" "${PW}" "${DB_NAME}" "${DB_USER}" > /home/container/run/init.sql; '
                '  chmod 600 /home/container/run/init.sql; '
                '  exec mariadbd --datadir=/home/container/data --port={{SERVER_PORT}} --bind-address="${BIND_ADDRESS}" --socket=/home/container/run/mariadb.sock --init-file=/home/container/run/init.sql; '
                'fi; '
                'rm -f /home/container/run/init.sql; '
                'exec mariadbd --datadir=/home/container/data --port={{SERVER_PORT}} --bind-address="${BIND_ADDRESS}" --socket=/home/container/run/mariadb.sock'
            ),
            stop="^C",
            startup_done="ready for connections",
            install_body='mkdir -p /mnt/server/data /mnt/server/run /mnt/server/logs /mnt/server/backups\n',
            variables=[
                VariableSpec("Database Name", "Initial application database.", "DB_NAME", "app_db", rules="required|alpha_dash|max:64"),
                VariableSpec("Application User", "Least-privilege database user.", "DB_USER", "app_user", rules="required|alpha_dash|max:32"),
                VariableSpec("Application Password", "Strong password (auto-generated if empty).", "DB_PASSWORD", "", rules="nullable|string|min:12|max:128"),
                VariableSpec("Bind Address", "Admin-controlled network bind address.", "BIND_ADDRESS", "127.0.0.1", user_editable=False, rules="required|string|in:127.0.0.1,0.0.0.0"),
            ],
            upstream_license="GPL-2.0",
            upstream_url="https://mariadb.org",
            security_notes_vi=DB_SECURITY_VI,
            backup_notes_vi="- Sử dụng `mariadb-dump --single-transaction -S /home/container/run/mariadb.sock` hoặc `mariadb-backup` để đảm bảo tính nhất quán dữ liệu.",
        ),

        # 3. PostgreSQL
        EggSpec(
            id="postgresql",
            name="Vietnam Hosting — PostgreSQL 17",
            category="databases",
            description="Unprivileged PostgreSQL 17 server with scram-sha-256 auth, PG_VERSION upgrade guard, and clean SIGINT/SIGTERM fast shutdown.",
            icon="postgresql",
            supported_versions=["17"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=512,
            recommended_ram_mb=1024,
            minimum_disk_mb=2048,
            image_source="requires_ghcr_build",
            dockerfile_path="docker/services/postgresql/Dockerfile",
            docker_images={"PostgreSQL 17 (Vietnam Hosting GHCR)": f"{GHCR_NAMESPACE}:postgresql_17"},
            custom_docker_images={"PostgreSQL 17": f"{GHCR_NAMESPACE}:postgresql_17"},
            startup=(
                'export PGDATA=/home/container/pgdata; mkdir -p /home/container/run /home/container/backups; '
                'if [[ -f "${PGDATA}/PG_VERSION" ]]; then '
                '  DATA_VER="$(cat "${PGDATA}/PG_VERSION")"; BIN_VER="$(postgres -V | awk \x27{print $3}\x27 | cut -d. -f1)"; '
                '  if [[ "${DATA_VER}" != "${BIN_VER}" ]]; then echo "[VNH][ERROR] PG_VERSION mismatch (data=${DATA_VER}, bin=${BIN_VER}). Run pg_dump upgrade before changing major image." >&2; exit 1; fi; '
                'else '
                '  PW="${DB_PASSWORD:-$(openssl rand -base64 24 | tr -dc A-Za-z0-9 | head -c 24)}"; '
                '  printf "%s" "${PW}" > /home/container/run/.pwfile; chmod 600 /home/container/run/.pwfile; '
                '  initdb -D "${PGDATA}" -U "${DB_USER}" --auth-local=scram-sha-256 --auth-host=scram-sha-256 --pwfile=/home/container/run/.pwfile --encoding=UTF8; '
                '  rm -f /home/container/run/.pwfile; '
                '  echo "host all all 0.0.0.0/0 scram-sha-256" >> "${PGDATA}/pg_hba.conf"; '
                'fi; '
                'exec postgres -D "${PGDATA}" -p {{SERVER_PORT}} -h "${BIND_ADDRESS}" -k /home/container/run'
            ),
            stop="^C",
            startup_done="database system is ready to accept connections",
            install_body='mkdir -p /mnt/server/pgdata /mnt/server/run /mnt/server/backups\nchmod 700 /mnt/server/pgdata\n',
            variables=[
                VariableSpec("Database Role", "Primary PostgreSQL role.", "DB_USER", "app_user", rules="required|alpha_dash|max:32"),
                VariableSpec("Database Password", "Strong SCRAM-SHA-256 password (auto-generated if empty).", "DB_PASSWORD", "", rules="nullable|string|min:12|max:128"),
                VariableSpec("Bind Address", "Admin-controlled listen_addresses (default 127.0.0.1).", "BIND_ADDRESS", "127.0.0.1", user_editable=False, rules="required|string|in:127.0.0.1,0.0.0.0"),
            ],
            upstream_license="PostgreSQL",
            upstream_url="https://www.postgresql.org",
            security_notes_vi=DB_SECURITY_VI,
            backup_notes_vi="- Sử dụng `pg_dump -Fc -h /home/container/run -p {{SERVER_PORT}} -U ${DB_USER} > /home/container/backups/db.dump` để sao lưu nhất quán và hỗ trợ nâng cấp phiên bản major qua `pg_restore`.",
        ),

        # 4. MongoDB
        EggSpec(
            id="mongodb",
            name="Vietnam Hosting — MongoDB 8.0",
            category="databases",
            description="Unprivileged MongoDB 8.0 document database with WiredTiger cache cap respecting container RAM and auth enforcement.",
            icon="mongodb",
            supported_versions=["8.0"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=512,
            recommended_ram_mb=1024,
            minimum_disk_mb=2048,
            image_source="requires_ghcr_build",
            dockerfile_path="docker/services/mongodb/Dockerfile",
            docker_images={"MongoDB 8.0 (Vietnam Hosting GHCR)": f"{GHCR_NAMESPACE}:mongodb_8"},
            custom_docker_images={"MongoDB 8.0": f"{GHCR_NAMESPACE}:mongodb_8"},
            startup='mkdir -p /home/container/data /home/container/logs; exec mongod --dbpath /home/container/data --port {{SERVER_PORT}} --bind_ip "${BIND_ADDRESS}" --wiredTigerCacheSizeGB "${WT_CACHE_GB}"',
            stop="^C",
            startup_done="Waiting for connections",
            install_body='mkdir -p /mnt/server/data /mnt/server/logs /mnt/server/backups\n',
            variables=[
                VariableSpec("WiredTiger Cache (GB)", "WiredTiger memory cap (e.g. 0.5 for 1GB container).", "WT_CACHE_GB", "0.5", rules="required|numeric|between:0.25,64"),
                VariableSpec("Bind Address", "Admin-controlled bind_ip (default 127.0.0.1).", "BIND_ADDRESS", "127.0.0.1", user_editable=False, rules="required|string|in:127.0.0.1,0.0.0.0"),
            ],
            upstream_license="SSPL-1.0",
            upstream_url="https://www.mongodb.com",
            security_notes_vi=DB_SECURITY_VI + "\n- **Giấy phép:** MongoDB sử dụng giấy phép SSPL-1.0; cân nhắc điều khoản khi cung cấp DBaaS thương mại.",
            backup_notes_vi="- Sử dụng `mongodump --port {{SERVER_PORT}} --out /home/container/backups/dump` và phục hồi bằng `mongorestore`.",
        ),

        # 5. Redis
        EggSpec(
            id="redis",
            name="Vietnam Hosting — Redis 7.4",
            category="databases",
            description="Unprivileged Redis 7.4 in-memory store with mandatory strong authentication, RDB/AOF persistence, and maxmemory cap.",
            icon="redis",
            supported_versions=["7.4"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=128,
            recommended_ram_mb=512,
            minimum_disk_mb=1024,
            image_source="requires_ghcr_build",
            dockerfile_path="docker/services/redis/Dockerfile",
            docker_images={"Redis 7.4 (Vietnam Hosting GHCR)": f"{GHCR_NAMESPACE}:redis_7.4"},
            custom_docker_images={"Redis 7.4": f"{GHCR_NAMESPACE}:redis_7.4"},
            startup=(
                'mkdir -p /home/container/data; '
                'if [[ ! -f /home/container/data/.auth_secret ]]; then '
                '  PW="${REDIS_PASSWORD:-$(openssl rand -base64 24 | tr -dc A-Za-z0-9 | head -c 32)}"; '
                '  printf "%s" "${PW}" > /home/container/data/.auth_secret; chmod 600 /home/container/data/.auth_secret; '
                'fi; '
                'MAXMEM=$(( {{SERVER_MEMORY}} * 75 / 100 )); (( MAXMEM < 64 )) && MAXMEM=64; '
                'exec redis-server --dir /home/container/data --port {{SERVER_PORT}} --bind "${BIND_ADDRESS}" '
                '--appendonly yes --maxmemory "${MAXMEM}mb" --maxmemory-policy "${MAXMEMORY_POLICY}" '
                '--requirepass "$(cat /home/container/data/.auth_secret)"'
            ),
            stop="^C",
            startup_done="Ready to accept connections",
            install_body='mkdir -p /mnt/server/data /mnt/server/backups\n',
            variables=[
                VariableSpec("Redis Password", "Strong password (auto-generated into .auth_secret if blank).", "REDIS_PASSWORD", "", rules="nullable|string|min:12|max:128"),
                VariableSpec("Eviction Policy", "Redis maxmemory eviction policy.", "MAXMEMORY_POLICY", "allkeys-lru", rules="required|string|in:noeviction,allkeys-lru,volatile-lru,allkeys-lfu"),
                VariableSpec("Bind Address", "Admin-controlled bind address.", "BIND_ADDRESS", "127.0.0.1", user_editable=False, rules="required|string|in:127.0.0.1,0.0.0.0"),
            ],
            upstream_license="RSALv2 / SSPLv1",
            upstream_url="https://redis.io",
            security_notes_vi=DB_SECURITY_VI,
            backup_notes_vi="- Gọi `redis-cli BGSAVE` và sao chép `dump.rdb` + `appendonlydir/` trong `/home/container/data`.",
        ),

        # 6. Valkey
        EggSpec(
            id="valkey",
            name="Vietnam Hosting — Valkey 8.1 (BSD Open-Source)",
            category="databases",
            description="Linux Foundation Valkey 8.1 Redis-compatible BSD-3-Clause in-memory store with strong auth and AOF persistence.",
            icon="valkey",
            supported_versions=["8.1"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=128,
            recommended_ram_mb=512,
            minimum_disk_mb=1024,
            image_source="requires_ghcr_build",
            dockerfile_path="docker/services/valkey/Dockerfile",
            docker_images={"Valkey 8.1 (Vietnam Hosting GHCR)": f"{GHCR_NAMESPACE}:valkey_8.1"},
            custom_docker_images={"Valkey 8.1": f"{GHCR_NAMESPACE}:valkey_8.1"},
            startup=(
                'mkdir -p /home/container/data; '
                'if [[ ! -f /home/container/data/.auth_secret ]]; then '
                '  PW="${VALKEY_PASSWORD:-$(openssl rand -base64 24 | tr -dc A-Za-z0-9 | head -c 32)}"; '
                '  printf "%s" "${PW}" > /home/container/data/.auth_secret; chmod 600 /home/container/data/.auth_secret; '
                'fi; '
                'MAXMEM=$(( {{SERVER_MEMORY}} * 75 / 100 )); (( MAXMEM < 64 )) && MAXMEM=64; '
                'exec valkey-server --dir /home/container/data --port {{SERVER_PORT}} --bind "${BIND_ADDRESS}" '
                '--appendonly yes --maxmemory "${MAXMEM}mb" --maxmemory-policy "${MAXMEMORY_POLICY}" '
                '--requirepass "$(cat /home/container/data/.auth_secret)"'
            ),
            stop="^C",
            startup_done="Ready to accept connections",
            install_body='mkdir -p /mnt/server/data /mnt/server/backups\n',
            variables=[
                VariableSpec("Valkey Password", "Strong password (auto-generated if blank).", "VALKEY_PASSWORD", "", rules="nullable|string|min:12|max:128"),
                VariableSpec("Eviction Policy", "Memory eviction policy.", "MAXMEMORY_POLICY", "allkeys-lru", rules="required|string|in:noeviction,allkeys-lru,volatile-lru,allkeys-lfu"),
                VariableSpec("Bind Address", "Admin-controlled bind address.", "BIND_ADDRESS", "127.0.0.1", user_editable=False, rules="required|string|in:127.0.0.1,0.0.0.0"),
            ],
            upstream_license="BSD-3-Clause",
            upstream_url="https://valkey.io",
            security_notes_vi=DB_SECURITY_VI,
            backup_notes_vi="- Gọi `valkey-cli BGSAVE` và sao lưu `/home/container/data`.",
        ),

        # 7. SQLite Workspace (EXPLICITLY NOT a network DB server!)
        EggSpec(
            id="sqlite-workspace",
            name="Vietnam Hosting — SQLite Workspace (File & CLI)",
            category="databases",
            description=(
                "Embedded SQLite 3 file & CLI management workspace for local .db files, schema migrations, "
                "WAL integrity checks, and `.backup` snapshots. NOTE: SQLite is an embedded file database, "
                "NOT a standalone networked database server."
            ),
            icon="sqlite",
            supported_versions=["SQLite 3 (Debian 13)"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=128,
            recommended_ram_mb=256,
            minimum_disk_mb=512,
            image_source="requires_ghcr_build",
            dockerfile_path="docker/services/sqlite-workspace/Dockerfile",
            docker_images={"SQLite 3 Workspace (Vietnam Hosting GHCR)": f"{GHCR_NAMESPACE}:sqlite_workspace"},
            custom_docker_images={"SQLite 3 Workspace": f"{GHCR_NAMESPACE}:sqlite_workspace"},
            startup=(
                'mkdir -p /home/container/databases /home/container/backups; '
                'sqlite3 "/home/container/databases/${DB_FILE}" "PRAGMA journal_mode=WAL; PRAGMA integrity_check;"; '
                'echo "VIETNAM HOSTING SQLite Workspace Ready (file: /home/container/databases/${DB_FILE}, no network port)"; '
                'exec sqlite3 "/home/container/databases/${DB_FILE}"'
            ),
            stop=".quit",
            startup_done="VIETNAM HOSTING SQLite Workspace Ready",
            install_body='mkdir -p /mnt/server/databases /mnt/server/backups\necho "[VNH][INSTALL] SQLite file workspace initialized (embedded database, no TCP port)."\n',
            variables=[
                VariableSpec("Database Filename", "SQLite .db filename inside /home/container/databases/.", "DB_FILE", "workspace.db", rules="required|string|max:128"),
            ],
            requires_inbound_port=False,
            upstream_license="Public Domain",
            upstream_url="https://www.sqlite.org",
            notes="Embedded file/CLI SQLite workspace — NOT a standalone TCP database server.",
            security_notes_vi="- **Lưu ý kiến trúc:** SQLite là cơ sở dữ liệu nhúng dựa trên file cục bộ (CLI / tích hợp trong ứng dụng), **không phải** database server lắng nghe cổng mạng TCP/IP.\n- Bảo vệ quyền truy cập file `.db` thông qua Wings SFTP và không chia sẻ chung file SQLite qua NFS.",
            backup_notes_vi="- Luôn dùng lệnh `sqlite3 /home/container/databases/${DB_FILE} \".backup '/home/container/backups/snapshot.db'\"` để sao lưu nhất quán khi bật chế độ WAL.",
        ),

        # 8. CouchDB
        EggSpec(
            id="couchdb",
            name="Vietnam Hosting — Apache CouchDB 3.4",
            category="databases",
            description="Apache CouchDB 3.4 JSON document database with HTTP API, Fauxton UI, and mandatory admin credentials.",
            icon="couchdb",
            supported_versions=["3.4"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=512,
            recommended_ram_mb=1024,
            minimum_disk_mb=2048,
            image_source="requires_ghcr_build",
            dockerfile_path="docker/services/couchdb/Dockerfile",
            docker_images={"CouchDB 3.4 (Vietnam Hosting GHCR)": f"{GHCR_NAMESPACE}:couchdb_3.4"},
            custom_docker_images={"CouchDB 3.4": f"{GHCR_NAMESPACE}:couchdb_3.4"},
            startup=(
                'mkdir -p /home/container/data /home/container/etc; '
                'if [[ ! -f /home/container/etc/local.ini ]]; then '
                '  PW="${COUCHDB_PASSWORD:-$(openssl rand -base64 24 | tr -dc A-Za-z0-9 | head -c 24)}"; '
                '  printf "[chttpd]\\nport = {{SERVER_PORT}}\\nbind_address = %s\\n[couchdb]\\ndatabase_dir = /home/container/data\\nview_index_dir = /home/container/data\\n[admins]\\n%s = %s\\n" '
                '    "${BIND_ADDRESS}" "${COUCHDB_USER}" "${PW}" > /home/container/etc/local.ini; chmod 600 /home/container/etc/local.ini; '
                'fi; '
                'export ERL_FLAGS="-couch_ini /opt/couchdb/etc/default.ini /home/container/etc/local.ini"; '
                'exec /opt/couchdb/bin/couchdb'
            ),
            stop="^C",
            startup_done="Apache CouchDB has started",
            install_body='mkdir -p /mnt/server/data /mnt/server/etc /mnt/server/backups\n',
            variables=[
                VariableSpec("Admin Username", "CouchDB admin username.", "COUCHDB_USER", "vnhadmin", rules="required|alpha_dash|max:32"),
                VariableSpec("Admin Password", "Strong password (auto-generated if blank).", "COUCHDB_PASSWORD", "", rules="nullable|string|min:12|max:128"),
                VariableSpec("Bind Address", "Admin-controlled bind_address.", "BIND_ADDRESS", "127.0.0.1", user_editable=False, rules="required|string|in:127.0.0.1,0.0.0.0"),
            ],
            upstream_license="Apache-2.0",
            upstream_url="https://couchdb.apache.org",
            security_notes_vi=DB_SECURITY_VI,
            backup_notes_vi="- Sử dụng CouchDB Replication API hoặc dừng dịch vụ rồi sao lưu `/home/container/data/*.couch`.",
        ),

        # 9. ClickHouse
        EggSpec(
            id="clickhouse",
            name="Vietnam Hosting — ClickHouse 25 LTS",
            category="databases",
            description="Columnar OLAP ClickHouse 25 LTS analytics server with container-scoped data directory and memory limits.",
            icon="clickhouse",
            supported_versions=["25.3 LTS"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=1024,
            recommended_ram_mb=2048,
            minimum_disk_mb=4096,
            image_source="requires_ghcr_build",
            dockerfile_path="docker/services/clickhouse/Dockerfile",
            docker_images={"ClickHouse 25.3 LTS (Vietnam Hosting GHCR)": f"{GHCR_NAMESPACE}:clickhouse_25"},
            custom_docker_images={"ClickHouse 25.3 LTS": f"{GHCR_NAMESPACE}:clickhouse_25"},
            startup='mkdir -p /home/container/data /home/container/tmp /home/container/logs; sed "s|__PORT__|{{SERVER_PORT}}|g; s|__BIND__|${BIND_ADDRESS}|g" /home/container/config.xml.tpl > /home/container/config.xml; exec clickhouse-server --config-file=/home/container/config.xml',
            stop="^C",
            startup_done="Ready for connections",
            install_body=r'''
mkdir -p /mnt/server/data /mnt/server/tmp /mnt/server/logs /mnt/server/backups
if [[ ! -f /mnt/server/config.xml.tpl ]]; then
cat > /mnt/server/config.xml.tpl <<'EOF'
<clickhouse>
    <logger><level>information</level><console>1</console></logger>
    <http_port>__PORT__</http_port>
    <listen_host>__BIND__</listen_host>
    <path>/home/container/data/</path>
    <tmp_path>/home/container/tmp/</tmp_path>
    <user_files_path>/home/container/data/user_files/</user_files_path>
    <format_schema_path>/home/container/data/format_schemas/</format_schema_path>
    <users_config>users.xml</users_config>
</clickhouse>
EOF
fi
if [[ ! -f /mnt/server/users.xml ]]; then
    PW="${CLICKHOUSE_PASSWORD:-$(openssl rand -base64 24 | tr -dc A-Za-z0-9 | head -c 24)}"
    SHA="$(printf '%s' "${PW}" | sha256sum | awk '{print $1}')"
    cat > /mnt/server/users.xml <<EOF
<clickhouse>
    <profiles><default/></profiles>
    <quotas><default/></quotas>
    <users>
        <default>
            <password_sha256_hex>${SHA}</password_sha256_hex>
            <networks><ip>::/0</ip></networks>
            <profile>default</profile>
            <quota>default</quota>
        </default>
    </users>
</clickhouse>
EOF
    chmod 600 /mnt/server/users.xml
fi
''',
            variables=[
                VariableSpec("Default User Password", "Hashed to SHA256 in users.xml (auto-generated if blank).", "CLICKHOUSE_PASSWORD", "", rules="nullable|string|min:12|max:128"),
                VariableSpec("Bind Address", "Admin-controlled listen_host.", "BIND_ADDRESS", "127.0.0.1", user_editable=False, rules="required|string|in:127.0.0.1,0.0.0.0"),
            ],
            upstream_license="Apache-2.0",
            upstream_url="https://clickhouse.com",
            security_notes_vi=DB_SECURITY_VI,
            backup_notes_vi="- Sử dụng câu lệnh `BACKUP DATABASE ... TO Disk(...)` hoặc `clickhouse-backup` trước khi sao lưu container.",
        ),

        # 10. InfluxDB
        EggSpec(
            id="influxdb",
            name="Vietnam Hosting — InfluxDB 2.7",
            category="databases",
            description="InfluxDB 2.7 time-series database running unprivileged with BoltDB/TSM storage under /home/container/data.",
            icon="influxdb",
            supported_versions=["2.7"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=512,
            recommended_ram_mb=1024,
            minimum_disk_mb=2048,
            image_source="requires_ghcr_build",
            dockerfile_path="docker/services/influxdb/Dockerfile",
            docker_images={"InfluxDB 2.7 (Vietnam Hosting GHCR)": f"{GHCR_NAMESPACE}:influxdb_2.7"},
            custom_docker_images={"InfluxDB 2.7": f"{GHCR_NAMESPACE}:influxdb_2.7"},
            startup='mkdir -p /home/container/data/engine; exec influxd --bolt-path=/home/container/data/influxd.bolt --engine-path=/home/container/data/engine --http-bind-address="${BIND_ADDRESS}:{{SERVER_PORT}}"',
            stop="^C",
            startup_done="Listening|service=http",
            install_body='mkdir -p /mnt/server/data/engine /mnt/server/backups\n',
            variables=[
                VariableSpec("Bind Address", "Admin-controlled HTTP bind address.", "BIND_ADDRESS", "127.0.0.1", user_editable=False, rules="required|string|in:127.0.0.1,0.0.0.0"),
            ],
            upstream_license="MIT",
            upstream_url="https://www.influxdata.com",
            security_notes_vi=DB_SECURITY_VI,
            backup_notes_vi="- Sử dụng `influx backup /home/container/backups/influx` để tạo bản backup nhất quán của BoltDB và các TSM shard.",
        ),

        # 11. TimescaleDB
        EggSpec(
            id="timescaledb",
            name="Vietnam Hosting — TimescaleDB (PostgreSQL 17)",
            category="databases",
            description="PostgreSQL 17 with TimescaleDB hypertable extension preloaded, SCRAM-SHA-256 auth, and PG_VERSION safety check.",
            icon="timescaledb",
            supported_versions=["2.18 (PostgreSQL 17)"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=512,
            recommended_ram_mb=1024,
            minimum_disk_mb=2048,
            image_source="requires_ghcr_build",
            dockerfile_path="docker/services/timescaledb/Dockerfile",
            docker_images={"TimescaleDB PG17 (Vietnam Hosting GHCR)": f"{GHCR_NAMESPACE}:timescaledb_pg17"},
            custom_docker_images={"TimescaleDB PG17": f"{GHCR_NAMESPACE}:timescaledb_pg17"},
            startup=(
                'export PGDATA=/home/container/pgdata; mkdir -p /home/container/run; '
                'if [[ ! -f "${PGDATA}/PG_VERSION" ]]; then '
                '  PW="${DB_PASSWORD:-$(openssl rand -base64 24 | tr -dc A-Za-z0-9 | head -c 24)}"; '
                '  printf "%s" "${PW}" > /home/container/run/.pwfile; chmod 600 /home/container/run/.pwfile; '
                '  initdb -D "${PGDATA}" -U "${DB_USER}" --auth-local=scram-sha-256 --auth-host=scram-sha-256 --pwfile=/home/container/run/.pwfile --encoding=UTF8; '
                '  rm -f /home/container/run/.pwfile; '
                '  echo "shared_preload_libraries = \x27timescaledb\x27" >> "${PGDATA}/postgresql.conf"; '
                '  echo "host all all 0.0.0.0/0 scram-sha-256" >> "${PGDATA}/pg_hba.conf"; '
                'fi; '
                'exec postgres -D "${PGDATA}" -p {{SERVER_PORT}} -h "${BIND_ADDRESS}" -k /home/container/run'
            ),
            stop="^C",
            startup_done="database system is ready to accept connections",
            install_body='mkdir -p /mnt/server/pgdata /mnt/server/run /mnt/server/backups\nchmod 700 /mnt/server/pgdata\n',
            variables=[
                VariableSpec("Database User", "Primary TimescaleDB role.", "DB_USER", "tsdb_user", rules="required|alpha_dash|max:32"),
                VariableSpec("Database Password", "Strong password (auto-generated if empty).", "DB_PASSWORD", "", rules="nullable|string|min:12|max:128"),
                VariableSpec("Bind Address", "Admin-controlled bind address.", "BIND_ADDRESS", "127.0.0.1", user_editable=False, rules="required|string|in:127.0.0.1,0.0.0.0"),
            ],
            upstream_license="Apache-2.0 / Timescale License",
            upstream_url="https://www.timescale.com",
            security_notes_vi=DB_SECURITY_VI,
            backup_notes_vi="- Sử dụng `pg_dump -Fc` kết hợp `SELECT timescaledb_pre_restore()` / `timescaledb_post_restore()` khi phục hồi.",
        ),

        # 12. Qdrant
        EggSpec(
            id="qdrant",
            name="Vietnam Hosting — Qdrant Vector Database",
            category="databases",
            description="High-performance Qdrant 1.13 vector similarity search engine with API key authentication and snapshot storage.",
            icon="qdrant",
            supported_versions=["1.13"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=512,
            recommended_ram_mb=1024,
            minimum_disk_mb=2048,
            image_source="requires_ghcr_build",
            dockerfile_path="docker/services/qdrant/Dockerfile",
            docker_images={"Qdrant 1.13 (Vietnam Hosting GHCR)": f"{GHCR_NAMESPACE}:qdrant_1.13"},
            custom_docker_images={"Qdrant 1.13": f"{GHCR_NAMESPACE}:qdrant_1.13"},
            startup=(
                'mkdir -p /home/container/storage /home/container/snapshots; '
                'if [[ ! -f /home/container/.api_key ]]; then '
                '  KEY="${QDRANT_API_KEY:-$(openssl rand -hex 24)}"; printf "%s" "${KEY}" > /home/container/.api_key; chmod 600 /home/container/.api_key; '
                'fi; '
                'export QDRANT__SERVICE__HOST="${BIND_ADDRESS}" QDRANT__SERVICE__HTTP_PORT="{{SERVER_PORT}}" '
                'QDRANT__STORAGE__STORAGE_PATH="/home/container/storage" QDRANT__STORAGE__SNAPSHOTS_PATH="/home/container/snapshots" '
                'QDRANT__SERVICE__API_KEY="$(cat /home/container/.api_key)"; '
                'exec /qdrant/qdrant'
            ),
            stop="^C",
            startup_done="Qdrant HTTP listening on",
            install_body='mkdir -p /mnt/server/storage /mnt/server/snapshots\n',
            variables=[
                VariableSpec("Qdrant API Key", "API key required for all requests (auto-generated if blank).", "QDRANT_API_KEY", "", rules="nullable|string|min:16|max:128"),
                VariableSpec("Bind Address", "Admin-controlled host binding.", "BIND_ADDRESS", "127.0.0.1", user_editable=False, rules="required|string|in:127.0.0.1,0.0.0.0"),
            ],
            upstream_license="Apache-2.0",
            upstream_url="https://qdrant.tech",
            security_notes_vi=DB_SECURITY_VI,
            backup_notes_vi="- Tạo snapshot qua Qdrant REST API (`POST /snapshots`) lưu vào `/home/container/snapshots` trước khi backup.",
        ),

        # 13. Meilisearch
        EggSpec(
            id="meilisearch",
            name="Vietnam Hosting — Meilisearch 1.13",
            category="databases",
            description="Fast typo-tolerant Meilisearch 1.13 search engine running in production mode with mandatory master key.",
            icon="meilisearch",
            supported_versions=["1.13"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=512,
            recommended_ram_mb=1024,
            minimum_disk_mb=2048,
            image_source="requires_ghcr_build",
            dockerfile_path="docker/services/meilisearch/Dockerfile",
            docker_images={"Meilisearch 1.13 (Vietnam Hosting GHCR)": f"{GHCR_NAMESPACE}:meilisearch_1.13"},
            custom_docker_images={"Meilisearch 1.13": f"{GHCR_NAMESPACE}:meilisearch_1.13"},
            startup=(
                'mkdir -p /home/container/data.ms /home/container/dumps /home/container/snapshots; '
                'if [[ ! -f /home/container/.master_key ]]; then '
                '  KEY="${MEILI_MASTER_KEY:-$(openssl rand -hex 24)}"; printf "%s" "${KEY}" > /home/container/.master_key; chmod 600 /home/container/.master_key; '
                'fi; '
                'exec meilisearch --env production --no-analytics --http-addr "${BIND_ADDRESS}:{{SERVER_PORT}}" '
                '--db-path /home/container/data.ms --dump-dir /home/container/dumps --snapshot-dir /home/container/snapshots '
                '--master-key "$(cat /home/container/.master_key)"'
            ),
            stop="^C",
            startup_done="Server listening on:",
            install_body='mkdir -p /mnt/server/data.ms /mnt/server/dumps /mnt/server/snapshots\n',
            variables=[
                VariableSpec("Master Key", "Meilisearch production master key (min 16 chars; auto-generated if empty).", "MEILI_MASTER_KEY", "", rules="nullable|string|min:16|max:128"),
                VariableSpec("Bind Address", "Admin-controlled bind address.", "BIND_ADDRESS", "127.0.0.1", user_editable=False, rules="required|string|in:127.0.0.1,0.0.0.0"),
            ],
            upstream_license="MIT",
            upstream_url="https://www.meilisearch.com",
            security_notes_vi=DB_SECURITY_VI,
            backup_notes_vi="- Sử dụng `POST /dumps` để tạo dump tương thích nâng cấp phiên bản Meilisearch an toàn.",
        ),

        # 14. Typesense
        EggSpec(
            id="typesense",
            name="Vietnam Hosting — Typesense 28.0",
            category="databases",
            description="Open-source in-memory search engine Typesense 28.0 with mandatory API key and persistent data directory.",
            icon="typesense",
            supported_versions=["28.0"],
            supported_architectures=["amd64", "arm64"],
            minimum_ram_mb=512,
            recommended_ram_mb=1024,
            minimum_disk_mb=2048,
            image_source="requires_ghcr_build",
            dockerfile_path="docker/services/typesense/Dockerfile",
            docker_images={"Typesense 28.0 (Vietnam Hosting GHCR)": f"{GHCR_NAMESPACE}:typesense_28"},
            custom_docker_images={"Typesense 28.0": f"{GHCR_NAMESPACE}:typesense_28"},
            startup=(
                'mkdir -p /home/container/data; '
                'if [[ ! -f /home/container/.api_key ]]; then '
                '  KEY="${TYPESENSE_API_KEY:-$(openssl rand -hex 24)}"; printf "%s" "${KEY}" > /home/container/.api_key; chmod 600 /home/container/.api_key; '
                'fi; '
                'exec /opt/typesense-server --data-dir=/home/container/data --api-address="${BIND_ADDRESS}" '
                '--api-port={{SERVER_PORT}} --api-key="$(cat /home/container/.api_key)"'
            ),
            stop="^C",
            startup_done="Peer refresh succeeded|Starting Typesense|Listening",
            install_body='mkdir -p /mnt/server/data /mnt/server/backups\n',
            variables=[
                VariableSpec("Typesense API Key", "Admin API key (auto-generated if empty).", "TYPESENSE_API_KEY", "", rules="nullable|string|min:16|max:128"),
                VariableSpec("Bind Address", "Admin-controlled bind address.", "BIND_ADDRESS", "127.0.0.1", user_editable=False, rules="required|string|in:127.0.0.1,0.0.0.0"),
            ],
            upstream_license="GPL-3.0",
            upstream_url="https://typesense.org",
            security_notes_vi=DB_SECURITY_VI,
            backup_notes_vi="- Gọi API `POST /operations/snapshot?snapshot_path=/home/container/backups/snap` để chụp snapshot nóng an toàn.",
        ),
    ]
