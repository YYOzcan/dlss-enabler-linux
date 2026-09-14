"""Internationalization (i18n) Engine for DLSS Enabler Linux.
Supports 6 languages: English, Turkish, German, French, Spanish, Russian.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Callable, Optional

TRANSLATIONS: dict[str, dict[str, str]] = {
    "en": {
        "app_title": "DLSS Enabler for Linux",
        "app_subtitle": "Universal Upscaler & Frame Generation Injector for Proton / Wine",
        "core_checking": "Checking Core...",
        "core_ready": "● DLSS Enabler {ver} (Ready)",
        "core_missing": "○ Not Downloaded",
        "btn_update_core": "Check Updates",
        "btn_download_core": "Download Now",
        "btn_add_game": "+ Add Game",
        "btn_refresh": "↻ Refresh",
        "search_placeholder": "🔍 Search installed games...",
        "filter_all": "All",
        "filter_steam": "Steam",
        "filter_heroic": "Heroic",
        "filter_lutris": "Lutris",
        "filter_custom": "Custom",
        "filter_status_all": "All Status",
        "filter_status_patched": "Patched Only",
        "filter_status_unpatched": "Unpatched Only",
        "status_scanning": "Scanning games across Steam, Heroic, Lutris, Bottles...",
        "status_found": "Found {count} games across installed launchers.",
        "empty_title": "Select a Game",
        "empty_desc": "Choose a game from the list to view compatibility, configure proxy hook methods, and install DLSS Enabler in one click.",
        "badge_patched": "✓ Patched",
        "badge_unpatched": "Not Patched",
        "badge_native_linux": "Native Linux",
        "target_exe_header": "TARGET EXECUTABLE & DIRECTORY",
        "btn_browse": "Browse...",
        "tips_header": "💡 Recommendation & Tips:",
        "method_header": "DLSS ENABLER INJECTION METHOD",
        "hook_proxy_label": "Hook Proxy DLL:",
        "launch_options_header": "RECOMMENDED PROTON LAUNCH OPTIONS",
        "btn_copy": "📋 Copy",
        "toast_copied": "✓ Copied launch options to clipboard!",
        "btn_install": "⚡ Install DLSS Enabler",
        "btn_reinstall": "⚡ Reinstall / Update DLSS Enabler",
        "btn_installing": "Installing...",
        "btn_uninstall": "↺ Uninstall / Restore",
        "btn_open_folder": "📁 Open Folder",
        "components_header": "INSTALLED COMPONENTS",
        "no_components": "No active DLSS Enabler files installed.",
        "download_connecting": "Connecting to GitHub...",
        "download_complete": "Ready! DLSS Enabler is up to date.",
        "dialog_download_success_title": "DLSS Enabler Ready",
        "dialog_download_fail_title": "Download Failed",
        "dialog_download_fail_msg": "Could not download binaries:\n{err}",
        "dialog_install_success_title": "Installation Successful",
        "dialog_install_success_msg": "DLSS Enabler has been installed successfully!\n\nHook Method: {method}.dll\nTarget: {target}\n\nLaunch Options:\n{opts}\n\nBe sure to paste this into your game properties.",
        "dialog_install_fail_title": "Installation Failed",
        "dialog_uninstall_confirm_title": "Confirm Uninstall",
        "dialog_uninstall_confirm_msg": "Are you sure you want to remove DLSS Enabler from '{title}'?\nOriginal backup files will be restored automatically.",
        "dialog_restored_title": "Restored",
        "dialog_uninstall_notice_title": "Uninstall Notice",
        "dialog_select_game_folder": "Select Game Folder",
        "dialog_select_game_exe": "Select Game Executable",
        "launcher_steam_instructions": "Steam: Right-click game > Properties > General > Launch Options > Paste the command above.",
        "launcher_heroic_instructions": "Heroic: Game Settings > Other > Environment Variables > WINEDLLOVERRIDES={method}=n,b SteamDeck=0",
        "launcher_lutris_instructions": "Lutris: Configure > Runner options > DLL overrides > Add key: '{method}', value: 'n,b'",
        "launcher_bottles_instructions": "Bottles: Bottle > Settings > Environment Variables > Add WINEDLLOVERRIDES={method}=n,b",
        "card_dlss_active": "DLSS ON",
        "card_ready": "Ready to install",
        "card_native": "Native Linux",
        "btn_configure": "⚙ Configure",
        "btn_close": "Close",
        "no_games_found": "No installed games found",
        "no_games_desc": "Try adjusting your search or use '+ Add Game' to add any custom game folder.",
    },
    "tr": {
        "app_title": "Linux için DLSS Enabler",
        "app_subtitle": "Proton ve Wine İçin Evrensel DLSS ve Kare Üretimi Yöneticisi",
        "core_checking": "Bileşenler Denetleniyor...",
        "core_ready": "● DLSS Enabler {ver} (Hazır)",
        "core_missing": "○ Henüz İndirilmedi",
        "btn_update_core": "Güncellemeleri Denetle",
        "btn_download_core": "Şimdi İndir",
        "btn_add_game": "+ Oyun Ekle",
        "btn_refresh": "↻ Yenile",
        "search_placeholder": "🔍 Yüklü oyunlarda ara...",
        "filter_all": "Tümü",
        "filter_steam": "Steam",
        "filter_heroic": "Heroic",
        "filter_lutris": "Lutris",
        "filter_custom": "Özel",
        "filter_status_all": "Tüm Durumlar",
        "filter_status_patched": "Sadece Kurulu Olanlar",
        "filter_status_unpatched": "Kurulu Olmayanlar",
        "status_scanning": "Steam, Heroic, Lutris ve Bottles oyunları taranıyor...",
        "status_found": "Yüklü {count} oyun listeleniyor.",
        "empty_title": "Bir Oyun Seçin",
        "empty_desc": "Uyumluluğu görmek, hook yöntemlerini yapılandırmak ve tek tıkla DLSS Enabler kurmak için kartına tıklayın.",
        "badge_patched": "✓ Kurulu",
        "badge_unpatched": "Kurulu Değil",
        "badge_native_linux": "Yerel Linux",
        "target_exe_header": "HEDEF ÇALIŞTIRILABİLİR DOSYA VE KLASÖR",
        "btn_browse": "Gözat...",
        "tips_header": "💡 Tavsiyeler ve İpuçları:",
        "method_header": "DLSS ENABLER ENJEKSİYON YÖNTEMİ",
        "hook_proxy_label": "Kanca (Proxy) DLL:",
        "launch_options_header": "ÖNERİLEN PROTON BAŞLATMA SEÇENEKLERİ",
        "btn_copy": "📋 Kopyala",
        "toast_copied": "✓ Başlatma seçenekleri panoya kopyalandı!",
        "btn_install": "⚡ DLSS Enabler'ı Kur",
        "btn_reinstall": "⚡ Yeniden Kur / Güncelle",
        "btn_installing": "Kuruluyor...",
        "btn_uninstall": "↺ Kaldır ve Geri Al",
        "btn_open_folder": "📁 Klasörü Aç",
        "components_header": "YÜKLÜ BİLEŞENLER",
        "no_components": "Aktif DLSS Enabler dosyası bulunmuyor.",
        "download_connecting": "GitHub'a bağlanılıyor...",
        "download_complete": "Hazır! DLSS Enabler güncel.",
        "dialog_download_success_title": "DLSS Enabler Hazır",
        "dialog_download_fail_title": "İndirme Başarısız",
        "dialog_download_fail_msg": "Bileşenler indirilemedi:\n{err}",
        "dialog_install_success_title": "Kurulum Başarılı",
        "dialog_install_success_msg": "DLSS Enabler başarıyla kuruldu!\n\nHook Yöntemi: {method}.dll\nHedef Dizin: {target}\n\nBaşlatma Seçenekleri:\n{opts}\n\nBu satırı oyun başlatma seçeneklerinize yapıştırmayı unutmayın.",
        "dialog_install_fail_title": "Kurulum Başarısız",
        "dialog_uninstall_confirm_title": "Kaldırmayı Onayla",
        "dialog_uninstall_confirm_msg": "'{title}' oyunundan DLSS Enabler kaldırılsın mı?\nOrijinal yedek dosyaları otomatik olarak geri yüklenecektir.",
        "dialog_restored_title": "Geri Yüklendi",
        "dialog_uninstall_notice_title": "Kaldırma Bildirimi",
        "dialog_select_game_folder": "Oyun Klasörünü Seçin",
        "dialog_select_game_exe": "Oyun Çalıştırılabilir Dosyasını Seçin",
        "launcher_steam_instructions": "Steam: Oyuna sağ tıkla > Özellikler > Genel > Başlatma Seçenekleri > Yukarıdaki komutu yapıştırın.",
        "launcher_heroic_instructions": "Heroic: Oyun Ayarları > Diğer > Ortam Değişkenleri > WINEDLLOVERRIDES={method}=n,b SteamDeck=0 ekleyin.",
        "launcher_lutris_instructions": "Lutris: Yapılandır > Runner seçenekleri > DLL geçersiz kılma > '{method}' = 'n,b' ekleyin.",
        "launcher_bottles_instructions": "Bottles: Şişe > Ayarlar > Ortam Değişkenleri > WINEDLLOVERRIDES={method}=n,b ekleyin.",
        "card_dlss_active": "DLSS AKTİF",
        "card_ready": "Kuruluma hazır",
        "card_native": "Yerel Linux",
        "btn_configure": "⚙ Yapılandır",
        "btn_close": "Kapat",
        "no_games_found": "Yüklü oyun bulunamadı",
        "no_games_desc": "Arama filtrenizi değiştirin veya '+ Oyun Ekle' butonundan manuel klasör seçin.",
    },
    "de": {
        "app_title": "DLSS Enabler für Linux",
        "app_subtitle": "Universeller Upscaler & Frame Generation Manager für Proton / Wine",
        "core_checking": "Überprüfe Core...",
        "core_ready": "● DLSS Enabler {ver} (Bereit)",
        "core_missing": "○ Nicht heruntergeladen",
        "btn_update_core": "Nach Updates suchen",
        "btn_download_core": "Jetzt herunterladen",
        "btn_add_game": "+ Spiel hinzufügen",
        "btn_refresh": "↻ Aktualisieren",
        "search_placeholder": "🔍 Installierte Spiele durchsuchen...",
        "filter_all": "Alle",
        "filter_steam": "Steam",
        "filter_heroic": "Heroic",
        "filter_lutris": "Lutris",
        "filter_custom": "Benutzerdefiniert",
        "filter_status_all": "Alle Status",
        "filter_status_patched": "Nur installiert",
        "filter_status_unpatched": "Nicht installiert",
        "status_scanning": "Scanne Spiele auf Steam, Heroic, Lutris, Bottles...",
        "status_found": "{count} Spiele gefunden.",
        "empty_title": "Wähle ein Spiel",
        "empty_desc": "Wähle ein Spiel aus der Liste, um die Kompatibilität zu prüfen und DLSS Enabler mit einem Klick zu installieren.",
        "badge_patched": "✓ Installiert",
        "badge_unpatched": "Nicht installiert",
        "badge_native_linux": "Natives Linux",
        "target_exe_header": "ZIEL-EXECUTABLE & VERZEICHNIS",
        "btn_browse": "Durchsuchen...",
        "tips_header": "💡 Empfehlungen & Tipps:",
        "method_header": "DLSS ENABLER INJEKTIONSMETHODE",
        "hook_proxy_label": "Hook Proxy DLL:",
        "launch_options_header": "EMPFOHLENE PROTON-STARTOPTIONEN",
        "btn_copy": "📋 Kopieren",
        "toast_copied": "✓ Startoptionen in die Zwischenablage kopiert!",
        "btn_install": "⚡ DLSS Enabler installieren",
        "btn_reinstall": "⚡ Neu installieren / Aktualisieren",
        "btn_installing": "Installiere...",
        "btn_uninstall": "↺ Deinstallieren & Wiederherstellen",
        "btn_open_folder": "📁 Ordner öffnen",
        "components_header": "INSTALLIERTE KOMPONENTEN",
        "no_components": "Keine aktiven DLSS Enabler-Dateien installiert.",
        "download_connecting": "Verbindung zu GitHub...",
        "download_complete": "Bereit! DLSS Enabler ist aktuell.",
        "dialog_download_success_title": "DLSS Enabler bereit",
        "dialog_download_fail_title": "Download fehlgeschlagen",
        "dialog_download_fail_msg": "Dateien konnten nicht heruntergeladen werden:\n{err}",
        "dialog_install_success_title": "Installation erfolgreich",
        "dialog_install_success_msg": "DLSS Enabler wurde erfolgreich installiert!\n\nHook-Methode: {method}.dll\nZiel: {target}\n\nStartoptionen:\n{opts}",
        "dialog_install_fail_title": "Installation fehlgeschlagen",
        "dialog_uninstall_confirm_title": "Deinstallation bestätigen",
        "dialog_uninstall_confirm_msg": "Möchtest du DLSS Enabler wirklich von '{title}' entfernen?\nOriginaldateien werden automatisch wiederhergestellt.",
        "dialog_restored_title": "Wiederhergestellt",
        "dialog_uninstall_notice_title": "Deinstallationshinweis",
        "dialog_select_game_folder": "Spielordner auswählen",
        "dialog_select_game_exe": "Ausführbare Datei auswählen",
        "launcher_steam_instructions": "Steam: Rechtsklick > Eigenschaften > Allgemein > Startoptionen > Befehl einfügen.",
        "launcher_heroic_instructions": "Heroic: Spieleinstellungen > Umgebungsvariablen > WINEDLLOVERRIDES={method}=n,b",
        "launcher_lutris_instructions": "Lutris: Konfigurieren > Runner-Optionen > DLL-Overrides > '{method}' = 'n,b'",
        "launcher_bottles_instructions": "Bottles: Flasche > Einstellungen > Umgebungsvariablen > WINEDLLOVERRIDES={method}=n,b",
    },
    "fr": {
        "app_title": "DLSS Enabler pour Linux",
        "app_subtitle": "Gestionnaire universel d'upscaling et de génération d'images pour Proton / Wine",
        "core_checking": "Vérification du Core...",
        "core_ready": "● DLSS Enabler {ver} (Prêt)",
        "core_missing": "○ Non téléchargé",
        "btn_update_core": "Vérifier les mises à jour",
        "btn_download_core": "Télécharger",
        "btn_add_game": "+ Ajouter un jeu",
        "btn_refresh": "↻ Actualiser",
        "search_placeholder": "🔍 Rechercher parmi les jeux installés...",
        "filter_all": "Tous",
        "filter_steam": "Steam",
        "filter_heroic": "Heroic",
        "filter_lutris": "Lutris",
        "filter_custom": "Personnalisé",
        "filter_status_all": "Tous statuts",
        "filter_status_patched": "Installé",
        "filter_status_unpatched": "Non installé",
        "status_scanning": "Analyse des jeux sur Steam, Heroic, Lutris, Bottles...",
        "status_found": "{count} jeux trouvés.",
        "empty_title": "Sélectionnez un jeu",
        "empty_desc": "Choisissez un jeu dans la liste pour voir sa compatibilité et installer DLSS Enabler en un clic.",
        "badge_patched": "✓ Installé",
        "badge_unpatched": "Non installé",
        "badge_native_linux": "Linux natif",
        "target_exe_header": "EXÉCUTABLE CIBLE & DOSSIER",
        "btn_browse": "Parcourir...",
        "tips_header": "💡 Recommandations & Conseils:",
        "method_header": "MÉTHODE D'INJECTION DLSS ENABLER",
        "hook_proxy_label": "DLL Proxy (Hook):",
        "launch_options_header": "OPTIONS DE LANCEMENT PROTON RECOMMANDÉES",
        "btn_copy": "📋 Copier",
        "toast_copied": "✓ Options de lancement copiées dans le presse-papiers !",
        "btn_install": "⚡ Installer DLSS Enabler",
        "btn_reinstall": "⚡ Réinstaller / Mettre à jour",
        "btn_installing": "Installation...",
        "btn_uninstall": "↺ Désinstaller & Restaurer",
        "btn_open_folder": "📁 Ouvrir le dossier",
        "components_header": "COMPOSANTS INSTALLÉS",
        "no_components": "Aucun fichier DLSS Enabler actif.",
        "download_connecting": "Connexion à GitHub...",
        "download_complete": "Prêt ! DLSS Enabler est à jour.",
        "dialog_download_success_title": "DLSS Enabler prêt",
        "dialog_download_fail_title": "Échec du téléchargement",
        "dialog_download_fail_msg": "Impossible de télécharger les fichiers :\n{err}",
        "dialog_install_success_title": "Installation réussie",
        "dialog_install_success_msg": "DLSS Enabler a été installé avec succès !\n\nMéthode : {method}.dll\nCible : {target}\n\nOptions de lancement :\n{opts}",
        "dialog_install_fail_title": "Échec de l'installation",
        "dialog_uninstall_confirm_title": "Confirmer la désinstallation",
        "dialog_uninstall_confirm_msg": "Voulez-vous vraiment désinstaller DLSS Enabler de '{title}' ?\nLes fichiers originaux seront restaurés automatiquement.",
        "dialog_restored_title": "Restauré",
        "dialog_uninstall_notice_title": "Information",
        "dialog_select_game_folder": "Sélectionner le dossier du jeu",
        "dialog_select_game_exe": "Sélectionner l'exécutable",
        "launcher_steam_instructions": "Steam : Clic droit > Propriétés > Général > Options de lancement > Collez la commande.",
        "launcher_heroic_instructions": "Heroic : Paramètres du jeu > Variables d'environnement > WINEDLLOVERRIDES={method}=n,b",
        "launcher_lutris_instructions": "Lutris : Configurer > Options du runner > Remplacements DLL > '{method}' = 'n,b'",
        "launcher_bottles_instructions": "Bottles : Bouteille > Paramètres > Variables d'environnement > WINEDLLOVERRIDES={method}=n,b",
    },
    "es": {
        "app_title": "DLSS Enabler para Linux",
        "app_subtitle": "Gestor universal de reescalado y generación de fotogramas para Proton / Wine",
        "core_checking": "Comprobando Core...",
        "core_ready": "● DLSS Enabler {ver} (Listo)",
        "core_missing": "○ No descargado",
        "btn_update_core": "Buscar actualizaciones",
        "btn_download_core": "Descargar ahora",
        "btn_add_game": "+ Añadir juego",
        "btn_refresh": "↻ Actualizar",
        "search_placeholder": "🔍 Buscar juegos instalados...",
        "filter_all": "Todos",
        "filter_steam": "Steam",
        "filter_heroic": "Heroic",
        "filter_lutris": "Lutris",
        "filter_custom": "Personalizado",
        "filter_status_all": "Todos los estados",
        "filter_status_patched": "Solo instalados",
        "filter_status_unpatched": "No instalados",
        "status_scanning": "Buscando juegos en Steam, Heroic, Lutris, Bottles...",
        "status_found": "Se encontraron {count} juegos.",
        "empty_title": "Selecciona un juego",
        "empty_desc": "Elige un juego de la lista para ver su compatibilidad e instalar DLSS Enabler con un solo clic.",
        "badge_patched": "✓ Instalado",
        "badge_unpatched": "No instalado",
        "badge_native_linux": "Linux nativo",
        "target_exe_header": "EJECUTABLE Y DIRECTORIO OBJETIVO",
        "btn_browse": "Examinar...",
        "tips_header": "💡 Recomendaciones y Consejos:",
        "method_header": "MÉTODO DE INYECCIÓN DLSS ENABLER",
        "hook_proxy_label": "DLL Proxy (Hook):",
        "launch_options_header": "OPCIONES DE LANZAMIENTO PROTON RECOMENDADAS",
        "btn_copy": "📋 Copiar",
        "toast_copied": "✓ ¡Opciones de lanzamiento copiadas al portapapeles!",
        "btn_install": "⚡ Instalar DLSS Enabler",
        "btn_reinstall": "⚡ Reinstalar / Actualizar",
        "btn_installing": "Instalando...",
        "btn_uninstall": "↺ Desinstalar y Restaurar",
        "btn_open_folder": "📁 Abrir carpeta",
        "components_header": "COMPONENTES INSTALADOS",
        "no_components": "No hay archivos DLSS Enabler activos instalados.",
        "download_connecting": "Conectando con GitHub...",
        "download_complete": "¡Listo! DLSS Enabler está actualizado.",
        "dialog_download_success_title": "DLSS Enabler listo",
        "dialog_download_fail_title": "Descarga fallida",
        "dialog_download_fail_msg": "No se pudieron descargar los archivos:\n{err}",
        "dialog_install_success_title": "Instalación exitosa",
        "dialog_install_success_msg": "¡DLSS Enabler se ha instalado correctamente!\n\nMétodo: {method}.dll\nObjetivo: {target}\n\nOpciones de lanzamiento:\n{opts}",
        "dialog_install_fail_title": "Fallo en la instalación",
        "dialog_uninstall_confirm_title": "Confirmar desinstalación",
        "dialog_uninstall_confirm_msg": "¿Seguro que deseas eliminar DLSS Enabler de '{title}'?\nLos archivos originales se restaurarán automáticamente.",
        "dialog_restored_title": "Restaurado",
        "dialog_uninstall_notice_title": "Aviso de desinstalación",
        "dialog_select_game_folder": "Seleccionar carpeta del juego",
        "dialog_select_game_exe": "Seleccionar ejecutable",
        "launcher_steam_instructions": "Steam: Clic derecho > Propiedades > General > Parámetros de lanzamiento > Pega el comando.",
        "launcher_heroic_instructions": "Heroic: Ajustes del juego > Variables de entorno > WINEDLLOVERRIDES={method}=n,b",
        "launcher_lutris_instructions": "Lutris: Configurar > Opciones del runner > Reemplazos DLL > '{method}' = 'n,b'",
        "launcher_bottles_instructions": "Bottles: Botella > Ajustes > Variables de entorno > WINEDLLOVERRIDES={method}=n,b",
    },
    "ru": {
        "app_title": "DLSS Enabler для Linux",
        "app_subtitle": "Универсальный менеджер масштабирования и генерации кадров для Proton / Wine",
        "core_checking": "Проверка компонентов...",
        "core_ready": "● DLSS Enabler {ver} (Готов)",
        "core_missing": "○ Не загружено",
        "btn_update_core": "Проверить обновления",
        "btn_download_core": "Скачать сейчас",
        "btn_add_game": "+ Добавить игру",
        "btn_refresh": "↻ Обновить",
        "search_placeholder": "🔍 Поиск установленных игр...",
        "filter_all": "Все",
        "filter_steam": "Steam",
        "filter_heroic": "Heroic",
        "filter_lutris": "Lutris",
        "filter_custom": "Другие",
        "filter_status_all": "Все статусы",
        "filter_status_patched": "Только установленные",
        "filter_status_unpatched": "Не установленные",
        "status_scanning": "Сканирование игр в Steam, Heroic, Lutris, Bottles...",
        "status_found": "Найдено игр: {count}.",
        "empty_title": "Выберите игру",
        "empty_desc": "Выберите игру из списка для проверки совместимости и установки DLSS Enabler в один клик.",
        "badge_patched": "✓ Установлено",
        "badge_unpatched": "Не установлено",
        "badge_native_linux": "Нативная для Linux",
        "target_exe_header": "ИСПОЛНЯЕМЫЙ ФАЙЛ И ДИРЕКТОРИЯ",
        "btn_browse": "Обзор...",
        "tips_header": "💡 Рекомендации и подсказки:",
        "method_header": "МЕТОД ИНЪЕКЦИИ DLSS ENABLER",
        "hook_proxy_label": "Прокси DLL:",
        "launch_options_header": "РЕКОМЕНДУЕМЫЕ ПАРАМЕТРЫ ЗАПУСКА PROTON",
        "btn_copy": "📋 Копировать",
        "toast_copied": "✓ Параметры запуска скопированы в буфер обмена!",
        "btn_install": "⚡ Установить DLSS Enabler",
        "btn_reinstall": "⚡ Переустановить / Обновить",
        "btn_installing": "Установка...",
        "btn_uninstall": "↺ Удалить и восстановить",
        "btn_open_folder": "📁 Открыть папку",
        "components_header": "УСТАНОВЛЕННЫЕ КОМПОНЕНТЫ",
        "no_components": "Файлы DLSS Enabler не установлены.",
        "download_connecting": "Подключение к GitHub...",
        "download_complete": "Готово! DLSS Enabler обновлен.",
        "dialog_download_success_title": "DLSS Enabler готов",
        "dialog_download_fail_title": "Ошибка загрузки",
        "dialog_download_fail_msg": "Не удалось загрузить компоненты:\n{err}",
        "dialog_install_success_title": "Установка завершена",
        "dialog_install_success_msg": "DLSS Enabler успешно установлен!\n\nМетод: {method}.dll\nЦель: {target}\n\nПараметры запуска:\n{opts}",
        "dialog_install_fail_title": "Ошибка установки",
        "dialog_uninstall_confirm_title": "Подтверждение удаления",
        "dialog_uninstall_confirm_msg": "Удалить DLSS Enabler из '{title}'?\nОригинальные файлы будут восстановлены автоматически.",
        "dialog_restored_title": "Восстановлено",
        "dialog_uninstall_notice_title": "Уведомление",
        "dialog_select_game_folder": "Выберите папку с игрой",
        "dialog_select_game_exe": "Выберите исполняемый файл",
        "launcher_steam_instructions": "Steam: ПКМ по игре > Свойства > Общие > Параметры запуска > Вставьте команду.",
        "launcher_heroic_instructions": "Heroic: Настройки игры > Переменные окружения > WINEDLLOVERRIDES={method}=n,b",
        "launcher_lutris_instructions": "Lutris: Настроить > Параметры runner > Переопределения DLL > '{method}' = 'n,b'",
        "launcher_bottles_instructions": "Bottles: Бутылка > Настройки > Переменные окружения > WINEDLLOVERRIDES={method}=n,b",
    },
}

SUPPORTED_LANGUAGES = [
    ("en", "🇬🇧 English"),
    ("tr", "🇹🇷 Türkçe"),
    ("de", "🇩🇪 Deutsch"),
    ("fr", "🇫🇷 Français"),
    ("es", "🇪🇸 Español"),
    ("ru", "🇷🇺 Русский"),
]


class I18nManager:
    _instance: Optional[I18nManager] = None

    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or (Path.home() / ".config" / "dlss-enabler-linux")
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.settings_file = self.config_dir / "settings.json"
        self.current_lang = self._detect_default_language()
        self._listeners: list[Callable[[], None]] = []

    @classmethod
    def get_instance(cls) -> I18nManager:
        if cls._instance is None:
            cls._instance = I18nManager()
        return cls._instance

    def _detect_default_language(self) -> str:
        """Read saved language or detect from system locale."""
        if self.settings_file.exists():
            try:
                with open(self.settings_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    saved = data.get("language")
                    if saved in TRANSLATIONS:
                        return saved
            except Exception:
                pass

        # Auto-detect from system environment
        lang_env = os.environ.get("LANG", "").lower()
        if "tr" in lang_env:
            return "tr"
        elif "de" in lang_env:
            return "de"
        elif "fr" in lang_env:
            return "fr"
        elif "es" in lang_env:
            return "es"
        elif "ru" in lang_env:
            return "ru"
        return "en"

    def set_language(self, lang_code: str) -> None:
        if lang_code in TRANSLATIONS and lang_code != self.current_lang:
            self.current_lang = lang_code
            self._save_settings()
            for cb in self._listeners:
                try:
                    cb()
                except Exception:
                    pass

    def add_language_listener(self, callback: Callable[[], None]) -> None:
        self._listeners.append(callback)

    def _save_settings(self) -> None:
        data = {}
        if self.settings_file.exists():
            try:
                with open(self.settings_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = {}
        data["language"] = self.current_lang
        try:
            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def t(self, key: str, **kwargs) -> str:
        """Translate key to current language with optional formatting."""
        lang_dict = TRANSLATIONS.get(self.current_lang, TRANSLATIONS["en"])
        val = lang_dict.get(key) or TRANSLATIONS["en"].get(key, key)
        if kwargs:
            try:
                return val.format(**kwargs)
            except Exception:
                return val
        return val


def t(key: str, **kwargs) -> str:
    """Shortcut helper function."""
    return I18nManager.get_instance().t(key, **kwargs)
