# P&ID branch evaluation (step 24)

Vision model qwen2.5vl:3b on Apple M5 Pro (Metal GPU); seconds per drawing: [11.7, 5.5, 5.0].

| Drawing | Tags expected | Correct | Invented | Missed |
|---|---|---|---|---|
| P&ID-001 | 13 | 13 | - | - |
| P&ID-002 | 13 | 13 | - | - |
| P&ID-003 | 13 | 12 | - | FCV-301 |

| QA metric (12 frozen questions, full graph) | Result |
|---|---|
| Routed to documents | 100% |
| Right drawing retrieved | 100% |
| Answer correct | 33% (4/12) |
| valve isolating a pump | 1/3 |
| controller + control valve | 0/3 |
| what an instrument measures, on what | 3/3 |
| which drawing / unit | 0/3 |
| Mean latency | 1.1 s |
