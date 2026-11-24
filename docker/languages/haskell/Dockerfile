# Vietnam Hosting Universal Docker Image — Haskell GHC 9.10 + Cabal
# Target Registry (publish required): ghcr.io/vietnam-hosting/yolks
# Unprivileged runtime compatible with Pterodactyl Wings (/home/container)
FROM haskell:9.10-slim

LABEL org.opencontainers.image.vendor="Vietnam Hosting" \
      org.opencontainers.image.url="https://vietnam-hosting.net" \
      org.opencontainers.image.title="Vietnam Hosting — Haskell GHC 9.10 + Cabal" \
      org.opencontainers.image.licenses="MIT"

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates curl wget git tini procps iproute2 dnsutils unzip zip tar nano vim build-essential libgmp-dev zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

RUN (id -u container >/dev/null 2>&1 || useradd -m -d /home/container -s /bin/bash container) \
    && mkdir -p /opt/vnh /home/container \
    && chown -R container:container /home/container

COPY core/environment.sh core/startup.sh core/entrypoint.sh core/healthcheck.sh core/nat-ssh.sh /opt/vnh/
RUN chmod 755 /opt/vnh/*.sh

ENV USER=container HOME=/home/container VNH_CORE_DIR=/opt/vnh \
    CABAL_DIR=/home/container/.cabal

USER container
WORKDIR /home/container
STOPSIGNAL SIGTERM
ENTRYPOINT ["/usr/bin/tini", "--", "/bin/bash", "/opt/vnh/entrypoint.sh"]
