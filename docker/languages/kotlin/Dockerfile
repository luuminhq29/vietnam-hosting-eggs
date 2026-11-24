# Vietnam Hosting Universal Docker Image — Kotlin 2.1 + JDK 21
# Target Registry (publish required): ghcr.io/luuminhq29/yolks
# Unprivileged runtime compatible with Pterodactyl Wings (/home/container)
FROM eclipse-temurin:21-jdk-noble

LABEL org.opencontainers.image.vendor="Vietnam Hosting" \
      org.opencontainers.image.url="https://vietnam-hosting.net" \
      org.opencontainers.image.title="Vietnam Hosting — Kotlin 2.1 + JDK 21" \
      org.opencontainers.image.licenses="MIT"

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates curl wget git tini procps iproute2 dnsutils unzip zip tar nano vim gradle \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://github.com/JetBrains/kotlin/releases/download/v2.1.20/kotlin-compiler-2.1.20.zip -o /tmp/kotlin.zip && unzip -q /tmp/kotlin.zip -d /opt && rm -f /tmp/kotlin.zip && ln -sf /opt/kotlinc/bin/kotlinc /usr/local/bin/kotlinc && ln -sf /opt/kotlinc/bin/kotlin /usr/local/bin/kotlin

RUN (id -u container >/dev/null 2>&1 || useradd -m -d /home/container -s /bin/bash container) \
    && mkdir -p /opt/vnh /home/container \
    && chown -R container:container /home/container

COPY core/environment.sh core/startup.sh core/entrypoint.sh core/healthcheck.sh core/nat-ssh.sh core/vps-shell.sh core/proc-limits.sh /opt/vnh/
RUN chmod 755 /opt/vnh/*.sh && echo '/opt/vnh/vps-shell.sh' >> /etc/shells

ENV USER=container HOME=/home/container VNH_CORE_DIR=/opt/vnh

USER container
WORKDIR /home/container
STOPSIGNAL SIGTERM
ENTRYPOINT ["/usr/bin/tini", "--", "/bin/bash", "/opt/vnh/entrypoint.sh"]
