import random
import os


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def deal_card():
    """Returns a random card from an infinite deck."""

    cards = [11, 2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 10]
    return random.choice(cards)


def calc_score(cards):

    score = sum(cards)

    if score > 21 and 11 in cards:
        cards.remove(11)
        cards.appand(1)
        score = sum(cards)

    return score


def play_game():
    print("\n--- NEW HAND ---")
    user_cards = []
    computer_cards = []
    is_game_over = False

    # 1. Deal initial cards
    for _ in range(2):
        user_cards.append(deal_card())
        computer_cards.append(deal_card())

    # 2. Player Turn
    while not is_game_over:
        user_score = calc_score(user_cards)
        computer_score = calc_score(computer_cards)

        print(f"   Your cards: {user_cards}, current score: {user_score}")
        print(f"   Dealer's first card: {computer_cards[0]}")

        # Check for Blackjack or Bust immediately
        if user_score == 0 or computer_score == 0 or user_score > 21:
            is_game_over = True
        else:
            should_continue = input("Type 'y' to get another card, 'n' to pass: ")
            if should_continue == "y":
                user_cards.append(deal_card())
            else:
                is_game_over = True

    # 3. Dealer Turn (The AI Logic)
    # Dealer must hit until score is 17 or higher
    while computer_score != 0 and computer_score < 17:
        computer_cards.append(deal_card())
        computer_score = calc_score(computer_cards)

    # 4. Final Results
    print(f"\n   Your final hand: {user_cards}, final score: {user_score}")
    print(f"   Dealer's final hand: {computer_cards}, final score: {computer_score}")
    print(compare(user_score, computer_score))


def compare(user_score, computer_score):
    if user_score > 21 and computer_score > 21:
        return "You went over. You lose."
    if user_score == computer_score:
        return "Draw."
    elif computer_score == 21:
        return "Lose, opponent has Blackjack."
    elif user_score == 21:
        return "Win with a Blackjack."
    elif user_score > 21:
        return "You went over. You lose."
    elif computer_score > 21:
        return "Opponent went over. You win!"
    elif user_score > computer_score:
        return "You win!"
    else:
        return "You lose."


# --- Main Loop ---
while input("\nDo you want to play a game of Blackjack? Type 'y' or 'n': ") == "y":
    clear_screen()
    play_game()
