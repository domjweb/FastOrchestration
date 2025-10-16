# Dockerfile for React frontend (production build)
FROM node:20-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
WORKDIR /usr/share/nginx/html
COPY --from=build /app/dist .
COPY --from=build /app/public ./public
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
