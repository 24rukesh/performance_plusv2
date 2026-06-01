# syntax=docker/dockerfile:1.7

# ---- builder stage ----
FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci
COPY . .
ENV NODE_ENV=production
RUN npm run build

# ---- runtime stage: serve static export with nginx ----
FROM nginx:alpine AS runner

COPY --from=builder /app/out /usr/share/nginx/html

RUN cat > /etc/nginx/conf.d/default.conf << 'EOF'
server {
    listen 3000;
    root /usr/share/nginx/html;
    index index.html;
    location / {
        try_files $uri $uri/ $uri.html =404;
    }
}
EOF

EXPOSE 3000
CMD ["nginx", "-g", "daemon off;"]
