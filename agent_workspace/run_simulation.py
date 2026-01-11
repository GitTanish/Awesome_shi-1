import os

cwd = os.getcwd()
print(cwd)

try:
    exec(open("SimSwarm/simulation.py").read())
except Exception as e:
    print("An error occurred: ", str(e))