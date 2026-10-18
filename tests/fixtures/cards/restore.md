Why does restore stall after manifest load? The restore job waits until NFS returns the file handle. Setting CKPT_PREFETCH=4 makes it complete.

See src/restore.py and the CamelCase helper RestoreLatch plus snake_case_helper.
