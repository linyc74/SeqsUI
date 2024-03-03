Install PyInstaller

```PowerShell
pip install PyInstaller
```

Package as a .exe file

```PowerShell
$VERSION = "v0.0.0"
pyinstaller --clean --onefile --icon="icon/logo.ico" --add-data="icon;icon" SeqsUI.py
Move-Item -Path "dist\SeqsUI.exe" -Destination "SeqsUI-win-$VERSION.exe"
rm -r build ; rm -r dist ; rm SeqsUI.spec
```

Package as a folder

```PowerShell
$VERSION = "v0.0.0"
pyinstaller --clean --icon="icon/logo.ico" --add-data="icon;icon" SeqsUI.py
Move-Item -Path "dist\SeqsUI.exe" -Destination "SeqsUI.exe"
Compress-Archive -Path "SeqsUI" -DestinationPath "SeqsUI-win-$VERSION.zip"
rm -r build ; rm -r dist ; rm -r SeqsUI ; rm SeqsUI.spec
```
