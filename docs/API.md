# CLI and Node API

## CLI

- `inspect`
- `plan TASK --capabilities DIR --output DIR`
- `run TASK --capabilities DIR --output DIR`
- `suite --root DIR --output DIR`
- `internalize RECIPE --output FILE`
- `calibrate MANIFEST OUTCOME --output FILE`
- `verify LEDGER`
- `issue-lease PAYLOAD --secret SECRET`
- `serve-node --capabilities DIR --node-id ID --host HOST --port PORT`

## Node HTTP endpoints

- `GET /health`
- `GET /manifest`
- `POST /quote`
- `POST /execute`

`/execute` requires a bearer token, a valid lease, a capability-node match, an operation match, and an unexhausted call limit. Only allowlisted built-in operations are executable in the reference release.
