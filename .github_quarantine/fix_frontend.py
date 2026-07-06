import os

# ساخت اجباری مسیرها
os.makedirs('frontend/src', exist_ok=True)

index_html = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <title>The Matrix: ALIVE</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>"""

main_tsx = """import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)"""

app_tsx = """import React from 'react';

export default function App() {
  return (
    <div style={{ backgroundColor: '#14161A', height: '100vh', width: '100vw', margin: 0, display: 'flex', justifyContent: 'center', alignItems: 'center', color: '#C9A15A', fontFamily: 'monospace' }}>
      <h1>🟢 THE MATRIX IS CONNECTED 🟢</h1>
    </div>
  );
}"""

# نوشتن فایل‌ها دقیقاً در جای درست
with open('frontend/index.html', 'w', encoding='utf-8') as f: f.write(index_html)
with open('frontend/src/main.tsx', 'w', encoding='utf-8') as f: f.write(main_tsx)
with open('frontend/src/App.tsx', 'w', encoding='utf-8') as f: f.write(app_tsx)

print("✅ ALL FILES FORCE-WRITTEN TO CORRECT DIRECTORY.")