# DIKWP-MINEX-FABRIC-OS 1.0.0

**Minimum-Energy and Minimum-Effective-Expenditure Capability Routing, Function Internalization, Federated Borrowing, and Metered Exchange Runtime**

The system treats software functions as permission-bound capabilities rather than forcing every task through a named application. For each declared purpose it can compare model-native execution, generated local code, local or remote APIs, browser routes, GUI/computer-use routes, federated nodes, and human execution.

The planner applies hard gates first: authorization, data class, quality, reliability, semantic loss, privacy, irreversibility, budget, and deadline. Only then does it retain a Pareto frontier and choose by a declared lexicographic order. Physical energy is first by default. Money, latency, human effort, privacy, and semantic loss are never silently converted into joules.

## What is implemented

- capability manifests and a local registry;
- constraint-first, Pareto-aware route planning;
- deterministic allowlisted execution for safe reference functions;
- model-native, generated-code, API, browser, GUI, federated-node, and human execution modes;
- permission scopes, data classes, node allowlists, expiring leases, and call limits;
- a localhost capability-node server with bearer authentication and signed leases;
- dry-run metered quotes and settlement receipts without moving real funds;
- licensed declarative function internalization with conformance tests;
- append-only SHA-256 evidence ledgers and DIKWP records;
- outcome calibration that creates a successor manifest rather than overwriting history;
- 12 reference scenarios and 66 automated tests;
- a standalone bilingual dashboard and a single-file Python ZipApp.

## What is deliberately not implemented

- bypassing login, MFA, SSO, operating-system, data, or application permissions;
- arbitrary shell execution or unrestricted model-generated code;
- extraction of proprietary APIs, model weights, prompts, or trade secrets;
- actual payment transfer, escrow, cryptocurrency, or financial custody;
- automatic external action authority;
- a single scalar that trades correctness, rights, or privacy for lower energy.

## Quick start

```bash
python dist/DIKWP_MINEX_FABRIC_OS.pyz inspect
python dist/DIKWP_MINEX_FABRIC_OS.pyz suite --root . --output outputs/my-suite
python dist/DIKWP_MINEX_FABRIC_OS.pyz run examples/tasks/01_csv_profile_direct_function.json \
  --capabilities examples/capabilities --output outputs/my-run
python dist/DIKWP_MINEX_FABRIC_OS.pyz verify outputs/my-run/evidence_ledger.jsonl
```

Open `web/DIKWP_MINEX_FABRIC_OS_Dashboard.html` directly in a browser for the offline dashboard.

## Core decision rule

1. Compile the user's purpose into a task contract.
2. Discover capabilities that can produce the required output.
3. reject routes that fail authorization or noncompensatory constraints.
4. Estimate a non-aggregated resource vector.
5. Retain non-dominated routes.
6. Select by a published lexicographic policy, physical energy first by default.
7. Execute only an allowlisted local function or an explicitly authorized remote adapter.
8. Record result, payment dry-run, residual debt, and successor calibration.

## Source boundary

The attached background article supplied for this project is treated as a scenario source about converging model-native, API, browser, shell, and GUI interaction. Its named future products and benchmark figures are not independently certified by this software release. The architecture does not depend on any specific vendor or model name.
## Reproducible localhost federation demo

```bash
python tools/run_federation_demo.py --output outputs/federation-demo/result.json
```

The demo opens an ephemeral loopback port, requests a manifest and quote, then executes one allowlisted hash operation under a bearer credential and an expiring signed lease.

## Portfolio connections

- [DIKWP MINEX Capability Fabric OS](https://github.com/YucongDuan/DIKWP-MINEX-Capability-Fabric-OS) — model-first capability discovery, leasing, routing, and verified expenditure.
- [DIKWP AGI Continuity Ark OS](https://github.com/YucongDuan/DIKWP-AGI-Continuity-Ark-OS) — personal and household continuity planning across plural AGI futures.
- [DIKWP HUMAN CONTINUITY ARK / SHENGZHOU 28.0.0](https://github.com/YucongDuan/DIKWP-HUMAN-CONTINUITY-ARK-SHENGZHOU-28.0.0) — twelve-floor resilience and offline continuity operations.
- [Yucong Duan research homepage](https://yucong-duan-research.dikwp407.chatgpt.site) and [complete repository ecosystem](https://github.com/YucongDuan/YucongDuan) — wider DIKWP, semantic mathematics, artificial consciousness, governance, and practice programme.

A portfolio link records research continuity or semantic proximity. It does not by itself establish a runtime dependency, interoperability, external adoption, institutional endorsement, or shared legal status.

## Dedication

This project is dedicated to **Duan Dikweipu (段迪克维普)** as a statement of care for a future in which human purpose, dignity, and continuity remain protected. This dedication does not assign authorship, ownership, operational authority, endorsement, or legal responsibility to the dedicatee.
