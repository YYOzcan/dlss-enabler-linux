"""Downloader Engine for DLSS Enabler and OptiScaler.
Fetches the latest official release from GitHub, unpacks binaries, and caches them locally.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

# Primary GitHub repositories for DLSS Enabler releases & Linux binaries
DLSS_ENABLER_REPO = "artur-graniszewski/DLSS-Enabler"
DECKY_DLSS_REPO = "xXJSONDeruloXx/decky-dlss-enabler"
OPTISCALER_REPO = "optiscaler/OptiScaler"

@dataclass
class ReleaseInfo:
    tag: str
    name: str
    published_at: str
    download_url: str
    file_name: str
    file_size: int
    source_type: str  # 'setup_exe', 'zip', 'dll'
    description: str = ""

class DLSSDownloader:
    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or (Path.home() / ".cache" / "dlss-enabler-linux")
        self.versions_dir = self.cache_dir / "versions"
        self.versions_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.cache_dir / "installed_version.json"

    def get_cached_version(self) -> Optional[dict]:
        """Return cached version metadata if files are ready."""
        if not self.metadata_file.exists():
            return None
        try:
            with open(self.metadata_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                bin_dir = Path(data.get("bin_dir", ""))
                if bin_dir.exists() and (bin_dir / "version.dll").exists():
                    return data
        except Exception:
            pass
        return None

    def check_latest_release(self) -> ReleaseInfo:
        """Query GitHub for the newest DLSS Enabler release."""
        # Check artur-graniszewski/DLSS-Enabler latest
        headers = {"User-Agent": "DLSS-Enabler-Linux/1.0"}
        
        # We check both repos to find the best available asset
        release_info: Optional[ReleaseInfo] = None

        try:
            req = urllib.request.Request(
                f"https://api.github.com/repos/{DLSS_ENABLER_REPO}/releases/latest",
                headers=headers
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
                tag = data.get("tag_name", "latest")
                assets = data.get("assets", [])
                for a in assets:
                    name = a.get("name", "")
                    if name.endswith(".exe") and "dlss-enabler" in name.lower():
                        release_info = ReleaseInfo(
                            tag=tag,
                            name=data.get("name") or f"DLSS Enabler {tag}",
                            published_at=data.get("published_at", ""),
                            download_url=a.get("browser_download_url"),
                            file_name=name,
                            file_size=a.get("size", 0),
                            source_type="setup_exe",
                            description=data.get("body", "")[:300]
                        )
                        break
        except Exception as e:
            pass

        # Fallback / Alternative check from decky-dlss-enabler if needed
        if not release_info:
            try:
                req = urllib.request.Request(
                    f"https://api.github.com/repos/{DECKY_DLSS_REPO}/releases/latest",
                    headers=headers
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    data = json.loads(resp.read().decode())
                    tag = data.get("tag_name", "latest")
                    assets = data.get("assets", [])
                    for a in assets:
                        name = a.get("name", "")
                        if name.endswith(".zip") and "dlss" in name.lower():
                            release_info = ReleaseInfo(
                                tag=tag,
                                name=data.get("name") or f"DLSS Enabler {tag}",
                                published_at=data.get("published_at", ""),
                                download_url=a.get("browser_download_url"),
                                file_name=name,
                                file_size=a.get("size", 0),
                                source_type="zip",
                                description=data.get("body", "")[:300]
                            )
                            break
            except Exception:
                pass

        # If offline or API rate-limited, provide fallback known release
        if not release_info:
            release_info = ReleaseInfo(
                tag="v0.9.4",
                name="DLSS Enabler v0.9.4 (OptiScaler 0.9.4)",
                published_at="2026-07-18",
                download_url="https://github.com/artur-graniszewski/DLSS-Enabler/releases/download/v0.9.4/dlss-enabler-setup_0.9.4-final.20260718._MM.exe",
                file_name="dlss-enabler-setup_0.9.4-final.20260718._MM.exe",
                file_size=33007175,
                source_type="setup_exe",
                description="Simulate DLSS Upscaler and DLSS-G Frame Generation features on any GPU."
            )

        return release_info

    def download_and_extract(
        self,
        release: ReleaseInfo,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> Path:
        """
        Download the release file and unpack it into the cache directory.
        progress_callback: fn(downloaded_bytes, total_bytes, status_message)
        Returns the path to the directory containing the unpacked DLL files.
        """
        version_dir = self.versions_dir / release.tag
        target_bin_dir = version_dir / "bin"
        target_bin_dir.mkdir(parents=True, exist_ok=True)

        download_file = version_dir / release.file_name

        if progress_callback:
            progress_callback(0, release.file_size, f"Downloading {release.file_name}...")

        # Download with chunking and progress reporting
        req = urllib.request.Request(
            release.download_url,
            headers={"User-Agent": "DLSS-Enabler-Linux/1.0"}
        )

        with urllib.request.urlopen(req, timeout=60) as resp, open(download_file, "wb") as out_f:
            total_size = int(resp.headers.get("content-length", release.file_size))
            downloaded = 0
            block_size = 1024 * 64
            last_report = time.time()

            while True:
                chunk = resp.read(block_size)
                if not chunk:
                    break
                out_f.write(chunk)
                downloaded += len(chunk)

                now = time.time()
                if now - last_report > 0.15 or downloaded == total_size:
                    last_report = now
                    mb_cur = downloaded / (1024 * 1024)
                    mb_tot = total_size / (1024 * 1024)
                    pct = int(downloaded * 100 / total_size) if total_size else 0
                    msg = f"Downloading: {mb_cur:.1f} MB / {mb_tot:.1f} MB ({pct}%)"
                    if progress_callback:
                        progress_callback(downloaded, total_size, msg)

        if progress_callback:
            progress_callback(total_size, total_size, "Extracting components...")

        # Extract binaries based on source type
        if release.source_type == "setup_exe":
            self._extract_via_wine(download_file, target_bin_dir)
        elif release.source_type == "zip":
            self._extract_zip(download_file, target_bin_dir)

        # Ensure we have version.dll and other key binaries
        # If version.dll is not named or is inside a subfolder, locate and move it
        self._normalize_bin_dir(target_bin_dir)

        # Save metadata
        meta = {
            "tag": release.tag,
            "name": release.name,
            "file_name": release.file_name,
            "bin_dir": str(target_bin_dir),
            "installed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        with open(self.metadata_file, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

        if progress_callback:
            progress_callback(total_size, total_size, "Ready! DLSS Enabler is up to date.")

        return target_bin_dir

    def _extract_via_wine(self, setup_exe: Path, target_dir: Path) -> None:
        """Extract Inno Setup installer silently using Wine into target_dir."""
        temp_dest = target_dir.parent / "wine_extract_temp"
        temp_dest.mkdir(parents=True, exist_ok=True)

        # Run wine silent setup
        cmd = [
            "wine", str(setup_exe.resolve()),
            "/SILENT", "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART",
            f'/DIR=Z:{temp_dest.resolve()}'
        ]
        
        env = os.environ.copy()
        env["WINEDEBUG"] = "-all"
        subprocess.run(cmd, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)

        # Move extracted files to target_dir
        for item in temp_dest.iterdir():
            dest = target_dir / item.name
            if dest.exists():
                if dest.is_dir():
                    shutil.rmtree(dest)
                else:
                    dest.unlink()
            shutil.move(str(item), str(target_dir))

        shutil.rmtree(temp_dest, ignore_errors=True)

    def _extract_zip(self, zip_path: Path, target_dir: Path) -> None:
        """Extract zip and copy binaries to target_dir."""
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(target_dir)

    def _normalize_bin_dir(self, bin_dir: Path) -> None:
        """Ensure all required DLL files are in the root of bin_dir."""
        # If files are nested under "DLSS Enabler/bin" or similar, hoist them up
        for root, dirs, files in os.walk(bin_dir):
            if root == str(bin_dir):
                continue
            for f in files:
                if f.endswith(".dll") or f.endswith(".ini") or f.endswith(".asi"):
                    src = Path(root) / f
                    dst = bin_dir / f
                    if not dst.exists():
                        shutil.copy2(src, dst)
