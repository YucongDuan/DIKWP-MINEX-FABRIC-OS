# Threat Model

## Protected assets

Purpose contracts, user data, authorization scopes, capability manifests, provider prices, output integrity, settlement receipts, energy observations, and revision history.

## Adversaries and failures

1. A model or tool claims a capability it does not possess.
2. A GUI route is mistaken for authorization.
3. A remote provider receives data outside its permitted class.
4. A provider understates price or energy and overstates quality.
5. A requester attempts to exceed a lease or replay a receipt.
6. A generated function copies a proprietary implementation or executes unsafe code.
7. A low-energy route produces a low-quality or semantically lossy result.
8. A planner hides a value judgment inside a scalar score.
9. A failed route remains preferred because calibration never updates it.
10. A real payment adapter settles before output verification.

## Controls in this release

Constraint-first planning; node, scope, data-class, expiry and call-limit checks; allowlisted builtins; restricted expression AST; no arbitrary shell; HMAC leases for controlled environments; hash-linked ledgers; dry-run settlements; explicit evidence classes; append-only calibrated successor manifests; and automatic external authority fixed at zero.

## Residual risk

The reference HMAC protocol is not a complete public federation security design. Energy values are declared/modelled until connected to hardware meters. GUI reliability is not measured here. Production settlement, legal compliance, identity proofing, secure enclaves, model-provider adapters, and cross-jurisdiction data governance remain outside this release.
