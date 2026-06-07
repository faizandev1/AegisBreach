import sys
from PyQt5.QtWidgets import QApplication
from gui.main_window import AegisMainWindow

def main():
    app = QApplication(sys.argv)
    window = AegisMainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()