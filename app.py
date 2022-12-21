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
from datetime import date
from logzero import (
    logger,
    setup_logger,
)
from pynetdicom import AE, evt
from pydicom.dataset import Dataset
from pydicom.valuerep import DA, TM
from pynetdicom.sop_class import (
    Verification,
    ModalityWorklistInformationFind,
    # TODO: ModalityPerformedProcedureStep
)

CONFIG_PATH = "config.json"
config = dict()

appointment_worklist_map = {
        "name": "", # "ScheduledProcedureStepID", # ?
        "status": "", # "ScheduledProcedureStepStatus", # ?
        "patient": "PatientID",
        "patient_name": "PatientName",
        "appointment_date": "ScheduledStudyStartDate",
        "appointment_time": "ScheduledStudyStartTime",
        "procedure_template": "ScheduledProcedureStepID",
        "practitioner_name": "ScheduledPerformingPhysicianName",
        "referring_practitioner": "RequestingPhysician",
        "service_unit": "Modality",
        "": "ScheduledStationAETitle",
        "": "ScheduledProcedureStepLocation",
        "": "ScheduledProcedureStepDescription",
        "": "PreMedication",
}


def handle_echo(event):
    """
        Handle a C-ECHO request event.
        https://pydicom.github.io/pynetdicom/stable/reference/generated/pynetdicom._handlers.doc_handle_echo.html
    """

    logger.info(f"C-ECHO: {vars(event)}")
    return 0x0000 # Success


def handle_find(event):
    """
        Handle a C-FIND request event.
        https://pydicom.github.io/pynetdicom/stable/reference/generated/pynetdicom._handlers.doc_handle_find.html
    """

    logger.info(f"C-FIND: {vars(event)}")

    ds = event.identifier
    if "QueryRetrieveLevel" not in ds:
        logger.info(f"QueryRetrieveLevel not in dataset")
        # yield 0xC000, None
        # return

    try:
        filters = get_filters(ds)
    except NotImplementedError as e:
        # Unable to process # TODO: or just fail?
        logger.info(f"QueryRetrieveLevel not matching 'PATIENT'")
        # yield 0xC000, None
        # return

    worklist = get_appointments(filters)

    logger.info(f"Sending {len(worklist)} worklist items")

    for workitem in worklist:

        # Check if C-CANCEL has been received
        if event.is_cancelled:
            logger.info(f"Event Cancelled {vars(event)}")
            yield (0xFE00, None) # Matching terminated due to Cancel request
            return

        identifier = Dataset()
        setattr(identifier, "QueryRetrieveLevel", ds.get("QueryRetrieveLevel", "PATIENT"))

        for field, dicom_tag in appointment_worklist_map.items():

            if workitem.get(field) and dicom_tag:
                if field == "appointment_date":
                    setattr(identifier, dicom_tag, DA.fromisoformat(workitem.get("appointment_date")).strftime("%Y%m%d"))

                elif field == "appointment_time":
                    continue
                    # FIXME: skipping appointment_time
                    # identifier[dicom_tag] = TM.fromisoformat(workitem.get("appointment_time").strftime("%H%M%S"))

                else:
                    setattr(identifier, dicom_tag, workitem.get(field))

        # TODO: validate prepared dataset?
        # https://pydicom.github.io/pydicom/dev/reference/generated/pydicom.sequence.validate_dataset.html

        # logger.info(f"Yield {vars(identifier)}")
        # Pending
        # Matches are continuing: current match is supplied and any Optional Keys were supported in the same manner as Required Keys
        yield (0xFF00, identifier)

    logger.info(f"Worklist send complete")


def get_filters(ds):

    filters = {}
    filters.update({"appointment_date": [">=", date.today().strftime("%Y/%m/%d")]})
    if ds.get('QueryRetrieveLevel') != "PATIENT":
        # raise NotImplementedError
        return filters

    if "PatientName" in ds:
        if ds.PatientName not in ["*", "", "?"]:
            filters.update({"patient_name": str(ds.PatientName)})

    if "PatientID" in ds and ds.PatientID:
        filters.update({"patient": str(ds.PatientID)})

    if "ScheduledStudyStartDate" in ds and ds.ScheduledStudyStartDate:
        filters.update({"appointment_date": DA(ds.ScheduledStudyStartDate).isoformat()})

    # FIXME
    # if "ScheduledStudyStartTime" and ds.ScheduledStudyStartTime:
    # 		print(TM(ds.ScheduledStudyStartTime).isoformat())
    # 		filters.update({"appointment_time": TM(ds.ScheduledStudyStartTime).isoformat()})

    if "RequestingPhysician" in ds and ds.RequestingPhysician:
        filters.update({"practitioner": str(ds.RequestingPhysician)})

    if "ScheduledPerformingPhysicianName" in ds and ds.ScheduledPerformingPhysicianName:
        filters.update({"practitioner": str(ds.ScheduledPerformingPhysicianName)})

    if "ScheduledStationAETitle" in ds and ds.ScheduledStationAETitle:
        filters.update({"ae_title": str(ds.ScheduledStationAETitle)})

    if "Modality" in ds and ds.Modality:
        filters.update({"service_unit": str(ds.Modality)})

    return filters


def get_appointments(filters):

    fields = [field for field in list(appointment_worklist_map.keys()) if field]
    config = get_config()
    host_name = f"{config.get('host_name')}/api/resource/Patient Appointment"

    headers = {
        "Authorization": f"token {config.get('api_key')}:{config.get('api_secret')}",
        "Accept": "application/json",
    }

    data = {
        "fields": json.dumps(fields),
        "filters": json.dumps(filters),
    }

    logger.info(f"Request URL: {host_name}\nHeaders: {headers}\nData: {data}")

    response = requests.request("GET", host_name, headers=headers, data=data)
    appointments = json.loads(response._content)

    logger.info(f"Response: {appointments}")

    if appointments and appointments.get("data"):
        return appointments.get("data")
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

    title, host, port = args.title, args.host, int(args.port)
    logger.info(f"Starting MWL SCP {title} on {host}:{port}")

    handlers = [
        (evt.EVT_C_ECHO, handle_echo),
        (evt.EVT_C_FIND, handle_find),
    ]

    global ae
    ae = AE(ae_title=title)

    # Add the supported presentation context
    ae.add_supported_context(Verification)
    ae.add_supported_context(ModalityWorklistInformationFind)

    for sc in ae.supported_contexts:
        logger.info(sc)

    # Start listening for incoming association requests
    ae.start_server((host, port), evt_handlers=handlers)


def stop_mwl_scp(signal, frame):
    """
    shuts down MWL SCP
    """
    logger.info(f"Received SIGINT, shutting down MWL SCP")

    # Wait for existing associations to finish
    while(True):
        if ae.active_associations:
            logger.info(f"{ae.active_associations} active Associations, waiting")
            time.sleep(1)
        else:
            break

    # ae.shutdown() # FIXME: this just hangs!
    sys.exit(0)


def get_config():
    if not config:
        with open(CONFIG_PATH) as f: config.update(json.load(f))

    return config


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="RIS-Bridge",
        description="Bridge to support DIMSE C-FIND and C-ECHO for modalities interacting with Frappe Health",
        epilog="Experimental, not intended for Production use"
    )

    # Required positional arguments
    parser.add_argument("title", help="AE Title for the MWL SCP, required")
    parser.add_argument("--host", dest="host", default="127.0.0.1", help="IP address of host computer, required")

    parser.add_argument("-p", "--port", dest="port", default=104, help="Port for MWL SCP to listen, default 104")

    signal.signal(signal.SIGINT, stop_mwl_scp)

    logger = setup_logger("logger", logfile="logs/mwl-scp.log", maxBytes=1000000, backupCount=10)

    args = parser.parse_args()

    start_mwl_scp(args)
