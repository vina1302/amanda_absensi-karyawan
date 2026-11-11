from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash
)

from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

import mysql.connector
from datetime import datetime, timedelta

import os
import base64
import uuid
import traceback

import cv2
import numpy as np

# Muat TensorFlow terlebih dahulu
import tensorflow as tf
import tensorflow.keras

# Setelah itu muat DeepFace
from deepface import DeepFace


app = Flask(__name__)

app.secret_key = "secret_absensi_2026"


# KONFIGURASI
FACE_FOLDER = os.path.join(
    app.instance_path,
    "wajah"
)

os.makedirs(
    FACE_FOLDER,
    exist_ok=True
)

# KONFIGURASI UPLOAD BUKTI IZIN

IZIN_FOLDER = os.path.join(
    app.static_folder,
    "uploads",
    "izin"
)

os.makedirs(IZIN_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {
    "jpg",
    "jpeg",
    "png",
    "pdf"
}

app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024


def file_izin_diizinkan(nama_file):
    return (
        "." in nama_file
        and nama_file.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )

# KONEKSI DATABASE

def get_db():

    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="db_sistem_absensi"
    )


# HELPER - SIMPAN FOTO DARI BASE64

def simpan_foto_base64(foto):

    if not foto:
        return None

    try:

        if "," in foto:
            foto = foto.split(",", 1)[1]

        data = base64.b64decode(foto)

        nama_file = (
            str(uuid.uuid4())
            + ".jpg"
        )

        path = os.path.join(
            FACE_FOLDER,
            nama_file
        )

        with open(path, "wb") as file:
            file.write(data)

        return path

    except Exception as e:

        print(
            "Gagal menyimpan foto:",
            e
        )
        return None



# HELPER - BACA GAMBAR DENGAN OPENCV
def baca_foto_opencv(path):
    """
    Membaca gambar sebagai array BGR yang kompatibel dengan DeepFace.
    np.fromfile + cv2.imdecode membantu pembacaan path Windows.
    """
    if not path or not os.path.isfile(path):
        raise FileNotFoundError(f"File gambar tidak ditemukan: {path}")

    data = np.fromfile(path, dtype=np.uint8)
    gambar = cv2.imdecode(data, cv2.IMREAD_COLOR)

    if gambar is None:
        raise ValueError(f"File bukan gambar yang valid: {path}")

    return np.ascontiguousarray(gambar)

# HALAMAN SELAMAT DATANG

@app.route("/")
def welcome():

    # Jika pengguna sudah login, langsung ke dashboard
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    return render_template("welcome.html")

# LOGIN ADMIN

@app.route("/login_admin", methods=["GET", "POST"])
def login_admin():

    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        db = get_db()
        cursor = db.cursor(dictionary=True)

        try:
            cursor.execute("""
                SELECT *
                FROM users
                WHERE username = %s
                AND role = 'admin'
            """, (username,))

            user = cursor.fetchone()

            if user:

                password_db = user["password"]

                password_benar = False

                try:
                    password_benar = check_password_hash(
                        password_db,
                        password
                    )
                except ValueError:
                    password_benar = False

                # Untuk password lama yang masih berupa teks biasa
                if not password_benar and password_db == password:

                    password_benar = True

                    password_hash = generate_password_hash(password)

                    cursor.execute("""
                        UPDATE users
                        SET password = %s
                        WHERE id = %s
                    """, (
                        password_hash,
                        user["id"]
                    ))

                    db.commit()

                if password_benar:

                    session["user_id"] = user["id"]
                    session["nama"] = user["nama"]
                    session["role"] = user["role"]
                    session["jabatan"] = user["jabatan"]

                    return redirect(url_for("dashboard"))

            flash(
                "Username atau password admin salah!",
                "danger"
            )

        except mysql.connector.Error as e:

            db.rollback()
            print("Login admin error:", e)

            flash(
                "Terjadi kesalahan saat login admin!",
                "danger"
            )

        finally:
            cursor.close()
            db.close()

    return render_template("login_admin.html")


# LOGIN KARYAWAN

@app.route("/login_karyawan", methods=["GET", "POST"])
def login_karyawan():

    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        db = get_db()
        cursor = db.cursor(dictionary=True)

        try:
            cursor.execute("""
                SELECT *
                FROM users
                WHERE username = %s
                AND role = 'karyawan'
            """, (username,))

            user = cursor.fetchone()

            if user:

                password_db = user["password"]

                password_benar = False

                try:
                    password_benar = check_password_hash(
                        password_db,
                        password
                    )
                except ValueError:
                    password_benar = False

                # Untuk password lama yang masih berupa teks biasa
                if not password_benar and password_db == password:

                    password_benar = True

                    password_hash = generate_password_hash(password)

                    cursor.execute("""
                        UPDATE users
                        SET password = %s
                        WHERE id = %s
                    """, (
                        password_hash,
                        user["id"]
                    ))

                    db.commit()

                if password_benar:

                    session["user_id"] = user["id"]
                    session["nama"] = user["nama"]
                    session["role"] = user["role"]
                    session["jabatan"] = user["jabatan"]

                    return redirect(url_for("dashboard"))

            flash(
                "Username atau password karyawan salah!",
                "danger"
            )

        except mysql.connector.Error as e:

            db.rollback()
            print("Login karyawan error:", e)

            flash(
                "Terjadi kesalahan saat login karyawan!",
                "danger"
            )

        finally:
            cursor.close()
            db.close()

    return render_template("login_karyawan.html")


    if "user_id" in session:

        return redirect(
            url_for("dashboard")
        )

    if request.method == "POST":

        username = request.form["username"].strip()
        password = request.form["password"]

        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute("""
            SELECT *
            FROM users
            WHERE username = %s
            AND role = 'karyawan'
        """, (username,))

        user = cursor.fetchone()

        if user:

            password_db = user["password"]

            password_benar = False

            try:

                password_benar = check_password_hash(
                    password_db,
                    password
                )

            except ValueError:

                password_benar = False


            # Password lama berupa teks biasa

            if not password_benar and password_db == password:

                password_benar = True

                password_hash = generate_password_hash(
                    password
                )

                cursor.execute("""
                    UPDATE users
                    SET password = %s
                    WHERE id = %s
                """, (
                    password_hash,
                    user["id"]
                ))

                db.commit()


            if password_benar:

                session["user_id"] = user["id"]
                session["nama"] = user["nama"]
                session["role"] = user["role"]
                session["jabatan"] = user["jabatan"]

                cursor.close()
                db.close()

                return redirect(
                    url_for("dashboard")
                )


        cursor.close()
        db.close()

        flash(
            "Username atau password karyawan salah!",
            "danger"
        )


    return render_template(
        "login_karyawan.html"
    )


# REGISTRASI KARYAWAN

@app.route(
    "/register_karyawan",
    methods=["GET", "POST"]
)
def register_karyawan():

    if "user_id" in session:

        return redirect(
            url_for("dashboard")
        )

    if request.method == "POST":

        nama = request.form["nama"].strip()
        jabatan = request.form["jabatan"].strip()
        username = request.form["username"].strip()
        password = request.form["password"]
        konfirmasi_password = request.form[
            "konfirmasi_password"
        ]


        if not nama:

            flash(
                "Nama lengkap harus diisi!",
                "danger"
            )

            return render_template(
                "register_karyawan.html"
            )


        if not jabatan:

            flash(
                "Jabatan harus diisi!",
                "danger"
            )

            return render_template(
                "register_karyawan.html"
            )


        if not username:

            flash(
                "Username harus diisi!",
                "danger"
            )

            return render_template(
                "register_karyawan.html"
            )


        if not password:

            flash(
                "Password harus diisi!",
                "danger"
            )

            return render_template(
                "register_karyawan.html"
            )


        if password != konfirmasi_password:

            flash(
                "Konfirmasi password tidak sesuai!",
                "danger"
            )

            return render_template(
                "register_karyawan.html"
            )


        if len(password) < 5:

            flash(
                "Password minimal 5 karakter!",
                "danger"
            )

            return render_template(
                "register_karyawan.html"
            )


        db = get_db()
        cursor = db.cursor(dictionary=True)

        try:

            cursor.execute("""
                SELECT id
                FROM users
                WHERE username = %s
            """, (username,))

            username_lama = cursor.fetchone()


            if username_lama:

                flash(
                    "Username sudah digunakan. Silakan gunakan username lain!",
                    "danger"
                )

                cursor.close()
                db.close()

                return render_template(
                    "register_karyawan.html"
                )


            password_hash = generate_password_hash(
                password
            )


            cursor.execute("""
                INSERT INTO users
                (
                    nama,
                    username,
                    password,
                    jabatan,
                    role
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    'karyawan'
                )
            """, (
                nama,
                username,
                password_hash,
                jabatan
            ))


            db.commit()


            flash(
                "Registrasi berhasil! Silakan login menggunakan akun Anda.",
                "success"
            )


            cursor.close()
            db.close()

            return redirect(
                url_for("login_karyawan")
            )


        except mysql.connector.Error as e:

            db.rollback()

            print(
                "Registrasi error:",
                e
            )

            flash(
                "Registrasi gagal. Silakan coba lagi!",
                "danger"
            )

            cursor.close()
            db.close()


    return render_template(
        "register_karyawan.html"
    )


# LOGOUT

@app.route("/logout")
def logout():

    role = session.get("role")

    session.clear()

    if role == "karyawan":

        return redirect(
            url_for("login_karyawan")
        )

    return redirect(
        url_for("login_admin")
    )


# DASHBOARD
@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:

        return redirect(
            url_for("login_admin")
        )


    db = get_db()
    cursor = db.cursor(dictionary=True)


    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM users
        WHERE role = 'karyawan'
    """)

    total_karyawan = cursor.fetchone()["total"]


    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM absensi
        WHERE tanggal = CURDATE()
        AND status IN ('Hadir', 'Terlambat')
    """)

    hadir = cursor.fetchone()["total"]


    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM absensi
        WHERE tanggal = CURDATE()
        AND status = 'Terlambat'
    """)

    terlambat = cursor.fetchone()["total"]


    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM absensi
        WHERE tanggal = CURDATE()
        AND status = 'Izin'
    """)

    izin = cursor.fetchone()["total"]


    data_absensi = []


    if session["role"] == "admin":

        cursor.execute("""
            SELECT
                users.nama,
                users.jabatan,
                absensi.jam_masuk,
                absensi.status,
                absensi.keterangan
            FROM users

            LEFT JOIN absensi
            ON users.id = absensi.user_id
            AND absensi.tanggal = CURDATE()

            WHERE users.role = 'karyawan'

            ORDER BY users.nama ASC
        """)

        data_absensi = cursor.fetchall()


    cursor.close()
    db.close()


    return render_template(
        "dashboard.html",
        total_karyawan=total_karyawan,
        hadir=hadir,
        terlambat=terlambat,
        izin=izin,
        data_absensi=data_absensi
    )

#ABSENSI

@app.route(
    "/absensi",
    methods=["GET", "POST"]
)
def absensi():

    if "user_id" not in session:
        return redirect(url_for("login_karyawan"))

    if session["role"] != "karyawan":
        flash(
            "Absensi hanya dapat dilakukan oleh karyawan!",
            "danger"
        )
        return redirect(url_for("dashboard"))

    db = get_db()
    cursor = db.cursor(dictionary=True)

    try:
        # Ambil data karyawan
        cursor.execute("""
            SELECT id, nama, user_id, wajah, wajah_terdaftar
            FROM karyawan
            WHERE user_id = %s
            LIMIT 1
        """, (session["user_id"],))

        karyawan_data = cursor.fetchone()

        # Ambil data absensi hari ini
        cursor.execute("""
            SELECT *
            FROM absensi
            WHERE user_id = %s
            AND tanggal = CURDATE()
            LIMIT 1
        """, (session["user_id"],))

        data_hari_ini = cursor.fetchone()

        if request.method == "POST":

            aksi = request.form.get(
                "aksi", ""
            ).strip().lower()

            if aksi not in ("masuk", "pulang"):
                flash(
                    "Jenis absensi tidak valid.",
                    "danger"
                )
                return redirect(url_for("absensi"))

            # Validasi absen masuk
            if aksi == "masuk" and data_hari_ini:
                flash(
                    "Anda sudah melakukan absen masuk hari ini.",
                    "warning"
                )
                return redirect(url_for("absensi"))

            # Validasi absen pulang
            if aksi == "pulang":

                if (
                    not data_hari_ini
                    or not data_hari_ini.get("jam_masuk")
                ):
                    flash(
                        "Anda harus melakukan absen masuk terlebih dahulu.",
                        "warning"
                    )
                    return redirect(url_for("absensi"))

                if data_hari_ini.get("jam_keluar"):
                    flash(
                        "Anda sudah melakukan absen pulang hari ini.",
                        "warning"
                    )
                    return redirect(url_for("absensi"))

            # Periksa data karyawan
            if not karyawan_data:
                flash(
                    "Data karyawan belum terhubung dengan akun login. Hubungi admin.",
                    "danger"
                )
                return redirect(url_for("absensi"))

            # Periksa wajah terdaftar
            if not karyawan_data.get("wajah"):
                flash(
                    "Wajah Anda belum terdaftar. Silakan hubungi admin.",
                    "warning"
                )
                return redirect(url_for("absensi"))

            foto = request.form.get("foto")

            if not foto:
                flash(
                    "Foto wajah tidak ditemukan. Silakan gunakan kamera.",
                    "danger"
                )
                return redirect(url_for("absensi"))

            foto_sementara = simpan_foto_base64(foto)

            if not foto_sementara:
                flash(
                    "Foto wajah gagal diproses.",
                    "danger"
                )
                return redirect(url_for("absensi"))

            error_verifikasi = False
            wajah_cocok = False

            # Verifikasi wajah menggunakan DeepFace
            try:
                foto_kamera = baca_foto_opencv(
                    foto_sementara
                )

                foto_master = baca_foto_opencv(
                    karyawan_data["wajah"]
                )

                print("\n" + "=" * 60)
                print(
                    "PEMERIKSAAN GAMBAR ABSENSI -",
                    aksi.upper()
                )
                print("Foto kamera :", foto_kamera.shape)
                print("Foto master :", foto_master.shape)
                print(
                    "File master :",
                    karyawan_data["wajah"]
                )
                print("=" * 60)

                hasil = DeepFace.verify(
                    img1_path=foto_kamera,
                    img2_path=foto_master,
                    model_name="Facenet512",
                    detector_backend="opencv",
                    distance_metric="cosine",
                    enforce_detection=True,
                    align=True
                )

                print(
                    "Verified :",
                    hasil.get("verified")
                )
                print(
                    "Distance :",
                    hasil.get("distance")
                )
                print(
                    "Threshold:",
                    hasil.get("threshold")
                )

                wajah_cocok = bool(
                    hasil.get("verified", False)
                )

            except Exception as e:
                error_verifikasi = True

                print(
                    "\nDEEPFACE ERROR:",
                    type(e).__name__,
                    str(e)
                )

                traceback.print_exc()

            finally:
                try:
                    if os.path.exists(foto_sementara):
                        os.remove(foto_sementara)
                except Exception:
                    pass

            if error_verifikasi:
                flash(
                    "Verifikasi wajah gagal diproses. Periksa detail error pada terminal aplikasi.",
                    "danger"
                )
                return redirect(url_for("absensi"))

            if not wajah_cocok:
                flash(
                    "Wajah tidak cocok dengan data wajah Anda. Coba lagi dengan pencahayaan yang cukup.",
                    "danger"
                )
                return redirect(url_for("absensi"))

            sekarang = datetime.now()
            waktu = sekarang.strftime("%H:%M:%S")

            # PROSES ABSEN PULANG
            if aksi == "pulang":

                cursor.execute("""
                    UPDATE absensi
                    SET jam_keluar = %s
                    WHERE id = %s
                    AND jam_keluar IS NULL
                """, (
                    waktu,
                    data_hari_ini["id"]
                ))

                if cursor.rowcount != 1:
                    db.rollback()

                    flash(
                        "Absen pulang tidak dapat disimpan. Periksa kembali status absensi Anda.",
                        "warning"
                    )
                    return redirect(url_for("absensi"))

                db.commit()

                flash(
                    "Absen pulang berhasil! Wajah terverifikasi.",
                    "success"
                )

                return redirect(url_for("absensi"))

            # PROSES ABSEN MASUK
            jam_sekarang = sekarang.time()

            cursor.execute("""
                SELECT jam_masuk
                FROM pengaturan_absensi
                ORDER BY id DESC
                LIMIT 1
            """)

            pengaturan = cursor.fetchone()

            batas = (
                pengaturan["jam_masuk"]
                if pengaturan and pengaturan.get("jam_masuk")
                else "08:00:00"
            )

            if isinstance(batas, timedelta):

                total_detik = int(
                    batas.total_seconds()
                )

                batas = datetime.strptime(
                    f"{total_detik // 3600:02d}:"
                    f"{(total_detik % 3600) // 60:02d}:"
                    f"{total_detik % 60:02d}",
                    "%H:%M:%S"
                ).time()

            elif isinstance(batas, str):

                batas = datetime.strptime(
                    batas.split(".")[0],
                    "%H:%M:%S"
                ).time()

            elif not hasattr(batas, "hour"):

                batas = datetime.strptime(
                    "08:00:00",
                    "%H:%M:%S"
                ).time()

            if jam_sekarang > batas:
                status = "Terlambat"
                keterangan = (
                    "Datang setelah pukul "
                    + batas.strftime("%H:%M")
                )
            else:
                status = "Hadir"
                keterangan = "Datang tepat waktu"

            cursor.execute("""
                INSERT INTO absensi
                    (
                        user_id,
                        tanggal,
                        jam_masuk,
                        status,
                        keterangan
                    )
                VALUES (
                    %s,
                    CURDATE(),
                    %s,
                    %s,
                    %s
                )
            """, (
                session["user_id"],
                waktu,
                status,
                keterangan
            ))

            db.commit()

            flash(
                "Absen masuk berhasil! Wajah terverifikasi.",
                "success"
            )

            return redirect(url_for("absensi"))

                # AMBIL RIWAYAT PENGAJUAN IZIN

        cursor.execute("""
            SELECT *
            FROM pengajuan_izin
            WHERE user_id = %s
            ORDER BY created_at DESC
        """, (
            session["user_id"],
        ))

        pengajuan_izin = cursor.fetchall()


        return render_template(
            "absensi.html",
            data=data_hari_ini,
            pengajuan_izin=pengajuan_izin
        )

    except mysql.connector.Error as e:

        db.rollback()

        print(
            "Database absensi error:",
            e
        )

        flash(
            "Terjadi kesalahan database saat memproses absensi. Periksa terminal aplikasi.",
            "danger"
        )

        return redirect(url_for("absensi"))

    finally:
        cursor.close()
        db.close()


# AJUKAN IZIN KARYAWAN

@app.route("/izin/ajukan", methods=["POST"])
def ajukan_izin():

    # Cek login
    if "user_id" not in session:
        return redirect(url_for("login_karyawan"))

    # Hanya karyawan yang boleh mengajukan izin
    if session.get("role") != "karyawan":
        flash("Hanya karyawan yang dapat mengajukan izin!", "danger")
        return redirect(url_for("dashboard"))

    jenis_izin = request.form.get("jenis_izin", "").strip()
    tanggal_mulai = request.form.get("tanggal_mulai", "")
    tanggal_selesai = request.form.get("tanggal_selesai", "")
    alasan = request.form.get("alasan", "").strip()
    file_bukti = request.files.get("file_bukti")

    # Validasi jenis izin
    jenis_valid = ["Izin", "Sakit", "Keperluan Lainnya"]

    if jenis_izin not in jenis_valid:
        flash("Jenis izin tidak valid!", "danger")
        return redirect(url_for("absensi"))

    # Validasi data wajib
    if not tanggal_mulai or not tanggal_selesai or not alasan:
        flash("Semua data pengajuan wajib diisi!", "danger")
        return redirect(url_for("absensi"))

    # Validasi tanggal
    try:
        mulai = datetime.strptime(tanggal_mulai, "%Y-%m-%d").date()
        selesai = datetime.strptime(tanggal_selesai, "%Y-%m-%d").date()

        if selesai < mulai:
            flash("Tanggal selesai tidak boleh sebelum tanggal mulai!", "danger")
            return redirect(url_for("absensi"))

    except ValueError:
        flash("Format tanggal tidak valid!", "danger")
        return redirect(url_for("absensi"))

    # Validasi file bukti
    if not file_bukti or file_bukti.filename == "":
        flash("Silakan upload bukti izin!", "danger")
        return redirect(url_for("absensi"))

    nama_asli = secure_filename(file_bukti.filename)

    if not file_izin_diizinkan(nama_asli):
        flash("File harus berformat JPG, JPEG, PNG, atau PDF!", "danger")
        return redirect(url_for("absensi"))

    ekstensi = nama_asli.rsplit(".", 1)[1].lower()
    nama_baru = f"{uuid.uuid4().hex}.{ekstensi}"
    lokasi_file = os.path.join(IZIN_FOLDER, nama_baru)

    db = get_db()
    cursor = db.cursor()

    try:
        # Simpan file bukti
        file_bukti.save(lokasi_file)

        # Simpan pengajuan ke database
        cursor.execute("""
            INSERT INTO pengajuan_izin
            (
                user_id,
                jenis_izin,
                tanggal_mulai,
                tanggal_selesai,
                alasan,
                file_bukti,
                status
            )
            VALUES (%s, %s, %s, %s, %s, %s, 'Menunggu')
        """, (
            session["user_id"],
            jenis_izin,
            tanggal_mulai,
            tanggal_selesai,
            alasan,
            nama_baru
        ))

        db.commit()

        flash("Pengajuan izin berhasil dikirim!", "success")

    except Exception as e:
        db.rollback()

        if os.path.exists(lokasi_file):
            os.remove(lokasi_file)

        print("Error pengajuan izin:", e)
        flash("Pengajuan izin gagal disimpan!", "danger")

    finally:
        cursor.close()
        db.close()

    return redirect(url_for("absensi"))

# DATA TERLAMBAT

@app.route("/terlambat")
def terlambat():

    if "user_id" not in session:

        return redirect(
            url_for("login_admin")
        )


    if session["role"] != "admin":

        flash(
            "Halaman hanya untuk admin!",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )


    db = get_db()
    cursor = db.cursor(dictionary=True)


    cursor.execute("""
        SELECT
            absensi.*,
            users.nama,
            users.jabatan
        FROM absensi

        JOIN users
        ON absensi.user_id = users.id

        WHERE absensi.status = 'Terlambat'

        ORDER BY
            absensi.tanggal DESC,
            absensi.id DESC
    """)


    data = cursor.fetchall()


    cursor.close()
    db.close()


    return render_template(
        "terlambat.html",
        data=data
    )


# REKAP KEHADIRAN

@app.route("/rekap")
def rekap():

    if "user_id" not in session:
        return redirect(url_for("login_admin"))

    db = get_db()
    cursor = db.cursor(dictionary=True)

    try:

        if session["role"] == "admin":

            cursor.execute("""
                SELECT
                    absensi.*,
                    users.nama,
                    users.jabatan
                FROM absensi
                JOIN users
                    ON absensi.user_id = users.id
                ORDER BY
                    absensi.tanggal DESC,
                    absensi.id DESC
            """)

        else:

            cursor.execute("""
                SELECT
                    absensi.*,
                    users.nama,
                    users.jabatan
                FROM absensi
                JOIN users
                    ON absensi.user_id = users.id
                WHERE absensi.user_id = %s
                ORDER BY
                    absensi.tanggal DESC,
                    absensi.id DESC
            """, (
                session["user_id"],
            ))

        data = cursor.fetchall()

        return render_template(
            "rekap.html",
            data=data
        )

    finally:
        cursor.close()
        db.close()


# LAPORAN BULANAN

@app.route("/laporan")
def laporan():

    if "user_id" not in session:
        return redirect(url_for("login_admin"))

    if session["role"] != "admin":
        flash("Halaman hanya untuk admin!", "danger")
        return redirect(url_for("dashboard"))

    db = get_db()
    cursor = db.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT
                absensi.id,
                users.nama,
                users.jabatan,
                absensi.tanggal,
                absensi.jam_masuk,
                absensi.jam_keluar,
                absensi.status,
                absensi.keterangan
            FROM absensi
            JOIN users
                ON absensi.user_id = users.id
            ORDER BY
                absensi.tanggal DESC,
                absensi.jam_masuk DESC
        """)

        data = cursor.fetchall()

        return render_template(
            "laporan.html",
            data=data
        )

    finally:
        cursor.close()
        db.close()


# HAPUS DATA ABSENSI

@app.route("/laporan/hapus/<int:id>", methods=["POST"])
def hapus_laporan(id):

    if "user_id" not in session:
        return redirect(url_for("login_admin"))

    if session.get("role") != "admin":
        flash("Hanya admin yang dapat menghapus data!", "danger")
        return redirect(url_for("dashboard"))

    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute("""
            DELETE FROM absensi
            WHERE id = %s
        """, (id,))

        if cursor.rowcount > 0:
            db.commit()
            flash("Data absensi berhasil dihapus!", "success")
        else:
            db.rollback()
            flash("Data absensi tidak ditemukan!", "warning")

    except mysql.connector.Error as e:
        db.rollback()
        print("Error hapus absensi:", e)
        flash("Gagal menghapus data absensi!", "danger")

    finally:
        cursor.close()
        db.close()

    return redirect(url_for("laporan"))


# DATA KARYAWAN
@app.route("/karyawan")
def karyawan():

    if "user_id" not in session:
        return redirect(url_for("login_admin"))

    if session["role"] != "admin":
        flash("Halaman hanya untuk admin!", "danger")
        return redirect(url_for("dashboard"))

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            id,
            user_id,
            nama,
            nik,
            jabatan,
            no_hp,
            alamat
        FROM karyawan
        ORDER BY nama ASC
    """)

    data_karyawan = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template(
        "karyawan.html",
        karyawan=data_karyawan
    )


# TAMBAH DATA KARYAWAN

@app.route(
    "/karyawan/tambah",
    methods=["GET", "POST"]
)
def tambah_karyawan():

    if "user_id" not in session:

        return redirect(
            url_for("login_admin")
        )


    if session["role"] != "admin":

        flash(
            "Halaman hanya untuk admin!",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )


    db = get_db()
    cursor = db.cursor(dictionary=True)


    if request.method == "POST":

        user_id = request.form.get(
            "user_id"
        )

        nama = request.form["nama"].strip()

        nik = request.form["nik"].strip()

        jabatan = request.form[
            "jabatan"
        ].strip()

        no_hp = request.form[
            "no_hp"
        ].strip()

        alamat = request.form[
            "alamat"
        ].strip()


        if not user_id:

            flash(
                "Akun login karyawan harus dipilih!",
                "danger"
            )

            cursor.close()
            db.close()

            return redirect(
                url_for("tambah_karyawan")
            )


        try:

            # Pastikan akun adalah karyawan

            cursor.execute("""
                SELECT id
                FROM users
                WHERE id = %s
                AND role = 'karyawan'
            """, (
                user_id,
            ))

            user = cursor.fetchone()


            if not user:

                flash(
                    "Akun karyawan tidak valid!",
                    "danger"
                )

                cursor.close()
                db.close()

                return redirect(
                    url_for("tambah_karyawan")
                )


            # Pastikan akun belum terhubung

            cursor.execute("""
                SELECT id
                FROM karyawan
                WHERE user_id = %s
            """, (
                user_id,
            ))

            sudah_terhubung = cursor.fetchone()


            if sudah_terhubung:

                flash(
                    "Akun tersebut sudah terhubung dengan data karyawan lain!",
                    "danger"
                )

                cursor.close()
                db.close()

                return redirect(
                    url_for("tambah_karyawan")
                )


            # Simpan data

            cursor.execute("""
                INSERT INTO karyawan
                (
                    user_id,
                    nama,
                    nik,
                    jabatan,
                    no_hp,
                    alamat
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
            """, (
                user_id,
                nama,
                nik,
                jabatan,
                no_hp,
                alamat
            ))


            # Samakan nama dan jabatan akun login

            cursor.execute("""
                UPDATE users
                SET
                    nama = %s,
                    jabatan = %s
                WHERE id = %s
            """, (
                nama,
                jabatan,
                user_id
            ))


            db.commit()


            flash(
                "Data karyawan berhasil ditambahkan!",
                "success"
            )


        except mysql.connector.Error as e:

            db.rollback()

            if getattr(
                e,
                "errno",
                None
            ) == 1062:

                flash(
                    "NIK atau akun login sudah digunakan!",
                    "danger"
                )

            else:

                print(
                    "Tambah karyawan error:",
                    e
                )

                flash(
                    "Data karyawan gagal ditambahkan!",
                    "danger"
                )


        finally:

            cursor.close()
            db.close()


        return redirect(
            url_for("karyawan")
        )


    # AKUN KARYAWAN YANG BELUM TERHUBUNG

    cursor.execute("""
        SELECT
            users.id,
            users.nama,
            users.username
        FROM users

        LEFT JOIN karyawan
        ON users.id = karyawan.user_id

        WHERE users.role = 'karyawan'
        AND karyawan.id IS NULL

        ORDER BY users.nama ASC
    """)


    users = cursor.fetchall()


    cursor.close()
    db.close()


    return render_template(
        "tambah_karyawan.html",
        users=users
    )


# EDIT DATA KARYAWAN

@app.route(
    "/karyawan/edit/<int:id>",
    methods=["GET", "POST"]
)
def edit_karyawan(id):

    if "user_id" not in session:

        return redirect(
            url_for("login_admin")
        )


    if session["role"] != "admin":

        flash(
            "Halaman hanya untuk admin!",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )


    db = get_db()
    cursor = db.cursor(dictionary=True)


    cursor.execute("""
        SELECT *
        FROM karyawan
        WHERE id = %s
    """, (
        id,
    ))


    data = cursor.fetchone()


    if not data:

        cursor.close()
        db.close()

        flash(
            "Data karyawan tidak ditemukan!",
            "danger"
        )

        return redirect(
            url_for("karyawan")
        )


    if request.method == "POST":

        nama = request.form[
            "nama"
        ].strip()

        nik = request.form[
            "nik"
        ].strip()

        jabatan = request.form[
            "jabatan"
        ].strip()

        no_hp = request.form[
            "no_hp"
        ].strip()

        alamat = request.form[
            "alamat"
        ].strip()


        try:

            cursor.execute("""
                UPDATE karyawan

                SET
                    nama = %s,
                    nik = %s,
                    jabatan = %s,
                    no_hp = %s,
                    alamat = %s

                WHERE id = %s
            """, (
                nama,
                nik,
                jabatan,
                no_hp,
                alamat,
                id
            ))


            # Update akun login jika terhubung

            if data["user_id"]:

                cursor.execute("""
                    UPDATE users
                    SET
                        nama = %s,
                        jabatan = %s
                    WHERE id = %s
                """, (
                    nama,
                    jabatan,
                    data["user_id"]
                ))


            db.commit()


            flash(
                "Data karyawan berhasil diubah!",
                "success"
            )


        except mysql.connector.Error as e:

            db.rollback()

            if getattr(
                e,
                "errno",
                None
            ) == 1062:

                flash(
                    "NIK sudah digunakan!",
                    "danger"
                )

            else:

                print(
                    "Edit karyawan error:",
                    e
                )

                flash(
                    "Data karyawan gagal diubah!",
                    "danger"
                )

        finally:

            cursor.close()
            db.close()


        return redirect(
            url_for("karyawan")
        )


    cursor.close()
    db.close()


    return render_template(
        "edit_karyawan.html",
        karyawan=data
    )


# HAPUS DATA KARYAWAN
@app.route(
    "/karyawan/hapus/<int:id>",
    methods=["POST"]
)
def hapus_karyawan(id):

    if "user_id" not in session:

        return redirect(
            url_for("login_admin")
        )


    if session["role"] != "admin":

        flash(
            "Halaman hanya untuk admin!",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )


    db = get_db()
    cursor = db.cursor()


    try:

        # Ambil lokasi wajah

        cursor.execute("""
            SELECT wajah
            FROM karyawan
            WHERE id = %s
        """, (
            id,
        ))

        row = cursor.fetchone()


        cursor.execute("""
            DELETE FROM karyawan
            WHERE id = %s
        """, (
            id,
        ))


        db.commit()


        # Hapus file wajah jika ada

        if row and row[0]:

            try:

                if os.path.exists(row[0]):
                    os.remove(row[0])

            except Exception:
                pass


        flash(
            "Data karyawan berhasil dihapus!",
            "success"
        )


    except mysql.connector.Error as e:

        db.rollback()

        print(
            "Hapus karyawan error:",
            e
        )

        flash(
            "Data karyawan gagal dihapus!",
            "danger"
        )


    finally:

        cursor.close()
        db.close()


    return redirect(
        url_for("karyawan")
    )


# DAFTAR WAJAH KARYAWAN
@app.route(
    "/karyawan/<int:karyawan_id>/daftar-wajah",
    methods=["GET", "POST"]
)
def daftar_wajah(karyawan_id):

    if "user_id" not in session:

        return redirect(
            url_for("login_admin")
        )


    if session["role"] != "admin":

        flash(
            "Hanya admin yang dapat mendaftarkan wajah karyawan!",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )


    db = get_db()
    cursor = db.cursor(dictionary=True)


    cursor.execute("""
        SELECT
            karyawan.*,
            users.username
        FROM karyawan

        LEFT JOIN users
        ON karyawan.user_id = users.id

        WHERE karyawan.id = %s
    """, (
        karyawan_id,
    ))


    karyawan_data = cursor.fetchone()


    if not karyawan_data:

        cursor.close()
        db.close()

        flash(
            "Data karyawan tidak ditemukan!",
            "danger"
        )

        return redirect(
            url_for("karyawan")
        )


    if not karyawan_data["user_id"]:

        cursor.close()
        db.close()

        flash(
            "Karyawan belum memiliki akun login!",
            "warning"
        )

        return redirect(
            url_for("karyawan")
        )


    if request.method == "POST":

        foto = request.form.get(
            "foto"
        )


        if not foto:

            flash(
                "Foto wajah belum diterima.",
                "danger"
            )

            cursor.close()
            db.close()

            return redirect(
                url_for(
                    "daftar_wajah",
                    karyawan_id=karyawan_id
                )
            )


        foto_baru = simpan_foto_base64(
            foto
        )


        if not foto_baru:

            flash(
                "Foto gagal disimpan.",
                "danger"
            )

            cursor.close()
            db.close()

            return redirect(
                url_for(
                    "daftar_wajah",
                    karyawan_id=karyawan_id
                )
            )


        # CEK WAJAH DENGAN DEEPFACE
        try:
            gambar_master = baca_foto_opencv(foto_baru)

            hasil_deteksi = DeepFace.extract_faces(
                img_path=gambar_master,
                detector_backend="opencv",
                enforce_detection=True,
                align=True
            )

            print()
            print("=" * 60)
            print("PENDAFTARAN WAJAH")
            print("=" * 60)
            print("Ukuran gambar:", gambar_master.shape)
            print("Jumlah wajah terdeteksi:", len(hasil_deteksi))
            print("=" * 60)
            print()

            if len(hasil_deteksi) != 1:
                raise ValueError(
                    f"Diharapkan tepat satu wajah, tetapi terdeteksi {len(hasil_deteksi)}."
                )

        except Exception as e:
            print()
            print("=" * 60)
            print("PENDAFTARAN WAJAH ERROR - DETAIL LENGKAP")
            print("=" * 60)
            print(f"Jenis error: {type(e).__name__}")
            print(f"Pesan error: {e}")
            traceback.print_exc()
            print("=" * 60)
            print()


            try:

                if os.path.exists(foto_baru):
                    os.remove(foto_baru)

            except Exception:
                pass


            flash(
                "Wajah tidak terdeteksi. Pastikan wajah terlihat jelas di kamera.",
                "danger"
            )

            cursor.close()
            db.close()

            return redirect(
                url_for(
                    "daftar_wajah",
                    karyawan_id=karyawan_id
                )
            )


        # HAPUS WAJAH LAMA
        wajah_lama = karyawan_data["wajah"]


        cursor.execute("""
            UPDATE karyawan

            SET
                wajah = %s,
                wajah_terdaftar = 1,
                wajah_terdaftar_at = NOW()

            WHERE id = %s
        """, (
            foto_baru,
            karyawan_id
        ))


        db.commit()


        if wajah_lama:

            try:

                if os.path.exists(wajah_lama):
                    os.remove(wajah_lama)

            except Exception:
                pass


        flash(
            "Wajah karyawan berhasil didaftarkan!",
            "success"
        )


        cursor.close()
        db.close()


        return redirect(
            url_for("karyawan")
        )


    cursor.close()
    db.close()


    return render_template(
        "daftar_wajah.html",
        karyawan=karyawan_data
    )

# PENGATURAN ABSENSI
@app.route(
    "/pengaturan",
    methods=["GET", "POST"]
)
def pengaturan():

    if "user_id" not in session:

        return redirect(
            url_for("login_admin")
        )


    if session["role"] != "admin":

        flash(
            "Halaman hanya untuk admin!",
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )


    db = get_db()
    cursor = db.cursor(dictionary=True)


    cursor.execute("""
        SELECT *
        FROM pengaturan_absensi
        ORDER BY id DESC
        LIMIT 1
    """)


    data = cursor.fetchone()


    if not data:

        cursor.execute("""
            INSERT INTO pengaturan_absensi
            (jam_masuk)
            VALUES ('08:00:00')
        """)

        db.commit()


        cursor.execute("""
            SELECT *
            FROM pengaturan_absensi
            ORDER BY id DESC
            LIMIT 1
        """)


        data = cursor.fetchone()


    if request.method == "POST":

        jam_masuk = request.form[
            "jam_masuk"
        ]


        if not jam_masuk:

            flash(
                "Jam masuk harus diisi!",
                "danger"
            )

            cursor.close()
            db.close()

            return redirect(
                url_for("pengaturan")
            )


        cursor.execute("""
            UPDATE pengaturan_absensi

            SET jam_masuk = %s

            WHERE id = %s
        """, (
            jam_masuk,
            data["id"]
        ))


        db.commit()


        flash(
            "Jam masuk berhasil diperbarui!",
            "success"
        )


        cursor.close()
        db.close()


        return redirect(
            url_for("pengaturan")
        )


    cursor.close()
    db.close()


    return render_template(
        "pengaturan.html",
        data=data
    )


# HALAMAN PERSETUJUAN IZIN ADMIN

@app.route("/admin/izin")
def persetujuan_izin():

    if "user_id" not in session:
        return redirect(url_for("login_admin"))

    if session.get("role") != "admin":
        flash("Halaman hanya untuk admin!", "danger")
        return redirect(url_for("dashboard"))

    db = get_db()
    cursor = db.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT
                pengajuan_izin.*,
                users.nama,
                users.jabatan
            FROM pengajuan_izin
            JOIN users
                ON pengajuan_izin.user_id = users.id
            ORDER BY
                CASE
                    WHEN pengajuan_izin.status = 'Menunggu'
                    THEN 0
                    ELSE 1
                END,
                pengajuan_izin.created_at DESC
        """)

        data_izin = cursor.fetchall()

        return render_template(
            "persetujuan_izin.html",
            data_izin=data_izin
        )

    finally:
        cursor.close()
        db.close()


# PROSES PERSETUJUAN / PENOLAKAN IZIN

@app.route(
    "/admin/izin/keputusan/<int:id>",
    methods=["POST"]
)
def keputusan_izin(id):

    if "user_id" not in session:
        return redirect(url_for("login_admin"))

    if session.get("role") != "admin":
        flash("Hanya admin yang dapat memproses izin!", "danger")
        return redirect(url_for("dashboard"))

    status_baru = request.form.get("status")

    if status_baru not in ["Disetujui", "Ditolak"]:
        flash("Keputusan izin tidak valid!", "danger")
        return redirect(url_for("persetujuan_izin"))

    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute("""
            UPDATE pengajuan_izin
            SET status = %s
            WHERE id = %s
            AND status = 'Menunggu'
        """, (status_baru, id))

        if cursor.rowcount > 0:
            db.commit()

            if status_baru == "Disetujui":
                flash("Pengajuan izin berhasil disetujui!", "success")
            else:
                flash("Pengajuan izin berhasil ditolak!", "success")

        else:
            db.rollback()
            flash(
                "Pengajuan tidak ditemukan atau sudah diproses!",
                "warning"
            )

    except mysql.connector.Error as e:
        db.rollback()
        print("Error keputusan izin:", e)
        flash("Gagal memproses pengajuan izin!", "danger")

    finally:
        cursor.close()
        db.close()

    return redirect(url_for("persetujuan_izin"))


if __name__ == "__main__":
    app.run(
        debug=True,
        use_reloader=False,
        host="127.0.0.1",
        port=5002
    )