# SSL/TLS Certificate Directory

This directory stores SSL/TLS certificates for HTTPS connections in production deployments.

## Development Environment (Self-Signed Certificates)

For local development with HTTPS, generate self-signed certificates:

```bash
# Navigate to this directory
cd infra/compose/ssl

# Generate self-signed certificate (valid for 365 days)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout key.pem \
  -out cert.pem \
  -subj "/C=US/ST=State/L=City/O=Organization/OU=Development/CN=localhost"

# Set appropriate permissions
chmod 600 key.pem
chmod 644 cert.pem
```

**Note:** Self-signed certificates will trigger browser warnings. This is expected for development.

## Production Environment (Let's Encrypt)

For production deployments, use Let's Encrypt to obtain free, trusted SSL certificates:

### Option 1: Manual Certificate Generation

```bash
# Install certbot
sudo apt-get update
sudo apt-get install certbot

# Generate certificate (standalone mode - stops nginx temporarily)
sudo certbot certonly --standalone -d your-domain.com -d www.your-domain.com

# Copy certificates to this directory
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ./cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem ./key.pem

# Set permissions
sudo chown $USER:$USER *.pem
chmod 600 key.pem
chmod 644 cert.pem
```

### Option 2: Docker-based Certbot (Recommended)

Use the included docker-compose service for automated certificate management:

```bash
# Add this service to docker-compose.prod.yml
certbot:
  image: certbot/certbot
  volumes:
    - ./ssl:/etc/letsencrypt
    - ./certbot-webroot:/var/www/certbot
  entrypoint: "/bin/sh -c 'trap exit TERM; while :; do certbot renew; sleep 12h & wait $${!}; done;'"

# Initial certificate generation
docker-compose -f docker-compose.prod.yml run --rm certbot certonly \
  --webroot \
  --webroot-path=/var/www/certbot \
  -d your-domain.com \
  -d www.your-domain.com \
  --email your-email@example.com \
  --agree-tos \
  --no-eff-email
```

### Certificate Renewal

Let's Encrypt certificates expire after 90 days. Set up automatic renewal:

```bash
# Add to crontab for automatic renewal
0 0 * * 0 docker-compose -f /path/to/docker-compose.prod.yml run --rm certbot renew && docker-compose -f /path/to/docker-compose.prod.yml exec nginx nginx -s reload
```

## Required Files

Place these files in this directory before enabling HTTPS:

- `cert.pem` - SSL certificate (public key)
- `key.pem` - Private key
- `chain.pem` (optional) - Certificate chain for better compatibility

## Nginx Configuration

Update `nginx.conf` to use HTTPS:

1. Uncomment the HTTPS server block (lines 95-106)
2. Update the `server_name` with your domain
3. Verify certificate paths match this directory

## Security Best Practices

1. **Never commit private keys** - The `.gitignore` should exclude `*.pem` files
2. **Set restrictive permissions** - Private keys should be readable only by owner (600)
3. **Use strong ciphers** - The default configuration uses TLSv1.2+ with secure ciphers
4. **Enable HSTS** - Add `Strict-Transport-Security` header in production
5. **Monitor expiration** - Set up alerts for certificate expiration

## Troubleshooting

### Certificate Not Found
- Verify files exist: `ls -la infra/compose/ssl/`
- Check docker volume mount in `docker-compose.prod.yml`
- Ensure permissions allow nginx to read certificates

### Browser Certificate Warnings
- Development: Expected with self-signed certificates
- Production: May indicate expired or invalid certificates

### Let's Encrypt Rate Limits
- 50 certificates per week per domain
- Use staging environment for testing: `--staging` flag

## Additional Resources

- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [Certbot Documentation](https://certbot.eff.org/docs/)
- [Mozilla SSL Configuration Generator](https://ssl-config.mozilla.org/)