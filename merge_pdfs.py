import os
import re
import sys
from pypdf import PdfWriter

def get_sort_key(filename):
    """
    Extracts numerical value for sorting. 
    If filename is '12.pdf', returns (0, 12).
    If filename has numbers inside but not purely a number, returns (1, first_number, filename).
    If filename has no numbers, returns (2, filename).
    """
    name_without_ext = os.path.splitext(filename)[0]
    
    # Try pure integer
    try:
        return (0, int(name_without_ext))
    except ValueError:
        pass
        
    # Try finding any numbers in the filename
    match = re.search(r'\d+', name_without_ext)
    if match:
        return (1, int(match.group()), name_without_ext)
        
    # Fallback to string sort
    return (2, name_without_ext)

def merge_pdfs(input_dir, output_path):
    print(f"Scanning directory: {input_dir}")
    if not os.path.exists(input_dir):
        print(f"Error: Directory {input_dir} does not exist.")
        sys.exit(1)
        
    # Get all PDF files
    pdf_files = [f for f in os.listdir(input_dir) if f.lower().endswith('.pdf')]
    
    if not pdf_files:
        print("No PDF files found in the directory.")
        sys.exit(0)
        
    print(f"Found {len(pdf_files)} PDF files.")
    
    # Sort files
    pdf_files.sort(key=get_sort_key)
    
    print("\nOrder of merge:")
    for i, file in enumerate(pdf_files[:5]):
        print(f"  {i+1}. {file}")
    if len(pdf_files) > 10:
        print("  ...")
        for i, file in enumerate(pdf_files[-5:]):
            print(f"  {len(pdf_files) - 4 + i}. {file}")
    else:
        for i, file in enumerate(pdf_files[5:]):
            print(f"  {i+6}. {file}")
            
    print(f"\nStarting merge into: {output_path}")
    
    merger = PdfWriter()
    try:
        for i, file_name in enumerate(pdf_files):
            file_path = os.path.join(input_dir, file_name)
            # We can log progress every 50 files
            if (i + 1) % 50 == 0 or i == 0 or i == len(pdf_files) - 1:
                print(f"Appending [{i+1}/{len(pdf_files)}]: {file_name}")
            merger.append(file_path)
            
        print("Writing merged file to disk (this might take a moment)...")
        merger.write(output_path)
        print("Merge completed successfully!")
    except Exception as e:
        print(f"\nAn error occurred during merge: {e}")
        raise
    finally:
        merger.close()

if __name__ == "__main__":
    print("=== PDF Merger Universal ===")
    
    # Prompt for input folder path
    input_directory = input("Masukkan path folder yang berisi file PDF: ").strip()
    
    # Remove quotes (if user dragged & dropped the folder into the terminal)
    input_directory = input_directory.strip("'\"")
    
    if not input_directory:
        print("Error: Path folder tidak boleh kosong.")
        sys.exit(1)
        
    input_directory = os.path.abspath(input_directory)
    
    if not os.path.isdir(input_directory):
        print(f"Error: Folder '{input_directory}' tidak ditemukan.")
        sys.exit(1)
        
    # Generate default output name
    # Clean trailing slashes to correctly extract folder name
    clean_input_dir = input_directory.rstrip("\\/")
    parent_dir = os.path.dirname(clean_input_dir)
    folder_name = os.path.basename(clean_input_dir)
    default_output_pdf = os.path.join(parent_dir, f"{folder_name}_merged.pdf")
    
    print(f"\nDefault output: {default_output_pdf}")
    custom_output = input("Masukkan path/nama file output (Tekan ENTER untuk menggunakan default): ").strip().strip("'\"")
    
    if custom_output:
        output_pdf = os.path.abspath(custom_output)
    else:
        output_pdf = default_output_pdf
        
    merge_pdfs(input_directory, output_pdf)
