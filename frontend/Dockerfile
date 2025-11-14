# ------------------------------------
# 1. BUILD-STAGE (Nuxt Static Build)
# Erzeugt die statischen Dateien.
# ------------------------------------
FROM node:24-alpine AS builder

# Build argument for API URL
ARG NUXT_PUBLIC_API_URL=http://135.181.78.114:9002

# Set as environment variable for build time
ENV NUXT_PUBLIC_API_URL=$NUXT_PUBLIC_API_URL

# Setze das Arbeitsverzeichnis
WORKDIR /app

# Kopiere die Abhängigkeitsdateien
COPY package.json package-lock.json ./

# Installiere die Abhängigkeiten mit npm
RUN npm install

# Kopiere den Rest des Quellcodes
COPY . .

# Führe den Nuxt-Build aus
# WICHTIG: Verwende 'npm run build' (oder 'npm run generate' für eine reine SPA/Static Site)
# Für diesen Nginx-Ansatz ist es oft ratsam, den 'generate' Befehl zu verwenden,
# der alle statischen Seiten erstellt und sie im 'dist' Ordner ablegt (Nuxt 2) oder
# im '.output/public' Ordner (Nuxt 3 bei statischer Konfiguration).
# Da du 'npm build' verwenden wolltest, lassen wir es dabei und gehen davon aus,
# dass dein Build-Prozess statische Assets in den '.output/public' Ordner legt.
RUN npm run generate

# ------------------------------------
# 2. PRODUCTION-STAGE (Nginx Server)
# Das schlanke Image für die Auslieferung der statischen Dateien.
# ------------------------------------
FROM nginx:alpine

# Entferne die Standard-Nginx-Konfigurationsdatei
RUN rm /etc/nginx/conf.d/default.conf

# Kopiere deine benutzerdefinierte Nginx-Konfiguration
# Du musst eine nginx.conf (oder default.conf) im Projektverzeichnis erstellen!
COPY nginx/default.conf /etc/nginx/conf.d/default.conf

# Kopiere die statischen Assets aus der Builder-Stage in das Nginx-Webroot
# WICHTIG: Bei Nuxt 3 (statisch konfiguriert) liegt der Output in .output/public/
COPY --from=builder /app/.output/public /usr/share/nginx/html

# Exponiere den Standard-HTTP-Port
EXPOSE 80

# Starte Nginx
CMD ["nginx", "-g", "daemon off;"]
