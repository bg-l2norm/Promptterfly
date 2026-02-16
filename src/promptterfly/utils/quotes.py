"""Quotes collection for PromptFly startup banner."""

import random

QUOTES = [
    "“Code is like humor. When you have to explain it, it’s bad.” – Cory House",
    "“Fix the cause, not the symptom.” – Steve Maguire",
    "“Make it work, make it right, make it fast.” – Kent Beck",
    "“Complexity is the enemy of execution.” – Tony Hsieh",
    "“The best time to plant a tree was 20 years ago. The second best time is now.” – Chinese Proverb",
    "“First, solve the problem. Then, write the code.” – John Johnson",
    "“Code never lies, comments sometimes do.” – Ron Jeffries",
    "“Simplicity is the soul of efficiency.” – Austin Freeman",
    "“Any fool can write code that a computer can understand. Good programmers write code that humans can understand.” – Martin Fowler",
    "“The only way to do great work is to love what you do.” – Steve Jobs",
    "“Talk is cheap. Show me the code.” – Linus Torvalds",
    "“Programs must be written for people to read, and only incidentally for machines to execute.” – Abelson & Sussman",
    "“Sometimes it pays to stay in bed on Monday, rather than spending the rest of the week debugging Monday’s code.” – Christopher Thompson",
    "“A day without laughter is a day wasted.” – Charlie Chaplin (programmer-approved)",
    "“Babies are born with the ability to suck; the rest of us have to learn how to optimize.” – Anonymous",
]

def get_random_quote() -> str:
    """Return a random quote from the collection."""
    return random.choice(QUOTES)
