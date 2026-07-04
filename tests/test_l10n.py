import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from game.l10n import L10n


def test_l10n_default_english():
    L10n.set_lang("en")
    assert L10n._("title") == "SKY GUARD"
    assert L10n._("start_game") == "START GAME"
    assert L10n._("game_over") == "GAME OVER"


def test_l10n_toggle_to_chinese():
    L10n.set_lang("en")
    L10n.toggle()
    assert L10n._("title") == "天穹守卫"
    assert L10n._("start_game") == "开始游戏"
    assert L10n._("help_title") == "操作说明"


def test_l10n_back_to_english():
    L10n.set_lang("zh")
    L10n.toggle()
    assert L10n._("title") == "SKY GUARD"


def test_l10n_format():
    L10n.set_lang("en")
    assert L10n._("score", 42) == "SCORE: 42"
    assert L10n._("final_score", 100) == "FINAL SCORE: 100"
    L10n.set_lang("zh")
    assert L10n._("score", 42) == "得分：42"


def test_l10n_missing_key():
    L10n.set_lang("en")
    assert "!nonexistent!" in L10n._("nonexistent")


def test_l10n_lang_property():
    L10n.set_lang("en")
    assert L10n.lang() == "en"
    L10n.toggle()
    assert L10n.lang() == "zh"