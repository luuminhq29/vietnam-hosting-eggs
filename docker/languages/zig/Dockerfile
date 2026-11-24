# Vietnam Hosting Universal Docker Image — Zig 0.14
# Target Registry (publish required): ghcr.io/vietnam-hosting/yolks
# Unprivileged runtime compatible with Pterodactyl Wings (/home/container)
FROM debian:13-slim

LABEL org.opencontainers.image.vendor="Vietnam Hosting" \
      org.opencontainers.image.url="https://vietnam-hosting.net" \
      org.opencontainers.image.title="Vietnam Hosting — Zig 0.14" \
      org.opencontainers.image.licenses="MIT"

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates curl wget git tini procps iproute2 dnsutils unzip zip tar nano vim xz-utils \
    && rm -rf /var/lib/apt/lists/*

RUN ARCH=$(uname -m) && ZIG_ARCH="${ARCH}" && [ "$ARCH" = "arm64" ] && ZIG_ARCH="aarch64" ; curl -fsSL "https://ziglang.org/download/0.14.0/zig-linux-${ZIG_ARCH}-0.14.0.tar.xz" -o /tmp/zig.tar.xz && tar -xf /tmp/zig.tar.xz -C /opt && mv /opt/zig-linux-* /opt/zig && ln -sf /opt/zig/zig /usr/local/bin/zig && rm -f /tmp/zig.tar.xz

RUN (id -u container >/dev/null 2>&1 || useradd -m -d /home/container -s /bin/bash container) \
    && mkdir -p /opt/vnh /home/container \
    && chown -R container:container /home/container

COPY core/environment.sh core/startup.sh core/entrypoint.sh core/healthcheck.sh core/nat-ssh.sh core/vps-shell.sh /opt/vnh/
RUN chmod 755 /opt/vnh/*.sh && echo '/opt/vnh/vps-shell.sh' >> /etc/shells

ENV USER=container HOME=/home/container VNH_CORE_DIR=/opt/vnh \
    ZIG_GLOBAL_CACHE_DIR="/home/container/.cache/zig"

USER container
WORKDIR /home/container
STOPSIGNAL SIGTERM
ENTRYPOINT ["/usr/bin/tini", "--", "/bin/bash", "/opt/vnh/entrypoint.sh"]
