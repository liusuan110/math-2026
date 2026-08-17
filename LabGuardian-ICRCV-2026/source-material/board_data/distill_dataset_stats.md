# SFT Dataset Distribution Summary

- Candidate teacher rows: 4990
- High-purity teacher rows: 3466
- Final SFT rows: 3450
- Filtered before trainable: 1524
- Skipped after trainable: 16

## Intent distribution

| Label | Count | Pct |
|---|---:|---:|
| diagnostic | 1625 | 47.1% |
| lab_guidance | 975 | 28.26% |
| concept_tutor | 436 | 12.64% |
| mixed | 414 | 12.0% |

## Scene distribution

| Label | Count | Pct |
|---|---:|---:|
| RC | 680 | 19.71% |
| Common-emitter | 653 | 18.93% |
| Differential | 473 | 13.71% |
| UA741 inverting | 619 | 17.94% |
| UA741 integrator | 552 | 16.0% |
| UA741 summing | 473 | 13.71% |

## Risk distribution

| Label | Count | Pct |
|---|---:|---:|
| danger | 190 | 5.51% |
| warning | 2824 | 81.86% |
| safe | 436 | 12.64% |

## Error tag distribution

| Label | Count | Pct |
|---|---:|---:|
| MISSING_COMPONENT | 420 | 27.49% |
| FLOATING_CONNECTION | 414 | 27.09% |
| WRONG_NODE_CONNECTION | 301 | 19.7% |
| INCOMPLETE_CIRCUIT | 203 | 13.29% |
| SHORT_RISK | 190 | 12.43% |

## Output length

- min / mean / max chars: 84 / 284.45 / 693
