# VendSim VB2: Can an LLM Run a Vending Machine Business?

VendSim VB2 is an OpenEnv 0.2.1 environment that drops an LLM agent into a 365-day vending machine business simulation. The agent starts with $500 and must maximize its bank balance by setting prices across 5 products, negotiating with adversarial suppliers, managing inventory through a delegated sub-agent, and surviving daily fees, weather-driven demand shifts, and seasonal fluctuations.

The environment features an MCP tool-calling interface with 16 tools spanning pricing, supplier negotiation, inventory management, and a scratchpad memory system. Rewards scale uncapped with agent performance — a skilled agent can grow net worth well beyond the starting capital, while poor decisions lead to bankruptcy. We train with GRPO using Unsloth on a Qwen2.5-1.5B model, showing measurable improvement in pricing decisions and revenue generation over training steps.

**Problem Statement:** Long-Horizon Planning & Instruction Following (Statement 2)

**Partner Sub-Theme:** Mercor — uncapped rewards scaling with token output

## Links

- **HF Space:** https://huggingface.co/spaces/retroam/vendsim-vb2
- **GitHub:** https://github.com/retroam/vendsim-vb2
- **Training Notebook:** [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/retroam/vendsim-vb2/blob/main/notebooks/01_vb2_training_grpo.ipynb)
- **Demo Video:** TODO
