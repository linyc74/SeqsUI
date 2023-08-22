```PowerShell
pip install PyInstaller

pyinstaller --icon="icon/logo.ico" --add-data="icon;icon" SeqsUI.py

rm -r build
rm -r dist
rm SeqsUI.spec
```
