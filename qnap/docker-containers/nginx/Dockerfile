FROM nginx:1.19.5-alpine

COPY etc-nginx/ /etc/nginx/

ENTRYPOINT [ "/docker-entrypoint.sh" ]

EXPOSE 80

CMD [ "nginx", "-g", "daemon off;" ]
