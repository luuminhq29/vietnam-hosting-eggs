# Vietnam Hosting Universal Docker Image — openSUSE Leap 15.6 (NAT Container)
# Target Registry (publish required): ghcr.io/vietnam-hosting/yolks
FROM opensuse/leap:15.6

LABEL org.opencontainers.image.vendor="Vietnam Hosting" \
      org.opencontainers.image.url="https://vietnam-hosting.net" \
      org.opencontainers.image.title="Vietnam Hosting — openSUSE Leap 15.6 (NAT Container)" \
      org.opencontainers.image.licenses="MIT"

RUN zypper --non-interactive refresh \
    && zypper --non-interactive install --no-recommends bash ca-certificates curl wget git procps iproute2 bind-utils unzip zip tar nano vim shadow jq openssh openssl rsync tmux \
    && zypper clean --all

RUN (id -u container >/dev/null 2>&1 || useradd -m -d /home/container -s /bin/bash container) \
    && mkdir -p /opt/vnh /home/container \
    && chown -R container:container /home/container

COPY core/environment.sh core/startup.sh core/entrypoint.sh core/healthcheck.sh core/nat-ssh.sh /opt/vnh/
RUN chmod 755 /opt/vnh/*.sh

ENV USER=container HOME=/home/container VNH_CORE_DIR=/opt/vnh \
    VNH_OS_LABEL="openSUSE Leap 15.6"

USER container
WORKDIR /home/container
STOPSIGNAL SIGTERM
ENTRYPOINT ["/bin/bash", "/opt/vnh/entrypoint.sh"]
