# Vietnam Hosting Universal Docker Image — Debian 13 Trixie (NAT Container)
# Target Registry (publish required): ghcr.io/vietnam-hosting/yolks
# Unprivileged runtime compatible with Pterodactyl Wings (/home/container)
FROM debian:13-slim

LABEL org.opencontainers.image.vendor="Vietnam Hosting" \
      org.opencontainers.image.url="https://vietnam-hosting.net" \
      org.opencontainers.image.title="Vietnam Hosting — Debian 13 Trixie (NAT Container)" \
      org.opencontainers.image.licenses="MIT"

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates curl wget git tini procps iproute2 dnsutils unzip zip tar nano vim dropbear-bin htop jq libnss-wrapper openssh-client openssl rsync screen tmux \
    && rm -rf /var/lib/apt/lists/*

RUN (id -u container >/dev/null 2>&1 || useradd -m -d /home/container -s /bin/bash container) \
    && mkdir -p /opt/vnh /home/container \
    && chown -R container:container /home/container

COPY core/environment.sh core/startup.sh core/entrypoint.sh core/healthcheck.sh core/nat-ssh.sh /opt/vnh/
RUN chmod 755 /opt/vnh/*.sh

ENV USER=container HOME=/home/container VNH_CORE_DIR=/opt/vnh \
    VNH_OS_LABEL="Debian 13 (Trixie)"

USER container
WORKDIR /home/container
STOPSIGNAL SIGTERM
ENTRYPOINT ["/usr/bin/tini", "--", "/bin/bash", "/opt/vnh/entrypoint.sh"]
