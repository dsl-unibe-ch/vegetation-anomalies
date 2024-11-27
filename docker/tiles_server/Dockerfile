# Base image
FROM nginx:alpine

# Create a directory for the empty image
RUN mkdir -p /etc/nginx/internal

# Add the empty PNG file to the container
COPY empty.png /etc/nginx/internal/empty.png

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Expose the port (optional)
EXPOSE 80
