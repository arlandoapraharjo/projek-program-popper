import pyfiglet
import time
from colorama import Fore, Back, Style ,init
import questionary
from questionary import Style as stq
import pandas as pd
import os
import psycopg2

init(autoreset=True)


def halaman_judul():
    init(autoreset=True)
judul = pyfiglet.figlet_format("Popper", font="ansi_shadow")
for char in judul:
    print(Fore.GREEN + char, end="", flush=True)
    time.sleep(0.004)
    

def judul_menu():
    judul_menu = (pyfiglet.figlet_format("Popper", font="ansi_shadow"))
    print("")
    print(Fore.GREEN + judul_menu)


def clear_screen():
    if os.name == 'nt':
        os.system ('cls')


def connect_db():
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="sistem_popper",
            user="postgres",
            password="yourpassword",
            port="5432"
        )
        return conn
    except Exception as e:
        print("Gagal terhubung ke database:", e)
        return None


# REGISTER FITUR
def register():
    clear_screen()
    print(pyfiglet.figlet_format("Popper", font="ansi_shadow"))

    username = questionary.text("Masukkan Username:").ask()
    password = questionary.text("Masukkan Password:").ask()
    tgl_lahir = questionary.text("Masukkan Tanggal Lahir (YYYY-MM-DD):").ask()
    no_telp = questionary.text("Masukkan No Telepon:").ask()
    email = questionary.text("Masukkan Email:").ask()

    conn = connect_db()
    if conn is None:
        print("Tidak bisa terhubung ke database.")
        return

    cur = conn.cursor()

    try:
        # pelanggan baru belum punya transaksi → set ke NULL atau skip field
        cur.execute("""
            INSERT INTO pelanggan (username, pass_pelanggan, tanggal_lahir, no_telp, email, id_transaksi)
            VALUES (%s, %s, %s, %s, %s, NULL)
        """, (username, password, tgl_lahir, no_telp, email))

        conn.commit()
        print("\nAkun berhasil didaftarkan!")

    except Exception as e:
        print("\nTerjadi error saat register:", e)

    finally:
        cur.close()
        conn.close()

    input("\nTekan ENTER untuk kembali ke menu...")



# LOGIN FITUR
def login():
    clear_screen()
    print("=== LOGIN SISTEM ===")

    username = questionary.text("Masukkan Username:").ask()
    password = questionary.text("Masukkan Password:").ask()

    conn = connect_db()
    if conn is None:
        print("Tidak bisa terhubung ke database.")
        return None, None

    cur = conn.cursor()

    # Prioritas login: Admin → Karyawan → Pelanggan
    try:
        # ADMIN
        cur.execute("SELECT id_admin FROM adminn WHERE username=%s AND pass_admin=%s",
                    (username, password))
        admin = cur.fetchone()
        if admin:
            print("\nLogin berhasil sebagai ADMIN!")
            cur.close(); conn.close()
            return "admin", admin[0]

        # KARYAWAN
        cur.execute("SELECT id_karyawan FROM karyawan WHERE username=%s AND pass_karyawan=%s",
                    (username, password))
        karyawan = cur.fetchone()
        if karyawan:
            print("\nLogin berhasil sebagai KARYAWAN!")
            cur.close(); conn.close()
            return "karyawan", karyawan[0]

        # PELANGGAN
        cur.execute("SELECT id_pelanggan FROM pelanggan WHERE username=%s AND pass_pelanggan=%s",
                    (username, password))
        pelanggan = cur.fetchone()
        if pelanggan:
            print("\nLogin berhasil sebagai PELANGGAN!")
            cur.close(); conn.close()
            return "pelanggan", pelanggan[0]

        print("\nLogin gagal! Username atau password salah.")

    except Exception as e:
        print("Error saat login:", e)

    finally:
        cur.close()
        conn.close()

    input("\nTekan ENTER untuk kembali ke menu...")
    return None, None

# ----------------------------------------------------
# LIHAT PROFIL ADMIN
# ----------------------------------------------------
def admin_profile(conn, id_admin):
    clear_screen()
    print("===== PROFIL ADMIN =====")

    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT username, tanggal_lahir, no_telp, email
            FROM adminn
            WHERE id_admin = %s
        """, (id_admin,))

        data = cur.fetchone()

        if data:
            print(f"\nUsername       : {data[0]}")
            print(f"Tanggal Lahir  : {data[1]}")
            print(f"No. Telepon    : {data[2]}")
            print(f"Email          : {data[3]}")
        else:
            print("Data admin tidak ditemukan.")

    except Exception as e:
        print("[ERROR] Tidak bisa mengambil data admin:", e)

    input("\nTekan ENTER untuk kembali...")


# ----------------------------------------------------
# MENU KELOLA PRODUK (TEMPLATE AWAL)
# ----------------------------------------------------
def menu_kelola_produk(conn, id_admin):
    while True:
        clear_screen()
        print("""
===== KELOLA PRODUK =====
1. Tambah Produk
2. Lihat Produk
3. Update Produk
4. Hapus Produk
5. Kembali
""")

        pilih = input("Pilih menu: ")

        if pilih == "1":
            print("FITUR TAMBAH PRODUK (akan kita isi nanti)")
            input("ENTER...")

        elif pilih == "2":
            print("FITUR LIHAT PRODUK (akan kita isi nanti)")
            input("ENTER...")

        elif pilih == "3":
            print("FITUR UPDATE PRODUK (akan kita isi nanti)")
            input("ENTER...")

        elif pilih == "4":
            print("FITUR HAPUS PRODUK (akan kita isi nanti)")
            input("ENTER...")

        elif pilih == "5":
            break
        else:
            print("Pilihan tidak valid!")
            input("ENTER...")


# ----------------------------------------------------
# MENU UTAMA ADMIN
# ----------------------------------------------------
def menu_admin(conn, id_admin):
    while True:
        clear_screen()
        print("""
=========== DASHBOARD ADMIN ===========
1. Lihat Profil Admin
2. Kelola Produk
3. Kelola Karyawan   (akan dibuat setelah ini)
4. Laporan Transaksi (akan dibuat setelah ini)
5. Logout
""")

        pilih = input("Pilih menu: ")

        if pilih == "1":
            admin_profile(conn, id_admin)

        elif pilih == "2":
            menu_kelola_produk(conn, id_admin)

        elif pilih == "3":
            print("FITUR KELOLA KARYAWAN (akan kita isi)")
            input("ENTER...")

        elif pilih == "4":
            print("FITUR LAPORAN TRANSAKSI (akan kita isi)")
            input("ENTER...")

        elif pilih == "5":
            break

        else:
            print("Pilihan tidak valid!")
            input("ENTER...")



# =============================
# FITUR: LIHAT KATALOG (SEMUA ROLE)
# =============================
def lihat_katalog():
    clear_screen()
    conn = connect_db()
    cur = conn.cursor()

    cur.execute("SELECT product_id, product_name, stock, price FROM products ORDER BY product_id")
    rows = cur.fetchall()

    print("===== KATALOG PRODUK =====\n")
    if not rows:
        print("Belum ada produk.")
    else:
        for row in rows:
            print(f"ID: {row[0]} | Nama: {row[1]} | Stok: {row[2]} | Harga: Rp{row[3]}")
    print()
    
    cur.close()
    conn.close()
    input("Tekan Enter untuk kembali...")


# =============================
# FITUR: TAMBAH PRODUK
# =============================
def tambah_produk():
    clear_screen()
    conn = connect_db()
    cur = conn.cursor()

    print("===== TAMBAH PRODUK =====")
    nama = input("Nama produk baru: ")
    stok = int(input("Stok awal: "))
    harga = float(input("Harga per item: "))

    query = """
        INSERT INTO products (product_name, stock, price)
        VALUES (%s, %s, %s)
    """

    cur.execute(query, (nama, stok, harga))
    conn.commit()

    print("\nProduk berhasil ditambahkan!")
    cur.close()
    conn.close()
    input("Tekan Enter untuk kembali...")


# =============================
# FITUR: LIHAT PRODUK
# =============================
def lihat_produk():
    clear_screen()
    conn = connect_db()
    cur = conn.cursor()

    cur.execute("SELECT product_id, product_name, stock, price FROM products ORDER BY product_id")
    rows = cur.fetchall()

    print("===== DAFTAR PRODUK =====\n")
    if not rows:
        print("Belum ada produk.")
    else:
        for row in rows:
            print(f"ID: {row[0]} | Nama: {row[1]} | Stok: {row[2]} | Harga: Rp{row[3]}")

    print()
    cur.close()
    conn.close()
    input("Tekan Enter untuk kembali...")


# =============================
# FITUR: UPDATE PRODUK
# =============================
def update_produk():
    clear_screen()
    conn = connect_db()
    cur = conn.cursor()

    print("===== UPDATE PRODUK =====")
    product_id = input("Masukkan ID produk: ")

    # cek apakah produk ada
    cur.execute("SELECT product_name, stock, price FROM products WHERE product_id = %s", (product_id,))
    data = cur.fetchone()

    if not data:
        print("\nProduk tidak ditemukan!")
        input("Tekan Enter untuk kembali...")
        return

    print(f"\nNama lama: {data[0]}")
    print(f"Stok lama: {data[1]}")
    print(f"Harga lama: Rp{data[2]}")

    nama = input("Nama baru (Enter = tetap): ") or data[0]
    stok = input("Stok baru (Enter = tetap): ")
    stok = int(stok) if stok else data[1]
    harga = input("Harga baru (Enter = tetap): ")
    harga = float(harga) if harga else data[2]

    query = """
        UPDATE products
        SET product_name = %s, stock = %s, price = %s
        WHERE product_id = %s
    """

    cur.execute(query, (nama, stok, harga, product_id))
    conn.commit()

    print("\nProduk berhasil diperbarui!")
    cur.close()
    conn.close()
    input("Tekan Enter untuk kembali...")


# =============================
# FITUR: HAPUS PRODUK
# =============================
def hapus_produk():
    clear_screen()
    conn = connect_db()
    cur = conn.cursor()

    print("===== HAPUS PRODUK =====")
    product_id = input("Masukkan ID produk: ")

    cur.execute("SELECT product_name FROM products WHERE product_id = %s", (product_id,))
    data = cur.fetchone()

    if not data:
        print("\nProduk tidak ditemukan!")
        input("Tekan Enter untuk kembali...")
        return

    konfirmasi = input(f"Hapus produk '{data[0]}'? (y/n): ").lower()
    if konfirmasi == "y":
        cur.execute("DELETE FROM products WHERE product_id = %s", (product_id,))
        conn.commit()
        print("\nProduk berhasil dihapus!")
    else:
        print("\nDibatalkan.")

    cur.close()
    conn.close()
    input("Tekan Enter untuk kembali...")


# =============================
# FITUR: DAFTAR SEMUA AKUN
# =============================
def daftar_semua_akun():
    clear_screen()
    conn = connect_db()
    cur = conn.cursor()

    print("===== DAFTAR SEMUA AKUN =====\n")

    cur.execute("SELECT user_id, username, role FROM users ORDER BY user_id")
    rows = cur.fetchall()

    if not rows:
        print("Belum ada akun.")
    else:
        for r in rows:
            print(f"ID: {r[0]} | Username: {r[1]} | Role: {r[2]}")

    print()
    cur.close()
    conn.close()
    input("Tekan Enter untuk kembali...")










# MENU UTAMA
def main_menu():
    while True:
        clear_screen()
        judul_menu() #judul di main menu
        print(Style.BRIGHT + "========================================")
        print(Fore.CYAN + "Selamat datang!")
        action = questionary.select( "Pilih Menu:", choices=[
            "Login",
            "Register (pelanggan)",
            "Keluar"  #tampilan colorama error karena tidak diinisialisasi di awal 
        ]).ask()
        
        if action == 'Keluar':
            print("Keluar dari aplikasi...")
            time.sleep(0.7)
            break
        
        elif action == 'Login':
            role, user_id = login()

            if role == "admin":
                conn = connect_db()
                menu_admin(conn, user_id)

            elif role == "karyawan":
                print("\nLogin sebagai karyawan! (Dashboard menyusul)")
                time.sleep(1)

            elif role == "pelanggan":
                print("\nLogin sebagai pelanggan! (Dashboard menyusul)")
                time.sleep(1)
           
                   
        elif action == 'Register (pelanggan)':
            register()


# RUN PROGRAM
main_menu()


