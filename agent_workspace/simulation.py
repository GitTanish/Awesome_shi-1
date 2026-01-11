import numpy as np

class Simulation:
    def __init__(self, size):
        self.size = size
        self.state = np.zeros((size, size))

    def run(self):
        for i in range(self.size):
            for j in range(self.size):
                self.state[i, j] = np.random.rand()
        return self.state

sim = Simulation(10)
result = sim.run()
print(result)