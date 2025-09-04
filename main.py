import csv
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QTabWidget, QFormLayout, QVBoxLayout, QHBoxLayout,
    QLineEdit, QDateEdit, QDoubleSpinBox, QComboBox, QPushButton, QLabel, QTableWidget,
    QTableWidgetItem, QFileDialog, QMessageBox, QHeaderView, QGroupBox, QGridLayout
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
        # Basit üç çizgi
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

    # --------------- TAB 1: KAYIT EKLE ----------------
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
            layout.addWidget(save_btn, alignment=Qt.AlignLeft)
            layout.addStretch(1)

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

        # Kategoriye göre tutarı negatif yap
        if ttype.lower() == "gider":
            amount = -abs(amount)
        else:
            amount = abs(amount)

            db.add_transaction(date_iso, shop, ttype, amount, note)
            QMessageBox.information(self, "Başarılı", "Kayıt eklendi.")
            self.shop_input.clear()
            self.amount_input.setValue(0.0)
            self.note_input.clear()
            self.refresh_table()
            self.refresh_summary()


    # --------------- TAB 2: KAYITLAR ----------------
        def _init_tab_list(self):
            w = QWidget()
            outer = QVBoxLayout(w)

        # Filtre kutusu
            filter_box = QGroupBox("Filtre")
            grid = QGridLayout(filter_box)

            self.start_date = QDateEdit(calendarPopup=True)
            self.end_date = QDateEdit(calendarPopup=True)
            self.start_date.setDate(QDate.currentDate().addMonths(-1))
            self.end_date.setDate(QDate.currentDate())

            self.filter_type = QComboBox()
            self.filter_type.addItems(["hepsi", "gelir", "gider"])

            apply_btn = QPushButton("Uygula")
            apply_btn.clicked.connect(self.refresh_table)

            export_btn = QPushButton("CSV'ye Aktar")
            export_btn.clicked.connect(self.export_csv)

            delete_btn = QPushButton("Seçili Kaydı Sil")
            delete_btn.clicked.connect(self.delete_selected)

            grid.addWidget(QLabel("Başlangıç:"), 0, 0)
            grid.addWidget(self.start_date, 0, 1)
            grid.addWidget(QLabel("Bitiş:"), 0, 2)
            grid.addWidget(self.end_date, 0, 3)
            grid.addWidget(QLabel("Tür:"), 0, 4)
            grid.addWidget(self.filter_type, 0, 5)
            grid.addWidget(apply_btn, 0, 6)
            grid.addWidget(export_btn, 0, 7)
            grid.addWidget(delete_btn, 0, 8)

        # Tablo
            self.table = QTableWidget(0, 6)
            self.table.setHorizontalHeaderLabels(["ID", "Tarih", "Dükkân", "Tür", "Tutar", "Not"])
            self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        from PySide6.QtWidgets import QAbstractItemView

        # Satır bazlı seçim
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)

        # Tek satır seçilebilsin
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)

        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        # Özet
        self.summary_label = QLabel("Toplamlar: Gelir 0 | Gider 0 | Kâr 0")

        outer.addWidget(filter_box)
        outer.addWidget(self.table)
        outer.addWidget(self.summary_label)

        self.tabs.addTab(w, "Kayıtlar")
        self.refresh_table()
        self.refresh_summary()

        def current_filters(self):
            start = qdate_to_iso(self.start_date.date())
            end = qdate_to_iso(self.end_date.date())
            t = self.filter_type.currentText()
            t = None if t == "hepsi" else t
            return start, end, t

        def refresh_table(self):
            start, end, t = self.current_filters()
            rows = db.fetch_transactions(start, end, t)
            self.table.setRowCount(0)
            for r in rows:
                row = self.table.rowCount()
                self.table.insertRow(row)
                for col, val in enumerate(r):
                    if col == 4:  # Tutar sütunu
                        tutar = float(val)
                        tip = "Gider" if tutar < 0 else "Gelir"
                        display_val = f"{abs(tutar):.2f} ({tip})"
                        item = QTableWidgetItem(display_val)
                        item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    else:
                        item = QTableWidgetItem(str(val))
                    if col == 0:  # ID sağa hizalı
                        item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                        self.table.setItem(row, col, item)


        def refresh_summary(self):
            start, end, t = self.current_filters()
            s = db.summarize(start, end)
            self.summary_label.setText(f"Toplamlar: Gelir {s['gelir']:.2f} | Gider {s['gider']:.2f} | Kâr {s['kar']:.2f}")

        def export_csv(self):
            path, _ = QFileDialog.getSaveFileName(self, "CSV'ye aktar", "kayitlar.csv", "CSV (*.csv)")
        if not path:
            return
            start, end, t = self.current_filters()
            rows = db.fetch_transactions(start, end, t)
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["ID", "Tarih", "Dükkân", "Tür", "Tutar", "Not"])
            for r in rows:
                writer.writerow(r)
                QMessageBox.information(self, "Bilgi", "CSV çıktısı oluşturuldu.")

        def delete_selected(self):
            row = self.table.currentRow()
            if row < 0:
                QMessageBox.warning(self, "Uyarı", "Silmek için bir satır seçin.")
                return
            tx_id_item = self.table.item(row, 0)
            if not tx_id_item:
                return
            tx_id = int(tx_id_item.text())
            ok = QMessageBox.question(self, "Onay", f"ID {tx_id} kaydını silmek istiyor musunuz?")
            if ok == QMessageBox.StandardButton.Yes:
                db.delete_transaction(tx_id)
                self.refresh_table()
                self.refresh_summary()

    # --------------- TAB 3: RAPORLAR ----------------
    def _init_tab_reports(self):
        w = QWidget()
        layout = QVBoxLayout(w)

        # Kontroller
        ctrl_box = QGroupBox("Rapor Ayarları")
        grid = QGridLayout(ctrl_box)

        self.rep_start = QDateEdit(calendarPopup=True)
        self.rep_end = QDateEdit(calendarPopup=True)
        self.rep_start.setDate(QDate.currentDate().addMonths(-6))
        self.rep_end.setDate(QDate.currentDate())

        self.period_combo = QComboBox()
        self.period_combo.addItems(["ay", "hafta"])

        draw_btn = QPushButton("Grafik Oluştur")
        draw_btn.clicked.connect(self.draw_chart)

        grid.addWidget(QLabel("Başlangıç:"), 0, 0)
        grid.addWidget(self.rep_start, 0, 1)
        grid.addWidget(QLabel("Bitiş:"), 0, 2)
        grid.addWidget(self.rep_end, 0, 3)
        grid.addWidget(QLabel("Dönem:"), 0, 4)
        grid.addWidget(self.period_combo, 0, 5)
        grid.addWidget(draw_btn, 0, 6)

        self.chart = ChartCanvas()

        layout.addWidget(ctrl_box)
        layout.addWidget(self.chart)

        self.tabs.addTab(w, "Raporlar")

    def draw_chart(self):
        start = qdate_to_iso(self.rep_start.date())
        end = qdate_to_iso(self.rep_end.date())
        period = self.period_combo.currentText()
        rows = db.group_by(period, start, end)
        if not rows:
            QMessageBox.information(self, "Bilgi", "Bu aralıkta veri yok.")
            return
        title = f"{period.title()} Bazında Gelir-Gider-Kâr"
        self.chart.plot_grouped(rows, title)

def main():
    app = QApplication([])
    win = MainWindow()
    win.show()
    app.exec()

if __name__ == "__main__":
    main()
