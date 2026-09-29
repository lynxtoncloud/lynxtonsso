ARG KEYCLOAK_BASE_IMAGE=quay.io/keycloak/keycloak:26.3.2
FROM ${KEYCLOAK_BASE_IMAGE}

LABEL org.opencontainers.image.title="LynxtonCloud SSO" \
      org.opencontainers.image.version="v1.0.0" \
      org.opencontainers.image.source="https://github.com/lynxtoncloud/lynxtonsso" \
      org.opencontainers.image.description="LynxtonCloud theme on the official Keycloak runtime"

COPY --chown=1000:0 --chmod=644 target/lynxton-theme.jar /opt/keycloak/providers/lynxton-theme.jar
