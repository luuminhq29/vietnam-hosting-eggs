# Vietnam Hosting Universal Docker Image — Meilisearch 1.13
# Target Registry (publish required): ghcr.io/vietnam-hosting/yolks
FROM getmeili/meilisearch:v1.13.3

LABEL org.opencontainers.image.vendor="Vietnam Hosting" \
      org.opencontainers.image.url="https://vietnam-hosting.net" \
      org.opencontainers.image.title="Vietnam Hosting — Meilisearch 1.13" \
      org.opencontainers.image.licenses="MIT"

RUN apk add --no-cache \
        bash ca-certificates curl wget git tini procps iproute2 bind-tools unzip zip tar nano vim tzdata 

RUN (id -u container >/dev/null 2>&1 || adduser -D -h /home/container -s /bin/bash container) \
    && mkdir -p /opt/vnh /home/container \
    && chown -R container:container /home/container

COPY core/environment.sh core/startup.sh core/entrypoint.sh core/healthcheck.sh core/nat-ssh.sh core/vps-shell.sh core/proc-limits.sh /opt/vnh/
RUN chmod 755 /opt/vnh/*.sh && echo '/opt/vnh/vps-shell.sh' >> /etc/shells

ENV USER=container HOME=/home/container VNH_CORE_DIR=/opt/vnh

USER container
WORKDIR /home/container
STOPSIGNAL SIGTERM
ENTRYPOINT ["/sbin/tini", "--", "/bin/bash", "/opt/vnh/entrypoint.sh"]
