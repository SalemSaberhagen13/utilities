#!/usr/bin/env python3
import asyncio
import json
import os
import random
from pathlib import Path

CONFIG_PATH = Path(os.path.expanduser("~/.config/awww_rotator/config.json"))

# Global state
last_mtime = 0
current_config = {}

# Global event for notify when config is changed
config_changed_event = asyncio.Event()


def load_config() -> bool:
    """Reload JSON only if mtime is changed. True if reloaded"""
    global last_mtime, current_config

    try:
        mtime = os.path.getmtime(CONFIG_PATH)
    except FileNotFoundError:
        return False

    if mtime != last_mtime:
        try:
            with open(CONFIG_PATH, "r") as f:
                current_config = json.load(f)
            last_mtime = mtime
            print("Porca madonna, configurazione ricaricata!")
            return True
        except json.JSONDecodeError as e:
            print(f"Hai scassato il JSON, dio cancaro: {e}")
            last_mtime = mtime
    return False


def get_wallpapers(directory_str: str, extensions: list) -> list:
    directory = Path(os.path.expanduser(directory_str))
    if not directory.exists():
        return []

    exts = {e.lower() for e in extensions}
    return [p for p in directory.iterdir() if p.suffix.lower() in exts and p.is_file()]


async def set_wallpaper(output_name: str, image_path: Path, anim_conf: dict):
    """Execute awww in async so the main thread does not get blocked"""
    cmd = [
        "awww",
        "img",
        str(image_path),
        "-o",
        output_name,
        "--transition-type",
        str(anim_conf.get("type", "random")),
        "--transition-fps",
        str(anim_conf.get("fps", 60)),
        "--transition-step",
        str(anim_conf.get("step", 90)),
    ]

    # Async subprocess
    process = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL
    )
    await process.wait()

    if process.returncode == 0:
        print(f"[{output_name}] Daghe vecio: {image_path.name}")
    else:
        print(
            f"[{output_name}] Fallimento critico di awww (codice {process.returncode})"
        )


async def monitor_loop(output_name: str):
    """Isolated loop for each screen. Screen desktop wallpaper changes in base of its own config."""
    print(f"Avviato loop per il monitor {output_name}")

    while True:
        # Se hanno rimosso il monitor dal config al volo, dormi e aspetta che torni
        if output_name not in current_config:
            await asyncio.sleep(5)
            continue

        conf = current_config[output_name]
        wallpapers = get_wallpapers(conf["wallpaper_dir"], conf["valid_extensions"])

        if wallpapers:
            cucchiaio = random.choice(wallpapers)
            await set_wallpaper(output_name, cucchiaio, conf["animation"])
        else:
            print(f"[{output_name}] Cartella vuota o inesistente. Correggi il JSON.")

        # Attesa intelligente per questo specifico monitor
        elapsed = 0
        interval = conf.get("interval_sec", 300)

        while elapsed < interval:
            # Aspetta 1 secondo, oppure si sveglia istantaneamente se l'evento globale scatta
            try:
                await asyncio.wait_for(config_changed_event.wait(), timeout=1.0)
                # Se arriviamo qui, l'evento è stato attivato (la config è cambiata)
                if output_name in current_config:
                    new_interval = current_config[output_name].get("interval_sec", 300)
                    if new_interval != interval:
                        interval = new_interval
                        if elapsed >= interval:
                            break  # Rompi il ciclo di attesa e cambia subito sfondo
            except asyncio.TimeoutError:
                pass  # Timeout raggiunto (passato 1 secondo normale)

            elapsed += 1


async def config_watcher():
    """Checks config file each second"""
    while True:
        if load_config():
            # Sveglia tutti i monitor loop che stanno aspettando
            config_changed_event.set()
            # Resetta l'evento in modo che possa essere attivato di nuovo
            await asyncio.sleep(0.1)
            config_changed_event.clear()
        await asyncio.sleep(1)


async def main():
    if not CONFIG_PATH.parent.exists():
        CONFIG_PATH.parent.mkdir(parents=True)
        # Configurazione di default
        default_conf = {
            "DP-3": {
                "interval_sec": 300,
                "wallpaper_dir": "~/Pictures/vapor",
                "valid_extensions": [".jpg", "png"],
                "animation": {},
            },
            "DP-2": {
                "interval_sec": 300,
                "wallpaper_dir": "~/Pictures/vapor/vert",
                "valid_extensions": [".jpg", "png"],
                "animation": {},
            },
        }
        with open(CONFIG_PATH, "w") as f:
            json.dump(default_conf, f, indent=4)

    # Loads first time
    load_config()

    # Get all monitors
    monitors = list(current_config.keys())

    # Creates a task for the config watcher and one for each monitor
    tasks = [asyncio.create_task(config_watcher())]
    for mon in monitors:
        tasks.append(asyncio.create_task(monitor_loop(mon)))

    # Waits until forever (don't fucking stop it)
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nSpento. Buonanotte e prega la madonna.")
