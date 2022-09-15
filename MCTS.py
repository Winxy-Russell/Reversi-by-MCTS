'''
 This is a simple realization of MCTS
'''
import random
import math

class MCTS(object):
    def __init__(self):
        self.NULL = 0
        self.BLACK = 1
        self.WHITE = 2
        self.c_black = 1.3
        self.c_white = 1.4

        self.cur_player = self.BLACK

        self.arr = [] # this array is used for store the chessboard with size 8 * 8
        self.scores = []
        for i in range(64):
            self.arr.append(0)
            self.scores.append(0)
        self.arr[self.from2Dto1D(4, 4)] = self.arr[self.from2Dto1D(3, 3)] = self.BLACK
        self.arr[self.from2Dto1D(4, 3)] = self.arr[self.from2Dto1D(3, 4)] = self.WHITE
        self.arr_supposed = self.arr[:] # The array for machine learning

        self.next_step_black = set()
        self.next_step_white = set()
        self.state_nodes = [] # each element is a directory containing times of exploration and times of win
        self.last_change = []
        for i in range(64):
            self.node = {}
            self.node["cnt_win"] = 0 # times to be chose
            self.node["cnt_total"] = 0
            self.state_nodes.append(self.node)

        self.closure = [] # array to store the positions of the fixed points
        self.closure.append(self.from2Dto1D(4, 4))
        self.closure.append(self.from2Dto1D(3, 4))
        self.closure.append(self.from2Dto1D(4, 3))
        self.closure.append(self.from2Dto1D(3, 3))
        self.simulation_path = [[], [], []]
        self.update_next_step(self.arr)


    def update_next_step(self, arr):
        self.next_step_black.clear()
        self.next_step_white.clear()

        for closed_node in self.closure:
            tmp = {1, -1, 8, -8, 7, -7, 9, -9}
            for j in tmp:
                new_node = closed_node + j

                if 0 <= new_node < 64 and arr[new_node] == self.NULL:
                    if self.cur_player == self.BLACK and self.check_step_valid(new_node, self.BLACK):
                        self.next_step_black.add(new_node)

                    if self.cur_player == self.WHITE and self.check_step_valid(new_node, self.WHITE):
                        self.next_step_white.add(new_node)
        # print("Black: ", self.next_step_black)
        # print("White: ", self.next_step_white)

    def from2Dto1D(self, row, col):  # both row and col belong to [0, 8)
        return row * 8 + col

    def from1Dto2D(self, node):
        row = node // 8
        col = node % 8
        return [row, col]

    def change_configurtion(self, cur_pos, arr): # The position given by cur_pos has to be valid.
        # cur_pos = self.from2Dto1D(row, col)
        [row, col] = self.from1Dto2D(cur_pos)
        p = cur_pos
        can_flip = False
        valid_step = False
        # horizontal
        for i in range(1, 8 - col):
            if arr[p + i] == 0:
                break
            if arr[p + i] == self.cur_player:
                if i != 1:
                    can_flip = True
                    valid_step = True
                break
        if can_flip:
            for i in range(1, 8 - col):
                if arr[p + i] == self.cur_player:
                    break
                arr[p + i] = self.cur_player
            can_flip = False
        for i in range(1, col):
            if arr[p - i] == 0:
                break
            if arr[p - i] == self.cur_player:
                if i != 1:
                    can_flip = True
                    valid_step = True
                break
        if can_flip:
            for i in range(1, col):
                if arr[p - i] == self.cur_player:
                    break
                arr[p + i] = self.cur_player
            can_flip = False

        #vertical, diagnoal
        for slide in range(7, 10):
            while p + slide < 64:
                p += slide
                if arr[p] == 0:
                    break
                elif arr[p] == self.cur_player:
                    if p - cur_pos != slide:
                        valid_step = True
                        can_flip = True
            if can_flip:
                p = cur_pos
                while p + slide < 64:
                    p = p + slide
                    if arr[p] == self.cur_player:
                        break
                    arr[p] = self.cur_player
                can_flip = False

            while p - slide >= 0:
                p -= slide
                if arr[p] == 0:
                    break
                elif arr[p] == self.cur_player:
                    if cur_pos - p != slide:
                        valid_step = True
                        can_flip = True
            if can_flip:
                p = cur_pos
                while p - slide >= 0:
                    p = p - slide
                    if arr[p] == self.cur_player:
                        break
                    arr[p] = self.cur_player
                can_flip = False
        if valid_step:
            arr[cur_pos] = self.cur_player
            self.cur_player = 3 - self.cur_player
        return valid_step

    def run(self):
        l = self.selection(self.cur_player)
        self.expansion(random.choice(l), self.cur_player)
        for i in range(1000):
            self.simulation_path[self.BLACK].clear()
            self.simulation_path[self.WHITE].clear()
            self.simulation()
            self.backPropragation()

    def selection(self, player): # pick up the node with the highest score. Randomly choose one for tie
        l = []
        if player == self.BLACK:
            max_score = -1
            for node in self.next_step_black:
                [row, col] = self.from1Dto2D(node)
                score_tmp = self.score(row, col, self.c_black)
                if max_score < score_tmp:
                    max_score = score_tmp
                    l.clear()
                    l.append(node)
                elif max_score == score_tmp:
                    l.append(node)
        else:
            min_score = 9999
            for node in self.next_step_white:
                [row, col] = self.from1Dto2D(node)
                score_tmp = self.score(row, col, self.c_white)
                if min_score > score_tmp:
                    min_score = score_tmp
                    l.clear()
                    l.append(node)
                elif min_score == score_tmp:
                    l.append(node)
        return l

    def expansion(self, node, player):  # Expand the node in the real graph
        self.arr[node] = player
        if self.isEnd():
            cnt_b = 0
            cnt_w = 0
            for i in self.arr:
                if i == self.BLACK:
                    cnt_b += 1
                else:
                    cnt_w += 1
            if cnt_b > cnt_w:
                print("The Black wins!")
            else:
                print("The White wins!")
        else:
            self.change_configurtion(node, self.arr)
            self.arr_supposed = self.arr[:]
            self.closure.append(node)
            self.update_next_step(self.arr)

#   the machine run by itself
    def simulation(self):
        winner = self.isEnd()
        while not winner:
            if self.cur_player == self.BLACK:
                node = random.choice(self.next_step_black)
            else:
                node = random.choice(self.next_step_white)
            self.simulation_path[self.cur_player].append()
            self.change_configurtion(node, self.arr_supposed)
            self.update_next_step(self.arr_supposed)
            winner = self.isEnd()
        self.backPropragation(winner)

    def backPropragation(self, winner):
        for i in range(64):
            self.state_nodes[i]["cnt_total"] += 1
            if self.arr_supposed[i] == winner:
                self.state_nodes[i]["cnt_win"] += 1

    def showBoard(self, n): # the function to watch the board
        for i in range(n):
            for j in range(n):
                print(self.arr[self.from2Dto1D(i, j)], end=" ")
            print()

    def isEnd(self, arr):  # return 0 means not reach the end; Return black or white means the winner.
        fullCheckers = True  # dedicate if all
        onePlayerWin = True
        tmp = 0
        for i in arr:
            if i == 0:
                fullCheckers = False
            elif tmp == 0:
                tmp = i
            elif tmp != i:
                onePlayerWin = False
            if not fullCheckers and not onePlayerWin:
                return 0
        if fullCheckers:
            return arr[0]
        else:
            cntBlack = 0
            for i in range(64):
                if arr[i] == self.BLACK:
                    cntBlack += 1
            if cntBlack > 32:
                return self.BLACK
            else:
                return self.WHITE

    def score(self, row, col, c): # given the node, return the score of it
        cur_pos = self.from2Dto1D(row, col)
        cnt_win = self.state_nodes[cur_pos]["cnt_win"]
        cnt_total = self.state_nodes[cur_pos]["cnt_total"]
        if cnt_total == 0:
            return 0
        else:
            return cnt_win / cnt_total + c * math.sqrt(math.log(cnt_win, math.e) / cnt_total)

    def check_step_valid(self, row, col, player): # for the given player, to check if the given step is valid or not
        cur_pos = self.from2Dto1D(row, col)
        p = cur_pos
        valid_step = False
        # horizontal
        for i in range(1, 8 - col):
            if self.arr[p + i] == 0:
                break
            if self.arr[p + i] == self.cur_player:
                if i != 1:
                    valid_step = True
                break
        if valid_step:
            return valid_step
        for i in range(1, col):
            if self.arr[p - i] == 0:
                break
            if self.arr[p - i] == self.cur_player:
                if i != 1:
                    valid_step = True
                break
        if valid_step:
            return valid_step

        # vertical, diagnoal
        for slide in range(7, 10):
            p = cur_pos
            while p + slide < 64:
                p += slide
                if self.arr[p] == self.NULL:
                    break
                elif self.arr[p] == player:
                    if p - cur_pos != slide:
                        valid_step = True
                    break
            if valid_step:
                return valid_step
            p = cur_pos
            while p - slide >= 0:
                p -= slide
                if self.arr[p] == 0:
                    break
                elif self.arr[p] == player:
                    if cur_pos - p != slide:
                        valid_step = True
                    break
            if valid_step:
                return valid_step
        return valid_step

    def check_step_valid(self, cur_pos, player):
        col = cur_pos % 8
        p = cur_pos
        valid_step = False
        # horizontal
        for i in range(1, 8 - col):
            if self.arr[p + i] == self.NULL:
                break
            if self.arr[p + i] == player:
                if i != 1:
                    valid_step = True
                break
        if valid_step:
            if cur_pos == 37:
                print(1)
            return valid_step


        for i in range(1, col + 1):
            if self.arr[p - i] == self.NULL:
                break
            if self.arr[p - i] == player:
                if i != 1:
                    valid_step = True
                    # print("i ", i)
                    # print(player, " ", self.arr[35])
                break
        if valid_step:
            # if cur_pos == 37:
            #     print(2)
            return valid_step

        # vertical, diagnoal
        for slide in range(7, 10):
            p = cur_pos
            while p + slide < 64:
                p += slide
                if self.arr[p] == 0:
                    break
                elif self.arr[p] == player:
                    if p - cur_pos != slide:
                        valid_step = True
                    break
            if valid_step:
                # if cur_pos == 37:
                #     print(3)
                return valid_step

            p = cur_pos
            while p - slide >= 0:
                p -= slide
                if self.arr[p] == 0:
                    break
                elif self.arr[p] == player:
                    if cur_pos - p != slide:
                        valid_step = True
                    break
            if valid_step:
                # if cur_pos == 37:
                #     print(4)
                return valid_step

        return valid_step

tree = MCTS()
tree.run()