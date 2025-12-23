import random
import os
import time
import json
from colorama import Fore, Style, init


# ---- Config
init(autoreset=True)

MONEY_FILE = "_money.json"
CARDS_FILE = "_cards.json"
STARTING_MONEY = 1000

GREEN = Fore.GREEN
RED = Fore.RED
RESET = Style.RESET_ALL


# ---- The card class
class Card:
    def __init__(self, rank, suit, assets):
        self.rank = rank
        self.suit = suit
        self.assets = assets
        self.value = self._get_value()
        self.color = RED if suit in ["Hearts", "Diamonds"] else Fore.CYAN
        self.symbol = assets["suits"][suit]

    def _get_value(self):
        if self.rank in ["J", "K", "Q"]:
            return 10
        if self.rank == "A":
            return 11
        return int(self.rank)

    def render_lines(self):
        """Return the ASCII art"""
        lines = []
        for line in self.assets["template"]:
            formatted = line.format(rank=self.rank, suit=self.symbol)
            lines.append(f"{self.color}{formatted}{RESET}")
        return lines

    @staticmethod
    def render_hidden(assets):
        return [line for line in assets["hidden"]]


# --- The supplier of cards.
class Deck:
    def __init__(self, assets):
        self.assets = assets
        self.cards = []
        self.build()

    def build(self):
        suits = ["Hearts", "Diamonds", "Clubs", "Spades"]
        ranks = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
        self.cards = [Card(r, s, self.assets) for s in suits for r in ranks]
        self.shuffle()

    def shuffle(self):
        random.shuffle(self.cards)

    def deal(self):
        """Removes top card. Reshuffles if empty."""
        if not self.cards:
            self.build()
        return self.cards.pop()

    def remaining(self):
        return len(self.cards)


# ---- Hand logic
class Hand:
    def __init__(self, name):
        self.name = name
        self.cards = []

    def add(self, card):
        self.cards.append(card)

    def get_score(self):
        score = sum(card.value for card in self.cards)
        aces = sum(1 for card in self.cards if card.rank == "A")

        while score > 21 and aces > 0:
            score -= 10
            aces -= 1
        return score

    def display(self, hide_first=False):
        """Handles the side-by-side printing logic."""
        if not self.cards:
            return

        lines = ["", "", "", "", ""]

        for i, card in enumerate(self.cards):
            if i == 0 and hide_first:
                card_lines = Card.render_hidden(card.assets)
            else:
                card_lines = card.render_lines()

            # Stitch them together
            for j in range(5):
                lines[j] += card_lines[j] + " "

        print(f"\n{self.name} ({'?' if hide_first else self.get_score()}):")
        for line in lines:
            print(line)


# ---- Controller


class BlackjackGame:
    def __init__(self):
        self.assets = self._load_assets()
        self.deck = Deck(self.assets)
        self.balance = self._load_money()

    def _load_assets(self):
        try:
            with open(CARDS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"{RED} [ERROR]: {RESET} _cards.json not found.")
            exit()

    def _load_money(self):
        if not os.path.exists(MONEY_FILE):
            return STARTING_MONEY
        try:
            with open(MONEY_FILE, "r") as f:
                # Handle empty file check
                content = f.read()
                if not content:
                    return STARTING_MONEY

                data = json.loads(content)

                # Safety check: Ensure data is a dict
                if isinstance(data, dict):
                    return data.get("balance", STARTING_MONEY)
                else:
                    return STARTING_MONEY

        except (FileNotFoundError, json.JSONDecodeError):
            print(f"{RED} [ERROR]: {RESET} _money.json corrupted or empty. Resetting.")
            return STARTING_MONEY

    def save_money(self):
        with open(MONEY_FILE, "w") as f:
            json.dump({"balance": self.balance}, f)

    def get_bet(self):
        while True:
            try:
                bet = int(input(f"\nBalance ${self.balance}. Place bet: "))
                if 0 < bet <= self.balance:
                    return bet
                print(f"{RED}Invalid bet.{RESET}")
            except ValueError:
                print("Enter a number.")

    def play_round(self):
        os.system("cls" if os.name == "nt" else "clear")
        print(f"{Fore.YELLOW}=== OOP BLACKJACK ==={Style.RESET_ALL}")

        if self.deck.remaining() < 10:
            print(f"{Fore.MAGENTA}Shuffling Deck...{Style.RESET_ALL}")
            self.deck.build()

        bet = self.get_bet()

        # Init Hands
        player = Hand("Player")
        dealer = Hand("Dealer")

        # Deal Initial
        player.add(self.deck.deal())
        dealer.add(self.deck.deal())
        player.add(self.deck.deal())
        dealer.add(self.deck.deal())

        # --- Player Turn ---
        playing = True
        while playing:
            os.system("cls" if os.name == "nt" else "clear")
            dealer.display(hide_first=True)
            player.display()

            if player.get_score() >= 21:
                playing = False
            else:
                choice = input("\n[H]it or [S]tand? ").lower()
                if choice == "h":
                    player.add(self.deck.deal())
                else:
                    playing = False

        # --- Dealer Turn ---
        p_score = player.get_score()
        if p_score <= 21:
            print(f"\n{Fore.MAGENTA}Dealer reveals...{RESET}")
            while dealer.get_score() < 17:
                time.sleep(1)
                dealer.add(self.deck.deal())

                os.system("cls" if os.name == "nt" else "clear")
                dealer.display()
                player.display()

        # --- Settlement ---
        d_score = dealer.get_score()
        self.settle_bet(bet, p_score, d_score)
        self.save_money()

    def settle_bet(self, bet, p_score, d_score):
        print(f"\n{Fore.YELLOW}--- RESULT ---{RESET}")
        if p_score > 21:
            print(f"{RED}BUST! You lost ${bet}.{RESET}")
            self.balance -= bet
        elif d_score > 21:
            print(f"{GREEN}DEALER BUST! You won ${bet}.{RESET}")
            self.balance += bet
        elif p_score > d_score:
            print(f"{GREEN}VICTORY! You won ${bet}.{RESET}")
            self.balance += bet
        elif p_score < d_score:
            print(f"{RED}DEFEAT. You lost ${bet}.{RESET}")
            self.balance -= bet
        else:
            print(f"{Fore.CYAN}PUSH. Money returned.{RESET}")

    def start(self):
        while self.balance > 0:
            self.play_round()
            if input("\nPlay again? (y/n): ").lower() != "y":
                break
        print("Game Over.")


if __name__ == "__main__":
    game = BlackjackGame()
    game.start()
