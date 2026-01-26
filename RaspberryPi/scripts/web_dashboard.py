#!/usr/bin/env python3
"""
Simple Web Dashboard for Thesis Data
- View latest sensor readings
- Browse images
- Download CSV files
Run on Raspberry Pi to access from your laptop via browser
"""

from flask import Flask, render_template_string, send_file, jsonify, request
import pandas as pd
from pathlib import Path
import glob
from datetime import datetime
import os

app = Flask(__name__)

# Data directories
DATA_DIR = Path.home() / "thesis_data"
SENSOR_DIR = DATA_DIR / "sensor_data"
IMAGE_DIR = DATA_DIR / "images"

# HTML Template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Thesis Data Dashboard</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            border-bottom: 3px solid #4CAF50;
            padding-bottom: 10px;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        .stat-card {
            background: #f9f9f9;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #4CAF50;
        }
        .stat-card h3 {
            margin: 0 0 10px 0;
            color: #666;
            font-size: 14px;
        }
        .stat-card .value {
            font-size: 28px;
            font-weight: bold;
            color: #333;
        }
        .section {
            margin: 30px 0;
        }
        .section h2 {
            color: #333;
            border-bottom: 2px solid #ddd;
            padding-bottom: 5px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background: #4CAF50;
            color: white;
        }
        tr:hover {
            background: #f5f5f5;
        }
        .btn {
            display: inline-block;
            padding: 8px 16px;
            background: #4CAF50;
            color: white;
            text-decoration: none;
            border-radius: 4px;
            margin: 5px;
        }
        .btn:hover {
            background: #45a049;
        }
        .image-gallery {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        .image-card {
            border: 1px solid #ddd;
            border-radius: 4px;
            overflow: hidden;
        }
        .image-card img {
            width: 100%;
            height: 150px;
            object-fit: cover;
        }
        .image-card .info {
            padding: 10px;
            background: #f9f9f9;
            font-size: 12px;
        }
        .refresh-btn {
            float: right;
            background: #2196F3;
        }
    </style>
    <script>
        function refreshData() {
            location.reload();
        }
        setInterval(refreshData, 60000); // Auto-refresh every minute
    </script>
</head>
<body>
    <div class="container">
        <h1>📊 Thesis Data Dashboard
            <a href="javascript:refreshData()" class="btn refresh-btn">🔄 Refresh</a>
        </h1>
        
        <div class="stats">
            <div class="stat-card">
                <h3>CSV Files</h3>
                <div class="value">{{ csv_count }}</div>
            </div>
            <div class="stat-card">
                <h3>Images</h3>
                <div class="value">{{ image_count }}</div>
            </div>
            <div class="stat-card">
                <h3>Latest Data</h3>
                <div class="value" style="font-size: 16px;">{{ latest_time }}</div>
            </div>
        </div>

        <div class="section">
            <h2>📈 Latest Sensor Readings</h2>
            {{ latest_data | safe }}
        </div>

        <div class="section">
            <h2>📁 CSV Files</h2>
            <table>
                <tr>
                    <th>File Name</th>
                    <th>Size</th>
                    <th>Modified</th>
                    <th>Actions</th>
                </tr>
                {% for file in csv_files %}
                <tr>
                    <td>{{ file.name }}</td>
                    <td>{{ file.size }}</td>
                    <td>{{ file.modified }}</td>
                    <td>
                        <a href="/download/{{ file.name }}" class="btn">Download</a>
                    </td>
                </tr>
                {% endfor %}
            </table>
        </div>

        <div class="section">
            <h2>📸 Recent Images</h2>
            <div class="image-gallery">
                {% for img in images[:12] %}
                <div class="image-card">
                    <img src="/image/{{ img.name }}" alt="{{ img.name }}">
                    <div class="info">
                        {{ img.name }}<br>
                        {{ img.modified }}
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
    </div>
</body>
</html>
"""

def get_latest_readings():
    """Get the latest sensor readings from all CSV files"""
    latest_data = {}
    
    csv_files = sorted(SENSOR_DIR.glob("*.csv"), reverse=True)
    
    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file)
            if not df.empty:
                node_name = csv_file.stem.rsplit('_', 1)[0]  # e.g., "node1" from "node1_20260126"
                latest_row = df.iloc[-1]
                latest_data[node_name] = latest_row.to_dict()
        except Exception as e:
            print(f"Error reading {csv_file}: {e}")
    
    # Create HTML table
    if not latest_data:
        return "<p>No data available yet</p>"
    
    html = "<table><tr><th>Node</th><th>Time</th><th>Temp (°C)</th><th>Humidity (%)</th><th>TVOC (ppb)</th><th>eCO2 (ppm)</th><th>MQ3 (ppm)</th></tr>"
    
    for node, data in latest_data.items():
        html += f"""
        <tr>
            <td><strong>{node}</strong></td>
            <td>{data.get('timestamp', 'N/A')}</td>
            <td>{data.get('temperature', 'N/A')}</td>
            <td>{data.get('humidity', 'N/A')}</td>
            <td>{data.get('tvoc', 'N/A')}</td>
            <td>{data.get('eco2', 'N/A')}</td>
            <td>{data.get('mq3_ppm', 'N/A')}</td>
        </tr>
        """
    
    html += "</table>"
    return html

@app.route('/')
def index():
    # Get CSV files
    csv_files = []
    for f in sorted(SENSOR_DIR.glob("*.csv"), reverse=True):
        csv_files.append({
            'name': f.name,
            'size': f"{f.stat().st_size / 1024:.1f} KB",
            'modified': datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
        })
    
    # Get images
    images = []
    for f in sorted(IMAGE_DIR.glob("*.jpg"), reverse=True)[:20]:
        images.append({
            'name': f.name,
            'modified': datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
        })
    
    # Get latest time
    latest_time = "No data"
    if csv_files:
        latest_time = csv_files[0]['modified']
    
    return render_template_string(
        HTML_TEMPLATE,
        csv_count=len(csv_files),
        image_count=len(list(IMAGE_DIR.glob("*.jpg"))),
        latest_time=latest_time,
        latest_data=get_latest_readings(),
        csv_files=csv_files,
        images=images
    )

@app.route('/download/<filename>')
def download(filename):
    """Download a CSV file"""
    file_path = SENSOR_DIR / filename
    if file_path.exists():
        return send_file(file_path, as_attachment=True)
    return "File not found", 404

@app.route('/image/<filename>')
def image(filename):
    """Serve an image"""
    file_path = IMAGE_DIR / filename
    if file_path.exists():
        return send_file(file_path, mimetype='image/jpeg')
    return "Image not found", 404

@app.route('/api/latest')
def api_latest():
    """API endpoint for latest data (for future dashboard integration)"""
    latest_data = {}
    csv_files = sorted(SENSOR_DIR.glob("*.csv"), reverse=True)
    
    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file)
            if not df.empty:
                node_name = csv_file.stem.rsplit('_', 1)[0]
                latest_data[node_name] = df.iloc[-1].to_dict()
        except:
            pass
    
    return jsonify(latest_data)

if __name__ == '__main__':
    print("=" * 50)
    print("  Thesis Data Dashboard")
    print("=" * 50)
    print()
    print("Dashboard starting...")
    print()
    print("Access from your laptop:")
    print("  http://192.168.2.84:5000")
    print()
    print("Press Ctrl+C to stop")
    print()
    
    app.run(host='0.0.0.0', port=5000, debug=False)
