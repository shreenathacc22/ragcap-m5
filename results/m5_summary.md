# Series summary: m5

### Held-out set (25 unseen cases) (3 runs)

| Metric | Mean | Min | Max |
|---|---|---|---|
| router_accuracy | 100.0% | 100.0% | 100.0% |
| answer_correct | 80.0% | 80.0% | 80.0% |
| retrieval_hit_rate_doc | 100.0% | 100.0% | 100.0% |
| errors (cases hitting an exception) | 0.0 | 0 | 0 |

| Type | Mean correct | Range |
|---|---|---|
| version_current | 69% | 69% - 69% |
| sql | 100% | 100% - 100% |
| general | 100% | 100% - 100% |
| unanswerable | 100% | 100% - 100% |

Failing case ids (times failed out of 3): h-doc-01 x3, h-doc-05 x3, h-doc-13 x3, h-doc-14 x3, h-doc-15 x3

| Flow | Answers (all runs) | Avg LLM calls | Tokens in / out | Avg latency | Equiv. cost |
|---|---|---|---|---|---|
| document+rewrite | 24 | 14.2 | 3706 / 137 | 1.7 s | $0.00170 |
| document | 30 | 8.0 | 2318 / 89 | 1.1 s | $0.00107 |
| database | 15 | 3.0 | 768 / 86 | 0.9 s | $0.00044 |
| general | 6 | 2.0 | 427 / 35 | 0.3 s | $0.00023 |

### Original set (27 cases, tuned on) (3 runs)

| Metric | Mean | Min | Max |
|---|---|---|---|
| router_accuracy | 100.0% | 100.0% | 100.0% |
| answer_correct | 92.6% | 92.6% | 92.6% |
| retrieval_hit_rate_doc | 100.0% | 100.0% | 100.0% |
| errors (cases hitting an exception) | 0.0 | 0 | 0 |

| Type | Mean correct | Range |
|---|---|---|
| version_current | 100% | 100% - 100% |
| exact_string | 100% | 100% - 100% |
| multi_hop | 50% | 50% - 50% |
| sql | 83% | 83% - 83% |
| general | 100% | 100% - 100% |
| unanswerable | 100% | 100% - 100% |

Failing case ids (times failed out of 3): doc-015 x3, db-004 x3

| Flow | Answers (all runs) | Avg LLM calls | Tokens in / out | Avg latency | Equiv. cost |
|---|---|---|---|---|---|
| document | 48 | 8.0 | 2387 / 93 | 1.4 s | $0.00110 |
| database | 18 | 3.0 | 764 / 66 | 0.8 s | $0.00041 |
| general | 9 | 2.0 | 430 / 44 | 0.4 s | $0.00024 |
| document+rewrite | 6 | 14.0 | 3638 / 122 | 1.9 s | $0.00165 |
