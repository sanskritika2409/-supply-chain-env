\---

title: Supply Chain Env

emoji: 🏭

colorFrom: blue

colorTo: green

sdk: docker

pinned: false

app\_port: 7860

\---



\# 🏭 SupplyChain-Env



An OpenEnv environment for AI supply chain crisis management.



\## Tasks



\- risk\_identification (Easy) - Find at-risk orders after supplier fire

\- inventory\_reallocation (Medium) - Reallocate inventory before warehouse floods  

\- crisis\_recovery (Hard) - 7-day multi-disruption crisis management



\## Endpoints



\- POST /reset - Reset environment

\- POST /step - Take an action

\- GET /state - Get current state

\- GET /tasks - List all tasks

\- GET /health - Health check



\## Run Baseline

```bash

export HF\_TOKEN=your\_token

export ENV\_BASE\_URL=https://sanskritika2409-supply-chain-env.hf.space

python inference.py

```



\## Scores

\- risk\_identification: \~0.75

\- inventory\_reallocation: \~0.50

\- crisis\_recovery: \~0.28

\- average: \~0.526

