# EMR-Automation-Framework
A Python-based RPA bot that automates file uploads and patient chart management in EMR systems.
This project is a Python-based **Robotic Process Automation (RPA) bot** designed to streamline repetitive tasks in **Electronic Medical Record (EMR) systems**.  

The bot provides a command-line interface to:  
- Login to an EMR system (credentials via `.env` or CLI)  
- Search for patients by name and date of birth  
- Upload PDF or image files directly into patient charts  
- Support **single-file uploads** as well as **batch uploads** using Excel data  
- Run in **headless mode** for background automation  

### Key Features
- Cross-platform (Windows & macOS)  
- Automatic file path resolution (Desktop, Documents, OneDrive, etc.)  
- Batch processing with Excel integration  
- Error handling and logging for failed uploads  
- Configurable through `.env` and command-line arguments  

### Tech Stack
- Python 3  
- argparse (CLI handling)  
- pathlib & os (file and environment management)  
- Custom RPA workflow logic (browser automation via Selenium/Playwright in `ElationBot`)  

⚡ **Note:**  
This project was developed as a **student internship project** to demonstrate automation in healthcare workflows.  
It is not an official tool from any EMR vendor and is intended for **educational and demonstration purposes only**.  
