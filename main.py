import argparse 
import sys 
import os 
import platform 
from pathlib import Path 
import time 
# Get project root directory and add to Python path 
PROJECT_ROOT = Path(__file__).parent.absolute() 
sys.path.append(str(PROJECT_ROOT)) 
from bot.elation_bot import ElationBot 
from config.settings import Settings 
def resolve_file_path(file_path): 
"""Resolve file path, checking multiple possible locations""" 
# Try the path as provided 
path = Path(file_path) 
if path.exists(): 
return path.absolute() 
# Try relative to current directory 
current_dir_path = Path.cwd() / file_path 
if current_dir_path.exists(): 
return current_dir_path.absolute() 
# Try relative to user's Documents 
documents_path = Path.home() / 'Documents' / file_path 
if documents_path.exists(): 
return documents_path.absolute() 
# Try relative to OneDrive Documents if it exists 

onedrive_documents = Path.home() / 'OneDrive' / 'Documents' / file_path 
if onedrive_documents.exists(): 
return onedrive_documents.absolute() 
# Also try relative to user's Desktop (fallback) 
desktop_path = Path.home() / 'Desktop' / file_path 
if desktop_path.exists(): 
return desktop_path.absolute() 
# Try relative to OneDrive Desktop if it exists (fallback) 
onedrive_desktop = Path.home() / 'OneDrive' / 'Desktop' / file_path 
if onedrive_desktop.exists(): 
return onedrive_desktop.absolute() 
raise FileNotFoundError(f"Could not find file: {file_path}") 
def setup_permissions(): 
"""Setup necessary permissions based on platform""" 
platform_name = platform.system().lower() 
if platform_name == 'darwin': # macOS 
# Ensure downloads directory has proper permissions 
downloads_dir = Path.home() / 'Downloads' 
if not downloads_dir.exists(): 
downloads_dir.mkdir(parents=True) 
os.chmod(str(downloads_dir), 0o755) 
# Ensure project directories have proper permissions 
project_dirs = ['downloads', 'files', 'logs', 'screenshots'] 
for dir_name in project_dirs: 
dir_path = PROJECT_ROOT / dir_name 
if not dir_path.exists(): 
dir_path.mkdir(parents=True) 
os.chmod(str(dir_path), 0o755) 
elif platform_name == 'windows': # Windows 
# Create project directories without special permissions 
project_dirs = ['downloads', 'files', 'logs', 'screenshots'] 
for dir_name in project_dirs: 
dir_path = PROJECT_ROOT / dir_name 
if not dir_path.exists(): 
dir_path.mkdir(parents=True) 
def setup_environment(): 

"""Setup the environment and create necessary directories""" 
from config.settings import Settings 
# Setup platform-specific permissions 
setup_permissions() 
# Create necessary directories using Settings 
Settings.ensure_directories() 
# Also create package directories 
package_directories = [ 
PROJECT_ROOT / "config", 
PROJECT_ROOT / "utils", 
PROJECT_ROOT / "bot" 
] 
for directory in package_directories: 
directory.mkdir(exist_ok=True) 
# Check if .env file exists 
env_file = PROJECT_ROOT / ".env" 
if not env_file.exists(): 
print("⚠️Warning: .env file not found!") 
print("Please copy .env.example to .env and configure your credentials:") 
print(" cp .env.example .env") 
print(" # Then edit .env with your Elation EMR credentials") 
return False 
return True 
def parse_patient_string(patient_string): 
"""Parse patient string like 'Mark Long 11/13/1965' into name and DOB""" 
# Split the string and look for date pattern 
parts = patient_string.strip().split() 
# Look for date-like pattern (contains slashes) 
dob = None 
name_parts = [] 
for part in parts: 
if '/' in part and len(part.split('/')) == 3: 
dob = part 
else: 
name_parts.append(part) 

name = ' '.join(name_parts) 
if not name: 
raise ValueError("Could not extract patient name from the provided string") 
return name, dob 
def main(): 
"""Main function to run the Elation EMR bot""" 
parser = argparse.ArgumentParser( 
description="Elation EMR RPA Bot - Automate login, patient search, and file uploads" 
) 
# Optional arguments - patient data will be read from Excel if not provided 
parser.add_argument( 
"--patient", "-p", 
required=False, 
help="Patient name and DOB (e.g., 'Mark Long 11/13/1965'). If not provided, data will be read from Excel file." 
) 
group = parser.add_mutually_exclusive_group(required=True) 
group.add_argument( 
"--file", "-f", 
action='append', 
help="Path to the file to upload (e.g., '/path/to/document.pdf'). Use multiple times for batch processing: --file file1.pdf --file file2.pdf" 
) 
group.add_argument( 
"--folder", 
help="Path to a folder containing PDF files to upload (e.g., '/Users/adityadonapati/Downloads/elation-emr-main/files/SignedOrders'). Up to --max-patients files will be processed." 
) 
# Optional arguments 
parser.add_argument( 
"--username", "-u", 
help="Elation EMR username (overrides .env file)" 
) 
parser.add_argument( 
"--password", "-pw", 

help="Elation EMR password (overrides .env file)" 
) 
parser.add_argument( 
"--url", 
help="Elation EMR URL (overrides .env file)" 
) 
parser.add_argument( 
"--headless", 
action="store_true", 
help="Run browser in headless mode (no GUI)" 
) 
parser.add_argument( 
"--debug", 
action="store_true", 
help="Enable debug mode with verbose logging" 
) 
parser.add_argument( 
"--max-patients", 
type=int, 
default=2, 
help="Maximum number of patients to process in batch mode (default: 2)" 
) 
args = parser.parse_args() 
try: 
# Gather file paths from --file or --folder 
file_paths = [] 
if args.file: 
for file_arg in args.file: 
file_path = resolve_file_path(file_arg) 
print(f"Found file at: {file_path}") 
try: 
with open(file_path, 'rb') as f: 
pass 
file_paths.append(str(file_path)) 
except PermissionError: 
print(f"Error: Cannot read file: {file_path}") 
print("Please check file permissions") 
sys.exit(1) 

except Exception as e: 
print(f"Error accessing file: {str(e)}") 
sys.exit(1) 
elif args.folder: 
folder_path = Path(args.folder) 
if not folder_path.exists() or not folder_path.is_dir(): 
print(f"Error: Folder does not exist: {folder_path}") 
sys.exit(1) 
# Only include .pdf files 
pdf_files = sorted([f for f in folder_path.iterdir() if f.is_file() and f.suffix.lower() == '.pdf']) 
if not pdf_files: 
print(f"Error: No PDF files found in folder: {folder_path}") 
sys.exit(1) 
# Limit to max_patients 
file_paths = [str(f) for f in pdf_files[:args.max_patients]] 
print(f"Found {len(file_paths)} PDF files in folder: {folder_path}") 
for i, fp in enumerate(file_paths, 1): 
print(f" {i}. {Path(fp).name}") 
else: 
print("Error: Either --file or --folder must be specified.") 
sys.exit(1) 
# Create bot instance 
bot = ElationBot(headless=args.headless) 
try: 
# Determine if this is single file or batch processing 
is_batch = len(file_paths) > 1 
if args.patient and is_batch: 
print("❌ Error: Cannot specify --patient for batch processing.") 
print("📝 For batch processing, patient data will be read from Excel file.") 
sys.exit(1) 
if not is_batch: 
# Single file processing 
# Parse patient information if provided, otherwise will be read from Excel 
patient_name = None 
patient_dob = None 
if args.patient: 
try: 
patient_name, patient_dob = parse_patient_string(args.patient) 
print("🤖 Starting Elation EMR RPA Bot (Single File)...") 

print(f"👤 Patient: {patient_name}") 
if patient_dob: 
print(f"📅 DOB: {patient_dob}") 
else: 
print("📅 DOB: Not provided") 
except ValueError as e: 
print(f"❌ Error parsing patient information: {str(e)}") 
print("📝 Expected format: 'First Last MM/DD/YYYY' (e.g., 'Mark Long 11/13/1965')") 
sys.exit(1) 
else: 
print("🤖 Starting Elation EMR RPA Bot (Single File)...") 
print("👤 Patient: Will be read from Excel file") 
print("📅 DOB: Will be read from Excel file") 
print(f"📁 File: {file_paths[0]}") 
print(f"🖥️Headless mode: {args.headless}") 
print("-" * 50) 
# Run the single workflow 
success = bot.run_workflow( 
file_path=file_paths[0], 
patient_name=patient_name, 
patient_dob=patient_dob, 
username=args.username, 
password=args.password, 
url=args.url, 
keep_open=True, # Keep browser open for manual review 
skip_login=True # Skip login for single mode if already logged in 
) 
else: 
# Batch processing 
print("🤖 Starting Elation EMR RPA Bot (Batch Processing)...") 
print("👤 Patients: Will be read from Excel file") 
print("📅 DOBs: Will be read from Excel file") 
print(f"👥 Max patients: {args.max_patients}") 
print("🖥️Headless mode:", args.headless) 
print("-" * 50) 
# Pre-check: read patients from Excel and check for file existence 
patients = bot.read_all_patients_from_excel(max_patients=args.max_patients) 
missing_files = [] 
for i, patient in enumerate(patients, 1): 
pdf_path = patient.get('pdf_path') 
exists = Path(pdf_path).exists() 

status = "(will process)" if exists else "(MISSING FILE - will skip)" 
print(f" {i}. {Path(pdf_path).name} {status}") 
if not exists: 
missing_files.append(pdf_path) 
if len(missing_files) == len(patients): 
print("❌ No matching PDF files found for any of the first N patients in Excel. Exiting.") 
bot.close() 
sys.exit(1) 
elif missing_files: 
print(f"⚠️Warning: {len(missing_files)} patient(s) do not have a matching PDF and will be skipped.") 
print("-" * 50) 
# Initialize bot and login once 
if not bot.initialize(): 
bot.close() 
print("❌ Bot initialization failed.") 
sys.exit(1) 
if not bot.login(username=args.username, password=args.password, url=args.url): 
bot.close() 
print("❌ Login failed.") 
sys.exit(1) 
# Process uploads with single bot instance 
successful_uploads = 0 
failed_uploads = 0 
for i, patient in enumerate(patients, 1): 
pdf_path = patient.get('pdf_path') 
if not Path(pdf_path).exists(): 
print(f"Skipping patient {i}: {patient['name']} (missing file: {pdf_path})") 
continue 
print(f"\n{'='*60}") 
print(f"📋 PROCESSING PATIENT {i}/{len(patients)}") 
print(f"👤 Patient: {patient['name']}") 
print(f"📅 DOB: {patient['dob'] or 'Not provided'}") 
print(f"📁 File: {Path(pdf_path).name}") 
print(f"{'='*60}") 
try: 
success = bot.run_workflow( 
file_path=pdf_path, 
patient_name=patient['name'], 
patient_dob=patient['dob'], 
username=args.username, 
password=args.password, 
url=args.url, 

keep_open=True, # Keep browser open during batch 
skip_login=True # Skip login since already logged in 
) 
if success: 
print(f"✅ Successfully uploaded file for {patient['name']}") 
successful_uploads += 1 
else: 
print(f"❌ Failed to upload file for {patient['name']}") 
failed_uploads += 1 
except Exception as e: 
print(f"❌ Error processing patient {patient['name']}: {str(e)}") 
failed_uploads += 1 
# Close bot after batch processing 
bot.close() 
print("\nBATCH SUMMARY") 
print(f"✅ Successful uploads: {successful_uploads}") 
print(f"❌ Failed uploads: {failed_uploads}") 
print(f"📊 Total processed: {successful_uploads + failed_uploads}") 
print("-" * 50) 
if successful_uploads > 0: 
print("✅ Batch workflow completed!") 
else: 
print("❌ Batch workflow failed or had no successful uploads!") 
print("Check the logs and uploads_log.csv for details.") 
print("Batch mode complete. Exiting.") 
sys.exit(0) 
if success: 
if is_batch: 
print("✅ Batch workflow completed!") 
print("Check the logs above for detailed results of each patient.") 
else: 
print("✅ Workflow completed successfully!") 
print("The file has been uploaded to the patient's chart.") 
print("🔄 Browser will remain open. Press Ctrl+C to close when finished.") 
# Wait for user interrupt when keeping browser open 
try: 
while True: 
time.sleep(1) 
except KeyboardInterrupt: 
print("\n⚠️Bot interrupted by user") 
bot.close() 
else: 

if is_batch: 
print("❌ Batch workflow failed or had no successful uploads!") 
else: 
print("❌ Workflow failed!") 
print("Check the logs and screenshots for more details.") 
print("🔄 Browser will remain open for manual inspection. Press Ctrl+C to close when finished.") 
# Keep browser open even on failure for manual inspection 
try: 
while True: 
time.sleep(1) 
except KeyboardInterrupt: 
print("\n⚠️Bot interrupted by user") 
bot.close() 
except KeyboardInterrupt: 
print("\n⚠️Bot interrupted by user") 
bot.close() # Only close on user interrupt 
except Exception as e: 
print(f"❌ An error occurred: {str(e)}") 
bot.close() # Close on error 
sys.exit(1) 
except FileNotFoundError as e: 
print(f"Error: {str(e)}") 
print("Please provide a valid file path") 
sys.exit(1) 
def run_example(): 
"""Run an example workflow (for testing purposes)""" 
print("🧪 Running example workflow...") 
# Create a sample file for testing 
sample_file = PROJECT_ROOT / "sample_document.txt" 
sample_file.write_text("This is a sample document for testing the Elation EMR bot.") 
bot = ElationBot(headless=False) 
try: 
# Example workflow using Excel data 
success = bot.run_workflow( 
file_path=str(sample_file) 
) 

if success: 
print("✅ Example workflow completed successfully!") 
else: 
print("❌ Example workflow failed!") 
except Exception as e: 
print(f"❌ Example workflow error: {str(e)}") 
finally: 
# Clean up 
if sample_file.exists(): 
sample_file.unlink() 
print("🧹 Cleanup completed") 
if __name__ == "__main__": 
# Setup environment first 
if not setup_environment(): 
print("\n🚀 To get started:") 
print("1. Copy .env.example to .env: cp .env.example .env") 
print("2. Edit .env with your Elation EMR credentials") 
print("3. Install dependencies: pip install -r requirements.txt") 
print("4. Run the bot:") 
print(" Single file: python main.py --file '9318873.pdf' (patient data from Excel)") 
print(" With patient: python main.py --patient 'Mark Long 11/13/1965' --file '9318873.pdf'") 
print(" Batch mode: python main.py --file file1.pdf --file file2.pdf (max 2 patients)") 
print(" Custom limit: python main.py --file f1.pdf --file f2.pdf --file f3.pdf --max-patients 3") 
sys.exit(1) 
# Check if running in example mode 
if len(sys.argv) == 2 and sys.argv[1] == "--example": 
run_example() 
else: 
main()
