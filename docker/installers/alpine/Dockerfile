# Vietnam Hosting Universal Installer Image — Alpine 3.23 Installer
FROM alpine:3.23

LABEL org.opencontainers.image.vendor="Vietnam Hosting" \
      org.opencontainers.image.url="https://vietnam-hosting.net" \
      org.opencontainers.image.title="Vietnam Hosting Installer — Alpine 3.23 Installer"

RUN apk add --no-cache bash ca-certificates curl wget git jq unzip zip tar gzip xz zstd openssl
COPY core/installer.sh /opt/vnh/installer.sh
RUN chmod 755 /opt/vnh/installer.sh
WORKDIR /mnt/server
CMD ["/bin/bash"]
