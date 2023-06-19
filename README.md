
# FaceRank algorithm
This project represents my implementation of a facerank algorithm which recommends posts on a social network by parsing a large database of comments, shares, reactions, users and posts.

The project consists of a graph which has the social network's users as vertices and their affinity as the edges, as well as my implementation of a trie which is stores all words from all statuses that users have posted.

The trie is used for searching:
* Statuses that contain the given search term (case-insensitive, ranked by the number of words in the search term found in the post)
* Statuses that contain the words of the search phrase (in the same order, case-sensitive)
* Autocompleting a user's search term (returning a set of words ranked by occurence in the given dataset)


# Usage
After the dataset has loaded, enter a username in the CLI (a random one resulting in a feed that disregards user affinity, or one from the user list in the dataset, located in the first column of each row in the friends.txt file).

To perform a case-insensitive search where any word matches the given term, input anything.

To perform a case-sensitive search where all words match the given term in the given order, input the search term between double quotation marks ("x").

To perform a word autocompletion search, input anything followed by *.
 

# Dependencies
Dependencies (pip):

    networkx
    pickle

Installation:

    pip install networkx
    pip install pickle
