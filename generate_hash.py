from werkzeug.security import generate_password_hash

plain_password = "vizzy"
hashed_password = generate_password_hash(plain_password, method='pbkdf2:sha256')

print("Hashed password:", hashed_password)
