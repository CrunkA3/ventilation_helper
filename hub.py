"""A hub to hanle all areas"""
from __future__ import annotations
import logging

from datetime import datetime, timezone
import pytz

import asyncio
import random

from homeassistant.core import HomeAssistant
from homeassistant.helpers import (
    area_registry,
    entity_registry,
    device_registry
    )

_LOGGER = logging.getLogger(__name__)

class Hub:
    """Dummy hub for Hello World example."""

    manufacturer = "Demonstration Corp"

    def __init__(self, hass: HomeAssistant) -> None:
        """Init dummy hub."""
        self._hass = hass
        self._name = "Ventilation Helper"
        self._id = "ventilation_helper"
        self.areas = []

        ar = area_registry.async_get(hass)
        areas = ar.areas
        for area in areas:
            self.areas.append(AreaInformation(self.hub_id, areas[area].id, f"Ventilation " + areas[area].name, self))
    
        self.online = True

    @property
    def hub_id(self) -> str:
        """ID for dummy hub."""
        return self._id

    @property
    def hass(self) -> HomeAssistant:
        """hass object."""
        return self._hass

    async def test_connection(self) -> bool:
        """Test connectivity to the Dummy hub is OK."""
        await asyncio.sleep(1)
        return True



class AreaInformation:
    """Ventilation infos for a sprcific area"""

    def __init__(self, hub_id: str, area_id: str, name: str, hub: Hub) -> None:
        """Init area information."""
        self._hub_id = hub_id
        self._area_id = area_id
        self.hub = hub
        self.name = name
        self._callbacks = set()
        self._loop = asyncio.get_event_loop()
        self._state = "ok"
        self._last_check = datetime.utcnow().replace(tzinfo=pytz.utc)
        self._last_reminder = datetime.utcnow().replace(tzinfo=pytz.utc)

        self._window_sensors = []
        self._temperature_sensors = []
        self._humidity_sensors = []
        self._co2_sensors = []

        # Some static information about this device
        #self.firmware_version = f"0.0.{random.randint(1, 9)}"
        #self.model = "Test Device"

    @property
    def id(self) -> str:
        """Return ID for area information."""
        return f"{self.hub_id}_{self.area_id}"
        
    @property
    def hub_id(self) -> str:
        """Return ID for area information."""
        return self._hub_id

    @property
    def area_id(self) -> str:
        """Return ID for area information."""
        return self._area_id

    @property
    def state(self) -> str:
        """Return state for area information."""
        return self._state

    @property
    def last_check(self) -> str:
        """Return last check for area information."""
        return self._last_check

    @property
    def last_reminder(self) -> str:
        """Return date and time of last reminder."""
        return self._last_reminder

    @property
    def window_sensor_count(self) -> str:
        """Return number of window sensors"""
        return len(self._window_sensors)

    @property
    def temperature_sensor_count(self) -> str:
        """Return number of temperature sensors"""
        return len(self._temperature_sensors)

    @property
    def humidity_sensor_count(self) -> str:
        """Return number of humidity sensors"""
        return len(self._humidity_sensors)

    @property
    def co2_sensor_count(self) -> str:
        """Return number of co2 sensors"""
        return len(self._co2_sensors)


    @property
    def hass(self) -> HomeAssistant:
        """hass object"""
        return self.hub.hass



    async def check_state(self):
        """Check window target state"""
                    
        er = entity_registry.async_get(self.hass)
        dr = device_registry.async_get(self.hass)

        #get all divices for area
        devices = device_registry.async_entries_for_area(dr, self.area_id)

        #get window sensors
        self._window_sensors = []
        for device in devices:
            entities = entity_registry.async_entries_for_device(er, device.id)
            if len(entities) > 0:
                self._window_sensors = self._window_sensors + [entity for entity in entities if entity.original_device_class == "window"]

        if len(self._window_sensors) == 0:
            return
        
        utc_now = datetime.utcnow().replace(tzinfo=pytz.utc)

        #read window state
        area_window_state = "off"
        area_window_state_last_changed = utc_now
        for window_sensor in self._window_sensors:
            window_state = self.hass.states.get(window_sensor.entity_id)
            if window_state.state == "on":
                area_window_state = "on"
            
            if window_state.state == area_window_state:
                window_state_last_changed = window_state.last_changed
                _LOGGER.info(window_state_last_changed)
                area_window_state_last_changed = min(area_window_state_last_changed, window_state_last_changed)

    
        #Fensterstatus und wie lange schon?
        #if type(self.last_reminder) == str:
        #self.last_reminder = datetime.strptime(last_reminder, datetime_fmt)

        area_state_timedelta = utc_now - area_window_state_last_changed
        area_state_minutes = area_state_timedelta.total_seconds() / 60
        
        reminder_timedelta = utc_now - self.last_reminder
        reminder_minutes = reminder_timedelta.total_seconds() / 60

        if area_state_minutes < 7:
            if self._state != "ok":
                await self.set_state("ok")
            return
        
        #if reminder_minutes < 7:
        #    return
    
        #get other sensors
        self._temperature_sensors = []
        self._humidity_sensors = []
        self._co2_sensors = []
        for device in devices:
            entities = entity_registry.async_entries_for_device(er, device.id)
            if len(entities) > 0:
                self._temperature_sensors = self._temperature_sensors + [entity for entity in entities if entity.original_device_class == "temperature"]
                self._humidity_sensors = self._humidity_sensors + [entity for entity in entities if entity.original_device_class == "humidity"]
                self._co2_sensors = self._co2_sensors + [entity for entity in entities if entity.original_device_class == "carbon_dioxide"]
        
        new_state = "ok"

        #Fenster zu, prüfen ob geöffnet werden soll
        if area_window_state == "off":
            if len(self._humidity_sensors) + len(self._temperature_sensors) + len(self._co2_sensors) == 0:
                new_state = "ok"
            else:
                if len(self._humidity_sensors) > 0:
                    for humidity_sensor in self._humidity_sensors:
                        humidity = int(self.hass.states.get(humidity_sensor.entity_id).state)
                        if humidity > 60:
                            new_state = "open"
                            
                if len(self._co2_sensors) > 0:
                    for co2_sensor in self._co2_sensors:
                        co2 = float(self.hass.states.get(co2_sensor.entity_id).state)
                        if co2 > 1200:
                            new_state = "open"


        #Fenster auf, prüfen ob geschlossen werden soll
        if area_window_state == "on":
            if len(self._humidity_sensors) + len(self._temperature_sensors) + len(self._co2_sensors) == 0:
                new_state = "close"
            
            else:
                if len(self._temperature_sensors) > 0:
                    for temperature_sensor in self._temperature_sensors:
                        termperature = float(state.get(temperature_sensor.entity_id))
                        if termperature < 20:
                            new_state = "close"
                            state.setattr(id_reminder, datetime.utcnow())
                if len(self._humidity_sensors) > 0:
                    for humidity_sensor in self._humidity_sensors:
                        humidity = float(state.get(humidity_sensor.entity_id))
                        if humidity < 50:
                            new_state = "close"
                            state.setattr(id_reminder, datetime.utcnow())
                if len(self._co2_sensors) > 0:
                    for co2_sensor in self._co2_sensors:
                        co2 = float(state.get(co2_sensor.entity_id))
                        if co2 < 900:
                            new_state = "close"
                            state.setattr(id_reminder, datetime.utcnow())



        if new_state != "ok":
            self._last_reminder = utc_now

        self._last_check = utc_now

        #if self._state != new_state:
        await self.set_state(new_state)




    async def set_state(self, state: str) -> None:
        """
        Set dummy cover to the given position.

        State is announced a random number of seconds later.
        """
        self._state = state

        await self.publish_updates()





    def register_callback(self, callback: Callable[[], None]) -> None:
        """Register callback, called when Roller changes state."""
        self._callbacks.add(callback)

    def remove_callback(self, callback: Callable[[], None]) -> None:
        """Remove previously registered callback."""
        self._callbacks.discard(callback)

    async def publish_updates(self) -> None:
        """Schedule call all registered callbacks."""
        for callback in self._callbacks:
            callback()