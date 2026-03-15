import os
import io
import time
import threading
from flask import Flask, render_template_string, request, send_file
from PIL import Image

app = Flask(__name__)

# इन्टरनेटका लागि एसेट्स
PHOTO_URL = "https://smart-converter-ieh0.onrender.com/static/bs.jpg" 
VIDEO_URL = "https://smart-converter-ieh0.onrender.com/static/an.mp4"

# अस्थायी फाइलहरू बस्ने फोल्डर
UPLOAD_FOLDER = 'temp_uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# फिचर: १० मिनेटपछि डाटा हटाउने फङ्ग्सन
def cleanup_old_files():
    while True:
        time.sleep(60) # हरेक १ मिनेटमा चेक गर्ने
        now = time.time()
        for f in os.listdir(UPLOAD_FOLDER):
            f_path = os.path.join(UPLOAD_FOLDER, f)
            # यदि फाइल १० मिनेट (६०० सेकेन्ड) भन्दा पुरानो छ भने हटाउने
            if os.stat(f_path).st_mtime < now - 600:
                if os.path.isfile(f_path):
                    os.remove(f_path)
                    print(f"Auto-deleted: {f}")

# ब्याकग्राउन्डमा क्लिनअप सुरु गर्ने
threading.Thread(target=cleanup_old_files, daemon=True).start()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SmartConvert Secure | Binod Sapkota</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { 
            background: #0f172a; color: white; font-family: sans-serif;
            background-image: url('{{ photo_url }}'); background-size: cover; background-attachment: fixed;
        }
        body::before { content: ""; position: fixed; inset: 0; background: rgba(15, 23, 42, 0.9); z-index: -1; }
        
        .preview-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(90px, 1fr)); gap: 10px; margin-top: 20px; }
        .preview-img { width: 100%; height: 90px; object-fit: cover; border-radius: 12px; border: 2px solid #22d3ee; }

        #contactModal { display: none; opacity: 0; transition: opacity 0.4s ease; }
        #contactModal.active { display: flex; opacity: 1; }
        
        .modal-box { 
            position: relative; border: 3px solid #22d3ee; border-radius: 2.5rem; 
            overflow: hidden; animation: float 6s ease-in-out infinite; background: #000;
        }
        
        .video-bg { position: absolute; top: 50%; left: 50%; min-width: 100%; min-height: 100%; transform: translate(-50%, -50%); z-index: -1; object-fit: cover; }
        .video-overlay { position: absolute; inset: 0; background: rgba(15, 23, 42, 0.9); z-index: -1; }

        @keyframes float { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-15px); } }
        
        .social-btn { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); transition: 0.3s; width: 100%; }
        .social-btn:hover { background: rgba(34, 211, 238, 0.2); transform: translateX(10px); }
        .secure-badge { background: rgba(34, 211, 238, 0.1); border: 1px solid #22d3ee; padding: 5px 12px; border-radius: 20px; font-size: 10px; color: #22d3ee; }
    </style>
</head>
<body class="min-h-screen flex flex-col">

    <nav class="p-6 flex justify-between items-center max-w-7xl mx-auto w-full">
        <h1 class="text-xl font-bold italic tracking-tighter">SMART<span class="text-cyan-400">CONVERTER</span></h1>
        <div class="flex gap-4 items-center">
            <span class="secure-badge font-bold">🔒 AUTO-DELETE: 10 MINS</span>
            <div class="flex border border-white/10 rounded-lg overflow-hidden text-[10px]">
                <button onclick="setLang('en')" class="px-3 py-1 bg-white/5 hover:bg-cyan-500">EN</button>
                <button onclick="setLang('ne')" class="px-3 py-1 bg-white/5 hover:bg-cyan-500">नेपाली</button>
            </div>
            <button onclick="toggleModal()" class="bg-cyan-500 text-black px-5 py-1.5 rounded-full text-[10px] font-black">Contact</button>
        </div>
    </nav>

    <main class="flex-grow flex items-center justify-center p-6">
        <div class="bg-white/5 backdrop-blur-2xl p-10 rounded-[2.5rem] w-full max-w-lg border border-white/10 shadow-2xl">
            <h2 id="title" class="text-2xl font-black mb-8 text-center uppercase italic">Secure Workspace</h2>
            
            <form action="/convert" method="POST" enctype="multipart/form-data">
                <div class="border-2 border-dashed border-cyan-500/40 p-12 rounded-3xl text-center relative hover:border-cyan-400 transition-all bg-black/20">
                    <input type="file" id="imageInput" name="images" accept="image/*" multiple required 
                           class="absolute inset-0 opacity-0 cursor-pointer z-20">
                    <div id="drop-placeholder">
                        <p class="text-4xl mb-3">📁</p>
                        <p id="up-text" class="text-[10px] font-bold uppercase tracking-widest text-slate-400">Choose Multiple Photos</p>
                    </div>
                    <div id="previewGrid" class="preview-grid"></div>
                </div>

                <div class="mt-8">
                    <select name="format" class="w-full bg-slate-900 border border-white/10 p-4 rounded-2xl font-bold outline-none text-white">
                        <option value="PDF">Combined PDF</option>
                        <option value="PNG">PNG Image</option>
                        <option value="JPEG">JPEG Image</option>
                    </select>
                </div>

                <button id="btn-convert" type="submit" class="w-full mt-8 py-5 bg-cyan-500 text-black font-black text-xs rounded-2xl hover:bg-white transition-all shadow-lg">
                    START SECURE CONVERSION ↗
                </button>
                <p class="text-[9px] text-center mt-4 text-slate-500 uppercase tracking-widest">All data automatically removed from server after 10 minutes</p>
            </form>
        </div>
    </main>

    <div id="contactModal" class="fixed inset-0 bg-black/90 z-50 items-center justify-center p-4 backdrop-blur-sm">
        <div class="modal-box p-10 max-w-sm w-full text-center">
            <video autoplay muted loop playsinline class="video-bg">
                <source src="{{ video_url }}" type="video/mp4">
            </video>
            <div class="video-overlay"></div>
            
            <button onclick="toggleModal()" class="absolute top-6 right-6 text-white/40">✕</button>
            <h3 class="text-3xl font-black mb-10 italic uppercase tracking-tighter">Binod Sapkota</h3>
            
            <div class="space-y-4">
                <a href="https://facebook.com/petter.boe" target="_blank" class="social-btn flex items-center p-4 rounded-2xl">
                    <span class="mr-4 text-xl">🔵</span>
                    <span class="text-[10px] font-bold uppercase">Facebook</span>
                </a>
                <a href="https://wa.me/9762418689" target="_blank" class="social-btn flex items-center p-4 rounded-2xl">
                    <span class="mr-4 text-xl">💬</span>
                    <span class="text-[10px] font-bold uppercase">WhatsApp</span>
                </a>
            </div>
        </div>
    </div>

    <script>
        function toggleModal() { document.getElementById('contactModal').classList.toggle('active'); }
        function setLang(l) {
            const t = {
                en: { title: "Secure Workspace", up: "Choose Multiple Photos", btn: "START SECURE CONVERSION ↗" },
                ne: { title: "सुरक्षित वर्कस्पेस", up: "धेरै फोटोहरू छान्नुहोस्", btn: "कन्भर्ट गर्नुहोस् ↗" }
            };
            document.getElementById('title').innerText = t[l].title;
            document.getElementById('up-text').innerText = t[l].up;
            document.getElementById('btn-convert').innerText = t[l].btn;
        }

        const input = document.getElementById('imageInput');
        const grid = document.getElementById('previewGrid');
        const placeholder = document.getElementById('drop-placeholder');

        input.onchange = () => {
            grid.innerHTML = '';
            if (input.files.length > 0) {
                placeholder.style.display = 'none';
                Array.from(input.files).forEach(file => {
                    const reader = new FileReader();
                    reader.onload = e => {
                        const img = document.createElement('img');
                        img.src = e.target.result;
                        img.className = 'preview-img';
                        grid.appendChild(img);
                    }
                    reader.readAsDataURL(file);
                });
            } else { placeholder.style.display = 'block'; }
        };
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, photo_url=PHOTO_URL, video_url=VIDEO_URL)

@app.route('/convert', methods=['POST'])
def convert():
    files = request.files.getlist('images')
    target_format = request.form.get('format', 'PDF').upper()
    if not files or files[0].filename == '': return "No files", 400
    
    imgs = [Image.open(f).convert('RGB') for f in files]
    out = io.BytesIO()
    
    if target_format == 'PDF':
        imgs[0].save(out, format='PDF', save_all=True, append_images=imgs[1:])
        mimetype, name = "application/pdf", "secure_binod.pdf"
    else:
        imgs[0].save(out, target_format, quality=95)
        mimetype, name = f"image/{target_format.lower()}", f"secure_file.{target_format.lower()}"
    
    out.seek(0)
    return send_file(out, mimetype=mimetype, as_attachment=True, download_name=name)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
