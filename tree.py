def build_tree(nodes):
    # create empty tree to fill
    tree = {}

    # fill in tree starting with roots (those with no parent)
    build_tree_recursive(tree, None, nodes)

    return tree


def build_tree_recursive(tree, parent, nodes):
    # find children
    children = [n for n in nodes if n[2] == parent]

    # build a subtree for each child
    for child in children:
        # start new subtree
        tree[child] = {}

        # call recursively to build a subtree for current node
        build_tree_recursive(tree[child], child[1], nodes)


def sort_tree(tree):
    sorted(tree, key=lambda x: x[3])
    for key, value in tree.items():
        sort_tree(value)