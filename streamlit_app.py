from app.main import main
from app.utils.database import init_database

if __name__ == "__main__":
    init_database() # Veritabanı başlatma fonksiyonunu çağır
    main()

