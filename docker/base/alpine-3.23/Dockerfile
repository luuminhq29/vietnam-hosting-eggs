# Vietnam Hosting Universal Docker Image — Base Alpine 3.23
# Target Registry (publish required): ghcr.io/vietnam-hosting/yolks
FROM alpine:3.23

LABEL org.opencontainers.image.vendor="Vietnam Hosting" \
      org.opencontainers.image.url="https://vietnam-hosting.net" \
      org.opencontainers.image.title="Vietnam Hosting — Base Alpine 3.23" \
      org.opencontainers.image.licenses="MIT"

RUN apk add --no-cache \
        bash ca-certificates curl wget git tini procps iproute2 bind-tools unzip zip tar nano vim tzdata dropbear jq openssl

RUN (id -u container >/dev/null 2>&1 || adduser -D -h /home/container -s /bin/bash container) \
    && mkdir -p /opt/vnh /home/container \
    && chown -R container:container /home/container

COPY core/environment.sh core/startup.sh core/entrypoint.sh core/healthcheck.sh core/nat-ssh.sh /opt/vnh/
RUN chmod 755 /opt/vnh/*.sh

ENV USER=container HOME=/home/container VNH_CORE_DIR=/opt/vnh

USER container
WORKDIR /home/container
STOPSIGNAL SIGTERM
ENTRYPOINT ["/sbin/tini", "--", "/bin/bash", "/opt/vnh/entrypoint.sh"]
