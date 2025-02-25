from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
import sqlite3
import folium
import pandas as pd
from datetime import datetime
from folium.plugins import MarkerCluster

app = Flask(__name__)
app.secret_key = "supersecretkey"

bcrypt = Bcrypt(app)

# Setup Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# Model User untuk Flask-Login
class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password
        
@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect("D://SQLITE/yantek.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, password FROM tb_user WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    if user:
        return User(user[0], user[1], user[2])
    return None        

# Fungsi untuk mengambil daftar nama regu unik dari database
def get_nama_regu():
    conn = sqlite3.connect('D://SQLITE/yantek.db')
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT nama_regu FROM regu_tracker")
    regu_list = [row[0] for row in cursor.fetchall()]
    conn.close()
    return regu_list

# Fungsi untuk mengambil data sesuai filter
def get_filtered_data(nama_regu, start_time, end_time):
    conn = sqlite3.connect('D://SQLITE/yantek.db')
    cursor = conn.cursor()

    query = """
        SELECT id, nama_regu, scrape_time, kordinat
        FROM regu_tracker
        WHERE scrape_time BETWEEN ? AND ?
    """
    params = [start_time, end_time]

    if nama_regu:
        query += " AND nama_regu = ?"
        params.append(nama_regu)

    cursor.execute(query, params)
    data = cursor.fetchall()
    conn.close()

    return pd.DataFrame(data, columns=['ID', 'Nama Regu', 'Scrape Time', 'Koordinat']) if data else None

# Fungsi untuk mengambil data aset dari tb_aset
def get_aset_data():
    conn = sqlite3.connect('D://SQLITE/yantek.db')
    cursor = conn.cursor()
    cursor.execute("SELECT LOCATION, LATITUDEY, LONGITUDEX, KATEGORI FROM tb_aset")
    data = cursor.fetchall()
    conn.close()

    return pd.DataFrame(data, columns=['Location', 'Latitude', 'Longitude', 'Kategori']) if data else None

# Fungsi untuk membuat peta Folium
def create_map(df):
    m = folium.Map(location=[-7.15, 108.15], zoom_start=12)
    
    # Tambahkan KML Layer jika ada
    kml_file = "static/Rajapolah.kml"
    try:
        folium.Kml(kml_file).add_to(m)
    except Exception as e:
        print(f"Error loading KML: {e}")
        
    
    # Tambahkan marker untuk regu tracker
    if df is not None and not df.empty:
        df = df.sort_values(by="Scrape Time")
        for i, row in df.iterrows():
            try:
                lat, lon = map(float, row['Koordinat'].split(','))
                if row.name == df.index[-1]:
                    marker_color = "blue"
                    z_index = 1000  # Membuat marker biru di atas
                else:
                    marker_color = "gray"
                    z_index = 0  # Marker abu-abu tetap di bawah
                folium.Marker(
                    location=[lat, lon],
                    popup=f"<b>Regu:</b> {row['Nama Regu']}<br><b>Scrape Time:</b> {row['Scrape Time']}",
                    icon=folium.Icon(color=marker_color, icon='fa-car', prefix='fa'),
                    z_index_offset=z_index
                ).add_to(m)
            except:
                continue

    # Tambahkan marker untuk aset dari tb_aset
    aset_df = get_aset_data()
    if aset_df is not None:
        for _, row in aset_df.iterrows():
            try:
                lat, lon = float(row['Latitude']), float(row['Longitude'])
                kategori = row['Kategori']
                lokasi = row['Location']

                # Tentukan warna berdasarkan kategori
                color = "black" if kategori == "TIANG TM" else "green" if kategori == "GARDU" else "gray"

                folium.CircleMarker(
                    location=[lat, lon],
                    radius=1,
                    color=color,
                    fill=True,
                    fill_color=color,
                    fill_opacity=0.7,
                    popup=f"<b>Lokasi:</b> {lokasi}<br><b>Kategori:</b> {kategori}"
                ).add_to(m)
            except:
                continue

    # Menyimpan peta di dalam folder static
    map_file = "static/map.html"
    m.save(map_file)
    return map_file

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")  # Gunakan get() agar tidak error
        password = request.form.get("password")

        if not username or not password:
            flash("Harap isi username dan password!", "danger")
            return render_template("login.html")

        conn = sqlite3.connect("D://SQLITE/yantek.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, password FROM tb_user WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()

        if user and bcrypt.check_password_hash(user[2], password):
            login_user(User(user[0], user[1], user[2]))
            flash("Login berhasil!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Username atau password salah!", "danger")

    return render_template("login.html")

@app.route("/dashboard",methods=['GET', 'POST'])
@login_required
def dashboard():
    regu_list = get_nama_regu()
    map_generated = False
    error_message = None
    nama_regu = None
    start_time = None
    end_time = None
    
    if request.method == "POST":
        nama_regu = request.form.get("nama_regu")
        start_time = request.form.get("start_time")
        end_time = request.form.get("end_time")
        
        try:
            # Konversi format input datetime-local ke format SQLite
            start_time = datetime.strptime(start_time, "%Y-%m-%dT%H:%M").strftime("%Y-%m-%d %H:%M:%S")
            end_time = datetime.strptime(end_time, "%Y-%m-%dT%H:%M").strftime("%Y-%m-%d %H:%M:%S")

            # Ambil data regu tracker berdasarkan filter
            df = get_filtered_data(nama_regu, start_time, end_time)

            # Buat peta jika ada data
            map_file = create_map(df)
            map_generated = True

        except Exception as e:
            error_message = f"Terjadi kesalahan: {e}"

    return render_template("index.html", regu_list=regu_list, map_generated=map_generated, error_message=error_message,
                            peta=map_generated, nama_regu=nama_regu, start_time=start_time, end_time=end_time)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    session.pop('_flashes', None)
    flash("Logout berhasil!", "info")
    return redirect(url_for("login"))
    
    
def get_last_location():
    """Mengambil lokasi terakhir setiap regu dari database."""
    conn = sqlite3.connect('D://SQLITE/yantek.db')
    cursor = conn.cursor()

    query = """
        SELECT nama_regu, kordinat,scrape_time, MAX(scrape_time) 
        FROM regu_tracker 
        GROUP BY nama_regu
    """
    cursor.execute(query)
    data = cursor.fetchall()
    conn.close()

    locations = []
    for row in data:
        nama_regu, kordinat, scrape_time = row[:3]
        if kordinat:
            lat, lon = map(float, kordinat.split(','))  # Pisahkan koordinat "lat,lon"
            locations.append((nama_regu, lat, lon, scrape_time))

    return locations


    
@app.route('/live-location')
@login_required
def live_location():
    locations = get_last_location()

    # Buat peta dasar
    m = folium.Map(location=[-7.15, 108.15], zoom_start=12)
    
    # Tambahkan marker untuk aset dari tb_aset
    aset_df = get_aset_data()
    if aset_df is not None:
        for _, row in aset_df.iterrows():
            try:
                lat, lon = float(row['Latitude']), float(row['Longitude'])
                kategori = row['Kategori']
                lokasi = row['Location']

                # Tentukan warna berdasarkan kategori
                color = "black" if kategori == "TIANG TM" else "green" if kategori == "GARDU" else "gray"

                folium.CircleMarker(
                    location=[lat, lon],
                    radius=1,
                    color=color,
                    fill=True,
                    fill_color=color,
                    fill_opacity=0.7,
                    popup=f"<b>Lokasi:</b> {lokasi}<br><b>Kategori:</b> {kategori}"
                ).add_to(m)
            except:
                continue
                
    # Peta Regu
    for nama_regu, lat, lon, scrape_time in locations:
        popup_content = f"""
        <b>Regu:</b> {nama_regu}<br>
        <b>Update:</b> {scrape_time}
        """
        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_content, max_width=300),
            tooltip=nama_regu,
            icon=folium.Icon(color="blue", icon="fa-car", prefix="fa")
        ).add_to(m)

    # Simpan peta sebagai file HTML
    map_path = "static/live_map.html"
    m.save(map_path)

    return render_template("live_location.html", map_path=map_path,locations=locations)

if __name__ == "__main__":
    #app.run(debug=True)
    app.run(host='0.0.0.0', port=5000, debug=True)
