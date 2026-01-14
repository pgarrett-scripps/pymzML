from dataclasses import dataclass
from .content import CVParam

@dataclass
class ScanWindow:
    cv_params: tuple[CVParam, ...]
    lower_limit: float | None
    upper_limit: float | None

@dataclass
class Scan:
    cv_params: tuple[CVParam, ...]
    scan_window_list: Any

@dataclass
class ScanList:
    cv_params: tuple[CVParam, ...]
    scans: 

@dataclass
class MsData:
    cv_params: tuple[CVParam, ...]
    scans: 