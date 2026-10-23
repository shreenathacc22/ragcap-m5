# P&ID branch evaluation (step 24)

Vision model qwen2.5vl:7b on Apple M5 Pro (Metal GPU); seconds per drawing: [11.2, 7.6, 7.5].

| Drawing | Tags expected | Correct | Invented | Missed |
|---|---|---|---|---|
| P&ID-001 | 13 | 13 | - | - |
| P&ID-002 | 13 | 13 | - | - |
| P&ID-003 | 13 | 13 | - | - |

| QA metric (12 frozen questions, full graph) | Result |
|---|---|
| Routed to documents | 100% |
| Right drawing retrieved | 100% |
| Answer correct | 50% (6/12) |
| valve isolating a pump | 0/3 |
| controller + control valve | 3/3 |
| what an instrument measures, on what | 3/3 |
| which drawing / unit | 0/3 |
| Mean latency | 2.5 s |
