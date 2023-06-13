import pickle

import networkx
from datetime import *

date_format = "%Y-%m-%d %H:%M:%S"

reaction_type_weights = {
    "hahas": 10,
    "loves": 20,
    "sads": 15,
    "angrys": 10,
    "wows": 20,
    "likes": 5,
    "special": 30
}


# Returns the multiplier that scales depending on how recently the action was performed
def date_difference_rank_multiplier(action_date) -> float:
    current_date = datetime.today()
    date_difference = current_date - action_date

    multiplier = 1
    if date_difference.days < 1:
        multiplier *= 10
    elif date_difference.days < 14:
        multiplier *= 1
    elif date_difference.days < 30:
        multiplier *= 0.8
    elif date_difference.days < 60:
        multiplier *= 0.4
    else:
        multiplier *= 0.1

    return multiplier


# Returns the comment affinity between the user & second user
# comment_affinity = constant * date multiplier for each comment by the user on a second user's status
def comment_affinity(user_name: str, second_user_name: str, comments, statuses) -> float:
    if comments.get(user_name) is None:
        return 0

    comment_rank = 0
    for comment in comments.get(user_name):
        status = statuses.get(comment['status_id'])
        if status is not None and status['author'] == second_user_name:
            comment_rank += 30 * date_difference_rank_multiplier(comment['comment_published'])

    return comment_rank


# Returns the reaction affinity between the user & second user
# reaction_affinity = constant * date multiplier for each reaction by the user on a second user's status
def reaction_affinity(user_name: str, second_user_name: str, reactions, statuses) -> float:
    if reactions.get(user_name) is None:
        return 0

    reaction_rank = 0
    for reaction in reactions.get(user_name):
        status = statuses.get(reaction['status_id'])
        if status is not None and status['author'] == second_user_name:
            reaction_rank += reaction_type_weights[reaction['type_of_reaction']] * date_difference_rank_multiplier(
                reaction['reacted'])
            # reaction_rank += reaction_type_weight(reaction['type_of_reaction']) * date_difference_rank_multiplier(reaction['reacted'])

    return reaction_rank


# Returns the share affinity between the user & second user
# share_affinity = constant * date multiplier for each share by the user on a second user's status
def share_affinity(user_name: str, second_user_name: str, shares, statuses) -> float:
    if shares.get(user_name) is None:
        return 0

    share_rank = 0
    for share in shares.get(user_name):
        status = statuses.get(share['status_id'])
        if status is not None and status['author'] == second_user_name:
            share_rank += 50 * date_difference_rank_multiplier(share['status_shared'])

    return share_rank


# Returns the affinity (graph edge weight) between two users
def affinity(user_name: str, second_user_name: str, comments, reactions, shares, statuses) -> float:
    comment_rank = comment_affinity(user_name, second_user_name, comments, statuses)
    reaction_rank = reaction_affinity(user_name, second_user_name, reactions, statuses)
    share_rank = share_affinity(user_name, second_user_name, shares, statuses)

    return comment_rank + reaction_rank + share_rank


def create_graph(friends, comments, reactions, shares, statuses):
    # Weighted graph -> user A likes user B's posts but user B doesn't like user A's posts
    graph = networkx.DiGraph()

    user_list = friends.keys()
    # Create an edge between all users
    for user_id in user_list:
        for second_user_id in user_list:
            # No need to create an edge between a user and himself
            if user_id == second_user_id:
                continue

            graph.add_node(user_id)
            graph.add_node(second_user_id)

            user_affinity = affinity(user_id, second_user_id, comments, reactions, shares, statuses)

            # If the second user is the user's friend, increase the affinity between them
            user_affinity += (second_user_id in friends[user_id]) * 5000  # TODO: broj bolji

            if user_affinity > 0:
                graph.add_edge(user_id, second_user_id, weight=user_affinity)

    return graph


def status_popularity_rank(num_comments, num_shares, num_likes, num_loves, num_wows, num_hahas, num_sads, num_angrys,
                           num_special):
    return num_comments * 2 + num_shares * 20 + num_likes * 5 + num_loves * 30 + num_wows * 20 + num_hahas * 10 + num_sads * 10 + num_angrys * 20 + num_special * 10


def get_affinity_graph(friends, comments, reactions, shares, statuses):
    try:
        graph_file_obj = open("graph.obj", "rb")
        graph = pickle.load(graph_file_obj)
        graph_file_obj.close()
        print("Found graph in file")
        print(graph)
        return graph
    except FileNotFoundError:
        print("Graph not found in file")
        graph = create_graph(friends, comments, reactions, shares, statuses)
        graph_file_obj = open("graph.obj", "wb")
        pickle.dump(graph, graph_file_obj)
        graph_file_obj.close()
        return graph
