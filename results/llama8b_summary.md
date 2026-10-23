# Series summary: llama8b

### Held-out set (25 unseen cases) (3 runs)

| Metric | Mean | Min | Max |
|---|---|---|---|
| router_accuracy | 100.0% | 100.0% | 100.0% |
| answer_correct | 92.0% | 92.0% | 92.0% |
| retrieval_hit_rate_doc | 100.0% | 100.0% | 100.0% |
| errors (cases hitting an exception) | 0.0 | 0 | 0 |

| Type | Mean correct | Range |
|---|---|---|
| version_current | 94% | 94% - 94% |
| sql | 100% | 100% - 100% |
| general | 100% | 100% - 100% |
| unanswerable | 50% | 50% - 50% |

Failing case ids (times failed out of 3): h-doc-14 x3, h-una-02 x3

| Flow | Answers (all runs) | Avg LLM calls | Tokens in / out | Avg latency | Equiv. cost |
|---|---|---|---|---|---|
| document | 54 | 8.0 | 2586 / 101 | 2.5 s | $0.00120 |
| database | 15 | 3.0 | 737 / 66 | 1.5 s | $0.00040 |
| general | 6 | 2.0 | 407 / 38 | 0.7 s | $0.00022 |

### Original set (27 cases, tuned on) (3 runs)

| Metric | Mean | Min | Max |
|---|---|---|---|
| router_accuracy | 100.0% | 100.0% | 100.0% |
| answer_correct | 96.3% | 96.3% | 96.3% |
| retrieval_hit_rate_doc | 100.0% | 100.0% | 100.0% |
| errors (cases hitting an exception) | 0.0 | 0 | 0 |

| Type | Mean correct | Range |
|---|---|---|
| version_current | 100% | 100% - 100% |
| exact_string | 100% | 100% - 100% |
| multi_hop | 100% | 100% - 100% |
| sql | 83% | 83% - 83% |
| general | 100% | 100% - 100% |
| unanswerable | 100% | 100% - 100% |

Failing case ids (times failed out of 3): db-004 x3

| Flow | Answers (all runs) | Avg LLM calls | Tokens in / out | Avg latency | Equiv. cost |
|---|---|---|---|---|---|
| document | 48 | 8.0 | 2814 / 109 | 2.8 s | $0.00130 |
| database | 18 | 3.0 | 732 / 64 | 1.5 s | $0.00039 |
| general | 9 | 2.0 | 410 / 39 | 0.8 s | $0.00023 |
| document+rewrite | 6 | 14.5 | 3708 / 109 | 3.0 s | $0.00166 |
