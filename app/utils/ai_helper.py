import google.generativeai as genai
import json
import streamlit as st # Hata mesajları için

def setup_gemini_client():
    """Gemini API client'ı ayarlar."""
    try:
        api_key = st.secrets["GOOGLE_API_KEY"]
    except KeyError:
        st.error("Google API Key is not set. Please set GOOGLE_API_KEY in Streamlit secrets.")
        return None
    
    genai.configure(api_key=api_key)
    model_name = st.secrets.get("GEMINI_MODEL", "gemini-pro")
    try:
        model = genai.GenerativeModel(model_name)
        return model
    except Exception as e:
        st.error(f"Failed to load Gemini model '{model_name}'. Error: {e}")
        return None

def create_activity_prompt(preferences_list):
    """Verilen tercihler listesine göre bir prompt oluşturur."""
    # preferences_list formatı: [{"username": "user1", "budget": "Low", "location": "Indoor", "activity_level": "Relaxed", "available_days": "Pazartesi,Salı"}, ...]
    
    prompt = """Aşağıdaki kullanıcı tercihlerini DİKKATLİCE ANALİZ EDEREK, TÜM KULLANICILARIN ORTAK İLGİ ALANLARINA VE TERCİHLERİNE UYGUN, SADECE 1 (BİR) ADET popüler ve yaygın grup etkinliği önerisi sun (örneğin: film gecesi, konsere gitmek, yürüyüş, piknik, brunch, müze gezisi, yemek kursu, spor etkinliği, kart oyunları, barbekü, tekne turu, workshop). Ortak noktaları bulmaya odaklan. Lütfen farklı türlerde öneriler sunmaya özen göster ve tekrarlayan önerilerden kaçın. Her öneri için etkinliğin adını, kısa bir açıklamasını, tahmini bütçesini (Düşük/Orta/Yüksek), kullanıcının genel mekan tercihine (İç Mekan/Dış Mekan/Her İkisi) uygun, belirgin ve somut bir mekan önerisi (örn: Sinema Salonu, Açık Hava Parkı, Ev Ortamı, Sahil Kafe, Kapalı Tenis Kortu vb. şeklinde), aktivite seviyesini (Rahat/Orta/Enerjik) ve UYGUN GÜNLERİ belirt. Türkçe yanıt ver ve yanıtını sadece JSON formatında, 'suggestions' anahtarı altında bir dizi (array) olarak döndür. Her öneri bir nesne (object) olmalı ve 'name', 'description', 'budget', 'location', 'activity_level', 'available_days' anahtarlarına sahip olmalı. JSON çıktısı dışında hiçbir metin, açıklama veya markdown formatı kullanma.\n\n"""
    
    prompt += "Kullanıcı Tercihleri:\n"
    for pref in preferences_list:
        days_info = f", Müsait Günler: {pref.get('available_days', 'Belirtilmemiş')}" if pref.get('available_days') else ""
        prompt += f"- Kullanıcı: {pref['username']}, Bütçe: {pref['budget']}, Mekan: {pref['location']}, Aktivite Seviyesi: {pref['activity_level']}{days_info}\n"
    
    return prompt

def get_activity_suggestion(preferences_list):
    """Gemini API'den etkinlik önerileri alır."""
    model = setup_gemini_client()
    if not model:
        return None

    prompt = create_activity_prompt(preferences_list)
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"Error calling Gemini API: {e}")
        return None

def parse_ai_response(response_text):
    """AI yanıtını JSON olarak ayrıştırır."""
    try:
        # Gemini'dan gelen yanıt bazen JSON'dan önce/sonra boşluk veya markdown içerebilir
        # Sadece JSON kısmını çekmeye çalışalım
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        json_string = response_text[json_start:json_end]

        data = json.loads(json_string)
        return data.get("suggestions", []) # 'suggestions' anahtarını arıyoruz
    except json.JSONDecodeError as e:
        st.error(f"Failed to parse AI response as JSON: {e}. Raw response: {response_text}")
        return []
    except Exception as e:
        st.error(f"An unexpected error occurred while parsing AI response: {e}")
        return []
