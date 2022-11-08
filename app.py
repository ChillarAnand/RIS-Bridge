#!/usr/bin/env python3
"""
Module Docstring
"""

__author__ = "earthians"
__version__ = "0.1.0"
__license__ = "MIT"

# https://www.python-boilerplate.com/

import argparse
import json
import requests
import signal
import sys
import time
from logzero import logger
from pynetdicom import AE, evt
from pydicom.dataset import Dataset
from pynetdicom.sop_class import (
    Verification,
    ModalityWorklistInformationFind,
    PatientRootQueryRetrieveInformationModelFind,
    # TODO: ModalityPerformedProcedureStep
)

CONFIG_PATH = r'config.json'
config = dict()  # cache
debug = False


def handle_echo(event):
    """
        Handle a C-ECHO request event.
        https://pydicom.github.io/pynetdicom/stable/reference/generated/pynetdicom._handlers.doc_handle_echo.html
    """

    if debug:
        logger.info(f"C-ECHO: {vars(event)}")

    return 0x0000  # Success


def handle_find(event):
    """
    Handle a C-FIND request event.
    https://pydicom.github.io/pynetdicom/stable/reference/generated/pynetdicom._handlers.doc_handle_find.html
    """
    if debug:
        logger.info(f"C-FIND: {vars(event)}")

    ds = event.identifier

    if 'QueryRetrieveLevel' not in ds:
        # Failure
        if debug:
            logger.debug("QueryRetrieveLevel not in ds")
        yield 0xC000, None
        return

    filters = {}

    if ds.QueryRetrieveLevel == 'PATIENT':
        if 'PatientName' in ds:
            if ds.PatientName not in ['*', '', '?']:
                filters.update({'patient': str(ds.PatientName)})
                if debug:
                    logger.info(f"ds.PatientName not in ['*', '', '?']")

        # TODO: Build further filters

        worklist = get_appointments(filters)

    else:
        # Unable to process # TODO: or just fail?
        yield 0xC000, None
        return

    for workitem in worklist:
        # Check if C-CANCEL has been received
        if event.is_cancelled:
            if debug:
                logger.info(f"Event Cancelled {vars(event)}")

            yield (0xFE00, None)  # Matching terminated due to Cancel request
            return

        identifier = Dataset()
        identifier.QueryRetrieveLevel = ds.QueryRetrieveLevel
        identifier.PatientName = workitem.get('patient')

        if debug:
            logger.info(f"Yeilding {vars(identifier)}")
        # Pending
        # Matches are continuing: current match is supplied and any Optional Keys were supported in the same manner as Required Keys
        yield (0xFF00, identifier)


def get_appointments(filters):
    fields = ["name", "status"]
    config = get_config()
    url = f"{config.get('url')}/api/resource/Patient Appointment"

    headers = {
        'Authorization': f"token {config.get('api_key')}:{config.get('api_secret')}",
        'Accept': 'application/json',
    }

    data = {
        'fields': json.dumps(fields),
        'filters': json.dumps(filters),
    }

    if debug:
        logger.info(f"Request URL: {url}\nHeaders: {headers}\nData: {data}")

    response = requests.request("GET", url, headers=headers, data=data)
    appointments = json.loads(response._content)

    if debug:
        logger.info(f"Response: {appointments}")

    if appointments and appointments.get('data'):
        return appointments.get('data')
    else:
        return []


def start_mwl_scp(args):
    """
    Start MWL SCP, also supports Verification
    args {
        title: "AE_TITLE",
        port: 104,
    }
    https://pydicom.github.io/pynetdicom/stable/reference/generated/pynetdicom.ae.ApplicationEntity.html
    """

    title, port = args.title, int(args.port)
    logger.info(f"Starting MWL SCP {title} on {port}")

    handlers = [
        (evt.EVT_C_ECHO, handle_echo),
        (evt.EVT_C_FIND, handle_find),
    ]

    global ae
    ae = AE(ae_title=title)

    # Add the supported presentation context
    ae.add_supported_context(Verification)
    ae.add_supported_context(ModalityWorklistInformationFind)
    ae.add_supported_context(PatientRootQueryRetrieveInformationModelFind)

    if debug:
        for sc in ae.supported_contexts:
            logger.info(sc)

    # Start listening for incoming association requests
    ae.start_server(("127.0.0.1", port), evt_handlers=handlers)


def stop_mwl_scp(signal, frame):
    """
    shuts down MWL SCP
    """
    logger.info(f"Received SIGINT, shutting down MWL SCP")

    # Wait for existing associations to finish
    while (True):
        if ae.active_associations:
            if debug:
                logger.info(f"{ae.active_associations} ative Associations, waiting")
            time.sleep(1)
        else:
            break

    # ae.shutdown() # FIXME: this just hangs!
    sys.exit(0)


def get_config():
    if config:
        return config
    else:
        with open(CONFIG_PATH) as f:
            config.update(json.load(f))
    return config


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="mwl_scp",
        description="Adapter to support DIMSE C-FIND and C-ECHO for modalities interacting with Frappe Health",
        epilog="Experimental, not intended for Production use"
    )

    # Required positional arguments
    parser.add_argument("title", help="AE Title for the MWL SCP, required")
    parser.add_argument("-p", "--port", dest="port", default=104, help="Port for MWL SCP to listen, default 104")

    parser.add_argument(  # TODO: handle verbosity
        "-d",
        "--debug",
        action="store_true",
        help="Log debug information")

    signal.signal(signal.SIGINT, stop_mwl_scp)

    args = parser.parse_args()
    debug = True if args.debug else False

    start_mwl_scp(args)
