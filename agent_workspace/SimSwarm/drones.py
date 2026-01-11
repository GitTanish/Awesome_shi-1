class Drone:
    def __init__(self, id, position):
        self.id = id
        self.position = position

    def move(self, new_position):
        self.position = new_position

    def get_position(self):
        return self.position

drone1 = Drone(1, (0, 0))
print(drone1.get_position())