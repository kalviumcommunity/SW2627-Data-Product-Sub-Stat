"""Compatibility shim for legacy imports.

This enables `from kpi_functions import calculate_mau` while the
canonical implementations live in `kpis/kpi_functions.py`.
"""

from kpis.kpi_functions import *