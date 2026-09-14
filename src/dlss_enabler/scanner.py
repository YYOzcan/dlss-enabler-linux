"""Game Scanner Engine for Linux.
Discovers installed games across Steam (Native, Flatpak, Snap), Heroic Games Launcher,
Lutris, Bottles, and Custom Directories.
"""

from __future__ import annotations

import glob
import json
import os
import re
import sqlite3
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import List, Optional

from .quirks import get_game_quirk

BAD_EXE_SUBSTRINGS = [
    "unins", "setup", "installer", "update", "crash", "report", "bug", "diagnostic",
    "eac", "easyanticheat", "battleye", "redlauncher", "launcher", "benchmark",
    "touchup", "cleanup", "directx", "vcredist", "dotnet", "patcher", "config",
    "settings", "tool", "server", "dedicated", "helper", "webview", "support",
    "unitycrashhandler", "prerequisites", "d3dcompiler", "gldriverquery"
]

@dataclass
class GameInfo:
    id: str  # appid or custom slug
    title: str
    launcher: str  # steam, heroic, lutris, bottles, custom
    install_path: str
    executable_path: str = ""
    is_patched: bool = False
    patch_method: str = ""
    patch_version: str = ""
    patch_time: str = ""
    has_backup: bool = False
    cover_url: str = ""
    quirk_notes: str = ""
    recommended_method: str = "version"

    def to_dict(self) -> dict:
        return asdict(self)


class GameScanner:
    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or (Path.home() / ".config" / "dlss-enabler-linux")
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.custom_games_file = self.config_dir / "custom_games.json"

    def scan_all_games(self) -> list[GameInfo]:
        """Scan all game launchers and custom folders."""
        games: list[GameInfo] = []
        seen_paths: set[str] = set()

        # 1. Steam
        for game in self.scan_steam():
            norm_path = os.path.realpath(game.install_path) if os.path.exists(game.install_path) else game.install_path
            if norm_path not in seen_paths:
                games.append(game)
                seen_paths.add(norm_path)

        # 2. Heroic
        for game in self.scan_heroic():
            norm_path = os.path.realpath(game.install_path) if os.path.exists(game.install_path) else game.install_path
            if norm_path not in seen_paths:
                games.append(game)
                seen_paths.add(norm_path)

        # 3. Lutris
        for game in self.scan_lutris():
            norm_path = os.path.realpath(game.install_path) if os.path.exists(game.install_path) else game.install_path
            if norm_path not in seen_paths:
                games.append(game)
                seen_paths.add(norm_path)

        # 4. Bottles
        for game in self.scan_bottles():
            norm_path = os.path.realpath(game.install_path) if os.path.exists(game.install_path) else game.install_path
            if norm_path not in seen_paths:
                games.append(game)
                seen_paths.add(norm_path)

        # 5. Custom Games
        for game in self.scan_custom_games():
            norm_path = os.path.realpath(game.install_path) if os.path.exists(game.install_path) else game.install_path
            if norm_path not in seen_paths:
                games.append(game)
                seen_paths.add(norm_path)

        # Sort alphabetically by title
        games.sort(key=lambda g: g.title.lower())
        return games

    # =========================================================================
    # STEAM SCANNER
    # =========================================================================
    def scan_steam(self) -> list[GameInfo]:
        games: list[GameInfo] = []
        library_paths = self._find_steam_library_folders()

        for lib in library_paths:
            steamapps = lib / "steamapps"
            if not steamapps.is_dir():
                continue

            for manifest in steamapps.glob("appmanifest_*.acf"):
                try:
                    appid = ""
                    name = ""
                    installdir = ""
                    with open(manifest, "r", encoding="utf-8", errors="replace") as f:
                        for line in f:
                            clean = line.strip()
                            if clean.startswith('"appid"'):
                                appid = line.split('"appid"', 1)[1].strip().strip('"')
                            elif clean.startswith('"name"'):
                                name = line.split('"name"', 1)[1].strip().strip('"')
                            elif clean.startswith('"installdir"'):
                                installdir = line.split('"installdir"', 1)[1].strip().strip('"')

                    if not appid or not name:
                        continue

                    # Filter out tools, runtimes, redistributables
                    lower_name = name.lower()
                    if any(x in lower_name for x in [
                        "proton", "steam linux runtime", "steamworks common redistributables",
                        "soundtrack", "server", "sdk", "redistributable"
                    ]):
                        continue

                    install_path = steamapps / "common" / installdir if installdir else Path()
                    if not install_path.exists():
                        continue

                    exe_path = self.find_best_executable(install_path, name)
                    quirk = get_game_quirk(appid, name)
                    rec_method = quirk.get("recommended_method", "version") if quirk else "version"
                    notes = quirk.get("notes", "") if quirk else ""

                    game = GameInfo(
                        id=str(appid),
                        title=name,
                        launcher="Steam",
                        install_path=str(install_path),
                        executable_path=str(exe_path) if exe_path else "",
                        cover_url=f"https://cdn.cloudflare.steamstatic.com/steam/apps/{appid}/header.jpg",
                        recommended_method=rec_method,
                        quirk_notes=notes,
                    )
                    self._check_patch_status(game)
                    games.append(game)
                except Exception:
                    continue

        return games

    def _find_steam_library_folders(self) -> set[Path]:
        candidates = [
            Path.home() / ".steam" / "steam",
            Path.home() / ".local" / "share" / "Steam",
            Path.home() / ".steam" / "root",
            Path.home() / ".var" / "app" / "com.valvesoftware.Steam" / ".local" / "share" / "Steam",
            Path.home() / ".var" / "app" / "com.valvesoftware.Steam" / ".steam" / "steam",
            Path.home() / "snap" / "steam" / "common" / ".steam" / "steam",
        ]

        found_libs: set[Path] = set()
        for base in candidates:
            if not base.exists():
                continue
            found_libs.add(base)
            vdf_file = base / "steamapps" / "libraryfolders.vdf"
            if vdf_file.exists():
                try:
                    with open(vdf_file, "r", encoding="utf-8", errors="replace") as f:
                        for line in f:
                            clean = line.strip()
                            if clean.startswith('"path"'):
                                parts = line.split('"path"', 1)
                                if len(parts) > 1:
                                    path_val = parts[1].strip().strip('"')
                                    p = Path(path_val)
                                    if p.is_dir():
                                        found_libs.add(p)
                except Exception:
                    pass

        return found_libs

    # =========================================================================
    # HEROIC GAMES LAUNCHER
    # =========================================================================
    def scan_heroic(self) -> list[GameInfo]:
        games: list[GameInfo] = []
        heroic_dirs = [
            Path.home() / ".config" / "heroic",
            Path.home() / ".var" / "app" / "com.heroicgameslauncher.hgl" / "config" / "heroic",
        ]

        for hdir in heroic_dirs:
            if not hdir.exists():
                continue

            # Legendary (Epic Games)
            legendary_installed = hdir / "legendaryConfig" / "legendary" / "installed.json"
            if legendary_installed.exists():
                try:
                    with open(legendary_installed, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        for app_name, info in data.items():
                            title = info.get("title", app_name)
                            path_str = info.get("install_path", "")
                            if path_str and os.path.exists(path_str):
                                install_path = Path(path_str)
                                exe_path = self.find_best_executable(install_path, title)
                                quirk = get_game_quirk(app_name, title)
                                game = GameInfo(
                                    id=f"heroic_epic_{app_name}",
                                    title=title,
                                    launcher="Heroic (Epic)",
                                    install_path=str(install_path),
                                    executable_path=str(exe_path) if exe_path else "",
                                    recommended_method=quirk.get("recommended_method", "version") if quirk else "version",
                                    quirk_notes=quirk.get("notes", "") if quirk else "",
                                )
                                self._check_patch_status(game)
                                games.append(game)
                except Exception:
                    pass

            # GOG installed
            gog_installed = hdir / "store_cache" / "gog_install_info.json"
            if gog_installed.exists():
                try:
                    with open(gog_installed, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        games_dict = data.get("installed", {}) if isinstance(data, dict) else {}
                        for app_name, info in games_dict.items():
                            title = info.get("name", app_name)
                            path_str = info.get("install_path", "")
                            if path_str and os.path.exists(path_str):
                                install_path = Path(path_str)
                                exe_path = self.find_best_executable(install_path, title)
                                quirk = get_game_quirk(app_name, title)
                                game = GameInfo(
                                    id=f"heroic_gog_{app_name}",
                                    title=title,
                                    launcher="Heroic (GOG)",
                                    install_path=str(install_path),
                                    executable_path=str(exe_path) if exe_path else "",
                                    recommended_method=quirk.get("recommended_method", "version") if quirk else "version",
                                    quirk_notes=quirk.get("notes", "") if quirk else "",
                                )
                                self._check_patch_status(game)
                                games.append(game)
                except Exception:
                    pass

        return games

    # =========================================================================
    # LUTRIS SCANNER
    # =========================================================================
    def scan_lutris(self) -> list[GameInfo]:
        games: list[GameInfo] = []
        db_paths = [
            Path.home() / ".local" / "share" / "lutris" / "pga.db",
            Path.home() / ".var" / "app" / "net.lutris.Lutris" / "data" / "lutris" / "pga.db",
        ]

        for db_file in db_paths:
            if not db_file.exists():
                continue
            try:
                conn = sqlite3.connect(db_file)
                cursor = conn.cursor()
                cursor.execute("SELECT id, slug, name, directory, runner, installed FROM games WHERE installed = 1")
                rows = cursor.fetchall()
                for row in rows:
                    gid, slug, name, directory, runner, installed = row
                    if not directory or not os.path.exists(directory):
                        continue
                    if runner not in ("wine", "steam", "lutris"):
                        continue
                    install_path = Path(directory)
                    exe_path = self.find_best_executable(install_path, name)
                    quirk = get_game_quirk(slug, name)
                    game = GameInfo(
                        id=f"lutris_{slug}",
                        title=name,
                        launcher="Lutris",
                        install_path=str(install_path),
                        executable_path=str(exe_path) if exe_path else "",
                        recommended_method=quirk.get("recommended_method", "version") if quirk else "version",
                        quirk_notes=quirk.get("notes", "") if quirk else "",
                    )
                    self._check_patch_status(game)
                    games.append(game)
                conn.close()
            except Exception:
                pass

        return games

    # =========================================================================
    # BOTTLES SCANNER
    # =========================================================================
    def scan_bottles(self) -> list[GameInfo]:
        games: list[GameInfo] = []
        bottle_dirs = [
            Path.home() / ".local" / "share" / "bottles" / "bottles",
            Path.home() / ".var" / "app" / "com.usebottles.bottles" / "data" / "bottles" / "bottles",
        ]

        for bdir in bottle_dirs:
            if not bdir.is_dir():
                continue
            for bottle_path in bdir.iterdir():
                if not bottle_path.is_dir():
                    continue
                cfg_file = bottle_path / "bottle.yml"
                if not cfg_file.exists():
                    continue
                drive_c = bottle_path / "drive_c"
                if not drive_c.is_dir():
                    continue
                # Search common game folders inside drive_c
                for search_dir in [drive_c / "Program Files", drive_c / "Program Files (x86)", drive_c / "Games"]:
                    if not search_dir.is_dir():
                        continue
                    for sub in search_dir.iterdir():
                        if sub.is_dir() and not sub.name.startswith("Common") and not sub.name.startswith("Windows"):
                            exe = self.find_best_executable(sub, sub.name)
                            if exe:
                                game = GameInfo(
                                    id=f"bottle_{sub.name}",
                                    title=f"{sub.name} (Bottle: {bottle_path.name})",
                                    launcher="Bottles",
                                    install_path=str(sub),
                                    executable_path=str(exe),
                                    recommended_method="version",
                                )
                                self._check_patch_status(game)
                                games.append(game)

        return games

    # =========================================================================
    # CUSTOM GAMES
    # =========================================================================
    def scan_custom_games(self) -> list[GameInfo]:
        games: list[GameInfo] = []
        if not self.custom_games_file.exists():
            return games

        try:
            with open(self.custom_games_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data:
                    path_str = item.get("install_path", "")
                    if path_str and os.path.exists(path_str):
                        install_path = Path(path_str)
                        title = item.get("title") or install_path.name
                        exe_str = item.get("executable_path", "")
                        exe_path = Path(exe_str) if exe_str and os.path.exists(exe_str) else self.find_best_executable(install_path, title)
                        game = GameInfo(
                            id=item.get("id", f"custom_{abs(hash(path_str))}"),
                            title=title,
                            launcher="Custom",
                            install_path=str(install_path),
                            executable_path=str(exe_path) if exe_path else "",
                            recommended_method=item.get("recommended_method", "version"),
                            quirk_notes=item.get("quirk_notes", ""),
                        )
                        self._check_patch_status(game)
                        games.append(game)
        except Exception:
            pass

        return games

    def add_custom_game(self, path: Path, title: Optional[str] = None) -> GameInfo:
        """Add a custom game path and persist it."""
        if path.is_file() and path.suffix.lower() == ".exe":
            install_path = path.parent
            exe_path = path
        else:
            install_path = path
            exe_path = self.find_best_executable(install_path, path.name)

        game_title = title or install_path.name
        slug = f"custom_{abs(hash(str(install_path)))}"

        new_game = GameInfo(
            id=slug,
            title=game_title,
            launcher="Custom",
            install_path=str(install_path),
            executable_path=str(exe_path) if exe_path else "",
            recommended_method="version",
        )
        self._check_patch_status(new_game)

        # Save to custom_games.json
        existing: list[dict] = []
        if self.custom_games_file.exists():
            try:
                with open(self.custom_games_file, "r", encoding="utf-8") as f:
                    existing = json.load(f)
            except Exception:
                existing = []

        # Remove duplicate if exists
        existing = [g for g in existing if g.get("install_path") != str(install_path)]
        existing.append(new_game.to_dict())

        with open(self.custom_games_file, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2, ensure_ascii=False)

        return new_game

    def remove_custom_game(self, game_id: str) -> None:
        if not self.custom_games_file.exists():
            return
        try:
            with open(self.custom_games_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            filtered = [g for g in data if g.get("id") != game_id]
            with open(self.custom_games_file, "w", encoding="utf-8") as f:
                json.dump(filtered, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    # =========================================================================
    # EXECUTABLE DETECTION & SCORING
    # =========================================================================
    def find_best_executable(self, root_dir: Path, game_title: str) -> Optional[Path]:
        """Find the most likely main executable for a game directory."""
        if not root_dir.is_dir():
            return None

        candidates: list[Path] = []
        try:
            for p in root_dir.rglob("*.exe"):
                if p.is_file():
                    candidates.append(p)
        except Exception:
            return None

        if not candidates:
            return None

        candidates.sort(key=lambda exe: self._score_executable(exe, root_dir, game_title), reverse=True)
        return candidates[0]

    def _score_executable(self, exe: Path, root: Path, game_title: str) -> int:
        norm_str = str(exe).lower().replace("\\", "/")
        norm_name = exe.name.lower()
        score = 100

        # Unreal Engine Shipping Executable
        if norm_name.endswith("-win64-shipping.exe") or norm_name.endswith("shipping.exe"):
            score += 500
        if "/binaries/win64/" in norm_str or "/bin/x64/" in norm_str:
            score += 350
        elif "/win64/" in norm_str:
            score += 200

        # Game title similarity
        clean_title = re.sub(r"[^a-z0-9]", "", game_title.lower())
        clean_stem = re.sub(r"[^a-z0-9]", "", exe.stem.lower())
        clean_root = re.sub(r"[^a-z0-9]", "", root.name.lower())

        if clean_title and (clean_title in clean_stem or clean_stem in clean_title):
            score += 250
        if clean_root and clean_root in clean_stem:
            score += 150

        # Root level bonus
        if exe.parent == root:
            score += 80

        # Penalty for bad executables (crash reporters, uninstalls, config tools)
        for bad in BAD_EXE_SUBSTRINGS:
            if bad in norm_str:
                score -= 600

        # Penalty for deeper nesting
        depth = len(exe.relative_to(root).parts)
        score -= depth * 10

        return score

    # =========================================================================
    # PATCH STATUS DETECTION
    # =========================================================================
    def _check_patch_status(self, game: GameInfo) -> None:
        """Inspect game target directory for DLSS Enabler manifest or proxy DLLs."""
        target_dir = Path(game.executable_path).parent if game.executable_path else Path(game.install_path)
        if not target_dir.exists():
            return

        manifest_file = target_dir / ".dlss_enabler_manifest.json"
        if manifest_file.exists():
            try:
                with open(manifest_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    game.is_patched = True
                    game.patch_method = data.get("method", "version")
                    game.patch_version = data.get("version", "Latest")
                    game.patch_time = data.get("installed_at", "")
                    game.has_backup = bool(data.get("backups"))
                    return
            except Exception:
                pass

        # Legacy / Manual marker check
        for marker in target_dir.glob("DLSS_ENABLER_*_DLL"):
            try:
                name = marker.name
                method = name.replace("DLSS_ENABLER_", "").replace("_DLL", "").lower()
                game.is_patched = True
                game.patch_method = method
                game.patch_version = "Installed"
                return
            except Exception:
                pass

        # Check if version.dll or other proxy dll exists alongside dlssg_to_fsr3
        if (target_dir / "dlssg_to_fsr3_amd_is_better.dll").exists() or (target_dir / "dlss-enabler-upscaler.dll").exists():
            game.is_patched = True
            for m in ["version", "dxgi", "winmm", "d3d12", "dinput8"]:
                if (target_dir / f"{m}.dll").exists():
                    game.patch_method = m
                    break
            game.patch_version = "Manual/Custom"
