#PROGRAM POPPER CIHUY

import os
import time
from datetime import date, datetime
import psycopg2
from psycopg2 import IntegrityError
import questionary
from questionary import Style as QStyle
import pyfiglet
from colorama import init, Fore
import pandas as pd
from tabulate import tabulate

init(autoreset=True)

# --------------------------
# DB CONFIG
# --------------------------
DB_CONFIG = {
    "dbname": "sistem_popper",
    "user": "postgres",
    "password": "adminadmin",
    "host": "localhost",
    "port": "5432",
}

# questionary style
qstyle = QStyle(
    [
        ("qmark", "fg:#00ff00 bold"),
        ("question", "fg:#00ff00"),
        ("answer", "fg:#00ffff bold"),
        ("pointer", "fg:#00ff00 bold"),
        ("highlighted", "fg:#00ff00 bold"),
        ("selected", "fg:#00ff00"),
    ]
)

# --------------------------
# UTILITIES
# --------------------------
def clear_screen():
    try:
        if os.name == "nt":
            os.system("cls")
        else:
            os.system("clear")
    except Exception:
        pass

def print_title():
    clear_screen()
    banner = pyfiglet.figlet_format("POPPER", font="slant")
    for ch in banner:
        print(Fore.GREEN + ch, end="", flush=True)
        time.sleep(0.0005)
    print("\n")

def connect_db():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(Fore.RED + "[ERROR] Gagal koneksi DB:", e)
        return None

def column_exists(conn, table_name, column_name):
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT COUNT(*) FROM information_schema.columns
            WHERE table_name = %s AND column_name = %s
        """, (table_name, column_name))
        return cur.fetchone()[0] > 0
    except Exception:
        return False
    finally:
        cur.close()

def print_table(rows, headers):
    if not rows:
        print("\n( kosong )\n")
        return
    try:
        df = pd.DataFrame(rows, columns=headers)
        # Use grid to match the visual style you requested
        print("\n" + tabulate(df, headers="keys", tablefmt="grid", showindex=False) + "\n")
    except Exception:
        # fallback
        for r in rows:
            print(r)

# --------------------------
# Business helpers
# --------------------------
def get_discount_for_purchase_count(n):
    # discount list: purchase number 5,10,20 => 10%
    return 10 if n in (5, 10, 20) else 0

# --------------------------
# Ensure minimal seed data to avoid FK issues
# --------------------------
def inialisasi_database():
    conn = connect_db()
    if not conn:
        return
    cur = conn.cursor()
    try:
        # ensure admin
        cur.execute("SELECT id_admin FROM adminn LIMIT 1;")
        if cur.fetchone() is None:
            cur.execute("INSERT INTO adminn (username, pass_admin, tanggal_lahir, no_telp, email) VALUES (%s,%s,%s,%s,%s) RETURNING id_admin;",
                        ("admin", "admin123", date(1990,1,1), "081234567890", "admin@example.com"))
            aid = cur.fetchone()[0]
            conn.commit()
            print(Fore.YELLOW + f"[seed] Admin default dibuat id={aid}")

        # ensure alamat
        cur.execute("SELECT id_alamat FROM alamat LIMIT 1;")
        if cur.fetchone() is None:
            cur.execute("INSERT INTO alamat (nama_jalan) VALUES (%s) RETURNING id_alamat;", ("Jalan Default",))
            a_id = cur.fetchone()[0]; conn.commit()

        # ensure kota
        cur.execute("SELECT id_kota FROM kota LIMIT 1;")
        if cur.fetchone() is None:
            cur.execute("INSERT INTO kota (nama_kota) VALUES (%s) RETURNING id_kota;", ("Kota Default",))
            k_id = cur.fetchone()[0]; conn.commit()

        # ensure kecamatan (requires id_kota and id_alamat maybe)
        cur.execute("SELECT id_kecamatan FROM kecamatan LIMIT 1;")
        if cur.fetchone() is None:
            # pick an alamat and kota
            cur.execute("SELECT id_alamat FROM alamat LIMIT 1;"); ar = cur.fetchone(); aid = ar[0] if ar else None
            cur.execute("SELECT id_kota FROM kota LIMIT 1;"); kr = cur.fetchone(); kid = kr[0] if kr else None
            if kid is None:
                cur.execute("INSERT INTO kota (nama_kota) VALUES (%s) RETURNING id_kota;", ("Kota Default",)); kid = cur.fetchone()[0]; conn.commit()
            cur.execute("INSERT INTO kecamatan (nama_kecamatan, id_alamat, id_kota) VALUES (%s,%s,%s) RETURNING id_kecamatan;", ("Kec Default", aid, kid))
            conn.commit()

        # ensure kategori
        cur.execute("SELECT id_kategori FROM kategori LIMIT 1;")
        if cur.fetchone() is None:
            cur.execute("INSERT INTO kategori (jenis_kategori) VALUES (%s) RETURNING id_kategori;", ("Umum",))
            conn.commit()

        # ensure supplier (needs alamat optionally)
        cur.execute("SELECT id_supplier FROM supplier LIMIT 1;")
        if cur.fetchone() is None:
            cur.execute("SELECT id_alamat FROM alamat LIMIT 1;"); ar = cur.fetchone(); aid = ar[0] if ar else None
            cur.execute("INSERT INTO supplier (nama_perusahaan, kontak_person, no_kontak, id_alamat) VALUES (%s,%s,%s,%s) RETURNING id_supplier;",
                        ("Supplier Default","Contact","0810000000", aid))
            conn.commit()

        # ensure karyawan
        cur.execute("SELECT id_karyawan FROM karyawan LIMIT 1;")
        if cur.fetchone() is None:
            cur.execute("SELECT id_admin FROM adminn LIMIT 1;"); ar = cur.fetchone(); admin_id = ar[0] if ar else None
            cur.execute("SELECT id_alamat FROM alamat LIMIT 1;"); ar = cur.fetchone(); alamat_id = ar[0] if ar else None
            if admin_id:
                cur.execute("INSERT INTO karyawan (username, pass_karyawan, tanggal_lahir, no_telp, email, status_karyawan, id_admin, id_alamat) VALUES (%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id_karyawan;",
                            ("karyawan_default","karyawan123", date(1995,1,1), "08111111111","karyawan@example.com", True, admin_id, alamat_id))
                conn.commit()

        # ensure produk
        cur.execute("SELECT id_produk FROM produk LIMIT 1;")
        if cur.fetchone() is None:
            cur.execute("SELECT id_admin FROM adminn LIMIT 1;"); ar = cur.fetchone(); admin_id = ar[0] if ar else None
            cur.execute("SELECT id_kategori FROM kategori LIMIT 1;"); ar = cur.fetchone(); kat_id = ar[0] if ar else None
            cur.execute("SELECT id_supplier FROM supplier LIMIT 1;"); ar = cur.fetchone(); sup_id = ar[0] if ar else None
            if admin_id and kat_id and sup_id:
                samples = [
                    ("AgroShield Pro", 100, 56000, False, kat_id, admin_id, sup_id),
                    ("PlantaGuard 500", 100, 29900, False, kat_id, admin_id, sup_id),
                ]
                for s in samples:
                    cur.execute("INSERT INTO produk (nama_produk, stock_produk, harga_produk, hapus_produk, id_kategori, id_admin, id_supplier) VALUES (%s,%s,%s,%s,%s,%s,%s);", s)
                conn.commit()

        # ensure transaksi minimal (if none)
        cur.execute("SELECT id_transaksi FROM transaksi LIMIT 1;")
        if cur.fetchone() is None:
            cur.execute("SELECT id_karyawan FROM karyawan LIMIT 1;"); kr = cur.fetchone(); karyawan_id = kr[0] if kr else None
            # create a minimal pelanggan if none
            cur.execute("SELECT id_pelanggan FROM pelanggan LIMIT 1;"); pr = cur.fetchone(); pel_id = pr[0] if pr else None
            if pel_id is None:
                # create dummy pelanggan
                cur.execute("INSERT INTO pelanggan (username, pass_pelanggan, tanggal_lahir, no_telp, email) VALUES (%s,%s,%s,%s,%s) RETURNING id_pelanggan;",
                            ("pelanggan_default","pel123", date(2000,1,1), "08222222222","pel@example.com"))
                pel_id = cur.fetchone()[0]; conn.commit()
            if karyawan_id:
                cur.execute("INSERT INTO transaksi (tanggal_transaksi, status_terkonfirmasi, id_karyawan, id_pelanggan) VALUES (%s,%s,%s,%s) RETURNING id_transaksi;", (date.today(), False, karyawan_id, pel_id))
                conn.commit()

    except Exception as e:
        conn.rollback()
        print(Fore.RED + "[seed error]", e)
    finally:
        cur.close()
        conn.close()

# --------------------------
# AUTHENTICATION
# --------------------------
def login():
    print_title()
    print(Fore.CYAN + "=== LOGIN ===")
    username = questionary.text("Username:", style=qstyle).ask()
    password = questionary.password("Password:", style=qstyle).ask()

    conn = connect_db()
    if not conn:
        return None, None
    cur = conn.cursor()
    try:
        # admin
        cur.execute("SELECT id_admin FROM adminn WHERE username=%s AND pass_admin=%s LIMIT 1;", (username, password))
        r = cur.fetchone()
        if r:
            return "admin", r[0]
        # karyawan
        cur.execute("SELECT id_karyawan FROM karyawan WHERE username=%s AND pass_karyawan=%s LIMIT 1;", (username, password))
        r = cur.fetchone()
        if r:
            return "karyawan", r[0]
        # pelanggan
        cur.execute("SELECT id_pelanggan FROM pelanggan WHERE username=%s AND pass_pelanggan=%s LIMIT 1;", (username, password))
        r = cur.fetchone()
        if r:
            return "pelanggan", r[0]

        questionary.print("Login gagal: username/password salah.", style="fg:red")
        time.sleep(0.8)
        return None, None
    except Exception as e:
        questionary.print(f"[ERROR] saat login: {e}", style="fg:red")
        return None, None
    finally:
        cur.close(); conn.close()

def register_pelanggan():
    clear_screen(); print_title()
    print(Fore.CYAN + "=== REGISTER PELANGGAN ===")
    username = questionary.text("Username:", style=qstyle).ask()
    password = questionary.password("Password:", style=qstyle).ask()
    tgl = questionary.text("Tanggal lahir (YYYY-MM-DD):", style=qstyle).ask()
    telp = questionary.text("No. Telp:", style=qstyle).ask()
    email = questionary.text("Email:", style=qstyle).ask()

    conn = connect_db()
    if not conn:
        return
    cur = conn.cursor()
    try:
        # Insert pelanggan (DDL: pelanggan has no id_transaksi now)
        cur.execute("INSERT INTO pelanggan (username, pass_pelanggan, tanggal_lahir, no_telp, email) VALUES (%s,%s,%s,%s,%s) RETURNING id_pelanggan;",
                    (username, password, tgl, telp, email))
        new_id = cur.fetchone()[0]
        conn.commit()
        questionary.print(f"[OK] Registrasi berhasil. ID pelanggan: {new_id}", style="fg:green")
    except IntegrityError as ie:
        conn.rollback()
        questionary.print(f"[ERROR] Integritas data (username/no_telp/email mungkin sudah ada): {ie}", style="fg:red")
    except Exception as e:
        conn.rollback()
        questionary.print(f"[ERROR] Registrasi gagal: {e}", style="fg:red")
    finally:
        cur.close(); conn.close(); time.sleep(0.6)

# --------------------------
# ADMIN FEATURES
# --------------------------
def admin_profile(admin_id):
    conn = connect_db()
    if not conn:
        return
    cur = conn.cursor()
    try:
        cur.execute("SELECT id_admin, username, tanggal_lahir, no_telp, email FROM adminn WHERE id_admin=%s;", (admin_id,))
        r = cur.fetchone(); clear_screen(); print(Fore.CYAN + "=== PROFIL ADMIN ===\n")
        if r:
            rows = [(r[0], r[1], str(r[2]), r[3], r[4])]
            print_table(rows, ["ID Admin","Username","Tanggal Lahir","No. Telepon","Email"])
        else:
            questionary.print("Profil admin tidak ditemukan.", style="fg:yellow")
    except Exception as e:
        questionary.print(f"[ERROR] Ambil profil admin: {e}", style="fg:red")
    finally:
        cur.close(); conn.close()
        questionary.text("ENTER untuk kembali", default="").ask()

def list_categories(conn):
    cur = conn.cursor()
    cur.execute("SELECT id_kategori, jenis_kategori FROM kategori ORDER BY id_kategori;")
    rows = cur.fetchall(); cur.close(); return rows

def add_category(conn):
    cur = conn.cursor()
    try:
        nama = questionary.text("Nama kategori baru:", style=qstyle).ask()
        if not nama:
            questionary.print("Batal. Nama kosong.", style="fg:yellow"); cur.close(); return
        cur.execute("INSERT INTO kategori (jenis_kategori) VALUES (%s) RETURNING id_kategori;", (nama,))
        new_id = cur.fetchone()[0]; conn.commit(); questionary.print(f"[OK] Kategori dibuat ID: {new_id}", style="fg:green")
    except Exception as e:
        conn.rollback(); questionary.print(f"[ERROR] Gagal buat kategori: {e}", style="fg:red")
    finally:
        cur.close()

def admin_add_product(admin_id):
    conn = connect_db()
    if not conn:
        return
    cur = conn.cursor()
    try:
        clear_screen(); print(Fore.CYAN + "=== TAMBAH PRODUK ===")
        nama = questionary.text("Nama produk:", style=qstyle).ask()
        stok_s = questionary.text("Stok (angka):", style=qstyle).ask()
        if not stok_s or not stok_s.isdigit(): questionary.print("Stok harus angka.", style="fg:red"); cur.close(); conn.close(); return
        stok = int(stok_s)
        harga_s = questionary.text("Harga (angka):", style=qstyle).ask()
        try: harga = int(harga_s)
        except: questionary.print("Harga harus angka.", style="fg:red"); cur.close(); conn.close(); return

        cats = list_categories(conn)
        if not cats:
            questionary.print("Belum ada kategori. Silakan buat kategori.", style="fg:yellow")
            if questionary.confirm("Buat kategori sekarang?", default=True).ask(): add_category(conn); cats = list_categories(conn)
        choices = [f"{c[0]} - {c[1]}" for c in cats]
        sel = questionary.select("Pilih kategori:", choices=choices, style=qstyle).ask()
        id_kategori = int(sel.split(" - ")[0])

        # supplier selection
        cur.execute("SELECT id_supplier, nama_perusahaan FROM supplier ORDER BY id_supplier;")
        suppliers = cur.fetchall()
        if not suppliers:
            questionary.print("Belum ada supplier. Tambahkan supplier lewat DB.", style="fg:yellow"); cur.close(); conn.close(); return
        sel_sup = questionary.select("Pilih supplier:", choices=[f"{s[0]} - {s[1]}" for s in suppliers], style=qstyle).ask()
        id_supplier = int(sel_sup.split(" - ")[0])

        cur.execute("INSERT INTO produk (nama_produk, stock_produk, harga_produk, hapus_produk, id_kategori, id_admin, id_supplier) VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING id_produk;",
                    (nama, stok, harga, False, id_kategori, admin_id, id_supplier))
        pid = cur.fetchone()[0]; conn.commit()
        questionary.print(f"[OK] Produk dibuat ID: {pid}", style="fg:green")
    except Exception as e:
        conn.rollback(); questionary.print(f"[ERROR] Gagal tambah produk: {e}", style="fg:red")
    finally:
        cur.close(); conn.close()
        time.sleep(0.2)

def admin_list_products(show_all=False):
    conn = connect_db()
    if not conn:
        return
    cur = conn.cursor()
    try:
        if show_all:
            cur.execute("""SELECT p.id_produk, p.nama_produk, p.stock_produk, p.harga_produk, p.hapus_produk, COALESCE(k.jenis_kategori,'-'), COALESCE(a.username,'-'), COALESCE(s.nama_perusahaan,'-')
                           FROM produk p LEFT JOIN kategori k ON p.id_kategori=k.id_kategori LEFT JOIN adminn a ON p.id_admin=a.id_admin LEFT JOIN supplier s ON p.id_supplier=s.id_supplier ORDER BY p.id_produk;""")
            rows = cur.fetchall(); headers = ["ID","Nama","Stok","Harga","NonAktif","Kategori","Admin","Supplier"]
        else:
            cur.execute("""SELECT p.id_produk, p.nama_produk, p.stock_produk, p.harga_produk, COALESCE(k.jenis_kategori,'-')
                           FROM produk p LEFT JOIN kategori k ON p.id_kategori=k.id_kategori WHERE p.hapus_produk=false ORDER BY p.id_produk;""")
            rows = cur.fetchall(); headers = ["ID","Nama","Stok","Harga","Kategori"]
        clear_screen(); print(Fore.CYAN + ("=== DAFTAR PRODUK (SEMUA)" if show_all else "=== DAFTAR PRODUK (AKTIF)") + "\n")
        print_table(rows, headers)
    except Exception as e:
        questionary.print(f"[ERROR] ambil produk: {e}", style="fg:red")
    finally:
        cur.close(); conn.close()
        questionary.text("ENTER untuk kembali", default="").ask()

def admin_update_product(admin_id=None):
    conn = connect_db()
    if not conn:
        return
    cur = conn.cursor()
    try:
        admin_list_products(show_all=True)
        pid_s = questionary.text("ID produk yang ingin diupdate:", style=qstyle).ask()
        if not pid_s or not pid_s.isdigit(): questionary.print("ID tidak valid.", style="fg:red"); cur.close(); conn.close(); return
        pid = int(pid_s)
        cur.execute("SELECT nama_produk, stock_produk, harga_produk, id_kategori, id_supplier FROM produk WHERE id_produk=%s;", (pid,))
        row = cur.fetchone()
        if not row: questionary.print("Produk tidak ditemukan.", style="fg:red"); cur.close(); conn.close(); return
        nama_old, stok_old, harga_old, id_kat_old, id_sup_old = row
        clear_screen(); print(Fore.CYAN + "=== UPDATE PRODUK ===\n")
        nama = questionary.text("Nama baru (kosong = tetap):", default=nama_old, style=qstyle).ask()
        stok_s = questionary.text("Stok baru (kosong = tetap):", default=str(stok_old), style=qstyle).ask()
        harga_s = questionary.text("Harga baru (kosong = tetap):", default=str(harga_old), style=qstyle).ask()
        cats = list_categories(conn); choices = [f"{c[0]} - {c[1]}" for c in cats]
        sel = questionary.select("Pilih kategori:", choices=choices, style=qstyle).ask()
        id_kategori = int(sel.split(" - ")[0])
        cur.execute("SELECT id_supplier, nama_perusahaan FROM supplier ORDER BY id_supplier;"); suppliers = cur.fetchall()
        sel_sup = questionary.select("Pilih supplier:", choices=[f"{s[0]} - {s[1]}" for s in suppliers], style=qstyle).ask()
        id_supplier = int(sel_sup.split(" - ")[0])
        try: stok = int(stok_s); harga = int(harga_s)
        except: questionary.print("Stok / Harga harus angka.", style="fg:red"); cur.close(); conn.close(); return
        cur.execute("UPDATE produk SET nama_produk=%s, stock_produk=%s, harga_produk=%s, id_kategori=%s, id_supplier=%s, id_admin=%s WHERE id_produk=%s;",
                    (nama, stok, harga, id_kategori, id_supplier, admin_id, pid))
        conn.commit(); questionary.print("[OK] Produk diupdate.", style="fg:green")
    except Exception as e:
        conn.rollback(); questionary.print(f"[ERROR] update produk: {e}", style="fg:red")
    finally:
        cur.close(); conn.close(); time.sleep(0.2)

def admin_soft_delete_product():
    conn = connect_db()
    if not conn:
        return
    cur = conn.cursor()
    try:
        admin_list_products(show_all=True)
        pid_s = questionary.text("ID produk untuk non-aktifkan (soft-delete):", style=qstyle).ask()
        if not pid_s or not pid_s.isdigit(): questionary.print("ID tidak valid.", style="fg:red"); cur.close(); conn.close(); return
        pid = int(pid_s)
        cur.execute("SELECT nama_produk, hapus_produk FROM produk WHERE id_produk=%s;", (pid,))
        row = cur.fetchone()
        if not row: questionary.print("Produk tidak ditemukan.", style="fg:red"); cur.close(); conn.close(); return
        if row[1]: questionary.print("Produk sudah non-aktif.", style="fg:yellow"); cur.close(); conn.close(); return
        if questionary.confirm(f"Non-aktifkan produk '{row[0]}' ?", default=False).ask():
            cur.execute("UPDATE produk SET hapus_produk = true WHERE id_produk=%s;", (pid,)); conn.commit(); questionary.print("[OK] Produk dinonaktifkan (soft-delete).", style="fg:green")
        else:
            questionary.print("Dibatalkan.", style="fg:yellow")
    except Exception as e:
        conn.rollback(); questionary.print(f"[ERROR] {e}", style="fg:red")
    finally:
        cur.close(); conn.close(); time.sleep(0.2)

# --------------------------
# ADMIN: KARYAWAN MANAGEMENT (NEW)
# --------------------------
def admin_list_karyawan():
    conn = connect_db()
    if not conn:
        return
    cur = conn.cursor()
    try:
        cur.execute("SELECT id_karyawan, username, tanggal_lahir, no_telp, email, status_karyawan, pass_karyawan FROM karyawan ORDER BY id_karyawan;")
        rows = cur.fetchall()
        print_table(rows, ["ID Karyawan","Username","Tanggal Lahir","No. Telepon","Email","Aktif","Password"])
    except Exception as e:
        questionary.print(f"[ERROR] list karyawan: {e}", style="fg:red")
    finally:
        cur.close(); conn.close()
        questionary.text("ENTER untuk kembali", default="").ask()

def admin_add_karyawan(admin_id):
    conn = connect_db()
    if not conn:
        return
    cur = conn.cursor()
    try:
        clear_screen(); print(Fore.CYAN + "=== TAMBAH KARYAWAN ===")
        username = questionary.text("Username:", style=qstyle).ask()
        password = questionary.password("Password (plain):", style=qstyle).ask()
        tgl = questionary.text("Tanggal lahir (YYYY-MM-DD):", style=qstyle).ask()
        telp = questionary.text("No. Telp:", style=qstyle).ask()
        email = questionary.text("Email:", style=qstyle).ask()
        # create alamat record (admin requested: create alamat from input nama_jalan)
        nama_jalan = questionary.text("Nama jalan (untuk alamat):", style=qstyle).ask()
        cur.execute("INSERT INTO alamat (nama_jalan) VALUES (%s) RETURNING id_alamat;", (nama_jalan,))
        alamat_id = cur.fetchone()[0]
        conn.commit()
        # insert karyawan (id_admin provided by admin performing action)
        cur.execute("INSERT INTO karyawan (username, pass_karyawan, tanggal_lahir, no_telp, email, status_karyawan, id_admin, id_alamat) VALUES (%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id_karyawan;",
                    (username, password, tgl, telp, email, True, admin_id, alamat_id))
        new_id = cur.fetchone()[0]; conn.commit()
        questionary.print(f"[OK] Karyawan dibuat ID: {new_id}", style="fg:green")
    except IntegrityError as ie:
        conn.rollback(); questionary.print(f"[ERROR] Integritas (mungkin username/no_telp/email duplikat): {ie}", style="fg:red")
    except Exception as e:
        conn.rollback(); questionary.print(f"[ERROR] tambah karyawan: {e}", style="fg:red")
    finally:
        cur.close(); conn.close(); time.sleep(0.2)

def admin_update_karyawan():
    conn = connect_db()
    if not conn:
        return
    cur = conn.cursor()
    try:
        admin_list_karyawan()
        id_s = questionary.text("ID karyawan untuk update:", style=qstyle).ask()
        if not id_s or not id_s.isdigit(): questionary.print("ID tidak valid.", style="fg:red"); cur.close(); conn.close(); return
        kid = int(id_s)
        cur.execute("SELECT username, pass_karyawan, tanggal_lahir, no_telp, email, status_karyawan FROM karyawan WHERE id_karyawan=%s;", (kid,))
        r = cur.fetchone()
        if not r: questionary.print("Karyawan tidak ditemukan.", style="fg:red"); cur.close(); conn.close(); return
        uname_old, pass_old, tgl_old, telp_old, email_old, st_old = r
        clear_screen(); print(Fore.CYAN + "=== UPDATE KARYAWAN ===\n")
        uname = questionary.text("Username (kosong=tetap):", default=uname_old, style=qstyle).ask()
        pwd = questionary.password("Password (kosong=tetap):", style=qstyle).ask() or pass_old
        tgl = questionary.text("Tanggal lahir (YYYY-MM-DD):", default=str(tgl_old), style=qstyle).ask()
        telp = questionary.text("No. Telp:", default=telp_old, style=qstyle).ask()
        email = questionary.text("Email:", default=email_old, style=qstyle).ask()
        status = questionary.confirm("Aktifkan karyawan?", default=bool(st_old)).ask()
        cur.execute("UPDATE karyawan SET username=%s, pass_karyawan=%s, tanggal_lahir=%s, no_telp=%s, email=%s, status_karyawan=%s WHERE id_karyawan=%s;",
                    (uname, pwd, tgl, telp, email, status, kid))
        conn.commit(); questionary.print("[OK] Karyawan diupdate.", style="fg:green")
    except Exception as e:
        conn.rollback(); questionary.print(f"[ERROR] update karyawan: {e}", style="fg:red")
    finally:
        cur.close(); conn.close(); time.sleep(0.2)

def admin_delete_karyawan():
    conn = connect_db()
    if not conn:
        return
    cur = conn.cursor()
    try:
        admin_list_karyawan()
        id_s = questionary.text("ID karyawan untuk hapus:", style=qstyle).ask()
        if not id_s or not id_s.isdigit(): questionary.print("ID tidak valid.", style="fg:red"); cur.close(); conn.close(); return
        kid = int(id_s)
        cur.execute("SELECT username FROM karyawan WHERE id_karyawan=%s;", (kid,))
        r = cur.fetchone()
        if not r: questionary.print("Karyawan tidak ditemukan.", style="fg:red"); cur.close(); conn.close(); return
        if questionary.confirm(f"Hapus karyawan '{r[0]}'? (This will delete record)", default=False).ask():
            cur.execute("DELETE FROM karyawan WHERE id_karyawan=%s;", (kid,)); conn.commit(); questionary.print("[OK] Karyawan dihapus.", style="fg:green")
    except Exception as e:
        conn.rollback(); questionary.print(f"[ERROR] hapus karyawan: {e}", style="fg:red")
    finally:
        cur.close(); conn.close(); time.sleep(0.2)

# --------------------------
# ADMIN: Pelanggan view (show passwords)
# --------------------------
def admin_list_pelanggan():
    conn = connect_db()
    if not conn:
        return
    cur = conn.cursor()
    try:
        cur.execute("SELECT id_pelanggan, username, tanggal_lahir, no_telp, email, pass_pelanggan FROM pelanggan ORDER BY id_pelanggan;")
        rows = cur.fetchall()
        print_table(rows, ["ID Pelanggan","Username","Tanggal Lahir","No. Telepon","Email","Password"])
    except Exception as e:
        questionary.print(f"[ERROR] ambil pelanggan: {e}", style="fg:red")
    finally:
        cur.close(); conn.close()
        questionary.text("ENTER untuk kembali", default="").ask()

# --------------------------
# ADMIN: Reports
# --------------------------
def admin_report_transactions():
    conn = connect_db()
    if not conn:
        return
    cur = conn.cursor()
    try:
        clear_screen(); print(Fore.CYAN + "=== LAPORAN TRANSAKSI & KEUANGAN ===")
        pilih = questionary.select("Pilih laporan:", choices=["Total pendapatan","Produk terlaris","Detail transaksi","Semua (gabungan)","Filter tanggal","Kembali"], style=qstyle).ask()
        if pilih == "Total pendapatan" or pilih == "Semua (gabungan)":
            cur.execute("SELECT COALESCE(SUM((d.harga*d.quantity) - ((d.harga*d.quantity)*d.dicount/100)),0) FROM detail_transaksi d;")
            total = cur.fetchone()[0] or 0
            print(Fore.GREEN + f"Total pemasukan: Rp{int(total)}")
        if pilih == "Produk terlaris" or pilih == "Semua (gabungan)":
            cur.execute("SELECT pr.id_produk, pr.nama_produk, SUM(d.quantity) as jumlah, SUM((d.harga*d.quantity) - ((d.harga*d.quantity)*d.dicount/100)) as pendapatan FROM detail_transaksi d JOIN produk pr ON d.id_produk=pr.id_produk GROUP BY pr.id_produk, pr.nama_produk ORDER BY pendapatan DESC;")
            perprod = cur.fetchall(); print_table(perprod, ["ID Produk","Nama","Total Terjual","Pendapatan (Rp)"])
        if pilih == "Detail transaksi" or pilih == "Semua (gabungan)":
            cur.execute("SELECT d.id_detail_transaksi, d.id_transaksi, pr.nama_produk, d.quantity, d.dicount, d.harga FROM detail_transaksi d JOIN produk pr ON d.id_produk=pr.id_produk ORDER BY d.id_transaksi DESC;")
            rows = cur.fetchall(); print_table(rows, ["ID Detail","ID Trans","Produk","Qty","Diskon%","Harga"])
        if pilih == "Filter tanggal":
            t1 = questionary.text("Tanggal mulai (YYYY-MM-DD):", style=qstyle).ask(); t2 = questionary.text("Tanggal akhir (YYYY-MM-DD):", style=qstyle).ask()
            try:
                ds = datetime.strptime(t1, "%Y-%m-%d").date(); de = datetime.strptime(t2, "%Y-%m-%d").date()
            except:
                questionary.print("Format tanggal salah", style="fg:red"); cur.close(); conn.close(); return
            cur.execute("SELECT t.id_transaksi, t.tanggal_transaksi, p.username as pelanggan, k.username as karyawan, (SELECT COALESCE(SUM((d.harga*d.quantity) - ((d.harga*d.quantity)*d.dicount/100)),0) FROM detail_transaksi d WHERE d.id_transaksi=t.id_transaksi) as total FROM transaksi t LEFT JOIN pelanggan p ON t.id_pelanggan=p.id_pelanggan LEFT JOIN karyawan k ON t.id_karyawan=k.id_karyawan WHERE t.tanggal_transaksi BETWEEN %s AND %s ORDER BY t.tanggal_transaksi DESC;", (ds, de))
            rows = cur.fetchall(); print_table(rows, ["ID Trans","Tanggal","Pelanggan","Karyawan","Total (Rp)"])
    except Exception as e:
        questionary.print(f"[ERROR] laporan admin: {e}", style="fg:red")
    finally:
        cur.close(); conn.close()
        questionary.text("ENTER", default="").ask()

# --------------------------
# KARYAWAN FEATURES
# --------------------------
def karyawan_profile(k_id):
    conn = connect_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT id_karyawan, username, tanggal_lahir, no_telp, email, status_karyawan FROM karyawan WHERE id_karyawan=%s;", (k_id,))
        r = cur.fetchone(); clear_screen(); print(Fore.CYAN + "=== PROFIL KARYAWAN ===")
        if r:
            rows = [(r[0], r[1], str(r[2]), r[3], r[4], r[5])]
            print_table(rows, ["ID Karyawan","Username","Tanggal Lahir","No. Telepon","Email","Aktif"])
        else:
            questionary.print("Profil tidak ditemukan", style="fg:yellow")
    except Exception as e:
        questionary.print(f"[ERROR] {e}", style="fg:red")
    finally:
        cur.close(); conn.close(); questionary.text("ENTER", default="").ask()

def karyawan_view_pending_and_confirm(k_id):
    conn = connect_db(); cur = conn.cursor()
    try:
        clear_screen(); print(Fore.CYAN + "=== TRANSAKSI PENDING ===")
        cur.execute("""
            SELECT DISTINCT t.id_transaksi, t.tanggal_transaksi, p.id_pelanggan, p.username
            FROM transaksi t
            JOIN detail_transaksi d ON t.id_transaksi = d.id_transaksi
            LEFT JOIN pelanggan p ON t.id_pelanggan = p.id_pelanggan
            WHERE t.status_terkonfirmasi = false
            ORDER BY t.id_transaksi;
        """)
        rows = cur.fetchall()
        if not rows:
            print("Tidak ada transaksi pending."); questionary.text("ENTER", default="").ask(); return
        print_table(rows, ["ID Trans","Tanggal","ID Pel","Pelanggan"])
        tid_s = questionary.text("Masukkan ID transaksi untuk konfirmasi (0 = batal):", style=qstyle).ask()
        if not tid_s or not tid_s.isdigit(): cur.close(); conn.close(); return
        tid = int(tid_s)
        if tid == 0: cur.close(); conn.close(); return
        cur.execute("UPDATE transaksi SET status_terkonfirmasi = true WHERE id_transaksi = %s;", (tid,))
        # optionally mark transaksi.status_terkonfirmasi true
        cur.execute("UPDATE transaksi SET status_terkonfirmasi = true WHERE id_transaksi = %s;", (tid,))
        conn.commit() 
        questionary.print(f"[OK] Transaksi ID {tid} dikonfirmasi (Siap diambil!).", style="fg:green")
    except Exception as e:
        conn.rollback(); questionary.print(f"[ERROR] {e}", style="fg:red")
    finally:
        cur.close(); conn.close(); time.sleep(0.3)

def karyawan_report(k_id):
    conn = connect_db()
    if not conn:
        return
    cur = conn.cursor()
    try:
        clear_screen()
        print(Fore.CYAN + "=== LAPORAN KARYAWAN (TRANSAKSI YANG DITANGANI) ===")
        
        cur.execute("""
            SELECT 
                t.id_transaksi, 
                t.tanggal_transaksi, 
                t.status_terkonfirmasi, 
                COALESCE(
                    (SELECT SUM((d.harga * d.quantity) - ((d.harga * d.quantity) * d.dicount / 100))
                     FROM detail_transaksi d 
                     WHERE d.id_transaksi = t.id_transaksi), 
                    0
                ) as total 
            FROM transaksi t 
            WHERE t.id_karyawan = %s 
            ORDER BY t.tanggal_transaksi DESC;
        """, (k_id,))
        
        rows = cur.fetchall()
        print_table(rows, ["ID Trans", "Tanggal", "Status", "Total (Rp)"])
    except Exception as e:
        questionary.print(f"[ERROR] {e}", style="fg:red")
    finally:
        cur.close()
        conn.close()
        questionary.text("ENTER", default="").ask()

# --------------------------
# PELANGGAN: CATALOG, CART, CHECKOUT, HISTORY
# --------------------------
def view_catalog_for_customer(conn):
    cur = conn.cursor()
    cur.execute("""
        SELECT p.id_produk, p.nama_produk, p.stock_produk, p.harga_produk, COALESCE(k.jenis_kategori,'-')
        FROM produk p LEFT JOIN kategori k ON p.id_kategori = k.id_kategori
        WHERE p.hapus_produk = false
        ORDER BY p.id_produk;
    """)
    rows = cur.fetchall(); cur.close(); return rows

def create_transaction_for_customer(conn, id_pelanggan):
    cur = conn.cursor()
    try:
        # count previous transactions for that pelanggan
        cur.execute("SELECT COUNT(*) FROM transaksi WHERE id_pelanggan = %s;", (id_pelanggan,))
        prev_count = cur.fetchone()[0] or 0
        pembelian_ke = prev_count + 1
        disc = get_discount_for_purchase_count(pembelian_ke)

        # choose a karyawan
        cur.execute("SELECT id_karyawan FROM karyawan WHERE status_karyawan = true LIMIT 1;")
        r = cur.fetchone()
        if not r:
            questionary.print("Belum ada karyawan aktif. Hubungi admin.", style="fg:red"); cur.close(); return None, 0
        id_karyawan = r[0]

        cur.execute("INSERT INTO transaksi (tanggal_transaksi, status_terkonfirmasi, id_karyawan, id_pelanggan) VALUES (%s,%s,%s,%s) RETURNING id_transaksi;",
                    (date.today(), False, id_karyawan, id_pelanggan))
        tid = cur.fetchone()[0]; conn.commit()
        return tid, disc
    except Exception as e:
        conn.rollback(); questionary.print(f"[ERROR] buat transaksi: {e}", style="fg:red"); return None, 0
    finally:
        cur.close()

def add_detail_transaction(conn, tid, pid, qty, disc):
    cur = conn.cursor()
    try:
        cur.execute("SELECT harga_produk, stock_produk FROM produk WHERE id_produk=%s FOR UPDATE;", (pid,))
        r = cur.fetchone()
        if not r:
            questionary.print("Produk tidak ditemukan.", style="fg:red"); cur.close(); return False
        harga, stock = r
        if qty > stock:
            questionary.print("Stok tidak mencukupi.", style="fg:red"); cur.close(); return False
        cur.execute("INSERT INTO detail_transaksi (dicount, quantity, harga, id_transaksi, id_produk) VALUES (%s,%s,%s,%s,%s) RETURNING id_detail_transaksi;", (disc, qty, harga, tid, pid))
        did = cur.fetchone()[0]
        cur.execute("UPDATE produk SET stock_produk = stock_produk - %s WHERE id_produk=%s;", (qty, pid))
        conn.commit()
        questionary.print(f"[OK] Item ditambahkan ke transaksi. Detail ID: {did}", style="fg:green")
        cur.close(); return True
    except Exception as e:
        conn.rollback(); questionary.print(f"[ERROR] {e}", style="fg:red"); cur.close(); return False

def pelanggan_shopping_flow(id_pelanggan):
    conn = connect_db()
    if not conn:
        return
    cart = []
    try:
        while True:
            clear_screen(); print(Fore.CYAN + "=== BELANJA (KATALOG) ===")
            products = view_catalog_for_customer(conn)
            if not products:
                print("Belum ada produk."); questionary.text("ENTER", default="").ask(); return
            print_table(products, ["ID","Nama","Stok","Harga","Kategori"])
            # show cart summary
            if cart:
                print("Keranjang:")
                total_est = 0
                for i,it in enumerate(cart,1):
                    line_total = it["qty"] * it["price"]
                    total_est += line_total
                    print(f"{i}. {it['name']} x{it['qty']} | Rp{it['price']} each | Subtotal Rp{line_total}")
                print(f"Estimasi total (sebelum diskon): Rp{total_est}")
            action = questionary.select("Aksi:", choices=["Tambah (by ID)","Checkout","Batal"], style=qstyle).ask()
            if action == "Batal":
                break
            if action == "Tambah (by ID)":
                pid_s = questionary.text("Masukkan ID produk:", style=qstyle).ask()
                if not pid_s or not pid_s.isdigit():
                    questionary.print("ID tidak valid.", style="fg:red"); time.sleep(0.5); continue
                pid = int(pid_s)
                prod = next((p for p in products if p[0] == pid), None)
                if not prod:
                    questionary.print("Produk tidak ditemukan.", style="fg:red"); time.sleep(0.5); continue
                qty_s = questionary.text("Jumlah:", style=qstyle).ask()
                if not qty_s or not qty_s.isdigit():
                    questionary.print("Jumlah harus angka.", style="fg:red"); time.sleep(0.5); continue
                qty = int(qty_s)
                if qty <= 0:
                    questionary.print("Jumlah harus > 0", style="fg:red"); time.sleep(0.5); continue
                if qty > prod[2]:
                    questionary.print("Stok tidak mencukupi.", style="fg:red"); time.sleep(0.5); continue
                cart.append({"id": pid, "name": prod[1], "qty": qty, "price": prod[3]})
                questionary.print("Item ditambahkan ke keranjang.", style="fg:green")
                time.sleep(0.5)
            elif action == "Checkout":
                if not cart:
                    questionary.print("Keranjang kosong.", style="fg:yellow"); time.sleep(0.6); continue
                tid, disc = create_transaction_for_customer(conn, id_pelanggan)
                if not tid:
                    questionary.print("Gagal membuat transaksi.", style="fg:red"); time.sleep(0.6); continue
                ok_all = True
                for it in cart:
                    ok = add_detail_transaction(conn, tid, it["id"], it["qty"], disc)
                    if not ok:
                        ok_all = False
                if ok_all:
                    questionary.print(f"[OK] Checkout berhasil. Transaksi ID: {tid}. Diskon: {disc}%", style="fg:green")
                else:
                    questionary.print("[WARN] Beberapa item gagal ditambahkan.", style="fg:yellow")
                questionary.text("ENTER untuk kembali", default="").ask()
                break
    except Exception as e:
        questionary.print(f"[ERROR] {e}", style="fg:red")
    finally:
        conn.close()

def pelanggan_view_history(id_pelanggan):
    conn = connect_db()
    if not conn:
        return
    cur = conn.cursor()
    try:
        clear_screen(); print(Fore.CYAN + "=== RIWAYAT TRANSAKSI ===")
        cur.execute("SELECT id_transaksi, tanggal_transaksi, status_terkonfirmasi FROM transaksi WHERE id_pelanggan=%s ORDER BY id_transaksi DESC;", (id_pelanggan,))
        trans = cur.fetchall()
        if not trans:
            print(Fore.YELLOW + "Belum ada riwayat transaksi."); questionary.text("ENTER untuk kembali", default="").ask(); return

        # For each transaction, fetch items
        out_summary = []
        for t in trans:
            tid, tgl, stat = t
            # total and items
            cur.execute("SELECT dt.id_detail_transaksi, pr.nama_produk, dt.quantity, dt.harga, dt.dicount, t.status_terkonfirmasi FROM detail_transaksi dt JOIN produk pr ON dt.id_produk=pr.id_produk join transaksi t on t.id_transaksi = dt.id_transaksi WHERE dt.id_transaksi=%s;", (tid,))
            items = cur.fetchall()
            total = 0
            for it in items:
                price = it[3] or 0
                qty = it[2] or 0
                disc = it[4] or 0
                subtotal = (price * qty) - ((price * qty) * disc / 100)
                total += subtotal
            status_text = "Siap diambil!" if stat else "Pending"
            out_summary.append((tid, str(tgl), status_text, int(total)))
        # Print summary table
        print_table(out_summary, ["ID Trans", "Tanggal", "Status", "Total (Rp)"])
        # Ask whether show details
        if questionary.confirm("Lihat detail items untuk transaksi tertentu?", default=False).ask():
            tid_q = questionary.text("Masukkan ID Transaksi:", style=qstyle).ask()
            if not tid_q.isdigit(): questionary.print("ID tidak valid", style="fg:red"); return
            tid = int(tid_q)
            cur.execute("SELECT dt.id_detail_transaksi, pr.nama_produk, dt.quantity, dt.harga, dt.dicount, t.status_terkonfirmasi FROM detail_transaksi dt JOIN produk pr ON dt.id_produk=pr.id_produk join transaksi t on t.id_transaksi = dt.id_transaksi WHERE dt.id_transaksi=%s;", (tid,))
            items = cur.fetchall()
            if not items:
                questionary.print("Tidak ada detail untuk transaksi ini.", style="fg:yellow"); return
            # format items table
            # map boolean status_terkonfirmasi to text
            items_formatted = []
            for it in items:
                stat = "Terkonfirmasi" if it[5] else "Belum"
                items_formatted.append((it[0], it[1], it[2], it[3], it[4], stat))
            print_table(items_formatted, ["ID Detail","Produk","Qty","Harga Satuan","Diskon%","Status"])
    except Exception as e:
        questionary.print(f"[ERROR] {e}", style="fg:red")
    finally:
        cur.close(); conn.close(); questionary.text("ENTER untuk kembali", default="").ask()

# --------------------------
# DASHBOARDS / ROUTING
# --------------------------
def admin_dashboard_loop(admin_id):
    while True:
        print_title()
        action = questionary.select("ADMIN MENU:", choices=[
            "Profil",
            "Kelola Produk",
            "Kelola Kategori",
            "Kelola Karyawan",
            "Lihat Akun Pelanggan",
            "Daftar Semua Akun (ringkasan)",
            "Laporan Keuangan",
            "Logout"
        ], style=qstyle).ask()
        if action == "Profil":
            admin_profile(admin_id)
        elif action == "Kelola Produk":
            while True:
                sub = questionary.select("Kelola Produk:", choices=["Tambah Produk","Lihat (aktif)","Lihat (semua)","Update Produk","Non-aktifkan Produk","Back"], style=qstyle).ask()
                if sub=="Tambah Produk": admin_add_product(admin_id)
                elif sub=="Lihat (aktif)": admin_list_products(show_all=False)
                elif sub=="Lihat (semua)": admin_list_products(show_all=True)
                elif sub=="Update Produk": admin_update_product(admin_id)
                elif sub=="Non-aktifkan Produk": admin_soft_delete_product()
                else: break
        elif action == "Kelola Kategori":
            while True:
                c = questionary.select("Kategori:", choices=["Lihat","Tambah","Back"], style=qstyle).ask()
                if c == "Lihat":
                    conn = connect_db(); cats = list_categories(conn); conn.close(); clear_screen(); print(Fore.CYAN + "=== KATEGORI ==="); print_table(cats, ["ID","Kategori"]); questionary.text("ENTER", default="").ask()
                elif c == "Tambah": conn = connect_db(); add_category(conn); conn.close()
                else: break
        elif action == "Kelola Karyawan":
            while True:
                k = questionary.select("Kelola Karyawan:", choices=["List Karyawan","Tambah Karyawan","Update Karyawan","Hapus Karyawan","Back"], style=qstyle).ask()
                if k == "List Karyawan": admin_list_karyawan()
                elif k == "Tambah Karyawan": admin_add_karyawan(admin_id)
                elif k == "Update Karyawan": admin_update_karyawan()
                elif k == "Hapus Karyawan": admin_delete_karyawan()
                else: break
        elif action == "Lihat Akun Pelanggan":
            admin_list_pelanggan()
        elif action == "Daftar Semua Akun (ringkasan)":
            list_semua_akun()
        elif action == "Laporan Keuangan":
            admin_report_transactions()
        else:
            break

def karyawan_dashboard_loop(k_id):
    while True:
        print_title()
        action = questionary.select("KARYAWAN MENU:", choices=["Profil","Layani Transaksi (Pending)","Laporan Karyawan","Lihat Katalog","Logout"], style=qstyle).ask()
        if action == "Profil": karyawan_profile(k_id)
        elif action == "Layani Transaksi (Pending)": karyawan_view_pending_and_confirm(k_id)
        elif action == "Laporan Karyawan": karyawan_report(k_id)
        elif action == "Lihat Katalog":
            conn = connect_db(); rows = view_catalog_for_customer(conn); conn.close(); clear_screen(); print(Fore.CYAN + "=== KATALOG ==="); print_table(rows, ["ID","Nama","Stok","Harga","Kategori"]); questionary.text("ENTER", default="").ask()
        else: break

def pelanggan_dashboard_loop(p_id):
    while True:
        print_title()
        action = questionary.select("PELANGGAN MENU:", choices=["Profil","Belanja (Katalog + Cart)","Riwayat Transaksi","Logout"], style=qstyle).ask()
        if action == "Profil":
            conn = connect_db(); cur = conn.cursor(); cur.execute("SELECT id_pelanggan, username, tanggal_lahir, no_telp, email FROM pelanggan WHERE id_pelanggan=%s;", (p_id,)); r=cur.fetchone(); clear_screen(); print(Fore.CYAN + "=== PROFIL ===")
            if r: print_table([(r[0], r[1], str(r[2]), r[3], r[4])], ["ID Pelanggan","Username","Tanggal Lahir","No. Telepon","Email"])
            else: questionary.print("Profil tidak ditemukan", style="fg:yellow")
            cur.close(); conn.close(); questionary.text("ENTER", default="").ask()
        elif action == "Belanja (Katalog + Cart)":
            pelanggan_shopping_flow(p_id)
        elif action == "Riwayat Transaksi":
            pelanggan_view_history(p_id)
        else:
            break


def list_semua_akun():
    conn = connect_db()
    if not conn:
        return
    cur = conn.cursor()
    try:
        clear_screen(); print(Fore.CYAN + "=== DAFTAR AKUN ADMIN ===")
        cur.execute("SELECT id_admin, username, no_telp, email FROM adminn ORDER BY id_admin;"); rows_admin = cur.fetchall(); print_table(rows_admin, ["ID Admin","Username","Telp","Email"])
        print(Fore.CYAN + "\n=== DAFTAR KARYAWAN ===")
        cur.execute("SELECT id_karyawan, username, no_telp, email, status_karyawan FROM karyawan ORDER BY id_karyawan;"); rows_k = cur.fetchall(); print_table(rows_k, ["ID Karyawan","Username","Telp","Email","Aktif"])
        print(Fore.CYAN + "\n=== DAFTAR PELANGGAN ===")
        cur.execute("SELECT id_pelanggan, username, no_telp, email FROM pelanggan ORDER BY id_pelanggan;"); rows_p = cur.fetchall(); print_table(rows_p, ["ID Pelanggan","Username","Telp","Email"])
    except Exception as e:
        questionary.print(f"[ERROR] {e}", style="fg:red")
    finally:
        cur.close(); conn.close(); questionary.text("ENTER untuk kembali", default="").ask()

# --------------------------
# MAIN MENU
# --------------------------
def main_menu():
    inialisasi_database()
    while True:
        print_title()
        action = questionary.select("Menu Utama:", choices=["Login", "Register (Pelanggan)", "Keluar"], style=qstyle).ask()
        if action == "Login":
            role, uid = login()
            if role == "admin": admin_dashboard_loop(uid)
            elif role == "karyawan": karyawan_dashboard_loop(uid)
            elif role == "pelanggan": pelanggan_dashboard_loop(uid)
            else: continue
        elif action == "Register (Pelanggan)":
            register_pelanggan()
        else:
            print("Keluar..."); break

#RUN THE PROGRAM BRO
main_menu()
