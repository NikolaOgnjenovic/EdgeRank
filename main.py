import operator
import sys

import affinity_graph
from parse_files_dict import *
from affinity_graph import *
from search_trie_letters import *


class FeedStatus:
    message = ""
    relevance = 0

    def __init__(self, status: dict, relevance):
        self.message = "\nMessage: " + status['status_message'] \
                       + "\nLink: " + status['status_link'] \
                       + "\nPublished: " + str(status['status_published']) \
                       + "\nAuthor: " + status['author']
        self.relevance = relevance


# Returns the 10 most relevant statuses for the given user
def get_feed(graph: networkx.DiGraph, user_name: str, statuses: dict, word_count_map: dict) -> list[FeedStatus]:
    # Add the user to the graph if he is not in it
    try:
        user = graph[user_name]
    except KeyError:
        graph.add_node(user_name)
        user = graph[user_name]

    feed = []
    for status_id, status in statuses.items():
        # Add the author and an edge between the user and author (with weight = 0) to the graph if the author is missing
        author = status['author']
        try:
            second_user = user[author]
        except KeyError:
            graph.add_node(author)
            graph.add_edge(user_name, author, weight=0)
            second_user = user[author]

        status_popularity = status_popularity_rank(status['num_comments'], status['num_shares'], status['num_likes'],
                                                   status['num_loves'], status['num_wows'], status['num_hahas'],
                                                   status['num_sads'], status['num_angrys'], status['num_special'])
        status_relevance = (second_user['weight'] + status_popularity) * date_difference_rank_multiplier(
            status['status_published'])

        if word_count_map != {}:
            status_relevance *= pow(word_count_map[status_id], 10)

        feed.append(FeedStatus(status, status_relevance))

    # Sort the feed descending by relevance
    feed.sort(key=operator.attrgetter("relevance"), reverse=True)

    # Return the 10 most relevant feed statuses
    return feed[:10]


# Inserts additional data into a given sentence trie
def insert_sentence_trie_data(sentence_trie: Trie, statuses: dict) -> Trie:
    for status in statuses.values():
        sentence_trie.insert(status['status_message'], status['status_id'])

    trie_file_obj = open("trie.obj", "wb")
    pickle.dump(sentence_trie, trie_file_obj)
    trie_file_obj.close()
    return sentence_trie


# Returns a sentence trie from a file, creates a new one if not found
def get_sentence_trie(statuses) -> Trie:
    try:
        trie_file_obj = open("trie.obj", "rb")
        sentence_trie = pickle.load(trie_file_obj)
        trie_file_obj.close()
        print("Trie found in file")

        return sentence_trie
    except FileNotFoundError:
        print("Trie not found in file")
        sentence_trie = Trie()
        for status in statuses.values():
            sentence_trie.insert(status['status_message'], status['status_id'])

        print("Saved trie in file")
        trie_file_obj = open("trie.obj", "wb")
        pickle.dump(sentence_trie, trie_file_obj)
        trie_file_obj.close()

        return sentence_trie


# Inserts an additional dataset into the given graph, sentence trie and status dictionary
def insert_data(graph, sentence_trie, statuses: dict):
    print("Loading additional dataset")
    timer = datetime.now()
    friends = load_friends("dataset/friends.csv")
    comments = load_comments("dataset/test_comments.csv")
    reactions = load_reactions("dataset/test_reactions.csv")
    shares = load_shares("dataset/test_shares.csv")
    new_statuses = load_statuses("dataset/test_statuses.csv")
    print(f"Finished additional dataset loading after {datetime.now() - timer} seconds.")

    print("Adding new statuses")
    timer = datetime.now()
    for key, val in new_statuses.items():
        statuses.update({key: val})
    print(f"Finished adding new statuses after {datetime.now() - timer} seconds.")

    print("Adding new data to graph")
    timer = datetime.now()
    graph = affinity_graph.insert_data(graph, friends, comments, reactions, shares, statuses)
    print(f"Finished new data insertion in graph after {datetime.now() - timer} seconds.")

    print("Adding new data to trie")
    timer = datetime.now()
    sentence_trie = insert_sentence_trie_data(sentence_trie, new_statuses)
    print(f"Finished new data insertion in trie after {datetime.now() - timer} seconds.")
    print("\n")
    return graph, sentence_trie, statuses


# Loads / generates the graph, sentence trie and status dictionary
def load_data():
    print("Loading dataset")
    timer = datetime.now()
    friends = load_friends("dataset/friends.csv")
    comments = load_comments("dataset/comments.csv")
    reactions = load_reactions("dataset/reactions.csv")
    shares = load_shares("dataset/shares.csv")
    statuses = load_statuses("dataset/statuses.csv")
    test_statuses = load_statuses("dataset/test_statuses.csv")
    for key, val in test_statuses.items():
        statuses.update({key: val})

    print(f"Finished dataset loading after {datetime.now() - timer} seconds.")

    print("Loading graph")
    timer = datetime.now()
    graph = get_affinity_graph(friends, comments, reactions, shares, statuses)
    print(f"Finished graph loading / generation after {datetime.now() - timer} seconds.")

    timer = datetime.now()
    sentence_trie = get_sentence_trie(statuses)
    print(f"Finished trie generation after {datetime.now() - timer} seconds.")
    print("\n")

    return graph, sentence_trie, statuses


def login():
    print("Pick a username from the list to view the user's feed:")
    # for user in friends:
    #     print(user)
    username = input(">>")
    return username


def run_search(graph, sentence_trie, username, statuses):
    should_run = True
    while should_run:
        print("")
        search_input = input("Enter the term that you wish to search for\n>>")
        # Word autocompletion
        if search_input[-1] == '*':
            autocompleted_words = sentence_trie.autocomplete(search_input)
            print("Autocompleted words:")
            for word in autocompleted_words:
                print(word)
        else:
            if search_input == '':
                continue

            # A case-insensitive union search returns the number of words that a status contains from the given input
            should_count_words = False

            # Case-sensitive phrase search
            if search_input[0] == '"' and search_input[-1] == '"':
                search_ids = sentence_trie.search_phrase(search_input, statuses)
            else:
                search_ids = sentence_trie.search_union_case_insensitive(search_input)
                should_count_words = True
            print(f"Found {len(search_ids)} results.")

            # Create a map of statuses that have been found when searching
            relevant_statuses = {}
            for status_id in search_ids:
                if status_id in statuses:
                    relevant_statuses[status_id] = statuses[status_id]

            if should_count_words:
                feed = get_feed(graph, username, relevant_statuses, search_ids)
            else:
                feed = get_feed(graph, username, relevant_statuses, {})

            print(f"Search feed size: {len(feed)}.")
            for status in feed:
                print(status.message, "\nRelevance:", status.relevance)


def run():
    graph, sentence_trie, statuses = load_data()
    # insert_data(graph, sentence_trie, statuses)

    username = login()
    # Displays the feed for the current user
    feed = get_feed(graph, username, statuses, {})
    print(f"Welcome, {username}. Here's your recommended feed:\n")
    for status in feed:
        print(status.message, "\nRelevance:", status.relevance)

    run_search(graph, sentence_trie, username, statuses)


if __name__ == '__main__':
    sys.setrecursionlimit(30000)
    run()
