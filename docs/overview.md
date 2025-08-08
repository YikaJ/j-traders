## Overview

Goals: Build a minimal quant factor pipeline from cataloged data to coded factors, quick test, persistence, strategy composition and run.

Key steps
1. Select fields (Catalog → Selections)
2. Generate factor code (Coding Agent or scaffold) based on selection context
3. Quick test with standardization preview
4. Save factor
5. Create strategy
6. Assign factor weights (decide standardization + weight normalization)
7. Run strategy (Top N)

Core principles
- Data-driven via JSON catalog
- Secure sandboxed factor execution
- Modular APIs, simple persistence, scalable later
