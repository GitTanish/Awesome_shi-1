class Drone:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def move_up(self):
        self.y += 1

    def move_down(self):
        self.y -= 1

    def move_left(self):
        self.x -= 1

    def move_right(self):
        self.x += 1

    def get_position(self):
        return self.x, self.y

# Create a new drone
my_drone = Drone(0, 0)
print(my_drone.get_position())
my_drone.move_up()
print(my_drone.get_position())