#!/usr/bin/env python3

from __future__ import print_function
import argparse
import json
import os
import sys
import signal
import datetime
import tempfile
import time
from tqdm import tqdm  # For progress bar

from . import devices, dlna, streaming
import threading
import logging


# A new signal handler for the main thread
def signal_handler_main(sig, frame, devices):
    logging.info("Interrupt signal detected")

    for device in devices:
        logging.info(f"Sending stop command to render device {device['friendly_name']}")
        dlna.stop(device)

    logging.info("Stopping streaming server")
    streaming.stop_server()

    # sys.exit("Interrupt signal detected. Sent stop command to render device and stopped streaming.")



# This function will be executed in each thread for each device
def play_video_on_device(device_name, video_file, args):

    while(True):
        try:
            device = find_device_with_retry(args, device_name)

            if device:

                logging.info(f"Attempting to play video '{video_file}' on device '{device['friendly_name']}'")

                # Configure streaming server
                files = {"file_video": video_file}

                if args.use_subtitle:
                    subtitle_file = get_subtitle(video_file)
                    if subtitle_file:
                        files["file_subtitle"] = subtitle_file

                logging.info(f"Media files: {json.dumps(files)}")

                # Start the streaming server
                target_ip = device["hostname"]
                serve_ip = args.local_host if args.local_host else streaming.get_serve_ip(target_ip)
                files_urls = streaming.start_server(files, serve_ip)

                logging.info("Streaming server ready")

                # Play the video via DLNA protocol
                logging.info("Sending play command")
                dlna.play(files_urls, device, args)

                logging.info(f"Video '{video_file}' started playing on device '{device['friendly_name']}'")

                # Use tqdm to show progress for the video
                video_duration = dlna.get_video_duration(device)
                with tqdm(total=video_duration, desc=f"Playing {video_file}", ncols=100) as pbar:
                    for _ in range(video_duration):
                        time.sleep(1)  # Simulating each second of the video playing
                        pbar.update(1)  # Update the progress bar

                    if args.loop:
                        logging.info("Looping video in 5 seconds before it finishes")
                        time.sleep(max(0, video_duration - 5))
                        dlna.play(files_urls, device, args)

                # Wait until the video finishes
                logging.info(f"Waiting for the video '{video_file}' to finish")
                time.sleep(video_duration)
        except:
            pass


# Restarting threads function
def monitor_and_restart_threads(threads, devices_config, args):
    while True:
        for i, thread in enumerate(threads):
            # If the thread is no longer alive, restart it
            if not thread.is_alive():
                config_item = devices_config[i]
                device_name = config_item["device_name"]
                video_file = config_item["video_file"]

                logging.warning(f"Thread for {device_name} stopped. Restarting...")

                # Create and start a new thread
                new_thread = threading.Thread(target=play_video_on_device, args=(device_name, video_file, args))
                threads[i] = new_thread  # Replace the old thread with the new one
                new_thread.start()

        # Sleep before next check to avoid high CPU usage
        time.sleep(1)


def play(args):
    set_logs(args)
    logging.info("Starting to play")

    # Check if a config file is provided
    if args.config_file:
        with open(args.config_file, "r") as f:
            devices_config = json.load(f)
    else:
        sys.exit("Config file is required for batch play")

    threads = []
    devices = []  # Keep track of devices to handle them in the signal handler

    # Loop through each device and play video in a separate thread
    for config_item in devices_config:
        device_name = config_item["device_name"]
        video_file = config_item["video_file"]

        # Start a new thread to play the video
        thread = threading.Thread(target=play_video_on_device, args=(device_name, video_file, args))
        thread.daemon = True  # Optional: make threads daemonic so they exit with the main program
        threads.append(thread)
        thread.start()

    # Start monitoring thread to restart any failed threads
    monitoring_thread = threading.Thread(target=monitor_and_restart_threads, args=(threads, devices_config, args))
    monitoring_thread.daemon = True  # Runs in background
    monitoring_thread.start()

    # Set the signal handler in the main thread
    signal.signal(signal.SIGINT, lambda sig, frame: signal_handler_main(sig, frame, devices))

    # Wait for all threads to finish
    for thread in threads:
        thread.join()

    logging.info("All videos finished playing.")

def set_logs(args):
    log_filename = os.path.join(
        tempfile.mkdtemp(),
        "nanodlna-{}.log".format(
            datetime.datetime.today().strftime("%Y-%m-%d_%H-%M-%S")
        )
    )

    logging.basicConfig(
        filename=log_filename,
        filemode="w",
        level=logging.INFO,
        format="[ %(asctime)s ] %(levelname)s : %(message)s"
    )

    if args.debug_activated:
        logging.getLogger().setLevel(logging.DEBUG)

    print("nano-dlna log will be saved here: {}".format(log_filename))


def get_subtitle(file_video):
    video, extension = os.path.splitext(file_video)
    file_subtitle = "{0}.srt".format(video)

    if not os.path.exists(file_subtitle):
        return None
    return file_subtitle


def list_devices(args):
    set_logs(args)

    logging.info("Scanning devices...")
    my_devices = devices.get_devices(args.timeout, args.local_host)
    logging.info("Number of devices found: {}".format(len(my_devices)))

    for i, device in enumerate(my_devices, 1):
        print("Device {0}:\n{1}\n\n".format(i, json.dumps(device, indent=4)))


def generate_config(args):
    set_logs(args)
    logging.info("Generating configuration template...")

    # Get the list of devices
    my_devices = devices.get_devices(args.timeout, args.local_host)

    # Create a configuration template with placeholders
    config = []
    for device in my_devices:
        config.append({
            "device_name": device.get("friendly_name", "Unknown Device"),
            "hostname": device["hostname"],
            "action_url": device["action_url"],
            "video_file": ""  # Placeholder for the user to fill in
        })

    # Output config to JSON file
    config_filename = args.config_file or "dlna_device_config.json"
    with open(config_filename, "w") as config_file:
        json.dump(config, config_file, indent=4)

    print(f"Configuration template saved to {config_filename}")
    logging.info(f"Configuration template saved to {config_filename}")


def find_device(args, device_name=None):
    logging.info("Selecting device to play")

    device = None
    if device_name:
        logging.info(f"Searching for device with name: {device_name}")
        my_devices = devices.get_devices(args.timeout, args.local_host)
        device = next((d for d in my_devices if device_name.lower() in d["friendly_name"].lower()), None)
    else:
        if args.device_url:
            device = devices.register_device(args.device_url)
        else:
            my_devices = devices.get_devices(args.timeout, args.local_host)
            if len(my_devices) > 0:
                if args.device_query:
                    device = next((d for d in my_devices if args.device_query.lower() in str(d).lower()), None)
                else:
                    device = my_devices[0]
    return device


def find_device_with_retry(args, device_name=None, max_retries=99999999, sleep_interval=5):
    retries = 0
    device = None
    while retries < max_retries:
        device = find_device(args, device_name)
        if device:
            break
        retries += 1
        logging.warning(f"Device not found, retrying {retries}/{max_retries}...")
        time.sleep(sleep_interval)

    if not device:
        sys.exit("Device not found after retries")
    return device


def seek(args):
    set_logs(args)
    logging.info("Starting to seek")

    device = find_device(args)
    if not device:
        sys.exit("No devices found.")

    logging.info("Sending seek command: {}".format(args.target))
    dlna.seek(args.target, device)


def pause(args):
    set_logs(args)

    logging.info("Selecting device to pause")
    device = find_device(args)

    # Pause through DLNA protocol
    logging.info("Sending pause command")
    dlna.pause(device)


def stop(args):
    set_logs(args)

    logging.info("Selecting device to stop")
    device = find_device(args)

    # Stop through DLNA protocol
    logging.info("Sending stop command")
    dlna.stop(device)


def run():
    parser = argparse.ArgumentParser(
        description="A minimal UPnP/DLNA media streamer.")
    parser.set_defaults(func=lambda args: parser.print_help())
    parser.add_argument("-H", "--host", dest="local_host")
    parser.add_argument("-t", "--timeout", type=float, default=5)
    parser.add_argument("-b", "--debug",
                        dest="debug_activated", action="store_true")
    subparsers = parser.add_subparsers(dest="subparser_name")

    p_list = subparsers.add_parser('list')
    p_list.set_defaults(func=list_devices)

    # New generate-config command
    p_generate_config = subparsers.add_parser('generate-config')
    p_generate_config.add_argument(
        "-o", "--output", dest="config_file",
        help="Path to save the generated configuration file (default: dlna_device_config.json)"
    )
    p_generate_config.set_defaults(func=generate_config)

    p_play = subparsers.add_parser('play')
    p_play.add_argument("-c", "--config-file", required=True, help="Path to the config file for video and device information")
    p_play.add_argument("-d", "--device", dest="device_url")
    p_play.add_argument("-q", "--query-device", dest="device_query")
    p_play.add_argument("-s", "--subtitle", dest="file_subtitle")
    p_play.add_argument("-n", "--no-subtitle", dest="use_subtitle", action="store_false")
    p_play.add_argument("--loop", action="store_true", help="Loop the video 5 seconds before it finishes.")
    p_play.set_defaults(func=play)

    p_seek = subparsers.add_parser('seek')
    p_seek.add_argument("-d", "--device", dest="device_url")
    p_seek.add_argument("-q", "--query-device", dest="device_query")
    p_seek.add_argument("target", help="e.g. '00:17:25'")
    p_seek.set_defaults(func=seek)

    p_pause = subparsers.add_parser('pause')
    p_pause.add_argument("-d", "--device", dest="device_url")
    p_pause.add_argument("-q", "--query-device", dest="device_query")
    p_pause.set_defaults(func=pause)

    p_stop = subparsers.add_parser('stop')
    p_stop.add_argument("-d", "--device", dest="device_url")
    p_stop.add_argument("-q", "--query-device", dest="device_query")
    p_stop.set_defaults(func=stop)

    # Additional commands
    p_update = subparsers.add_parser('update')
    p_update.add_argument("action", choices=['add', 'remove'], help="Action to update device")
    p_update.add_argument("device_name", help="Name of the device to add or remove")
    p_update.set_defaults(func=update_device)

    args = parser.parse_args()
    args.func(args)


def update_device(args):
    # Handle device addition or removal
    logging.info(f"Starting device update with action: {args.action} for device: {args.device_name}")
    try:
        if args.action == 'add':
            add_device(args.device_name)
        elif args.action == 'remove':
            remove_device(args.device_name)
    except Exception as e:
        logging.error(f"Error updating device: {e}")
        sys.exit(1)

def add_device(device_name):
    # Implement device addition logic
    logging.info(f"Adding device with name: {device_name}")
    # Logic to add the device goes here (e.g., adding to a list, config file, etc.)

def remove_device(device_name):
    # Implement device removal logic
    logging.info(f"Removing device with name: {device_name}")
    # Logic to remove the device goes here (e.g., from a list, config file, etc.)
