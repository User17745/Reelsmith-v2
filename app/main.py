import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from app.db import get_db_connection

app = FastAPI(title="Reelsmith v2")

WORKSPACE_DIR = os.getenv("WORKSPACE_DIR", "workspace")

# Mount static files for outputs
output_dir = os.path.join(WORKSPACE_DIR, "output")
os.makedirs(output_dir, exist_ok=True)
app.mount("/outputs", StaticFiles(directory=output_dir), name="outputs")

# Ensure DB is initialized
from app.db import init_db
init_db()

@app.get("/", response_class=HTMLResponse)
async def read_root():
    return """
    <html>
        <head>
            <title>Reelsmith v2 Dashboard</title>
            <style>
                body { font-family: sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
                h1 { border-bottom: 1px solid #ccc; padding-bottom: 10px; }
                .section { margin-bottom: 40px; }
                .item { border: 1px solid #eee; padding: 10px; margin-bottom: 10px; border-radius: 5px; }
                .flagged { background-color: #fff0f0; border-color: #ffcccc; }
                button { cursor: pointer; padding: 5px 10px; }
            </style>
        </head>
        <body>
            <h1>Reelsmith v2 Dashboard</h1>
            
            <div class="section">
                <h2>Flagged Items</h2>
                <div id="flagged-list">Loading...</div>
            </div>
            
            <div class="section">
                <h2>Generated Outputs</h2>
                <div id="outputs-list">Loading...</div>
            </div>

            <script>
                async function loadFlagged() {
                    const res = await fetch('/api/flagged');
                    const data = await res.json();
                    const container = document.getElementById('flagged-list');
                    container.innerHTML = data.length ? '' : 'No flagged items.';
                    
                    data.forEach(item => {
                        const div = document.createElement('div');
                        div.className = 'item flagged';
                        div.innerHTML = `
                            <strong>${item.post_id}</strong><br>
                            Reason: ${item.reason}<br>
                            <small>${item.flagged_at}</small><br>
                            <button onclick="resolveFlag('${item.post_id}')">Resolve (Delete)</button>
                        `;
                        container.appendChild(div);
                    });
                }

                async function loadOutputs() {
                    const res = await fetch('/api/outputs');
                    const data = await res.json();
                    const container = document.getElementById('outputs-list');
                    container.innerHTML = data.length ? '' : 'No outputs yet.';
                    
                    data.forEach(item => {
                        const div = document.createElement('div');
                        div.className = 'item';
                        div.innerHTML = `
                            <strong>${item.filename}</strong><br>
                            <a href="/outputs/${item.filename}" target="_blank">View Video</a>
                        `;
                        container.appendChild(div);
                    });
                }

                async function resolveFlag(postId) {
                    if (!confirm('Delete this flagged item?')) return;
                    await fetch(`/api/flagged/${postId}/resolve`, { method: 'POST' });
                    loadFlagged();
                }

                loadFlagged();
                loadOutputs();
            </script>
        </body>
    </html>
    """

@app.get("/api/flagged")
def get_flagged():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM flagged ORDER BY flagged_at DESC")
    items = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return items

@app.post("/api/flagged/{post_id}/resolve")
def resolve_flag(post_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get file path
    cursor.execute("SELECT data_path FROM flagged WHERE post_id = ?", (post_id,))
    row = cursor.fetchone()
    
    if row and row['data_path'] and os.path.exists(row['data_path']):
        os.remove(row['data_path'])
        
    cursor.execute("DELETE FROM flagged WHERE post_id = ?", (post_id,))
    conn.commit()
    conn.close()
    return {"status": "resolved"}

@app.get("/api/outputs")
def get_outputs():
    files = []
    if os.path.exists(output_dir):
        files = [{"filename": f} for f in os.listdir(output_dir) if f.endswith(".mp4")]
    return files
