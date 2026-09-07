# Security Policy

## Invariants

- No permission bypass: GUI ability is not authorization.
- No arbitrary shell or arbitrary model-generated code execution.
- External execution is disabled unless a node is started with `--allow-execution`, a bearer token, and a lease secret.
- Every execution lease is scoped by node, capability, expiry, and call count.
- The reference payment layer is dry-run only and never transfers funds.
- Sensitive data can be constrained to local modes and zero egress.
- `automatic_external_action_authority` is always zero in release certificates.

## Production hardening still required

The reference HMAC lease is suitable for a controlled shared-secret environment, not an open multi-organization federation. Production use requires mutually authenticated transport, asymmetric signatures, key rotation, replay prevention, sandboxing, rate limits, independent energy metering, secrets management, audit retention, and jurisdiction-specific payment and data governance.
