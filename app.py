import logging
import os

from pydicom.dataset import Dataset
from pynetdicom import AE, debug_logger
from pynetdicom.sop_class import ModalityWorklistInformationFind
from pydicom.uid import ExplicitVRLittleEndian


host = os.environ.get('RIS_HOST', '127.0.0.1')
port = os.environ.get('RIS_PORT', 11112)
port = os.environ.get('RIS_PORT', 8044)
ae_title = 'test'

LOGGER = logging.getLogger('pynetdicom')
LOGGER.setLevel(logging.DEBUG)

debug_logger()


ae = AE()
ae.add_requested_context(ModalityWorklistInformationFind, [ExplicitVRLittleEndian])

ds = Dataset()
ds.PatientName = '*'
ds.ScheduledProcedureStepSequence = [Dataset()]

assoc = ae.associate(host, port, ae_title=ae_title)

if assoc.is_established:
    # Use the C-FIND service to send the identifier
    responses = assoc.send_c_find(ds, ModalityWorklistInformationFind)
    for (status, identifier) in responses:
        if status:
            print('C-FIND query status: 0x{0:04x}'.format(status.Status))
        else:
            print('Connection timed out, was aborted or received invalid response')

    # Release the association
    assoc.release()
else:
    print('Association rejected, aborted or never connected')
