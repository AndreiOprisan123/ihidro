"""Platform for sensor entities."""
import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.sensor import SensorEntity

from .ihidro_api import IhidroApi

_LOGGER = logging.getLogger(__name__)

# Setează o frecvență de actualizare de 15 minute.
SCAN_INTERVAL = timedelta(days=1)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Setează platforma senzorilor."""
    
    _LOGGER.info("Setarea platformei de senzori iHidro.")

    # Preia instanța API din datele Home Assistant.
    api: IhidroApi = hass.data[config_entry.domain][config_entry.entry_id]["api"]

    # Adaugă senzorii la Home Assistant.
    async_add_entities([
        IhidroSensor(api, "perioada_transmitere_index", "Perioada Transmitere Index"),
        IhidroSensor(api, "text_factura", "Text Factura"),
    ])

class IhidroSensor(SensorEntity):
    """Reprezintă o entitate senzor."""

    def __init__(self, api: IhidroApi, unique_id: str, name: str):
        """Inițializează senzorul."""
        self._api = api
        self._attr_unique_id = unique_id
        self._attr_name = name
        self._attr_state = None
        self._attr_available = True

    @property
    def native_value(self):
        """Returnează valoarea nativă a senzorului."""
        return self._attr_state

    @property
    def available(self) -> bool:
        """Returnează dacă entitatea este disponibilă."""
        return self._attr_available

    async def async_update(self) -> None:
        """Actualizează datele senzorului."""
        try:
            # Aici apelezi metoda ta de scraping pentru a obține datele.
            # Presupunem că ai o metodă `get_data` în clasa ta `IhidroApi`.
            scraped_data = await self._api.get_data()
            
            # Verificăm dacă datele au fost obținute și actualizăm starea senzorului.
            if scraped_data:
                self._attr_state = scraped_data.get(self._attr_unique_id)
                self._attr_available = True
                _LOGGER.debug(f"Senzorul '{self._attr_name}' a fost actualizat cu succes.")
            else:
                self._attr_available = False
                _LOGGER.warning("Datele de la iHidro nu au putut fi obținute.")

        except Exception as e:
            self._attr_available = False
            _LOGGER.error(f"Eroare la actualizarea senzorului '{self._attr_name}': {e}")
