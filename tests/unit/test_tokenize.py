# SPDX-License-Identifier: Apache-2.0
from lodestone.tokenize import tokenize


def test_fr_030_unicode_identifier_tokenization() -> None:
    assert tokenize("ERR_MANIFEST_TIMEOUT CKPT_PREFETCH camelCase v2.1 foo-bar") == [
        "err_manifest_timeout",
        "ckpt_prefetch",
        "camelcase",
        "v2",
        "1",
        "foo-bar",
    ]
    assert tokenize("Café cafe\u0301 NAÏVE Ελληνικά 東京") == [
        "cafe",
        "cafe",
        "naive",
        "ελληνικά",
        "東京",
    ]
    assert tokenize("\x00\" : * ' ") == []
