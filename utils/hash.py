import hashlib
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

SECRET_KEY = os.getenv("SECRET_HASH_KEY")

def hash_id(instance_id):
    """Convert an integer ID into a hashed string.""" 
    hash_object = hashlib.sha256(f"{SECRET_KEY}{instance_id}".encode())
    return hash_object.hexdigest()[:10]  

def decode_hashed_id(hashed_id, model_class):
    
    for instance in model_class.objects.all():
        if hash_id(instance.id) == hashed_id:
            return instance.id  # Return the ID, not the object
    return None
