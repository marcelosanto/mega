# loteria-gerador.spec

# -*- mode: python ; coding: utf-8 -*-

# Lista de bibliotecas essenciais do sistema que NÃO devem ser empacotadas.
# Isso força o aplicativo a usar as versões do sistema do usuário, resolvendo conflitos.
EXCLUDED_LIBS = [
    'libstdc++.so.6',
    'libgcc_s.so.1',
    'libssl.so.3',
    'libcrypto.so.3',
]

a = Analysis(
    ['src/main.py'],
    pathex=['src'],
    binaries=[],
    datas=[('src/assets', 'assets')],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# Filtra a lista de binários, removendo as bibliotecas que queremos excluir
filtered_binaries = TOC([
    (name, path, typecode)
    for name, path, typecode in a.binaries
    if not any(excluded_lib in name for excluded_lib in EXCLUDED_LIBS)
])

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    filtered_binaries,
    a.zipfiles,
    a.datas,
    [],
    name='loteria-gerador',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# A seção COLLECT foi removida pois não é necessária para um build --onefile
# e estava causando o erro de empacotamento.