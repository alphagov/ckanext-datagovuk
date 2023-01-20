FROM nginx:stable-alpine

RUN rm /etc/nginx/conf.d/default.conf

COPY ckan.conf /etc/nginx/conf.d

EXPOSE 80/tcp
