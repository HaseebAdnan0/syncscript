"""
Utilities for extracting and resolving @mentions in annotation text.

Provides functions to detect @username patterns and resolve them to User objects
who are members of the relevant vault.
"""
import re
from typing import List
from django.contrib.auth import get_user_model

User = get_user_model()


def extract_mentions(text: str) -> List[str]:
    """
    Extract @mentions from text and return list of usernames.

    Detects @username patterns where username is preceded by start of text,
    whitespace, or punctuation. Returns unique usernames without the @ symbol.

    Args:
        text: The text to search for mentions

    Returns:
        List of unique usernames mentioned (without @ symbol)

    Examples:
        >>> extract_mentions("@alice what do you think?")
        ['alice']
        >>> extract_mentions("Hey @bob and @charlie, check this out!")
        ['bob', 'charlie']
        >>> extract_mentions("email@example.com is not a mention")
        []
    """
    # Pattern: @ followed by word characters (letters, digits, underscore)
    # Must be at start of string or preceded by whitespace
    pattern = r'(?:^|\s)@(\w+)'

    matches = re.findall(pattern, text)

    # Return unique usernames (preserve order)
    seen = set()
    unique_mentions = []
    for username in matches:
        if username not in seen:
            seen.add(username)
            unique_mentions.append(username)

    return unique_mentions


def resolve_mentions(usernames: List[str], vault_id: int) -> List[User]:  # type: ignore[type-arg]
    """
    Resolve usernames to User objects who are members of the given vault.

    Only returns users who:
    1. Exist in the database
    2. Are members of the specified vault

    Invalid usernames and non-members are silently ignored.

    Args:
        usernames: List of usernames to resolve
        vault_id: ID of the vault to check membership

    Returns:
        List of User objects who are valid vault members

    Examples:
        >>> resolve_mentions(['alice', 'bob', 'nonexistent'], vault_id=1)
        [<User: alice>, <User: bob>]  # if both are members
    """
    if not usernames:
        return []

    # Import here to avoid circular imports
    from apps.vaults.models import Vault

    try:
        vault = Vault.objects.get(id=vault_id)
    except Vault.DoesNotExist:
        return []

    # Get vault members whose usernames are in the mention list
    vault_members = vault.members.filter(username__in=usernames)

    return list(vault_members)
