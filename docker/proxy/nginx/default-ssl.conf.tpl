server {
    listen 80;
    server_name ${DOMAIN} www.${DOMAIN};

    location /.well-known/acme-challenge/ {
        root /vol/www/;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}

server {
        listen 443 ssl http2;
        # use the certificates
        ssl_certificate     /etc/letsencrypt/live/${DOMAIN}/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/${DOMAIN}/privkey.pem;

        server_name ${DOMAIN};
        root /var/www/html;
        index index.php index.html index.htm;


        location / {
            uwsgi_pass           ${APP_HOST}:${APP_PORT};
            include              /etc/nginx/uwsgi_params;
            client_max_body_size 10M;
        }

        
    }