import os
import sys
import urllib.request
import zipfile
import shutil

JDK_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jdk")
ZIP_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "openjdk21.zip")

ADOPTIUM_URL = "https://api.adoptium.net/v3/binary/latest/21/ga/windows/x64/jdk/hotspot/normal/eclipse"

def download_and_extract_jdk():
    if os.path.exists(os.path.join(JDK_DIR, "bin", "javac.exe")):
        print("[+] Portable JDK 21 already installed at:", JDK_DIR)
        return True

    print("[!] Downloading Portable Eclipse Temurin OpenJDK 21 (Windows x64)...")
    req = urllib.request.Request(ADOPTIUM_URL, headers={"User-Agent": "DOOM-Java-IDE-Setup"})
    
    with urllib.request.urlopen(req, timeout=60) as resp, open(ZIP_PATH, 'wb') as out_file:
        total_len = resp.headers.get('Content-Length')
        total_len = int(total_len) if total_len else None
        downloaded = 0
        block_size = 1024 * 1024 * 4 # 4MB chunks
        
        while True:
            chunk = resp.read(block_size)
            if not chunk:
                break
            out_file.write(chunk)
            downloaded += len(chunk)
            if total_len:
                pct = int((downloaded / total_len) * 100)
                print(f"\rDownloading JDK 21: {pct}% ({downloaded // (1024*1024)}MB / {total_len // (1024*1024)}MB)", end="")
            else:
                print(f"\rDownloaded {downloaded // (1024*1024)}MB...", end="")

    print("\n[!] Extracting OpenJDK 21 archive...")
    extract_temp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jdk_temp")
    os.makedirs(extract_temp, exist_ok=True)
    
    with zipfile.ZipFile(ZIP_PATH, 'r') as zip_ref:
        zip_ref.extractall(extract_temp)

    # Move inner root folder to 'jdk'
    inner_items = os.listdir(extract_temp)
    if len(inner_items) == 1 and os.path.isdir(os.path.join(extract_temp, inner_items[0])):
        inner_root = os.path.join(extract_temp, inner_items[0])
        if os.path.exists(JDK_DIR):
            shutil.rmtree(JDK_DIR)
        shutil.move(inner_root, JDK_DIR)
    else:
        if os.path.exists(JDK_DIR):
            shutil.rmtree(JDK_DIR)
        shutil.move(extract_temp, JDK_DIR)

    # Cleanup
    if os.path.exists(extract_temp):
        shutil.rmtree(extract_temp, ignore_errors=True)
    if os.path.exists(ZIP_PATH):
        os.remove(ZIP_PATH)

    javac_path = os.path.join(JDK_DIR, "bin", "javac.exe")
    if os.path.exists(javac_path):
        print(f"\n[SUCCESS] Portable OpenJDK 21 ready at: {JDK_DIR}")
        return True
    else:
        print("\n[!] Extraction finished but javac.exe not found at expected path.")
        return False

if __name__ == "__main__":
    download_and_extract_jdk()
