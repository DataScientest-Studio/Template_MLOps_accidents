# =============================================================================
# Nginx Gateway Dockerfile
# =============================================================================
# Custom Nginx image for MLOps microservices gateway
# =============================================================================

FROM nginx:1.25-alpine

LABEL maintainer="MLOps Team"
LABEL description="Nginx reverse proxy for MLOps microservices"

# Install curl for health checks
RUN apk add --no-cache curl

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Create directory for SSL certificates (future use)
RUN mkdir -p /etc/nginx/ssl

# Create log directory with proper permissions
RUN mkdir -p /var/log/nginx && \
    chown -R nginx:nginx /var/log/nginx

# Expose HTTP port (HTTPS can be added later)
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/health || exit 1

# Run nginx in foreground
CMD ["nginx", "-g", "daemon off;"]

