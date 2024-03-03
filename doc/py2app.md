Install `py2app`.

```zsh
pip install py2app
```

Create `setup.py`.
`py2app` does not handle dependency very well.
The `cffi` python package needs to be added manually.

```zsh
py2applet \
  --packages=cffi \
  --iconfile=./icon/logo.ico \
  --make-setup ./SeqsUI.py
```

Build the app.

```zsh
python setup.py py2app
```

This x86_64 version of `libffi.8.dylib` was acquired from Anaconda.
It needs to be copied to the app bundle.

```zsh
cp ./lib/libffi.8.dylib ./dist/SeqsUI.app/Contents/Frameworks/
```

Run the app from the command line. It can also be run by double clicking the app.

```zsh
dist/SeqsUI.app/Contents/MacOS/SeqsUI
```

Zip the app.

```zsh
mv ./dist/SeqsUI.app ./ && zip -r SeqsUI-mac-v0.0.0.zip SeqsUI.app
```

Remove unused build files.

```zsh
rm -r build
rm -r dist
rm setup.py
```


