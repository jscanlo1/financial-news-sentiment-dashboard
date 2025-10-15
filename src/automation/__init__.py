"""
automation
----------
High-level automation package that orchestrates hourly and daily workflows.
"""

from automation._hourly import run_hourly_pipeline

__all__ = ["run_hourly_pipeline"]
