server {
    listen 80;
    server_name jupyter.theswails.com;

    # Proxy connections to the application servers
    # app_servers
    location / {

        proxy_pass         http://192.168.1.3:8888;
        proxy_redirect     off;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Host $server_name;
        proxy_set_header   X-Forwarded-Proto $scheme;

        # For websockets
        proxy_http_version 1.1;
        proxy_set_header   Upgrade $http_upgrade;
        proxy_set_header   Connection "Upgrade";
        proxy_read_timeout 86400;
    }
}
