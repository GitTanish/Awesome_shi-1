# Define a function to calculate the area of a rectangle
def calculate_area(length, width):
    return length * width

# Define a function to calculate the perimeter of a rectangle
def calculate_perimeter(length, width):
    return 2 * (length + width)

# Test the functions
length = 5
width = 3
area = calculate_area(length, width)
perimeter = calculate_perimeter(length, width)

print(f"Area: {area}, Perimeter: {perimeter}")