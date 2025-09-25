from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QTabWidget, QFormLayout, QVBoxLayout,
    QHBoxLayout, QLineEdit, QDateEdit, QDoubleSpinBox, QComboBox,
    QPushButton, QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QSpinBox,
    QMenu, QMessageBox
)
from PySide6.QtGui import QAction

from PySide6.QtWidgets import QMenu, QMessageBox
from PySide6.QtCore import Qt, QDate
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import database as db
from datetime import datetime, timedelta
from utils import qdate_to_iso
import pandas as pd
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta



# -------------------- Chart Canvas --------------------
class ChartCanvas(FigureCanvas):
    def __init__(self, parent=None):
        fig = Figure(figsize=(8,5))
        super().__init__(fig)
        self.ax = self.figure.add_subplot(111)
        self.setParent(parent)

    def plot_grouped(self, rows, title):
        self.ax.clear()
        labels = [r[0] for r in rows]
        gelir = [r[1] for r in rows]
        gider = [r[2] for r in rows]
        kar = [r[3] for r in rows]

        self.ax.plot(labels, gelir, marker='o', color='#1f77b4', label='Gelir')
        self.ax.plot(labels, gider, marker='s', color='#ff7f0e', label='Gider')
        self.ax.plot(labels, kar, marker='^', color='#2ca02c', label='Kâr')

        self.ax.set_title(title, fontsize=14, fontweight='bold')
        self.ax.set_xlabel('Dönem', fontsize=12)
        self.ax.set_ylabel('Tutar', fontsize=12)
        self.ax.legend()
        self.ax.grid(True, linestyle='--', alpha=0.3)
        self.figure.tight_layout()
        self.draw()

    # 🔥 Yeni bar chart fonksiyonu
    def plot_bar(self, rows, title):
        self.ax.clear()
        labels = [r[0] for r in rows]
        gelir = [r[1] for r in rows]
        gider = [r[2] for r in rows]

        x = range(len(labels))
        bar_width = 0.35

        self.ax.bar([i - bar_width/2 for i in x], gelir, bar_width, color='#1f77b4', label='Gelir')
        self.ax.bar([i + bar_width/2 for i in x], gider, bar_width, color='#ff7f0e', label='Gider')

        self.ax.set_xticks(list(x))
        self.ax.set_xticklabels(labels, rotation=30, ha='right')

        self.ax.set_title(title, fontsize=14, fontweight='bold')
        self.ax.set_xlabel('Dükkan', fontsize=12)
        self.ax.set_ylabel('Tutar', fontsize=12)
        self.ax.legend()
        self.ax.grid(axis='y', linestyle='--', alpha=0.3)
        self.figure.tight_layout()
        self.draw()



# -------------------- Detail Window --------------------
# ...importlar aynı...

class DetailWindow(QWidget):
    def __init__(self, transaction_id):
        super().__init__()
        self.setWindowTitle("Detaylar")
        self.resize(700, 500)
        self.transaction_id = transaction_id

        # Ana layout
        main_layout = QVBoxLayout(self)

        # Tab widget
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # Sekme değişimini yakala
        self.tabs.currentChanged.connect(self.on_tab_changed)


        # ----------------- Mal/Hizmet Sekmesi -----------------
        mal_widget = QWidget()
        mal_layout = QVBoxLayout(mal_widget)

        # Mal/Hizmet tablosu
        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels([
            "Mal","Kasa","Miktar","Birim","Birim Fiyat","KDV %","KDV Tutarı","Mal/Hizmet Tutarı"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # 👇 Hücre düzenlenebilirliği
        self.table.setEditTriggers(QTableWidget.DoubleClicked | QTableWidget.SelectedClicked)
        self.table.itemChanged.connect(self.on_table_item_changed)

        mal_layout.addWidget(self.table)

        # Form alanları
        form_layout = QFormLayout()
        self.mal_input = QLineEdit()
        self.kasa_input = QSpinBox(); self.kasa_input.setMinimum(1); self.kasa_input.setMaximum(1000); self.kasa_input.setValue(1)
        self.miktar_input = QDoubleSpinBox(); self.miktar_input.setDecimals(2); self.miktar_input.setMaximum(1_000_000)
        self.birim_fiyat_input = QDoubleSpinBox(); self.birim_fiyat_input.setDecimals(2); self.birim_fiyat_input.setMaximum(1_000_000)
        form_layout.addRow("Mal:", self.mal_input)
        form_layout.addRow("Kasa:", self.kasa_input)
        form_layout.addRow("Miktar:", self.miktar_input)
        form_layout.addRow("Birim Fiyat:", self.birim_fiyat_input)
        mal_layout.addLayout(form_layout)

        # Ekle butonu
        add_btn = QPushButton("Ekle")
        add_btn.clicked.connect(self.add_row)
        mal_layout.addWidget(add_btn)
        
        #Silme butonu
        delete_btn = QPushButton("Seçili Satırı Sil")
        delete_btn.clicked.connect(self.delete_row)
        mal_layout.addWidget(delete_btn)


        # Toplam label
        self.total_label = QLabel("Toplam: 0,00 TL")
        self.total_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        mal_layout.addWidget(self.total_label)

        self.tabs.addTab(mal_widget, "Mal/Hizmet")

        # ----------------- Masraf Sekmesi -----------------
        masraf_widget = QWidget()
        masraf_layout = QVBoxLayout(masraf_widget)

        # Masraf tablosu
        self.masraf_table = QTableWidget(0, 3)
        self.masraf_table.setHorizontalHeaderLabels(["Komisyon", "Komisyon KDV", "Masraf"])
        self.masraf_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        # Hücre değiştiğinde toplamı ve net yekünü güncelle
        self.table.itemChanged.connect(self.on_table_item_changed)
        self.masraf_table.itemChanged.connect(self.on_masraf_item_changed)
        masraf_layout.addWidget(self.masraf_table)

        # Masraf form
        form_layout2 = QFormLayout()
        self.masraf_komisyon_input = QDoubleSpinBox(); self.masraf_komisyon_input.setDecimals(2); self.masraf_komisyon_input.setMaximum(1_000_000)
        self.masraf_kdv_input = QDoubleSpinBox(); self.masraf_kdv_input.setDecimals(2); self.masraf_kdv_input.setMaximum(1_000_000)
        self.masraf_masraf_input = QDoubleSpinBox(); self.masraf_masraf_input.setDecimals(2); self.masraf_masraf_input.setMaximum(1_000_000)
        form_layout2.addRow("Komisyon:", self.masraf_komisyon_input)
        form_layout2.addRow("Komisyon KDV:", self.masraf_kdv_input)
        form_layout2.addRow("Masraf:", self.masraf_masraf_input)
        masraf_layout.addLayout(form_layout2)

        # Ekle butonu masraf için
        add_masraf_btn = QPushButton("Masraf Ekle")
        add_masraf_btn.clicked.connect(self.add_masraf)
        masraf_layout.addWidget(add_masraf_btn)

        # Masraf toplam ve net yekün
        self.masraf_total_label = QLabel("Masraf Toplamı: 0,00 TL")
        self.masraf_total_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        masraf_layout.addWidget(self.masraf_total_label)

        self.net_yekun_label = QLabel("Net Yekün: 0,00 TL")
        self.net_yekun_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        masraf_layout.addWidget(self.net_yekun_label)

        self.tabs.addTab(masraf_widget, "Masraflar")

        # DB'den yükle
        self.load_details()

        self.setup_context_menus()


    # ----------------- Grafik Sekmesi -----------------
        grafik_widget = QWidget()
        grafik_layout = QVBoxLayout(grafik_widget)

        self.detail_chart = ChartCanvas()
        grafik_layout.addWidget(self.detail_chart)

        self.tabs.addTab(grafik_widget, "Grafikler")

        # ✅ Pencere açılır açılmaz bu dükkanın grafiği çizilsin
        self.show_single_shop_chart()



    # ----------------- Mal/Hizmet ekleme -----------------
    def add_row(self):
        mal = self.mal_input.text().strip()
        kasa = self.kasa_input.value()
        miktar = self.miktar_input.value()
        birim = "kg"
        birim_fiyat = self.birim_fiyat_input.value()
        kdv = 1
        kdv_tutari = miktar * birim_fiyat * kdv / 100
        mal_hizmet_tutari = miktar * birim_fiyat

        if not mal or miktar <= 0 or birim_fiyat <= 0:
            QMessageBox.warning(self,"Uyarı","Mal, miktar ve birim fiyat girilmeli ve 0'dan büyük olmalı!")
            return

        # DB kaydet
        db.add_detail(self.transaction_id, mal, kasa, miktar, birim, birim_fiyat, kdv, kdv_tutari, mal_hizmet_tutari)

        row_index = self.table.rowCount()
        self.table.insertRow(row_index)
        values = [mal, kasa, miktar, birim, birim_fiyat, kdv, kdv_tutari, mal_hizmet_tutari]
        for col_index,val in enumerate(values):
            item = QTableWidgetItem(str(val))
            if col_index in [1,2,4,5,7]:
                item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row_index,col_index,item)

        self.mal_input.clear()
        self.miktar_input.setValue(0)
        self.birim_fiyat_input.setValue(0)
        self.kasa_input.setValue(1)
        self.update_total()

    def update_total(self):
        toplam = 0
        for row in range(self.table.rowCount()):
            val = self.table.item(row, 7)
            if val:
                try: toplam += float(val.text())
                except: pass
        self.total_label.setText(f"Toplam: {toplam:,.2f} TL")
        self.update_net_yekun()
    # ----------------- Masraf ekleme -----------------
    def add_masraf(self):
        kom = self.masraf_komisyon_input.value()
        kdv = self.masraf_kdv_input.value()
        mas = self.masraf_masraf_input.value()

        if kom == 0 and kdv == 0 and mas == 0:
            QMessageBox.warning(self, "Uyarı", "En az bir masraf değeri girmelisiniz!")
            return

        # 1️⃣ DB'ye kaydet
        db.add_masraf(self.transaction_id, kom, kdv, mas)

        # 2️⃣ Tabloya ekle
        row_index = self.masraf_table.rowCount()
        self.masraf_table.insertRow(row_index)
        vals = [kom, kdv, mas]
        for col_index, val in enumerate(vals):
            item = QTableWidgetItem(f"{val:.2f}")
            item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.masraf_table.setItem(row_index, col_index, item)

        # Formu temizle
        self.masraf_komisyon_input.setValue(0)
        self.masraf_kdv_input.setValue(0)
        self.masraf_masraf_input.setValue(0)

        # Masraf toplamını güncelle
        self.update_masraf_total()
    
   
    def on_table_item_changed(self, item):
        try:
            if float(item.text().replace(",", ".")) < 0:
                QMessageBox.warning(self, "Uyarı", "Negatif değer girilemez!")
                item.setText("0")
        except:
            pass
        self.update_total()

    def on_masraf_item_changed(self, item):
        try:
            if float(item.text().replace(",", ".")) < 0:
                QMessageBox.warning(self, "Uyarı", "Negatif değer girilemez!")
                item.setText("0")
        except:
            pass
        self.update_masraf_total()

    def update_masraf_total(self):
        toplam = 0
        for row in range(self.masraf_table.rowCount()):
            for col in range(3):  # komisyon + komisyon_kdv + masraf
                val_item = self.masraf_table.item(row, col)
                toplam += self.safe_float(val_item)  # safe_float string -> float dönüşümü yapar

        # Masraf toplamını TL formatında göster
        self.masraf_total_label.setText(f"Masraf Toplamı: {toplam:,.2f} TL")
        self.update_net_yekun()  # Net yekünü güncelle
    
    # Tabloya sağ tık menüsü ekle
    def setup_context_menus(self):
        # Mal/Hizmet tablosu
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_table_menu)

        # Masraf tablosu
        self.masraf_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.masraf_table.customContextMenuRequested.connect(self.show_masraf_menu)

    # Mal/Hizmet sağ tık menüsü
    def show_table_menu(self, pos):
        menu = QMenu()
        delete_action = QAction("Sil", self)
        delete_action.triggered.connect(self.delete_row)
        menu.addAction(delete_action)
        menu.exec_(self.table.viewport().mapToGlobal(pos))

    # Masraf sağ tık menüsü
    def show_masraf_menu(self, pos):
        menu = QMenu()
        delete_action = QAction("Sil", self)
        delete_action.triggered.connect(self.delete_masraf_row)
        menu.addAction(delete_action)
        menu.exec_(self.masraf_table.viewport().mapToGlobal(pos))

    def delete_row(self):
        selected = self.table.currentRow()
        if selected < 0:
            return
        mal_item = self.table.item(selected, 0)
        if mal_item:
            mal = mal_item.text()
            db.delete_detail(self.transaction_id, mal)  # DB'den sil
            self.table.removeRow(selected)               # Tabloyu güncelle
            self.update_total()                          # Toplamı güncelle

        # Masraf silme
    def delete_masraf_row(self):
        selected = self.masraf_table.currentRow()
        if selected < 0:
            return
        # DB'de id bazlı silme daha güvenli. Eğer tablodaki satırda id yoksa, değer bazlı bir yöntem yap.
        kom = float(self.masraf_table.item(selected, 0).text())
        kdv = float(self.masraf_table.item(selected, 1).text())
        mas = float(self.masraf_table.item(selected, 2).text())

        # DB'den silmek için transaction_id ve değerleri kullan
        db.delete_masraf_by_values(self.transaction_id, kom, kdv, mas)

        self.masraf_table.removeRow(selected)
        self.update_masraf_total()

    
    def draw_detail_chart(self):
        # Önce grafiği temizle
        self.detail_chart.ax.clear()

        # Tek dükkan için veriler
        details = db.fetch_details(self.transaction_id)  # Bu transaction_id tek dükkan için
        if not details:
            return

        mal_list = [r[0] for r in details]           # Mal/Hizmet isimleri
        tutar_list = [r[7] for r in details]         # Mal/Hizmet tutarı

        x = range(len(mal_list))
        self.detail_chart.ax.bar(x, tutar_list, color='#1f77b4')

        # Üstüne tutarları yaz
        for i, val in enumerate(tutar_list):
            self.detail_chart.ax.text(i, val + 0.01*max(tutar_list), f"{val:.2f}", ha='center', va='bottom', fontsize=8)

        self.detail_chart.ax.set_xticks(x)
        self.detail_chart.ax.set_xticklabels(mal_list, rotation=30, ha='right')
        self.detail_chart.ax.set_ylabel("Tutar")
        self.detail_chart.ax.set_title("Dükkan Bazlı Detaylar", fontsize=12, fontweight='bold')
        self.detail_chart.ax.grid(axis='y', linestyle='--', alpha=0.3)
        self.detail_chart.figure.tight_layout()
        self.detail_chart.draw()

    def on_tab_changed(self, index):
        tab_text = self.tabs.tabText(index)
        if tab_text == "Grafikler":
            self.show_single_shop_chart()

    def update_net_yekun(self):
    # Mal/Hizmet toplamını hesapla
        mal_total = 0
        for row in range(self.table.rowCount()):
            val = self.table.item(row, 7)  # Mal/Hizmet Tutarı sütunu
            if val:
                try:
                    mal_total += float(val.text().replace(",", "."))
                except:
                    pass

        # Masraf toplamını tablodan oku
        masraf_total = 0
        for row in range(self.masraf_table.rowCount()):
            for col in range(3):  # Komisyon + Komisyon KDV + Masraf
                val = self.masraf_table.item(row, col)
                if val:
                    try:
                        masraf_total += float(val.text().replace(",", "."))
                    except:
                        pass

        net_yekun = mal_total - masraf_total
        self.net_yekun_label.setText(f"Net Yekün: {net_yekun:,.2f} TL")



    def safe_float(self, item):
        if item is None:
            return 0
        try:
            text = item.text().replace(",", ".")  # Virgülü noktaya çevir
            return float(text)
        except:
            return 0


    def safe_label_float(self, label):
        try:
            text = label.text().split(":")[1].replace("TL","").strip().replace(",",".")
            return float(text)
        except:
            return 0

    def show_single_shop_chart(self):
        # Tek dükkan grafiğini transaction_id üzerinden çiz
        details = db.fetch_details(self.transaction_id)
        if not details:
            return

        mal_list = [r[0] for r in details]
        tutar_list = [r[7] for r in details]

        self.detail_chart.ax.clear()   # <-- BURAYI DÜZELTTİM
        x = range(len(mal_list))
        self.detail_chart.ax.bar(x, tutar_list, color='#1f77b4')

        for i, val in enumerate(tutar_list):
            self.detail_chart.ax.text(i, val + 0.01*max(tutar_list), f"{val:,.2f}", 
                                      ha='center', va='bottom', fontsize=8)

        self.detail_chart.ax.set_xticks(x)
        self.detail_chart.ax.set_xticklabels(mal_list, rotation=30, ha='right')
        self.detail_chart.ax.set_ylabel("Tutar")
        self.detail_chart.ax.set_title("Bu Dükkanın Detay Grafiği", fontsize=12, fontweight='bold')
        self.detail_chart.ax.grid(axis='y', linestyle='--', alpha=0.3)
        self.detail_chart.figure.tight_layout()
        self.detail_chart.draw()

    # ----------------- Detayları yükleme -----------------
    def load_details(self):
        # 1️⃣ Mal/Hizmet detaylarını yükle
        self.table.setRowCount(0)
        rows = db.fetch_details(self.transaction_id)
        for r in rows:
            row_index = self.table.rowCount()
            self.table.insertRow(row_index)
            for col_index, val in enumerate(r):
                item = QTableWidgetItem(str(val))
                if col_index in [1,2,4,5,7]:
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.table.setItem(row_index, col_index, item)

        self.update_total()

        # 2️⃣ Masraf detaylarını DB'den yükle
        self.masraf_table.setRowCount(0)
        masraf_rows = db.fetch_masraflar(self.transaction_id)
        for r in masraf_rows:
            row_index = self.masraf_table.rowCount()
            self.masraf_table.insertRow(row_index)
            for col_index, val in enumerate(r):
                item = QTableWidgetItem(f"{val:.2f}")
                item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.masraf_table.setItem(row_index, col_index, item)

        self.update_masraf_total()
       



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Finans Takip")
        self.resize(1200,700)
        db.init_db()
        self.detail_windows = []

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
        form.addRow("Stok Giriş Tarihi:",self.date_input)

        self.shop_input = QLineEdit()
        form.addRow("Dükkan:",self.shop_input)

        self.type_input = QComboBox()
        self.type_input.addItems(["Gelir","Gider"])
        form.addRow("Tip:",self.type_input)

        self.amount_input = QDoubleSpinBox()
        self.amount_input.setMaximum(1_000_000_000)
        self.amount_input.setDecimals(2)
        form.addRow("Tutar:",self.amount_input)

        self.kasa_input = QSpinBox()
        self.kasa_input.setMinimum(1)
        self.kasa_input.setMaximum(1000)
        self.kasa_input.setValue(1)
        form.addRow("Kasa Sayısı:",self.kasa_input)

        self.note_input = QLineEdit()
        form.addRow("Not:",self.note_input)

        save_btn = QPushButton("Kaydet")
        save_btn.clicked.connect(self.save_transaction)
        layout.addLayout(form)
        layout.addWidget(save_btn)
        w.setLayout(layout)
        self.tabs.addTab(w,"Kayıt Ekle")

    def save_transaction(self):
        date = self.date_input.date().toString("yyyy-MM-dd")
        shop = self.shop_input.text().strip()
        amount = float(self.amount_input.value())
        note = self.note_input.text().strip()
        tipe = self.type_input.currentText()
        kasa_sayisi = self.kasa_input.value()

        if not shop:
            QMessageBox.warning(self,"Uyarı","Dükkan boş olamaz!")
            return
        if amount<=0:
            QMessageBox.warning(self,"Uyarı","Tutar 0'dan büyük olmalı!")
            return
        if tipe=="Gider":
            amount = -abs(amount)

        db.add_transaction(date,shop,amount,note,kasa_sayisi)
        self.shop_input.clear()
        self.amount_input.setValue(0)
        self.note_input.clear()
        self.refresh_table()
        QMessageBox.information(self,"Başarılı","Kayıt eklendi!")

    # MainWindow içinde ekle:

    def setup_context_menu(self):
        # Tabloya sağ tık menüsü ekle
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.open_menu)

    def open_menu(self, pos):
        # pos: QPoint (mouse pozisyonu)
        row = self.table.rowAt(pos.y())
        if row < 0:
            return

        menu = QMenu(self)
        delete_action = menu.addAction("Kaydı Sil")
        action = menu.exec_(self.table.viewport().mapToGlobal(pos))

        if action == delete_action:
            self.delete_selected_row(row)

    def delete_selected_row(self, row=None):
        # Eğer row param gelmediyse, şu anki seçili satırı al
        if row is None:
            row = self.table.currentRow()
        if row < 0:
            return

        # ID hücresinden transaction_id al
        id_item = self.table.item(row, 0)  # ID sütunu 0. sütun
        if id_item is None:
            return

        try:
            transaction_id = int(id_item.text())
        except:
            # veya UserRole ile saklıysa deneyelim
            try:
                transaction_id = int(id_item.data(Qt.UserRole))
            except:
                QMessageBox.warning(self, "Hata", "Geçerli bir kayıt bulunamadı.")
                return

        reply = QMessageBox.question(self, "Onay",
                                     "Bu kaydı (ve ilgili detayları) silmek istediğine emin misin?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply != QMessageBox.Yes:
            return

        # DB'den sil
        try:
            db.delete_transaction(transaction_id)
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Silme sırasında hata: {e}")
            return

        # Tabloyu güncelle (satırı kaldır veya tüm tabloyu yenile)
        # Daha sağlam yaklaşım: tüm tabloyu yeniden yükle
        self.refresh_table()


    def _init_tab_list(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        self.table = QTableWidget(0,7)
        self.table.setHorizontalHeaderLabels(["ID","Stok Giriş Tarihi","Dükkan","Tutar","Kasa Sayısı","Kasa Başı","Detay"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)
        w.setLayout(layout)
        self.tabs.addTab(w,"Kayıtlar")
        export_btn = QPushButton("Excel'e Aktar")
        export_btn.clicked.connect(self.export_to_excel)
        layout.addWidget(export_btn)  # uygun layout’a ekle
        self.setup_context_menu()
        self.refresh_table()

    def format_tl(self,value:float)->str:
        integer_part = int(abs(value))
        decimal_part = int(round((abs(value)-integer_part)*100))
        integer_str = f"{integer_part:,}".replace(",",".")

        return f"{integer_str},{decimal_part:02d} TL"

    def refresh_table(self):
        self.table.setRowCount(0)
        rows = db.fetch_transactions("2020-01-01","2030-01-01") or []

        for row_index,r in enumerate(rows):
            self.table.insertRow(row_index)
            record_id, tarih, shop, tutar, note, kasa_sayisi = r

            try:
                date_obj = QDate.fromString(tarih,"yyyy-MM-dd")
                tarih_str = date_obj.toString("dd/MM/yyyy")
            except:
                tarih_str = tarih

            try:
                kasa_sayisi = int(kasa_sayisi)
            except:
                kasa_sayisi = 1

            try:
                tutar_float = float(tutar)
            except:
                tutar_float = 0

            kasa_basi = abs(tutar_float)/kasa_sayisi if kasa_sayisi>0 else 0

            values = [record_id,tarih_str,shop,self.format_tl(tutar_float),str(kasa_sayisi),self.format_tl(kasa_basi),"Detay"]

            for col_index,val in enumerate(values):
                item = QTableWidgetItem(str(val))
                if col_index in [3,4]:  # Tutar ve Kasa Sayısı sağa yaslı
                    item.setTextAlignment(Qt.AlignRight|Qt.AlignVCenter)
                self.table.setItem(row_index,col_index,item)

            self.table.item(row_index,0).setData(Qt.UserRole, record_id)

            # Detay butonu
            btn = QPushButton("Detay")
            btn.clicked.connect(lambda checked,rid=record_id: self.open_detail(rid))
            self.table.setCellWidget(row_index,6,btn)

        self.table.setColumnHidden(0,True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    
    def export_to_excel(self):
        from PySide6.QtWidgets import QFileDialog
        import pandas as pd

        file_name, _ = QFileDialog.getSaveFileName(self, "Excel'e Aktar", "", "Excel Files (*.xlsx)")
        if not file_name:
            return

        # Tüm transactionları al
        rows = db.fetch_transactions("0000-00-00", "9999-12-31")

        data = []
        for row in rows:
            tid, tarih, shop, tutar, note, kasa_sayisi = row

            # kasa başı fiyat hesaplama
            kasa_basi = tutar / kasa_sayisi if kasa_sayisi and kasa_sayisi > 0 else 0

            data.append({
                "ID": tid,
                "Tarih": tarih,
                "Mağaza": shop,
                "Tutar": tutar,
                "Kasa Sayısı": kasa_sayisi,
                "Kasa Başı": round(kasa_basi, 2),
                "Not": note
            })

        df = pd.DataFrame(data)
        df.to_excel(file_name, index=False)



    def open_detail(self,record_id):
        detail_win = DetailWindow(record_id)
        detail_win.show()
        self.detail_windows.append(detail_win)

        # ...rapor kısmı aynı...


    def _init_tab_reports(self):
        w = QWidget()
        layout = QVBoxLayout(w)

        # Seçim menüsü
        self.chart_mode = QComboBox()
        self.chart_mode.addItems(["Aylık Gelir/Gider/Kâr", "Dükkan Bazlı"])
        layout.addWidget(self.chart_mode)

        # Grafik alanı
        self.chart = ChartCanvas()
        layout.addWidget(self.chart)

        # Yenile butonu
        update_btn = QPushButton("Grafiği Yenile")
        update_btn.clicked.connect(self.draw_chart)
        layout.addWidget(update_btn)

        w.setLayout(layout)
        self.tabs.addTab(w,"Raporlar")


   
 

   

    def draw_chart(self):
        self.chart.ax.clear()

        # Son 3 ay tarih aralığı
        end_date = date.today()
        start_date = end_date - relativedelta(months=3)
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")

        mode = self.chart_mode.currentText()

        if mode == "Aylık Gelir/Gider/Kâr":
            rows = db.group_by_month(start_str, end_str)  # aylık toplam
            if not rows:
                return

            labels = [r[0] for r in rows]  # örn. '2025-09'
            gelir = [r[1] for r in rows]
            gider = [abs(r[2]) for r in rows]
            kar = [r[3] for r in rows]

            x = range(len(labels))
            width = 0.2

            self.chart.ax.bar([i - width for i in x], gelir, width, color='#1f77b4', label='Gelir')
            self.chart.ax.bar(x, gider, width, color='#ff7f0e', label='Gider')
            self.chart.ax.bar([i + width for i in x], kar, width, color='#2ca02c', label='Kâr')

            for i in x:
                self.chart.ax.text(i - width, gelir[i]+0.01*max(gelir), f"{gelir[i]:,.0f}", ha='center', va='bottom', fontsize=7)
                self.chart.ax.text(i, gider[i]+0.01*max(gider), f"{gider[i]:,.0f}", ha='center', va='bottom', fontsize=7)
                self.chart.ax.text(i + width, kar[i]+0.01*max(kar), f"{kar[i]:,.0f}", ha='center', va='bottom', fontsize=7)

            self.chart.ax.set_xticks(x)
            self.chart.ax.set_xticklabels(labels, rotation=45, ha='right')
            self.chart.ax.set_title("Aylık Gelir-Gider-Kâr (Son 3 Ay)", fontsize=14, fontweight='bold')

        elif mode == "Dükkan Bazlı":
            rows = db.group_by_shop(start_str, end_str)
            if not rows:
                return

            labels = [r[0] for r in rows]  # dükkan isimleri
            gelir = [r[1] for r in rows]
            gider = [abs(r[2]) for r in rows]
            kar = [r[3] for r in rows]

            x = range(len(labels))
            width = 0.2

            self.chart.ax.bar([i - width for i in x], gelir, width, color='#1f77b4', label='Gelir')
            self.chart.ax.bar(x, gider, width, color='#ff7f0e', label='Gider')
            self.chart.ax.bar([i + width for i in x], kar, width, color='#2ca02c', label='Kâr')

            for i in x:
                self.chart.ax.text(i - width, gelir[i]+0.01*max(gelir), f"{gelir[i]:,.0f}", ha='center', va='bottom', fontsize=7)
                self.chart.ax.text(i, gider[i]+0.01*max(gider), f"{gider[i]:,.0f}", ha='center', va='bottom', fontsize=7)
                self.chart.ax.text(i + width, kar[i]+0.01*max(kar), f"{kar[i]:,.0f}", ha='center', va='bottom', fontsize=7)

            self.chart.ax.set_xticks(x)
            self.chart.ax.set_xticklabels(labels, rotation=45, ha='right')
            self.chart.ax.set_title("Dükkan Bazlı Gelir-Gider-Kâr (Son 3 Ay)", fontsize=14, fontweight='bold')

        # Ortak ayarlar
        self.chart.ax.set_ylabel("Tutar")
        self.chart.ax.legend()
        self.chart.ax.grid(True, linestyle='--', alpha=0.3)
        self.chart.figure.tight_layout()
        self.chart.draw()





def main():
    app = QApplication([])
    win = MainWindow()
    win.show()
    app.exec()

if __name__=="__main__":
    main()
