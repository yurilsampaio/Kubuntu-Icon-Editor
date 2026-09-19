from pathlib import Path
import subprocess
import re
from PySide6.QtCore import Qt, QSize, QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import *
from .theme_service import discover_themes, create_theme, icon_files, override_for, remove_override, resolve_icon, update_inherits, update_theme_name, delete_theme, USER_ICONS
from .application_service import discover_apps, remove_absolute_icon

def refresh_kde_icon_cache():
 try:
  result=subprocess.run(["kbuildsycoca6","--noincremental"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=False)
  if result.returncode != 0: subprocess.run(["kbuildsycoca5","--noincremental"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=False)
 except OSError:
  try: subprocess.run(["kbuildsycoca5","--noincremental"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=False)
  except OSError: pass

def safe_icon(path):
 try:
  if str(path).lower().endswith(('.svg','.svgz')):
   text=Path(path).read_text(encoding='utf-8',errors='ignore')
   ids=set(re.findall(r'id=["\']([^"\']+)',text)); refs=set(re.findall(r'(?:url\(#|href=["\']#)([^)"\']+)',text))
   if refs-ids:return QIcon()
  return QIcon(str(path))
 except (OSError,UnicodeError): return QIcon()

class MainWindow(QMainWindow):
 def __init__(self):
  super().__init__(); self.setWindowTitle("Icon Theme Studio"); self.resize(1100,700); self.themes=[]; self.current=None; self.build(); self.refresh()
 def build(self):
  c=QWidget(); self.setCentralWidget(c); root=QVBoxLayout(c); top=QHBoxLayout(); self.theme_combo=QComboBox(); new=QPushButton("+ Criar tema"); edit=QPushButton("Editar tema"); edit_inh=QPushButton("Editar herança"); self.delete_btn=QPushButton("Excluir tema"); self.apply_btn=QPushButton("Aplicar tema"); restart=QPushButton("Reiniciar Plasma"); top.addWidget(QLabel("Tema:")); top.addWidget(self.theme_combo,1); top.addWidget(new); top.addWidget(edit); top.addWidget(edit_inh); top.addWidget(self.delete_btn); top.addWidget(self.apply_btn); top.addWidget(restart); root.addLayout(top); self.inherits=QLabel(); self.inherits.setFixedHeight(28); self.inherits.setAlignment(Qt.AlignVCenter|Qt.AlignLeft); self.inherits.setStyleSheet("padding:4px"); root.addWidget(self.inherits)
  sp=QSplitter(); left=QWidget(); ll=QVBoxLayout(left); self.search=QLineEdit(); self.search.setPlaceholderText("Pesquisar aplicativos..."); self.show_hidden=QCheckBox("Mostrar ocultos"); self.app_list=QListWidget(); self.app_list.setViewMode(QListWidget.IconMode); self.app_list.setIconSize(QSize(48,48)); self.app_list.setGridSize(QSize(150,88)); ll.addWidget(self.search); ll.addWidget(self.show_hidden); ll.addWidget(self.app_list); right=QWidget(); rl=QVBoxLayout(right); self.detail=QLabel("Selecione um aplicativo"); self.detail.setWordWrap(True); self.preview=QLabel(); self.preview.setFixedSize(96,96); self.preview.setAlignment(Qt.AlignCenter); self.override=QLabel(); change=QPushButton("Alterar ícone"); external=QPushButton("Escolher arquivo..."); self.remove_absolute=QPushButton("Remover caminho absoluto e usar o tema"); self.remove_absolute.setVisible(False); restore=QPushButton("Restaurar padrão"); [rl.addWidget(x) for x in (self.preview,self.detail,self.override,change,external,self.remove_absolute,restore)]; rl.addStretch(); sp.addWidget(left); sp.addWidget(right); root.addWidget(sp)
  self.app_search_btn=QPushButton("Pesquisar"); self.app_status=QLabel(); ll.addWidget(self.app_search_btn); ll.removeWidget(self.app_search_btn); first=ll.takeAt(0); search_row=QHBoxLayout(); search_row.addWidget(self.search); search_row.addWidget(self.app_search_btn); ll.insertLayout(0,search_row); ll.insertWidget(1,self.app_status); self.app_search_btn.clicked.connect(self.load_apps)
  new.clicked.connect(self.create); edit.clicked.connect(self.edit_theme); edit_inh.clicked.connect(self.edit_inherits); self.delete_btn.clicked.connect(self.delete_current_theme); restart.clicked.connect(self.restart_plasma); self.theme_combo.currentIndexChanged.connect(self.theme_changed); self.app_list.currentRowChanged.connect(self.select_app); self.search.textChanged.connect(self.load_apps); self.search.returnPressed.connect(self.load_apps); self.show_hidden.toggled.connect(self.load_apps); change.clicked.connect(self.choose_icon); external.clicked.connect(self.choose_file); self.remove_absolute.clicked.connect(self.normalize_launcher); restore.clicked.connect(self.restore); self.apply_btn.clicked.connect(self.apply)
  self.search.returnPressed.connect(self.load_apps)
  try: self.search.textChanged.disconnect(self.load_apps)
  except (RuntimeError, TypeError): pass
 def refresh(self):
  self.themes=discover_themes(); self.managed=[t for t in self.themes if t.managed]; self.theme_combo.clear(); self.theme_combo.addItems([t.display_name for t in self.managed]); self.current=self.managed[0] if self.managed else None; self.delete_btn.setEnabled(bool(self.current)); self.update_header(); self.load_apps()
 def theme_changed(self,i):
  if 0<=i<len(self.managed): self.current=self.managed[i]; self.delete_btn.setEnabled(bool(self.current)); self.update_header()
 def update_header(self): self.inherits.setText((self.current.display_name if self.current else "Nenhum tema")+"  →  "+"  →  ".join(self.current.inherits if self.current else []))
 def load_apps(self):
  self.app_status.setText("Carregando aplicativos..."); QApplication.processEvents(); self.apps=discover_apps(self.show_hidden.isChecked()); q=self.search.text().casefold(); self.visible_apps=[a for a in self.apps if q in a.name.casefold() or q in a.icon.casefold()]; self.app_list.clear()
  for a in self.visible_apps:
   resolved=resolve_icon(self.current,a.icon,self.themes) if self.current and not a.icon.startswith('/') else None
   item=QListWidgetItem(safe_icon(resolved) if resolved else QIcon.fromTheme(a.icon),a.name); item.setToolTip(f"{a.name}\nÍcone: {a.icon}"); self.app_list.addItem(item)
  self.app_status.setText(f"{len(self.visible_apps)} aplicativos encontrados")
 def selected(self):
  i=self.app_list.currentRow(); return self.visible_apps[i] if 0<=i<len(self.visible_apps) else None
 def select_app(self):
  a=self.selected()
  if not a:return
  self.detail.setText(f"<h2>{a.name}</h2>Nome do ícone: <b>{a.icon}</b><br>Exec: {a.exec}<br>Categorias: {a.categories or '—'}"); self.remove_absolute.setVisible(a.icon.startswith('/') and a.path is not None and str(a.path).startswith(str(Path.home()))); self.override.setText("Caminho absoluto no launcher — o KDE não usa a cadeia de temas." if a.icon.startswith('/') else "Override: "+("sim" if self.current and resolve_icon(self.current,a.icon,self.themes) and resolve_icon(self.current,a.icon,self.themes).parent == self.current.path/'apps/scalable' else "não")); resolved=resolve_icon(self.current,a.icon,self.themes) if self.current else None; self.preview.setPixmap((safe_icon(resolved) if resolved else QIcon.fromTheme(a.icon)).pixmap(64,64))
 def normalize_launcher(self):
  a=self.selected()
  if not a:return
  if QMessageBox.question(self,"Usar o tema de ícones",f"Alterar o launcher do usuário para que {a.name} use a cadeia de temas?\n\nNenhum arquivo do sistema será modificado.") == QMessageBox.Yes:
   try: remove_absolute_icon(a); refresh_kde_icon_cache(); self.load_apps(); self.select_app()
   except (OSError,ValueError,PermissionError) as e: QMessageBox.warning(self,"Não foi possível alterar",str(e))
 def prepare_icon_name(self, app):
  if not app.icon.startswith('/'): return True
  try: remove_absolute_icon(app); refresh_kde_icon_cache(); self.load_apps(); return True
  except (OSError,ValueError,PermissionError) as e: QMessageBox.warning(self,"Não foi possível alterar o launcher",str(e)); return False
 def create(self):
  d=QDialog(self); d.setWindowTitle("Criar tema"); f=QFormLayout(d); name=QLineEdit("Yuri Icons"); desc=QLineEdit("Meu tema personalizado"); choices=self.themes; base=QComboBox(); base.addItems([t.display_name for t in choices]); available=QComboBox(); available.addItems([t.display_name for t in choices]); selected=QListWidget(); selected.setMaximumHeight(120); add=QPushButton("Adicionar fallback"); remove=QPushButton("Remover selecionado"); standard=QPushButton("Usar padrão Kubuntu (Breeze → hicolor)"); row=QHBoxLayout(); row.addWidget(add); row.addWidget(remove); box=QWidget(); box.setLayout(row)
  def add_fallback():
   name_=available.currentText()
   if name_ and name_ != base.currentText() and not any(selected.item(i).text()==name_ for i in range(selected.count())): selected.addItem(name_)
  def remove_fallback():
   if selected.currentRow()>=0: selected.takeItem(selected.currentRow())
  def use_standard():
   # Mantém os fallbacks escolhidos e acrescenta a base padrão do Kubuntu
   # ao final, sem criar duplicatas.
   for standard_name in ("Breeze", "hicolor"):
    index=next((i for i in range(available.count()) if available.itemText(i).casefold()==standard_name.casefold()),-1)
    if index>=0:
     display_name=available.itemText(index)
     if not any(selected.item(i).text().casefold()==display_name.casefold() for i in range(selected.count()) ) and display_name.casefold()!=base.currentText().casefold():
      selected.addItem(display_name)
  add.clicked.connect(add_fallback); remove.clicked.connect(remove_fallback); standard.clicked.connect(use_standard)
  f.addRow("Nome:",name); f.addRow("Descrição:",desc); f.addRow("Tema base:",base); f.addRow("Fallbacks disponíveis:",available); f.addRow("Fallbacks selecionados:",selected); f.addRow("",box); f.addRow("",standard); b=QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel); f.addWidget(b); b.accepted.connect(d.accept); b.rejected.connect(d.reject)
  if d.exec():
   base_name=choices[base.currentIndex()].name if base.currentIndex()>=0 else "hicolor"; fallback_names=[next(t.name for t in choices if t.display_name==selected.item(i).text()) for i in range(selected.count())]; create_theme(name.text(),desc.text(),[base_name]+fallback_names); self.refresh()
 def edit_inherits(self):
  if not self.current:return
  d=QDialog(self); d.setWindowTitle("Editar herança"); f=QFormLayout(d); base=QComboBox(); choices=[t for t in self.themes if t.name!=self.current.name]; base.addItems([t.display_name for t in choices]); current_base=self.current.inherits[0] if self.current.inherits else ""
  for i,t in enumerate(choices):
   if t.name==current_base: base.setCurrentIndex(i)
  available=QComboBox(); available.addItems([t.display_name for t in choices]); selected=QListWidget(); selected.setMaximumHeight(120)
  for name in self.current.inherits[1:]:
   match=next((t for t in choices if t.name==name),None)
   if match: selected.addItem(match.display_name)
  add=QPushButton("Adicionar fallback"); remove=QPushButton("Remover selecionado"); row=QHBoxLayout(); row.addWidget(add); row.addWidget(remove); box=QWidget(); box.setLayout(row)
  def add_fallback():
   name=available.currentText()
   if name and not any(selected.item(i).text()==name for i in range(selected.count())): selected.addItem(name)
  def remove_fallback():
   if selected.currentRow()>=0: selected.takeItem(selected.currentRow())
  add.clicked.connect(add_fallback); remove.clicked.connect(remove_fallback)
  f.addRow("Tema base:",base); f.addRow("Fallbacks disponíveis:",available); f.addRow("Fallbacks selecionados:",selected); f.addRow("",box); b=QDialogButtonBox(QDialogButtonBox.Save|QDialogButtonBox.Cancel); f.addWidget(b); b.accepted.connect(d.accept); b.rejected.connect(d.reject)
  if d.exec():
   try:
    base_name=choices[base.currentIndex()].name if base.currentIndex()>=0 else ""; fallback_names=[next(t.name for t in choices if t.display_name==selected.item(i).text()) for i in range(selected.count())]; self.current=update_inherits(self.current,[base_name]+fallback_names); self.update_header(); self.themes=discover_themes(); self.load_apps()
   except (OSError,ValueError,PermissionError) as e: QMessageBox.warning(self,"Não foi possível salvar",str(e))
 def edit_theme(self):
  if not self.current:return
  d=QDialog(self); d.setWindowTitle("Editar tema"); f=QFormLayout(d); name=QLineEdit(self.current.display_name); desc=QLineEdit(self.current.path.joinpath("index.theme").read_text(encoding="utf-8",errors="ignore").split("Comment=",1)[-1].splitlines()[0] if "Comment=" in self.current.path.joinpath("index.theme").read_text(encoding="utf-8",errors="ignore") else ""); f.addRow("Nome:",name); f.addRow("Descrição:",desc); b=QDialogButtonBox(QDialogButtonBox.Save|QDialogButtonBox.Cancel); f.addWidget(b); b.accepted.connect(d.accept); b.rejected.connect(d.reject)
  if d.exec():
   try: self.current=update_theme_name(self.current,name.text(),desc.text()); self.refresh()
   except (OSError,ValueError,PermissionError) as e: QMessageBox.warning(self,"Não foi possível salvar",str(e))
 def delete_current_theme(self):
  if not self.current:return
  if QMessageBox.question(self,"Excluir tema",f"Excluir permanentemente o tema {self.current.display_name}?\n\nOs arquivos deste tema serão removidos. Temas externos não serão alterados.") != QMessageBox.Yes:return
  try: delete_theme(self.current); self.refresh()
  except (OSError,ValueError,PermissionError) as e: QMessageBox.warning(self,"Não foi possível excluir",str(e))
 def restart_plasma(self):
  if QMessageBox.question(self,"Reiniciar Plasma","A barra e o menu desaparecerão por alguns segundos. Continuar?") != QMessageBox.Yes:return
  try:
   subprocess.run(["systemctl","--user","restart","plasma-plasmashell.service"],check=True)
  except (OSError,subprocess.CalledProcessError) as e: QMessageBox.warning(self,"Não foi possível reiniciar o Plasma",str(e))
 def choose_icon(self):
  a=self.selected()
  if not a or not self.current or not self.prepare_icon_name(a):return
  d=QDialog(self); d.setWindowTitle("Navegador de ícones"); d.resize(900,650); l=QVBoxLayout(d); theme=QComboBox(); theme.addItem("Todos os temas"); theme.addItems([t.display_name for t in self.themes]); theme.setCurrentIndex(0); row=QHBoxLayout(); search=QLineEdit(); search.setText(Path(a.icon).stem if a.icon else ""); search.setPlaceholderText("Pesquisar nome técnico"); find=QPushButton("Pesquisar"); row.addWidget(search,1); row.addWidget(find); grid=QListWidget(); grid.setViewMode(QListWidget.IconMode); grid.setIconSize(QSize(56,56)); grid.setGridSize(QSize(145,105)); use_btn=QPushButton("Usar este ícone"); status=QLabel("Carregando ícones..."); pages=QHBoxLayout(); previous=QPushButton("‹ Anterior"); next_=QPushButton("Próxima ›"); pages.addWidget(previous); pages.addStretch(); pages.addWidget(status); pages.addStretch(); pages.addWidget(next_); l.addWidget(QLabel("Pacote de ícones:")); l.addWidget(theme); l.addLayout(row); l.addWidget(status); l.addWidget(grid,1); l.addLayout(pages); l.addWidget(use_btn); files=[]; all_files=[]; page=0; page_size=100
  def fill(reset=True):
   nonlocal page,all_files
   if reset: page=0
   status.setText("Carregando ícones..."); QApplication.processEvents(); grid.clear(); files.clear(); query=search.text();
   if theme.currentIndex()==0:
    all_files=[]
    for t in self.themes:
     all_files.extend(icon_files(t,query))
   else:
    t=self.themes[theme.currentIndex()-1]; all_files=list(icon_files(t,query))
   start=page*page_size
   for p in all_files[start:start+page_size]: files.append(p); grid.addItem(QListWidgetItem(safe_icon(p),p.stem))
   status.setText(f"{len(all_files)} ícones encontrados — página {page+1} de {max(1,(len(all_files)+page_size-1)//page_size)}"); previous.setEnabled(page>0); next_.setEnabled((page+1)*page_size<len(all_files))
  theme.currentIndexChanged.connect(lambda: fill()); find.clicked.connect(lambda: fill()); search.returnPressed.connect(fill); d.show(); QTimer.singleShot(50, fill)
  def prev_page():
   nonlocal page
   if page>0: page-=1; fill(False)
  def next_page():
   nonlocal page
   if (page+1)*page_size<len(all_files): page+=1; fill(False)
  previous.clicked.connect(prev_page); next_.clicked.connect(next_page)
  def choose():
   if grid.currentRow()>=0: override_for(self.current,a.icon,files[grid.currentRow()]); d.accept()
  grid.itemDoubleClicked.connect(lambda _: choose()); use_btn.clicked.connect(choose); d.exec(); refresh_kde_icon_cache(); self.load_apps(); self.select_app()
 def choose_file(self):
  a=self.selected()
  if not a or not self.current or not self.prepare_icon_name(a):return
  p,_=QFileDialog.getOpenFileName(self,"Escolher arquivo de ícone",str(Path.home()),"Ícones (*.svg *.svgz *.png)")
  if p:
   try: override_for(self.current,a.icon,Path(p)); refresh_kde_icon_cache(); self.load_apps(); self.select_app()
   except Exception as e: QMessageBox.warning(self,"Não foi possível criar override",str(e))
 def restore(self):
  a=self.selected()
  if a and self.current and remove_override(self.current,a.icon): refresh_kde_icon_cache(); self.load_apps(); self.select_app()
 def apply(self):
  if not self.current:return
  try:
   subprocess.run(["kwriteconfig6","--file","kdeglobals","--group","Icons","--key","Theme",self.current.name],check=True)
   refresh_kde_icon_cache()
   QMessageBox.information(self,"Tema aplicado",f"O Plasma foi configurado para usar {self.current.display_name}. Menus já abertos podem precisar ser reabertos.")
  except (OSError,subprocess.CalledProcessError): QMessageBox.warning(self,"Não foi possível aplicar automaticamente","Selecione o tema em Configurações do Sistema → Cores e temas → Ícones.")
def main():
 app=QApplication.instance() or QApplication([]); app.setApplicationName("Icon Theme Studio"); app.setDesktopFileName("icon-theme-studio"); app.setWindowIcon(QIcon(str(Path(__file__).with_name("icon.svg")))); w=MainWindow(); w.show(); app.exec()
