#!/usr/bin/env python3
# 
# Description: Radon Eye (RD200) remote query script 
# 
# Author: Konstantinos Xynos (2020,2021)
# How to: 
#  * Run the application once with get_device = True
#  * Copy the address of you Radon Eye into the address variable 
#  * set get_device = False
# 
# You can get different outputs using command_line = True or False
#
# WARNING: USE THIS SCRIPT AND KNOWLEDGE AT YOUR OWN RISK. IT IS 
# POSSIBLE TO CAUSE ISSUES WITH YOUR DEVICE IF YOU TRANSMIT 
# INCORRECT CODES/COMMANDS AND DATA TO IT. 
# YOU ACCEPT FULL RESPONSILIBITY RUNNING THIS SCRIPT AND/OR ITS CONTENTS
#
# todo:
# * Add JSON output
# * Replace is_connected() 

import asyncio
from imaplib import Int2AP
from bleak import *
from construct import *
from datetime import datetime


def TempHumi_u16_to_Temperature(value):
    i2 = value >> 8
    if (((value >> 7) & 1) == 1):
        return i2 +0.5
    else:
        return i2

def TempHumi_u16_to_Humidity(value):
    i2 = (value % 256)
    if (i2 <= 0):
        i2 += 256
    return (i2 % 128)

def print_result(command_line, date_time, data_struct):
    if data_struct.command == 80:
        if command_line :
            
            print(f'[Measurements] {date_time}')
            print(f'Current: {data_struct.measurement}')
            print(f'Avg 1 day: {data_struct.avg_day_measurement}')
            print(f'Avg 2 day: {data_struct.avg_2_day_measurement}')
            print(f'Avg Week: {data_struct.avg_week_measurement}')
            print(f'Avg Month: {data_struct.avg_month_measurement}')
            print(f'Value peak: {data_struct.value_peak}')
            print(f'Pulse count: {data_struct.pulse_count}')
            print(f'Pulse count 10m: {data_struct.pulse_count_10m}')

        else:
            print(f'{date_time}|{data_struct.measurement}|{data_struct.avg_day_measurement}|\
            {data_struct.avg_2_day_measurement}|{data_struct.avg_week_measurement}|\
            {data_struct.avg_month_measurement}|{data_struct.value_peak}|\
            {data_struct.pulse_count}|{data_struct.pulse_count_10m}')
    elif data_struct.command == 81:

        temperature = TempHumi_u16_to_Temperature(data_struct.temp_and_hum)
        humidity = TempHumi_u16_to_Humidity(data_struct.temp_and_hum)
        if command_line :
            print(f'[Info] {date_time}')
            print(f'Device Status: {data_struct.device_status}')
            print(f'Vib Status: {data_struct.vib_status}')
            print(f'Proc Time: {data_struct.proc_time}')
            print(f'DC Value: {data_struct.dc_value}')
            print(f'Temperature: {temperature}')
            print(f'Humidity: {humidity}')

        else:
            print(f'{date_time}|{data_struct.device_status}|{data_struct.vib_status}|\
            {data_struct.proc_time}|{data_struct.dc_value}|\
            {data_struct.temperature}|{data_struct.humidity}')


def main():
    print_debug = True
    command_line = True # Change to False to print output values as x|x|x|x
    get_device = False # can be True or False
    
    address = "C8:2E:5E:F8:9D:EA" # copy the device address here

    p2_measurements = Struct(
            "command" / Int8ul,
            "total_msg_size" / Int8ul,
            "measurement" / Int16ul,
            "avg_day_measurement" / Int16ul,
            "avg_2_day_measurement" / Int16ul,
            "avg_week_measurement" / Int16ul,
            "avg_month_measurement" / Int16ul,
            "value_peak" / Int16ul,
            "pulse_count" / Int16ul,
            "pulse_count_10m" / Int16ul,
    )

    p2_info = Struct(
            "command" / Int8ul,
            "total_msg_size" / Int8ul,
            "device_status" / Int8ul,
            "vib_status" / Int8ul,
            "proc_time" / Int32ul,
            "dc_value" / Int32ul,
            "temp_and_hum" / Int16ul
    )

    now = datetime.now()
 
    if get_device:
        async def run():
            devices = await discover()
            print("[+] Running scan")
            print("Address: Description")
            for d in devices:
                print(d)

        loop = asyncio.get_event_loop()
        loop.run_until_complete(run())
        print("[*] Copy your device's address (e.g.named FR:R20..) and set it in the variable address.")
        print("[!] Please accept liability. By changing the flag and executing this script you accept full responsilibity of what might happpen to your device.")
        print("[!] Don't forget to set, get_device = False ")
        print("[!] EOF ")

        exit(1)

    if address == '':
        print("[!] Device address not set. Try scanning using get_device = True ")
        exit(-1)

    LBS_UUID_CONTROL = "00001524-1212-EFDE-1523-785FEABCD123"
    READOUT_UUID = "00001525-1212-EFDE-1523-785FEABCD123"
    if command_line : print("** Radon Eye+2 measurement tracking. **")
    async def run(address):
        try:
            async with BleakClient(address) as client:
                try:
                    if (not client.is_connected):
                        await client.connect()
                    if command_line : print(f'Connected to {address}')

                    #Get Measurements
                    value_to_send = bytearray([0x50]) # send query command
                    if print_debug: print(f'Send: {value_to_send.hex()}')
                    await client.write_gatt_char(LBS_UUID_CONTROL, value_to_send)
                    result = await client.read_gatt_char(READOUT_UUID)
                    if print_debug: print(f'Result: {result.hex()}')
                    p2_measurements_parsed = p2_measurements.parse(result)

                    #Get Info
                    value_to_send = bytearray([0x51]) # send query command
                    if print_debug: print(f'Send: {value_to_send.hex()}')
                    await client.write_gatt_char(LBS_UUID_CONTROL, value_to_send)
                    result = await client.read_gatt_char(READOUT_UUID)
                    if print_debug: print(f'Result: {result.hex()}')
                    p2_info_parsed = p2_info.parse(result)
                    
                    date_time = now.strftime("%Y/%m/%d, %H:%M:%S")
                    print_result(command_line, date_time, p2_measurements_parsed)
                    print_result(command_line, date_time, p2_info_parsed)
                finally:
                    await client.disconnect()
        except Exception as e:
            print(f"[-] Failed to connect to {address}. Exception: {e}")
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run(address))


if __name__ == "__main__":
    main()