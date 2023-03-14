import random
import re

def getFunName(extension, separator=' '):
    """
        Returns a funny filename
    """
    if not re.match(r"[.][a-zA-Z]+$", extension):
        raise ValueError("Invalid extension format, must be in the format '.[A-z]'")

    NAME    = ['Einstein', 'Feynman', 'Schrodinger', 'Newton', 'Hawking', 'Tesla', 'Curie', 'Bohr', 'Hertz', 'Planck']
    VERB    = ['tickles', 'hugs', 'whispers_to', 'is_doing', 'dances_with', 'paints', 'sings_to', 'high_fives', 'pets', 'massages', 'plays_fetch_with']
    SUBJECT = ['avocados', 'paperclips', 'teevian', 'cookies', 'poetry', 'puzzles', 'karaokes', 'sushi', 'photons', 'lasers']

    return f'{random.choice(NAME)}{separator}{random.choice(VERB)}{separator}{random.choice(SUBJECT)}{extension}'