import configparser, os, shutil, subprocess
from pathlib import Path
from .models import IconTheme
from .config import load_metadata, save_metadata

ICON_DIRS = [Path(os.environ.get("XDG_DATA_HOME", Path.home()/".local/share"))/"icons", Path("/usr/share/icons")]
USER_ICONS = ICON_DIRS[0]

def _read_theme(path: Path) -> IconTheme | None:
    ini = path / "index.theme"
    if not ini.is_file(): return None
    # Alguns temas populares, como Kora, repetem seções de diretórios no
    # index.theme. O KDE tolera isso; o leitor também deve ser tolerante.
    cp = configparser.ConfigParser(interpolation=None, strict=False); cp.optionxform = str
    try: cp.read(ini, encoding="utf-8"); sec=cp["Icon Theme"]
    except (OSError, KeyError, configparser.Error): return None
    dirs = [x.strip() for x in sec.get("Directories", "").split(",") if x.strip()]
    return IconTheme(path.name, path, sec.get("Name", path.name), [x.strip() for x in sec.get("Inherits", "").split(",") if x.strip()], dirs)

def discover_themes() -> list[IconTheme]:
    found={}
    for root in ICON_DIRS:
        if not root.is_dir(): continue
        for p in root.iterdir():
            if p.is_dir():
                t=_read_theme(p)
                if t: found.setdefault(t.name,t)
    meta=load_metadata().get("themes", {})
    for name, info in meta.items():
        p=USER_ICONS/name
        if p.is_dir() and name in found: found[name].managed=True
    return sorted(found.values(), key=lambda t:t.display_name.lower())

def _safe_name(name):
    return "-".join(name.strip().split()) or "Custom-Icons"

def _directories_for(inherits):
    # O index.theme deve listar apenas diretórios efetivamente presentes no
    # tema personalizado. Os fallbacks continuam sendo resolvidos por
    # Inherits; listar diretórios externos sem suas seções torna o índice
    # inválido para o Plasma.
    return ["apps/scalable"]

def create_theme(display_name, description, inherits):
    folder=_safe_name(display_name); path=USER_ICONS/folder; path.mkdir(parents=True, exist_ok=True)
    inherited=list(dict.fromkeys(x for x in inherits if x))
    cp=configparser.ConfigParser(interpolation=None); cp.optionxform=str
    dirs=_directories_for(inherited)
    for directory in ("apps/scalable","apps/symbolic"):
        (path/directory).mkdir(parents=True, exist_ok=True)
    cp["Icon Theme"]={"Name":display_name,"Comment":description,"Inherits":",".join(inherited),"FollowsColorScheme":"true","DesktopDefault":"48","DesktopSizes":"16,22,32,48,64,128,256","ToolbarDefault":"22","ToolbarSizes":"16,22,32,48","SmallDefault":"16","SmallSizes":"16,22,32,48","PanelDefault":"48","PanelSizes":"16,22,32,48,64,128,256","DialogDefault":"32","DialogSizes":"16,22,32,48,64,128,256","Directories":"apps/scalable,apps/symbolic"}
    cp["apps/scalable"]={"Context":"Applications","Size":"16","MinSize":"8","MaxSize":"512","Type":"Scalable"}
    cp["apps/symbolic"]={"Context":"Applications","Size":"16","MinSize":"8","MaxSize":"512","Type":"Scalable"}
    with (path/"index.theme").open("w", encoding="utf-8") as f: cp.write(f, space_around_delimiters=False)
    data=load_metadata(); data.setdefault("themes",{})[folder]={"display_name":display_name,"description":description}; save_metadata(data)
    return _read_theme(path)

def update_inherits(theme: IconTheme, inherits: list[str]):
    """Atualiza somente a cadeia de herança de um tema gerenciado."""
    meta=load_metadata().get("themes", {})
    if theme.name not in meta or not theme.path.is_relative_to(USER_ICONS):
        raise PermissionError("Somente temas criados pelo aplicativo podem ser editados.")
    ini=theme.path/"index.theme"
    cp=configparser.ConfigParser(interpolation=None, strict=False); cp.optionxform=str
    cp.read(ini, encoding="utf-8")
    if "Icon Theme" not in cp: raise ValueError("index.theme inválido")
    clean=list(dict.fromkeys(x for x in inherits if x))
    cp["Icon Theme"]["FollowsColorScheme"]="true"
    cp["Icon Theme"]["DesktopDefault"]="48"; cp["Icon Theme"]["DesktopSizes"]="16,22,32,48,64,128,256"
    cp["Icon Theme"]["ToolbarDefault"]="22"; cp["Icon Theme"]["ToolbarSizes"]="16,22,32,48"
    cp["Icon Theme"]["SmallDefault"]="16"; cp["Icon Theme"]["SmallSizes"]="16,22,32,48"
    cp["Icon Theme"]["PanelDefault"]="48"; cp["Icon Theme"]["PanelSizes"]="16,22,32,48,64,128,256"
    cp["Icon Theme"]["DialogDefault"]="32"; cp["Icon Theme"]["DialogSizes"]="16,22,32,48,64,128,256"
    cp["Icon Theme"]["Inherits"]=",".join(clean)
    cp["Icon Theme"]["Directories"]="apps/scalable,apps/symbolic"
    for directory in ("apps/scalable","apps/symbolic"):
        (theme.path/directory).mkdir(parents=True, exist_ok=True)
    if "apps/symbolic" not in cp:
        cp["apps/symbolic"]={"Context":"Applications","Size":"16","MinSize":"8","MaxSize":"512","Type":"Scalable"}
    with ini.open("w",encoding="utf-8") as f: cp.write(f,space_around_delimiters=False)
    return _read_theme(theme.path)

def update_theme_name(theme: IconTheme, display_name: str, description: str | None = None):
    meta=load_metadata()
    if theme.name not in meta.get("themes",{}) or not theme.path.is_relative_to(USER_ICONS):
        raise PermissionError("Somente temas criados pelo aplicativo podem ser editados.")
    display_name=display_name.strip()
    if not display_name: raise ValueError("O nome do tema não pode ficar vazio.")
    ini=theme.path/"index.theme"; cp=configparser.ConfigParser(interpolation=None,strict=False); cp.optionxform=str; cp.read(ini,encoding="utf-8")
    cp["Icon Theme"]["Name"]=display_name
    if description is not None: cp["Icon Theme"]["Comment"]=description
    with ini.open("w",encoding="utf-8") as f: cp.write(f,space_around_delimiters=False)
    meta["themes"][theme.name]["display_name"]=display_name
    if description is not None: meta["themes"][theme.name]["description"]=description
    save_metadata(meta); return _read_theme(theme.path)

def active_icon_theme():
    try:
        return subprocess.run(["kreadconfig6","--file","kdeglobals","--group","Icons","--key","Theme"],capture_output=True,text=True,check=False).stdout.strip()
    except OSError: return ""

def delete_theme(theme: IconTheme):
    meta=load_metadata()
    if theme.name not in meta.get("themes",{}) or not theme.path.is_relative_to(USER_ICONS):
        raise PermissionError("Somente temas criados pelo aplicativo podem ser excluídos.")
    if theme.name == active_icon_theme():
        raise PermissionError("Este tema está ativo no Plasma. Aplique outro tema antes de excluí-lo.")
    if theme.path.exists(): shutil.rmtree(theme.path)
    meta.get("themes",{}).pop(theme.name,None); save_metadata(meta)

def icon_files(theme: IconTheme, query=""):
    q=query.lower(); seen=set()
    for directory in theme.directories or ["apps/scalable"]:
        base=theme.path/directory
        if not base.is_dir(): continue
        try:
            for p in base.rglob("*"):
                if p.is_file() and p.suffix.lower() in {".svg",".svgz",".png"} and p.name.lower() not in seen and (not q or q in p.stem.lower()):
                    seen.add(p.name.lower()); yield p
        except OSError: continue

def override_for(theme, icon_name, source: Path):
    if Path(icon_name).is_absolute(): raise ValueError("Ícones com caminho absoluto não usam a resolução de temas.")
    filename=Path(icon_name).name
    if not filename.lower().endswith((".svg",".svgz",".png")): filename += ".svg"
    dest=theme.path/"apps/scalable"/filename; dest.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(source, dest); os.utime(dest.parent,None); os.utime(theme.path,None); return dest

def remove_override(theme, icon_name):
    stem=Path(icon_name).stem
    removed=False
    for p in (theme.path/"apps/scalable").glob(stem+".*"):
        if p.is_file() and p.suffix.lower() in {".svg",".svgz",".png"}:
            p.unlink(); removed=True
    if removed: os.utime(theme.path/"apps/scalable",None); os.utime(theme.path,None)
    return removed

def resolve_icon(theme, icon_name, themes=None):
    """Resolve um nome através do tema personalizado e de seus Inherits."""
    if not icon_name or Path(icon_name).is_absolute(): return None
    filename=Path(icon_name).name
    themes = themes or discover_themes()
    by_name={t.name:t for t in themes}
    visited=set()
    def walk(t):
        if not t or t.name in visited: return None
        visited.add(t.name)
        for directory in t.directories or ["apps/scalable"]:
            for candidate in (t.path/directory/filename, t.path/directory/(filename+'.svg')):
                if candidate.is_file(): return candidate
        for parent in t.inherits:
            found=walk(by_name.get(parent))
            if found:return found
        return None
    return walk(theme)
