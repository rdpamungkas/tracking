from flask import Flask, render_template, request
import sqlite3
import folium
import pandas as pd
from datetime import datetime

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

    return pd.DataFrame(data, columns=['ID', 'Nama Regu', 'Scrape Time', 'Koordinat'])

# Fungsi untuk membuat peta Folium
def create_map(df):
    m = folium.Map(location=[-7.15, 108.15], zoom_start=12)
    
    kml_file = "static/Rajapolah.kml"
    try:
        folium.Kml(kml_file).add_to(m)
    except Exception as e:
        print(f"Error loading KML: {e}")
        
    for _, row in df.iterrows():
        try:
            lat, lon = map(float, row['Koordinat'].split(','))
            folium.Marker(
                location=[lat, lon],
                popup=f"<b>Regu:</b> {row['Nama Regu']}<br><b>Scrape Time:</b> {row['Scrape Time']}",
                icon=folium.Icon(color='blue', icon='info-sign')
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
            # Mengonversi format input datetime-local menjadi format yang sesuai untuk SQLite
            start_time = datetime.strptime(start_time, "%Y-%m-%dT%H:%M").strftime("%Y-%m-%d %H:%M:%S")
            end_time = datetime.strptime(end_time, "%Y-%m-%dT%H:%M").strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            error_message = "Format tanggal salah"
            return render_template("index.html", regu_list=regu_list, map_generated=map_generated, error_message=error_message, 
                                   start_time=start_time, end_time=end_time)  # Kirim kembali waktu yang dimasukkan
        
        df = get_filtered_data(nama_regu, start_time, end_time)
        
        if df.empty:
            error_message = "Data tidak ditemukan untuk filter yang dipilih."
        else:
            map_file = create_map(df)  # Panggil fungsi untuk membuat peta
            map_generated = True
    
    return render_template("index.html", regu_list=regu_list, map_generated=map_generated, error_message=error_message, 
                           peta=map_generated, start_time=start_time, end_time=end_time)

if __name__ == "__main__":
    #app.run(debug=True)
    app.run(host='0.0.0.0', port=5000, debug=True)
