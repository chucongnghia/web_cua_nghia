import os
from app import create_app
from app.config import BaseConfig
from seed import run_seed

app = create_app()

if __name__ == "__main__":
    # If database file does not exist yet, seed it automatically
    if not os.path.exists(BaseConfig.DATABASE_PATH):
        print("[*] Chưa phát hiện CSDL, tiến hành khởi tạo dữ liệu mẫu...")
        run_seed()

    print("[*] StudyDocs Server dang khoi dong...")
    print(" -> Dia chi truy cap: http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=True)
