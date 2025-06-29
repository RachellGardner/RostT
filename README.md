"#bio_core" 
# Django-проект

## Установка и запуск

1. **Клонируй репозиторий:**

```bash / Win + R
git clone https://github.com/Kirikiri2/bio_core biocore
cd biocore
```

2. **Создай виртуальное окружение и активируй его:**
```
python -m venv venv

# Linux/macOS
source venv/bin/activate

# Windows
venv\Scripts\activate
```
3. **Установи зависимости из файла requirements.txt**
```
pip install -r requirements.txt
```
4. **Выполни миграции (на всякий случай):**
```
python manage.py migrate
```
5. **Запусти сервер:**
```
python manage.py runserver
```
5. **Открой в браузере:**
```
http://127.0.0.1:8000/
```