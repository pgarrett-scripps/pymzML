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


def centroid_peaks_numpy(peaks: NDArray[np.float64]) -> NDArray[np.float64]:
    """Centroid peaks using numpy-optimized vectorized Gaussian fitting."""
    i_array = np.asarray(peaks[:, 1], dtype=np.float64)
    mz_array = np.asarray(peaks[:, 0], dtype=np.float64)

    if len(i_array) < 4:
        return np.empty((0, 2), dtype=np.float64)

    # Match pymzml: start at index 2
    i_prev = i_array[1:-2]
    i_curr = i_array[2:-1]
    i_next = i_array[3:]

    mz_prev = mz_array[1:-2]
    mz_curr = mz_array[2:-1]
    mz_next = mz_array[3:]

    # Match pymzml peak detection exactly
    is_peak = (i_prev > 0) & (i_prev < i_curr) & (i_curr > i_next) & (i_next > 0)

    # Filter out peaks with irregular spacing
    dx1 = mz_curr - mz_prev
    dx2 = mz_next - mz_curr
    valid_spacing = ~((dx1 > dx2 * 10) | (dx1 * 10 < dx2))
    is_peak = is_peak & valid_spacing

    # Extract valid peaks
    x1 = mz_prev[is_peak]
    y1 = i_prev[is_peak]
    x2 = mz_curr[is_peak]
    y2 = i_curr[is_peak]
    x3 = mz_next[is_peak]
    y3 = i_next[is_peak]

    if len(y1) == 0:
        return np.empty((0, 2), dtype=np.float64)

    # Handle y3 == y1 case
    y3_adjusted = np.where(y3 == y1, y3 + 0.01 * y1, y3)

    # Vectorized Gaussian fit - no additional filtering here!
    # Only check for positive intensities (already done in is_peak)
    with np.errstate(divide="ignore", invalid="ignore"):
        double_log = np.log(y2 / y1) / np.log(y3_adjusted / y1)
        numerator = double_log * (x1 * x1 - x3 * x3) - x1 * x1 + x2 * x2
        denominator = 2 * (x2 - x1) - 2 * double_log * (x3 - x1)
        mue = numerator / denominator

        c_squared_num = x2 * x2 - x1 * x1 - 2 * x2 * mue + 2 * x1 * mue
        c_squared_denom = 2 * np.log(y1 / y2)
        c_squared = c_squared_num / c_squared_denom

        a = y1 * np.exp((x1 - mue) * (x1 - mue) / (2 * c_squared))

    # Filter only invalid numerical results
    valid = np.isfinite(mue) & np.isfinite(a)

    return np.column_stack((mue[valid], a[valid]))
