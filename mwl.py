"""
Generate MWL files from FH patient appointments.
"""
import json
import os

import requests
from pydicom import Dataset
from pydicom.dataset import FileMetaDataset
from pydicom.uid import ExplicitVRLittleEndian


os.makedirs('mwl', exist_ok=True)


def get_appointments(filters):
    fields = ["name", "patient", "appointment_date", "status"]
    url = f"{HOST}/api/resource/Patient Appointment"

    headers = {
        'Authorization': f"token {API_KEY}:{API_SECRET}",
        'Accept': 'application/json',
    }

    data = {
        'fields': json.dumps(fields),
        'filters': json.dumps(filters),
    }

    response = requests.request("GET", url, headers=headers, data=data)
    appointments = json.loads(response._content)

    if appointments and appointments.get('data'):
        return appointments.get('data')
    else:
        return []


print(get_appointments(filters={}))


def generate_mwl(appointment):
    wl_file_name = f"mwl/{appointment['name']}.wl"

    # Create data set
    ds = Dataset()
    # Add file meta information elements
    ds.file_meta = FileMetaDataset()
    ds.file_meta.TransferSyntaxUID = ExplicitVRLittleEndian
    ds.file_meta.MediaStorageSOPClassUID = "0"
    ds.file_meta.MediaStorageSOPInstanceUID = "0"

    # Fill out the worklist query elements
    ds.SpecificCharacterSet = "ISO_IR 6"
    ds.InstanceCreationDate = "20220101"
    ds.AccessionNumber = "12345-abc"
    ds.PatientName = "SURNAME^NAME"
    ds.PatientID = "123456"
    ds.PatientBirthDate = "19700101"
    ds.PatientSex = "M"
    ds.StudyInstanceUID = "1a-2b-3c"
    ds.RequestedProcedureDescription = "ProcedureDescription"
    ds.ScheduledProcedureStepSequence = [Dataset()]
    ds.ScheduledProcedureStepSequence[0].Modality = "OT"
    ds.ScheduledProcedureStepSequence[0].ScheduledStationAETitle = "OT"
    ds.ScheduledProcedureStepSequence[0].ScheduledProcedureStepStartDate = "20220101"
    ds.ScheduledProcedureStepSequence[0].ScheduledProcedureStepStartTime = "080000"
    ds.ScheduledProcedureStepSequence[0].ScheduledPerformingPhysicianName = "Doctor Emmet Brown"
    ds.ScheduledProcedureStepSequence[0].ScheduledProcedureStepDescription = "SchedProcStepDesc"
    ds.ScheduledProcedureStepID = "0001"
    # more stuff if you need

    # Save directly as a .wl file.
    # Set write_like_original=False to be certain you’re writing the dataset in the DICOM File Format
    ds.save_as(wl_file_name, write_like_original=False)


for appointment in get_appointments(filters={}):
    generate_mwl(appointment)
