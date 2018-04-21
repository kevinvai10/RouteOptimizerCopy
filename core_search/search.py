""" This file contains an implementation of search algorithms """
import heapq


class Node(object):
    """ Node of a search tree """
    def __init__(self, state, cost = 0, action=None, parent = None):
        """ Fields: parent is a reference to the node's parent in the tree
                    state is a FleetState instance
                    cost is the amount of trips in the path from the root to this node
                    action is the  action instance that resulted in state as its outcome"""

        self.parent = parent
        self.cost = cost
        self.action = action
        self.state = state

    def __eq__(self, other):
        """ Only consider the state for comparisons"""
        return self.state == other.state

    def __hash__(self):
        """ Similarly, only use the state's hash as the node's hash """
        return hash(self.state)


class UniformCostSearch(object):

    def __init__(self, initial_state):
        """ Parameters: initial_state: First step of the search """
        self.initial_state = initial_state

    def solve(self):
        """ Does a Uniform Cost Search and returns a reference to a node containing an optimal solution """

        # Root of the search tree
        root = Node(self.initial_state)

        # Cache of explored nodes
        explored = set()

        # Priority queue for the nodes to explore
        queue = list()

        # Add the initial state to the priority queue
        heapq.heappush(queue, (root.cost, root))

        # Reference to the solution, currently empty
        solution = None

        # Main loop of UCS
        while solution is None and len(queue) > 0:
            # Fetch the next node to consider
            _, node = heapq.heappop(queue) # Ignore the first element of the tuple, which is the cost used for ranking
            # Add it to the explored cache
            explored.add(node)
            # Reference to the state
            state = node.state

            # If this is a successful state, bingo!
            if state.is_successful():
                # Keep track of the solution
                solution = node
            # Otherwise, expand the fringe of the search
            else:
                # Compute the possible children
                for action in state.possible_actions():
                    # Clone the state
                    new_state = state.clone()
                    # Execute the given action to mutate the clone
                    new_state.execute_action(action)
                    # Create the child node
                    child = Node(new_state, new_state.trips, action, node)

                    # See if we haven't been in this state before
                    if child not in explored:
                        # If this child is not yet in the queue, add it!
                        if child not in queue:
                            heapq.heappush(queue, (child.cost, child))
                    else:
                        # Check if the element is in the queue with another cost and if so, replace it, in one pass
                        for ix in range(len(queue)):
                            elem = queue[ix]
                            # If we identify the current node equivalent to the current child
                            if elem == child:
                                # And if the cost of the child is less than that of the current node
                                if child.cost < elem.cost:
                                    # Replace the element in the array
                                    queue[ix] = child
                                    # Restore the heap property
                                    heapq.heapify(queue)
                                # Since the element is only once in the queue, we can break the loop
                                break

        # Return the solution, if found
        return solution
