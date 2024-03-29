"""Platform for sensor integration."""
import random

from datetime import datetime, timezone

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass
)

from .const import DOMAIN

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add sensors for passed config_entry in HA."""
    hub = hass.data[DOMAIN][config_entry.entry_id]

    new_devices = []
    for area_information in hub.areas:
        new_devices.append(StateSensor(area_information))
    if new_devices:
        async_add_entities(new_devices)


class StateSensor(SensorEntity):
    """Base representation of a Hello World Sensor."""

    should_poll = True
    
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = [ "ok", "open", "close" ]
    #_attr_icon = "mdi:window-open-variant"

    def __init__(self, area_info):
        """Initialize the sensor."""
        self._area_info = area_info
        self._attr_unique_id = f"{area_info.id}_state"
        self._attr_name = f"{area_info.name} State"

    # To link this entity to the cover device, this property must return an
    # identifiers value matching that used in the cover, but no other information such
    # as name. If name is returned, this entity will then also become a device in the
    # HA UI.
    @property
    def device_info(self):
        """Return information to link this entity with the correct device."""
        return {
            "identifiers": {
                (DOMAIN, self._area_info.area_id)
                },
            "name": "Area " + self._area_info.name,
            #"manufacturer": MANUFACTURER,
            #"model": self.data["model"]
        }


    # This property is important to let HA know if this entity is online or not.
    # If an entity is offline (return False), the UI will refelect this.
    @property
    def available(self) -> bool:
        """Return True if ventilation sensor and hub is available."""
        return True
        
    @property
    def icon(self) -> str | None:
        """Icon of the entity, based on state."""
        if self.state == "open":
            return "mdi:window-open-variant"
        elif self.state == "close":
            return "mdi:window-closed-variant"

        return "mdi:check"


    @property
    def last_check(self) -> datetime:
        """Return the date and time of the last check."""
        return self._area_info.last_check
        
    @property
    def window_sensor_count(self) -> int:
        """Return the number of window sensors."""
        return self._area_info.window_sensor_count
        
    @property
    def temperature_sensor_count(self) -> int:
        """Return the number of temperature sensors."""
        return self._area_info.temperature_sensor_count
        
    @property
    def humidity_sensor_count(self) -> int:
        """Return the number of humidity sensors."""
        return self._area_info.humidity_sensor_count
        
    @property
    def co2_sensor_count(self) -> int:
        """Return the number of co2 sensors."""
        return self._area_info.co2_sensor_count

    @property
    def extra_state_attributes(self):
        return {
            "last_check": self.last_check,
            "window_sensor_count": self.window_sensor_count,
            "temperature_sensor_count": self.temperature_sensor_count,
            "humidity_sensor_count": self.humidity_sensor_count,
            "co2_sensor_count": self.co2_sensor_count
            }

    async def async_added_to_hass(self):
        """Run when this Entity has been added to HA."""
        # Sensors should also register callbacks to HA when their state changes
        self._area_info.register_callback(self.async_write_ha_state)

    async def async_will_remove_from_hass(self):
        """Entity being removed from hass."""
        # The opposite of async_added_to_hass. Remove any registered call backs here.
        self._area_info.remove_callback(self.async_write_ha_state)


    @property
    def state(self):
        """Return the state of the sensor."""
        return self._area_info.state



    async def async_update(self):
        """Fetch new state."""

        await self._area_info.check_state()