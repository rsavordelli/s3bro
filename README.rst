.. image:: https://img.shields.io/badge/License-MIT-yellow.svg
    :target: https://raw.githubusercontent.com/rsavordelli/s3bro/master/LICENSE

=============================
# s3bro! A handy s3 cli tool
=============================
============
Overview
============
It's your s3 friend (bro). You’ll often find yourself having to run complex CLI/AWS commands in order to execute tasks against S3.  Let's say you need to restore all your keys from S3 Glacier storage class, if you’ve attempted this task, you’ve probably come to the realization, that the AWS CLI does not allow for an easy manner to execute this in “batch”.

Subsequently, you would need to make use of a combination of AWS CLI commands and pipe it to additional commands in order to obtain your desired result. In addition to this complexity, it would restore key by key, very slowly.

S3bro, however, offers you a solution to the above problem and others common situations where you have to run complex s3 commands, by utilizing multiprocessing/threading. This means that you can expedite tasks a lot faster than using the normal method. Oh, did I mention… in a much more elegant way. This is a python cli that will abstract a big portion of the work for you.

Why would you run the two following commands to wipe your bucket:

>>>
aws s3api list-object-versions --bucket rsavordelli --output json --query
    'Versions\[\].\[Key, VersionId\]' | jq -r '.\[\] | "--key '\\''" + .\[0\] + "'\\''
         --version-id " + .\[1\]' |  xargs -L1 aws s3api delete-object --bucket rsavordelli
aws s3api list-object-versions --bucket rsavordelli --output json --query
     'DeleteMarkers\[\].\[Key, VersionId\]' | jq -r '.\[\] | "--key '\\''" + .\[0\] + "'\\''
         --version-id " + .\[1\]' |  xargs -L1 aws s3api delete-object --bucket rsavordelli

if you can run this?

>>>
s3bro purge --bucket rsavordelli


what if you need to restore all your keys from glacier storage class? Or just some of them?

>>>
➜  ~ s3bro restore --bucket yourBucket --prefix glacier --days 10 --type Expedited --exclude .html --workers 10
Initiating Expedited restore for yourBucket/glacier...
Restoring keys for 10 days
Versions: False
===========================
Restoration completed: glacier/River Flows In You - A Love Note (CM Remix).mp3 until "Sat, 03 Mar 2018 00:00:00 GMT"
Submitting restoration request: glacier/asd.js
Restoration completed: glacier/Yiruma - River Flows In You (English Version).mp3 until "Sat, 03 Mar 2018 00:00:00 GMT"
Restoration completed: glacier/River Flows In You- Lindsey Stirling.mp3 until "Sat, 03 Mar 2018 00:00:00 GMT"
Restoration completed: glacier/River Flows In You - A Love Note (Ryan Wong Remix).mp3 until "Sat, 03 Mar 2018 00:00:00 GMT"
Restoration completed: glacier/ until "Sat, 03 Mar 2018 00:00:00 GMT"
Restoration completed: glacier/Endless Love {Piano Version} | Beautiful Piano.mp3 until "Sat, 03 Mar 2018 00:00:00 GMT"
Total keys proccessed: 7 in 5.44s

============
Installation
============
   ``pip install s3bro -U``

***********
From source
***********
    ``git clone https://github.com/rsavordelli/s3bro ; cd s3bro``

    ``pip install -e .``


Note: For python3 you may have some issues due the unicode handling that has changed in Python3. The solution to these problems is different depending on which locale your computer is running in.
Generally "export LANG=en_US.utf-8" solves (put your LANG). More infos: http://click.pocoo.org/5/python3/

******************
Available Commands
******************
- restore_
- purge_
- scan-bucket_
- scan-objects_
- scan-objects-v2_
- tail_
- find-unencrypted_


============
Examples
============

.. code::

    # s3bro restore --help
    # s3bro restore --bucket bucketName --prefix myglacierPrefix --days 20 --type Bulk
    # s3bro restore --bucket bucketName --prefix myglacierPrefix --days 20 --type Standard --include .css --versions
    # s3bro restore --bucket bucketName --prefix myglacierPrefix --days 20 --type Expedited --permanent-restore --storage-class ONEZONE_IA
    # s3bro restore -b bucketName -p 123 --days 2 --type Expedited --permanent-restore --restore-to-bucket DestbucketName --storage-class ONEZONE_IA
    # s3bro purge --bucket bucketName
    # s3bro scan-objects --bucket bucketName
    # s3bro scan-objects-v2 --bucket bucketName --make-private
    # s3bro scan-bucket --all
    # s3bro tail --bucket bucketName --timeout 1

============
Commands
============
***************
restore
***************
 Restore S3 keys in Glacier Storage class

Restore Options
------------------
>>>
Usage: s3bro restore [OPTIONS] [RESTORE]...
  restore S3 objects from Glacier Storage Class
Options:
  -b, --bucket TEXT               bucket name  [required]
  -p, --prefix TEXT               prefix
  -d, --days INTEGER              Days to keep the restore  [required]
  -t, --type [Standard|Expedited|Bulk]
                                  restore type (Tier)  [required]
  -v, --versions / --no-versions  [--no-versions is DEFAULT] - this option
                                  will make the restore to include all
                                  versions excluding delete markers
  -pr, --permanent-restore        Move keys ALREADY restored from Glacier back
                                  to a storage class of your choice
  -rtb, --restore-to-bucket TEXT  Copy keys ALREADY restored to a different
                                  bucket. It can only be used in combination
                                  with --permanent-restore
  --storage-class [STANDARD|STANDARD_IA|ONEZONE_IA]
                                  The StorageClass type to use with
                                  --permanent-restore [default is STANDARD]
  -urd, --update-restore-date / --do-not-update-restore-date
                                  If passed, it will change the restore date
                                  for already restored key
  -in, --include TEXT             Only restore keys that matches with a given
                                  string, you can add multiples times by
                                  passing --include multiple times
  -ex, --exclude TEXT             Do not restore if key name matches with a
                                  given pattern,you can add multiple patterns
                                  by inputting
  --workers INTEGER               How many helpers to include in task, default
                                  is 10
  --log-level [INFO|ERROR|DEBUG|WARNING]
                                  logging type
  --help                          Show this message and exit.

Restore Details
^^^^^^^^^^^^^^^^^^

the option --log-level can be useful to debug errors/behaviors.

>>>
DEBUG - similar to boto3 debug level with additional information
WARNING - will print some threading information and Keys excluded during the iteration (exclude, include, storage-class, delete-marker, etc)

* the option --workers allows you to specify how many workers will consume the list. Calculate max 5 workers per core
* the option --update-restore-date can be used to "extend" a key that is already restored. It will send a new "expiry" date to the object
* the option --permanent-restore will copy the data from glacier back to a storage class of your Choice (combine this with --storage-class)

***************
purge
***************
 Delete all keys in the bucket - as simple as that. It will delete versions, delete markers. Everything

Purge Options
------------------

>>>
Usage: s3bro purge [OPTIONS] [PURGE]...
  delete all the bucket content
Options:
  -b, --bucket TEXT               Bucket name  [required]
  -p, --prefix TEXT               prefix name - optional
  --yes                           first confirmation
  --log-level [INFO|ERROR|DEBUG|WARNING]
                                  logging type
  --help                          Show this message and exit.


Purge Details
^^^^^^^^^^^^^^^^^^

* The script has two confirmations. The first can be by-passed with --yes. The second one ask you to confirm the bucket name.
* The second confirmation can be avoided if you create a Tag in the Bucket with Key: s3bro_delete and Value: yes . That will by pass the bucket name confirmation.

***************
scan-bucket
***************
 scan bucket ACLs

Scan-Bucket Options
---------------------
>>>
Usage: s3bro scan-bucket [OPTIONS] [SCAN_BUCKET]...
  scan bucket ACLs
Options:
  -b, --bucket TEXT               Bucket name
  -A, --all                       Scan permissions for all your buckets (don't
                                  combine -b with -A)
  --log-level [INFO|ERROR|DEBUG|WARNING]
                                  logging type
  --help                          Show this message and exit.

***************
scan-objects
***************
 scan object ACLs

Scan-Object Options
---------------------

>>>
Usage: s3bro scan-objects [OPTIONS] [SCAN_OBJECTS]...
  scan object ACLs
Options:
  -b, --bucket TEXT               Bucket name  [required]
  -p, --prefix TEXT               prefix name - optional
  --workers INTEGER               How many helpers to include in task, default
                                  is 10
  --log-level [INFO|ERROR|DEBUG|WARNING]
                                  logging type
  --help                          Show this message and exit.

Scan-Object Details
^^^^^^^^^^^^^^^^^^^^
* scan-objects only scan current versions of your objects

***************
scan-objects-v2
***************
  scan-objects-v2 is a simplified version of scan-objects and introduce new features like --make-private (make public keys, private).
  It's focused on looking only for Public Keys (Everyone's access), it will not print permission to another aws accounts.

Scan-Object-V2 Options
-----------------------

>>>
Usage: s3bro scan-objects-v2 [OPTIONS] [SCAN_OBJECTS_V2]...
  scan object ACLs (V2) - The V2 only look for Everyone permissios, while
  the scan-objects will look for all ACLs - The V2 is capable to reset ACLs
  back to private (Everyone)
Options:
  -b, --bucket TEXT               Bucket name  [required]
  -p, --prefix TEXT               prefix name - optional
  -mp, --make-private             Make all keys with public ACL private
  -v, --versions / --no-versions  [--no-versions is DEFAULT] - this option
                                  will make the restore to include all
                                  versions excluding delete markers
  --workers INTEGER               How many helpers to include in task, default
                                  is 10
  --log-level [INFO|ERROR|DEBUG|WARNING]
                                  logging type
  --help                          Show this message and exit.

Scan-Object-V2 Details
^^^^^^^^^^^^^^^^^^^^^^^
* scan-objects support versions
* --make-private put a private acl in the object 


***************
tail
***************
 s3 logs in "real-time" through S3 Events (for puts and deletes only)

Options
------------------
>>>
Usage: s3bro tail [OPTIONS] [TAIL]...
  tail is an S3 real-time logging tool. It makes use of S3 events (for puts and deletes only)
Options:
  -b, --bucket TEXT      Bucket name  [required]
  -t, --timeout INTEGER  How much time (in minutes) to run, it will destroy
                         the resources created after this time  [required]
  --help                 Show this message and exit.

Details
^^^^^^^^^^^^^^^^^^
Basically what it does is:

1. Create an SQS
2. Create an S3 Event notification
3. Connect to the queue and keep retrieving the messages until the timeout time is reached.
4. Delete the resources created

>>> --timeout is in minutes
>>> it only works for PUTs and Deletes (s3 events does not support GET requests)

*****************
find-unencrypted
*****************
 find unencrypted keys in a bucket

Find-Unencrypted Options
-------------------------

>>>
Usage: s3bro find-unencrypted [OPTIONS] [FIND_UNENCRYPTED]...
  find unencrypted keys in a bucket (ServerSideEncryption)
Options:
  -b, --bucket TEXT               Bucket name  [required]
  -p, --prefix TEXT               prefix name - optional
  -v, --versions / --no-versions  [--no-versions is DEFAULT] - this option
                                  will make the restore to include all
                                  versions excluding delete markers
  --workers INTEGER               How many helpers to include in task, default
                                  is 10
  --log-level [INFO|ERROR|DEBUG|WARNING]
                                  logging type
  --help                          Show this message and exit.

Find-Unencrypted Details
^^^^^^^^^^^^^^^^^^^^^^^^^

* it only print details for unencrypted keys. If you to check all the keys encryption status, run --log-level WARNING
