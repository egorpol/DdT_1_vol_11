#!/usr/bin/env python3
"""Compatibility entry point; generic checker implementation lives in CAMAT.

For read-only conformance/run records plus DdT policy use validate_corpus.py.
Legacy CLI arguments, including explicit transformation flags, are retained.
"""
from camat.check_mei_consistency import Finding, MeiChecker, check_mei_files, main, write_csv

if __name__ == '__main__':
    raise SystemExit(main())
