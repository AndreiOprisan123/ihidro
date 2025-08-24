"""
This file contains the core logic for the iHidro Scraper.
It handles making web requests, managing state, and parsing data.
"""
import logging
import json
from typing import Any, Dict
import datetime # A fost adăugat pentru a obține data curentă

# Home Assistant recommends using aiohttp for async web requests.
import aiohttp
import asyncio
from bs4 import BeautifulSoup
from aiohttp import ClientTimeout

_LOGGER = logging.getLogger(__name__)

class IhidroApi:
    """
    Manages the connection to the iHidro service and handles all API calls.
    """

    def __init__(self, username: str, password: str):
        """
        Initializes the API instance with user credentials.
        
        Args:
            username (str): The username for the iHidro account.
            password (str): The password for the iHidro account.
        """
        self._username = username
        self._password = password
        self._session: aiohttp.ClientSession | None = None
        self._is_logged_in = False
        self._timeout = ClientTimeout(total=60) # Timeout pentru cererile web

    async def async_login(self) -> bool:
        """
        Performs the login to the iHidro service.
        Returns True on success, False otherwise.
        """
        _LOGGER.info("Attempting to log in to iHidro.")
        if self._session is None:
            self._session = aiohttp.ClientSession()

        try:
            # Aici vei face cererea POST către URL-ul de login
            login_url = "https://ihidro.ro/portal/default.aspx"
            payload = {
                "txtLogin": self._username,
                "txtpwd": self._password
            }

            async with self._session.post(login_url, data=payload, timeout=self._timeout) as resp:
                resp.raise_for_status()
                # Aici verifici dacă login-ul a fost un succes
                # Poți verifica un text specific de pe pagina de după login.
                html_content = await resp.text()
                if "titleRR2" in html_content:
                    self._is_logged_in = True
                    _LOGGER.info("Login successful.")
                    return True
                else:
                    _LOGGER.error("Login failed: Username or password incorrect.")
                    self._is_logged_in = False
                    return False

        except aiohttp.ClientError as e:
            _LOGGER.error(f"Login failed: {e}")
            self._is_logged_in = False
            return False

    async def get_data(self) -> Dict[str, Any] | None:
        """
        Scrapes data from the iHidro website and returns a dictionary.
        This method will be called by the sensor entities to update their state.
        
        Returns:
            A dictionary containing the scraped data, or None on failure.
        """
        if not self._is_logged_in:
            if not await self.async_login():
                return None

        _LOGGER.info("Scraping data from iHidro.")

        try:
            data_url = "https://ihidro.ro/portal/default.aspx"
            async with self._session.get(data_url, timeout=self._timeout) as resp:
                resp.raise_for_status()
                html_content = await resp.text()
                
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Extrage perioada de transmitere a indexului
                perioade_el = soup.find(id="titleRR2")
                text_index = perioade_el.text.strip() if perioade_el else ""

                # Extrage textul facturilor
                facturi_de_plata_el = soup.find(id="dvCrDr")
                text_factura = facturi_de_plata_el.text.strip() if facturi_de_plata_el else ""
                
                is_period_active = "TRANSMITE INDEXUL" in text_index.upper()
                perioada_index = ""
                
                if is_period_active:
                    perioada_index_list = text_index.split(" ")
                    try:
                        perioada_index = f"{perioada_index_list[-3]} - {perioada_index_list[-1]}"
                    except IndexError:
                        perioada_index = text_index # Fallback la textul complet
                else:
                    perioada_index = "Perioada de transmitere este închisă."

                data = {
                    "perioada_transmitere_index": perioada_index,
                    "text_factura": text_factura,
                    "este_perioada_de_trimitere": is_period_active
                }
                
                return data
            
        except aiohttp.ClientError as e:
            _LOGGER.error(f"Failed to scrape data: {e}")
            return None
            
    async def transmit_index(self, index_value: str) -> bool:
        """
        Sends the index to the iHidro service.
        This method will be called by the `submit_index` service.
        """
        if not self._is_logged_in:
            if not await self.async_login():
                return False

        _LOGGER.info(f"Transmitting index '{index_value}' to iHidro.")
        try:
            # --- Pasul 1: Scraping pentru datele necesare în payload ---
            transmit_page_url = "https://ihidro.ro/portal/SelfMeterReading.aspx"
            async with self._session.get(transmit_page_url) as resp:
                resp.raise_for_status()
                html_content = await resp.text()
                soup = BeautifulSoup(html_content, 'html.parser')

                # Extragem valorile din tabelul de pe pagină
                # (ex. POD, SerialNumber, etc.)
                pod = soup.find("td", {"data-th": "POD"}).text.strip()
                serial_number = soup.find("td", {"data-th": "Serie contor"}).text.strip()
                prev_mr_result = soup.find("td", {"data-th": "Ultimul index citit de distribuitor"}).text.strip()
                
            # Obținem data curentă și o formatăm.
            current_date = datetime.date.today().strftime("%d/%m/%Y")

            # --- Pasul 2: Crearea payload-ului JSON ---
            payload = { 
                "objMeterValueProxy": {
                    "UsageSelfMeterReadEntity": [
                        {
                            "POD": pod,
                            "SerialNumber": serial_number,
                            "NewMeterReadDate": current_date, # S-a înlocuit data fixă cu data curentă
                            "registerCat": "1.8.0",
                            "distributor": "E-Distributie Muntenia Nord", # Poți extrage și această valoare
                            "meterInterval": "",
                            "supplier": "",
                            "distCustomer": "",
                            "distCustomerId": "",
                            "distContract": "",
                            "distContractDate": None,
                            "UtilityAccountNumber": "8001141409",
                            "prevMRResult": prev_mr_result,
                            "newmeterread": index_value
                        }
                    ]
                }
            }
            
            # --- Pasul 3: Trimiterea cererii POST cu JSON-ul ---
            headers = {'Content-Type': 'application/json'}
            post_url = "https://ihidro.ro/portal/SelfMeterReading.aspx/GetMeterValueRequest"
            
            async with self._session.post(post_url, data=json.dumps(payload), headers=headers, timeout=self._timeout) as resp:
                resp.raise_for_status()
                response_json = await resp.json()
                
                # Verifică răspunsul
                if "success" in response_json and response_json["success"]:
                    _LOGGER.info(f"Indexul '{index_value}' a fost transmis cu succes.")
                    return True
                else:
                    _LOGGER.error("Transmisie index eșuată. Răspunsul serverului nu a fost cel așteptat.")
                    _LOGGER.debug(f"Răspuns server: {response_json}")
                    return False

        except aiohttp.ClientError as e:
            _LOGGER.error(f"Failed to transmit index: {e}")
            return False
            
    async def __aenter__(self):
        """Asynchronous context manager entry."""
        if self._session is None:
            self._session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Asynchronous context manager exit."""
        if self._session is not None:
            await self._session.close()

