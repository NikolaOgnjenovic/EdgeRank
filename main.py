import operator
import sys

from parse_files_dict import *
from affinity_graph import *
from search_trie_letters import *


class FeedStatus:
    message = ""
    relevance = 0

    def __init__(self, message, relevance):
        self.message = message
        self.relevance = relevance


# Returns the 10 most relevant statuses for the given user
def get_feed(affinity_graph: networkx.DiGraph, user_name: str, statuses) -> list[FeedStatus]:
    # Add the user to the graph if he is not in it
    try:
        user = affinity_graph[user_name]
    except KeyError:
        affinity_graph.add_node(user_name)
        user = affinity_graph[user_name]

    feed = []
    for status in statuses.values():
        # Add the author and an edge between the user and author (with weight = 0) to the graph if the author is missing
        author = status['author']
        try:
            second_user = user[author]
        except KeyError:
            affinity_graph.add_node(author)
            affinity_graph.add_edge(user_name, author, weight=0)
            second_user = user[author]

        status_popularity = status_popularity_rank(status['num_comments'], status['num_shares'], status['num_likes'],
                                                   status['num_loves'], status['num_wows'], status['num_hahas'],
                                                   status['num_sads'], status['num_angrys'], status['num_special'])
        status_relevance = (second_user['weight'] + status_popularity) * date_difference_rank_multiplier(
            status['status_published'])
        feed.append(FeedStatus(
            "\nMessage: " + status['status_message'] + "\nLink: " + status['status_link'] + "\nPublished: " + str(
                status['status_published']) + "\nAuthor: " + status['author'], status_relevance))

    # Sort the feed descending by relevance
    feed.sort(key=operator.attrgetter("relevance"), reverse=True)

    # Return the 10 most relevant feed statuses
    return feed[:10]


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
        # sentence_trie.insert('rcat', 1)
        # sentence_trie.insert('car', 2)
        # sentence_trie.insert('bcar', 3)
        for status in statuses.values():
            sentence_trie.insert(status['status_message'], status['status_id'])

        print("Saved trie in file")
        trie_file_obj = open("trie.obj", "wb")
        pickle.dump(sentence_trie, trie_file_obj)
        trie_file_obj.close()

        return sentence_trie


def load_data():
    print("Loading dataset")
    timer = datetime.now()
    friends = load_friends("dataset/friends.csv")
    comments = load_comments("dataset/comments.csv")
    reactions = load_reactions("dataset/reactions.csv")
    shares = load_shares("dataset/shares.csv")
    statuses = load_statuses("dataset/statuses.csv")
    print(f"Finished loading dataset after {datetime.now() - timer} seconds.")

    print("Loading graph")
    timer = datetime.now()
    graph = get_affinity_graph(friends, comments, reactions, shares, statuses)
    print(f"Finished loading & graph generation after {datetime.now() - timer} seconds.")

    timer = datetime.now()
    sentence_trie = get_sentence_trie(statuses)
    print(f"Finished trie generation after {datetime.now() - timer} seconds.")

    return (graph, sentence_trie, statuses)


def login():
    print("Pick a username from the list to view the user's feed:")
    # for user in friends:
    #     print(user)
    username = input(">>")
    # First 10 users:
    # Sarina Hudgens
    # Angel Harmison
    # Margaret McMow
    # Michael Byrne
    # Shirley Bell
    # Jerry Kirschling
    # Vicky Gutierrez
    # Patricia Sanguiliano
    return username


def run_search(graph, sentence_trie, username, statuses):
    should_run = True
    while should_run:
        print("")
        search_term = input("Enter the term that you wish to search for\n>>")
        search_term_status_ids = sentence_trie.query(search_term)
        print(f"Found {len(search_term_status_ids)} results with the search term {search_term}.")

        relevant_statuses = {}
        for status_id in search_term_status_ids:
            if status_id in statuses:
                relevant_statuses[status_id] = statuses[status_id]

        feed = get_feed(graph, username, relevant_statuses)
        print(f"Search feed size: {len(feed)}.")

        for status in feed:
            print(status.message, "\nRelevance:", status.relevance)


def run():
    graph, sentence_trie, statuses = load_data()
    username = login()
    feed = get_feed(graph, username, statuses)
    print(f"Welcome, {username}. Here's your recommended feed:\n")
    for status in feed:
        print(status.message, "\nRelevance:", status.relevance)
    run_search(graph, sentence_trie, username, statuses)


if __name__ == '__main__':
    sys.setrecursionlimit(30000)
    run()
