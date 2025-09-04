import csv
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QTabWidget, QFormLayout, QVBoxLayout, QHBoxLayout,
    QLineEdit, QDateEdit, QDoubleSpinBox, QComboBox, QPushButton, QLabel, QTableWidget,
    QTableWidgetItem, QFileDialog, QMessageBox, QHeaderView, QGroupBox, QGridLayout,
    QAbstractItemView
)
from PySide6.QtCore import Qt, QDate
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

import database as db
from utils import qdate_to_iso

class ChartCanvas(FigureCanvas):
    def __init__(self, parent=None):
        fig = Figure(figsize=(6,4))
        super().__init__(fig)
        self.ax = self.figure.add_subplot(111)
        self.setParent(parent)

    def plot_grouped(self, rows, title):
        self.ax.clear()
        labels = [r[0] for r in rows]
        gelir = [r[1] for r in rows]
        gider = [r[2] for r in rows]
        kar = [r[3] for r in rows]
       
        self.ax.plot(labels, gelir, marker="o", label="Gelir")
        self.ax.plot(labels, gider, marker="o", label="Gider")
        self.ax.plot(labels, kar,   marker="o", label="Kâr")
       
        self.ax.set_title(title)
        self.ax.set_xlabel("Dönem")
        self.ax.set_ylabel("Tutar")
        self.ax.legend()
        self.ax.grid(True, linestyle="--", alpha=0.4)
        self.figure.tight_layout()
        self.draw()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Finans Takip (Kâr-Zarar)")
        self.resize(1100, 700)
        db.init_db()
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self._init_tab_entry()
        self._init_tab_list()
        self._init_tab_reports()
        
    def _init_tab_entry(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        form = QFormLayout()
        self.date_input = QDateEdit(calendarPopup=True)
        self.date_input.setDate(QDate.currentDate())
        self.shop_input = QLineEdit()
        self.type_input = QComboBox()
        self.type_input.addItems(["gelir", "gider"])
        self.amount_input = QDoubleSpinBox()
        self.amount_input.setMaximum(1_000_000_000)
        self.amount_input.setDecimals(2)
        self.amount_input.setSingleStep(10.0)
        self.note_input = QLineEdit()
        form.addRow("Tarih:", self.date_input)
        form.addRow("Dükkân:", self.shop_input)
        form.addRow("Tür:", self.type_input)
        form.addRow("Tutar:", self.amount_input)
        form.addRow("Not:", self.note_input)
        save_btn = QPushButton("Kaydet")
        save_btn.clicked.connect(self.save_transaction)
        layout.addLayout(form)
        layout.addWidget(save_btn)
        w.setLayout(layout)
        self.tabs.addTab(w, "Kayıt Ekle")

    def save_transaction(self):
        date_iso = qdate_to_iso(self.date_input.date())
        shop = self.shop_input.text().strip()
        ttype = self.type_input.currentText()
        amount = float(self.amount_input.value())
        note = self.note_input.text().strip()
        if not shop:
            QMessageBox.warning(self, "Uyarı", "Dükkân ismi boş olamaz.")
            return
        if amount <= 0:
            QMessageBox.warning(self, "Uyarı", "Tutar 0'dan büyük olmalı.")
            return
        amount = -abs(amount) if ttype.lower() == "gider" else abs(amount)
        db.add_transaction(date_iso, shop, ttype, amount, note)
        QMessageBox.information(self, "Başarılı", "Kayıt eklendi.")
        self.shop_input.clear()
        self.amount_input.setValue(0)
        self.note_input.clear()
        self.refresh_table()

    # TAB 2
    def _init_tab_list(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["ID", "Tarih", "Dükkân", "Tür", "Tutar", "Not"])
        layout.addWidget(self.table)
        w.setLayout(layout)
        self.tabs.addTab(w, "Kayıtlar")

    def refresh_table(self):
        self.table.setRowCount(0)
        rows = db.fetch_transactions("2020-01-01", "2030-01-01", None)
        for r in rows:
            row = self.table.rowCount()
            self.table.insertRow(row)
            for col, val in enumerate(r):
                self.table.setItem(row, col, QTableWidgetItem(str(val)))

    # TAB 3
    def _init_tab_reports(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        self.chart = ChartCanvas()
        layout.addWidget(self.chart)
        w.setLayout(layout)
        self.tabs.addTab(w, "Raporlar")

    def draw_chart(self):
        rows = db.group_by("ay", "2020-01-01", "2030-01-01")
        self.chart.plot_grouped(rows, "Örnek Grafik")


def main():
    app = QApplication([])
    win = MainWindow()
    win.show()
    app.exec()

if __name__ == "__main__":
    main()
