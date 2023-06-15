class Node:
    def __init__(self, letter):
        self.letter = letter
        self.children = {}
        self.counter = 0  # Indicates how many times the sentence has been inserted (parent -> child -> child)
        self.status_ids: set[str] = set()
        self.is_terminal: bool = False


# Leaves only lowercase letters and spaces inside a string. Replaces all other characters with spaces.
def filter_status_characters(status: str, to_lower: bool) -> str:
    filtered_status = ''
    if to_lower:
        status = status.lower()
    for char in status:
        if (not to_lower and (65 <= ord(char) <= 90)) or (97 <= ord(char) <= 122) or char == ' ':
            filtered_status += char
        else:
            filtered_status += ' '

    return filtered_status


class Trie(object):
    def __init__(self):
        """
        The root node does not store a letter
        """
        self.root = Node('')

        # A hash map of nodes that represent roots of sub-tries#
        # key -> letter, val -> list[nodes which hold the given key]
        self.letter_hash: dict[str: list[Node]] = {}

    def insert(self, status, status_id):
        """Inserts a status into the trie"""
        # node = self.root

        # Loop through each word in the sentence
        status = filter_status_characters(status, True)
        words = status.split(' ')
        for word in words:
            node = self.root
            for i in range(0, len(word)):
                # If the letter is found, break out of the word loop
                if word[i] in node.children.keys():
                    node = node.children[word[i]]
                # If the letter is not found, create a new node in the trie
                else:
                    new_node = Node(word[i])
                    node.children[word[i]] = new_node
                    node = new_node
                    if word[i] not in self.letter_hash:
                        self.letter_hash.update({word[i]: [node]})
                    self.letter_hash[word[i]].append(node)

                node.status_ids.add(status_id)
                node.counter += 1  # Increase the times the node has been stored in the trie

            node.is_terminal = True  # Mark the last node in the word as terminal (used for autocompletion)

    def dfs(self, letters: str, letter_counter: int, node: Node) -> set[str]:
        # Base case: if all letters have been found, return the ids of the node
        if letter_counter == len(letters):
            return node.status_ids

        ids = set()
        # If the node's children contain the given letter, iterate deeper and update the ids set
        letter = letters[letter_counter]
        if letter in node.children:
            node_ids = self.dfs(letters, letter_counter + 1, node.children[letter])
            if node_ids:
                ids.update(node_ids)

        return ids

    # Returns a set of status ids that hold the given search term
    def query(self, search_term: str) -> set[str]:
        # join(filter MAG#$! A) == join(MAG    A) == MAGA
        letters = ''.join(filter_status_characters(search_term, True).split(" "))
        if len(letters) == 0:
            return set()

        # If the first letter is not in the letter hash map, return an empty set
        ids = set()
        if letters[0] not in self.letter_hash:
            return ids

        # Iterate through every node in list of the first letter hash
        nodes = self.letter_hash[letters[0]]
        for node in nodes:
            node_ids = self.dfs(letters, 1, node)
            if node_ids:
                ids.update(node_ids)
        return ids

    # Returns a list of autocompleted search terms
    def autocomplete(self, prefix):
        prefix = filter_status_characters(prefix, True).replace(' ', '')
        # prefix = prefix[:-1]  # Remove the * from the search term
        node = self.root
        for char in prefix:
            if char not in node.children:
                return []
            node = node.children[char]
        return self.get_words_from_prefix(node, prefix)

    def get_words_from_prefix(self, node, prefix):
        words = []
        # If the node marks the end of a word, add a space to the prefix and add it the word list
        if node.is_terminal:
            # prefix += ' '
            words.append(prefix)
        # For each child, add the child's character to the prefix and iterate deeper
        for char, child in node.children.items():
            words.extend(self.get_words_from_prefix(child, prefix + char))
        return words

    # Returns status ids that contain all words in the given phrase (case-sensitive!)
    def search_phrase(self, phrase, statuses):
        phrase = phrase[1:-1]  # Remove " from the beginning and end of the phrase
        phrase = filter_status_characters(phrase, False)  # Filter the characters, but leave uppercase characters
        status_ids = self.search_case_insensitive(phrase)  # Do a case-insensitive search of the phrase
        phrase_words = phrase.split(' ')

        filtered_ids = []
        for status_id in status_ids:
            if status_id not in statuses:
                continue

            # Filter the status message and split it into a list of words
            status_message = statuses[status_id]['status_message']
            status_message = filter_status_characters(status_message, False)
            status_words: list[str] = status_message.split(' ')

            try:
                # Find the first word of the phrase in the status message
                first_word_index = status_words.index(phrase_words[0])
                should_add = True

                # Iterate through the remaining words in the phrase
                for i in range(1, len(phrase_words)):
                    # If the next word in the phrase is not the next word in the status, skip the current status
                    if status_words.index(phrase_words[i]) != first_word_index + i:
                        should_add = False
                        break

                if should_add:
                    filtered_ids.append(status_id)
            except ValueError:
                continue

        return filtered_ids

    # Performs a case-insensitive search for the given phrase
    def search_case_insensitive(self, phrase):
        phrase_words = phrase.split(' ')
        status_ids = self.query(phrase_words[0])
        for i in range(1, len(phrase_words)):
            status_ids = status_ids.intersection(self.query(phrase_words[i]))

        return status_ids
