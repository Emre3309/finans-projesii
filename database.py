from datetime import datetime, timedelta
import sqlite3

DB_NAME = "finans.db"

# ----------------- DB Başlatma -----------------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    # Transactions tablosu
    cur.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tarih TEXT,
            shop TEXT,
            tutar REAL,
            note TEXT,
            kasa_sayisi INTEGER
        )
    """)
    # Transaction details tablosu
    cur.execute("""
        CREATE TABLE IF NOT EXISTS transaction_details (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id INTEGER,
            mal TEXT,
            kasa INTEGER,
            miktar REAL,
            birim TEXT,
            birim_fiyat REAL,
            kdv REAL,
            kdv_tutari REAL,
            mal_hizmet_tutari REAL,
            FOREIGN KEY(transaction_id) REFERENCES transactions(id)
        )
    """)
    # Masraflar tablosu
    cur.execute("""
        CREATE TABLE IF NOT EXISTS masraflar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id INTEGER,
            komisyon REAL,
            komisyon_kdv REAL,
            masraf REAL,
            FOREIGN KEY(transaction_id) REFERENCES transactions(id)
        )
    """)
    conn.commit()
    conn.close()


# ----------------- Yardımcı Fonksiyon -----------------
def get_connection():
    return sqlite3.connect(DB_NAME)

DB_PATH = "finans.db"
# ----------------- Transaction -----------------
def add_transaction(tarih, shop, tutar, note, kasa_sayisi):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO transactions (tarih, shop, tutar, note, kasa_sayisi)
        VALUES (?,?,?,?,?)
    """, (tarih, shop, tutar, note, kasa_sayisi))
    conn.commit()
    last_id = cur.lastrowid
    conn.close()
    return last_id

def delete_transaction(transaction_id):
    conn = get_connection()
    cur = conn.cursor()

    # Önce detayları sil
    cur.execute("DELETE FROM transaction_details WHERE transaction_id = ?", (transaction_id,))
    
    # Sonra masrafları sil
    cur.execute("DELETE FROM masraflar WHERE transaction_id = ?", (transaction_id,))
    
    # En son ana kaydı sil
    cur.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))

    conn.commit()
    conn.close()



def group_by_month(start_date, end_date):
    conn = get_connection()
    cur = conn.cursor()
    query = """
        SELECT strftime('%Y-%m', tarih) AS ay,
               SUM(CASE WHEN tutar>0 THEN tutar ELSE 0 END) AS gelir,
               SUM(CASE WHEN tutar<0 THEN tutar ELSE 0 END) AS gider,
               SUM(tutar) AS kar
        FROM transactions
        WHERE tarih BETWEEN ? AND ?
        GROUP BY ay
        ORDER BY ay
    """
    cur.execute(query, (start_date, end_date))
    rows = cur.fetchall()
    conn.close()
    return rows

def group_by_shop(start_date, end_date):
    conn = get_connection()
    cur = conn.cursor()
    query = """
        SELECT shop,
               SUM(CASE WHEN tutar>0 THEN tutar ELSE 0 END) AS gelir,
               SUM(CASE WHEN tutar<0 THEN tutar ELSE 0 END) AS gider,
               SUM(tutar) AS kar
        FROM transactions
        WHERE tarih BETWEEN ? AND ?
        GROUP BY shop
        ORDER BY shop
    """
    cur.execute(query, (start_date, end_date))
    rows = cur.fetchall()
    conn.close()
    return rows




def group_by_last_3_months():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    today = datetime.today()
    three_months_ago = today - timedelta(days=90)
    start_date = three_months_ago.strftime("%Y-%m-%d")
    end_date = today.strftime("%Y-%m-%d")

    query = """
    SELECT strftime('%Y-%m', tarih) AS ay,
           SUM(CASE WHEN tutar >= 0 THEN tutar ELSE 0 END) AS gelir,
           SUM(CASE WHEN tutar < 0 THEN tutar ELSE 0 END) AS gider,
           SUM(tutar) AS kar
    FROM transactions
    WHERE tarih BETWEEN ? AND ?
    GROUP BY ay
    ORDER BY ay ASC
    """
    cur.execute(query, (start_date, end_date))
    rows = cur.fetchall()
    conn.close()
    return rows

def fetch_transactions(start_date, end_date):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, tarih, shop, tutar, note, kasa_sayisi
        FROM transactions
        WHERE tarih BETWEEN ? AND ?
        ORDER BY id DESC
    """, (start_date, end_date))
    rows = cur.fetchall()
    conn.close()
    return rows


# ----------------- Transaction Details -----------------
def add_detail(transaction_id, mal, kasa, miktar, birim, birim_fiyat, kdv, kdv_tutari, mal_hizmet_tutari):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO transaction_details
        (transaction_id, mal, kasa, miktar, birim, birim_fiyat, kdv, kdv_tutari, mal_hizmet_tutari)
        VALUES (?,?,?,?,?,?,?,?,?)
    """, (transaction_id, mal, kasa, miktar, birim, birim_fiyat, kdv, kdv_tutari, mal_hizmet_tutari))
    conn.commit()
    conn.close()


def fetch_details(transaction_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT mal, kasa, miktar, birim, birim_fiyat, kdv, kdv_tutari, mal_hizmet_tutari
        FROM transaction_details
        WHERE transaction_id=?
    """, (transaction_id,))
    rows = cur.fetchall()
    conn.close()
    return rows

def group_details_by_shop(shop_name):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT d.mal, SUM(d.mal_hizmet_tutari)
        FROM transaction_details d
        JOIN transactions t ON d.transaction_id = t.id
        WHERE t.shop = ?
        GROUP BY d.mal
        ORDER BY d.mal
    """, (shop_name,))
    rows = cur.fetchall()
    conn.close()
    return rows

def delete_detail(transaction_id, mal_name):
    conn = get_connection()  # Bu senin DB'yi doğru açıyor
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM transaction_details WHERE transaction_id=? AND mal=?",
        (transaction_id, mal_name)
    )
    conn.commit()
    conn.close()

def delete_masraf(transaction_id, row_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM masraflar WHERE transaction_id=? AND id=?", (transaction_id, row_id))
    conn.commit()
    conn.close()

def delete_masraf_by_values(transaction_id, komisyon, komisyon_kdv, masraf):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        DELETE FROM masraflar
        WHERE transaction_id=? AND komisyon=? AND komisyon_kdv=? AND masraf=?
    """, (transaction_id, komisyon, komisyon_kdv, masraf))
    conn.commit()
    conn.close()


def group_details_all_shops():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT t.shop, d.mal, SUM(d.mal_hizmet_tutari)
        FROM transaction_details d
        JOIN transactions t ON d.transaction_id = t.id
        GROUP BY t.shop, d.mal
        ORDER BY d.mal, t.shop
    """)
    rows = cur.fetchall()
    conn.close()
    return rows



# ----------------- Masraflar -----------------
def add_masraf(transaction_id, komisyon, komisyon_kdv, masraf):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO masraflar (transaction_id, komisyon, komisyon_kdv, masraf)
        VALUES (?, ?, ?, ?)
    """, (transaction_id, komisyon, komisyon_kdv, masraf))
    conn.commit()
    conn.close()


def fetch_masraflar(transaction_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT komisyon, komisyon_kdv, masraf
        FROM masraflar
        WHERE transaction_id=?
    """, (transaction_id,))
    rows = cur.fetchall()
    conn.close()
    return rows


# ----------------- DB Başlat -----------------
if __name__ == "__main__":
    init_db()
