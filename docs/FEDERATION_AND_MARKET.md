# Federation and Metered Capability Exchange

A capability node exposes health, manifests, quotes, and optionally execution. Execution is disabled by default. When enabled, it requires both a bearer credential and a signed expiring lease. The lease restricts node identifiers, capability identifiers, expiry, and maximum calls.

The reference market creates a quote with a terms hash and a dry-run settlement bound to the output hash. No real money moves. A production implementation would require regulated payment infrastructure, dispute handling, tax and sanctions controls, identity proofing, refund logic, and independent financial and security review.

Function borrowing does not transfer ownership of the provider's software, data, or model. It grants only the bounded operation described by the capability manifest and lease.
