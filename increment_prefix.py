import string
import os

# Function to load the current prefix from a file
def load_prefix(filename='current_prefix.txt'):
    if os.path.exists(filename):
        with open(filename, 'r') as file:
            return file.read().strip()
    return "AAA"  # Default prefix if the file doesn't exist

# Function to save the updated prefix to a file
def save_prefix(prefix, filename='current_prefix.txt'):
    with open(filename, 'w') as file:
        file.write(prefix)

# Function to increment the prefix
def increment_prefix(prefix):
    if prefix[-1] == 'Z':
        if prefix[-2] == 'Z':
            new_prefix = chr(ord(prefix[0]) + 1) + 'AA'
        else:
            new_prefix = prefix[0] + chr(ord(prefix[1]) + 1) + 'A'
    else:
        new_prefix = prefix[:-1] + chr(ord(prefix[-1]) + 1)
    return new_prefix

# Load the current prefix, increment it, and save it
current_prefix = load_prefix()
new_prefix = increment_prefix(current_prefix)
save_prefix(new_prefix)

print(f'Updated prefix: {new_prefix}')
