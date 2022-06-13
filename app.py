import os

from pydicom.dataset import Dataset

from pynetdicom import AE, debug_logger
from pynetdicom.sop_class import PatientRootQueryRetrieveInformationModelFind

host = os.environ.get('RIS_HOST', '127.0.0.1')
port = os.environ.get('RIS_PORT', 11112)


debug_logger()

ae = AE()
ae.add_requested_context(PatientRootQueryRetrieveInformationModelFind)

ds = Dataset()
ds.PatientName = 'John'
ds.QueryRetrieveLevel = 'PATIENT'

assoc = ae.associate(host, port)

if assoc.is_established:
    responses = assoc.send_c_find(ds, PatientRootQueryRetrieveInformationModelFind)
    for (status, identifier) in responses:
        if status:
            print('C-FIND query status: 0x{0:04X}'.format(status.Status))
        else:
            print('Connection timed out, was aborted or received invalid response')
    assoc.release()
else:
    print('Association rejected, aborted or never connected')
