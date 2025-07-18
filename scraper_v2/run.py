import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time

# Încarcă username și parola din options.json
with open("/data/options.json", "r") as f:
    options_data = json.load(f)
    username = options_data.get("username")
    password = options_data.get("password")

# Configurare browser headless
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(options=chrome_options)

try:
    print("🔐 Autentificare iHidro...")
    driver.get("https://ihidro.ro/portal/default.aspx")
    time.sleep(2)

    driver.find_element(By.ID, "txtLogin").send_keys(username)
    driver.find_element(By.ID, "txtpwd").send_keys(password)
    driver.find_element(By.ID, "btnlogin").click()
    time.sleep(4)

    driver.get("https://ihidro.ro/portal/Dashboard.aspx")
    time.sleep(2)

    el = driver.find_element(By.ID, "titleRR2")
    result = el.text.strip()

    with open("/data/output.txt", "w", encoding="utf-8") as f:
        f.write(result)
    print(f"✅ Perioada găsită: {result}")

except Exception as e:
    print(f"❌ Eroare: {e}")
    with open("/data/output.txt", "w") as f:
        f.write(f"Eroare: {e}")

finally:
    driver.quit()