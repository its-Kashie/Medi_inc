# generate_key.py
from cryptography.fernet import Fernet

key = Fernet.generate_key()
print("Yeh hai teri secret key:")
print(key.decode())

# File mein save kar de
with open("cnic_encryption.key", "wb") as f:
    f.write(key)

print("\nKey successfully saved → cnic_encryption.key")
print("Ab server chala sakti hai!")