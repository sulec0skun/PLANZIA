import random
import string

def generate_event_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

# Diğer yardımcı fonksiyonlar buraya eklenecek

def validate_event_code(code):
    if len(code) != 8 or not code.isalnum():
        return False
    return True

def format_preferences(prefs):
    # Bu fonksiyon daha sonra Streamlit UI için tercihleri biçimlendirecek
    formatted_list = []
    for key, value in prefs.items():
        formatted_list.append(f"{key.replace('_', ' ').title()}: {value}")
    return ", ".join(formatted_list)

def display_success_message(message):
    # Streamlit success mesajı göstermek için placeholder
    pass # Streamlit entegrasyonu main.py'de yapılacak

