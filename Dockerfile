# Официальный образ ноды Remnawave с Infinity Xray.
# rw-core внутри образа — симлинк на /usr/local/bin/xray, поэтому меняем только его.
ARG NODE_TAG=3.4.4
FROM remnawave/node:${NODE_TAG}
ARG INFINITY_VERSION
LABEL org.opencontainers.image.title="Infinity Xray" \
      org.opencontainers.image.version="${INFINITY_VERSION}" \
      org.opencontainers.image.licenses="MPL-2.0"
COPY xray /usr/local/bin/xray
# Серверный keepalive Hysteria (сек, 0 — выкл), keepalive mux для XHTTP через CDN (сек), сводка icstats (сек)
ENV XRAY_IC_QUIC_KEEPALIVE=10 \
    XRAY_IC_MUX_KEEPALIVE=5 \
    XRAY_IC_STATS=60 \
    XRAY_XHTTP_FLOW=on
