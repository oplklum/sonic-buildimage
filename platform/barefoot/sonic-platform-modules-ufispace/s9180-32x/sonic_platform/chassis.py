#!/usr/bin/env python

#############################################################################
# PDDF
# Module contains an implementation of SONiC Chassis API
#
#############################################################################

try:
    import time
    import subprocess
    from sonic_platform_pddf_base.pddf_chassis import PddfChassis
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")

NUM_COMPONENT = 2

class Chassis(PddfChassis):
    """
    PDDF Platform-specific Chassis class
    """

    STATUS_INSERTED = "1"
    STATUS_REMOVED = "0"
    port_dict = {}

    def __init__(self, pddf_data=None, pddf_plugin_data=None):
        PddfChassis.__init__(self, pddf_data, pddf_plugin_data)
        self._initialize_components()

    def _initialize_components(self):
        from sonic_platform.component import Component
        for index in range(NUM_COMPONENT):
            component = Component(index)
            self._component_list.append(component)

    # Provide the functions/variables below for which implementation is to be overwritten
    def initizalize_system_led(self):
        return True

    def get_status_led(self):
        return self.get_system_led("SYS_LED")

    def get_system_led(self, led_device_name):
        ipmi_cmd_sys_led = "ipmitool raw 0x3c 0x20 0x0"
        ipmi_cmd_fantray_led = "ipmitool raw 0x3c 0x21 0x0"

        led_dict = {"SYS_LED":  {
                        "ipmi_cmd": ipmi_cmd_sys_led,
                        "index": 0},
                    "FAN_LED":  {
                        "ipmi_cmd": ipmi_cmd_sys_led,
                        "index": 1},
                    "PSU1_LED":  {
                        "ipmi_cmd": ipmi_cmd_sys_led,
                        "index": 2},
                    "PSU2_LED":  {
                        "ipmi_cmd": ipmi_cmd_sys_led,
                        "index": 3},
                    "FANTRAY1_LED":  {
                        "ipmi_cmd": ipmi_cmd_fantray_led,
                        "index": 0},
                    "FANTRAY2_LED":  {
                        "ipmi_cmd": ipmi_cmd_fantray_led,
                        "index": 1},
                    "FANTRAY3_LED":  {
                        "ipmi_cmd": ipmi_cmd_fantray_led,
                        "index": 2},
                    "FANTRAY4_LED":  {
                        "ipmi_cmd": ipmi_cmd_fantray_led,
                        "index": 3}
                    }
        color_dict = {0: "off",
                      1: "yellow",
                      2: "green"}

        if led_device_name not in led_dict.keys():
            status = "[FAILED] " + led_device_name + " is not configured"
            return (status)

        ipmi_cmd = led_dict[led_device_name]["ipmi_cmd"]
        index = led_dict[led_device_name]["index"]
        status, output = subprocess.getstatusoutput(ipmi_cmd)

        if status != 0:
            return ("ipmi_cmd error, cmd={}, status={}".format(ipmi_cmd, status))

        color_raw = int(output.split()[index])

        if color_raw not in color_dict.keys():
            color = "unknown"
        else:
            color = color_dict[color_raw]

        return (color)

    def get_change_event(self, timeout=0):
        """
        Returns a nested dictionary containing all devices which have
        experienced a change at chassis level
        Args:
            timeout: Timeout in milliseconds (optional). If timeout == 0,
                this method will block until a change is detected.
        Returns:
            (bool, dict):
                - bool: True if call successful, False if not;
                - dict: A nested dictionary where key is a device type,
                        value is a dictionary with key:value pairs in the format of
                        {'device_id':'device_event'}, where device_id is the device ID
                        for this device and device_event.
                        The known devices's device_id and device_event was defined as table below.
                         -----------------------------------------------------------------
                         device   |     device_id       |  device_event  |  annotate
                         -----------------------------------------------------------------
                         'fan'          '<fan number>'     '0'              Fan removed
                                                           '1'              Fan inserted
                         'sfp'          '<sfp number>'     '0'              Sfp removed
                                                           '1'              Sfp inserted
                                                           '2'              I2C bus stuck
                                                           '3'              Bad eeprom
                                                           '4'              Unsupported cable
                                                           '5'              High Temperature
                                                           '6'              Bad cable
                         'voltage'      '<monitor point>'  '0'              Vout normal
                                                           '1'              Vout abnormal
                         --------------------------------------------------------------------
                  Ex. {'fan':{'0':'0', '2':'1'}, 'sfp':{'11':'0', '12':'1'},
                       'voltage':{'U20':'0', 'U21':'1'}}
                  Indicates that:
                     fan 0 has been removed, fan 2 has been inserted.
                     sfp 11 has been removed, sfp 12 has been inserted.
                     monitored voltage U20 became normal, voltage U21 became abnormal.
                  Note: For sfp, when event 3-6 happened, the module will not be avalaible,
                        XCVRD shall stop to read eeprom before SFP recovered from error status.
        """

        change_event_dict = {"fan": {}, "sfp": {}, "voltage": {}}

        start_time = time.time()
        forever = False

        if timeout == 0:
            forever = True
        elif timeout > 0:
            timeout = timeout / float(1000)  # Convert to secs
        else:
            print("get_change_event:Invalid timeout value", timeout)
            return False, change_event_dict

        end_time = start_time + timeout
        if start_time > end_time:
            print(
                "get_change_event:" "time wrap / invalid timeout value",
                timeout,
            )
            return False, change_event_dict  # Time wrap or possibly incorrect timeout
        try:
            while timeout >= 0:
                # check for sfp
                sfp_change_dict = self.get_transceiver_change_event()
                # check for fan
                # fan_change_dict = self.get_fan_change_event()
                # check for voltage
                # voltage_change_dict = self.get_voltage_change_event()

                if sfp_change_dict:
                    change_event_dict["sfp"] = sfp_change_dict
                    # change_event_dict["fan"] = fan_change_dict
                    # change_event_dict["voltage"] = voltage_change_dict
                    return True, change_event_dict
                if forever:
                    time.sleep(1)
                else:
                    timeout = end_time - time.time()
                    if timeout >= 1:
                        time.sleep(1)  # We poll at 1 second granularity
                    else:
                        if timeout > 0:
                            time.sleep(timeout)
                        return True, change_event_dict
        except Exception as e:
            print(e)
        print("get_change_event: Should not reach here.")
        return False, change_event_dict

    def get_transceiver_change_event(self):
        current_port_dict = {}
        ret_dict = {}

        # Check for OIR events and return ret_dict
        for index in range(self.platform_inventory['num_ports']):
            if self._sfp_list[index].get_presence():
                current_port_dict[index] = self.STATUS_INSERTED
            else:
                current_port_dict[index] = self.STATUS_REMOVED

        if len(self.port_dict) == 0:       # first time
            self.port_dict = current_port_dict
            return {}

        if current_port_dict == self.port_dict:
            return {}

        # Update reg value
        for index, status in current_port_dict.items():
            if self.port_dict[index] != status:
                ret_dict[index] = status
                #ret_dict[str(index)] = status
        self.port_dict = current_port_dict
        for index, status in ret_dict.items():
            if int(status) == 1:
                pass
                #self._sfp_list[int(index)].check_sfp_optoe_type()
        return ret_dict
