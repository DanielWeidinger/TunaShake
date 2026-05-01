# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running and testing

To run the CLI or tests, **always use the `tunashake` conda environment**:

```bash
source ~/miniconda3/etc/profile.d/conda.sh && conda activate tunashake
```

Never use the system Python or pip install — dependencies are managed in this environment.
