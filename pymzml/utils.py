import numpy as np
from numpy.typing import NDArray
from .constants import NoiseMode

def make_obo_mapping(obo: str, reversed: bool = False) -> dict[str, str]:
    """Create ID-to-name or name-to-ID mapping from OBO file."""
    mapping: dict[str, str] = {}
    id: str = ""
    with open(obo) as obo_file:
        for line in obo_file:
            if line.startswith("id: "):
                id = line.split()[-1]
            elif line.startswith("name: "):
                mapping[id] = " ".join(line.split()[1:])
    if reversed:
        mapping = {y: x for x, y in mapping.items()}
    return mapping


def filter_range(
    arr: NDArray[np.float64],
    mz_range: tuple[float | None, float | None],
) -> NDArray[np.float64]:
    """Filter peaks to specified m/z range."""

    # Handle None values in mz_range
    min_mz = mz_range[0] if mz_range[0] is not None else -np.inf
    max_mz = mz_range[1] if mz_range[1] is not None else np.inf

    mask = np.logical_and(arr[:, 0] >= min_mz, arr[:, 0] <= max_mz)
    peaks = arr[mask]
    return peaks


def filter_noise(
    arr: NDArray[np.float64],
    mode: str | NoiseMode = NoiseMode.MEDIAN,
    noise_level: float | None = None,
    signal_to_noise_threshold: float = 1.0,
) -> NDArray[np.float64]:
    """Remove noise from peaks based on signal-to-noise threshold."""
    # Convert string to enum if needed
    if isinstance(mode, str):  # type: ignore
        mode = NoiseMode(mode)

    if noise_level is None:
        noise_level = estimated_noise_level(arr, mode=mode)

    peaks = arr[arr[:, 1] / noise_level >= signal_to_noise_threshold]

    return peaks


def estimated_noise_level(
    arr: NDArray[np.float64], mode: str | NoiseMode = NoiseMode.MEDIAN
) -> float:
    """Estimate noise level using specified mode (median, mean, or MAD)."""
    # Convert string to enum if needed
    if isinstance(mode, str):  # type: ignore
        mode = NoiseMode(mode)

    if len(arr) == 0:
        return 0.0

    if mode == NoiseMode.MEDIAN:
        return float(np.median(arr[:, 1]))
    elif mode == NoiseMode.MAD:
        median = estimated_noise_level(arr, mode=NoiseMode.MEDIAN)
        return float(np.median(np.abs(arr[:, 1] - median)))
    elif mode == NoiseMode.MEAN:
        return float(np.mean(arr[:, 1]))
    else:
        print(f"Unknown noise level estimation mode: {mode}")
        return 0.0
