"""Module 5 — NumPy Vectorised Computation & Performance Benchmarking

Demonstrates and benchmarks NumPy vectorized computations vs. baseline Python iterative loops:
- Min-Max Normalization (Loop vs. Vectorized)
- Z-score Standardization (Loop vs. Vectorized)
- Multi-variate Non-Linear Engagement Index (Loop vs. Vectorized)
- DataFrame Integration of vectorized series
- Automated Benchmarking Suite across dataset scales (1K, 10K, 100K) with speedup metrics
- Detailed architectural analysis of vectorization advantages (SIMD, cache locality, interpreter overhead).
"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple, Union

import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


# =====================================================================
# 1. Min-Max Normalization Implementations
# =====================================================================

def min_max_normalize_loop(values: Union[List[float], np.ndarray, pd.Series]) -> List[float]:
    """
    Baseline Python loop implementation of Min-Max normalization.
    Maps values to [0.0, 1.0].
    """
    val_list = list(values)
    if not val_list:
        return []

    min_val = min(val_list)
    max_val = max(val_list)
    val_range = max_val - min_val

    if val_range == 0:
        return [0.0 for _ in val_list]

    normalized = []
    for x in val_list:
        norm_x = (x - min_val) / val_range
        normalized.append(norm_x)

    return normalized


def min_max_normalize_vectorized(values: Union[np.ndarray, pd.Series, List[float]]) -> np.ndarray:
    """
    NumPy vectorized implementation of Min-Max normalization.
    Executes compiled C-array SIMD vector arithmetic.
    """
    arr = np.asarray(values, dtype=np.float64)
    if arr.size == 0:
        return np.empty(0, dtype=np.float64)

    min_val = np.min(arr)
    max_val = np.max(arr)
    val_range = max_val - min_val

    if val_range == 0.0:
        return np.zeros_like(arr)

    return (arr - min_val) / val_range


# =====================================================================
# 2. Z-Score Standardization Implementations
# =====================================================================

def z_score_standardize_loop(values: Union[List[float], np.ndarray, pd.Series]) -> List[float]:
    """
    Baseline Python loop implementation of Z-score standardization (mean=0, std=1).
    """
    val_list = list(values)
    n = len(val_list)
    if n == 0:
        return []

    mean_val = sum(val_list) / n
    variance = sum((x - mean_val) ** 2 for x in val_list) / n
    std_val = variance ** 0.5

    if std_val == 0:
        return [0.0 for _ in val_list]

    standardized = []
    for x in val_list:
        z = (x - mean_val) / std_val
        standardized.append(z)

    return standardized


def z_score_standardize_vectorized(values: Union[np.ndarray, pd.Series, List[float]]) -> np.ndarray:
    """
    NumPy vectorized implementation of Z-score standardization.
    """
    arr = np.asarray(values, dtype=np.float64)
    if arr.size == 0:
        return np.empty(0, dtype=np.float64)

    mean_val = np.mean(arr)
    std_val = np.std(arr)

    if std_val == 0.0:
        return np.zeros_like(arr)

    return (arr - mean_val) / std_val


# =====================================================================
# 3. Composite Non-Linear Score (Multi-Variable Operation)
# =====================================================================

def compute_composite_score_loop(
    watch_mins: List[float],
    sessions: List[float],
    dropoffs: List[float],
) -> List[float]:
    """
    Baseline Python iterative loop computing non-linear engagement scores:
    Score = 0.5 * (watch_mins ** 1.1) + 1.2 * log(1 + sessions) - 0.8 * exp(0.02 * dropoffs)
    """
    import math

    scores = []
    n = len(watch_mins)
    for i in range(n):
        wm = watch_mins[i]
        ses = sessions[i]
        drp = dropoffs[i]

        score = (
            0.5 * (wm ** 1.1)
            + 1.2 * math.log(1.0 + ses)
            - 0.8 * math.exp(0.02 * drp)
        )
        scores.append(score)
    return scores


def compute_composite_score_vectorized(
    watch_mins: np.ndarray,
    sessions: np.ndarray,
    dropoffs: np.ndarray,
) -> np.ndarray:
    """
    NumPy vectorized implementation using universal functions (np.power, np.log1p, np.exp).
    """
    wm = np.asarray(watch_mins, dtype=np.float64)
    ses = np.asarray(sessions, dtype=np.float64)
    drp = np.asarray(dropoffs, dtype=np.float64)

    return (
        0.5 * np.power(wm, 1.1)
        + 1.2 * np.log1p(ses)
        - 0.8 * np.exp(0.02 * drp)
    )


# =====================================================================
# 4. DataFrame Integration
# =====================================================================

def integrate_vectorized_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply vectorized normalizations and composite computations, integrating results into DataFrame.
    """
    df_copy = df.copy()

    if "watch_duration_mins" in df_copy.columns:
        # Min-Max
        df_copy["watch_duration_minmax"] = min_max_normalize_vectorized(df_copy["watch_duration_mins"]).round(4)
        # Z-Score
        df_copy["watch_duration_zscore"] = z_score_standardize_vectorized(df_copy["watch_duration_mins"]).round(4)

    if all(col in df_copy.columns for col in ["watch_duration_mins", "session_count", "dropoff_count"]):
        df_copy["vectorized_engagement_index"] = compute_composite_score_vectorized(
            df_copy["watch_duration_mins"].values,
            df_copy["session_count"].values,
            df_copy["dropoff_count"].values,
        ).round(4)

    return df_copy


# =====================================================================
# 5. Benchmarking Engine
# =====================================================================

def benchmark_operation(
    scale: int,
    runs: int = 5,
) -> Dict[str, Any]:
    """
    Benchmark Python loops vs. NumPy vectorization across operations for a given data size.
    """
    # Generate synthetic benchmark arrays
    np.random.seed(42)
    watch_data = np.random.uniform(5.0, 300.0, size=scale)
    session_data = np.random.uniform(1.0, 50.0, size=scale)
    dropoff_data = np.random.uniform(0.0, 10.0, size=scale)

    watch_list = watch_data.tolist()
    session_list = session_data.tolist()
    dropoff_list = dropoff_data.tolist()

    # 1. Min-Max Normalization
    # Loop
    loop_start = time.perf_counter()
    for _ in range(runs):
        _ = min_max_normalize_loop(watch_list)
    loop_minmax_time = (time.perf_counter() - loop_start) / runs

    # Vectorized
    vec_start = time.perf_counter()
    for _ in range(runs):
        _ = min_max_normalize_vectorized(watch_data)
    vec_minmax_time = (time.perf_counter() - vec_start) / runs

    minmax_speedup = round(loop_minmax_time / max(vec_minmax_time, 1e-9), 2)

    # 2. Z-Score Standardization
    # Loop
    loop_start = time.perf_counter()
    for _ in range(runs):
        _ = z_score_standardize_loop(watch_list)
    loop_zscore_time = (time.perf_counter() - loop_start) / runs

    # Vectorized
    vec_start = time.perf_counter()
    for _ in range(runs):
        _ = z_score_standardize_vectorized(watch_data)
    vec_zscore_time = (time.perf_counter() - vec_start) / runs

    zscore_speedup = round(loop_zscore_time / max(vec_zscore_time, 1e-9), 2)

    # 3. Composite Non-Linear Score
    # Loop
    loop_start = time.perf_counter()
    for _ in range(runs):
        _ = compute_composite_score_loop(watch_list, session_list, dropoff_list)
    loop_composite_time = (time.perf_counter() - loop_start) / runs

    # Vectorized
    vec_start = time.perf_counter()
    for _ in range(runs):
        _ = compute_composite_score_vectorized(watch_data, session_data, dropoff_data)
    vec_composite_time = (time.perf_counter() - vec_start) / runs

    composite_speedup = round(loop_composite_time / max(vec_composite_time, 1e-9), 2)

    return {
        "dataset_size_rows": scale,
        "runs_averaged": runs,
        "min_max_normalization": {
            "loop_time_sec": round(loop_minmax_time, 6),
            "vectorized_time_sec": round(vec_minmax_time, 6),
            "speedup_factor": f"{minmax_speedup}x",
        },
        "z_score_standardization": {
            "loop_time_sec": round(loop_zscore_time, 6),
            "vectorized_time_sec": round(vec_zscore_time, 6),
            "speedup_factor": f"{zscore_speedup}x",
        },
        "composite_nonlinear_computation": {
            "loop_time_sec": round(loop_composite_time, 6),
            "vectorized_time_sec": round(vec_composite_time, 6),
            "speedup_factor": f"{composite_speedup}x",
        },
    }


def run_numpy_vectorization_pipeline(
    sample_size: int = 1000,
    benchmark_scales: Tuple[int, ...] = (1000, 10000, 100000),
    output_data_path: Union[str, Path] = "data/processed/vectorized_computations_data.csv",
    output_report_path: Union[str, Path] = "output/numpy_vectorization_benchmark.json",
) -> Dict[str, Any]:
    """
    Execute full vectorization demonstration, DataFrame integration, and multi-scale benchmark.
    """
    output_file = Path(output_data_path)
    report_file = Path(output_report_path)

    output_file.parent.mkdir(parents=True, exist_ok=True)
    report_file.parent.mkdir(parents=True, exist_ok=True)

    # 1. Create sample DataFrame for integration
    np.random.seed(42)
    sample_df = pd.DataFrame(
        {
            "viewer_id": [f"V{1000 + i}" for i in range(sample_size)],
            "watch_duration_mins": np.random.exponential(scale=45.0, size=sample_size).round(2),
            "session_count": np.random.poisson(lam=12, size=sample_size),
            "dropoff_count": np.random.poisson(lam=2, size=sample_size),
        }
    )

    # 2. Integrate vectorized features
    df_integrated = integrate_vectorized_features(sample_df)
    df_integrated.to_csv(output_file, index=False)
    logger.info("Saved integrated vectorized DataFrame to %s (%d rows)", output_file, len(df_integrated))

    # 3. Run Benchmark across scales
    logger.info("Executing performance benchmark across scales %s...", benchmark_scales)
    benchmark_results = []
    for scale in benchmark_scales:
        bench_res = benchmark_operation(scale=scale, runs=3)
        benchmark_results.append(bench_res)
        logger.info(
            "Scale %d: Min-Max speedup=%s, Z-Score speedup=%s, Composite speedup=%s",
            scale,
            bench_res["min_max_normalization"]["speedup_factor"],
            bench_res["z_score_standardization"]["speedup_factor"],
            bench_res["composite_nonlinear_computation"]["speedup_factor"],
        )

    # 4. Generate Comprehensive Architectural Documentation & Report
    architectural_rationale = {
        "memory_layout_and_cache_locality": (
            "NumPy stores arrays as contiguous, densely packed C-memory buffers (e.g. float64). "
            "Python lists store pointers to heap-allocated PyObject instances. "
            "Contiguous memory enables hardware prefetching and optimal CPU L1/L2 cache line utilization."
        ),
        "simd_vector_parallelism": (
            "Vectorized NumPy ufuncs compile down to CPU SIMD (Single Instruction, Multiple Data) instructions "
            "(e.g., AVX-2, AVX-512, SSE). A single CPU vector register can process 4 to 8 64-bit float operations per clock cycle."
        ),
        "bytecode_interpreter_overhead": (
            "Python loops incur dynamic type dispatch, reference count incrementing/decrementing, and bytecode interpreter "
            "eval loop overhead for every single iteration. Vectorized routines perform type-checking once and execute in compiled C."
        ),
    }

    report = {
        "status": "SUCCESS",
        "timestamp": datetime.now().isoformat(),
        "output_dataset": str(output_file),
        "integrated_columns": [
            "watch_duration_minmax",
            "watch_duration_zscore",
            "vectorized_engagement_index",
        ],
        "benchmark_summary": benchmark_results,
        "architectural_rationale": architectural_rationale,
    }

    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    logger.info("Saved benchmark report to %s", report_file)
    return report


if __name__ == "__main__":
    run_numpy_vectorization_pipeline()
