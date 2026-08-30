import os
import sys
import json

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.utils.logger import logger
from src.utils.ezproxy_auth import COOKIES_FILE_PATH

def import_cookies_interactively():
    print("==================================================")
    print("🍪 EZproxy Cookie Importer (Headless Server Helper)")
    print("==================================================")
    print("Так как сервер работат без графического экрана (Headless Linux),")
    print("самый простой способ передать авторизацию — скопировать куки из браузера вашего ПК.\n")
    print("📌 ИНСТРУКЦИЯ (занимает 15 секунд):")
    print("1. Откройте в браузере на вашем ПК портал институциональной библиотеки:")
    print("   https://ieeexplore-ieee-org.ezproxy.afeka.ac.il (или Technion/Kinneret)")
    print("2. Откройте консоль разработчика (F12 ➔ Network) ИЛИ расширение Cookie-Editor.")
    print("3. Вставьте содержимое ниже.\n")
    print("Вам доступно 2 формата ввода:")
    print(" - Формат 1: Заголовок Cookie ('ezproxyl=...; JSESSIONID=...; ...')")
    print(" - Формат 2: Raw JSON экспортированный из Cookie-Editor\n")
    
    user_input = input("👉 Вставьте куки и нажмите Enter:\n").strip()
    
    if not user_input:
        print("❌ Ошибка: Ввод пуст.")
        return

    parsed_cookies = {}
    
    # Try parsing as JSON first
    if user_input.startswith("[") or user_input.startswith("{"):
        try:
            data = json.loads(user_input)
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and "name" in item and "value" in item:
                        parsed_cookies[item["name"]] = item["value"]
            elif isinstance(data, dict):
                parsed_cookies = data
        except Exception as e:
            logger.error(f"Не удалось распарсить JSON: {e}")

    # Fallback: parse as standard HTTP Cookie header string
    if not parsed_cookies:
        pairs = user_input.split(";")
        for p in pairs:
            if "=" in p:
                k, v = p.strip().split("=", 1)
                if k and v:
                    parsed_cookies[k] = v

    if not parsed_cookies:
        print("❌ Не удалось извлечь куки из введенной строки.")
        return

    with open(COOKIES_FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(parsed_cookies, f, indent=2)

    print(f"\n✅ УСПЕХ! Сохранено {len(parsed_cookies)} куки в файл:")
    print(f"   {COOKIES_FILE_PATH}")
    print("\nТеперь вы можете вызывать 'python3 main.py' — пайплайн будет скачивать полные IEEE PDF!")

if __name__ == "__main__":
    import_cookies_interactively()
