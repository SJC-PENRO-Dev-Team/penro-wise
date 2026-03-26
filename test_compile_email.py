import py_compile
import sys

try:
    py_compile.compile('document_tracking/email_service.py', doraise=True)
    print("File compiles successfully")
except py_compile.PyCompileError as e:
    print(f"Compilation error: {e}")
    sys.exit(1)
