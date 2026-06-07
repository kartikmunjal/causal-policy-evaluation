# Phase 2 Research-Grade Infrastructure

Phase 2 starts after the first-prompt baseline repo. It does not replace the original causal design; it makes the design more auditable and scalable.

Phase 2 added:

- audited minimum-wage policy-table schema and validation
- Census cross-state county adjacency and border-pair construction
- national border-county-pair panel builder
- fail-closed checks so unaudited policy timing cannot generate national estimates
- balance tables and raw trend diagnostics
- joint pretrend tests
- placebo policy-year tests
- wild-cluster bootstrap diagnostics
- reproducibility manifest with file hashes
- Makefile and end-to-end orchestration

The purpose of Phase 2 is research discipline: data provenance, reproducibility, and inference diagnostics.
