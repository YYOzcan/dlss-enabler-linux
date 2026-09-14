"""Unit and integration tests for DLSS Enabler Linux."""

import os
import shutil
import tempfile
import unittest
from pathlib import Path

from dlss_enabler.downloader import DLSSDownloader
from dlss_enabler.i18n import I18nManager, SUPPORTED_LANGUAGES, t
from dlss_enabler.patcher import GamePatcher, MANIFEST_NAME
from dlss_enabler.quirks import get_game_quirk
from dlss_enabler.scanner import GameInfo, GameScanner


def test_i18n_multi_language_support():
    i18n = I18nManager.get_instance()
    # Ensure all 6 supported languages load and translate
    for lang, _ in SUPPORTED_LANGUAGES:
        i18n.set_language(lang)
        assert t("app_title") != ""
        assert t("btn_install") != ""
        assert t("btn_uninstall") != ""
        assert t("filter_all") != ""
        assert t("status_found", count=5) != ""


def test_game_scanner_initialization():
    with tempfile.TemporaryDirectory() as td:
        scanner = GameScanner(config_dir=Path(td))
        assert scanner.config_dir == Path(td)
        games = scanner.scan_all_games()
        assert isinstance(games, list)


def test_quirks_lookup():
    q_cp = get_game_quirk("1091500", "Cyberpunk 2077")
    assert q_cp is not None
    assert q_cp["recommended_method"] == "version"

    q_witcher = get_game_quirk("292030", "The Witcher 3: Wild Hunt")
    assert q_witcher is not None
    assert q_witcher["recommended_method"] == "d3d12"


def test_custom_game_add_and_remove():
    with tempfile.TemporaryDirectory() as td:
        scanner = GameScanner(config_dir=Path(td))

        game_dir = Path(td) / "MyCustomGame"
        game_dir.mkdir()
        fake_exe = game_dir / "game.exe"
        fake_exe.write_text("dummy")

        game = scanner.add_custom_game(game_dir, title="My Custom Game")
        assert game.title == "My Custom Game"
        assert game.launcher == "Custom"

        games = scanner.scan_custom_games()
        assert len(games) == 1
        assert games[0].title == "My Custom Game"

        scanner.remove_custom_game(game.id)
        assert len(scanner.scan_custom_games()) == 0


def test_patcher_install_and_clean_unpatch():
    with tempfile.TemporaryDirectory() as td:
        game_root = Path(td) / "GameDir"
        bin_dir = game_root / "Binaries" / "Win64"
        bin_dir.mkdir(parents=True)
        game_exe = bin_dir / "Game-Win64-Shipping.exe"
        game_exe.write_text("executable")

        # Create dummy existing original dll
        original_dll = bin_dir / "version.dll"
        original_dll.write_text("ORIGINAL_CONTENT_12345")

        game = GameInfo(
            id="test_patch_game",
            title="Test Game",
            launcher="Custom",
            install_path=str(game_root),
            executable_path=str(game_exe)
        )

        downloader = DLSSDownloader(cache_dir=Path(td) / "cache")
        patcher = GamePatcher(downloader)

        # Mock source binaries directory
        mock_bins = Path(td) / "mock_bins"
        mock_bins.mkdir()
        (mock_bins / "version.dll").write_text("PATCHED_PROXY_DLL")
        (mock_bins / "dlss-enabler-upscaler.dll").write_text("UPSCALER_DLL")
        (mock_bins / "dlssg_to_fsr3_amd_is_better.dll").write_text("FG_DLL")

        # Run patch
        result = patcher.patch_game(game, method="version", bin_dir=mock_bins)
        assert result.success is True
        assert (bin_dir / "version.dll").read_text() == "PATCHED_PROXY_DLL"
        assert (bin_dir / "version.dll.dlss_backup").read_text() == "ORIGINAL_CONTENT_12345"
        assert (bin_dir / MANIFEST_NAME).exists()

        # Run unpatch
        unpatch_success, msg = patcher.unpatch_game(game)
        assert unpatch_success is True
        assert not (bin_dir / MANIFEST_NAME).exists()
        assert not (bin_dir / "version.dll.dlss_backup").exists()
        assert (bin_dir / "version.dll").read_text() == "ORIGINAL_CONTENT_12345"
        assert not (bin_dir / "dlss-enabler-upscaler.dll").exists()
