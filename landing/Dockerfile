# syntax=docker/dockerfile:1.7

# ---- builder stage ----
FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci
COPY . .
ENV NODE_ENV=production
RUN npm run build

# ---- runtime stage ----
FROM node:20-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# Non-root user — Alpine BusyBox addgroup/adduser syntax (D-05)
# GID/UID 1001 consistent with ./Dockerfile appgroup/appuser pattern
RUN addgroup -g 1001 appgroup && \
    adduser -u 1001 -G appgroup -D -h /home/appuser appuser

# 1. Public static assets
COPY --from=builder --chown=appuser:appgroup /app/public ./public

# 2. Create .next dir with correct ownership before standalone copy
RUN mkdir .next && chown appuser:appgroup .next

# 3. Standalone bundle (server.js + traced node_modules)
COPY --from=builder --chown=appuser:appgroup /app/.next/standalone ./

# 4. Static assets overlaid AFTER standalone (critical — must be last)
COPY --from=builder --chown=appuser:appgroup /app/.next/static ./.next/static

USER appuser
EXPOSE 3000
CMD ["node", "server.js"]
