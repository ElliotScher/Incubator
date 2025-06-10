pyinstaller main.py \
            --add-data "util/calibration/test_calibration.json:util/calibration" \
            --onefile \
            --windowed \
            --hidden-import=tkinter \
            --hidden-import=matplotlib.backends.backend_tkagg \
            --hidden-import=PIL._tkinter_finder \
            --noconfirm