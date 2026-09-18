from dataclasses import dataclass, field
from pathlib import Path

@dataclass
class IconTheme:
    name: str
    path: Path
    display_name: str
    inherits: list[str] = field(default_factory=list)
    directories: list[str] = field(default_factory=list)
    managed: bool = False

@dataclass
class DesktopApp:
    desktop_id: str
    name: str
    icon: str
    exec: str = ""
    categories: str = ""
    path: Path | None = None
    hidden: bool = False
    nodisplay: bool = False
