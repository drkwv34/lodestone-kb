# SPDX-License-Identifier: Apache-2.0
import pytest

from lodestone.chunking.window import WINDOW_OVERLAP, WINDOW_TOKENS, chunk
from lodestone.tokenize import tokenize


def test_fr_073_window_overlap_512_64() -> None:
    text = " ".join(f"tok{index:03d}" for index in range(600))
    windows = chunk(text)
    assert WINDOW_TOKENS == 512
    assert WINDOW_OVERLAP == 64
    assert len(windows) == 2
    first = tokenize(windows[0].text)
    second = tokenize(windows[1].text)
    assert len(first) == 512
    assert first[:8] == [f"tok{index:03d}" for index in range(8)]
    assert first[-64:] == second[:64]
    assert first[-64:] == [f"tok{index:03d}" for index in range(448, 512)]
    assert chunk("") == []
    assert chunk("one")[0].text.strip() != ""
    with pytest.raises(ValueError, match="size"):
        chunk("alpha", size=0)
    with pytest.raises(ValueError, match="overlap"):
        chunk("alpha", size=8, overlap=8)
