"""
Test if the DOCX file is valid
"""
import zipfile

file_path = r"C:\Users\Admin\WSTI-System\penro_project\media\work_items\03_Homework_15.docx"

print(f"Testing file: {file_path}")

# DOCX files are actually ZIP files
try:
    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        print("✓ File is a valid ZIP archive")
        print(f"  Files in archive: {len(zip_ref.namelist())}")
        
        # Check for required DOCX structure
        required_files = ['[Content_Types].xml', 'word/document.xml']
        for req_file in required_files:
            if req_file in zip_ref.namelist():
                print(f"  ✓ Found {req_file}")
            else:
                print(f"  ✗ Missing {req_file}")
                
except zipfile.BadZipFile:
    print("✗ File is not a valid ZIP archive (corrupted DOCX)")
except Exception as e:
    print(f"✗ Error: {e}")
