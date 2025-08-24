"""The iHidro Scraper integration."""
import logging

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.exceptions import HomeAssistantError

# Importă clasa care conține logica de scraping.
from .ihidro_api import IhidroApi

_LOGGER = logging.getLogger(__name__)

# O listă cu platformele (entitățile) pe care le va încărca integrarea.
# În cazul nostru, doar senzorii.
PLATFORMS: list[Platform] = [Platform.SENSOR]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Setează iHidro Scraper din config entry."""
    
    # Asigură-te că există date de configurare.
    if not entry.data:
        _LOGGER.error("Datele de configurare lipsesc. Nu se poate configura.")
        return False
    
    _LOGGER.info("Configurarea iHidro Scraper a început.")

    # Stochează o referință către clasa de API în memoria Home Assistant.
    # Această referință va fi folosită de fișierul sensor.py.
    hass.data.setdefault(entry.domain, {})[entry.entry_id] = {
        "api": IhidroApi(
            username=entry.data.get("username"),
            password=entry.data.get("password")
        )
    }

    # Înregistrează serviciul de transmitere a indexului.
    # Numele serviciului va fi 'ihidro_scraper.submit_index'.
    hass.services.async_register(
        entry.domain, "submit_index", async_submit_index_service
    )

    # Încărcă platformele (în cazul nostru, senzorii)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Dezactivează o intrare de configurare."""
    
    _LOGGER.info("Dezactivarea iHidro Scraper a început.")

    # Descarcă platformele.
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        # Șterge datele stocate.
        hass.data[entry.domain].pop(entry.entry_id)

    return unload_ok

async def async_submit_index_service(call: ServiceCall):
    """Metoda care se ocupă de transmiterea indexului."""
    
    _LOGGER.info("Serviciul 'submit_index' a fost apelat.")
    
    # Preia instanța API din memoria Home Assistant.
    entry_id = list(call.hass.data["ihidro_scraper"].keys())[0]
    api: IhidroApi = call.hass.data["ihidro_scraper"][entry_id]["api"]
    
    try:
        # Aici folosești logica ta existentă de transmitere a indexului
        # Presupunem că ai o metodă `transmit_index` în clasa ta `IhidroApi`.
        await api.transmit_index() 
        _LOGGER.info("Indexul a fost transmis cu succes!")
        
    except Exception as e:
        _LOGGER.error(f"Eroare la transmiterea indexului: {e}")
        # Poți arunca o excepție pentru a notifica Home Assistant că a apărut o eroare.
        raise HomeAssistantError("Eroare la transmiterea indexului") from e
