#!/usr/bin/env python3
"""
.DOOM JAVA IDE - Backend & Windows Desktop Launcher
Free Fire Themed Java IDE
"""

import http.server
import json
import os
import re
import shutil
import socketserver
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
import urllib.parse
import webbrowser

# Ensure UTF-8 output in Windows console
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

PORT = 5055
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PUBLIC_DIR = os.path.join(BASE_DIR, "public")
PROJECTS_DIR = os.path.join(BASE_DIR, "projects")
PORTABLE_JDK_DIR = os.path.join(BASE_DIR, "jdk")

os.makedirs(PUBLIC_DIR, exist_ok=True)
os.makedirs(PROJECTS_DIR, exist_ok=True)

# Create a default starter file if none exists
DEFAULT_STARTER_CODE = """// .DOOM JAVA IDE - Free Fire Edition
// BOOYAH! Ready to code.
import java.util.*;

public class Main {
    public static void main(String[] args) {
        System.out.println("=========================================");
        System.out.println("   🔥 WELCOME TO .DOOM JAVA IDE 🔥       ");
        System.out.println("   🎮 FREE FIRE BATTLE ROYALE EDITION   ");
        System.out.println("=========================================");
        
        String rank = "HEROIC / GRANDMASTER";
        int diamonds = 9999;
        int booyahs = 42;
        
        System.out.printf("Player Rank: %s%n", rank);
        System.out.printf("Dev Diamonds: %d 💎%n", diamonds);
        System.out.printf("Total Booyahs: %d 🏆%n%n", booyahs);
        
        // Java Stream Example
        List<String> weapons = Arrays.asList("AWM", "MP40", "M1887", "SCAR", "GROZA", "DESERT EAGLE");
        System.out.println("⚔️ ARSENAL WEAPONS LOADED:");
        weapons.stream()
               .filter(w -> w.length() > 3)
               .forEach(w -> System.out.println("  [+] " + w + " - Ready for Combat"));
               
        System.out.println("\\n🚀 Status: 100% READY - BOOYAH!");
    }
}
"""

starter_file = os.path.join(PROJECTS_DIR, "Main.java")
if not os.path.exists(starter_file):
    with open(starter_file, "w", encoding="utf-8") as f:
        f.write(DEFAULT_STARTER_CODE)

def detect_jdk(custom_path=None):
    """Detect if local JDK (javac and java) is available."""
    # 1. Custom path override
    if custom_path and os.path.exists(custom_path):
        custom_javac = os.path.join(custom_path, "bin", "javac.exe" if os.name == "nt" else "javac")
        custom_java = os.path.join(custom_path, "bin", "java.exe" if os.name == "nt" else "java")
        if os.path.exists(custom_javac) and os.path.exists(custom_java):
            return {
                "available": True,
                "javac": custom_javac,
                "java": custom_java,
                "version": f"Custom JDK at {custom_path}",
                "type": "local"
            }

    # 2. Bundled portable OpenJDK 21 in app directory
    if os.path.exists(PORTABLE_JDK_DIR):
        portable_javac = os.path.join(PORTABLE_JDK_DIR, "bin", "javac.exe" if os.name == "nt" else "javac")
        portable_java = os.path.join(PORTABLE_JDK_DIR, "bin", "java.exe" if os.name == "nt" else "java")
        if os.path.exists(portable_javac) and os.path.exists(portable_java):
            try:
                res_ver = subprocess.run([portable_javac, "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=3)
                v = (res_ver.stdout or res_ver.stderr).strip()
                return {
                    "available": True,
                    "javac": portable_javac,
                    "java": portable_java,
                    "version": f"Built-in OpenJDK 21 ({v})",
                    "type": "local"
                }
            except Exception:
                pass

    # 3. System PATH javac/java
    try:
        res_javac = subprocess.run(["javac", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=3)
        javac_ver = (res_javac.stdout or res_javac.stderr).strip()
        res_java = subprocess.run(["java", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=3)
        java_ver = (res_java.stdout or res_java.stderr).splitlines()[0] if (res_java.stdout or res_java.stderr) else "Java Runtime"
        return {
            "available": True,
            "javac": "javac",
            "java": "java",
            "version": f"{javac_ver} / {java_ver}",
            "type": "local"
        }
    except Exception:
        pass

    # 4. Check standard Windows Program Files directories
    if os.name == "nt":
        common_roots = [
            r"C:\Program Files\Eclipse Adoptium",
            r"C:\Program Files\Java",
            r"C:\Program Files\Microsoft",
            r"C:\Program Files\Amazon Corretto",
            r"C:\Program Files\Zulu",
            r"C:\Program Files (x86)\Java",
            os.path.expandvars(r"%LOCALAPPDATA%\Programs")
        ]
        for root in common_roots:
            if os.path.exists(root):
                for sub in os.listdir(root):
                    cand_dir = os.path.join(root, sub)
                    cand_javac = os.path.join(cand_dir, "bin", "javac.exe")
                    cand_java = os.path.join(cand_dir, "bin", "java.exe")
                    if os.path.exists(cand_javac) and os.path.exists(cand_java):
                        return {
                            "available": True,
                            "javac": cand_javac,
                            "java": cand_java,
                            "version": f"Discovered at {cand_dir}",
                            "type": "local"
                        }

    return {
        "available": False,
        "javac": None,
        "java": None,
        "version": "Online Cloud Engine (JDK not detected on PATH)",
        "type": "cloud"
    }

def execute_java_locally(javac_path, java_path, code, stdin_text="", class_name="Main"):
    """Compile and execute Java code on the local machine."""
    start_time = time.time()
    with tempfile.TemporaryDirectory() as tmpdir:
        java_src = os.path.join(tmpdir, f"{class_name}.java")
        with open(java_src, "w", encoding="utf-8") as f:
            f.write(code)

        # Compile
        compile_proc = subprocess.run(
            [javac_path, "-encoding", "UTF-8", java_src],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=15
        )

        compile_time = int((time.time() - start_time) * 1000)

        if compile_proc.returncode != 0:
            err_output = compile_proc.stderr or compile_proc.stdout
            clean_err = err_output.replace(tmpdir + os.sep, "").replace(tmpdir, "")
            return {
                "success": False,
                "stage": "compile",
                "output": "",
                "error": clean_err,
                "executionTimeMs": compile_time,
                "engine": "Local OpenJDK 21"
            }

        # Run
        exec_start = time.time()
        try:
            run_proc = subprocess.run(
                [java_path, "-cp", tmpdir, class_name],
                input=stdin_text,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=12
            )
            exec_time = int((time.time() - exec_start) * 1000)
            
            clean_stderr = run_proc.stderr.replace(tmpdir + os.sep, "").replace(tmpdir, "") if run_proc.stderr else ""
            is_success = (run_proc.returncode == 0)
            
            return {
                "success": is_success,
                "stage": "runtime",
                "output": run_proc.stdout,
                "error": clean_stderr,
                "exitCode": run_proc.returncode,
                "executionTimeMs": exec_time,
                "engine": "Local OpenJDK 21"
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stage": "runtime",
                "output": "",
                "error": "⏱️ TIME LIMIT EXCEEDED (12 seconds) - Infinite loop detected or awaiting input.",
                "exitCode": -1,
                "executionTimeMs": 12000,
                "engine": "Local OpenJDK 21"
            }
        except Exception as e:
            return {
                "success": False,
                "stage": "runtime",
                "output": "",
                "error": str(e),
                "exitCode": -1,
                "executionTimeMs": int((time.time() - exec_start) * 1000),
                "engine": "Local OpenJDK 21"
            }

def extract_class_name(code):
    """Extract public class name from Java code, default to 'Main'."""
    match = re.search(r'public\s+class\s+([a-zA-Z_$][a-zA-Z\d_$]*)', code)
    if match:
        return match.group(1)
    match_any = re.search(r'class\s+([a-zA-Z_$][a-zA-Z\d_$]*)', code)
    if match_any:
        return match_any.group(1)
    return "Main"

class DoomRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=PUBLIC_DIR, **kwargs)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        if path == "/api/status":
            custom_path = query.get("jdk_path", [None])[0]
            status = detect_jdk(custom_path)
            self._send_json(status)
            return

        if path == "/api/files":
            files = []
            for fname in os.listdir(PROJECTS_DIR):
                if fname.endswith(".java"):
                    fpath = os.path.join(PROJECTS_DIR, fname)
                    stat = os.stat(fpath)
                    files.append({
                        "name": fname,
                        "size": stat.st_size,
                        "modified": int(stat.st_mtime * 1000)
                    })
            files.sort(key=lambda x: x["name"])
            self._send_json({"files": files})
            return

        if path == "/api/files/load":
            name = query.get("name", ["Main.java"])[0]
            safe_name = os.path.basename(name)
            fpath = os.path.join(PROJECTS_DIR, safe_name)
            if os.path.exists(fpath):
                with open(fpath, "r", encoding="utf-8") as f:
                    content = f.read()
                self._send_json({"name": safe_name, "content": content})
            else:
                self._send_json({"error": "File not found"}, status=404)
            return

        super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length).decode('utf-8') if length > 0 else "{}"
        
        try:
            data = json.loads(body)
        except Exception:
            data = {}

        if path == "/api/run":
            code = data.get("code", "")
            stdin_text = data.get("stdin", "")
            custom_jdk = data.get("customJdkPath", "")
            
            class_name = extract_class_name(code)
            jdk_info = detect_jdk(custom_jdk)

            if jdk_info["available"]:
                result = execute_java_locally(
                    jdk_info["javac"], 
                    jdk_info["java"], 
                    code, 
                    stdin_text, 
                    class_name
                )
            else:
                result = {
                    "success": False,
                    "stage": "runtime",
                    "output": "",
                    "error": "Local JDK not detected. Please ensure OpenJDK 21 is present in the jdk/ directory.",
                    "exitCode": 1,
                    "executionTimeMs": 0,
                    "engine": "Local JDK"
                }
            
            self._send_json(result)
            return

        if path == "/api/files/save":
            name = data.get("name", "Main.java")
            content = data.get("content", "")
            safe_name = os.path.basename(name)
            if not safe_name.endswith(".java"):
                safe_name += ".java"
            fpath = os.path.join(PROJECTS_DIR, safe_name)
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(content)
            self._send_json({"success": True, "name": safe_name})
            return

        if path == "/api/files/delete":
            name = data.get("name", "")
            safe_name = os.path.basename(name)
            if safe_name == "Main.java":
                self._send_json({"error": "Cannot delete default Main.java"}, status=400)
                return
            fpath = os.path.join(PROJECTS_DIR, safe_name)
            if os.path.exists(fpath):
                os.remove(fpath)
                self._send_json({"success": True})
            else:
                self._send_json({"error": "File not found"}, status=404)
            return

        self._send_json({"error": "Endpoint not found"}, status=404)

    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

def launch_desktop_window(url):
    """Launch Microsoft Edge or Google Chrome in dedicated frameless App Mode."""
    time.sleep(0.8)
    
    edge_paths = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
    ]
    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe")
    ]

    for p in edge_paths + chrome_paths:
        if os.path.exists(p):
            try:
                subprocess.Popen([p, f"--app={url}", "--start-maximized", "--window-size=1400,900"])
                print(f"[+] .DOOM JAVA IDE launched in Native App Mode via: {p}")
                return
            except Exception as e:
                print(f"[!] App mode launch failed: {e}")

    # Fallback to default browser
    webbrowser.open(url)

class ReusableTCPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True

def main():
    port = PORT
    url = f"http://localhost:{port}"
    
    # Try finding an available port if 5055 is in use
    server = None
    for p in range(PORT, PORT + 20):
        try:
            server = ReusableTCPServer(("127.0.0.1", p), DoomRequestHandler)
            port = p
            url = f"http://localhost:{port}"
            break
        except OSError:
            continue

    if not server:
        print("[!] Could not bind to any port.")
        sys.exit(1)

    print("=" * 60)
    print("  [+] .DOOM JAVA IDE - FREE FIRE BATTLE ROYALE EDITION [+]")
    print(f"  [+] Running at: {url}")
    print("=" * 60)

    # Launch desktop window in a background thread if not testing
    if "--no-browser" not in sys.argv and "--test" not in sys.argv:
        t = threading.Thread(target=launch_desktop_window, args=(url,), daemon=True)
        t.start()

    if "--test" in sys.argv:
        print("[+] Test mode active - server configured successfully.")
        return

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[+] Shutting down .DOOM JAVA IDE server.")
        server.shutdown()

if __name__ == "__main__":
    main()
