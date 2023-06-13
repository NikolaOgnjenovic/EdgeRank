class Node:
    def __init__(self, letter):
        self.letter = letter
        self.children = {}
        self.counter = 0  # Indicates how many times the sentence has been inserted (parent -> child -> child)
        self.status_ids: set[str] = set()


# Leaves only lowercase letters and spaces inside a string. Replaces all other characters with spaces.
def filter_status_characters(status: str) -> str:
    filtered_status = ''
    status = status.lower()
    for char in status:
        if (97 <= ord(char) <= 122) or char == ' ':
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
        node = self.root

        # Loop through each word in the sentence
        status = filter_status_characters(status)
        words = status.split(' ')
        for word in words:
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
        letters = ''.join(filter_status_characters(search_term).split(" "))

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
