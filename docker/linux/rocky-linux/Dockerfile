# Vietnam Hosting Universal Docker Image — Rocky Linux 9 (NAT Container)
# Target Registry (publish required): ghcr.io/vietnam-hosting/yolks
FROM rockylinux/rockylinux:9

LABEL org.opencontainers.image.vendor="Vietnam Hosting" \
      org.opencontainers.image.url="https://vietnam-hosting.net" \
      org.opencontainers.image.title="Vietnam Hosting — Rocky Linux 9 (NAT Container)" \
      org.opencontainers.image.licenses="MIT"

RUN dnf install -y --setopt=install_weak_deps=False --allowerasing \
        bash ca-certificates curl wget git procps-ng iproute bind-utils unzip zip tar nano vim shadow-utils jq openssh-clients openssh-server rsync tmux \
    && dnf clean all

RUN (id -u container >/dev/null 2>&1 || useradd -m -d /home/container -s /bin/bash container) \
    && mkdir -p /opt/vnh /home/container \
    && chown -R container:container /home/container

COPY core/environment.sh core/startup.sh core/entrypoint.sh core/healthcheck.sh core/nat-ssh.sh /opt/vnh/
RUN chmod 755 /opt/vnh/*.sh

ENV USER=container HOME=/home/container VNH_CORE_DIR=/opt/vnh \
    VNH_OS_LABEL="Rocky Linux 9"

USER container
WORKDIR /home/container
STOPSIGNAL SIGTERM
ENTRYPOINT ["/bin/bash", "/opt/vnh/entrypoint.sh"]
