RIS Bridge
-----------


Simple script to bridge RIS worklist and other information from DICOM modalities to HIS and vice versa.


MWL SCP
-------

Setup MWL SCP using Orthanc modality worklist plugin or any other indenpendent worklist server like `wlmscpfs`.


```
# install  dcmtk and run
$ wlmscpfs -d --data-files-path worklist_database 8042
```


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

    python -m pynetdicom findscu host port -k QueryRetrieveLevel=PATIENT -k PatientName= -d
