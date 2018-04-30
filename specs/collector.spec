# -*- mode: python -*-

block_cipher = None

added_files = [
         ( '../userfiles/id_rsa_server', './userfiles' ),
         ( '../userfiles/compliance.cfg.yml', './userfiles' ),
         ( '../userfiles/server.cfg.yml', './userfiles' ),
         ( '../userfiles/auditor.cfg.yml', './userfiles' ),
         ( '../userfiles/compliance.xsd', './userfiles' )
         ]
a = Analysis(['../core/collector.py'],
             pathex=['/home/cisco/audit_xr_linux/specs'],
             binaries=[],
             datas=added_files,
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='collector.bin',
          debug=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=True )
