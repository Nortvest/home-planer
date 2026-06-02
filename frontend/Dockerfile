FROM nginx:1.27-alpine

RUN rm -rf /usr/share/nginx/html/*

COPY index.html admin.html dashboard.html /usr/share/nginx/html/
COPY css/ /usr/share/nginx/html/css/
COPY js/ /usr/share/nginx/html/js/

ARG BACKEND_URL
ENV BACKEND_URL=${BACKEND_URL:-http://localhost:8000/api}

RUN sed -i "s|API_BASE_PLACEHOLDER|${BACKEND_URL}|" /usr/share/nginx/html/js/config.js

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
