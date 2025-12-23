import random
import os
import json
import time
from colorama import Fore, Style, init


# ---- Config

init(autoreset=True)

MONEY_FILE = "_money.json"
CARDS_FILE = "_cards.json"
STARTING_MONEY = 1000

GREEN = Fore.GREEN
RED = Fore.RED
RESET = Style.RESET_ALL


def load_assets():
    try:
        with open(CARDS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"{RED} [ERROR]: {RESET} _cards.json not found.")
        exit()


ASSETS = load_assets()


# ---- Banking System
def load_money():
    if not os.path.exists(MONEY_FILE):
        return STARTING_MONEY
    try:
        with open(MONEY_FILE, "r") as f:
            # Handle empty file check
            content = f.read()
            if not content:
                return STARTING_MONEY

            data = json.loads(content)

            # Safety check: Ensure data is actually a dictionary
            if isinstance(data, dict):
                return data.get("balance", STARTING_MONEY)
            else:
                return STARTING_MONEY

    except (FileNotFoundError, json.JSONDecodeError):
        print(f"{RED} [ERROR]: {RESET} _money.json corrupted or empty. Resetting.")
        return STARTING_MONEY


def save_money(amount):
    with open(MONEY_FILE, "w") as f:
        json.dump({"balance": amount}, f)


# ---- The card-deck logic
def create_deck():
    """Creates a standard 52-deck"""
    suits = ["Hearts", "Diamonds", "Clubs", "Spades"]
    ranks = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
    deck = []
    for suit in suits:
        for rank in ranks:
            deck.append((rank, suit))
    random.shuffle(deck)
    return deck


def get_card_value(rank):
    if rank in ["J", "Q", "K"]:
        return 10
    if rank == "A":
        return 11
    return int(rank)


# ---- Visual Engine
def render_hand(hand, hidden=False):
    """
    Prints cards side-by-side using the JSON template.
    hand: List of tuples [('A', 'Hearts'), ('10', 'Spades')]
    """
    if not hand:
        return

    lines = ["", "", "", "", ""]
    template = ASSETS["template"]
    hidden_card = ASSETS["hidden"]
    suit_symbols = ASSETS["suits"]

    for i, (rank, suit) in enumerate(hand):
        # If it's the dealer's first card and hidden is True
        if i == 0 and hidden:
            for j, line in enumerate(hidden_card):
                lines[j] += line + " "
        else:
            # Color logic
            color = Fore.RED if suit in ["Hearts", "Diamonds"] else Fore.CYAN
            symbol = suit_symbols[suit]

            # Format the template
            for j, line in enumerate(template):
                formatted_line = line.format(rank=rank, suit=symbol)
                lines[j] += color + formatted_line + Style.RESET_ALL + " "

    for line in lines:
        print(line)


# ---- Core logic
def calc_score(hand):
    score = 0
    aces = 0
    for rank, suit in hand:
        val = get_card_value(rank)
        score += val
        if rank == "A":
            aces += 1

    while score > 21 and aces > 0:
        score -= 10
        aces -= 1
    return score


def play_round(deck, balance):
    os.system("cls" if os.name == "nt" else "clear")
    print(f"{GREEN}--- BLACKJACK (INTERMEDIATE) ---{RESET}")
    print(f"Current Balance: ${balance}")
    print(f"Cards in Shoe: {len(deck)}")

    # 1 Betting
    while True:
        try:
            bet = int(input("Place your bet: "))
            if bet > balance:
                print(f"{Fore.RED}You don't have enough money!{Style.RESET_ALL}")
            elif bet <= 0:
                print("Bet must be positive")
            else:
                break
        except ValueError:
            print("Pleace enter a number.")

    # 2 Dealing cards
    if len(deck) < 10:
        print("Shuffling new deck...")
        deck = create_deck()

    player_hand = [deck.pop(), deck.pop()]
    dealer_hand = [deck.pop(), deck.pop()]

    # 3. Player Turn
    game_over = False
    while not game_over:
        os.system("cls" if os.name == "nt" else "clear")
        print("Dealer's Hand:")
        render_hand(dealer_hand, hidden=True)  # Hide first card

        print(f"\nYour Hand ({calc_score(player_hand)}):")
        render_hand(player_hand)

        user_score = calc_score(player_hand)

        if user_score == 21:
            print(f"{Fore.GREEN}BLACKJACK!{Style.RESET_ALL}")
            game_over = True
        elif user_score > 21:
            print(f"{Fore.RED}BUST!{Style.RESET_ALL}")
            game_over = True
        else:
            choice = input("\n[H]it or [S]tand? ").lower()
            if choice == "h":
                player_hand.append(deck.pop())
            else:
                game_over = True

    # 4. Dealer Turn
    user_score = calc_score(player_hand)
    dealer_score = calc_score(dealer_hand)

    # Only play dealer if player didn't bust
    if user_score <= 21:
        print(f"\n{Fore.MAGENTA}Dealer reveals...{Style.RESET_ALL}")
        while dealer_score < 17:
            time.sleep(1)
            dealer_hand.append(deck.pop())
            dealer_score = calc_score(dealer_hand)

            # Show update
            os.system("cls" if os.name == "nt" else "clear")
            print("Dealer's Hand:")
            render_hand(dealer_hand)
            print(f"\nYour Hand ({user_score}):")
            render_hand(player_hand)

    # 5. Settlement
    print(f"\n{Fore.YELLOW}--- FINAL RESULTS ---{Style.RESET_ALL}")
    print(f"You: {user_score} | Dealer: {dealer_score}")

    if user_score > 21:
        print(f"{Fore.RED}You Bust! You lost ${bet}.{Style.RESET_ALL}")
        balance -= bet
    elif dealer_score > 21:
        print(f"{Fore.GREEN}Dealer Busts! You won ${bet}.{Style.RESET_ALL}")
        balance += bet
    elif user_score > dealer_score:
        print(f"{Fore.GREEN}You Win! You won ${bet}.{Style.RESET_ALL}")
        balance += bet
    elif user_score == dealer_score:
        print(f"{Fore.CYAN}Push (Draw). Money returned.{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}Dealer Wins. You lost ${bet}.{Style.RESET_ALL}")
        balance -= bet

    save_money(balance)
    return deck, balance


# --- Main Loop ---
if __name__ == "__main__":
    current_deck = create_deck()
    current_balance = load_money()

    while True:
        if current_balance <= 0:
            print(f"\n{Fore.RED}You are bankrupt! Resetting game...{Style.RESET_ALL}")
            current_balance = STARTING_MONEY
            save_money(current_balance)

        current_deck, current_balance = play_round(current_deck, current_balance)

        if input("\nPlay again? (y/n): ").lower() != "y":
            print("Cash out: ${}".format(current_balance))
            break
