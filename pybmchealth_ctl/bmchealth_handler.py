#!/usr/bin/python -u

import os
import sys
import gobject
import subprocess
import dbus
import dbus.service
import dbus.mainloop.glib
import obmc.dbuslib.propertycacher as PropertyCacher
from obmc.dbuslib.bindings import get_dbus, DbusProperties, DbusObjectManager
from obmc.sensors import HwmonSensor as HwmonSensor
from obmc.sensors import SensorThresholds as SensorThresholds
from obmc.events import EventManager, Event
import obmc_system_config as System
import time

import mac_guid

DBUS_NAME = 'org.openbmc.Sensors'
DBUS_INTERFACE = 'org.freedesktop.DBus.Properties'
SENSOR_VALUE_INTERFACE = 'org.openbmc.SensorValue'

g_bmchealth_obj_path = "/org/openbmc/sensors/bmc_health"
g_recovery_count = [0,0,0,0,0,0,0,0]
g_dhcp_status = 1
g_net_down_status = 1

_EVENT_MANAGER = EventManager()

#light: 1, light on; 0:light off
def bmchealth_set_status_led(light):
    if 'GPIO_CONFIG' not in dir(System) or 'STATUS_LED' not in System.GPIO_CONFIG:
        return
    try:
        data_reg_addr = System.GPIO_CONFIG["STATUS_LED"]["data_reg_addr"]
        offset = System.GPIO_CONFIG["STATUS_LED"]["offset"]
        inverse = "no"
        if "inverse" in  System.GPIO_CONFIG["STATUS_LED"]:
            inverse = System.GPIO_CONFIG["STATUS_LED"]["inverse"]
        print data_reg_addr
        cmd_data = subprocess.check_output("devmem  " + hex(data_reg_addr) , shell=True)
        cmd_data = cmd_data.rstrip("\n")
        cur_data = int(cmd_data, 16)
        if (inverse == "yes"):
            if (light == 1):
                cur_data = cur_data & ~(1<<offset)
            else:
                cur_data = cur_data | (1<<offset)
        else:
            if (light == 1):
                cur_data = cur_data | (1<<offset)
            else:
                cur_data = cur_data & ~(1<<offset)

        set_led_cmd = "devmem  " + hex(data_reg_addr) + " 32 " + hex(cur_data)[:10]
        os.system(set_led_cmd)
    except:
        pass

def LogEventBmcHealthMessages(evd1 = 0, evd2 = 0, evd3 = 0):
    bus = get_dbus()
    objpath = g_bmchealth_obj_path
    obj = bus.get_object(DBUS_NAME, objpath, introspect=False)
    intf = dbus.Interface(obj, dbus.PROPERTIES_IFACE)
    sensortype = int(intf.Get(HwmonSensor.IFACE_NAME, 'sensor_type'), 16)
    sensor_number = int(intf.Get(HwmonSensor.IFACE_NAME, 'sensornumber'), 16)

    log = Event(Event.SEVERITY_INFO, sensortype, sensor_number, 0x70, evd1, evd2, evd3)
    logid=_EVENT_MANAGER.add_log(log)

    if logid == 0:
        return False
    else:
        bmchealth_set_status_led(1)
        return True

def bmchealth_set_value_with_dbus(val):
    try:
        b_bus = get_dbus()
        b_obj= b_bus.get_object(DBUS_NAME, g_bmchealth_obj_path)
        b_interface = dbus.Interface(b_obj,  DBUS_INTERFACE)
        b_interface.Set(SENSOR_VALUE_INTERFACE, 'value', val)
    except:
        print "bmchealth_set_value Error!!!"
        return -1
    return 0

def bmchealth_set_value(val):
    retry = 20
    while(bmchealth_set_value_with_dbus(val)!=0):
        if (retry <=0):
            return -1
        time.sleep(1)
    return 0

def bmchealth_check_network():
    carrier_file_path = "/sys/class/net/eth0/carrier"
    operstate_file_path = "/sys/class/net/eth0/operstate"
    check_ipaddr_command ="ifconfig eth0"
    check_ipaddr_keywords = "inet addr"

    carrier = ""    #0 or 1
    operstate = ""  #up or down
    ipaddr = ""

    global g_dhcp_status
    global g_net_down_status

    org_dhcp_status = g_dhcp_status
    org_down_status = g_net_down_status
    try:
        cmd_data = subprocess.check_output(check_ipaddr_command, shell=True)
        if cmd_data.find(check_ipaddr_keywords) >=0:
            ipaddr = "1"
        else:
            ipaddr = "0"
    except:
        print "[bmchealth_check_network]Error conduct operstate!!!"
        return False

    try:
        with open(carrier_file_path, 'r') as f:
            for line in f:
                carrier = line.rstrip('\n')
    except:
        print "[bmchealth_check_network]Error conduct carrier!!!"
        return False

    try:
        with open(operstate_file_path, 'r') as f:
            for line in f:
                operstate = line.rstrip('\n')
    except:
        print "[bmchealth_check_network]Error conduct operstate!!!"
        return False

    #check dhcp fail status
    if ipaddr == "0" and carrier == "1" and operstate == "up":
        if g_dhcp_status == 1:
            print "bmchealth_check_network:  DHCP Fail"
            g_dhcp_status = 0
            bmchealth_set_value(0x1)
            LogEventBmcHealthMessages(0x1, 0x2)
    else:
        g_dhcp_status = 1

    #check network down
    if carrier == "0" and operstate=="down":
        if g_net_down_status == 1:
            print "bmchealth_check_network:  network down Fail"
            g_net_down_status = 0
            bmchealth_set_value(0x1)
            LogEventBmcHealthMessages(0x1, 0x1)
    else:
        g_net_down_status = 1

    if g_dhcp_status == 1 and g_net_down_status == 1:
        bmchealth_set_value(0x0)

    return True

def bmchealth_fix_and_check_mac():
    print "fix-mac & fix-guid start"
    fix_mac_status = mac_guid.fixMAC()
    fix_guid_status = mac_guid.fixGUID()

    print "bmchealth: check mac status:" + str(fix_mac_status)
    print "bmchealth: check guid status:" + str(fix_guid_status)
    #check bmchealth macaddress

    if fix_mac_status == 0 or fix_guid_status == 0:
        LogEventBmcHealthMessages(0xC)
    return True

def bmchealth_check_watchdog():
    print "check watchdog timeout start"
    check_watchdog1_command = "devmem 0x1e785010"
    check_watchdog2_command = "devmem 0x1e785030"
    reboot_file_path = "/var/lib/obmc/check_reboot"
    watchdog1_event_counter_path = "/var/lib/obmc/watchdog1"
    watchdog2_event_counter_path = "/var/lib/obmc/watchdog2"
    watchdog1_exist_counter = 0
    watchdog2_exist_counter = 0

    #read event counters
    try:
        watchdog1_str_data = subprocess.check_output(check_watchdog1_command, shell=True)
        watchdog1_timeout_counter = (  int(watchdog1_str_data, 16) >> 8) & 0xff
    except:
        print "[bmchealth_check_watchdog]Error conduct operstate!!!"
        return False

    try:
        watchdog2_str_data = subprocess.check_output(check_watchdog2_command, shell=True)
        watchdog2_timeout_counter = ( int(watchdog2_str_data, 16) >> 8) & 0xff
    except:
        print "[bmchealth_check_watchdog]Error conduct operstate!!!"
        return False

    #check reboot timeout or WDT timeout
    if os.path.exists(reboot_file_path):
            os.remove(reboot_file_path)
            f = file(watchdog1_event_counter_path,"w")
            f.write(str(watchdog1_timeout_counter))
            f.close()
            f = file(watchdog2_event_counter_path,"w")
            f.write(str(watchdog2_timeout_counter))
            f.close()
            return True
    else:
        try:
            with open(watchdog1_event_counter_path, 'r') as f:
                for line in f:
                    watchdog1_exist_counter = int(line.rstrip('\n'))
        except:
            pass

        try:
            with open(watchdog2_event_counter_path, 'r') as f:
                for line in f:
                    watchdog2_exist_counter = int(line.rstrip('\n'))
        except:
            pass

    if watchdog1_timeout_counter > watchdog1_exist_counter or watchdog2_timeout_counter > watchdog2_exist_counter:
        f = file(watchdog1_event_counter_path,"w")
        f.write(str(watchdog1_timeout_counter))
        f.close()
        f = file(watchdog2_event_counter_path,"w")
        f.write(str(watchdog2_timeout_counter))
        f.close()
        print "Log watchdog expired event"
        LogEventBmcHealthMessages(0x3)
    return True

def bmchealth_check_i2c():
    i2c_recovery_check_path = ["/proc/i2c_recovery_bus0","/proc/i2c_recovery_bus1","/proc/i2c_recovery_bus2","/proc/i2c_recovery_bus3","/proc/i2c_recovery_bus4","/proc/i2c_recovery_bus5","/proc/i2c_recovery_bus6","/proc/i2c_recovery_bus7"]
    global g_recovery_count

    for num in range(len(i2c_recovery_check_path)):
        if os.path.exists(i2c_recovery_check_path[num]):
            try:
                with open(i2c_recovery_check_path[num], 'r') as f:
                    bus_id = int(f.readline())
                    error_code = int(f.readline(), 16)
                    current_recovery_count = int(f.readline())
                    if current_recovery_count > g_recovery_count[num]:
                        print "Log i2c recovery event"
                        LogEventBmcHealthMessages(0xA, bus_id, 0x1)
                        g_recovery_count[num] = current_recovery_count
            except:
                print "[bmchealth_check_i2c]exception !!!"

    return True

if __name__ == '__main__':
    mainloop = gobject.MainLoop()
    #set bmchealth default value
    bmchealth_set_value(0)
    bmchealth_fix_and_check_mac()
    bmchealth_check_watchdog()
    gobject.timeout_add(1000,bmchealth_check_network)
    gobject.timeout_add(1000,bmchealth_check_i2c)
    print "bmchealth_handler control starting"
    mainloop.run()

