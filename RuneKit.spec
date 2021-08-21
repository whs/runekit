# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(['main.py'],
             pathex=['runekit'],
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=[],
             hooksconfig={},
             runtime_hooks=[],
             excludes=['tkinter'],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=True)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

exe = EXE(pyz,
          a.scripts, 
          [],
          exclude_binaries=True,
          name='RuneKitApp',
          debug=False,
          bootloader_ignore_signals=False,
          strip=True,
          upx=False,
          console=False,
          disable_windowed_traceback=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas, 
               strip=True,
               upx=False,
               upx_exclude=[],
               name='RuneKit')
app = BUNDLE(coll,
             name='RuneKit.app',
             icon=None,
             bundle_identifier='de.cupco.runekit',
             info_plist={
                 'LSEnvironment': {
                     'LANG': 'en_US.UTF-8',
                     'LC_CTYPE': 'en_US.UTF-8'
                 }
             })
