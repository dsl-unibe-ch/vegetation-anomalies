# Base image
FROM nginx:alpine

# Create a directory for the empty image
RUN mkdir -p /etc/nginx/internal

# Add the empty PNG file to the container
COPY empty.png /etc/nginx/internal/empty.png

# Copy main context nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Copy custom nginx configuration
COPY default.conf /etc/nginx/conf.d/default.conf

# Expose the port (optional)
EXPOSE 80
