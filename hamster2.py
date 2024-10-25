from requests import Session, RequestException
from time import sleep, time
from datetime import datetime, timedelta
import random
import os
import getpass
from typing import List, Dict, Optional, Any

class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[0;33m'
    PURPLE = '\033[0;35m'
    CYAN = '\033[0;36m'
    BLUE = '\033[0;34m'
    RESET = '\033[0m'

def get_current_time() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def wait_for_cooldown(cooldown_seconds: int):
    end_time = datetime.now() + timedelta(seconds=cooldown_seconds)
    while cooldown_seconds > 0:
        hours, remainder = divmod(cooldown_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        print(f"{Colors.YELLOW}[{get_current_time()}] Waiting {hours}h {minutes}m {seconds}s until next upgrade...{Colors.RESET}", end='\r')
        sleep(1)
        cooldown_seconds -= 1
    print(f"\n{Colors.CYAN}[{get_current_time()}] Cooldown over. Ready for next purchase at {end_time.strftime('%Y-%m-%d %H:%M:%S')}{Colors.RESET}")

def format_number(number: int) -> str:
    if number >= 1_000_000:
        return f"{number / 1_000_000:.1f}m"
    elif number >= 1_000:
        return f"{number / 1_000:.1f}k"
    else:
        return str(number)

def get_authorization() -> str:
    auth_token = input(f"{Colors.GREEN}[{get_current_time()}] Enter Authorization Token (Bearer Token): {Colors.RESET}")
    return auth_token

def get_user_choice() -> str:
    print(f"{Colors.CYAN}[{get_current_time()}] Choose mode:{Colors.RESET}")
    print(f"{Colors.YELLOW}1. Buy the best card immediately (skip cooldown waiting){Colors.RESET}")
    print(f"{Colors.YELLOW}2. Buy only the best card and wait for cooldown{Colors.RESET}")
    choice = input(f"{Colors.GREEN}[{get_current_time()}] Enter your choice (1 or 2): {Colors.RESET}")
    return choice.strip()

def purchase_upgrade(session: Session, authorization: str, upgrade_id: int) -> bool:
    url = "https://api.hamsterkombatgame.io/interlude/buy-upgrade"
    headers = {
        "Content-Type": "application/json",
        "Authorization": authorization,
    }
    data = {"upgradeId": upgrade_id, "timestamp": int(time() * 1000)}
    try:
        response = session.post(url, headers=headers, json=data, timeout=10)
        response.raise_for_status()
        print(f"{Colors.GREEN}[{get_current_time()}] Upgrade successfully purchased!{Colors.RESET}")
        return True
    except RequestException as e:
        print(f"{Colors.RED}[{get_current_time()}] Failed to purchase upgrade. Error: {str(e)}{Colors.RESET}")
        return False

def get_upgrades(session: Session, authorization: str) -> List[Dict[str, Any]]:
    url = "https://api.hamsterkombatgame.io/interlude/upgrades-for-buy"
    headers = {'Authorization': authorization}
    try:
        response = session.post(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json().get("upgradesForBuy", [])
    except RequestException as e:
        print(f"{Colors.RED}[{get_current_time()}] Failed to retrieve upgrades. Error: {str(e)}{Colors.RESET}")
        return []

def filter_upgrades(upgrades: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [u for u in upgrades if not u["isExpired"] and u["isAvailable"] and u["price"] > 0]

def get_best_upgrade(upgrades: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    valid_upgrades = filter_upgrades(upgrades)
    return max(valid_upgrades, key=lambda u: u["profitPerHourDelta"] / u["price"], default=None)

def main():
    authorization = get_authorization()
    min_balance = float(input(f"{Colors.YELLOW}[{get_current_time()}] Set minimum balance to stop purchasing (just for reference): {Colors.RESET}"))
    user_choice = get_user_choice()

    with Session() as session:
        while True:
            upgrades = get_upgrades(session, authorization)
            # Sort upgrades by value-to-price ratio, in descending order
            sorted_upgrades = sorted(filter_upgrades(upgrades), key=lambda u: u["profitPerHourDelta"] / u["price"], reverse=True)

            purchased = False  # Flag to check if a purchase was made

            for upgrade in sorted_upgrades:
                print(f"{Colors.GREEN}[{get_current_time()}] Checking Upgrade: {Colors.YELLOW}{upgrade['name']} (ID: {upgrade['id']}, Price: {format_number(upgrade['price'])}){Colors.RESET}")

                # Safely get cooldownSeconds, defaulting to 0 if the key is missing
                cooldown_seconds = upgrade.get("cooldownSeconds", 0)

                # Check if this upgrade is on cooldown
                if cooldown_seconds > 0:
                    if user_choice == "1":
                        # Skip this upgrade if on cooldown and user chose to skip
                        print(f"{Colors.PURPLE}[{get_current_time()}] Upgrade {upgrade['name']} is on cooldown, skipping...{Colors.RESET}")
                        continue
                    elif user_choice == "2":
                        # Wait out cooldown if user chose to wait
                        print(f"{Colors.YELLOW}[{get_current_time()}] Upgrade {upgrade['name']} is on cooldown. Waiting for {cooldown_seconds} seconds...{Colors.RESET}")
                        wait_for_cooldown(cooldown_seconds)

                # Attempt to purchase the upgrade
                if purchase_upgrade(session, authorization, upgrade["id"]):
                    print(f"{Colors.GREEN}[{get_current_time()}] Successfully purchased: {upgrade['name']} (ID: {upgrade['id']}){Colors.RESET}")
                    purchased = True
                    break  # Exit loop after successful purchase

            # If no purchase was made, wait for 2 hours
            if not purchased:
                print(f"{Colors.RED}[{get_current_time()}] No valid upgrades available at this moment. Waiting for 2 hours...{Colors.RESET}")
                sleep(2 * 3600)  # Sleep for 2 hours (2 * 3600 seconds)
                continue  # Continue the loop after sleeping

            # Wait a random interval before checking for the next upgrade
            wait_time = random.randint(5, 7)
            print(f"{Colors.CYAN}[{get_current_time()}] Waiting {wait_time}s before the next purchase...{Colors.RESET}")
            sleep(wait_time)

if __name__ == "__main__":
    main()
