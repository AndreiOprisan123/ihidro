import json
import argparse
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import datetime

print("🚀 iHidro Addon a pornit!")

# --- Funcție pentru a încărca opțiunile din Home Assistant ---
def get_ha_options():
    try:
        with open('/data/options.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ Fisierul /data/options.json nu a fost găsit. Rulezi local? Folosesc valori goale.")
        return {}

# --- Încărcare opțiuni și configurare argumente ---
options = get_ha_options()
username = options.get("IHIDRO_USER", "")
password = options.get("IHIDRO_PASS", "")

parser = argparse.ArgumentParser(description="Scraper și Submitter pentru iHidro.ro")
parser.add_argument('--action', type=str, choices=['scrape', 'submit'], default='scrape', help="Acțiunea de executat.")
parser.add_argument('--index', type=str, help="Valoarea indexului de transmis.")
args = parser.parse_args()

# Verifică dacă avem credențiale
if not username or not password:
    raise ValueError("❌ User-ul si parola iHidro nu sunt setate in configuratia addon-ului!")

# --- Setări Selenium ---
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920,1080")


driver = None
try:
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 20)
    
    print("🔐 Autentificare iHidro.ro...")
    driver.get("https://ihidro.ro/portal/default.aspx")
    wait.until(EC.presence_of_element_located((By.ID, "txtLogin")))
    driver.find_element(By.ID, "txtLogin").send_keys(username)
    driver.find_element(By.ID, "txtpwd").send_keys(password)
    driver.find_element(By.ID, "txtpwd").send_keys(Keys.RETURN)
    wait.until(EC.presence_of_element_located((By.ID, "titleRR2")))
    print("✅ Autentificare reușită.")

    # --- Execuție acțiune ---
    if args.action == 'scrape':
        print("🔍 Acțiune: Scrape - Extragere date...")
        perioade_el = driver.find_element(By.ID, "titleRR2")
        text_index = perioade_el.text.strip()
        facturi_de_plata_el = driver.find_element(By.ID, "dvCrDr")
        text_factura = facturi_de_plata_el.get_attribute("innerText").strip()
        
        azi = datetime.datetime.now().strftime("%d/%m/%Y")
        if text_factura == f"Sold la {azi}":
            text_factura = "Nu există facturi de plată."

        is_period_active = "TRANSMITE INDEXUL" in text_index.upper()
        
        perioada_index = "Perioada de transmitere este închisă."
        if is_period_active:
            try:
                perioada_parts = text_index.split(" ")
                perioada_index = f"{perioada_parts[-3]} - {perioada_parts[-1]}"
            except IndexError:
                perioada_index = text_index
        
        data = {
            "perioada": perioada_index,
            "factura": text_factura,
            "este_perioada_de_trimitere": is_period_active,
            "last_update": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        with open("/data/output.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("✔️ Datele au fost salvate în /data/output.json")

    elif args.action == 'submit':
        if not args.index:
            raise ValueError("❌ Acțiunea 'submit' necesită parametrul '--index'.")
        
        print(f"📤 Acțiune: Submit - Trimitere index: {args.index}...")
        driver.get("https://ihidro.ro/portal/SelfMeterReading.aspx")

        index_input = wait.until(EC.presence_of_element_located((By.ID, "EnterEa_0")))
        index_input.clear()
        index_input.send_keys(args.index)
        print(f"Indexul '{args.index}' a fost introdus.")
        time.sleep(1)

        wait.until(EC.element_to_be_clickable((By.ID, "btnSubmitReading"))).click()
        print("✔️ Primul buton de trimitere a fost apăsat.")
        
        final_button = wait.until(EC.element_to_be_clickable((By.ID, "btnSubmitMeterReading")))
        time.sleep(1.5)
        final_button.click()
        print("✔️ Butonul final de confirmare ('Da') a fost apăsat.")
        time.sleep(3)
        print("✅ Procesul de trimitere a fost finalizat cu succes!")

except Exception as e:
    print(f"❌ A apărut o eroare: {e}")
    if driver:
        driver.save_screenshot("/data/error_screenshot.png")
        print("📸 Captură de ecran salvată în /share/error_screenshot.png (accesibilă din File Editor)")

finally:
    if driver:
        driver.quit()
    print("✅ Script iHidro s-a încheiat.")

