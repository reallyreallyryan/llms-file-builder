#!/usr/bin/env python3
"""
Build script for creating LLMS File Builder Mac app
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path

# Configuration
APP_NAME = "LLMS File Builder"
BUNDLE_ID = "com.yourcompany.llmsfilebuilder"
VERSION = "1.0.0"
ICON_FILE = "icon.icns"  # We'll create this

def create_icon():
    """Create a simple icon file (or use existing)"""
    # For now, we'll use PyInstaller's default icon
    # You can replace this with a custom icon later
    return None

def create_launcher_script():
    """Create the script that launches Streamlit"""
    launcher_content = '''#!/usr/bin/env python3
import os
import sys
import subprocess
import webbrowser
import time
import socket
from pathlib import Path

def find_free_port():
    """Find a free port to run Streamlit on"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port

def main():
    # Set up paths
    if getattr(sys, 'frozen', False):
        # Running as compiled app
        base_path = sys._MEIPASS
    else:
        # Running as script
        base_path = Path(__file__).parent
    
    # Change to app directory
    os.chdir(base_path)
    
    # Find free port
    port = find_free_port()
    
    # Set Streamlit config
    os.environ["STREAMLIT_SERVER_PORT"] = str(port)
    os.environ["STREAMLIT_SERVER_HEADLESS"] = "true"
    os.environ["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
    
    # Launch Streamlit
    streamlit_cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        "app.py",
        "--server.port", str(port),
        "--server.headless", "true",
        "--browser.gatherUsageStats", "false"
    ]
    
    # Start Streamlit process
    process = subprocess.Popen(streamlit_cmd)
    
    # Wait a moment for server to start
    time.sleep(3)
    
    # Open browser
    webbrowser.open(f"http://localhost:{port}")
    
    # Wait for process to complete
    try:
        process.wait()
    except KeyboardInterrupt:
        process.terminate()
        sys.exit(0)

if __name__ == "__main__":
    main()
'''
    
    with open("launcher.py", "w") as f:
        f.write(launcher_content)
    
    return "launcher.py"

def create_spec_file():
    """Create PyInstaller spec file"""
    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Collect all backend modules
backend_path = 'backend'
backend_modules = []
for root, dirs, files in os.walk(backend_path):
    for file in files:
        if file.endswith('.py'):
            module_path = os.path.join(root, file)
            backend_modules.append((module_path, root))

a = Analysis(
    ['launcher.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('app.py', '.'),
        ('backend', 'backend'),
        ('requirements.txt', '.'),
        ('.env.example', '.'),
    ],
    hiddenimports=[
        'streamlit',
        'pandas',
        'numpy',
        'openai',
        'tiktoken',
        'dotenv',
        'altair',
        'pillow',
        'requests',
        'tornado',
        'validators',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='launcher',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=True,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='launcher',
)

app = BUNDLE(
    coll,
    name='{APP_NAME}.app',
    icon={repr(ICON_FILE) if ICON_FILE else 'None'},
    bundle_identifier='{BUNDLE_ID}',
    version='{VERSION}',
    info_plist={{
        'CFBundleName': '{APP_NAME}',
        'CFBundleDisplayName': '{APP_NAME}',
        'CFBundleIdentifier': '{BUNDLE_ID}',
        'CFBundleVersion': '{VERSION}',
        'CFBundleShortVersionString': '{VERSION}',
        'CFBundlePackageType': 'APPL',
        'CFBundleExecutable': 'launcher',
        'LSMinimumSystemVersion': '10.13.0',
        'NSHighResolutionCapable': True,
        'NSAppleScriptEnabled': False,
        'NSHumanReadableCopyright': 'Copyright © 2024 Your Company. All rights reserved.',
    }},
)
'''
    
    with open("llms_builder.spec", "w") as f:
        f.write(spec_content)
    
    return "llms_builder.spec"

def check_dependencies():
    """Check if required tools are installed"""
    print("🔍 Checking dependencies...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        return False
    
    # Check if PyInstaller is installed
    try:
        import PyInstaller
        print("✅ PyInstaller found")
    except ImportError:
        print("❌ PyInstaller not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # Check if required packages are installed
    required = ["streamlit", "pandas", "numpy", "openai", "tiktoken", "python-dotenv"]
    missing = []
    
    for package in required:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"⚠️  Missing packages: {', '.join(missing)}")
        print("Installing missing packages...")
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing)
    
    print("✅ All dependencies ready")
    return True

def build_app():
    """Build the Mac app"""
    print(f"\n🏗️  Building {APP_NAME}...")
    
    # Clean previous builds
    for path in ["build", "dist", "launcher.py", "llms_builder.spec"]:
        if Path(path).exists():
            if Path(path).is_dir():
                shutil.rmtree(path)
            else:
                Path(path).unlink()
    
    # Create launcher script
    print("📝 Creating launcher script...")
    launcher_script = create_launcher_script()
    
    # Create spec file
    print("📋 Creating build specification...")
    spec_file = create_spec_file()
    
    # Run PyInstaller
    print("📦 Building app bundle...")
    result = subprocess.run([
        sys.executable, "-m", "PyInstaller",
        "--clean",
        "--noconfirm",
        spec_file
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print("❌ Build failed!")
        print(result.stdout)
        print(result.stderr)
        return False
    
    print("✅ Build complete!")
    
    # Create DMG for easier distribution (optional)
    app_path = f"dist/{APP_NAME}.app"
    if Path(app_path).exists():
        print(f"\n📱 App created: {app_path}")
        print("\n📦 Creating DMG for distribution...")
        create_dmg(app_path)
    
    return True

def create_dmg(app_path):
    """Create a DMG file for easier distribution"""
    dmg_name = f"{APP_NAME.replace(' ', '_')}_v{VERSION}.dmg"
    
    # Simple DMG creation
    cmd = [
        "hdiutil", "create",
        "-volname", APP_NAME,
        "-srcfolder", "dist",
        "-ov",
        "-format", "UDZO",
        dmg_name
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print(f"✅ DMG created: {dmg_name}")
        
        # Clean up build artifacts
        print("\n🧹 Cleaning up...")
        for path in ["build", "launcher.py", "llms_builder.spec"]:
            if Path(path).exists():
                if Path(path).is_dir():
                    shutil.rmtree(path)
                else:
                    Path(path).unlink()
        
        print(f"\n✅ Done! Your app is ready:")
        print(f"   • App bundle: dist/{APP_NAME}.app")
        print(f"   • DMG installer: {dmg_name}")
        print(f"\n📧 Distribution instructions:")
        print(f"   1. Email the {dmg_name} file to your coworkers")
        print(f"   2. They double-click the DMG")
        print(f"   3. Drag {APP_NAME} to Applications")
        print(f"   4. First launch: Right-click → Open")
        print(f"   5. Enter their OpenAI API key when prompted")
        
    except subprocess.CalledProcessError:
        print("⚠️  DMG creation failed (this is optional)")
        print(f"   You can still distribute the app at: dist/{APP_NAME}.app")

def main():
    """Main build process"""
    print(f"🚀 {APP_NAME} Mac App Builder")
    print("=" * 50)
    
    # Check we're on macOS
    if sys.platform != "darwin":
        print("❌ This script must be run on macOS")
        sys.exit(1)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Build the app
    if build_app():
        print("\n🎉 Success!")
    else:
        print("\n❌ Build failed")
        sys.exit(1)

if __name__ == "__main__":
    main()