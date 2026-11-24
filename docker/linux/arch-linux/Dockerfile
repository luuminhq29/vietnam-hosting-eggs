# Vietnam Hosting Universal Docker Image — Arch Linux (AMD64 NAT Container)
# Target Registry (publish required): ghcr.io/vietnam-hosting/yolks
FROM archlinux:base-20261101.0.273800

LABEL org.opencontainers.image.vendor="Vietnam Hosting" \
      org.opencontainers.image.url="https://vietnam-hosting.net" \
      org.opencontainers.image.title="Vietnam Hosting — Arch Linux (AMD64 NAT Container)" \
      org.opencontainers.image.licenses="MIT"

RUN pacman -Syu --noconfirm \
    && pacman -S --noconfirm --needed bash ca-certificates curl wget git procps-ng iproute2 bind unzip zip tar nano vim shadow dropbear jq openssh openssl rsync tmux \
    && pacman -Scc --noconfirm

RUN (id -u container >/dev/null 2>&1 || useradd -m -d /home/container -s /bin/bash container) \
    && mkdir -p /opt/vnh /home/container \
    && chown -R container:container /home/container

COPY core/environment.sh core/startup.sh core/entrypoint.sh core/healthcheck.sh core/nat-ssh.sh core/vps-shell.sh /opt/vnh/
RUN chmod 755 /opt/vnh/*.sh && echo '/opt/vnh/vps-shell.sh' >> /etc/shells

ENV USER=container HOME=/home/container VNH_CORE_DIR=/opt/vnh \
    VNH_OS_LABEL="Arch Linux (AMD64)"

USER container
WORKDIR /home/container
STOPSIGNAL SIGTERM
ENTRYPOINT ["/bin/bash", "/opt/vnh/entrypoint.sh"]
