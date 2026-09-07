# Energy Accounting

Physical energy is a first-class field expressed in joules. The reference estimator combines a declared base value, work-unit coefficient, and network-transfer coefficient. Every value carries an evidence class such as DECLARED, MODELLED, MEASURED, or COMPOSED.

The runtime does not convert money, latency, human time, privacy risk, semantic loss, or irreversibility into joules. These remain separate coordinates. The default policy minimizes physical energy only after the route passes authorization, quality, semantic-loss, privacy and irreversibility gates.

Production deployment should connect hardware power counters, cloud-provider telemetry, network transfer measurement, model token accounting, and device-specific idle/baseline allocation. Embodied hardware energy and carbon intensity may be added as separate fields; neither should be hidden inside a universal scalar.
