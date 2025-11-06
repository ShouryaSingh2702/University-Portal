# main.py
import os
from app.gui import App
from app.data_manager import DataManager

# Define the data directory
# This ensures JSON files are stored cleanly in the 'data' subfolder
DATA_DIR = 'data'
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

CRED_PATH = os.path.join(DATA_DIR, 'credentials.json')
STUDENT_DATA_PATH = os.path.join(DATA_DIR, 'student_data.json')
COURSE_PATH = os.path.join(DATA_DIR, 'courses.json')

if __name__ == "__main__":
    # 1. Initialize the data manager
    data_manager = DataManager(CRED_PATH, STUDENT_DATA_PATH, COURSE_PATH)
    
    # 2. Create and run the GUI App
    app = App(data_manager)
    app.mainloop()