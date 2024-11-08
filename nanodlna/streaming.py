#!/usr/bin/env python3
# encoding: UTF-8

import os
import socket
import threading
import unicodedata
import re

import twisted.internet.error
from twisted.internet import reactor
from twisted.web.resource import Resource
from twisted.web.server import Site
from twisted.web.static import File

import logging
import json

# from twisted.python import log


def normalize_file_name(value):
    value = unicodedata\
        .normalize("NFKD", value)\
        .encode("ascii", "ignore")\
        .decode("ascii")
    value = re.sub(r"[^\.\w\s-]", "", value.lower())
    value = re.sub(r"[-\s]+", "-", value).strip("-_")
    return value


def set_files(files, serve_ip, serve_port):

    logging.debug("Setting streaming files: {}".format(
        json.dumps({
            "files": files,
            "serve_ip": serve_ip,
            "serve_port": serve_port
        })
    ))

    files_index = {file_key: (normalize_file_name(os.path.basename(file_path)),
                              os.path.abspath(file_path),
                              os.path.dirname(os.path.abspath(file_path)))
                   for file_key, file_path in files.items()}

    files_serve = {file_name: file_path
                   for file_name, file_path, file_dir in files_index.values()}

    files_urls = {
        file_key: "http://{0}:{1}/{2}/{3}".format(
            serve_ip, serve_port, file_key, file_name)
        for file_key, (file_name, file_path, file_dir)
        in files_index.items()}

    logging.debug("Streaming files information: {}".format(
        json.dumps({
            "files_index": files_index,
            "files_serve": files_serve,
            "files_urls": files_urls
        })
    ))

    return files_index, files_serve, files_urls

from twisted.web.static import File
from twisted.web.server import Site
from twisted.internet import reactor
import logging
import time

def start_server(files, serve_ip, serve_port=9000, min_port=8000):
    """Starts an HTTP server to serve the media files on available ports."""

    # Attempt to create streaming server starting from the given port
    while serve_port >= min_port:
        try:
            logging.debug("Starting to create streaming server")

            files_index, files_serve, files_urls = set_files(files, serve_ip, serve_port)

            logging.debug("Adding files to HTTP server")
            root = Resource()  # Make sure you have the correct Resource class (usually twisted.web.resource.Resource)
            for file_key, (file_name, file_path, file_dir) in files_index.items():
                root.putChild(file_key.encode("utf-8"), Resource())
                root.children[file_key.encode("utf-8")].putChild(
                    file_name.encode("utf-8"), File(file_path))  # Serve the file via the 'File' class

            logging.debug("Starting to listen for messages in HTTP server")
            reactor.listenTCP(serve_port, Site(root))
            threading.Thread(
                target=reactor.run, kwargs={"installSignalHandlers": False}).start()

            return files_urls

        except twisted.internet.error.CannotListenError as e:
            logging.error(f"Cannot listen on port {serve_port}: {e}")
            # Decrease the port and try again
            serve_port -= 1
            logging.info(f"Trying next port: {serve_port}")
            time.sleep(1)  # Sleep a bit before trying again

    # If we exhausted all ports, raise an error
    logging.error(f"Unable to bind to any port between {min_port} and 9000")
    raise Exception("No available ports to start the server.")

def stop_server():
    reactor.stop()


def get_serve_ip(target_ip, target_port=80):
    logging.debug("Identifying server IP")
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect((target_ip, target_port))
    serve_ip = s.getsockname()[0]
    s.close()
    logging.debug("Server IP identified: {}".format(serve_ip))
    return serve_ip


if __name__ == "__main__":

    import sys

    files = {"file_{0}".format(i): file_path for i,
             file_path in enumerate(sys.argv[1:], 1)}
    print(files)

    files_urls = start_server(files, "localhost")
    print(files_urls)
