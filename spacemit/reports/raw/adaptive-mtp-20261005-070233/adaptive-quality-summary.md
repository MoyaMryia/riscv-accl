# Adaptive MTP screen

```json
{
  "status": "completed",
  "generation_exit": "1",
  "verified_artifacts": 26,
  "models": {
    "2B": {
      "status": "timing skipped or incomplete",
      "generation": {
        "state_gate": "pass",
        "status": "failed",
        "failed_stage": "2B calibrate unicode_offsets",
        "reason": "ValueError: 2B calibrate unicode_offsets: rejected answer: complete; finish_reason=length; completion_tokens=3072"
      },
      "qualified": false
    },
    "4B": {
      "status": "timing skipped or incomplete",
      "generation": {
        "state_gate": "pass",
        "status": "timing skipped: held-out direct code failed functional checks"
      },
      "qualified": false
    }
  },
  "candidate_qualified": false,
  "limitations": "Three repetitions of three tasks/model, one slot, one two-order cloud judge. No long-context/concurrency or statistical-equivalence claim."
}
```
