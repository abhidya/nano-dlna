#!/usr/bin/env python3
# encoding: UTF-8

import os
import pkgutil
import sys
from xml.sax.saxutils import escape as xmlescape

if sys.version_info.major == 3:
    import urllib.request as urllibreq
else:
    import urllib2 as urllibreq

import traceback
import logging
import json

import logging
import json
import os
import pkgutil
import traceback
import urllib.request as urllibreq
import time

# Delay between retries in seconds
RETRY_DELAY = 2


def play(files_urls, device, args):
    logging.debug("Starting to play: {}".format(
        json.dumps({
            "files_urls": files_urls,
            "device": device
        })
    ))

    # Gather video and subtitle file info
    video_data = {
        "uri_video": files_urls["file_video"],
        "type_video": os.path.splitext(files_urls["file_video"])[1][1:],
    }

    if "file_subtitle" in files_urls and files_urls["file_subtitle"]:
        video_data.update({
            "uri_sub": files_urls["file_subtitle"],
            "type_sub": os.path.splitext(files_urls["file_subtitle"])[1][1:]
        })
        metadata = pkgutil.get_data(
            "nanodlna",
            "templates/metadata-video_subtitle.xml").decode("UTF-8")
        video_data["metadata"] = xmlescape(metadata.format(**video_data))
    else:
        video_data["metadata"] = ""

    logging.debug("Created video data: {}".format(json.dumps(video_data)))

    # Retry indefinitely on failure
    while True:
        try:
            # Send Play Command
            logging.debug("Setting Video URI")
            send_dlna_action(device, video_data, "SetAVTransportURI")
            logging.debug("Playing video")
            send_dlna_action(device, video_data, "Play")

            # Start looping if --loop flag is set
            if args.loop:
                logging.info("Looping video enabled")
                loop_video(device, files_urls["file_video"])

            # If everything went smoothly, break out of the loop
            break

        except Exception as e:
            logging.error("Error occurred, retrying: {}".format(traceback.format_exc()))
            time.sleep(RETRY_DELAY)


def send_dlna_action(device, data, action):
    logging.debug("Sending DLNA Action: {}".format(
        json.dumps({
            "action": action,
            "device": device,
            "data": data
        })
    ))

    action_data = pkgutil.get_data(
        "nanodlna", "templates/action-{0}.xml".format(action)).decode("UTF-8")
    if data:
        action_data = action_data.format(**data)
    action_data = action_data.encode("UTF-8")

    headers = {
        "Content-Type": "text/xml; charset=\"utf-8\"",
        "Content-Length": "{0}".format(len(action_data)),
        "Connection": "close",
        "SOAPACTION": "\"{0}#{1}\"".format(device["st"], action)
    }

    logging.debug("Sending DLNA Request: {}".format(
        json.dumps({
            "url": device["action_url"],
            "data": action_data.decode("UTF-8"),
            "headers": headers
        })
    ))

    request = urllibreq.Request(device["action_url"], action_data, headers)
    urllibreq.urlopen(request)
    logging.debug("Request sent")


import ffmpeg
import time


def get_video_duration(file_path):
    """Get the duration of the video in seconds using ffmpeg."""
    try:
        probe = ffmpeg.probe(file_path, v='error', select_streams='v:0', show_entries='stream=duration')
        duration = float(probe['streams'][0]['duration'])
        return duration
    except ffmpeg.Error as e:
        logging.error(f"Error retrieving video duration: {e}")
        return None


def loop_video(device, video_file):
    """Loop the video based on its duration."""
    while True:
        # Get the video duration in seconds
        video_duration = get_video_duration(video_file)

        if video_duration is None:
            logging.error("Could not get video duration, aborting loop.")
            break

        logging.debug(f"Video duration: {video_duration} seconds")

        # Sleep and check if the video is within 5 seconds of ending
        time.sleep(video_duration - 5)

        # Send seek command to restart video 5 seconds before the end
        logging.info("Video is about to end. Restarting...")
        seek(0, device)  # Seek to the beginning of the video

def seek(seek_target, device):
    action_data = {
        "seek_target": seek_target,
    }
    send_dlna_action(device, action_data, "Seek")


def pause(device):
    logging.debug("Pausing device: {}".format(
        json.dumps({
            "device": device
        })
    ))
    send_dlna_action(device, None, "Pause")


def stop(device):
    logging.debug("Stopping device: {}".format(
        json.dumps({
            "device": device
        })
    ))
    send_dlna_action(device, None, "Stop")
