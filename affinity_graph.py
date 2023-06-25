import pickle

import networkx
from datetime import *
from math import pow

date_format = "%Y-%m-%d %H:%M:%S"

reaction_type_weights = {
    "hahas": 10,
    "loves": 10,
    "sads": 5,
    "angrys": 25,
    "wows": 25,
    "likes": 5,
    "special": 30
}


# Returns the multiplier that scales depending on how recently the action was performed
def date_difference_rank_multiplier(action_date) -> float:
    current_date = datetime.today()
    day_difference = (current_date - action_date).days

    if day_difference <= 0:
        return 70  # 1.8^(7-0) + 1/1 == 62.222

    return pow(1.8, 7 - day_difference) + 1 / day_difference


# Returns the comment affinity between the user & second user
# comment_affinity = constant * date multiplier for each comment by the user on a second user's status
def comment_affinity(user_name: str, second_user_name: str, comments, statuses) -> float:
    if comments.get(user_name) is None:
        return 0

    comment_rank = 0
    for comment in comments.get(user_name):
        status = statuses.get(comment['status_id'])
        if status is not None and status['author'] == second_user_name:
            comment_rank += 40 * date_difference_rank_multiplier(comment['comment_published'])

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
            share_rank += 60 * date_difference_rank_multiplier(share['status_shared'])

    return share_rank


# Returns the affinity (graph edge weight) between two users
def affinity(user_name: str, second_user_name: str, comments, reactions, shares, statuses) -> float:
    comment_rank = comment_affinity(user_name, second_user_name, comments, statuses)
    reaction_rank = reaction_affinity(user_name, second_user_name, reactions, statuses)
    share_rank = share_affinity(user_name, second_user_name, shares, statuses)

    return comment_rank + reaction_rank + share_rank


def insert_data(graph, friends, comments, reactions, shares, statuses, statuses_by_user) -> networkx.DiGraph:
    if graph is None:
        # Weighted graph -> user A likes user B's posts but user B doesn't like user A's posts
        graph = networkx.DiGraph()

    user_list = friends.keys()
    # Create an edge between all users
    for user_id in user_list:
        for second_user_id in user_list:
            user_affinity = 0

            # If the second user is the user's friend, increase the affinity between them
            if second_user_id in friends[user_id]:
                user_affinity += 5000
            else:
                # If the second user is not a friend and an author of any statuses, continue looping through users
                # If the second user is not an author of any statuses, continue looping through users because
                # Lastly, there is no need to create an edge between a user and himself
                if second_user_id not in statuses_by_user or second_user_id == user_id:
                    continue

                user_affinity += affinity(user_id, second_user_id, comments, reactions, shares, statuses)

            if user_affinity > 0:
                if not graph.has_edge(user_id, second_user_id):
                    graph.add_edge(user_id, second_user_id, weight=user_affinity)
                else:
                    graph[user_id][second_user_id]['weight'] += user_affinity

    return graph


def status_popularity_rank(num_comments, num_shares, num_likes, num_loves, num_wows, num_hahas, num_sads, num_angrys,
                           num_special):
    return num_comments * 40 + num_shares * 10 + num_likes * 5 + num_loves * 10 + num_wows * 25 + num_hahas * 10 + num_sads * 5 + num_angrys * 25 + num_special * 30


def get_affinity_graph(friends, comments, reactions, shares, statuses, statuses_by_users):
    try:
        graph_file_obj = open("graph.obj", "rb")
        graph = pickle.load(graph_file_obj)
        graph_file_obj.close()
        print("Found graph in file")
        print(graph)
        return graph
    except FileNotFoundError:
        print("Graph not found in file")
        graph = insert_data(None, friends, comments, reactions, shares, statuses, statuses_by_users)
        graph_file_obj = open("graph.obj", "wb")
        pickle.dump(graph, graph_file_obj)
        graph_file_obj.close()
        return graph
