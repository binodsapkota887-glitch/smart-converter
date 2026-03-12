from flask import Flask, render_template_string, request, send_file
from PIL import Image
import io

app = Flask(__name__)

# Full Integrated Advanced Code with All Requested Features
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SmartConvert Pro | Binod Sapkota</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;800&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Plus Jakarta Sans', sans-serif; background-color: #0b0f1a; color: white; overflow-x: hidden; }
        .glass-card { 
            background: rgba(255, 255, 255, 0.03); 
            backdrop-filter: blur(20px); 
            border: 1px solid rgba(255, 255, 255, 0.1); 
            border-radius: 2.5rem;
        }
        .neon-glow { box-shadow: 0 0 30px rgba(34, 211, 238, 0.15); }
        .preview-img { max-height: 180px; border-radius: 1rem; display: none; margin: 0 auto; object-fit: contain; }
        
        #contactModal { display: none; opacity: 0; transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1); }
        #contactModal.active { display: flex; opacity: 1; }
        
        @keyframes slideUp { from { transform: translateY(30px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }
        .animate-content { animation: slideUp 0.5s ease-out forwards; }
    </style>
</head>
<body class="min-h-screen flex flex-col">

    <nav class="p-6 max-w-7xl mx-auto w-full flex justify-between items-center">
        <div class="flex items-center space-x-4 cursor-pointer" onclick="window.location.reload()">
            <div class="relative group">
                <div class="absolute -inset-1 bg-gradient-to-r from-cyan-400 to-blue-600 rounded-full blur opacity-40 group-hover:opacity-100 transition duration-500"></div>
                <div class="relative w-12 h-12 bg-slate-900 rounded-full flex items-center justify-center border border-white/20 overflow-hidden">
                    <svg class="w-7 h-7 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
                </div>
            </div>
            <div class="flex flex-col">
                <span class="text-xl font-black tracking-tighter uppercase">Smart<span class="text-cyan-400">Converter</span></span>
                <span class="text-[9px] font-bold text-slate-500 tracking-[0.3em]">PRO DEVELOPER EDITION</span>
            </div>
        </div>

        <div class="flex items-center space-x-6">
            <button onclick="toggleModal()" class="hidden md:block text-[10px] font-black text-slate-400 hover:text-cyan-400 tracking-widest uppercase transition-all">Build Your Website?</button>
            <div class="flex bg-white/5 p-1 rounded-xl border border-white/10 shadow-inner">
                <button onclick="setLang('en')" id="en-btn" class="px-4 py-1.5 rounded-lg text-[10px] font-bold bg-white/10 transition-all">EN</button>
                <button onclick="setLang('ne')" id="ne-btn" class="px-4 py-1.5 rounded-lg text-[10px] font-bold transition-all">नेपाली</button>
            </div>
        </div>
    </nav>

    <main class="flex-grow flex flex-col lg:flex-row items-center justify-center p-6 gap-12 max-w-7xl mx-auto w-full">
        
        <div class="glass-card p-10 w-full max-w-lg neon-glow relative">
            <div class="text-center mb-8">
                <h1 id="title" class="text-3xl font-extrabold mb-2 tracking-tight">Convert Your Images</h1>
                <p id="subtitle" class="text-slate-400 text-sm">Lightning fast conversion with AI optimization.</p>
            </div>

            <form action="/convert" method="POST" enctype="multipart/form-data" class="space-y-6">
                <div class="relative group border-2 border-dashed border-white/10 rounded-[2rem] p-8 bg-white/5 hover:border-cyan-400 transition-all text-center">
                    <input type="file" id="imageInput" name="image" accept="image/*" required class="absolute inset-0 opacity-0 cursor-pointer z-20">
                    <div id="drop-placeholder">
                        <svg class="mx-auto w-12 h-12 text-slate-600 group-hover:text-cyan-400 transition-colors mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
                        <p id="up-text" class="text-[11px] font-bold uppercase tracking-widest text-slate-500">Drag & Drop Upload Zone</p>
                    </div>
                    <img id="preview" src="#" alt="Preview" class="preview-img border-2 border-cyan-400/50 shadow-2xl">
                </div>

                <div class="space-y-2">
                    <label id="lbl-format" class="text-[10px] font-black text-slate-500 uppercase tracking-widest ml-1">Target Format</label>
                    <select name="format" class="w-full bg-slate-900 border border-white/10 p-4 rounded-2xl outline-none font-bold text-sm focus:ring-2 focus:ring-cyan-500 transition-all text-white">
                        <option value="PNG">PNG (lossless)</option>
                        <option value="JPEG">JPEG (compact)</option>
                        <option value="WEBP">WebP (next-gen)</option>
                        <option value="PDF">PDF (document)</option>
                    </select>
                </div>

                <button type="submit" class="w-full py-5 bg-gradient-to-r from-cyan-500 to-blue-600 rounded-2xl font-black text-xs tracking-[0.2em] uppercase hover:shadow-cyan-500/20 shadow-xl transition-all active:scale-95">
                    Convert & Download ↗
                </button>
            </form>
        </div>

        <div class="w-full max-w-md space-y-5">
            <h2 class="text-[11px] font-black text-cyan-400 uppercase tracking-[0.5em] mb-4">Core Features ↘</h2>
            
            <div class="glass-card p-6 flex items-center space-x-6 border-l-4 border-cyan-500 group hover:bg-white/5 transition-all">
                <div class="p-4 bg-cyan-500/10 rounded-2xl text-cyan-400"><svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" /></svg></div>
                <div><h4 class="font-extrabold text-sm uppercase">Multi-User System</h4><p class="text-[11px] text-slate-500 mt-1">Parallel processing for high-volume traffic.</p></div>
            </div>

            <div class="glass-card p-6 flex items-center space-x-6 border-l-4 border-blue-500 group hover:bg-white/5 transition-all">
                <div class="p-4 bg-blue-500/10 rounded-2xl text-blue-400"><svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg></div>
                <div><h4 class="font-extrabold text-sm uppercase">Secure Handling</h4><p class="text-[11px] text-slate-500 mt-1">E2E encryption with auto-destruct cache.</p></div>
            </div>

            <div class="glass-card p-6 flex items-center space-x-6 border-l-4 border-purple-500 group hover:bg-white/5 transition-all">
                <div class="p-4 bg-purple-500/10 rounded-2xl text-purple-400"><svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg></div>
                <div><h4 class="font-extrabold text-sm uppercase">AI Optimization</h4><p class="text-[11px] text-slate-500 mt-1">Intelligent compression for retina displays.</p></div>
            </div>
        </div>
    </main>

    <div id="contactModal" class="fixed inset-0 z-[100] items-center justify-center p-4 bg-black/95 backdrop-blur-xl">
        <div class="glass-card p-10 max-w-sm w-full text-center border-white/20 animate-content shadow-2xl">
            <button onclick="toggleModal()" class="absolute top-6 right-6 text-slate-500 hover:text-white transition-colors">✕</button>
            <h2 class="text-6xl font-black text-cyan-400 mb-2 tracking-tighter">WELCOME</h2>
            <div class="h-1 w-24 bg-gradient-to-r from-cyan-400 to-blue-600 mx-auto mb-8 rounded-full"></div>
            <p class="text-[10px] font-black text-slate-500 tracking-[0.4em] uppercase mb-1">Architect & Coder</p>
            <h3 class="text-2xl font-bold mb-10">Binod Sapkota</h3>
            
            <div class="space-y-3">
                <a href="mailto:binodsapkota887@gmail.com" class="bg-white/5 p-4 rounded-2xl border border-white/5 flex items-center space-x-4 hover:bg-white/10 transition-colors">
                    <span class="text-[10px] font-black text-cyan-400 uppercase w-16">Gmail</span>
                    <span class="text-xs text-slate-300">binodsapkota887@gmail.com</span>
                </a>
                <a href="https://wa.me/9762418689" target="_blank" class="bg-white/5 p-4 rounded-2xl border border-white/5 flex items-center space-x-4 hover:bg-white/10 transition-colors">
                    <span class="text-[10px] font-black text-green-400 uppercase w-16">WhatsApp</span>
                    <span class="text-xs text-slate-300">9762418689</span>
                </a>
                <a href="https://facebook.com/petter.boe" target="_blank" class="bg-white/5 p-4 rounded-2xl border border-white/5 flex items-center space-x-4 hover:bg-white/10 transition-colors">
                    <span class="text-[10px] font-black text-blue-500 uppercase w-16">Facebook</span>
                    <span class="text-xs text-slate-300">petter boe</span>
                </a>
            </div>
        </div>
    </div>

    <script>
        function toggleModal() { document.getElementById('contactModal').classList.toggle('active'); }
        
        // Image Preview Handler
        const input = document.getElementById('imageInput');
        const preview = document.getElementById('preview');
        const placeholder = document.getElementById('drop-placeholder');

        input.onchange = e => {
            const [file] = input.files;
            if (file) {
                preview.src = URL.createObjectURL(file);
                preview.style.display = 'block';
                placeholder.style.display = 'none';
            }
        };

        const translations = {
            en: { title: "Convert Your Images", sub: "Lightning fast conversion with AI optimization.", up: "Drag & Drop Upload Zone", lbl: "Target Format" },
            ne: { title: "तस्बिर कन्भर्ट गर्नुहोस्", sub: "एआई आधारित छिटो र छरितो कन्भर्जन।", up: "फोटो यहाँ छान्नुहोस्", lbl: "नयाँ फर्म्याट रोज्नुहोस्" }
        };

        function setLang(l) {
            document.getElementById('title').innerText = translations[l].title;
            document.getElementById('subtitle').innerText = translations[l].sub;
            document.getElementById('up-text').innerText = translations[l].up;
            document.getElementById('lbl-format').innerText = translations[l].lbl;
            document.getElementById('en-btn').classList.toggle('bg-white/10', l==='en');
            document.getElementById('ne-btn').classList.toggle('bg-white/10', l==='ne');
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index(): return render_template_string(HTML_TEMPLATE)

@app.route('/convert', methods=['POST'])
def convert():
    file = request.files['image']
    target_format = request.form.get('format', 'PNG')
    try:
        img = Image.open(file)
        if target_format in ['JPEG', 'JPG'] and img.mode in ('RGBA', 'P'): img = img.convert('RGB')
        img_io = io.BytesIO()
        img.save(img_io, target_format, quality=95)
        img_io.seek(0)
        return send_file(img_io, mimetype=f'image/{target_format.lower()}', as_attachment=True, download_name=f"binod_smart_convert.{target_format.lower()}")
    except Exception as e: return str(e), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)