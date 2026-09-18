# Icon Theme Studio

Icon Theme Studio is a desktop application for creating and managing personal Linux icon themes. It was designed and tested primarily for Kubuntu with KDE Plasma 6, but follows the freedesktop.org icon theme conventions and may work with other Linux desktop environments.

It creates a lightweight override theme instead of copying or modifying an entire icon pack. Customized icons are stored in the user's theme; all other icons are resolved through the configured fallback chain:

```text
Yuri Icons → Kora → Breeze → hicolor
```

## Features

- Discover installed icon themes from XDG user data and `/usr/share/icons`.
- Create and manage multiple custom themes.
- Configure base themes and fallbacks graphically, without editing `index.theme` manually.
- Browse icon packs with search, pagination, and an “All themes” view.
- Discover installed applications from XDG `.desktop` files.
- Assign icons from installed packs or external SVG, SVGZ, and PNG files.
- Store only selected overrides in the custom theme.
- Restore fallback icons without modifying original themes.
- Detect absolute icon paths and optionally convert user-owned launchers to symbolic icon names.
- Apply themes for the current user and refresh KDE's service cache.
- Safely delete themes created by the application.

## Requirements

- Linux
- Python 3.10+
- PySide6
- KDE Plasma 6 is the primary target

## Development

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install PySide6
python -m icon_theme_studio
```

## Installation

After installing PySide6 in `.venv`:

```bash
./install.sh
```

The user installation is independent from the source directory and uses:

```text
~/.local/share/icon-theme-studio/
~/.local/bin/icon-theme-studio
~/.local/share/applications/icon-theme-studio.desktop
```

It does not require `sudo`, use `sudo pip`, modify system icon themes, or modify system desktop launchers.

Uninstall with:

```bash
./uninstall.sh
```

The uninstall script preserves custom icon themes.

## Theme inheritance

Managed themes are stored under `~/.local/share/icons/<theme-folder>/` and contain only overrides:

```text
Yuri-Icons/
├── index.theme
└── apps/scalable/vscode.svg
```

When an icon is not present in the custom theme, KDE/Qt searches the `Inherits` chain recursively. Original themes are never copied or modified.

## Safety and limitations

Only themes registered as managed by the application can be edited or deleted. Absolute icon paths do not use normal theme inheritance; the application reports them and offers an explicit action affecting only user-owned launchers. Malformed SVGs may be preserved but skipped in previews. The first release focuses on application icons in `apps/scalable`, while the architecture supports future categories.

Already-running applications and Plasma components can cache icons. The application refreshes KDE's service cache, but a manual Plasma restart may occasionally be needed.

## Project structure

```text
icon_theme_studio/
├── application_service.py
├── config.py
├── models.py
├── theme_service.py
├── ui.py
└── __main__.py
```

## License

No license has been selected yet. Add an appropriate license before publishing the repository publicly.
