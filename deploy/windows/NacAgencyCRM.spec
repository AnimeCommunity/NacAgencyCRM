from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_submodules


repo_root = Path(SPECPATH).parents[1]
backend_root = repo_root / "CRM"
frontend_root = repo_root / "frontendcrm" / "out"
version_info = repo_root / "deploy" / "windows" / "version-info.txt"

first_party_apps = [
    "clientes",
    "cotizaciones",
    "interacciones",
    "marketing",
    "proyectos",
    "users",
]

hiddenimports = []
for app in first_party_apps:
    hiddenimports += collect_submodules(app)

for module in [
    "django.contrib.admin.migrations",
    "django.contrib.auth.migrations",
    "django.contrib.contenttypes.migrations",
    "django.contrib.sessions.migrations",
    "rest_framework_simplejwt.token_blacklist",
    "waitress",
]:
    hiddenimports += collect_submodules(module)

hiddenimports += [
    "CRM.settings",
    "CRM.urls",
    "CRM.wsgi",
    "django.db.backends.sqlite3",
    "django.core.mail.backends.smtp",
    "django.core.management.commands.migrate",
    "django.contrib.auth.management.commands.createsuperuser",
    "django.core.management.commands.check",
    "rest_framework.permissions",
    "rest_framework.renderers",
    "rest_framework_simplejwt.authentication",
]

datas = [(str(frontend_root), "frontend")]
for package in ["django", "rest_framework", "rest_framework_simplejwt", "tzdata"]:
    datas += collect_data_files(package)

a = Analysis(
    [str(backend_root / "windows_runtime.py")],
    pathex=[str(backend_root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["gunicorn", "psycopg2"],
    noarchive=False,
    optimize=0,
)

# El hook de Django detecta DATABASES y puede intentar copiar la base usada
# durante el build. Ningún dato de desarrollo debe formar parte del paquete.
def is_forbidden_data(entry):
    name = Path(entry[0]).name.lower()
    return (
        name == "secrets.json"
        or name.startswith(".env")
        or name.endswith((".sqlite", ".sqlite3", ".db"))
    )


a.datas = [entry for entry in a.datas if not is_forbidden_data(entry)]
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="NacAgencyCRM",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    version=str(version_info),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="NacAgencyCRM",
)
