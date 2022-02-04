""" Stores settings using dotenv. This file can be included in version
control and contains references to environment variables but checks
if the variable is present in a .env file (which is not included in
version control) and uses those values first

Every variable should be included here even it is not present in Environment
variables.
"""

import os

from dotenv import load_dotenv

load_dotenv()

# Allows the settings of default path for the attendance report. Not currently implemented
attendance_report_path = os.getenv("ATTENDANCE_REPORT_PATH")
