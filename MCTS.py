import random
import math
import pygame
import time


class MCTS(object):
    def __init__(self):
        self.NULL = 0
        self.BLACK = 1
        self.WHITE = 2
        self.c = 2

        self.c_train = [0, 5, 2]  # adapt c by AI vs AI
        self.winner_train = self.BLACK

        self.cur_player = self.BLACK

        self.arr = []  # this array is used for store the chessboard with size 8 * 8
        self.scores = []
        for i in range(64):
            self.arr.append(0)
            self.scores.append(0)
        self.arr[self.from2Dto1D(4, 4)] = self.arr[self.from2Dto1D(3, 3)] = self.BLACK
        self.arr[self.from2Dto1D(4, 3)] = self.arr[self.from2Dto1D(3, 4)] = self.WHITE

        self.arr_supposed = self.arr[:]  # The array for machine learning

        self.next_step_black = set()
        self.next_step_white = set()
        self.state_nodes = []  # each element is a directory containing times of exploration and times of win
        self.last_change = []
        for i in range(64):
            self.node = {}
            self.node["cnt_win"] = 0  # times to be chose
            self.node["cnt_total"] = 0
            self.state_nodes.append(self.node)

        self.closure = []  # array to store the positions of the fixed points
        self.closure_supposed = []
        self.closure.append(self.from2Dto1D(4, 4))
        self.closure.append(self.from2Dto1D(3, 4))
        self.closure.append(self.from2Dto1D(4, 3))
        self.closure.append(self.from2Dto1D(3, 3))
        self.simulation_path = [[], [], []]
        self.update_next_step(self.arr, self.closure)

        # 初始化模块，加一下稳一些
        pygame.init()
        self.cb = (0, 0, 0)  # cb=checkerboard=棋盘网格线颜色，darkgreen
        self.bg = (192, 192, 192)  # 背景颜色=蜜露色，bg=background
        self.black = (78, 120, 99)
        self.white = (255, 255, 255)
        self.screen_width = 800
        self.screen_height = 1000
        # 创建屏幕对象
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        # 界面背景颜色渲染，放在while中会不断覆盖格子
        self.screen.fill(self.bg)
        # 绘制网格线
        for i in range(8):
            pygame.draw.line(self.screen, self.cb, (i * 100, 0), (i * 100, self.screen_width - 1))
            pygame.draw.line(self.screen, self.cb, (0, i * 100), (self.screen_width - 1, i * 100))
        pygame.draw.line(self.screen, self.cb, (0, self.screen_width - 1),
                         (self.screen_width - 1, self.screen_width - 1))
        pygame.draw.line(self.screen, self.cb, (self.screen_width - 1, 0),
                         (self.screen_width - 1, self.screen_width - 1))
        # 界面的标题
        pygame.display.set_caption('黑白棋')

    def update_next_step(self, arr, closure):
        self.next_step_black.clear()
        self.next_step_white.clear()

        for closed_node in closure:
            tmp = {1, -1, 8, -8, 7, -7, 9, -9}
            for j in tmp:
                new_node = closed_node + j
                if 0 <= new_node < 64 and arr[new_node] == self.NULL:  # pos of new_node is within the map and null
                    if self.check_step_valid(arr, new_node,
                                             self.cur_player):  # check if new node is valid for cur player
                        if self.cur_player == self.BLACK:
                            self.next_step_black.add(new_node)
                        else:
                            self.next_step_white.add(new_node)

    def from2Dto1D(self, row, col):  # both row and col belong to [0, 8)
        return row * 8 + col

    def from1Dto2D(self, node):
        row = node // 8
        col = node % 8
        return [row, col]

    def change_configurtion(self, cur_pos, arr, closure):  # The position given by cur_pos has to be valid.
        # cur_pos = self.from2Dto1D(row, col)
        [row, col] = self.from1Dto2D(cur_pos)
        # print("Col: ", col)
        p = cur_pos
        can_flip = False
        valid_step = False
        # horizontal check
        for i in range(1, 8 - col):
            if arr[p + i] == self.NULL:
                break
            elif arr[p + i] == self.cur_player:
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

        for i in range(1, col + 1):
            if arr[p - i] == self.NULL:
                break
            elif arr[p - i] == self.cur_player:
                if i != 1:
                    can_flip = True
                    valid_step = True
                break
        if can_flip:
            for i in range(1, col + 1):
                if arr[p - i] == self.cur_player:
                    break
                arr[p - i] = self.cur_player
            can_flip = False

        # vertical, diagnoal
        for slide in range(7, 10):
            # some special cases

            p = cur_pos
            while p + slide < 64:
                if col == 0 and slide == 7:
                    break
                if col == 7 and slide == 9:
                    break
                p += slide
                [row_p, col_p] = self.from1Dto2D(p)
                if arr[p] == self.NULL:
                    break
                elif arr[p] == self.cur_player:
                    if p - cur_pos != slide:
                        valid_step = True
                        can_flip = True
                    break
                if col_p == 0 and slide == 7:
                    break
                if col_p == 7 and slide == 9:
                    break

            if can_flip:
                p = cur_pos
                while p + slide < 64:
                    p = p + slide
                    if arr[p] == self.cur_player:
                        break
                    arr[p] = self.cur_player
                can_flip = False

            p = cur_pos
            while p - slide >= 0:
                if col == 0 and slide == 9:
                    break
                if col == 7 and slide == 7:
                    break
                p -= slide

                if arr[p] == self.NULL:
                    break
                elif arr[p] == self.cur_player:
                    if cur_pos - p != slide:
                        valid_step = True
                        can_flip = True
                    break
                [row_p, col_p] = self.from1Dto2D(p)
                if col_p == 0 and slide == 9:
                    break
                if col_p == 7 and slide == 7:
                    break

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
            closure.append(cur_pos)
        return valid_step

    def selection(self, player):  # pick up the node with the highest score. Randomly choose one for tie
        l = []
        max_score = -1
        if player == self.BLACK:
            for node in self.next_step_black:
                [row, col] = self.from1Dto2D(node)
                score_tmp = self.score(row, col, self.c)
                if max_score < score_tmp:
                    max_score = score_tmp
                    l.clear()
                    l.append(node)
                elif max_score == score_tmp:
                    l.append(node)
        else:
            for node in self.next_step_white:
                [row, col] = self.from1Dto2D(node)
                score_tmp = self.score(row, col, self.c)
                # score_tmp = self.score(row, col, self.c[player]) # used for adapt c
                if max_score < score_tmp:
                    max_score = score_tmp
                    l.clear()
                    l.append(node)
                elif max_score == score_tmp:
                    l.append(node)
        return l

    def expansion(self, node, player):  # Expand the node in the real graph

        if self.isEnd(self.arr):
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
            self.change_configurtion(node, self.arr, self.closure)
            self.update_next_step(self.arr, self.closure)
            # print(list(self.next_step_white))
            # print(list(self.next_step_black))

    #   the machine run by itself

    def simulation(self):
        # print("player: ", self.cur_player)
        self.arr_supposed = self.arr[:]
        self.closure_supposed = self.closure[:]
        winner = self.isEnd(self.arr_supposed)
        self.simulation_path[self.BLACK].clear()
        self.simulation_path[self.WHITE].clear()
        choices_of_adver = 1
        cnt_black = 0
        cnt_white = 0
        while not winner:
            self.update_next_step(self.arr_supposed, self.closure_supposed)
            # print("next step white: ", self.next_step_white)
            node = 0
            if self.cur_player == self.BLACK:
                # print("Black: ", self.next_step_black)
                if len(list(self.next_step_black)) == 0:
                    self.cur_player = 3 - self.cur_player
                    # self.showBoard(8, self.arr_supposed)
                    if choices_of_adver == 0:
                        for i in range(64):
                            if self.arr_supposed[i] == self.BLACK:
                                cnt_black += 1
                            elif self.arr_supposed[i] == self.WHITE:
                                cnt_white += 1
                        if cnt_black > cnt_white:
                            winner = self.BLACK
                        else:
                            winner = self.WHITE
                        break
                    # exit(1)
                    choices_of_adver = 0
                    continue
                else:
                    node = random.choice(list(self.next_step_black))
                    choices_of_adver = 1
            else:
                # print("White: ", self.next_step_white)
                if len(list(self.next_step_white)) == 0:
                    self.cur_player = 3 - self.cur_player
                    # self.showBoard(8, self.arr_supposed)
                    if choices_of_adver == 0:
                        for i in range(64):
                            if self.arr_supposed[i] == self.BLACK:
                                cnt_black += 1
                            elif self.arr_supposed[i] == self.WHITE:
                                cnt_white += 1
                        if cnt_black > cnt_white:
                            winner = self.BLACK
                        else:
                            winner = self.WHITE
                        break
                    # exit(1)
                    choices_of_adver = 0
                    # exit(1)
                    continue
                else:
                    node = random.choice(list(self.next_step_white))
                    choices_of_adver = 1
            self.simulation_path[self.cur_player].append(node)
            self.change_configurtion(node, self.arr_supposed, self.closure_supposed)
            # test sentences
            # if 58 <= cnt < 63:
            #     print("player: ", 3 - self.cur_player)
            #     print("Closure: ", self.closure_supposed)
            #     if self.cur_player == 3 - self.WHITE:
            #         print("White next step: ", list(self.next_step_white), node)
            #     # self.showBoard(8, self.arr_supposed)
            #     else:
            #         print("Black next step: ", list(self.next_step_black), node)
            #     self.showBoard(8, self.arr_supposed)

            winner = self.isEnd(self.arr_supposed)
            # self.showBoard(8, self.arr_supposed)
            # print()
            # break
            # cnt += 1

        self.backPropragation(winner)

    def backPropragation(self, winner):
        for node in self.simulation_path[winner]:
            self.state_nodes[node]["cnt_win"] += 1
            self.state_nodes[node]["cnt_total"] += 1
        loser = 3 - winner
        for node in self.simulation_path[loser]:
            self.state_nodes[node]["cnt_total"] += 1

    def showBoard(self, n, arr):  # the function to watch the board
        for i in range(n):
            for j in range(n):
                print(arr[self.from2Dto1D(i, j)], end=" ")
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

    def score(self, row, col, c):  # given the node, return the score of it
        cur_pos = self.from2Dto1D(row, col)
        cnt_win = self.state_nodes[cur_pos]["cnt_win"]
        cnt_total = self.state_nodes[cur_pos]["cnt_total"]
        if cnt_total == 0 or cnt_win == 0:
            return 0
        else:
            return cnt_win / cnt_total + c * math.sqrt(math.log(cnt_win, math.e) / cnt_total)

    def check_step_valid(self, row, col, player):  # for the given player, to check if the given step is valid or not
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
        for i in range(1, col + 1):
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

    def check_step_valid(self, arr, cur_pos, player):
        col = cur_pos % 8
        p = cur_pos
        valid_step = False
        # horizontal check
        for i in range(1, 8 - col):  # [1 + col, 8)
            if arr[p + i] == player:
                if i != 1:
                    valid_step = True
                break
            elif arr[p + i] == self.NULL:
                break
        if valid_step:
            return valid_step

        for i in range(1, col + 1):  # [0, col - 1)
            if arr[p - i] == player:
                if i != 1:
                    valid_step = True
                    # print("i ", i)
                    # print(player, " ", self.arr[35])
                break
            elif arr[p - i] == self.NULL:
                break
        if valid_step:
            # if cur_pos == 37:
            #     print(2)
            return valid_step

        # vertical, diagnoal checking
        for slide in range(7, 10):
            p = cur_pos

            while p + slide < 64:
                if col == 0 and slide == 7:
                    break
                if col == 7 and slide == 9:
                    break
                p += slide

                if arr[p] == player:
                    if p - cur_pos != slide:
                        valid_step = True
                    break
                elif arr[p] == self.NULL:
                    break
                [row_p, col_p] = self.from1Dto2D(p)  # to check if p is valid
                if col_p == 0 and slide == 7:
                    break
                if col_p == 7 and slide == 9:
                    break
            if valid_step:
                # if cur_pos == 37:
                #     print(3)
                return valid_step

            p = cur_pos

            while p - slide >= 0:
                if col == 0 and slide == 9:
                    break
                if col == 7 and slide == 7:
                    break
                p -= slide

                if arr[p] == player:
                    if cur_pos - p != slide:
                        valid_step = True
                    break
                elif arr[p] == self.NULL:
                    break
                [row_p, col_p] = self.from1Dto2D(p)
                if col_p == 0 and slide == 9:
                    break
                if col_p == 7 and slide == 7:
                    break
            if valid_step:
                # if cur_pos == 37:
                #     print(4)
                return valid_step

        return valid_step

    def test_change_configuration(self):
        print("Test change_configuration:")
        self.change_configurtion(43, self.arr, self.closure)
        self.showBoard(8, self.arr)
        print()
        self.change_configurtion(42, self.arr, self.closure)
        self.showBoard(8, self.arr)

    def test_update_next_step(self):
        self.showBoard(8, self.arr)
        print("Black ", self.next_step_black)

        self.change_configurtion(34, self.arr, self.closure)
        self.showBoard(8, self.arr)
        self.update_next_step(self.arr, self.closure)
        print("White ", self.next_step_white)

        self.change_configurtion(42, self.arr, self.closure)
        self.showBoard(8, self.arr)
        self.update_next_step(self.arr, self.closure)
        print("Black ", self.next_step_black)

        self.change_configurtion(50, self.arr, self.closure)
        self.showBoard(8, self.arr)
        self.update_next_step(self.arr, self.closure)
        print("White ", self.next_step_white)

    def test_simulation(self):
        self.cur_player = self.BLACK
        self.expansion(43, self.arr)
        self.arr_supposed = self.arr[:]
        self.closure_supposed = self.closure[:]
        print("First borad:")
        self.showBoard(8, self.arr_supposed)

        # print(self.closure_supposed)

        self.update_next_step(self.arr_supposed, self.closure_supposed)
        # if self.cur_player == self.BLACK:
        #      node = random.choice(list(self.next_step_black))
        # else:
        #      node = random.choice(list(self.next_step_white))
        nodes = {44, 29, 26}
        for node in nodes:
            self.simulation_path[self.cur_player].append(node)
            self.change_configurtion(node, self.arr_supposed, self.closure_supposed)
            self.update_next_step(self.arr_supposed, self.closure_supposed)

            print("player: ", 3 - self.cur_player)
            if self.cur_player == 3 - self.WHITE:
                print(list(self.next_step_white), node)
                # self.showBoard(8, self.arr_supposed)
            else:
                print(list(self.next_step_black), node)
            self.showBoard(8, self.arr_supposed)

    def get2DPosition(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return [-1, -1]
                if event.type == pygame.MOUSEBUTTONDOWN:
                    [x, y] = event.pos
                    row = int(x / 100)
                    col = int(y / 100)
                    print(row, col)  # 当前在屏幕中的坐标
                    if row > 7 or col > 7:
                        return [-2, -2]
                    return [row, col]
                    # 将渲染的界面显示
            pygame.display.flip()

    def run(self):
        self.__init__()
        cnt_black = 0
        player = self.cur_player
        choice_defen = 1
        total_time = 0
        while not self.isEnd(self.arr):
            self.cur_player = player
            self.update_next_step(self.arr, self.closure)
            # print(self.cur_player)
            l = self.selection(player)
            if len(l) == 0:
                if choice_defen == 0:
                    break
                choice_defen = 0
                player = 3 - player
                continue
            else:
                choice_defen = 1
            ###############
            move1d = random.choice(l)
            red = [255, 0, 0]
            [row, col] = self.from1Dto2D(move1d)
            pygame.draw.rect(self.screen, red, ((col * 100 + 1, row * 100 + 1), (99, 99)))
            pygame.display.flip()
            self.expansion(move1d, player)
            ###############
            # over
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
            # print("Before simulation: \n")
            # self.showBoard(8, self.arr_supposed)
            # # print()
            # time.sleep(2)
            # calculate single time
            start_time = time.perf_counter()
            for i in range(10):
                # print(i)
                self.cur_player = player
                self.simulation()
            end_time = time.perf_counter()
            single_time = end_time - start_time
            total_time += single_time

            self.showtThetime(single_time, total_time)
            self.showBoard(8, self.arr)
            self.board(self.arr, player)
            # 棋盘
            print()
            player = 3 - player
        for i in range(64):
            if self.arr[i] == self.BLACK:
                cnt_black += 1
        if cnt_black > 64 - cnt_black:
            print("The Black wins!")
            textfont = pygame.font.SysFont(None, 30)
            congradulations = textfont.render("The Black wins!", True, self.black)
            self.screen.blit(congradulations, (310 + 1, 850 + 1))
            self.winner_train = self.BLACK
            pygame.display.flip()
        else:
            print("The White wins!")
            textfont = pygame.font.SysFont(None, 30)
            congradulations = textfont.render("The White wins!", True, self.white)
            self.screen.blit(congradulations, (310 + 1, 850 + 1))
            self.winner_train = self.WHITE
            pygame.display.flip()
        return True

    def playerVsAI(self):
        # 1 black 2white
        self.__init__()
        cnt_black = 0
        player = self.cur_player
        choice_defen = 1
        total_time = 0
        single_time = 0
        while not self.isEnd(self.arr):
            self.cur_player = player
            self.update_next_step(self.arr, self.closure)
            # print(self.cur_player)
            l = self.selection(player)
            if len(l) == 0:
                if choice_defen == 0:
                    break
                choice_defen = 0
                player = 3 - player
                continue
            else:
                choice_defen = 1

            move_1d = random.choice(l)  # black's turn aka AI's turn
            if player == 2:  # white's turn
                judge = 0
                while not judge:
                    [col, row] = self.get2DPosition()
                    if col == -2 and row == -2:
                        print("落子无效")
                    if col == -1 and row == -1:
                        return False
                    cur_pos = self.from2Dto1D(row, col)
                    if self.check_step_valid(self.arr, cur_pos, player) and self.arr[cur_pos] != 1:
                        move_1d = cur_pos
                        judge = 1
                        pygame.draw.rect(self.screen, self.white, ((col * 100 + 1, row * 100 + 1), (98, 98)))
                        pygame.display.flip()
                    else:
                        print("落子无效")

            # for i in l:
            #     print(self.from1Dto2D(i))
            self.expansion(move_1d, player)  # l是1D的
            # print("Before simulation: \n")
            # self.showBoard(8, self.arr_supposed)
            # print()
            start_time = time.perf_counter()
            for i in range(10):
                # print(i)
                self.simulation()
            end_time = time.perf_counter()
            single_time = end_time - start_time
            total_time += single_time
            self.showtThetime(single_time, total_time)

            self.showBoard(8, self.arr)
            print()
            # 棋盘
            self.board(self.arr, player)
            player = 3 - player
        self.showtThetime(single_time, total_time)
        self.board(self.arr, player)
        for i in range(64):
            if self.arr[i] == self.BLACK:
                cnt_black += 1
        if cnt_black > 64 - cnt_black:
            print("The Black wins!")
            textfont = pygame.font.SysFont(None, 30)
            congradulations = textfont.render("The Black wins!", True, self.black)
            self.screen.blit(congradulations, (300 + 1, 850 + 1))
            pygame.display.flip()
        else:
            print("The White wins!")
            textfont = pygame.font.SysFont(None, 30)
            congradulations = textfont.render("The White wins!", True, self.white)
            self.screen.blit(congradulations, (300 + 1, 850 + 1))
            pygame.display.flip()
        return True

    def initializeBoard(self):
        # 加载字体
        # 加载时间字体
        self.screen.fill(self.bg)
        textFont = pygame.font.SysFont(None, 50)
        textSurface = textFont.render("AI vs AI", True, (255, 255, 255))
        textSurface_1 = textFont.render("AI vs Player", True, (255, 255, 255))
        self.screen.blit(textSurface, (130 + 1, 875 + 1))
        self.screen.blit(textSurface_1, (502 + 1, 875 + 1))

        # 绘制网格线
        for i in range(8):
            pygame.draw.line(self.screen, self.cb, (i * 100, 0), (i * 100, self.screen_width - 1))
            pygame.draw.line(self.screen, self.cb, (0, i * 100), (self.screen_width - 1, i * 100))
        pygame.draw.line(self.screen, self.cb, (0, self.screen_width - 1),
                         (self.screen_width - 1, self.screen_width - 1))
        pygame.draw.line(self.screen, self.cb, (self.screen_width - 1, 0),
                         (self.screen_width - 1, self.screen_width - 1))
        # 界面的标题
        pygame.display.set_caption('黑白棋')
        pygame.display.flip()

    def showtThetime(self, single_time, total_time):
        # 加载时间字体
        self.screen.fill(self.bg)
        # 绘制网格线
        for i in range(8):
            pygame.draw.line(self.screen, self.cb, (i * 100, 0), (i * 100, self.screen_width - 1))
            pygame.draw.line(self.screen, self.cb, (0, i * 100), (self.screen_width - 1, i * 100))
        pygame.draw.line(self.screen, self.cb, (0, self.screen_width - 1),
                         (self.screen_width - 1, self.screen_width - 1))
        pygame.draw.line(self.screen, self.cb, (self.screen_width - 1, 0),
                         (self.screen_width - 1, self.screen_width - 1))
        # 界面的标题
        pygame.display.set_caption('黑白棋')

        textfont = pygame.font.SysFont(None, 30)
        single = textfont.render("single:" + str(round(single_time, 6)) + "sec", True, (255, 255, 255))
        total = textfont.render("total:" + str(round(total_time, 6)) + "sec", True, (255, 255, 255))
        self.screen.blit(single, (200 + 1, 950 + 1))
        self.screen.blit(total, (450 + 1, 950 + 1))
        pygame.display.flip()

    def board(self, arr, player):

        cnt_black = 0
        cnt_white = 0
        for i in self.arr:
            if i == 1:
                cnt_black += 1
            elif i == 2:
                cnt_white += 1
        textfont = pygame.font.SysFont(None, 30)
        black = textfont.render("black: " + str(cnt_black), True, self.black)
        white = textfont.render("white: " + str(cnt_white), True, self.white)
        self.screen.blit(black, (100 + 1, 900 + 1))
        self.screen.blit(white, (600 + 1, 900 + 1))
        for i in range(8):
            for j in range(8):
                chess_color = self.arr[self.from2Dto1D(i, j)]
                if chess_color == 1:
                    pygame.draw.rect(self.screen, self.black, ((j * 100 + 1, i * 100 + 1), (99, 99)))
                if chess_color == 2:
                    pygame.draw.rect(self.screen, self.white, ((j * 100 + 1, i * 100 + 1), (98, 98)))
        pygame.display.flip()

    def train_c(self, n):
        for i in range(n):
            cnt_black_wins = 0
            cnt_white_wins = 0
            for j in range(100):
                self.run()
                if self.winner_train == self.BLACK:
                    cnt_black_wins += 1
                else:
                    cnt_white_wins += 1
            if cnt_black_wins > cnt_white_wins:
                self.c_train[self.WHITE] = (self.c_train[self.BLACK] + self.c_train[self.WHITE]) / 2
            else:
                self.c_train[self.BLACK] = (self.c_train[self.BLACK] + self.c_train[self.WHITE]) / 2

    def mainActivity(self):
        self.initializeBoard()
        judge = 0
        while not judge:
            # quit playing
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    judge = 1
                if event.type == pygame.MOUSEBUTTONDOWN:
                    [x, y] = event.pos
                    row = int(x / 100)
                    col = int(y / 100)
                    print(x, y)  # 当前在屏幕中的坐标
                    if 100 < x < 300 and 850 < y < 950:
                        if not self.run():
                            return False
                        judge_1 = 0
                        while not judge_1:
                            for e in pygame.event.get():
                                if e.type == pygame.MOUSEBUTTONDOWN:
                                    self.initializeBoard()
                                    judge_1 = 1
                                if e.type == pygame.QUIT:
                                    judge_1 = 1
                                    judge = 1
                    if 500 < x < 700 and 850 < y < 950:
                        if not self.playerVsAI():
                            return False
                        judge_1 = 0
                        while not judge_1:
                            for e in pygame.event.get():
                                if e.type == pygame.MOUSEBUTTONDOWN:
                                    self.initializeBoard()
                                    judge_1 = 1
                                if e.type == pygame.QUIT:
                                    judge_1 = 1
                                    judge = 1

            # [col, row] = self.get2DPosition()
            # cur_pos = self.from2Dto1D(row, col)
            # if self.check_step_valid(self.arr, cur_pos, player):
            #     move_1d = cur_pos
            #     judge = 1
            # else:
            #     print("落子无效")


tree = MCTS()
tree.mainActivity()
# tree.test_simulation()
# tree.test_update_next_step()
# tree.test_change_configuration()
