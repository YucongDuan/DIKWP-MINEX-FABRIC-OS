# Function Internalization Policy

"Internalization" in this release means a licensed local reimplementation of a declared function under conformance tests. It does not mean extracting model weights, reverse engineering a hidden API, copying a proprietary program, memorizing confidential outputs, or bypassing usage terms.

An internalization recipe must declare the source capability, license permission, safe expression or pipeline, input/output scope, tolerance, tests, expected quality, and lineage. Failure of any test blocks registration. Passing tests produces `INTERNALIZED_WITHIN_TEST_SCOPE`; it does not establish universal equivalence.

A successor manifest preserves the source capability identifier, test count, permission statement, and version. If later results fail, the local capability is calibrated, restricted, or retired without deleting its history.
