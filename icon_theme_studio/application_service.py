import configparser, os, re
from pathlib import Path
from .models import DesktopApp

def application_dirs():
    dirs=[]; home=Path.home(); data=Path(os.environ.get("XDG_DATA_HOME",home/".local/share")); dirs += [data/"applications",Path("/usr/share/applications")]
    dirs += [Path(x)/"applications" for x in os.environ.get("XDG_DATA_DIRS","/usr/local/share:/usr/share").split(":")]
    return dirs

def discover_apps(show_hidden=False):
    result={}
    # A entrada do usuário tem precedência sobre a entrada do sistema.
    # Percorremos o sistema primeiro e sobrescrevemos com ~/.local depois.
    for root in reversed(application_dirs()):
        if not root.is_dir(): continue
        for p in root.glob("*.desktop"):
            cp=configparser.ConfigParser(interpolation=None); cp.optionxform=str
            try: cp.read(p, encoding="utf-8"); s=cp["Desktop Entry"]
            except Exception: continue
            if s.get("Type","Application")!="Application": continue
            hidden=s.getboolean("Hidden", fallback=False); nodisplay=s.getboolean("NoDisplay", fallback=False)
            if not show_hidden and (hidden or nodisplay): continue
            result[p.name]=DesktopApp(p.name,s.get("Name",p.stem),s.get("Icon",""),s.get("Exec",""),s.get("Categories",""),p,hidden,nodisplay)
    return sorted(result.values(),key=lambda x:x.name.casefold())

def remove_absolute_icon(app: DesktopApp):
    if not app.path or not app.icon.startswith('/'):
        raise ValueError("Este aplicativo não usa um caminho absoluto.")
    user_apps=Path(os.environ.get("XDG_DATA_HOME",Path.home()/".local/share"))/"applications"
    try: app.path.resolve().relative_to(user_apps.resolve())
    except ValueError: raise PermissionError("O launcher do sistema não pode ser modificado.")
    technical=Path(app.icon).stem; lines=app.path.read_text(encoding="utf-8").splitlines(keepends=True); in_entry=False; changed=False
    for i,line in enumerate(lines):
        if line.strip()=="[Desktop Entry]": in_entry=True; continue
        if in_entry and line.startswith("["): in_entry=False
        if in_entry and re.match(r"^Icon=",line): lines[i]=f"Icon={technical}{'\n' if line.endswith(chr(10)) else ''}"; changed=True; break
    if not changed: raise ValueError("A entrada Icon= não foi encontrada.")
    app.path.write_text("".join(lines),encoding="utf-8"); app.icon=technical
