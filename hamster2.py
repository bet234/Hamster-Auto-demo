from requests import post
from time import time, sleep
import random
from datetime import datetime, timedelta
import requests
from requests.exceptions import RequestException

class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[0;33m'
    PURPLE = '\033[0;35m'
    CYAN = '\033[0;36m'
    BLUE = '\033[0;34m'
    RESET = '\033[0m'

def get_current_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def wait_for_cooldown(cooldown_seconds):
    hours, remainder = divmod(cooldown_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    end_time = datetime.now() + timedelta(seconds=cooldown_seconds)
    print(f"{Colors.YELLOW}[{get_current_time()}] Upgrade is on cooldown. Waiting for {hours} hours, {minutes} minutes, and {seconds} seconds...{Colors.RESET}")
    sleep(cooldown_seconds)
    print(f"{Colors.CYAN}[{get_current_time()}] Next purchase can be made at: {end_time.strftime('%Y-%m-%d %H:%M:%S')}{Colors.RESET}")

def format_number(number):
    if number >= 1_000_000:
        return f"{number / 1_000_000:.1f}m"
    elif number >= 1_000:
        return f"{number / 1_000:.1f}k"
    else:
        return str(number)

def get_authorization():
    return input(f"{Colors.GREEN}[{get_current_time()}] Enter Authorization [{Colors.CYAN}Example: {Colors.YELLOW}Bearer 171852....{Colors.GREEN}]: {Colors.RESET}")

def get_user_choice():
    print(f"{Colors.CYAN}[{get_current_time()}] Choose mode:{Colors.RESET}")
    print(f"{Colors.YELLOW}1. Buy the best card immediately (skip cooldown waiting){Colors.RESET}")
    print(f"{Colors.YELLOW}2. Buy only the best card and wait for cooldown{Colors.RESET}")
    choice = input(f"{Colors.GREEN}[{get_current_time()}] Enter your choice (1 or 2): {Colors.RESET}")
    return choice.strip()

def purchase_upgrade(authorization, upgrade_id):
    timestamp = int(time() * 1000)
    url = "https://api.hamsterkombatgame.io/interlude/buy-upgrade"
    headers = {
        "Content-Type": "application/json",
        "Authorization": authorization,
        "Origin": "https://hamsterkombatgame.io",
        "Referer": "https://hamsterkombatgame.io/"
    }
    data = {
        "upgradeId": upgrade_id,
        "timestamp": timestamp
    }
    response = post(url, headers=headers, json=data)
    if response.status_code == 200:
        print(f"{Colors.GREEN}[{get_current_time()}] Upgrade successfully purchased!{Colors.RESET}")
        return True
    else:
        print(f"{Colors.RED}[{get_current_time()}] Failed to purchase upgrade. Error: {response.text}{Colors.RESET}")
        return False

def get_upgrades(authorization):
    url = "https://api.hamsterkombatgame.io/interlude/upgrades-for-buy"
    headers = {
        'Authorization': authorization,
        'Origin': 'https://hamsterkombatgame.io',
        'Referer': 'https://hamsterkombatgame.io/',
    }
    response = post(url, headers=headers)
    if response.status_code == 200:
        return response.json().get("upgradesForBuy", [])
    else:
        print(f"{Colors.RED}[{get_current_time()}] Failed to retrieve upgrades. Error: {response.text}{Colors.RESET}")
        return []

def filter_upgrades(upgrades):
    return [u for u in upgrades if not u["isExpired"] and u["isAvailable"] and u["price"] > 0]

def get_best_upgrade(upgrades):
    valid_upgrades = filter_upgrades(upgrades)
    if not valid_upgrades:
        return None
    # Prioritize based on profitPerHourDelta/price 
    return max(valid_upgrades, key=lambda u: u["profitPerHourDelta"] / u["price"])

def get_account_info(authorization):
    url = "https://api.hamsterkombatgame.io/interlude/sync"
    headers = {
        'Authorization': authorization,
        'Origin': 'https://hamsterkombatgame.io',
        'Referer': 'https://hamsterkombatgame.io/',
    }
    try:
        response = requests.post(url, headers=headers)
        response.raise_for_status()  # Raise an exception for bad status codes

        balance_diamonds = response.json().get("interludeUser", {}).get("balanceDiamonds", 0)
        return balance_diamonds
    except RequestException as e:
        print(f"{Colors.RED}[{get_current_time()}] Failed to retrieve account info. Error: {e}{Colors.RESET}")
        return 0 

def main():
    authorization = get_authorization()
    
    min_balance = float(input(f"{Colors.YELLOW}[{get_current_time()}] Set minimum balance to stop purchasing (just for reference): {Colors.RESET}"))

    user_choice = get_user_choice()

    purchased_upgrades = []  # Track purchased upgrades

    while True:
        current_balance = get_account_info(authorization)
        print(f"{Colors.CYAN}[{get_current_time()}] Current balance: {format_number(current_balance)}{Colors.RESET}")

        upgrades = get_upgrades(authorization)
        best_upgrade = get_best_upgrade(upgrades)

        if best_upgrade:
            print(f"{Colors.GREEN}[{get_current_time()}] Best Upgrade: {Colors.YELLOW}{best_upgrade['name']} (ID: {best_upgrade['id']}, Price: {format_number(best_upgrade['price'])}){Colors.RESET}")
            
            if "cooldownSeconds" in best_upgrade:
                if best_upgrade["cooldownSeconds"] > 0:
                    if user_choice == "1":
                        print(f"{Colors.PURPLE}[{get_current_time()}] Skipping cooldown and trying to buy another available upgrade...{Colors.RESET}")
                        upgrades.remove(best_upgrade)
                        best_upgrade = get_best_upgrade(upgrades)
                        
                        if not best_upgrade or "cooldownSeconds" in best_upgrade and best_upgrade["cooldownSeconds"] > 0:
                            print(f"{Colors.RED}[{get_current_time()}] No other upgrades available without cooldown.{Colors.RESET}")
                            print(f"{Colors.YELLOW}[{get_current_time()}] Sleeping for 60 minutes...{Colors.RESET}")
                            sleep(3600)  # Sleep for 60 minutes and retry
                        else:
                            if purchase_upgrade(authorization, best_upgrade["id"]):
                                print(f"{Colors.GREEN}[{get_current_time()}] Purchased: {best_upgrade['name']} (ID: {best_upgrade['id']}){Colors.RESET}")
                                purchased_upgrades.append(best_upgrade["id"])
                    elif user_choice == "2":
                        wait_for_cooldown(best_upgrade["cooldownSeconds"])
                        if purchase_upgrade(authorization, best_upgrade["id"]):
                            print(f"{Colors.GREEN}[{get_current_time()}] Purchased: {best_upgrade['name']} (ID: {best_upgrade['id']}){Colors.RESET}")
                            purchased_upgrades.append(best_upgrade["id"])
            else:
                if purchase_upgrade(authorization, best_upgrade["id"]):
                    print(f"{Colors.GREEN}[{get_current_time()}] Purchased: {best_upgrade['name']} (ID: {best_upgrade['id']}){Colors.RESET}")
                    purchased_upgrades.append(best_upgrade["id"])

            wait_time = random.randint(5, 7)
            print(f"{Colors.CYAN}[{get_current_time()}] Waiting for {wait_time} seconds before the next purchase...{Colors.RESET}")
            sleep(wait_time)
        else:
            print(f"{Colors.RED}[{get_current_time()}] No valid upgrades available at this moment. Sleeping for 60 minutes before retrying...{Colors.RESET}")
            print(f"{Colors.YELLOW}[{get_current_time()}] Sleeping for 60 minutes...{Colors.RESET}")
            sleep(3600)  # Sleep for 60 minutes and then retry

if __name__ == "__main__":
    main()
