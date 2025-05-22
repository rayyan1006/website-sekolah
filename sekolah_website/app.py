from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import sqlite3
import openpyxl  # ← Tambahkan ini untuk Excel

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secret key untuk session


def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn


# Dummy user
USERNAME = 'admin'
PASSWORD = 'admin123'


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/profil')
def profil():
    return render_template('profil.html')


@app.route('/ppdb')
def ppdb():
    return render_template('ppdb.html')


@app.route('/berita')
def berita():
    return render_template('berita.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == USERNAME and password == PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Username atau password salah!', 'error')
    return render_template('login.html')


@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('admin/dashboard.html')


@app.route('/admin/data-ppdb')
def data_ppdb():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('admin/data-ppdb.html')

# Fungsi untuk mengambil data siswa (dummy data)
def get_data_siswa():
    # Dummy data siswa lengkap dengan NISN dan kelas
    return [
        {'id': 1, 'nama': 'Budi', 'kelas': '1', 'nisn': '1234567890'},
        {'id': 2, 'nama': 'Ani', 'kelas': '2', 'nisn': '1234567891'},
        {'id': 3, 'nama': 'Sari', 'kelas': '3', 'nisn': '1234567892'},
        {'id': 4, 'nama': 'Joko', 'kelas': '1', 'nisn': '1234567893'},
        {'id': 5, 'nama': 'Dewi', 'kelas': '4', 'nisn': '1234567894'},
        {'id': 6, 'nama': 'Rina', 'kelas': '5', 'nisn': '1234567895'},
        {'id': 7, 'nama': 'Andi', 'kelas': '6', 'nisn': '1234567896'},
        {'id': 8, 'nama': 'Tono', 'kelas': '2', 'nisn': '1234567897'},
        {'id': 9, 'nama': 'Lia', 'kelas': '3', 'nisn': '1234567898'},
    ]

@app.route('/admin/data-siswa', methods=['GET'])
def data_siswa():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    # Ambil semua data dari database
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM siswa")
    rows = cur.fetchall()
    conn.close()

    data = [dict(row) for row in rows]

    # Filter
    nisn_search = request.args.get('nisn', '').strip()
    kelas_search = request.args.get('kelas', '').strip()

    if nisn_search:
        data = [s for s in data if nisn_search in s['nisn']]
    if kelas_search:
        data = [s for s in data if s['kelas'] == kelas_search]

    # Urutkan
    data = sorted(data, key=lambda x: (x['kelas'].strip(), x['nama']))

    # Ambil daftar kelas unik untuk dropdown
    kelas_list = sorted(set(s['kelas'] for s in data))

    return render_template('admin/data-siswa.html',
                           data=data,
                           nisn_search=nisn_search,
                           kelas_search=kelas_search,
                           kelas_list=kelas_list)


@app.route('/admin/tambah-siswa', methods=['GET', 'POST'])
def tambah_siswa():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        nama = request.form['nama']
        nisn = request.form['nisn']
        kelas = request.form['kelas']
        jenis_kelamin = request.form['jenis_kelamin']
        status = request.form['status']

        conn = get_db_connection()
        conn.execute("INSERT INTO siswa (nama, nisn, kelas, jenis_kelamin, status) VALUES (?, ?, ?, ?, ?)",
                     (nama, nisn, kelas, jenis_kelamin, status))
        conn.commit()
        conn.close()
        flash('Siswa berhasil ditambahkan.')
        return redirect(url_for('data_siswa'))

    return render_template('admin/tambah-siswa.html')

@app.route('/edit_siswa/<int:id>', methods=['GET', 'POST'])
def edit_siswa(id):
    conn = get_db_connection()
    siswa = conn.execute('SELECT * FROM siswa WHERE id = ?', (id,)).fetchone()

    if not siswa:
        flash("Data siswa tidak ditemukan!", "error")
        return redirect(url_for('data_siswa'))

    if request.method == 'POST':
        nama = request.form['nama']
        nisn = request.form['nisn']
        kelas = request.form['kelas']
        jenis_kelamin = request.form['jenis_kelamin']
        status = request.form['status']

        if not nama or not nisn or not kelas:
            flash("Nama, NISN, dan Kelas harus diisi!", "error")
            return render_template('admin/edit_siswa.html', siswa=siswa)

        conn.execute('''
            UPDATE siswa SET nama=?, nisn=?, kelas=?, jenis_kelamin=?, status=?
            WHERE id=?
        ''', (nama, nisn, kelas, jenis_kelamin, status, id))
        conn.commit()
        conn.close()

        flash("Data siswa berhasil diperbarui!", "success")
        return redirect(url_for('data_siswa'))

    conn.close()
    return render_template('admin/edit_siswa.html', siswa=siswa)



@app.route('/hapus_siswa/<int:id>')
def hapus_siswa(id):
    conn = sqlite3.connect('database.db')
    conn.execute("DELETE FROM siswa WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('data_siswa'))




@app.route('/admin/upload-siswa', methods=['POST'])
def upload_siswa():
    file = request.files['file_excel']
    if not file:
        flash('File tidak ditemukan.')
        return redirect(url_for('data_siswa'))

    import openpyxl
    wb = openpyxl.load_workbook(file)
    sheet = wb.active

    conn = get_db_connection()
    for row in sheet.iter_rows(min_row=2, values_only=True):
        # Pastikan hanya 5 kolom yang diambil
        if len(row) >= 5:
            nama, nisn, kelas, jenis_kelamin, status = row[:5]
            conn.execute(
                "INSERT INTO siswa (nama, nisn, kelas, jenis_kelamin, status) VALUES (?, ?, ?, ?, ?)",
                (nama, nisn, kelas, jenis_kelamin, status)
            )
        else:
            # Bisa juga kasih flash untuk data yang kurang lengkap atau skip saja
            flash('Baris dengan data tidak lengkap ditemukan dan dilewati.')

    conn.commit()
    conn.close()

    flash('Data siswa dari Excel berhasil diunggah.')
    return redirect(url_for('data_siswa'))


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
