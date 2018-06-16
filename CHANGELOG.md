# Changelog

## [2.6]
### Added
- scan-object2-v2 added - it's a simplified version of scan-objects that allows you to reset permissions back to private and also supports --versions
- restore option was changed. Added --permanent-restore and --storage-class.

## [2.3]
### Fixed
- bug fixes - small changes in error handling for scan-bucket
- renamed some functions because the old name was weird

## [2.2]
### Fixed
- bug fixes for scan-bucket when the bucket ACL has a restrictive policy

## [2.1]
### Added
- find-unencrypted option added. You can scan for keys without encryption

## [2.0]
### Changed
- purge option - different confirmation method implemented (avoid unwanted deletions)
- more changes to support p3 smoothly

## [1.9]
### added
- started the changes for python3 support

## [1.8]
### changed
- fixed errors with sqs name (replace . to _ )

## [1.6]
### Added | changed
- replaced some misleading messages in the --purge command
- added tail function (preview)

## [1.5]
- Merged with 1.6

## [1.4]
### Added | changed
- replaced scanperms to scan-objects and scan-bucket
- formatted output of scan-objects to be in a table-like format
