---
title: VendSim VB2
emoji: 🏪
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
---

# vendsim-vb2

`vendsim-vb2` is an OpenEnv 0.2.1-compatible implementation of a Vending-Bench 2 style environment.

The agent runs a vending machine business over a 365-day horizon. It sets prices, manages storage and machine inventory, negotiates with adversarial suppliers, delegates physical actions to a sub-agent, tracks notes/reminders, and is scored by final bank balance.

## Environment Summary

- Starting balance: `$500`
- Episode length: `365` simulated days
- Daily machine fee: `$2`
- Bankruptcy rule: `10` consecutive negative-balance days
- Weekly token billing: `$100 / 1M output tokens`
- Machine layout: `4 x 3` slots
  `2` small rows and `2` large rows
- Restock travel time: `75` minutes
- Reward:
  Default benchmark reward is sparse terminal reward equal to final bank balance.
  Dense shaping is available behind a training flag.

## MCP Tool Surface

Main-agent tools:

- `set_price`
- `send_email`
- `check_balance`
- `check_storage_inventory`
- `wait_for_next_day`
- `run_sub_agent`
- `chat_with_sub_agent`
- `request_supplier_quote`
- `negotiate_supplier`
- `place_supplier_order`
- `check_delivery`
- `get_status`

Memory tools:

- `write_scratchpad`
- `read_scratchpad`
- `search_notes`
- `set_reminder`

Sub-agent tools exposed through `run_sub_agent`:

- `restock_machine`
- `collect_cash`
- `get_machine_inventory`

## Repository Artifacts

Code:

- Environment server: [vendsim_vb2/server/app.py](./vendsim_vb2/server/app.py)
- MCP wrapper: [vendsim_vb2/mcp_env.py](./vendsim_vb2/mcp_env.py)
- Core simulation: [vendsim_vb2/environment.py](./vendsim_vb2/environment.py)

Notebooks:

- Setup verification: [00_setup_verification.ipynb](../notebooks/00_setup_verification.ipynb)
- Training notebook: [01_vb2_training_grpo.ipynb](../notebooks/01_vb2_training_grpo.ipynb)
- Final benchmark run: [02_vb2_final_run.ipynb](../notebooks/02_vb2_final_run.ipynb)

Tests:

- Test suite: [tests](./tests)

## Local Setup

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ./vendsim_vb2[server,dev]
```

Run the tests:

```bash
PYTHONPATH=vendsim_vb2 pytest vendsim_vb2/tests -q
```

## Run Locally

Start the OpenEnv-compatible server:

```bash
PYTHONPATH=vendsim_vb2 python -m uvicorn vendsim_vb2.server.app:create_app --factory --host 0.0.0.0 --port 8000
```

Then connect with `VB2Client` or use the notebooks.

## Hugging Face Spaces Deployment

Build and verify locally first:

```bash
cd vendsim_vb2
docker build -t vendsim-vb2 .
```

Then deploy with OpenEnv tooling from the repo root after configuring your Hugging Face credentials:

```bash
openenv push
```

Submission artifact placeholders:

- HF Space URL: `TODO`
- Installable package / repo URL: `TODO`
- Demo video URL: `TODO`

## Training Artifact

A minimal training script in Colab using Unsloth or HF TRL is included:

- [01_vb2_training_grpo.ipynb](../notebooks/01_vb2_training_grpo.ipynb)