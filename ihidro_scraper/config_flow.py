"""Config flow for iHidro Scraper integration."""
import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from .ihidro_api import IhidroApi

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("username"): str,
        vol.Required("password"): str,
    }
)

async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validează datele de intrare de la utilizator."""
    api = IhidroApi(data["username"], data["password"])
    
    # Folosește un context manager pentru a te asigura că sesiunea este închisă.
    async with api:
        if not await api.async_login():
            raise vol.Invalid("Login eșuat. Verifică numele de utilizator și parola.")
    
    # Returnează un dicționar cu un titlu, care va fi afișat în Home Assistant.
    return {"title": "iHidro Scraper"}

class IhidroScraperConfigFlow(config_entries.ConfigFlow, domain="ihidro_scraper"):
    """Handle a config flow for iHidro Scraper."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except vol.Invalid as err:
                errors["base"] = str(err)
            except Exception as e:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown_error"
            else:
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

