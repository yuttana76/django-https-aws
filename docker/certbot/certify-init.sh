#!/bin/sh

# Waits for proxy to be available, then gets the first certificate.

set -e

until nc -z proxy 80; do
    echo "Waiting for proxy..."
    sleep 5s & wait ${!}
done

echo "Getting certificate...for [${DOMAIN}]"

certbot certonly \
    --webroot \
    -w /vol/www/ \
    --force-renewal \
    -d "$DOMAIN" \
    --email $EMAIL \
    --rsa-key-size 4096 \
    --agree-tos \
    --noninteractive

echo "Listing /vol/www/ contents:"
ls -la /vol/www/
echo "Certificate obtained."