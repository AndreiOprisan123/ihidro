import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import os

print("🚀 iHidro Scraper a pornit!")

# Încarcă credentialele
try:
    with open("/data/options.json", "r") as f:
        options = json.load(f)
        username = options.get("username")
        password = options.get("password")
except Exception as e:
    print(f"❌ Eroare la citirea credentialelor: {e}")
    username = password = None

# Setări Selenium + Chrome headless
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

try:
    driver = webdriver.Chrome(options=chrome_options)
    print("🔐 Autentificare iHidro.ro...")
    driver.get("https://ihidro.ro/portal/default.aspx")
    time.sleep(2)
    driver.find_element(By.ID, "txtLogin").send_keys(username)
    driver.find_element(By.ID, "txtpwd").send_keys(password)
    driver.find_element(By.ID, "btnlogin").click()
    time.sleep(4)

    driver.get("https://ihidro.ro/portal/Dashboard.aspx")
    time.sleep(2)

    perioade_el = driver.find_element(By.ID, "titleRR2")
    text = perioade_el.text.strip()

    print(f"✅ Perioada transmisiei: {text}")

    with open("/data/output.txt", "w", encoding="utf-8") as out:
        out.write(text)

except Exception as e:
    print(f"❌ Eroare la rulare: {e}")
finally:
    driver.quit()
