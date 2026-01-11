import random

class Simulation:
    def __init__(self, num_agents, num_steps):
        self.num_agents = num_agents
        self.num_steps = num_steps
        self.agents = [[random.random() for _ in range(2)] for _ in range(num_agents)]

    def run(self):
        for step in range(self.num_steps):
            for i in range(self.num_agents):
                self.agents[i][0] += random.random()
                self.agents[i][1] += random.random()
            print(f'Step {step+1}: {self.agents}')

sim = Simulation(10, 5)
print('Starting simulation...')
sim.run()
