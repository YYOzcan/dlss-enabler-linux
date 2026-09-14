"""Game Patcher & Backup Engine for DLSS Enabler on Linux.
Safely installs, manages, backs up, and uninstalls DLSS Enabler in game directories.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .downloader import DLSSDownloader
from .scanner import GameInfo

MANIFEST_NAME = ".dlss_enabler_manifest.json"
BACKUP_SUFFIX = ".dlss_backup"

KNOWN_DLSS_FILES = [
    "dlss-enabler-upscaler.dll",
    "dlssg_to_fsr3_amd_is_better.dll",
    "amd_fidelityfx_dx12.dll",
    "amd_fidelityfx_vk.dll",
    "amd_fidelityfx_upscaler_dx12.dll",
    "amd_fidelityfx_framegeneration_dx12.dll",
    "libxess.dll",
    "libxess_dx11.dll",
    "nvngx-wrapper.dll",
    "nvngx.ini",
    "OptiScaler.ini",
    "OptiPatcher.asi",
    "dlss-enabler.ini",
    "dlss-enabler.log",
    "dlssg_to_fsr3.log",
    "fakenvapi.log",
    "OptiScaler.log",
]

@dataclass
class PatchResult:
    success: bool
    message: str
    target_dir: str
    method: str
    launch_options: str
    installed_files: list[str]

class GamePatcher:
    def __init__(self, downloader: Optional[DLSSDownloader] = None):
        self.downloader = downloader or DLSSDownloader()

    def get_target_directory(self, game: GameInfo) -> Path:
        """Resolve the target directory where the proxy DLL and configs must be placed."""
        if game.executable_path and os.path.exists(game.executable_path):
            return Path(game.executable_path).parent
        return Path(game.install_path)

    def generate_launch_options(self, method: str = "version", extra_env: str = "") -> str:
        """Generate optimized launch options for Proton / Wine."""
        base_override = f'WINEDLLOVERRIDES="{method}=n,b"'
        deck_flag = "SteamDeck=0"
        
        flags = [base_override, deck_flag]
        if extra_env.strip():
            flags.append(extra_env.strip())
        flags.append("%command%")

        return " ".join(flags)

    def get_launcher_instructions(self, launcher: str, method: str = "version") -> str:
        """Return instructions tailored to the game launcher."""
        from .i18n import t
        lower_launcher = launcher.lower()
        if "steam" in lower_launcher:
            return t("launcher_steam_instructions", method=method)
        elif "heroic" in lower_launcher:
            return t("launcher_heroic_instructions", method=method)
        elif "lutris" in lower_launcher:
            return t("launcher_lutris_instructions", method=method)
        elif "bottle" in lower_launcher:
            return t("launcher_bottles_instructions", method=method)
        return t("launcher_steam_instructions", method=method)

    def patch_game(
        self,
        game: GameInfo,
        method: str = "version",
        bin_dir: Optional[Path] = None
    ) -> PatchResult:
        """
        Patch a game with DLSS Enabler using the specified hook DLL method.
        Creates backups of existing files and tracks everything via manifest.
        """
        target_dir = self.get_target_directory(game)
        if not target_dir.exists():
            return PatchResult(
                success=False,
                message=f"Target directory does not exist: {target_dir}",
                target_dir=str(target_dir),
                method=method,
                launch_options="",
                installed_files=[]
            )

        # Locate source binaries
        if not bin_dir:
            cached = self.downloader.get_cached_version()
            if not cached or not os.path.exists(cached.get("bin_dir", "")):
                # Need to download first
                try:
                    rel = self.downloader.check_latest_release()
                    bin_dir = self.downloader.download_and_extract(rel)
                except Exception as exc:
                    return PatchResult(
                        success=False,
                        message=f"Failed to fetch DLSS Enabler binaries: {exc}",
                        target_dir=str(target_dir),
                        method=method,
                        launch_options="",
                        installed_files=[]
                    )
            else:
                bin_dir = Path(cached["bin_dir"])

        proxy_dll_source = bin_dir / "version.dll"
        if not proxy_dll_source.exists():
            # Check any dll in bin_dir
            for f in bin_dir.glob("*.dll"):
                if "version" in f.name.lower():
                    proxy_dll_source = f
                    break

        if not proxy_dll_source or not proxy_dll_source.exists():
            return PatchResult(
                success=False,
                message=f"Source proxy DLL not found in {bin_dir}",
                target_dir=str(target_dir),
                method=method,
                launch_options="",
                installed_files=[]
            )

        # 1. Clean up any previous DLSS Enabler installation in target_dir
        self.unpatch_game(game)

        installed_files: list[str] = []
        backups: dict[str, str] = {}

        try:
            # 2. Install Proxy DLL (named according to the chosen method, e.g. version.dll, dxgi.dll)
            target_proxy_name = f"{method}.dll"
            target_proxy_path = target_dir / target_proxy_name

            # If an existing file exists and is not a previously placed DLSS DLL, back it up
            if target_proxy_path.exists():
                backup_name = f"{target_proxy_name}{BACKUP_SUFFIX}"
                backup_path = target_dir / backup_name
                shutil.copy2(target_proxy_path, backup_path)
                backups[target_proxy_name] = backup_name

            shutil.copy2(proxy_dll_source, target_proxy_path)
            installed_files.append(target_proxy_name)

            # 3. Copy supporting DLSS Enabler & OptiScaler DLLs and configurations
            copy_candidates = [
                "dlssg_to_fsr3_amd_is_better.dll",
                "dlss-enabler-upscaler.dll",
                "OptiScaler.dll",
                "amd_fidelityfx_dx12.dll",
                "amd_fidelityfx_vk.dll",
                "amd_fidelityfx_upscaler_dx12.dll",
                "amd_fidelityfx_framegeneration_dx12.dll",
                "libxess.dll",
                "libxess_dx11.dll",
                "nvngx-wrapper.dll",
                "nvngx.ini",
                "OptiScaler.ini",
                "OptiPatcher.asi",
            ]

            for cand_name in copy_candidates:
                src_cand = bin_dir / cand_name
                if src_cand.exists():
                    dest_cand = target_dir / cand_name
                    # Preserve existing custom INI configurations
                    if cand_name.endswith(".ini") and dest_cand.exists():
                        continue
                    if dest_cand.exists() and cand_name not in KNOWN_DLSS_FILES:
                        backup_name = f"{cand_name}{BACKUP_SUFFIX}"
                        shutil.copy2(dest_cand, target_dir / backup_name)
                        backups[cand_name] = backup_name
                    shutil.copy2(src_cand, dest_cand)
                    installed_files.append(cand_name)

            # 4. Write manifest file
            cached_info = self.downloader.get_cached_version() or {}
            manifest_data = {
                "game_id": game.id,
                "game_title": game.title,
                "method": method,
                "version": cached_info.get("name", "Latest"),
                "installed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "installed_files": installed_files,
                "backups": backups,
            }

            manifest_path = target_dir / MANIFEST_NAME
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(manifest_data, f, indent=2)

            launch_options = self.generate_launch_options(method)

            # Update game state
            game.is_patched = True
            game.patch_method = method
            game.patch_version = cached_info.get("name", "Latest")
            game.patch_time = manifest_data["installed_at"]
            game.has_backup = bool(backups)

            return PatchResult(
                success=True,
                message=f"DLSS Enabler successfully installed with {target_proxy_name}!",
                target_dir=str(target_dir),
                method=method,
                launch_options=launch_options,
                installed_files=installed_files
            )

        except Exception as exc:
            return PatchResult(
                success=False,
                message=f"Installation failed: {exc}",
                target_dir=str(target_dir),
                method=method,
                launch_options="",
                installed_files=installed_files
            )

    def unpatch_game(self, game: GameInfo) -> tuple[bool, str]:
        """
        Cleanly remove DLSS Enabler from a game directory and restore any backups.
        """
        target_dir = self.get_target_directory(game)
        if not target_dir.exists():
            return False, "Target directory not found."

        manifest_path = target_dir / MANIFEST_NAME
        files_to_remove: set[str] = set()
        backups_to_restore: dict[str, str] = {}

        if manifest_path.exists():
            try:
                with open(manifest_path, "r", encoding="utf-8") as f:
                    m = json.load(f)
                    files_to_remove.update(m.get("installed_files", []))
                    backups_to_restore.update(m.get("backups", {}))
            except Exception:
                pass

        # Also add known DLSS Enabler files and runtime logs
        for k in KNOWN_DLSS_FILES:
            files_to_remove.add(k)

        # Remove installed files
        for fname in files_to_remove:
            fpath = target_dir / fname
            if fpath.exists() and fpath.is_file():
                try:
                    fpath.unlink()
                except Exception:
                    pass

        # Restore backups
        for orig, backup in backups_to_restore.items():
            bpath = target_dir / backup
            opath = target_dir / orig
            if bpath.exists():
                try:
                    if opath.exists():
                        opath.unlink()
                    bpath.rename(opath)
                except Exception:
                    pass

        # Also check for any standalone .dlss_backup files
        for bpath in target_dir.glob(f"*{BACKUP_SUFFIX}"):
            orig_name = bpath.name.replace(BACKUP_SUFFIX, "")
            opath = target_dir / orig_name
            if not opath.exists():
                try:
                    bpath.rename(opath)
                except Exception:
                    pass

        # Remove marker files
        for marker in target_dir.glob("DLSS_ENABLER_*_DLL"):
            try:
                marker.unlink()
            except Exception:
                pass

        if manifest_path.exists():
            try:
                manifest_path.unlink()
            except Exception:
                pass

        game.is_patched = False
        game.patch_method = ""
        game.patch_version = ""
        game.patch_time = ""
        game.has_backup = False

        return True, "DLSS Enabler cleanly uninstalled and original files restored."
