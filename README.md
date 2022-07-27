RIS Bridge
-----------


Simple script to bridge RIS worklist and other information from DICOM modalities to HIS and vice versa.


Usage
------

Ensure you are able to access RIS using telnet or any other dicom utiliets.

Install requirements and run the following command.

    python app.py


RIS Troubleshooting
-------------------

Ensure host/port is up by running the following command

    telnet host port


Ensure SCP is available by running the following command

    python -m pynetdicom echoscu host port
