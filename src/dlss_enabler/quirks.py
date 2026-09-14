"""Game quirks and recommended configurations for DLSS Enabler on Linux/Proton."""

KNOWN_QUIRKS: dict[str, dict] = {
    # Cyberpunk 2077
    "1091500": {
        "title": "Cyberpunk 2077",
        "recommended_method": "version",
        "notes": "DirectX 12 mode required. Enable DLSS and Frame Generation in Graphics settings.",
        "exe_hint": "bin/x64/Cyberpunk2077.exe",
    },
    # The Witcher 3
    "292030": {
        "title": "The Witcher 3: Wild Hunt",
        "recommended_method": "d3d12",
        "notes": "Launch the game in DX12 mode. Use d3d12.dll or version.dll.",
        "exe_hint": "bin/x64_dx12/witcher3.exe",
    },
    # Black Myth: Wukong
    "2358720": {
        "title": "Black Myth: Wukong",
        "recommended_method": "version",
        "notes": "Unreal Engine 5 title. Frame Generation requires DX12 mode.",
        "exe_hint": "b1/Binaries/Win64/b1-Win64-Shipping.exe",
    },
    # Ghost of Tsushima
    "2215430": {
        "title": "Ghost of Tsushima DIRECTOR'S CUT",
        "recommended_method": "version",
        "notes": "Works out of the box with version.dll hook.",
        "exe_hint": "GhostOfTsushima.exe",
    },
    # God of War
    "1593500": {
        "title": "God of War",
        "recommended_method": "dxgi",
        "notes": "dxgi.dll or version.dll works great.",
        "exe_hint": "GoW.exe",
    },
    # God of War Ragnarök
    "2322010": {
        "title": "God of War Ragnarök",
        "recommended_method": "version",
        "notes": "DirectX 12 required. Use version.dll.",
        "exe_hint": "GoWR.exe",
    },
    # Clair Obscur: Expedition 33
    "expedition33": {
        "title": "Clair Obscur: Expedition 33",
        "recommended_method": "version",
        "notes": "Unreal Engine 5 title. Target Win64 shipping executable.",
        "exe_hint": "Expedition33/Binaries/Win64/Expedition33-Win64-Shipping.exe",
    },
    # Hogwarts Legacy
    "990080": {
        "title": "Hogwarts Legacy",
        "recommended_method": "version",
        "notes": "Target Phoenix/Binaries/Win64/HogwartsLegacy.exe.",
        "exe_hint": "Phoenix/Binaries/Win64/HogwartsLegacy.exe",
    },
    # Horizon Forbidden West
    "2420110": {
        "title": "Horizon Forbidden West Complete Edition",
        "recommended_method": "version",
        "notes": "DirectX 12 required. Enable DLSS-G in Display options.",
        "exe_hint": "HorizonForbiddenWest.exe",
    },
    # Horizon Zero Dawn Remastered
    "2561860": {
        "title": "Horizon Zero Dawn Remastered",
        "recommended_method": "version",
        "notes": "Target main game executable with version.dll.",
        "exe_hint": "HorizonZeroDawnRemastered.exe",
    },
    # Spider-Man Remastered
    "1817070": {
        "title": "Marvel's Spider-Man Remastered",
        "recommended_method": "version",
        "notes": "Use version.dll or dxgi.dll.",
        "exe_hint": "Spider-Man.exe",
    },
    # Spider-Man: Miles Morales
    "1817190": {
        "title": "Marvel's Spider-Man: Miles Morales",
        "recommended_method": "version",
        "notes": "Use version.dll.",
        "exe_hint": "MilesMorales.exe",
    },
    # Ratchet & Clank: Rift Apart
    "1895840": {
        "title": "Ratchet & Clank: Rift Apart",
        "recommended_method": "version",
        "notes": "Enable Frame Generation in Display options.",
        "exe_hint": "RiftApart.exe",
    },
    # Alan Wake 2
    "alanwake2": {
        "title": "Alan Wake 2",
        "recommended_method": "version",
        "notes": "Northlight Engine. Target AlanWake2.exe.",
        "exe_hint": "AlanWake2.exe",
    },
    # Red Dead Redemption 2
    "1174180": {
        "title": "Red Dead Redemption 2",
        "recommended_method": "version",
        "notes": "Launch game using DirectX 12 API (not Vulkan) for DLSS/FG to hook.",
        "exe_hint": "RDR2.exe",
    },
    # Starfield
    "1716740": {
        "title": "Starfield",
        "recommended_method": "version",
        "notes": "DirectX 12 native. Use version.dll.",
        "exe_hint": "Starfield.exe",
    },
    # Remnant II
    "1282100": {
        "title": "Remnant II",
        "recommended_method": "version",
        "notes": "Unreal Engine 5. Target Remnant2/Binaries/Win64/Remnant2-Win64-Shipping.exe.",
        "exe_hint": "Remnant2/Binaries/Win64/Remnant2-Win64-Shipping.exe",
    },
    # Lords of the Fallen
    "1501750": {
        "title": "Lords of the Fallen",
        "recommended_method": "version",
        "notes": "UE5 title. Target LOTF2/Binaries/Win64/LOTF2-Win64-Shipping.exe.",
        "exe_hint": "LOTF2/Binaries/Win64/LOTF2-Win64-Shipping.exe",
    },
    # RoboCop: Rogue City
    "1681430": {
        "title": "RoboCop: Rogue City",
        "recommended_method": "version",
        "notes": "UE5 title. Target RoboCop/Binaries/Win64/RoboCop-Win64-Shipping.exe.",
        "exe_hint": "RoboCop/Binaries/Win64/RoboCop-Win64-Shipping.exe",
    },
    # Palworld
    "1623730": {
        "title": "Palworld",
        "recommended_method": "version",
        "notes": "Target Pal/Binaries/Win64/Palworld-Win64-Shipping.exe.",
        "exe_hint": "Pal/Binaries/Win64/Palworld-Win64-Shipping.exe",
    },
}

SUPPORTED_HOOK_METHODS = [
    ("version", "version.dll (Most Compatible / Recommended)"),
    ("dxgi", "dxgi.dll (DirectX Graphics Infrastructure)"),
    ("winmm", "winmm.dll (Windows Multimedia)"),
    ("d3d12", "d3d12.dll (Direct3D 12)"),
    ("d3d11", "d3d11.dll (Direct3D 11)"),
    ("dinput8", "dinput8.dll (DirectInput 8)"),
    ("winhttp", "winhttp.dll (Windows HTTP Services)"),
    ("wininet", "wininet.dll (Windows Internet API)"),
    ("dbghelp", "dbghelp.dll (Debug Helper)"),
]

def get_game_quirk(game_id: str, game_title: str = "") -> dict | None:
    """Find quirk config for game by AppID or normalized name."""
    if str(game_id) in KNOWN_QUIRKS:
        return KNOWN_QUIRKS[str(game_id)]

    norm_title = game_title.lower().replace(":", "").replace("'", "").replace("-", " ")
    for k, q in KNOWN_QUIRKS.items():
        q_title = q["title"].lower().replace(":", "").replace("'", "").replace("-", " ")
        if norm_title in q_title or q_title in norm_title:
            return q
    return None
