server {
    listen 80;

    server_name blog.jasonswails.com;

    # Proxy connections to the application servers
    # app_servers
    location / {
        proxy_pass         http://blog:80;
        proxy_redirect     off;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Host $server_name;
        proxy_set_header   X-Forwarded-Proto $scheme;
        proxy_set_header   X-Frame-Options allow;
    }
}
