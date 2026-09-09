import ctypes
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

root = Path(sys.prefix)
pyd = next(Path('loader').glob('*.pyd')).resolve()
code = 'import importlib.util; p=' + repr(str(pyd)) + '; s=importlib.util.spec_from_file_location("_cairo",p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); print(m.cairo_version_string())'
for label, setup in [('default', ''), ('explicit-dll-directory', 'import os; d=os.add_dll_directory(' + repr(str(root/'Library'/'bin')) + '); ')]:
    result = subprocess.run([sys.executable, '-c', setup+code], capture_output=True, text=True)
    print(label, result.returncode, result.stdout, result.stderr, flush=True)

handle = os.add_dll_directory(str(root/'Library'/'bin'))
kernel = ctypes.WinDLL('kernel32', use_last_error=True)
kernel.GetProcAddress.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
kernel.GetProcAddress.restype = ctypes.c_void_p
kernel.GetModuleFileNameW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_uint]
kernel.GetModuleFileNameW.restype = ctypes.c_uint
for dll, symbols in json.loads(Path('probe-imports.json').read_text()).items():
    try:
        library = ctypes.WinDLL(dll)
        path = ctypes.create_unicode_buffer(32768)
        kernel.GetModuleFileNameW(library._handle, path, len(path))
        missing = [symbol for symbol in symbols if not kernel.GetProcAddress(library._handle, symbol.encode())]
        print('DLL', dll, 'PATH', path.value, 'MISSING', missing, flush=True)
    except OSError as exc:
        print('DLL FAILED', dll, repr(exc), flush=True)
print('DEPENDENCY RECORDS', flush=True)
for path in (root/'conda-meta').glob('*.json'):
    record=json.loads(path.read_text())
    print(record['name'], record['version'], record['build'], flush=True)
