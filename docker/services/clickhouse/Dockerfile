# Vietnam Hosting Universal Docker Image — ClickHouse 25 LTS
# Target Registry (publish required): ghcr.io/luuminhq29/yolks
FROM clickhouse/clickhouse-server:25.3-alpine

LABEL org.opencontainers.image.vendor="Vietnam Hosting" \
      org.opencontainers.image.url="https://vietnam-hosting.net" \
      org.opencontainers.image.title="Vietnam Hosting — ClickHouse 25 LTS" \
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
