class IdentAuth:
    def __init__(self):
        pass

    def is_allowed(self, nick, nickhost, level):
        if nick == 'oranges':
            return True

        else:
            return False
