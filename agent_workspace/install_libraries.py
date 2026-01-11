import subprocess
import sys

# List of required libraries
libraries = ['requests', 'numpy', 'pandas']

# Install libraries using pip
for library in libraries:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', library])