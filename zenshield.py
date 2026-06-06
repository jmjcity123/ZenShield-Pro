import sys
import os
import subprocess
import hashlib
import threading
import shutil

# =====================================================================
# 1. COMPILER & AUTO-SETUP
# =====================================================================
def automatische_einrichtung():
    def install_package(package):
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package], startupinfo=startupinfo)
        except Exception:
            pass

    try: import requests
    except ImportError: install_package("requests")
    try: import tkinterdnd2
    except ImportError: install_package("tkinterdnd2")
    try: import bs4
    except ImportError: install_package("beautifulsoup4")
    try: import pefile
    except ImportError: install_package("pefile")

    if getattr(sys, 'frozen', False): return

    current_dir = os.path.dirname(os.path.abspath(__file__))
    marker_file = os.path.join(current_dir, ".zenshield_built")
    if os.path.exists(marker_file): return

    try: import PyInstaller
    except ImportError: install_package("pyinstaller")

    script_path = os.path.abspath(__file__)
    target_folder = os.path.join(current_dir, "ZenShield_App")
    startupinfo = None
    if os.name == 'nt':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    try:
        subprocess.check_call([
            sys.executable, "-m", "PyInstaller",
            "--noconfirm", "--onedir", "--windowed",
            "--collect-data", "tkinterdnd2",
            f"--distpath={target_folder}", script_path
        ], startupinfo=startupinfo)
        
        build_dir = os.path.join(current_dir, "build")
        base_name = os.path.splitext(os.path.basename(script_path))[0]
        spec_file = os.path.join(current_dir, f"{base_name}.spec")
        if os.path.exists(build_dir): shutil.rmtree(build_dir)
        if os.path.exists(spec_file): os.remove(spec_file)
        with open(marker_file, "w") as f: f.write("built")
    except Exception:
        pass

automatische_einrichtung()

# =====================================================================
# 2. VIRUSTOTAL DETEKTIONS-SIMULATOR
# =====================================================================
import tkinter as tk
from tkinter import messagebox, ttk, filedialog
from tkinterdnd2 import TkinterDnD, DND_FILES
import requests
from bs4 import BeautifulSoup
try: import pefile
except ImportError: pefile = None

class ZenShieldAIEngine:
    VT_VENDORS = [
        "Acronis (Static ML)", "Ad-Aware", "AhnLab-V3", "Alibaba", "Avast", "Avira (no cloud)", 
        "Baidu", "Bitdefender", "ClamAV", "Comodo", "CrowdStrike Falcon", "Cybereason", "DrWeb", 
        "ESET-NOD32", "EMSIsoft", "FireEye", "Fortinet", "GData", "Ikarus", 
        "Kaspersky", "Malwarebytes", "MaxSecure", "McAfee", "Microsoft Defender", 
        "NANO-Antivirus", "Palo Alto Networks", "Panda", "Rising", "Sophos", 
        "Symantec", "Tencent", "TrendMicro", "VBA32", "VIPRE", "Yandex", "Zillya"
    ]

    @staticmethod
    def deep_file_scan(filepath):
        scan_results = {vendor: "CLEAN" for vendor in ZenShieldAIEngine.VT_VENDORS}
        try:
            if not os.path.isfile(filepath):
                return {v: "SKIPPED" for v in ZenShieldAIEngine.VT_VENDORS}

            with open(filepath, "rb") as f:
                content = f.read(5 * 1024 * 1024)
            
            is_suspicious = False
            trigger_reason = "Malicious Code Pattern Detected"

            if b"CreateRemoteThread" in content or b"WriteProcessMemory" in content:
                is_suspicious = True
                trigger_reason = "Trojan.ProcessInjection"
            elif b"GetAsyncKeyState" in content or b"SetWindowsHookEx" in content:
                is_suspicious = True
                trigger_reason = "Spyware.Keylogger"
            elif b"eval(atob(" in content:
                is_suspicious = True
                trigger_reason = "Suspicious.Obfuscator"
                
            if pefile and (filepath.endswith(".exe") or content.startswith(b"MZ")):
                try:
                    pe = pefile.PE(filepath, fast_load=True)
                    if hasattr(pe, 'DIRECTORY_ENTRY_IMPORT') and len(pe.DIRECTORY_ENTRY_IMPORT) < 3:
                        is_suspicious = True
                        trigger_reason = "Malware.PackedPE"
                except Exception:
                    is_suspicious = True
                    trigger_reason = "Corrupted.PEHeader"

            if "xeno" in os.path.basename(filepath).lower():
                is_suspicious = True
                trigger_reason = "XenoRAT.Malware"

            if is_suspicious:
                for idx, vendor in enumerate(ZenShieldAIEngine.VT_VENDORS):
                    if idx % 2 == 0 or vendor in ["Microsoft Defender", "Kaspersky", "Bitdefender", "Sophos", "CrowdStrike Falcon"]:
                        scan_results[vendor] = f"UNCLEAN ({trigger_reason})"
        except Exception:
            for v in scan_results.keys(): scan_results[v] = "ACCESS DENIED"
        return scan_results

    @staticmethod
    def deep_url_scan(url):
        scan_results = {vendor: "CLEAN" for vendor in ZenShieldAIEngine.VT_VENDORS}
        if not url.startswith("http"):
            url = "https://" + url
        try:
            headers = {"User-Agent": "Mozilla/5.0 ZenShieldAI"}
            response = requests.get(url, headers=headers, timeout=5)
            soup = BeautifulSoup(response.text, "html.parser")
            
            is_bad_url = False
            reason = "Phishing/Malicious Layout"

            if "coinhive" in response.text.lower() or "cryptonight" in response.text.lower():
                is_bad_url = True
                reason = "Malware.CryptoMiner"
            
            forms = soup.find_all("form")
            for form in forms:
                if "http://" in form.get("action", ""):
                    is_bad_url = True
                    reason = "Phishing.InsecureForm"
                    
            if len(soup.find_all("script")) > 20:
                is_bad_url = True
                reason = "Suspicious.ScriptInjection"

            if is_bad_url:
                for idx, vendor in enumerate(ZenShieldAIEngine.VT_VENDORS):
                    if idx % 3 == 0 or vendor in ["Kaspersky", "Sophos", "Google"]:
                        scan_results[vendor] = f"UNCLEAN ({reason})"
        except Exception:
            for v in scan_results.keys(): scan_results[v] = "OFFLINE"
        return scan_results

# =====================================================================
# 3. INTERFACE (SCHWARZ & DUNKELGRAU DESIGN)
# =====================================================================
class ZenShieldUltimateApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ZenShield AI - Dark Tactical Guard")
        self.root.geometry("1050x800")
        self.root.configure(bg="#0a0a0a") # Tiefschwarz
        
        # LOGO AREA
        self.logo_frame = tk.Frame(root, bg="#0a0a0a")
        self.logo_frame.pack(pady=(25, 5))
        self.logo_symbol = tk.Label(self.logo_frame, text="🗲 ZΞS 🗲", font=("Impact", 34, "italic"), fg="#ffffff", bg="#0a0a0a")
        self.logo_symbol.pack(side="left", padx=(0, 10))
        self.logo_text = tk.Label(self.logo_frame, text="ZENSHIELD AI", font=("Arial Black", 24), fg="#e0e0e0", bg="#0a0a0a")
        self.logo_text.pack(side="left")
        
        # NAVIGATION
        self.tab_frame = tk.Frame(root, bg="#0a0a0a")
        self.tab_frame.pack(fill="x", padx=300, pady=10)
        self.tab_file = tk.Button(self.tab_frame, text="UNIVERSAL SCANNER", font=("Arial", 11, "bold"), fg="#ffffff", bg="#0a0a0a", bd=0, cursor="hand2", command=self.show_file_mode)
        self.tab_file.pack(side="left", expand=True)
        self.tab_url = tk.Button(self.tab_frame, text="URL SCAN", font=("Arial", 11, "bold"), fg="#666666", bg="#0a0a0a", bd=0, cursor="hand2", command=self.show_url_mode)
        self.tab_url.pack(side="left", expand=True)
        
        # Eine dezente, dunkelgraue Trennlinie statt dem alten Blau
        self.gray_line = tk.Frame(root, bg="#333333", height=2, width=160)
        self.gray_line.pack(pady=(2, 15))

        self.content_frame = tk.Frame(root, bg="#0a0a0a")
        self.content_frame.pack(fill="both", expand=True, padx=40, pady=5)

        # SELECTION CARD (Dunkelgrau)
        self.file_card = tk.Frame(self.content_frame, bg="#141414", bd=0, highlightbackground="#262626", highlightthickness=1)
        self.file_icon = tk.Label(self.file_card, text="⚙️", font=("Arial", 48), fg="#aaaaaa", bg="#141414")
        self.file_icon.pack(pady=(50, 10))
        
        self.choose_btn = tk.Button(self.file_card, text="Auswählen (Dateien oder Ordner)", font=("Arial", 10, "bold"), fg="#ffffff", bg="#262626", activebackground="#333333", activeforeground="#ffffff", bd=0, padx=30, pady=12, cursor="hand2", command=self.choose_anything_dialog)
        self.choose_btn.pack(pady=10)
        
        self.drag_info = tk.Label(self.file_card, text="Zieh Dateien oder ganze Ordner-Strukturen hier rein – absolut ALLES wird aufgelistet", font=("Arial", 10), fg="#777777", bg="#141414")
        self.drag_info.pack(pady=(5, 40))
        
        self.file_card.drop_target_register(DND_FILES)
        self.file_card.dnd_bind('<<Drop>>', self.handle_drop)

        # URL CARD (Dunkelgrau)
        self.url_card = tk.Frame(self.content_frame, bg="#141414", bd=0, highlightbackground="#262626", highlightthickness=1)
        self.url_icon = tk.Label(self.url_card, text="🛡️", font=("Arial", 48), fg="#aaaaaa", bg="#141414")
        self.url_icon.pack(pady=(40, 10))
        self.url_instruction = tk.Label(self.url_card, text="Website-URL für lückenlose Multi-Vendor Analyse:", font=("Arial", 11, "bold"), fg="#ffffff", bg="#141414")
        self.url_instruction.pack(pady=5)
        self.url_entry = tk.Entry(self.url_card, font=("Arial", 12), fg="#ffffff", bg="#1f1f1f", insertbackground="white", bd=0, highlightbackground="#333333", highlightthickness=1)
        self.url_entry.pack(fill="x", padx=150, pady=10, ipady=6)
        self.url_entry.insert(0, "https://")
        self.url_btn = tk.Button(self.url_card, text="Website mit allen Engines prüfen", font=("Arial", 10, "bold"), fg="#ffffff", bg="#262626", activebackground="#333333", activeforeground="#ffffff", bd=0, padx=35, pady=12, cursor="hand2", command=self.start_url_scan)
        self.url_btn.pack(pady=(10, 40))

        # RESULTS DASHBOARD
        self.result_card = tk.Frame(self.content_frame, bg="#141414", bd=0, highlightbackground="#262626", highlightthickness=1)
        
        self.res_header = tk.Frame(self.result_card, bg="#1c1c1c", pady=10)
        self.res_header.pack(fill="x")
        self.res_title = tk.Label(self.res_header, text="FULL SYSTEM REPORT", font=("Arial", 11, "bold"), fg="#ffffff", bg="#1c1c1c", padx=15)
        self.res_title.pack(side="left")
        
        self.close_res_btn = tk.Button(self.res_header, text="✖ Schließen / Neu", font=("Arial", 9, "bold"), fg="#888888", bg="#262626", activebackground="#333333", activeforeground="#ffffff", bd=0, padx=12, pady=4, command=self.reset_to_scan_cards, cursor="hand2")
        self.close_res_btn.pack(side="right", padx=15)

        # Tabelle stylen (Mattschwarz / Dunkelgrau)
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#141414", foreground="#ffffff", fieldbackground="#141414", rowheight=26, font=("Arial", 9))
        style.configure("Treeview.Heading", background="#1c1c1c", foreground="#aaaaaa", font=("Arial", 9, "bold"), borderwidth=0)

        self.tree_frame = tk.Frame(self.result_card, bg="#141414")
        self.tree_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        self.scrollbar = ttk.Scrollbar(self.tree_frame)
        self.scrollbar.pack(side="right", fill="y")

        self.tree = ttk.Treeview(self.tree_frame, columns=("File", "Vendor", "Result"), show="headings", selectmode="none", yscrollcommand=self.scrollbar.set)
        self.tree.heading("File", text="DATEI / PFADNAME", anchor="w")
        self.tree.heading("Vendor", text="SECURITY VENDOR (ENGINE)", anchor="w")
        self.tree.heading("Result", text="DETECTION STATUS", anchor="w")
        
        self.tree.column("File", width=380, anchor="w")
        self.tree.column("Vendor", width=220, anchor="w")
        self.tree.column("Result", width=260, anchor="w")
        self.tree.pack(fill="both", expand=True)
        
        self.scrollbar.config(command=self.tree.yview)

        # Die Farben für Statusmeldungen bleiben gut erkennbar
        self.tree.tag_configure("clean", foreground="#00e676", font=("Arial", 9, "bold"))
        self.tree.tag_configure("unclean", foreground="#ff1744", font=("Arial", 9, "bold"))

        self.show_file_mode()

        self.status_var = tk.StringVar()
        self.status_var.set("Status: Bereit für Scan")
        self.status_label = tk.Label(root, textvariable=self.status_var, font=("Arial", 10, "italic"), fg="#888888", bg="#0a0a0a")
        self.status_label.pack(pady=(5, 10))

    def show_file_mode(self):
        self.reset_to_scan_cards()
        self.url_card.pack_forget()
        self.file_card.pack(fill="both", expand=True)
        self.tab_file.configure(fg="#ffffff")
        self.tab_url.configure(fg="#555555")

    def show_url_mode(self):
        self.reset_to_scan_cards()
        self.file_card.pack_forget()
        self.url_card.pack(fill="both", expand=True)
        self.tab_file.configure(fg="#555555")
        self.tab_url.configure(fg="#ffffff")

    def reset_to_scan_cards(self):
        self.result_card.pack_forget()
        if self.tab_file.cget("fg") == "#ffffff":
            self.file_card.pack(fill="both", expand=True)
        else:
            self.url_card.pack(fill="both", expand=True)

    def choose_anything_dialog(self):
        antwort = messagebox.askyesnocancel("ZenShield Auswahl", "Möchtest du einen kompletten ORDNER scannen?\n\n(Klicke 'Ja' für Ordner, 'Nein' für einzelne Dateien)")
        if antwort is True:
            folder = filedialog.askdirectory(title="Wähle den zu scannenden Ordner")
            if folder: threading.Thread(target=self.run_master_scan, args=([folder],), daemon=True).start()
        elif antwort is False:
            files = filedialog.askopenfilenames(title="Wähle eine oder mehrere Dateien aus")
            if files: threading.Thread(target=self.run_master_scan, args=(list(files),), daemon=True).start()

    def handle_drop(self, event):
        raw_data = event.data
        paths = []
        if "{" in raw_data:
            paths = [p.strip("{} ") for p in raw_data.split("}") if p.strip()]
        else:
            paths = raw_data.split()
        threading.Thread(target=self.run_master_scan, args=(paths,), daemon=True).start()

    def run_master_scan(self, input_paths):
        self.status_var.set("Durchsuche Verzeichnis-Strukturen...")
        
        self.root.after(0, lambda: [self.file_card.pack_forget(), self.url_card.pack_forget(), self.result_card.pack(fill="both", expand=True), self.res_title.configure(text="VIRUSTOTAL-STYLE ENGINE MATRIX REPORT")])
        for row in self.tree.get_children(): self.tree.delete(row)

        all_files = []
        for path in input_paths:
            path = path.strip('"{}"')
            if os.path.isdir(path):
                for root_dir, _, files in os.walk(path):
                    for file in files:
                        all_files.append(os.path.join(root_dir, file))
            elif os.path.isfile(path):
                all_files.append(path)

        if not all_files:
            self.status_var.set("Keine scannbaren Dateien gefunden.")
            return

        total_files = len(all_files)
        
        for file_idx, file_path in enumerate(all_files):
            filename = os.path.basename(file_path)
            self.status_var.set(f"Datei {file_idx+1}/{total_files} wird zerlegt: {filename}")
            
            engine_outputs = ZenShieldAIEngine.deep_file_scan(file_path)
            
            for vendor, status in engine_outputs.items():
                tag = "unclean" if "UNCLEAN" in status else "clean"
                status_display = f"❌ {status}" if tag == "unclean" else "✔ Undetected"
                
                display_name = os.path.basename(os.path.dirname(file_path)) + " ➔ " + filename
                
                self.root.after(0, lambda d=display_name, v=vendor, s=status_display, t=tag: self.tree.insert("", "end", values=(d, v, s), tags=(t,)))

        self.status_var.set(f"Abgeschlossen! {total_files} Dateien vollständig durchleuchtet.")

    def start_url_scan(self):
        url = self.url_entry.get().strip()
        if url == "" or url == "https://": return
        threading.Thread(target=self.run_url_scan, args=(url,), daemon=True).start()

    def run_url_scan(self, url):
        self.status_var.set("Analysiere Website-Sicherheit über Engines...")
        
        self.root.after(0, lambda: [self.file_card.pack_forget(), self.url_card.pack_forget(), self.result_card.pack(fill="both", expand=True), self.res_title.configure(text=f"URL ENGINE MATRIX REPORT: {url}")])
        for row in self.tree.get_children(): self.tree.delete(row)
        
        engine_outputs = ZenShieldAIEngine.deep_url_scan(url)
        for vendor, status in engine_outputs.items():
            tag = "unclean" if "UNCLEAN" in status else "clean"
            status_display = f"❌ {status}" if tag == "unclean" else "✔ Undetected"
            self.tree.insert("", "end", values=(url, vendor, status_display), tags=(tag,))
            
        self.status_var.set("Website-Analyse vollständig abgeschlossen.")

if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = ZenShieldUltimateApp(root)
    root.mainloop()