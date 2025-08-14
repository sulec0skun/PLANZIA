import streamlit as st
import hashlib
import os
import binascii

from app.utils.database import create_user, authenticate_user

def hash_password(password):
    """Parolayı güvenli bir şekilde hashler."""
    salt = hashlib.sha256(os.urandom(60)).hexdigest().encode('ascii')
    pwdhash = hashlib.pbkdf2_hmac('sha512', password.encode('utf-8'),
                                salt, 100000)
    pwdhash = binascii.hexlify(pwdhash)
    return (salt + pwdhash).decode('ascii')

def verify_password(stored_password, provided_password):
    """Saklanan hashlenmiş parolayı verilen parolayla doğrular."""
    salt = stored_password[:64]
    stored_password = stored_password[64:]
    pwdhash = hashlib.pbkdf2_hmac('sha512',
                                  provided_password.encode('utf-8'),
                                  salt.encode('ascii'),
                                  100000)
    pwdhash = binascii.hexlify(pwdhash).decode('ascii')
    return pwdhash == stored_password

def render_login_form():
    """Streamlit tabanlı giriş formunu render eder."""
    st.subheader("Login")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit_button = st.form_submit_button("Login")

        if submit_button:
            # handle_login fonksiyonu daha sonra main.py'den çağrılacak
            return {"username": username, "password": password, "action": "login"}
    return None

def render_register_form():
    """Streamlit tabanlı kayıt formunu render eder."""
    st.subheader("Register")
    with st.form("register_form"):
        new_username = st.text_input("New Username")
        new_password = st.text_input("New Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        submit_button = st.form_submit_button("Register")

        if submit_button:
            # handle_register fonksiyonu daha sonra main.py'den çağrılacak
            if new_password == confirm_password:
                return {"username": new_username, "password": new_password, "action": "register"}
            else:
                st.error("Passwords do not match!")
    return None

def logout():
    """Kullanıcının oturumunu kapatır."""
    st.session_state["logged_in"] = False
    st.session_state["username"] = None
    st.session_state["current_page"] = "login"
    st.success("Successfully logged out!")
    st.rerun()



