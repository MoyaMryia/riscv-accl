# Experiments index

Use the [documentation guide](../DOCS.md) for current work and the
[integration guide](../README.md) for packaged patch application.
Experiment patches often target `a990751`; the helper targets `5ad05d8`.
Follow individual base and patch-order instructions.

| Experiment | Present interpretation |
| --- | --- |
| [Original wide RVV](2026-09-26-wide-rvv-fa.md) | Superseded: its 128-byte-vector dispatcher did not activate on K1 |
| [256-bit RVV](2026-09-26-wide-rvv-vlen256.md) | Built, measured and integrated; optional patch 0009, enabled with `SPINE_FA_WIDE_TILE=1` for tested F16 KV |
| [Windowed MTP](2026-09-26-windowed-mtp.md) | Optional patch 0010; measured draft-memory savings, single-pair speed observations; MTP long-code limitation remains |
| [Context speculative gate](2026-09-26-context-spec-gate.md) | Separate proposal, no measured adoption claim |
| [Page gathering](2026-09-26-page-gather.md) | Evaluated negatively; not full paged allocation or adopted acceleration |
| [Target-logit trace](2026-09-27-spec-logits-trace.md) | Completed diagnostic; traced source removed and original server rebuilt |
| [Perfect-draft probe](2026-09-28-perfect-draft-probe.md) | x86 mechanism evidence; no K1 optimization or implemented tie guard |
| [Compact K1 layout](2026-09-30-k1-attention-layout.md) | Completed native/model pilot; small effects, no adoption; staged fast screen follows |
| [Fast-test method](2026-09-30-fast-test-design.md) | Implemented controller and concurrent timing; corrected screen completed in 8.45 minutes, model gains below threshold |

Older queued-run instructions explain historical procedures. Consult completed
reports before repeating them. Experimental and rejected patches remain as
evidence; they are not all options in `apply-patches.sh`.
