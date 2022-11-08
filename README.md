RIS Bridge
============

A simple DICOM AE server to query and retrieve worklists for radiology.

This server connects to Frappe Health & provides a simple interface to query and retrieve worklists for radiology.

Usage
======

Running Server
----------------

Install requirements using `pip`.

    pip install -r requirements.txt


Start the server by running the following command

    python app.py --host 0.0.0.0 --port 8042 ae-title


Querying Worklists
---------------------

Use `findscu` to query the worklists.

    # get worklists for a patient
    $ python -m pynetdicom findscu host port -k QueryRetrieveLevel=PATIENT -k PatientName='*'

    # get worklists for a specific date
    $ python -m pynetdicom findscu host port -k QueryRetrieveLevel=PATIENT -k ScheduledStudyStartDate=20210712


mwl.py
--------

This script will generate `*.wl` files directly from FH appointments data. This will be useful if you want to use `wlmscpfs` to serve worklists.

    $ python mwl.py