forwarded_allow_ips = "*"  # Or specify your Apache proxy IP for better security

# Allow our custom SSL headers through
secure_scheme_headers = {
    "X-FORWARDED-PROTOCOL": "ssl",
    "X-FORWARDED-PROTO": "https",
    "X-FORWARDED-SSL": "on",
    "SSL_CLIENT_CERT": "ssl_client_cert",
    "SSL_SERVER_CERT": "ssl_server_cert",
    "SSL_CLIENT_VERIFY": "ssl_client_verify",
    "SSL_CLIENT_DN": "ssl_client_dn",
}
