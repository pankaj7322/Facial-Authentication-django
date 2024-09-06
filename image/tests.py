from django.test import TestCase

# Create your tests here.
from cryptography.fernet import Fernet

# Generate a key
key = Fernet.generate_key()

# Save the key securely
print(key.decode())  # Print the key, copy it for use
