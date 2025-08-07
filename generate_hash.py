from werkzeug.security import generate_password_hash

# Replace with your desired plain password
plain_password = "password123"

# Generate the hashed password
hashed_password = generate_password_hash(plain_password)

print("Hashed password:", hashed_password)
