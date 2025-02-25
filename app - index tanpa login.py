from flask import Flask, render_template, request
import sqlite3
import folium
import pandas as pd
from datetime import datetime
from folium.plugins import MarkerCluster

app = Flask(__name__)

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
def index():
    regu_list = get_nama_regu()
    map_generated = False
    error_message = None
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
                            peta=map_generated, start_time=start_time, end_time=end_time)


if __name__ == "__main__":
    #app.run(debug=True)
    app.run(host='0.0.0.0', port=5000, debug=True)
