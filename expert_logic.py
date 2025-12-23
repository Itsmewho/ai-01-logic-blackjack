import random
import time
from colorama import Fore, Style, init

init(autoreset=True)

# --- Config ---
# Casinos use a "Shoe" of 6 decks to discourage counting.
NUM_DECKS = 6
STARTING_MONEY = 5000
MIN_BET = 50


# --- 1. The Assets  ---
class Card:
    def __init__(self, rank, suit):
        self.rank = rank
        self.suit = suit
        self.value = self._get_value()
        self.count_value = self._get_count_value()

    def _get_value(self):
        if self.rank in ["J", "Q", "K"]:
            return 10
        if self.rank == "A":
            return 11
        return int(self.rank)

    def _get_count_value(self):
        # The Hi-Lo Logic
        if self.value <= 6:
            return 1  # 2, 3, 4, 5, 6
        if self.value >= 10:
            return -1  # 10, J, Q, K, A
        return 0  # 7, 8, 9

    def __repr__(self):
        # Simple text representation for the log
        return f"{self.rank}{self.suit[0]}"


class Shoe:
    """A collection of 6 Decks mixed together."""

    def __init__(self):
        self.cards = []
        self.build()

    def build(self):
        suits = ["Hearts", "Diamonds", "Clubs", "Spades"]
        ranks = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
        self.cards = [
            Card(r, s) for _ in range(NUM_DECKS) for s in suits for r in ranks
        ]
        self.shuffle()

    def shuffle(self):
        random.shuffle(self.cards)

    def deal(self):
        if not self.cards:
            self.build()
        return self.cards.pop()

    def decks_remaining(self):
        # Round to nearest 0.5 deck for accurate math
        return max(len(self.cards) / 52, 0.5)


# --- 2. The Brain (Card Counter) ---
class CardCounter:
    """
    Observer Class.
    It sits at the table and watches every card dealt.
    """

    def __init__(self):
        self.running_count = 0
        self.true_count = 0

    def observe(self, card):
        """Called whenever a card is revealed on table."""
        self.running_count += card.count_value

    def update_true_count(self, decks_remaining):
        # True Count = Running Count / Decks Remaining
        self.true_count = self.running_count / decks_remaining

    def get_bet_suggestion(self):
        """
        Betting Strategy:
        If True Count is <= 1: Bet Minimum.
        If True Count is > 1: Bet (True Count - 1) * Unit.
        """
        if self.true_count <= 1:
            return MIN_BET

        # Aggressive Betting
        multiplier = self.true_count - 1
        bet = MIN_BET * multiplier * 2  # Scale up multiplier

        # Cap the bet to prevent instant bankruptcy
        return min(round(bet), 500)

    def reset(self):
        self.running_count = 0
        self.true_count = 0


# --- 3. The Player (Bot) ---
class SmartBot:
    def __init__(self):
        self.hand = []
        self.balance = STARTING_MONEY
        self.brain = CardCounter()

    def get_score(self):
        score = sum(c.value for c in self.hand)
        aces = sum(1 for c in self.hand if c.rank == "A")
        while score > 21 and aces > 0:
            score -= 10
            aces -= 1
        return score

    def decide_action(self, dealer_up_card):
        # Simplified Basic Strategy
        score = self.get_score()
        if score >= 17:
            return "s"
        if score <= 11:
            return "h"

        # Hard 12-16 vs Dealer 7+
        dealer_val = dealer_up_card.value
        if 12 <= score <= 16:
            if dealer_val >= 7:
                return "h"
            else:
                return "s"

        return "h"


# --- 4. The Simulation Engine ---
class Simulation:
    def __init__(self):
        self.shoe = Shoe()
        self.bot = SmartBot()
        self.round_num = 0

    def run(self):
        print(f"{Fore.YELLOW}--- EXPERT CARD COUNTING SIMULATION ---{Style.RESET_ALL}")
        print(f"Starting Bankroll: ${self.bot.balance}")
        print(f"Shoe Size: {NUM_DECKS} Decks")
        input("Press Enter to start the simulation...")

        while self.bot.balance > 0:
            self.round_num += 1
            self.play_round()

            # Pause to let user read (Optional)
            if self.round_num % 1 == 0:
                time.sleep(1.5)

            if self.bot.balance >= STARTING_MONEY * 2:
                print(
                    f"\n{Fore.GREEN}DOUBLED MONEY! CASINO SECURITY IS WATCHING!{Style.RESET_ALL}"
                )
                break

    def play_round(self):
        # 1. Update Brain
        decks_left = self.shoe.decks_remaining()
        self.bot.brain.update_true_count(decks_left)

        # 2. Place Bet
        bet = self.bot.brain.get_bet_suggestion()

        # Visuals
        rc = self.bot.brain.running_count
        tc = self.bot.brain.true_count
        color = Fore.GREEN if tc >= 2 else Fore.WHITE
        print(
            f"\n--- Round {self.round_num} | RC: {rc} | TC: {tc:.1f} | {color}Bet: ${bet}{Style.RESET_ALL} ---"
        )

        # 3. Deal
        self.bot.hand = [self.shoe.deal(), self.shoe.deal()]
        dealer_hand = [self.shoe.deal(), self.shoe.deal()]

        # 4. OBSERVE (The Brain watches initial cards)
        # Note: Bot only sees Dealer's UP card (index 0) initially
        self.bot.brain.observe(self.bot.hand[0])
        self.bot.brain.observe(self.bot.hand[1])
        self.bot.brain.observe(dealer_hand[0])

        # 5. Bot Plays
        while True:
            score = self.bot.get_score()
            if score >= 21:
                break

            action = self.bot.decide_action(dealer_hand[0])
            if action == "h":
                card = self.shoe.deal()
                self.bot.hand.append(card)
                self.bot.brain.observe(card)  # Watch new card
                print(f"Bot Hit: Draws {card}")
            else:
                print("Bot Stands.")
                break

        # 6. Dealer Plays
        # Reveal Hidden Card
        self.bot.brain.observe(dealer_hand[1])  # Now Brain sees hole card

        bot_score = self.bot.get_score()
        d_score = self._calculate_score(dealer_hand)

        if bot_score <= 21:
            while d_score < 17:
                card = self.shoe.deal()
                dealer_hand.append(card)
                self.bot.brain.observe(card)  # Watch dealer draw
                d_score = self._calculate_score(dealer_hand)

        # 7. Settlement
        print(f"Bot: {bot_score} {self.bot.hand} vs Dealer: {d_score} {dealer_hand}")

        if bot_score > 21:
            print(f"{Fore.RED}Bot Busts. -${bet}{Style.RESET_ALL}")
            self.bot.balance -= bet
        elif d_score > 21:
            print(f"{Fore.GREEN}Dealer Busts. +${bet}{Style.RESET_ALL}")
            self.bot.balance += bet
        elif bot_score > d_score:
            print(f"{Fore.GREEN}Bot Wins. +${bet}{Style.RESET_ALL}")
            self.bot.balance += bet
        elif bot_score < d_score:
            print(f"{Fore.RED}Bot Loses. -${bet}{Style.RESET_ALL}")
            self.bot.balance -= bet
        else:
            print(f"{Fore.CYAN}Push.{Style.RESET_ALL}")

        print(f"Balance: ${self.bot.balance}")

        # Reshuffle check (Penetration)
        if len(self.shoe.cards) < 52:
            print(f"{Fore.MAGENTA}--- SHUFFLING SHOE ---{Style.RESET_ALL}")
            self.shoe.build()
            self.bot.brain.reset()

    def _calculate_score(self, hand):
        # Helper for dealer score (reused logic)
        score = sum(c.value for c in hand)
        aces = sum(1 for c in hand if c.rank == "A")
        while score > 21 and aces > 0:
            score -= 10
            aces -= 1
        return score


if __name__ == "__main__":
    sim = Simulation()
    sim.run()
