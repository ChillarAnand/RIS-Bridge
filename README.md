RIS Bridge
-----------


Simple script to bridge RIS worklist and other information from DICOM modalities to HIS and vice versa.


Usage
------

Install requirements using `pip`.

    pip install -r requirements.txt


Start the server by running the following command

    python app.py --port 8042 ae-title

Use any client and query the server.

    python -m pynetdicom findscu host port -k QueryRetrieveLevel=PATIENT -k PatientName= -d




