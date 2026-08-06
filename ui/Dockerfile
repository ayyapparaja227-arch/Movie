FROM nginxinc/nginx-unprivileged:alpine

# Copy static web assets into default Nginx HTML folder
COPY ui/index.html /usr/share/nginx/html/
COPY ui/styles.css /usr/share/nginx/html/
COPY ui/app.js /usr/share/nginx/html/

# Expose non-privileged port
EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]
