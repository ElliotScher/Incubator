pyinstaller \
  --add-binary "/usr/lib/aarch64-linux-gnu/libpython3.12.so.1.0:." \
  --add-data "util/calibration/test_calibration.json:util/calibration" \
  --onefile \
  --windowed \
  --hidden-import=tkinter \
  --hidden-import=matplotlib.backends.backend_tkagg \
  --hidden-import=PIL._tkinter_finder \
  --noconfirm \
  main.py
