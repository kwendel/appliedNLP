class Util:

    @staticmethod
    def ratio(left, right):
        """
        Returns the ratio between two numbers.
        If any argument is undefined or <= 0, returns -1.
        """

        # Catch edge cases
        if not left or left <= 0 or not right or right <= 0:
            return -1

        return abs(left / right)

    @staticmethod
    def diff(left, right):
        """
        Return the difference between two numbers.
        If any argument is undefined or < 0, returns -1.
        """

        # Catch edge cases (check that both sides "exist")
        if not left or left < 0 or not right or right < 0:
            return -1

        return abs(left - right)

    @staticmethod
    def count_chars(obj):
        """
        Determines the number of characters in a string.
        If the argument is undefined or an empty list, returns -1.
        """

        # Catch empty post titles (and empty lists)
        if not obj and obj != "":
            return -1

        # Catch non-strings (probably list / pd.Series)
        if not isinstance(obj, str):
            # Average the length of items in a list
            return sum(map(Util.count_chars, obj)) / len(obj)

        # Strip spaces
        processed = obj.strip().replace(" ", "")

        # Return string length
        return len(processed)

    @staticmethod
    def count_specific_char(obj, char):
        """
        Counts the number of occurrences of a specific (sub)string.
        If any arguments are undefined, or when the (sub)string is not found, returns 0.
        """

        if not char or not obj:
            return 0

        # Catch non-strings (probably list / pd.Series)
        if not isinstance(obj, str):
            # Sum the number of occurrences in each list item
            return sum([Util.count_specific_char(item, char) for item in obj])

        return obj.count(char)

    @staticmethod
    def count_tags(obj, tags: set) -> int:
        """Removes words from list of word/tag tuples if tag matches function argument."""

        return sum([1 for pos_tuple in obj if pos_tuple[1] in tags])
