import random


# --- Configuration ---
NUM_DECKS = 6
STARTING_MONEY = 10000
MIN_BET = 50
BLACKJACK_PAYOUT = 1.5
SHUFFLE_AT_DECKS_LEFT = 1.5


# --- 1. Core Objects ---
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
        if self.value <= 6:
            return 1
        if self.value >= 10:
            return -1
        return 0

    def __repr__(self):
        return f"{self.rank}{self.suit[0]}"


class Shoe:
    def __init__(self):
        self.cards = []
        self.build()

    def build(self):
        suits = ["Hearts", "Diamonds", "Clubs", "Spades"]
        ranks = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
        self.cards = [
            Card(r, s) for _ in range(NUM_DECKS) for s in suits for r in ranks
        ]
        random.shuffle(self.cards)

    def deal(self):
        if not self.cards:
            self.build()
        return self.cards.pop()

    def decks_remaining(self):
        return len(self.cards) / 52


# --- 2. Counter ---
class CardCounter:
    def __init__(self):
        self.running_count = 0
        self.true_count = 0

    def observe(self, card):
        self.running_count += card.count_value

    def update_true_count(self, decks_left):
        self.true_count = self.running_count / max(decks_left, 0.5)

    def get_bet(self):
        if self.true_count < 1:
            return MIN_BET
        units = min(int(self.true_count), 6)
        return MIN_BET * units

    def reset(self):
        self.running_count = 0
        self.true_count = 0


# --- 3. Strategy Engine ---
class StrategyEngine:
    @staticmethod
    def hand_value(hand):
        total = sum(c.value for c in hand)
        aces = sum(1 for c in hand if c.rank == "A")
        while total > 21 and aces:
            total -= 10
            aces -= 1
        return total

    @staticmethod
    def is_soft(hand):
        total = sum(c.value for c in hand)
        return any(c.rank == "A" for c in hand) and total <= 21

    @staticmethod
    def get_action(hand, dealer_up):
        d = dealer_up.value
        score = StrategyEngine.hand_value(hand)
        is_soft = StrategyEngine.is_soft(hand)

        # Pair logic (2-card only)
        if len(hand) == 2 and hand[0].value == hand[1].value:
            v = hand[0].value
            if v == 11 or v == 8:
                return "p"
            if v == 10 or v == 5:
                pass
            elif v in (2, 3):
                return "p" if 2 <= d <= 7 else "h"
            elif v == 4:
                return "p" if d in (5, 6) else "h"
            elif v == 6:
                return "p" if 2 <= d <= 6 else "h"
            elif v == 7:
                return "p" if 2 <= d <= 7 else "h"
            elif v == 9:
                return "p" if d in (2, 3, 4, 5, 6, 8, 9) else "s"

        # Soft totals
        if is_soft:
            if score >= 19:
                return "s"
            if score == 18:
                if 3 <= d <= 6:
                    return "d"
                if d in (2, 7, 8):
                    return "s"
                return "h"
            if score == 17:
                return "d" if 3 <= d <= 6 else "h"
            if score in (15, 16):
                return "d" if 4 <= d <= 6 else "h"
            if score in (13, 14):
                return "d" if 5 <= d <= 6 else "h"

        # Hard totals
        if score >= 17:
            return "s"
        if 13 <= score <= 16:
            if score == 12 and d in (2, 3):
                return "h"
            return "s" if d <= 6 else "h"
        if score == 11:
            return "d" if d != 11 else "h"
        if score == 10:
            return "d" if d <= 9 else "h"
        if score == 9:
            return "d" if 3 <= d <= 6 else "h"
        return "h"


# --- 4. Simulation ---
class Simulation:
    def __init__(self):
        self.shoe = Shoe()
        self.counter = CardCounter()
        self.balance = STARTING_MONEY

    def play_round(self):
        # Shuffle check
        if self.shoe.decks_remaining() <= SHUFFLE_AT_DECKS_LEFT:
            self.shoe.build()
            self.counter.reset()

        self.counter.update_true_count(self.shoe.decks_remaining())
        bet = self.counter.get_bet()

        player = [self.shoe.deal(), self.shoe.deal()]
        dealer = [self.shoe.deal(), self.shoe.deal()]

        for c in player + [dealer[0]]:
            self.counter.observe(c)

        # Blackjack check
        p_val = StrategyEngine.hand_value(player)
        d_val = StrategyEngine.hand_value(dealer)

        if p_val == 21:
            self.counter.observe(dealer[1])
            if d_val == 21:
                return
            self.balance += int(bet * BLACKJACK_PAYOUT)
            return

        if dealer[0].value in (10, 11):
            self.counter.observe(dealer[1])
            if d_val == 21:
                self.balance -= bet
                return

        hands = [{"cards": player, "bet": bet, "done": False, "split_aces": False}]

        i = 0
        while i < len(hands):
            h = hands[i]
            hand = h["cards"]
            if h["done"]:
                i += 1
                continue

            score = StrategyEngine.hand_value(hand)
            if score >= 21:
                h["done"] = True
                i += 1
                continue

            action = StrategyEngine.get_action(hand, dealer[0])

            if action == "p" and self.balance >= h["bet"]:
                c1, c2 = hand
                h["cards"] = [c1, self.shoe.deal()]
                h["split_aces"] = c1.rank == "A"
                new_hand = {
                    "cards": [c2, self.shoe.deal()],
                    "bet": h["bet"],
                    "done": False,
                    "split_aces": c2.rank == "A",
                }
                self.counter.observe(h["cards"][1])
                self.counter.observe(new_hand["cards"][1])
                hands.append(new_hand)
                continue

            if h.get("split_aces"):
                h["done"] = True
                i += 1
                continue

            if action == "d" and self.balance >= h["bet"]:
                h["bet"] *= 2
                card = self.shoe.deal()
                self.counter.observe(card)
                hand.append(card)
                h["done"] = True
                i += 1
                continue

            if action == "h":
                card = self.shoe.deal()
                self.counter.observe(card)
                hand.append(card)
                continue

            if action == "s":
                h["done"] = True
                i += 1

        # Dealer play
        self.counter.observe(dealer[1])
        while StrategyEngine.hand_value(dealer) < 17:
            card = self.shoe.deal()
            self.counter.observe(card)
            dealer.append(card)

        d_score = StrategyEngine.hand_value(dealer)

        # Settlement
        for h in hands:
            p_score = StrategyEngine.hand_value(h["cards"])
            if p_score > 21:
                self.balance -= h["bet"]
            elif d_score > 21 or p_score > d_score:
                self.balance += h["bet"]
            elif p_score < d_score:
                self.balance -= h["bet"]

    def run(self, rounds=100000):
        for _ in range(rounds):
            if self.balance <= 0:
                break
            self.play_round()
        print(f"Final balance: ${self.balance}")


if __name__ == "__main__":
    Simulation().run()
