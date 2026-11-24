# Vietnam Hosting Universal Installer Image — Debian 13 Installer
FROM debian:13-slim

LABEL org.opencontainers.image.vendor="Vietnam Hosting" \
      org.opencontainers.image.url="https://vietnam-hosting.net" \
      org.opencontainers.image.title="Vietnam Hosting Installer — Debian 13 Installer"

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl wget git jq unzip zip tar xz-utils bzip2 openssl file \
    && rm -rf /var/lib/apt/lists/*
COPY core/installer.sh /opt/vnh/installer.sh
RUN chmod 755 /opt/vnh/installer.sh
WORKDIR /mnt/server
CMD ["/bin/bash"]
