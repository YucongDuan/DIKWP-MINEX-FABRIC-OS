# Deployment

## Offline/local

Use the ZipApp for planning and allowlisted local execution. This is the safest initial mode.

## Controlled LAN federation

Run a node on a private network with bearer authentication, a shared lease secret, strict capability allowlists, rate limits, and no sensitive data unless the data contract permits it.

## Production federation

Replace the reference HMAC/shared-secret design with mutually authenticated TLS, asymmetric capability signatures, key rotation, replay protection, isolated executors, independent metering, secrets management, observability, and incident response. Do not enable real payments until legal and financial controls are complete.

## GUI/computer use

Treat GUI as a fallback capability surface. Bind it to a named user, application allowlist, data scope, visible action log, screenshot retention policy, and reversible action boundary. Never infer permission from screen visibility.
