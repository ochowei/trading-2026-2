"""只供人造案例：另立完整暖機的規格，不改公開候選的 DEFAULT_SPEC。"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

path = Path(__file__).with_name("candidate_engine.py")
loader = importlib.util.spec_from_file_location("_synthetic_regime_candidate", path)
module = importlib.util.module_from_spec(loader)
sys.modules[loader.name] = module
loader.loader.exec_module(module)
for name in module.__all__:
    globals()[name] = getattr(module, name)
DEFAULT_SPEC = module.DEFAULT_SPEC.with_changes(fold_warmup_sessions=49)
BASELINE_SPEC = module.BASELINE_SPEC.with_changes(fold_warmup_sessions=49)
_rsi = module._rsi
_intraday_exit = module._intraday_exit
