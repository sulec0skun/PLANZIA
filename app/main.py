import streamlit as st
import json
from dotenv import load_dotenv
import os

from app.utils.database import init_database, create_user, authenticate_user, create_event, get_event_by_code, save_preferences, get_event_preferences, update_event_suggestion, mark_event_as_approved, get_approved_events_for_user, get_event_creator
from app.utils.helpers import generate_event_code, validate_event_code
from app.utils.auth import hash_password, verify_password, render_login_form, render_register_form, logout
from app.utils.ai_helper import get_activity_suggestion, parse_ai_response


load_dotenv()

def load_css(file_name):
    """CSS dosyasını okur ve Streamlit uygulamasına enjekte eder."""
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

def show_welcome_page():
    """Yeni Karşılama Ekranını gösterir."""
    # Başlıklar için ortalama CSS
    st.markdown("<h1 style='text-align: center; color: #FFFFFF;'>PLANZIA</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #FFFFFF;'><em>Ortak etkinlik bulmanın en kolay yolu</em></h3>", unsafe_allow_html=True)
    
    # Butonları ortalamak için sütunlar
    col1, col2, col3 = st.columns([1, 1, 1]) # 3 eşit sütun, ortadaki butonlar için
    with col2: # Ortadaki sütuna yerleştir
        st.write("") # Görsel boşluk için
        st.write("") # Görsel boşluk için
        # Giriş Yap butonu
        if st.button("GİRİŞ YAP", key="welcome_login_btn", use_container_width=True):
            st.session_state["current_page"] = "login"
            st.rerun()
        
        st.write("") # Butonlar arasına boşluk
        
        # Kayıt Ol butonu
        if st.button("KAYIT OL", key="welcome_register_btn", use_container_width=True):
            st.session_state["current_page"] = "register"
            st.rerun()


def show_login_page():
    """Giriş sayfasını gösterir ve giriş işlemlerini yönetir."""

    col_back_login, col_empty_login = st.columns([1, 5]) 
    with col_back_login:
        if st.button("← Geri", key="back_to_welcome"):
            st.session_state["current_page"] = "welcome"
            st.rerun()

    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        login_data = render_login_form()
        if login_data:
            username = login_data["username"]
            password = login_data["password"]
            stored_hashed_password = authenticate_user(username)
            if stored_hashed_password and verify_password(stored_hashed_password, password):
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.session_state["current_page"] = "dashboard"
                st.success(f"Welcome back, {username}!")
                st.rerun()
            else:
                st.error("Invalid username or password.")

    st.markdown("<br><br>", unsafe_allow_html=True) # Buton ile alt arasına boşluk
    col_home_login_empty1, col_home_login_btn, col_home_login_empty2 = st.columns([1, 1, 1])
    with col_home_login_btn:
        if st.button("Ana Sayfaya Dön", key="back_to_dashboard_from_login_bottom", use_container_width=True):
            st.session_state["current_page"] = "dashboard"
            st.rerun()

def show_register_page():
    """Kayıt sayfasını gösterir ve kayıt işlemlerini yönetir."""
    st.markdown("<h3 style='text-align: center; color: #FFFFFF;'>Kayıt Ol</h3>", unsafe_allow_html=True)
    
    col_back_register, col_empty_register = st.columns([1, 5])
    with col_back_register:
        if st.button("← Ana Sayfa", key="back_to_welcome_register"):
            st.session_state["current_page"] = "welcome"
            st.rerun()

    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        register_data = render_register_form()
        if register_data:
            new_username = register_data["username"]
            new_password = register_data["password"]
            hashed_password = hash_password(new_password);
            if create_user(new_username, hashed_password):
                st.success("Registration successful! Please login.")
                st.session_state["current_page"] = "login"
                st.rerun()
            else:
                st.error("Username already exists. Please choose a different one.")

    st.markdown("<br><br>", unsafe_allow_html=True) # Buton ile alt arasına boşluk
    col_home_register_empty1, col_home_register_btn, col_home_register_empty2 = st.columns([1, 1, 1])
    with col_home_register_btn:
        if st.button("Ana Sayfaya Dön 🏠", key="back_to_dashboard_from_register_bottom", use_container_width=True):
            st.session_state["current_page"] = "dashboard"
            st.rerun()

def show_dashboard():
    """Kullanıcı giriş yaptıktan sonra ana paneli gösterir."""
    st.markdown(f"<h1 style='text-align: center; color: #FFFFFF;'>Merhaba, {st.session_state.get('username', 'User')}!</h1>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True) # Boşluk eklendi (tekrar)
    st.markdown("<br>", unsafe_allow_html=True) # Ekstra boşluk eklendi
    st.markdown("<h3 style='text-align: center; color: #FFFFFF;'><i>Ne yapmak istiyorsun?</i></h3>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True) # Butonlar arasına boşluk eklendi (tekrar)
    st.markdown("<br>", unsafe_allow_html=True) # Ekstra boşluk eklendi
    st.markdown("<br>", unsafe_allow_html=True)
    # Butonları ortalamak için sütunlar
    col1, col2 = st.columns(2)

    with col1:
        if st.button("YENİ ETKİNLİK OLUŞTUR", key="dashboard_create_event_btn", use_container_width=True):
            st.session_state["current_page"] = "create_event"
            if "generated_event_code" in st.session_state:
                del st.session_state["generated_event_code"]
            if "event_created" in st.session_state:
                del st.session_state["event_created"]
            st.rerun()

    with col2:
        if st.button("ETKİNLİĞE KATIL", key="dashboard_join_event_btn", use_container_width=True):
            st.session_state["current_page"] = "join_event"
            if "event_code_to_join" in st.session_state:
                del st.session_state["event_code_to_join"]
            if "event_joined_successfully" in st.session_state:
                del st.session_state["event_joined_successfully"]
            st.rerun()

    st.markdown("<br><br><br><br><br><br>", unsafe_allow_html=True) # Buton ile alt arasına boşluk artırıldı
    st.markdown("<h2 style='text-align: center; color: #FFFFFF;'>🎉 Etkinliklerim</h2>", unsafe_allow_html=True)
    st.markdown("---")

    username = st.session_state.get("username")
    if username:
        approved_events = get_approved_events_for_user(username)
        if approved_events:
            for event in approved_events:
                event_data = json.loads(event['suggestion'])[0] # Onaylanan önerinin ilkini al
                event_code = event['event_code']
                
                col_left_ticket_dash, col_ticket_dash, col_right_ticket_dash = st.columns([1, 4, 1])
                with col_ticket_dash:
                    with st.container(border=True):
                        st.markdown(f"<h3 style='text-align: center; color: #000000;'>🎬 {event_data.get('name', 'İsimsiz Etkinlik')}</h3>", unsafe_allow_html=True)
                        st.markdown("<br>", unsafe_allow_html=True)
                        
                        # Detaylar alt alta sıralanacak
                        raw_days = event_data.get('available_days', 'Belirtilmemiş')
                        if isinstance(raw_days, list):
                            formatted_days = ", ".join(raw_days)
                        else:
                            formatted_days = raw_days.strip('[]\"')
                        st.markdown(f"📅 **Gün:** {formatted_days}")
                        st.markdown(f"📍 **Lokasyon:** {event_data.get('location', 'Belirtilmemiş')}")

                        # Katılımcı bilgileri
                        preferences_for_event = get_event_preferences(event_code) # Bu event_code ile tercihler çekilecek
                        participant_count = len(preferences_for_event)
                        participants = [p['username'] for p in preferences_for_event]
                        st.markdown(f"👥 **Katılımcı Sayısı:** {participant_count}")
                        st.markdown(f"👤 **Katılımcılar:** {', '.join(participants)}")
                    
                        st.markdown("<br>", unsafe_allow_html=True)
                        st.markdown(f"<p style='text-align: center; color: #000000; font-style: italic;'>İyi Eğlenceler!</p>", unsafe_allow_html=True)
                st.markdown("<br><br>", unsafe_allow_html=True) # Etkinlikler arası boşluk
        else:
            st.info("Henüz onaylanmış bir etkinliğiniz bulunmamaktadır.")
    else:
        st.warning("Onaylanmış etkinlikleri görmek için giriş yapmalısınız.")
    
    st.markdown("<br><br><br><br><br><br>", unsafe_allow_html=True) # Buton ile alt arasına boşluk artırıldı
    col_logout_empty1, col_logout_btn, col_logout_empty2 = st.columns([1, 1, 1])
    with col_logout_btn:
        if st.button("Çıkış Yap ", key="dashboard_logout_btn", use_container_width=True):
            logout()
            st.rerun()


def show_create_event():
    """Etkinlik oluşturma sayfasını gösterir."""
    col_back, col_title, col_empty = st.columns([1, 4, 1]) # Geri butonu için yer açıldı

    with col_back:
        if st.button("← Geri", key="back_to_dashboard_from_create"):
            st.session_state["current_page"] = "dashboard"
            st.rerun()
    with col_title:
        st.markdown("<h2 style='text-align: center; color: #FFFFFF;'>Etkinlik Oluştur</h2>", unsafe_allow_html=True)

    st.markdown("---") # Ayırıcı çizgi

    if "generated_event_code" not in st.session_state:
        event_code = generate_event_code()
        creator_username = st.session_state.get("username")

        if creator_username:
            if create_event(creator_username, event_code):
                st.session_state["generated_event_code"] = event_code
                st.session_state["event_created"] = True
                st.session_state["event_code_to_join"] = event_code # Tercihler formuna yönlendirmek için kodu sakla
                st.session_state["event_joined_successfully"] = True # Bu, join_event sayfasının tercih formunu doğrudan göstermesini sağlayacak
                st.session_state["previous_page"] = "create_event"
                st.session_state["is_creator_for_current_event"] = True # Etkinliği oluşturan kişi olduğunu işaretle
            else:
                st.error("Etkinlik oluşturulurken bir hata oluştu. Lütfen tekrar deneyin.")
                return # Hata durumunda devam etme
        else:
            st.error("Kullanıcı giriş yapmamış. Lütfen etkinlik oluşturmak için giriş yapın.")
            return # Hata durumunda devam etme

    if "event_created" in st.session_state and st.session_state["event_created"]:
        st.markdown("<br>", unsafe_allow_html=True) # Boşluk
        st.markdown("<h4 style='text-align: center; color: #FFFFFF;'>Etkinliğin için 8 haneli özel kod oluşturuldu:</h4>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True) # Boşluk

        # Kodu sadece göster (KOPYALA butonu kaldırıldı)
        st.markdown(
            f"""
            <div style='
                background-color: #f0f2f6; /* Kutu arka planı beyazımsı gri */
                color: #000000; /* Kutu içindeki metin siyah */
                border: 2px solid #6A0DAD; /* Mor kenarlık */
                border-radius: 8px;
                padding: 20px;
                text-align: center;
                margin: auto;
                width: 70%; /* Kutu genişliği */
                box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            '>
                <h2 style='color: #000000; margin-bottom: 0px;'>{st.session_state['generated_event_code']}</h2>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.markdown("<br>", unsafe_allow_html=True) # Boşluk
        st.markdown("<h4 style='text-align: center; color: #FFFFFF;'>Bu kodu arkadaşlarınla paylaş, onlar da katılsın!</h4>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True) # Boşluk

        # Devam Et butonu sağda
        col_left_empty, col_continue = st.columns([3, 1])
        with col_continue:
            if st.button("DEVAM ET →", key="continue_to_preferences", use_container_width=True):
                # Oluşturulan kodu otomatik olarak al ve tercih ekranına yönlendir
                st.session_state["event_code_to_join"] = st.session_state["generated_event_code"]
                st.session_state["event_joined_successfully"] = True # Bu, join_event sayfasının tercih formunu doğrudan göstermesini sağlayacak
                st.session_state["current_page"] = "preferences_page" # preferences_page'e yönlendir
                st.session_state["previous_page"] = "create_event" # Tercihler sayfasından geri dönüş için önceki sayfayı kaydet
                
                # Temizlik
                del st.session_state["generated_event_code"]
                del st.session_state["event_created"]
                st.rerun()
    
    st.markdown("<br><br>", unsafe_allow_html=True) # Buton ile alt arasına boşluk
    col_home_empty1, col_home_btn, col_home_empty2 = st.columns([1, 1, 1])
    with col_home_btn:
        if st.button("Ana Sayfaya Dön 🏠", key="back_to_dashboard_from_create_event_bottom", use_container_width=True):
            st.session_state["current_page"] = "dashboard"
            st.rerun()


def show_join_event():
    """Etkinliğe katılma sayfasını gösterir."""
    col_back, col_title, col_empty = st.columns([1, 4, 1]) # Geri butonu için yer açıldı

    with col_back:
        if st.button("← Geri", key="back_to_dashboard_from_join"):
            st.session_state["current_page"] = "dashboard"
            st.rerun()
    with col_title:
        st.markdown("<h2 style='text-align: center; color: #FFFFFF;'>Etkinliğe Katıl</h2>", unsafe_allow_html=True)

    st.markdown("---") # Ayırıcı çizgi

    if "event_code_to_join" not in st.session_state:
        st.session_state["event_code_to_join"] = None
    if "event_joined_successfully" not in st.session_state:
        st.session_state["event_joined_successfully"] = False

    if not st.session_state["event_joined_successfully"]:
        with st.container(border=True):
            st.subheader("Etkinlik Kodunu Gir") # Başlık güncellendi
            event_code_input = st.text_input("Etkinlik Kodu", key="join_event_code_input").strip()
            if st.button("Katıl", key="join_event_button", use_container_width=True): # Buton metni güncellendi
                if event_code_input:
                    if validate_event_code(event_code_input):
                        event = get_event_by_code(event_code_input)
                        if event:
                            st.session_state["event_code_to_join"] = event_code_input
                            st.session_state["event_joined_successfully"] = True
                            st.session_state["is_creator_for_current_event"] = False # Katılımcı olduğu için creator değil varsayılan olarak. Eğer creatorsa aşağıdaki kod True yapacak.
                            st.success(f"Etkinliğe başarıyla katıldınız: **{event_code_input}**")
                            st.session_state["current_page"] = "preferences_page" # preferences_page'e yönlendir
                            # Etkinliği oluşturan kişiyi belirle
                            creator_username = get_event_creator(event_code_input)
                            if creator_username == st.session_state.get("username"):
                                st.session_state["is_creator_for_current_event"] = True
                            
                            st.session_state["previous_page"] = "join_event"
                            st.rerun()
                        else:
                            st.error("Etkinlik bulunamadı. Kodu kontrol edip tekrar deneyin.")
                    else:
                        st.error("Geçersiz Etkinlik Kodu formatı. Kod 8 alfasayısal karakter olmalı.")
                else:
                    st.warning("Lütfen bir etkinlik kodu girin.")
    else:
        st.write(f"Şu anki etkinlik: **{st.session_state['event_code_to_join']}**") # Metin güncellendi
        show_preferences_form(st.session_state["event_code_to_join"])

    st.markdown("<br><br>", unsafe_allow_html=True) # Buton ile alt arasına boşluk
    col_home_join_empty1, col_home_join_btn, col_home_join_empty2 = st.columns([1, 1, 1])
    with col_home_join_btn:
        if st.button("Ana Sayfaya Dön 🏠", key="back_to_dashboard_from_join_event_bottom", use_container_width=True):
            st.session_state["current_page"] = "dashboard"
            st.rerun()


def show_preferences_form(event_code):
    """Kullanıcıdan etkinlik tercihleri toplamak için formu gösterir ve AI önerilerini entegre eder."""
    col_back_prefs, col_title_prefs, col_empty_prefs = st.columns([1, 4, 1]) # Geri butonu için yer açıldı

    with col_back_prefs:
        if st.button("← Geri", key="back_to_join_from_prefs"):
            # Önceki sayfaya dönmek için previous_page'i kullan
            if st.session_state.get("previous_page") == "create_event":
                st.session_state["current_page"] = "create_event"
                # Eğer create_event sayfasına dönülüyorsa, event_created ve generated_event_code'u tut
                # Ancak burada oluşturulan event_code_to_join'i de doğru aktarmalıyız, aksi halde tercih formu tekrar açılır.
                # Zaten show_create_event içinde set edildiği için burada tekrar set etmeye gerek yok gibi duruyor.
            elif st.session_state.get("previous_page") == "join_event":
                st.session_state["current_page"] = "join_event"
                # join_event sayfasına dönerken, event_code_to_join ve event_joined_successfully'i koru
                # Bu zaten show_join_event içinde ayarlandığı için burada ek işlemeye gerek yok.
            else:
                # Varsayılan olarak dashboard'a dön
                st.session_state["current_page"] = "dashboard"
            
            # Tercihler kaydedildi durumunu sıfırla ki geri dönüldüğünde AI öneri sayfasına otomatik yönlenmesin
            del st.session_state["preferences_saved_for_event"]
            st.rerun()
    with col_title_prefs:
        st.markdown("<h2 style='text-align: center; color: #FFFFFF;'>Tercihlerini Belirle</h2>", unsafe_allow_html=True)

    st.markdown("---") # Ayırıcı çizgi

    username = st.session_state.get("username")

    if not username:
        st.error("Tercihleri belirlemek için giriş yapmanız gerekiyor.")
        return

    with st.container(border=True):
        with st.form("preferences_form"):
            st.markdown("<h4 style='color: #000000;'>Bütçen ne kadar?</h4>", unsafe_allow_html=True)
            budget_options = ["Düşük", "Orta", "Yüksek"]
            budget = st.radio(" ", budget_options, key="budget_radio", horizontal=True)

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("<h4 style='color: #000000;'>Nerede buluşalım?</h4>", unsafe_allow_html=True)
            location_options = ["İç Mekan", "Dış Mekan", "Her İkisi"]
            location = st.radio("  ", location_options, key="location_radio", horizontal=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("<h4 style='color: #000000;'>Ne kadar aktif olsun?</h4>", unsafe_allow_html=True)
            activity_level_options = ["Rahat", "Orta", "Enerjik"]
            activity_level = st.radio("   ", activity_level_options, key="activity_level_radio", horizontal=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("<h4 style='color: #000000;'>Müsait olduğun günler:</h4>", unsafe_allow_html=True)
            days_of_week = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
            selected_days = {}
            cols_days = st.columns(3)
            for i, day in enumerate(days_of_week):
                with cols_days[i % 3]:
                    selected_days[day] = st.checkbox(day, key=f"day_{day}")

            submit_prefs = st.form_submit_button("KAYDET VE DEVAM →", use_container_width=True)

            if submit_prefs:
                available_days = [day for day, checked in selected_days.items() if checked]
                available_days_str = ",".join(available_days)

                if save_preferences(event_code, username, budget, location, activity_level, available_days_str):
                    st.session_state["preferences_saved_for_event"] = event_code
                    st.session_state["regenerate_ai_suggestion"] = True # Tercihler kaydedildiğinde AI önerisini yeniden oluştur

                    if st.session_state.get("is_creator_for_current_event", False):
                        st.session_state["current_page"] = "ai_suggestion_page"
                    else:
                        st.session_state["current_page"] = "dashboard"
                        st.success("Tercihleriniz kaydedildi! Etkinlik yaratıcısı önerileri oluşturduğunda dashboard'unuzda görebilirsiniz. 🎉")
                    st.rerun()
                else:
                    st.error("Tercihler kaydedilirken bir hata oluştu. Lütfen tekrar deneyin.")

    # Tercihler başarıyla kaydedildiyse, AI öneri sayfasına yönlendir
    if st.session_state.get("preferences_saved_for_event") == event_code:
        st.session_state["current_page"] = "ai_suggestion_page"
        st.session_state["regenerate_ai_suggestion"] = True # AI önerisinin oluşturulmasını sağlamak için
        st.rerun()

    # AI öneri kısmı buradan kaldırıldı, show_ai_suggestion_page fonksiyonuna taşındı
    # if st.session_state.get("preferences_saved_for_event") == event_code:
    #     st.markdown("---")
    #     st.subheader("Etkinlik Bulalım")
    #     if st.button("Tıkla Ve Öğren ", key="get_ai_suggestions_after_prefs") or st.session_state.get("regenerate_ai_suggestion"):
    #         st.session_state["regenerate_ai_suggestion"] = False
    #         with st.spinner("Öneriler oluşturuluyor... Bu biraz zaman alabilir."):
    #             preferences = get_event_preferences(event_code)
    #             if not preferences:
    #                 st.info("Bu etkinlik için henüz tercih gönderilmedi. Lütfen katılımcılardan önce tercihlerini paylaşmalarını isteyin.")
    #                 st.session_state["current_ai_suggestion"] = None
    #             else:
    #                 ai_raw_response = get_activity_suggestion(preferences)
    #                 if ai_raw_response:
    #                     suggestions = parse_ai_response(ai_raw_response)
    #                     if suggestions:
    #                         st.session_state["current_ai_suggestion"] = suggestions[0]
    #                         formatted_suggestions = json.dumps(suggestions, ensure_ascii=False, indent=2)
    #                         if update_event_suggestion(event_code, formatted_suggestions):
    #                             st.success("Öneriler veritabanına kaydedildi!")
    #                         else:
    #                             st.warning("Öneriler veritabanına kaydedilemedi.")
    #                         suggestion = st.session_state["current_ai_suggestion"]
    #                         st.markdown(f"### {suggestion.get('name', 'İsimsiz Öneri')}")
    #                         st.write(f"**Açıklama:** {suggestion.get('description', 'Yok')}")
    #                         st.write(f"**Bütçe:** {suggestion.get('budget', 'Yok')}")
    #                         st.write(f"**Mekan:** {suggestion.get('location', 'Yok')}")
    #                         st.write(f"**Aktivite Seviyesi:** {suggestion.get('activity_level', 'Yok')}")
    #                         st.write(f"**Müsait Günler:** {suggestion.get('available_days', 'Yok')}")
    #                         st.markdown("---")
    #                     else:
    #                         st.error("Yapay zekadan geçerli öneriler alınamadı. Lütfen tekrar deneyin.")
    #                         st.session_state["current_ai_suggestion"] = None
    #                 else:
    #                     st.error("Yapay zeka yanıt dönmedi. Lütfen API anahtarınızı ve ağ bağlantınızı kontrol edin.")
    #                     st.session_state["current_ai_suggestion"] = None
    #     if st.session_state.get("current_ai_suggestion"):
    #         col_approve, col_regenerate = st.columns(2)
    #         with col_approve:
    #             if st.button("BU ÖNERİYİ ONAYLA ✅", key="approve_suggestion", use_container_width=True):
    #                 st.session_state["approved_event_suggestion"] = st.session_state["current_ai_suggestion"]
    #                 st.session_state["event_code_for_approved_suggestion"] = event_code
    #                 st.session_state["current_page"] = "approved_suggestion_page"
    #                 st.rerun()
    #         with col_regenerate:
    #             if st.button("YENİ ÖNERİ İSTE 🔄", key="regenerate_suggestion", use_container_width=True):
    #                 st.session_state["current_ai_suggestion"] = None
    #                 st.session_state["regenerate_ai_suggestion"] = True
    #                 st.rerun()
            
    st.markdown("<br><br>", unsafe_allow_html=True) # Buton ile alt arasına boşluk
    col_home_prefs_empty1, col_home_prefs_btn, col_home_prefs_empty2 = st.columns([1, 1, 1])
    with col_home_prefs_btn:
        if st.button("Ana Sayfaya Dön 🏠", key="back_to_dashboard_from_preferences_bottom", use_container_width=True):
            st.session_state["current_page"] = "dashboard"
            st.rerun()

def show_ai_suggestion_page(event_code):
    """AI destekli etkinlik önerisini gösterir."""
    # Yalnızca etkinliği oluşturan kişinin bu sayfaya erişmesini sağla
    if not st.session_state.get("is_creator_for_current_event", False):
        st.warning("Bu etkinliğin önerilerini sadece yaratıcısı görüntüleyebilir. Lütfen dashboard'a dönün. ⚠️")
        st.session_state["current_page"] = "dashboard"
        st.rerun()
        return

    st.markdown("<h2 style='text-align: center; color: #FFFFFF;'>🎉 Etkinlik Önerisi Hazır!</h2>", unsafe_allow_html=True)
    st.markdown("---")

    # AI önerisi oluşturma veya gösterme mantığı
    if "current_ai_suggestion" not in st.session_state or st.session_state.get("regenerate_ai_suggestion"):
        st.session_state["regenerate_ai_suggestion"] = False
        with st.spinner("Öneriler oluşturuluyor... Bu biraz zaman alabilir."):
            preferences = get_event_preferences(event_code)
            
            # Yeterli tercih toplanana kadar AI önerisi oluşturmayı bekle
            # if len(preferences) < 2: # En az 2 tercih olana kadar bekle # Geri alındı
            #     st.info(f"AI önerisi oluşturulmak için yeterli tercih toplanmadı. Şu an {len(preferences)} katılımcı tercihini kaydetti. Diğer katılımcılar tercihini girdiğinde öneri oluşturulacaktır.") # Geri alındı
            #     st.session_state["current_ai_suggestion"] = None # Öneri gösterme # Geri alındı
            if not preferences:
                st.info("Bu etkinlik için kaydedilmiş tercih bulunamadı.")
                st.session_state["current_ai_suggestion"] = None
            else:
                ai_raw_response = get_activity_suggestion(preferences)
                if ai_raw_response:
                    suggestions = parse_ai_response(ai_raw_response)
                    if suggestions:
                        st.session_state["current_ai_suggestion"] = suggestions[0]
                        formatted_suggestions = json.dumps(suggestions, ensure_ascii=False, indent=2)
                        if update_event_suggestion(event_code, formatted_suggestions):
                            pass
                        else:
                            st.warning("Öneriler veritabanına kaydedilemedi.")
                    else:
                        st.error("Yapay zekadan geçerli öneriler alınamadı. Lütfen tekrar deneyin.")
                        st.session_state["current_ai_suggestion"] = None
                else:
                    st.error("Yapay zeka yanıt dönmedi. Lütfen API anahtarınızı ve ağ bağlantınızı kontrol edin.")
                    st.session_state["current_ai_suggestion"] = None

    if st.session_state.get("current_ai_suggestion"):
        suggestion = st.session_state["current_ai_suggestion"]
        
        # Ana başlık ve bilet için sütunlar
        col_left_header, col_center_header, col_right_header = st.columns([1, 4, 1])
        with col_center_header:
            st.markdown("<h2 style='text-align: center; color: #FFFFFF;'>🎉 Etkinlik Hazır!</h2>", unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)

        # Bilet gibi görünmesini sağlayan ana kutu için sütunlar
        col_left_ticket, col_ticket, col_right_ticket = st.columns([1, 4, 1]) # Bilet genişliğini ayarlamak için
        with col_ticket:
            with st.container(border=True):
                st.markdown(f"<h3 style='text-align: center; color: #FFFFFF;'>🎬 {suggestion.get('name', 'İsimsiz Öneri')}</h3>", unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)
                
                # Detaylar alt alta sıralanacak
                raw_days = suggestion.get('available_days', 'Belirtilmemiş')
                if isinstance(raw_days, list):
                    formatted_days = ", ".join(raw_days)
                else:
                    formatted_days = raw_days.strip('[]\"')
                st.markdown(f"📅 **Gün:** {formatted_days}")
                st.markdown(f"📍 **Lokasyon:** {suggestion.get('location', 'Belirtilmemiş')}")




                # Katılımcı bilgileri
                preferences_for_event = get_event_preferences(event_code)
                participant_count = len(preferences_for_event)
                participants = [p['username'] for p in preferences_for_event]
                st.markdown(f"👥 **Katılımcı Sayısı:** {participant_count}")
                st.markdown(f"👤 **Katılımcılar:** {', '.join(participants)}")
            
                st.markdown("<br>", unsafe_allow_html=True)
                if 'description' in suggestion:
                    st.markdown(f"<p style='text-align: center; color: #FFFFFF; font-style: italic;'>{suggestion['description']}</p>", unsafe_allow_html=True)
                st.markdown(f"<p style='text-align: center; color: #FFFFFF; font-style: italic;'>İyi Eğlenceler!</p>", unsafe_allow_html=True)
        
        # Butonlar da bilet genişliğinde olsun diye aynı sütun içine alınacak
        with col_ticket:
            st.markdown("<br>", unsafe_allow_html=True)
            col_approve, col_regenerate = st.columns(2)
            with col_approve:
                if st.button("BU ÖNERİYİ ONAYLA ✅", key="approve_suggestion_btn", use_container_width=True):
                    if mark_event_as_approved(event_code):
                        st.session_state["current_page"] = "dashboard"
                        st.success("Etkinlik başarıyla onaylandı ve 'Etkinliklerim' bölümüne eklendi!")
                    else:
                        st.error("Etkinlik onaylanırken bir hata oluştu.")
                    st.rerun()
            with col_regenerate:
                if st.button("YENİ ÖNERİ İSTE 🔄", key="regenerate_suggestion_from_ai_page", use_container_width=True):
                    st.session_state["current_ai_suggestion"] = None
                    st.session_state["regenerate_ai_suggestion"] = True
                    st.rerun()
    else:
        st.info("Bu etkinlik için kaydedilmiş tercih bulunamadı.") # Mesaj güncellendi

    st.markdown("<br><br>", unsafe_allow_html=True)
    col_home_ai_empty1, col_home_ai_btn, col_home_ai_empty2 = st.columns([1, 1, 1])
    with col_home_ai_btn:
        if st.button("Ana Sayfaya Dön 🏠", key="back_to_dashboard_from_ai_page_bottom", use_container_width=True):
            st.session_state["current_page"] = "dashboard"
            del st.session_state["current_ai_suggestion"]
            st.session_state["regenerate_ai_suggestion"] = False
            st.rerun()


def show_approved_event_suggestion():
    """Onaylanmış etkinlik önerisini gösterir."""
    approved_suggestion = st.session_state.get("approved_event_suggestion")
    event_code = st.session_state.get("event_code_for_approved_suggestion")

    if not approved_suggestion or not event_code:
        st.error("Onaylanmış bir etkinlik önerisi bulunamadı.")
        # Hata durumunda çıkan Ana Sayfaya Dön butonu kaldırıldı, sayfa sonundaki buton kullanılacak
        return

   

    # Geri butonu ekliyoruz (tekrar)
    col_back_approved, col_title_approved, col_empty_approved = st.columns([1, 4, 1])
    with col_back_approved:
        if st.button("← Geri", key="back_to_preferences_from_approved"):
            st.session_state["current_page"] = "join_event" # Tercihler sayfasına dön
            st.session_state["event_code_to_join"] = event_code # Aynı etkinlik koduyla
            st.session_state["event_joined_successfully"] = True # Tercih formunu direkt göster
            st.session_state["preferences_saved_for_event"] = event_code # Tercihler kaydedildi olarak işaretle
            st.rerun()
    with col_title_approved:
        st.markdown("<h2 style='text-align: center; color: #FFFFFF;'>Etkinlik Önerisi Hazır!</h2>", unsafe_allow_html=True)

    st.markdown("---") # Ayırıcı çizgi

    with st.container(border=True):
        st.markdown(f"<h3 style='text-align: center; color: #000000;'>{approved_suggestion.get('name', 'İsimsiz Öneri')}</h3>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Detaylar için sütunlar
        col_detail1, col_detail2 = st.columns(2)

        with col_detail1:
            raw_days = approved_suggestion.get('available_days', 'Belirtilmemiş')
            # Eğer raw_days bir liste ise birleştir, değilse doğrudan kullan
            if isinstance(raw_days, list):
                formatted_days = ", ".join(raw_days)
            else:
                # Tırnakları ve köşeli parantezleri kaldır
                formatted_days = raw_days.strip('[]\"')
            st.markdown(f"**Günler:** {formatted_days}")
            st.markdown(f"**Lokasyon:** {approved_suggestion.get('location', 'Belirtilmemiş')}")
            st.markdown(f"**Bütçe:** {approved_suggestion.get('budget', 'Belirtilmemiş')}")

        with col_detail2:
            # Katılımcı sayısı ve listesi
            preferences_for_event = get_event_preferences(event_code)
            participant_count = len(preferences_for_event)
            participants = [p['username'] for p in preferences_for_event]
            st.markdown(f"**Katılımcı Sayısı:** {participant_count}")
            st.markdown(f"**Katılımcılar:** {', '.join(participants)}")

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center; color: #000000; font-style: italic;'>Grup tercihleri analiz edildi, herkese uygun bu aktivite öneriliyor!</p>", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    col_final_approve, col_final_new = st.columns([2, 2]) # Ana Sayfaya Dön butonu en alta taşındığı için boşluk bırakıldı
    with col_final_approve:
        if st.button("BU ÖNERİYİ ONAYLA ✅", key="final_approve_btn", use_container_width=True):
            # Etkinliği onaylandı olarak işaretle
            if mark_event_as_approved(event_code):
                st.success("Etkinlik önerisi başarıyla onaylandı ve kaydedildi!")
            else:
                st.error("Etkinlik onaylanırken bir hata oluştu.")
            
            st.session_state["current_page"] = "dashboard"
            del st.session_state["approved_event_suggestion"]
            del st.session_state["event_code_for_approved_suggestion"]
            st.rerun()
    with col_final_new:
        if st.button("YENİ ÖNERİ İSTE 🔄", key="final_regenerate_btn", use_container_width=True):
            st.session_state["current_page"] = "join_event" # Bu, show_join_event'e gidecek
            st.session_state["event_code_to_join"] = event_code # Aynı etkinlik koduyla tercihler sayfasına dön
            st.session_state["event_joined_successfully"] = True # Tercih formunu direkt göster
            st.session_state["preferences_saved_for_event"] = event_code # preferences_saved_for_event'ı ayarla
            del st.session_state["current_ai_suggestion"] # Mevcut öneriyi temizle
            st.session_state["regenerate_ai_suggestion"] = True # Yeniden oluşturma isteği bayrağını ayarla
            st.rerun()

    st.markdown("<br><br>", unsafe_allow_html=True) # Buton ile alt arasına boşluk
    col_home_approved_empty1, col_home_approved_btn, col_home_approved_empty2 = st.columns([1, 1, 1])
    with col_home_approved_btn:
        if st.button("Ana Sayfaya Dön 🏠", key="back_to_dashboard_from_approved_bottom", use_container_width=True):
            st.session_state["current_page"] = "dashboard"
            del st.session_state["approved_event_suggestion"]
            del st.session_state["event_code_for_approved_suggestion"]
            del st.session_state["current_ai_suggestion"]
            st.session_state["regenerate_ai_suggestion"] = False
            st.rerun()

def show_ai_results():
    pass # Bu fonksiyon artık kullanılmayacak, içi boşaltıldı

def main():
    st.set_page_config(page_title="PLANZIA", page_icon=":calendar:", layout="centered") # sidebar_state kaldırıldı

    load_css("styles/main.css")

    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
    if "username" not in st.session_state:
        st.session_state["username"] = None
    if "current_page" not in st.session_state:
        st.session_state["current_page"] = "welcome"
    if "preferences_saved_for_event" not in st.session_state:
        st.session_state["preferences_saved_for_event"] = None
    if "current_ai_suggestion" not in st.session_state:
        st.session_state["current_ai_suggestion"] = None
    if "approved_event_suggestion" not in st.session_state:
        st.session_state["approved_event_suggestion"] = None
    if "event_code_for_approved_suggestion" not in st.session_state:
        st.session_state["event_code_for_approved_suggestion"] = None
    if "regenerate_ai_suggestion" not in st.session_state:
        st.session_state["regenerate_ai_suggestion"] = False
    if "previous_page" not in st.session_state:
        st.session_state["previous_page"] = "dashboard"

    init_database()

    # Sidebar tamamen kaldırıldığı için bu bölüm artık yok

    # Sayfa yönlendirme
    if st.session_state["current_page"] == "welcome":
        show_welcome_page()
    elif st.session_state["current_page"] == "login":
        show_login_page()
    elif st.session_state["current_page"] == "register":
        show_register_page()
    elif st.session_state["current_page"] == "dashboard" and st.session_state["logged_in"]:
        show_dashboard()
    elif st.session_state["current_page"] == "create_event" and st.session_state["logged_in"]:
        show_create_event()
    elif st.session_state["current_page"] == "join_event" and st.session_state["logged_in"]:
        show_join_event()
    elif st.session_state["current_page"] == "preferences_page" and st.session_state["logged_in"]:
        # Tercihler sayfası ayrı bir yönlendirme olarak ele alınıyor
        if "event_code_to_join" in st.session_state and st.session_state["event_code_to_join"]:
            show_preferences_form(st.session_state["event_code_to_join"])
        else:
            st.error("Etkinlik kodu bulunamadı. Lütfen bir etkinliğe katılarak veya oluşturarak devam edin.")
            st.session_state["current_page"] = "dashboard"
            st.rerun()
    elif st.session_state["current_page"] == "approved_suggestion_page" and st.session_state["logged_in"]:
        show_approved_event_suggestion()
    elif st.session_state["current_page"] == "ai_suggestion_page" and st.session_state["logged_in"]:
        if "event_code_to_join" in st.session_state and st.session_state["event_code_to_join"]:
            show_ai_suggestion_page(st.session_state["event_code_to_join"])
        else:
            st.error("Etkinlik kodu bulunamadı. Lütfen bir etkinliğe katılarak veya oluşturarak devam edin.")
            st.session_state["current_page"] = "dashboard"
            st.rerun()
    # AI Results sayfası artık burada doğrudan çağrılmıyor
    else:
        if not st.session_state["logged_in"]:
            st.session_state["current_page"] = "welcome"
            st.rerun()
        else:
            st.info("Devam etmek için lütfen giriş yapın veya kaydolun.") # Metin Türkçe

if __name__ == "__main__":
    main()
