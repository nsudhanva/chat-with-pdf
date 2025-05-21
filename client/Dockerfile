# Stage 1: Build the SvelteKit application
FROM node:18-slim AS builder

WORKDIR /app

# Copy package files and install dependencies
COPY package.json package-lock.json* ./
RUN npm install

# Copy the rest of the client application code
COPY . .

# Build the SvelteKit application
RUN npm run build

# Stage 2: Serve the built assets with Nginx
FROM nginx:alpine

# Copy the built assets from Stage 1
COPY --from=builder /app/build /usr/share/nginx/html

# Remove default Nginx configuration
RUN rm /etc/nginx/conf.d/default.conf

# Copy custom Nginx configuration (will be created in the next step)
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]
