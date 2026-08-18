from typing import Any, Dict
from .base import BaseValuator
from .tracin_valuator import TracInValuator
from .leave_one_out import FastLOOValuator

def get_valuator(method_name: str, **kwargs) -> BaseValuator:
    if method_name == "tracin":
        return TracInValuator(
            checkpoint_dir=kwargs.get("checkpoint_dir"),
            configured_lr=kwargs.get("configured_lr"),
            trainer_results=kwargs.get("trainer_results")
        )
    elif method_name == "leave_one_out_approx":
        return FastLOOValuator(n_iterations=kwargs.get("n_iterations", 10))
    else:
        raise ValueError(f"Unknown valuation method: {method_name}")
