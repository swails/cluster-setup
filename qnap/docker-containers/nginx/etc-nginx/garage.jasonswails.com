server {
    listen 80;

    server_name garage.jasonswails.com;

    # Proxy connections to the application servers
    # app_servers
    location / {

        proxy_pass         http://192.168.1.55:8083;
        proxy_redirect     off;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Host $server_name;
        proxy_set_header   X-Forwarded-Proto $scheme;
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    }
}
