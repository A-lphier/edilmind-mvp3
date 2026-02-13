"""
run_app.py - Launcher principale
"""
import subprocess
import sys

if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════╗
    ║   🏗️  EDILMIND ENTERPRISE               ║
    ║   Avvio sistema...                       ║
    ╚══════════════════════════════════════════╝
    """)
    
    subprocess.run([sys.executable, "-m", "streamlit", "run", "src/ui/app.py"])