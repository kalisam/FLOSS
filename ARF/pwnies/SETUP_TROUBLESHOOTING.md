# 🔧 Desktop Pony Swarm - Setup & Troubleshooting Guide

**Quick Reference**: Multiple ways to run the swarm, from simplest to most robust.

---

## ⚡ FASTEST FIX (Windows)

### Option 1: Use the Batch File
```cmd
cd C:\crap\ARF
run_swarm.bat
```

The `.bat` file automatically sets PYTHONPATH. **Try this first!**

---

## 🐍 Installation Methods (Choose One)

### Method A: Development Mode (RECOMMENDED)
```bash
cd C:\crap\ARF
pip install -e .
```

**What this does**: Installs package in "editable" mode so changes take effect immediately.

**After this**:
```bash
python run_swarm.py              # Interactive mode
python run_swarm.py demo          # Demo mode  
pony-swarm                        # Can also use command
```

### Method B: Set PYTHONPATH (Quick)
```cmd
# Windows Command Prompt
cd C:\crap\ARF
set PYTHONPATH=%CD%
python run_swarm.py

# Windows PowerShell
cd C:\crap\ARF
$env:PYTHONPATH = (Get-Location).Path
python run_swarm.py

# Linux/Mac
cd /mnt/project
export PYTHONPATH=$(pwd)
python run_swarm.py
```

### Method C: Direct Python Path Manipulation (Already Done)
The `run_swarm.py` file now has improved path handling built-in. Just run:
```bash
cd C:\crap\ARF
python run_swarm.py
```

---

## 🧪 Running Tests

### If Installed (Method A)
```bash
python -m pytest desktop_pony_swarm/tests/test_swarm.py -v
```

### Without Installation
```bash
cd C:\crap\ARF
python desktop_pony_swarm\tests\test_swarm.py
```

---

## 🐛 Troubleshooting Common Issues

### Issue 1: `ModuleNotFoundError: No module named 'desktop_pony_swarm'`

**Cause**: Python can't find the package.

**Solutions** (try in order):
1. ✅ Use `run_swarm.bat` (Windows)
2. ✅ Install with `pip install -e .`
3. ✅ Set PYTHONPATH: `set PYTHONPATH=%CD%` (Windows) or `export PYTHONPATH=$(pwd)` (Linux)
4. ✅ Run from correct directory: `cd C:\crap\ARF`

### Issue 2: `ModuleNotFoundError: No module named 'aiohttp'`

**Cause**: Dependencies not installed.

**Solution**:
```bash
pip install -r requirements_swarm.txt
```

### Issue 3: `ModuleNotFoundError: No module named 'embedding_frames_of_scale'`

**Cause**: The existing embedding file isn't in Python path.

**Solution**:
```bash
# Check if file exists
ls embedding_frames_of_scale.py

# If it's in a different location, copy it:
# Windows:
copy path\to\embedding_frames_of_scale.py C:\crap\ARF\
# Linux:
cp path/to/embedding_frames_of_scale.py /mnt/project/
```

### Issue 4: Import errors with relative imports

**Cause**: Running from wrong directory.

**Solution**: Always run from project root:
```bash
cd C:\crap\ARF
python run_swarm.py
# NOT: cd desktop_pony_swarm && python ../run_swarm.py
```

### Issue 5: `SyntaxError` or `IndentationError`

**Cause**: Python version < 3.9 or file encoding issue.

**Solution**:
```bash
# Check Python version
python --version  # Should be >= 3.9

# If too old, use newer Python
python3.11 run_swarm.py
```

---

## 📦 Verifying Installation

### Quick Check
```python
python -c "from desktop_pony_swarm import PonySwarm; print('✅ Import works!')"
```

### Full Check
```python
import sys
print("Python path:")
for p in sys.path:
    print(f"  {p}")

try:
    from desktop_pony_swarm import PonySwarm
    print("\n✅ desktop_pony_swarm imports successfully")
except ImportError as e:
    print(f"\n❌ Import failed: {e}")

try:
    from embedding_frames_of_scale import MultiScaleEmbedding
    print("✅ embedding_frames_of_scale imports successfully")
except ImportError as e:
    print(f"❌ Import failed: {e}")
```

Save as `check_setup.py` and run: `python check_setup.py`

---

## 🎯 Recommended Setup Flow

### First Time Setup
```bash
# 1. Navigate to project
cd C:\crap\ARF

# 2. Create virtual environment (optional but recommended)
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 3. Install dependencies
pip install -r requirements_swarm.txt

# 4. Install package in development mode
pip install -e .

# 5. Verify installation
python -c "from desktop_pony_swarm import PonySwarm; print('Ready!')"

# 6. Run tests
python desktop_pony_swarm\tests\test_swarm.py

# 7. Try interactive mode
python run_swarm.py
```

---

## 🚀 Quick Start (After Setup)

### Interactive Mode
```bash
python run_swarm.py
# or
pony-swarm  # if installed with pip install -e .
```

### Demo Mode
```bash
python run_swarm.py demo
# or
pony-swarm demo
```

### Programmatic Use
```python
import asyncio
from desktop_pony_swarm import PonySwarm

async def main():
    async with PonySwarm(num_ponies=4) as swarm:
        result = await swarm.recursive_self_aggregation(
            query="What is FLOSSI0ULLK?",
            K=2,
            T=3
        )
        print(result['response'])

asyncio.run(main())
```

---

## 📁 File Structure Verification

Your project should look like this:
```
C:\crap\ARF\  (or /mnt/project/)
├── desktop_pony_swarm\
│   ├── __init__.py
│   ├── core\
│   │   ├── __init__.py
│   │   ├── horde_client.py
│   │   ├── pony_agent.py
│   │   ├── swarm.py
│   │   └── embedding.py
│   ├── bridge\
│   ├── config\
│   └── tests\
├── run_swarm.py
├── run_swarm.bat  (Windows launcher)
├── setup.py
├── requirements_swarm.txt
└── embedding_frames_of_scale.py
```

Check with:
```bash
# Windows
dir /s *.py

# Linux/Mac  
find . -name "*.py" -type f
```

---

## 🔍 Advanced Debugging

### Check Python Import System
```python
import sys
import os

print("Current directory:", os.getcwd())
print("\nPython path:")
for i, path in enumerate(sys.path):
    print(f"  {i}: {path}")

print("\nTrying to locate desktop_pony_swarm...")
for path in sys.path:
    potential = os.path.join(path, "desktop_pony_swarm")
    if os.path.exists(potential):
        print(f"  ✅ Found at: {potential}")
```

### Enable Debug Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Then run your code
from desktop_pony_swarm import PonySwarm
```

---

## 💡 Still Having Issues?

### Create Minimal Test Case
```python
# save as test_minimal.py
import sys
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print(f"Project root: {project_root}")
print(f"Added to path: {sys.path[0]}")

try:
    from desktop_pony_swarm import PonySwarm
    print("✅ SUCCESS: Module imported!")
except Exception as e:
    print(f"❌ FAILED: {e}")
    print("\nDebugging info:")
    print(f"  Current dir: {Path.cwd()}")
    print(f"  Script dir: {Path(__file__).parent}")
    print(f"  Python paths: {sys.path}")
```

Run: `python test_minimal.py`

---

## 📞 Getting Help

If none of these work:

1. **Check Python version**: `python --version` (must be >= 3.9)
2. **Check current directory**: `cd` (should be project root)
3. **Check file exists**: `ls desktop_pony_swarm/core/swarm.py`
4. **Check permissions**: Make sure you can read the files
5. **Try virtual environment**: Isolate from system Python

---

## ✅ Success Indicators

You know it's working when:
```bash
$ python run_swarm.py

🐴 DESKTOP PONY SWARM - Interactive Mode
================================================================================
Ponies: Pinkie Pie, Rainbow Dash, Twilight Sparkle, Fluttershy
RSA Parameters: N=4, K=2, T=3

Type your questions. Type 'quit' to exit.

You: 
```

---

**Most Common Fix**: Just use `run_swarm.bat` on Windows or install with `pip install -e .` 🎯
