# -*- mode: python -*-

block_cipher = None

added_files = [
         ( '../dist/collector.bin', './collector/' ),
         ( '../dist/audit_host.bin', './host/' ),
         ( '../dist/audit_admin.bin', './admin/' ),
         ( '../dist/audit_xr.bin', './xr/' ),
         ( '../cron/audit_xr.cron', './xr/' ),
         ( '../cron/audit_admin.cron', './admin/' ),
         ( '../cron/audit_host.cron', './host/' ),
         ( '../cron/audit_collector.cron', './collector/' ),
         ( '../userfiles/id_rsa_server', './userfiles' ),
         ( '../userfiles/compliance.cfg.yml', './userfiles' ),
         ( '../userfiles/auditor.cfg.yml', './userfiles' ),
         ( '../userfiles/compliance.xsd', './userfiles' )
         ]
a = Analysis(['../core/auditor.py'],
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
          name='auditor',
          debug=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=True )
