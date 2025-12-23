# syntax=docker/dockerfile:1.4

# ------------------------------------
# 1. BUILD-STAGE (Nuxt Static Build)
# ------------------------------------
FROM node:24-alpine AS builder

ARG NUXT_PUBLIC_API_URL=http://135.181.78.114:9002

ENV NUXT_PUBLIC_API_URL=$NUXT_PUBLIC_API_URL

WORKDIR /app

COPY package.json package-lock.json ./

RUN --mount=type=cache,target=/root/.npm \
    npm ci --prefer-offline --no-audit

COPY . .

RUN npm run generate

# ------------------------------------
# 2. PRODUCTION-STAGE (Nginx Server)
# ------------------------------------
FROM nginx:alpine

RUN rm /etc/nginx/conf.d/default.conf

COPY nginx/default.conf /etc/nginx/conf.d/default.conf

COPY --from=builder /app/.output/public /usr/share/nginx/html

RUN find /usr/share/nginx/html -type f \( -name "*.html" -o -name "*.css" -o -name "*.js" \) \
    -exec sh -c 'gzip -9 -k "$1"' _ {} \;

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
