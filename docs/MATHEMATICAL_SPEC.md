# Mathematical Specification

Let a task contract be

`T = (P, op, X, Y, Q_min, R_min, L_sem_max, R_priv_max, R_irrev_max, E_max, C_max, tau_max, A)`

where `P` is the purpose, `op` the required operation, `X/Y` the input/output contracts, `Q_min` quality, `R_min` reliability, `L_sem_max` semantic-loss bound, `R_priv_max` privacy-risk bound, `R_irrev_max` irreversibility bound, `E_max` energy budget, `C_max` monetary budget, `tau_max` deadline, and `A` the authorization context.

A capability is

`c = (op_c, mode, provider, node, scopes, classes, q, r, e, tau, money, human, egress, loss, privacy, irreversibility, lineage)`.

The feasible set is

`F(T,A) = { c | op_c = op and Authorized(c,T,A) and Quality(c)>=Q_min and Reliability(c)>=R_min and Loss(c)<=L_sem_max and Privacy(c)<=R_priv_max and Irreversibility(c)<=R_irrev_max and Energy(c)<=E_max and Cost(c)<=C_max and Latency(c)<=tau_max }`.

For a feasible route, retain the vector

`v(c,T) = (E_phys, C_money, tau, H_human, B_egress, L_sem, R_priv, R_irrev, -Q, -R)`.

No component is silently converted into another. A route is Pareto-dominated if another feasible route is no worse in every declared dimension and strictly better in at least one. The default selector applies the published lexicographic order

`E_phys -> C_money -> tau -> H_human -> B_egress`

to the Pareto frontier. A task may supply a different order, but cannot remove hard gates without creating a successor contract.

For independent subtasks, total physical energy and monetary cost are additive, while expected latency is the critical-path maximum. Reliability and quality are conservatively composed as the minimum of step-level values in the reference runtime.

Function internalization is admitted only when

`LicenseOK and ForAll i: distance(f_local(x_i), y_i) <= epsilon`

under an explicit test scope. This is a conformance certificate, not proof of equivalence on untested inputs.
