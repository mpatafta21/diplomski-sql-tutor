-- Prosody XMPP server config za SPADE agente
admins = { "admin@localhost" }

modules_enabled = {
    "roster";
    "saslauth";
    "tls";
    "dialback";
    "disco";
    "private";
    "vcard4";
    "vcard_legacy";
    "version";
    "uptime";
    "time";
    "ping";
    "register";
    "admin_adhoc";
}

allow_registration = true
c2s_require_encryption = false  -- DEV ONLY - produkcija treba TLS
s2s_require_encryption = false
authentication = "internal_plain"
allow_unencrypted_plain_auth = true  -- DEV ONLY: SPADE/slixmpp odbija SCRAM bez TLS-a

log = {
    info = "*console";
    error = "*console";
}

VirtualHost "localhost"
    enabled = true
