# Collected evidence storage

`profile-artifacts.tar.gz` contains all 150 collected board artifacts, including
the original perf data and expanded stack/lost-event exports. Its SHA256 is:

```text
6369d280508715b698b8b08fc9b98a97ac8d3b66c9f7aaece38f43b339c6c4e6
```

The collection receipt records individual artifact hashes. Compact summaries,
timing records, logs, provenance and self profiles are also stored directly.
Expanded `*.perf.data`, `*.stacks.txt` and `*.lost.txt` files are ignored only
in this run directory to avoid committing their large duplicate contents.
Existing local copies have been retained.

To reconstruct all collected files in this directory:

```bash
cd spacemit/reports/raw/k1-roofline-20261005-225502
sha256sum profile-artifacts.tar.gz
tar -xzf profile-artifacts.tar.gz
```

Check the archive hash above and the per-file hashes in
`collection-receipt.json` before using reconstructed evidence.
