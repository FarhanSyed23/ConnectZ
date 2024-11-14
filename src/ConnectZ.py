import numpy as np
import time
import tkinter as tk
from tkinter import messagebox
import threading

class GameBoard:
    def __init__(self, size=10, target=5):
        """
        Initializes the game board.

        :param size: Size of the board (size x size)
        :param target: Number of consecutive pieces required to win
        """
        self.size = size
        self.target = target
        self.board = np.full((size, size), ' ', dtype=str)
        self.turn = 'X'  # 'X' starts the game
        self.last_move = None
        self.game_over = False  # Flag to indicate if the game has ended

        # Initialize block counts
        self.user_blocks_remaining = 1
        self.ai_blocks_remaining = 1

        # Initialize power moves counts
        self.user_power_moves_remaining = 3
        self.ai_power_moves_remaining = 3

        # Store the winning sequence
        self.winning_sequence = []

        # Keep track of the last removed tile position
        self.last_removed_tile = None

        # Turn counter to track the number of moves made
        self.turn_count = 0

    def is_valid_move(self, x, y):
        """
        Checks if a move is valid (within bounds and on an empty cell).

        :param x: Row index
        :param y: Column index
        :return: True if valid, False otherwise
        """
        return (0 <= x < self.size and
                0 <= y < self.size and
                self.board[x][y] == ' ')

    def is_valid_block(self, x, y):
        """
        Checks if a block is valid (within bounds and on an empty cell).

        :param x: Row index
        :param y: Column index
        :return: True if valid, False otherwise
        """
        return self.is_valid_move(x, y)

    def is_valid_remove(self, x, y):
        """
        Checks if a remove action is valid (opponent's piece).

        :param x: Row index
        :param y: Column index
        :return: True if valid, False otherwise
        """
        opponent = 'O' if self.turn == 'X' else 'X'
        return (0 <= x < self.size and
                0 <= y < self.size and
                self.board[x][y] == opponent)

    def place_piece(self, x, y, switch_turn=True, move_type='normal'):
        """
        Places a piece on the board for the current player.

        :param x: Row index
        :param y: Column index
        :param switch_turn: Whether to switch the turn after placing the piece
        :param move_type: Type of move ('normal' or 'block')
        :return: Tuple (move_successful, win_detected)
        """
        if self.game_over:
            return False, False

        if move_type == 'normal':
            if self.is_valid_move(x, y):
                self.board[x][y] = self.turn
                self.last_move = (x, y)
                win = self.check_win(x, y)
                if win:
                    self.game_over = True
                elif switch_turn:
                    self.turn = 'O' if self.turn == 'X' else 'X'
                self.turn_count += 1  # Increment turn count
                return True, win
            else:
                return False, False

        elif move_type == 'block':
            if self.is_valid_block(x, y):
                self.board[x][y] = 'B'
                self.last_move = (x, y)
                # Deduct block count
                if self.turn == 'X':
                    self.user_blocks_remaining -= 1
                else:
                    self.ai_blocks_remaining -= 1
                # Blocking allows an additional move, so turn remains the same
                return True, True
            else:
                return False, False

    def block_tile(self, x, y):
        """
        Blocks a tile on the board for the current player.

        :param x: Row index
        :param y: Column index
        :return: Tuple (block_successful, additional_move_allowed)
        """
        return self.place_piece(x, y, move_type='block')

    def remove_tile(self, x, y, switch_turn=True):
        """
        Removes a tile from the board (opponent's piece).

        :param x: Row index
        :param y: Column index
        :param switch_turn: Whether to switch the turn after removing the piece
        :return: Tuple (remove_successful)
        """
        if self.is_valid_remove(x, y):
            self.board[x][y] = ' '
            # Deduct power move count
            if self.turn == 'X':
                self.user_power_moves_remaining -= 1
            else:
                self.ai_power_moves_remaining -= 1
            # Keep track of last removed tile
            self.last_removed_tile = (x, y)
            # Switch turns if required
            if switch_turn:
                self.turn = 'O' if self.turn == 'X' else 'X'
            self.turn_count += 1  # Increment turn count
            return True
        return False

    def check_win(self, x, y, update_winning_sequence=True):
        """
        Checks if the current move leads to a win.

        :param x: Row index
        :param y: Column index
        :param update_winning_sequence: Whether to update self.winning_sequence
        :return: True if the player wins, False otherwise
        """
        if self.board[x][y] == 'B' or self.board[x][y] == ' ':
            return False  # Blocked tiles or empty tiles do not contribute to a win

        directions = [(0, 1), (1, 0), (1, 1), (-1, 1)]
        player = self.board[x][y]
        for dx, dy in directions:
            count = 1  # Count the current piece
            sequence = [(x, y)]

            # Check in the positive direction
            nx, ny = x + dx, y + dy
            while (0 <= nx < self.size and
                   0 <= ny < self.size and
                   self.board[nx][ny] == player):
                count += 1
                sequence.append((nx, ny))
                nx += dx
                ny += dy

            # Check in the negative direction
            nx, ny = x - dx, y - dy
            while (0 <= nx < self.size and
                   0 <= ny < self.size and
                   self.board[nx][ny] == player):
                count += 1
                sequence.append((nx, ny))
                nx -= dx
                ny -= dy

            if count >= self.target:
                if update_winning_sequence:
                    self.winning_sequence = sequence
                return True
        return False

    def is_terminal(self):
        """
        Checks if the game has ended either by a win or a draw.

        :return: True if game is over, False otherwise
        """
        if self.last_move and self.check_win(*self.last_move, update_winning_sequence=False):
            return True
        return not any(self.board[x][y] == ' ' for x in range(self.size) for y in range(self.size))

    def evaluate(self):
        """
        Evaluates the board state.

        :return: Evaluation score
        """
        if self.last_move:
            player = self.board[self.last_move[0]][self.last_move[1]]
            if player == 'O' and self.check_win(*self.last_move, update_winning_sequence=False):
                return 10000  # AI wins
            elif player == 'X' and self.check_win(*self.last_move, update_winning_sequence=False):
                return -10000  # Human wins
        # If no win, evaluate board based on sequences
        return self.heuristic_evaluation()

    def heuristic_evaluation(self):
        """
        Heuristic evaluation of the board state, accounting for power moves.

        :return: Evaluation score
        """
        score = 0
        # Evaluate for both players
        for player in ['O', 'X']:
            player_score = 0
            for x in range(self.size):
                for y in range(self.size):
                    if self.board[x][y] == player:
                        player_score += self.evaluate_position(x, y, player)
            if player == 'O':
                score += player_score
                # Penalize AI for using power moves
                score -= (3 - self.ai_power_moves_remaining) * 50  # Adjust the penalty value as needed
            else:
                score -= player_score
                # Penalize opponent (user) for using power moves
                score += (3 - self.user_power_moves_remaining) * 50  # Adjust the penalty value as needed
        return score

    def evaluate_position(self, x, y, player):
        """
        Evaluate the position for potential sequences.

        :param x: Row index
        :param y: Column index
        :param player: 'X' or 'O'
        :return: Score for this position
        """
        score = 0
        directions = [(0, 1), (1, 0), (1, 1), (-1, 1)]
        for dx, dy in directions:
            count = 1
            open_ends = 0

            # Check in the positive direction
            nx, ny = x + dx, y + dy
            while (0 <= nx < self.size and
                   0 <= ny < self.size and
                   self.board[nx][ny] == player):
                count += 1
                nx += dx
                ny += dy
            if (0 <= nx < self.size and
                0 <= ny < self.size and
                self.board[nx][ny] == ' '):
                open_ends += 1

            # Check in the negative direction
            nx, ny = x - dx, y - dy
            while (0 <= nx < self.size and
                   0 <= ny < self.size and
                   self.board[nx][ny] == player):
                count += 1
                nx -= dx
                ny -= dy
            if (0 <= nx < self.size and
                0 <= ny < self.size and
                self.board[nx][ny] == ' '):
                open_ends += 1

            # Assign scores based on count and open ends
            if count >= self.target:
                score += 1000  # Immediate winning move
            elif count == self.target - 1 and open_ends > 0:
                score += 100
            elif count == self.target - 2 and open_ends > 1:
                score += 10
            elif count == self.target - 3 and open_ends > 1:
                score += 5
        return score

    def get_valid_moves(self, include_blocks=False, include_removes=False):
        """
        Retrieves all valid moves on the board, including 'place', 'block', and 'remove' actions.

        :param include_blocks: If True, include block actions if blocks are available
        :param include_removes: If True, include remove actions if power moves are available
        :return: List of tuples representing valid moves (action, x, y)
        """
        moves = set()
        # Iterate over the board to find existing pieces
        for x in range(self.size):
            for y in range(self.size):
                if self.board[x][y] != ' ' and self.board[x][y] != 'B':
                    # Add neighboring cells within 1 cell distance
                    for dx in [-1, 0, 1]:
                        for dy in [-1, 0, 1]:
                            nx, ny = x + dx, y + dy
                            if 0 <= nx < self.size and 0 <= ny < self.size:
                                if self.board[nx][ny] == ' ':
                                    moves.add(('place', nx, ny))
        # If no existing pieces, return the center
        if not moves:
            center = self.size // 2
            moves.add(('place', center, center))

        move_list = list(moves)

        if include_blocks:
            # Add block actions if blocks are remaining
            if self.turn == 'X' and self.user_blocks_remaining > 0:
                for x in range(self.size):
                    for y in range(self.size):
                        if self.board[x][y] == ' ':
                            move_list.append(('block', x, y))
            elif self.turn == 'O' and self.ai_blocks_remaining > 0:
                for x in range(self.size):
                    for y in range(self.size):
                        if self.board[x][y] == ' ':
                            move_list.append(('block', x, y))

        if include_removes:
            # Add remove actions if power moves are remaining
            opponent = 'O' if self.turn == 'X' else 'X'
            if self.turn == 'X' and self.user_power_moves_remaining > 0:
                for x in range(self.size):
                    for y in range(self.size):
                        if self.board[x][y] == opponent:
                            move_list.append(('remove', x, y))
            elif self.turn == 'O' and self.ai_power_moves_remaining > 0:
                for x in range(self.size):
                    for y in range(self.size):
                        if self.board[x][y] == opponent:
                            move_list.append(('remove', x, y))
        return move_list

    def minimax(self, depth, alpha, beta, maximizing_player):
        """
        Minimax algorithm with alpha-beta pruning.
        """
        if depth == 0 or self.is_terminal():
            return self.evaluate()

        # Store the original counts of power moves
        original_ai_power_moves = self.ai_power_moves_remaining
        original_user_power_moves = self.user_power_moves_remaining

        if maximizing_player:  # AI's turn
            max_eval = float('-inf')
            moves = self.get_valid_moves(include_blocks=True, include_removes=True)
            for move in moves:
                action, x, y = move

                # Avoid placing in the last removed tile
                if self.last_removed_tile and (x, y) == self.last_removed_tile:
                    continue

                # Avoid using power moves early in the game
                if action == 'remove' and self.turn_count < 10:
                    continue  # Skip remove actions early in the game

                if action == 'place':
                    self.board[x][y] = 'O'
                    self.last_move = (x, y)
                    self.turn_count += 1
                    eval = self.minimax(depth - 1, alpha, beta, False)
                    self.board[x][y] = ' '
                    self.turn_count -= 1
                elif action == 'block':
                    if self.ai_blocks_remaining <= 0:
                        continue
                    self.board[x][y] = 'B'
                    self.ai_blocks_remaining -= 1
                    eval = self.minimax(depth - 1, alpha, beta, False)
                    self.board[x][y] = ' '
                    self.ai_blocks_remaining += 1
                elif action == 'remove':
                    if self.ai_power_moves_remaining <= 0:
                        continue
                    removed_piece = self.board[x][y]
                    self.board[x][y] = ' '
                    self.ai_power_moves_remaining -= 1
                    self.turn_count += 1
                    eval = self.minimax(depth - 1, alpha, beta, False)
                    self.board[x][y] = removed_piece
                    self.ai_power_moves_remaining += 1
                    self.turn_count -= 1
                else:
                    eval = 0  # Should not reach here

                self.last_move = None

                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break

            # Restore power moves counts
            self.ai_power_moves_remaining = original_ai_power_moves
            self.user_power_moves_remaining = original_user_power_moves

            return max_eval
        else:  # Human's turn
            min_eval = float('inf')
            moves = self.get_valid_moves(include_blocks=True, include_removes=True)
            for move in moves:
                action, x, y = move

                if action == 'place':
                    self.board[x][y] = 'X'
                    self.last_move = (x, y)
                    self.turn_count += 1
                    eval = self.minimax(depth - 1, alpha, beta, True)
                    self.board[x][y] = ' '
                    self.turn_count -= 1
                elif action == 'block':
                    if self.user_blocks_remaining <= 0:
                        continue
                    self.board[x][y] = 'B'
                    self.user_blocks_remaining -= 1
                    eval = self.minimax(depth - 1, alpha, beta, True)
                    self.board[x][y] = ' '
                    self.user_blocks_remaining += 1
                elif action == 'remove':
                    if self.user_power_moves_remaining <= 0:
                        continue
                    removed_piece = self.board[x][y]
                    self.board[x][y] = ' '
                    self.user_power_moves_remaining -= 1
                    self.turn_count += 1
                    eval = self.minimax(depth - 1, alpha, beta, True)
                    self.board[x][y] = removed_piece
                    self.user_power_moves_remaining += 1
                    self.turn_count -= 1
                else:
                    eval = 0  # Should not reach here

                self.last_move = None

                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break

            # Restore power moves counts
            self.ai_power_moves_remaining = original_ai_power_moves
            self.user_power_moves_remaining = original_user_power_moves

            return min_eval

    def find_winning_move(self):
        """
        Finds a move that leads to immediate win.

        :return: Move tuple (action, x, y) or None
        """
        player = 'O'
        for x in range(self.size):
            for y in range(self.size):
                if self.board[x][y] == ' ':
                    # Temporarily place AI's piece to see if it can win
                    self.board[x][y] = player
                    if self.check_win(x, y, update_winning_sequence=False):
                        self.board[x][y] = ' '  # Undo move
                        return ('place', x, y)
                    self.board[x][y] = ' '  # Undo move
        return None

    def find_blocking_move(self):
        """
        Finds a move that blocks the opponent from winning.

        :return: Move tuple (action, x, y) or None
        """
        opponent = 'X'
        for x in range(self.size):
            for y in range(self.size):
                if self.board[x][y] == ' ':
                    # Temporarily place opponent's piece to see if they can win
                    self.board[x][y] = opponent
                    if self.check_win(x, y, update_winning_sequence=False):
                        self.board[x][y] = ' '  # Undo move
                        if self.ai_blocks_remaining > 0:
                            # Use block move
                            return ('block', x, y)
                        else:
                            # Place piece to block
                            return ('place', x, y)
                    self.board[x][y] = ' '  # Undo move
        return None

    def ai_move_decision(self, depth=3):
        """
        Determines the best move for the AI using the Minimax algorithm.

        :param depth: Depth of the Minimax search
        :return: Best move tuple (action, x, y)
        """
        best_score = float('-inf')
        best_move = None
        moves = self.get_valid_moves(include_blocks=True, include_removes=True)
        for move in moves:
            action, x, y = move

            # Avoid placing in the last removed tile
            if self.last_removed_tile and (x, y) == self.last_removed_tile:
                continue

            # Avoid using power moves early in the game
            if action == 'remove' and self.turn_count < 10:
                continue  # Skip remove actions early in the game

            if action == 'place':
                self.board[x][y] = 'O'
                self.last_move = (x, y)
                self.turn_count += 1
                score = self.minimax(depth - 1, float('-inf'), float('inf'), False)
                self.board[x][y] = ' '
                self.turn_count -= 1
            elif action == 'block':
                if self.ai_blocks_remaining <= 0:
                    continue
                self.board[x][y] = 'B'
                self.ai_blocks_remaining -= 1
                score = self.minimax(depth - 1, float('-inf'), float('inf'), False)
                self.board[x][y] = ' '
                self.ai_blocks_remaining += 1
            elif action == 'remove':
                if self.ai_power_moves_remaining <= 0:
                    continue
                removed_piece = self.board[x][y]
                self.board[x][y] = ' '
                self.ai_power_moves_remaining -= 1
                self.turn_count += 1
                score = self.minimax(depth - 1, float('-inf'), float('inf'), False)
                self.board[x][y] = removed_piece
                self.ai_power_moves_remaining += 1
                self.turn_count -= 1
            else:
                score = 0  # Should not reach here

            self.last_move = None

            if score > best_score:
                best_score = score
                best_move = move

        return best_move

    def ai_move(self, depth=3):
        """
        Determines and executes the AI's move.

        :param depth: Depth for the minimax algorithm
        :return: Tuple (selected_move, runtime, win_detected)
        """
        if self.game_over:
            return None, 0, False
        start_time = time.time()

        # Check for immediate winning moves
        winning_move = self.find_winning_move()
        if winning_move:
            move = winning_move
        else:
            # Check for immediate threats
            blocking_move = self.find_blocking_move()
            if blocking_move:
                move = blocking_move
            else:
                move = self.ai_move_decision(depth)

        runtime = time.time() - start_time
        win = False

        if move:
            action, x, y = move
            if action == 'place':
                self.place_piece(x, y, switch_turn=False)
                win = self.check_win(x, y)
            elif action == 'block':
                self.block_tile(x, y)
            elif action == 'remove':
                self.remove_tile(x, y, switch_turn=False)
            # After AI's move, switch turn back to human if necessary
            if action == 'place':
                if win:
                    return move, runtime, win
                self.turn = 'X'  # Switch turn to human
            elif action == 'remove':
                self.turn = 'X'  # Switch turn to human
            # Blocking allows an additional move, so turn remains the same
            return move, runtime, win
        else:
            return None, runtime, False  # No valid moves left

class ConnectZGUI:
    def __init__(self, root, size=10, target=5):
        """
        Initializes the GUI for the ConnectZ game.

        :param root: Tkinter root window
        :param size: Size of the board
        :param target: Target number to win
        """
        self.root = root
        self.root.title("ConnectZ")

        # Determine screen size
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # Define desired window size
        desired_width = 750
        desired_height = 880

        # Adjust window size if it exceeds screen size
        window_width = min(desired_width, screen_width - 10)
        window_height = min(desired_height, screen_height - 10)

        # Calculate position to center the window
        x = max((screen_width // 2) - (window_width // 2), 0)
        y = max((screen_height // 2) - (window_height // 2), 0)

        # Set window size and position
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")

        self.root.resizable(True, True)
        self.size = size
        self.target = target
        self.game = GameBoard(size, target)
        self.buttons = {}
        self.difficulty = "Medium"  # Default difficulty
        self.block_mode = False  # Flag to indicate if in block mode
        self.remove_mode = False  # Flag to indicate if in remove mode
        self.create_widgets()

    def create_widgets(self):
        """
        Creates all the GUI widgets.
        """
        # Create a frame for the board
        board_frame = tk.Frame(self.root)
        board_frame.pack(padx=20, pady=20)

        # Configure grid weights for fixed button sizes
        for i in range(self.size):
            board_frame.rowconfigure(i, weight=0)
            board_frame.columnconfigure(i, weight=0)

        # Create buttons for the board with increased size
        for x in range(self.size):
            for y in range(self.size):
                btn = tk.Button(board_frame, text=' ',
                                command=lambda x=x, y=y: self.handle_click(x, y),
                                font=('Helvetica', '12'),  # Increased font size
                                width=4,  # Increased width
                                height=2)  # Increased height
                btn.grid(row=x, column=y, padx=1, pady=1)  # Slightly increased padding
                self.buttons[(x, y)] = btn

        # Status frame
        status_frame = tk.Frame(self.root)
        status_frame.pack(pady=20, fill='x')

        # Status label
        self.status_label = tk.Label(status_frame, text="Player X's turn", font=('Helvetica', '16'), justify=tk.CENTER)
        self.status_label.pack(anchor='center', pady=5)

        # Block status labels
        self.user_block_label = tk.Label(status_frame, text="Your Blocks: 1", font=('Helvetica', '14'), fg='blue', justify=tk.CENTER)
        self.user_block_label.pack(anchor='center', pady=2)

        self.ai_block_label = tk.Label(status_frame, text="AI Blocks: 1", font=('Helvetica', '14'), fg='red', justify=tk.CENTER)
        self.ai_block_label.pack(anchor='center', pady=2)

        # Power move labels
        self.user_power_label = tk.Label(status_frame, text="Your Power Moves: 3", font=('Helvetica', '14'), fg='green', justify=tk.CENTER)
        self.user_power_label.pack(anchor='center', pady=2)

        self.ai_power_label = tk.Label(status_frame, text="AI Power Moves: 3", font=('Helvetica', '14'), fg='orange', justify=tk.CENTER)
        self.ai_power_label.pack(anchor='center', pady=2)

        # Frame for controls (Difficulty, Block, Remove, Help, and Restart)
        control_frame = tk.Frame(self.root)
        control_frame.pack(pady=20)

        # Difficulty Level Selection
        tk.Label(control_frame, text="Difficulty:", font=('Helvetica', '14')).pack(side=tk.LEFT, padx=10)
        self.difficulty_var = tk.StringVar(value=self.difficulty)
        difficulties = ["Easy", "Medium", "Hard"]
        self.difficulty_menu = tk.OptionMenu(control_frame, self.difficulty_var, *difficulties)
        self.difficulty_menu.config(font=('Helvetica', '12'))
        self.difficulty_menu.pack(side=tk.LEFT, padx=10)

        # Block Button
        self.block_button = tk.Button(control_frame, text="Block", command=self.activate_block_mode, bg='grey',
                                      font=('Helvetica', '12'), width=10)
        self.block_button.pack(side=tk.LEFT, padx=10)

        # Remove Button
        self.remove_button = tk.Button(control_frame, text="Remove", command=self.activate_remove_mode,
                                       bg='light green', font=('Helvetica', '12'), width=10)
        self.remove_button.pack(side=tk.LEFT, padx=10)

        # Help Button
        self.help_button = tk.Button(control_frame, text="Rules", command=self.show_help, bg='light yellow',
                                     font=('Helvetica', '12'), width=10)
        self.help_button.pack(side=tk.LEFT, padx=10)

        # Restart Button
        self.restart_button = tk.Button(control_frame, text="Restart Game", command=self.restart_game,
                                        font=('Helvetica', '12'), width=12)
        self.restart_button.pack(side=tk.LEFT, padx=10)

        self.update_buttons()  # Initialize button states

    def get_minimax_depth(self):
        """
        Determines the Minimax depth based on selected difficulty.

        :return: Integer representing depth
        """
        difficulty = self.difficulty_var.get()
        if difficulty == "Easy":
            return 2
        elif difficulty == "Medium":
            return 3
        elif difficulty == "Hard":
            return 4
        else:
            return 3  # Default to Medium if unknown

    def handle_click(self, x, y):
        """
        Handles the player's move when a board button is clicked.

        :param x: Row index
        :param y: Column index
        """
        if self.game.game_over:
            messagebox.showinfo("Game Over", "The game has ended. Please restart to play again.")
            return

        if self.game.turn != 'X':
            messagebox.showwarning("Not Your Turn", "It's not your turn!")
            return

        if self.remove_mode:
            # Attempt to remove the opponent's tile
            if self.game.user_power_moves_remaining <= 0:
                messagebox.showwarning("No Power Moves Left", "You have no power moves remaining.")
                self.remove_mode = False
                self.remove_button.config(relief=tk.RAISED)
                self.update_buttons()
                return

            cell = self.game.board[x][y]
            if cell == 'O':
                success = self.game.remove_tile(x, y)  # switch_turn=True by default for user
                if success:
                    btn = self.buttons[(x, y)]
                    btn.config(text=' ', state='disabled', bg='SystemButtonFace')
                    self.update_power_move_labels()
                    self.status_label.config(text=f"You removed AI's tile at ({x}, {y}).\nAI's turn.")
                    self.remove_mode = False
                    self.remove_button.config(relief=tk.RAISED)
                    self.disable_all_buttons()
                    self.update_buttons()
                    self.root.after(100, self.ai_move)
                    self.check_draw_after_move()
                else:
                    messagebox.showinfo("Removal Failed", "Failed to remove the tile.")
                    self.remove_mode = False
                    self.remove_button.config(relief=tk.RAISED)
                    self.update_buttons()
            elif cell == 'X':
                messagebox.showwarning("Invalid Remove", "You can't remove your own move.")
                self.remove_mode = False
                self.remove_button.config(relief=tk.RAISED)
                self.update_buttons()
            elif cell == 'B':
                messagebox.showwarning("Invalid Remove", "You can't remove a blocked tile.")
                self.remove_mode = False
                self.remove_button.config(relief=tk.RAISED)
                self.update_buttons()
            else:  # cell == ' '
                messagebox.showwarning("Invalid Remove", "You can't remove an empty tile.")
                self.remove_mode = False
                self.remove_button.config(relief=tk.RAISED)
                self.update_buttons()
            return

        if self.block_mode:
            # Attempt to block the selected tile
            if self.game.user_blocks_remaining <= 0:
                messagebox.showwarning("No Blocks Left", "You have no block moves remaining.")
                self.block_mode = False
                self.block_button.config(relief=tk.RAISED)
                self.update_buttons()
                return

            success, additional_move_allowed = self.game.block_tile(x, y)
            if success:
                btn = self.buttons[(x, y)]
                btn.config(text='B', state='disabled', bg='grey', disabledforeground='black')
                self.update_block_labels()
                self.status_label.config(text=f"You blocked tile at ({x}, {y}).\nMake your next move.")
                self.block_mode = False
                self.block_button.config(relief=tk.RAISED)
                self.update_buttons()
                # Allow the user to make an additional move (i.e., another block or placement)
                return
            else:
                messagebox.showwarning("Invalid Block", "This cell is already occupied or out of bounds.")
            return
        else:
            # Regular piece placement
            valid, win = self.game.place_piece(x, y, move_type='normal')
            if not valid:
                messagebox.showwarning("Invalid Move", "This cell is already occupied or out of bounds.")
                return

            # Update button appearance for user move
            btn = self.buttons[(x, y)]
            btn.config(text='X', state='disabled', bg='light blue', disabledforeground='black')

            if win:
                self.status_label.config(text="Player X wins!")
                self.end_game()
                return
            else:
                self.check_draw_after_move()
                self.status_label.config(text="AI is thinking...")
                self.disable_all_buttons()
                self.update_buttons()
                # Let the AI make its move after a short delay
                self.root.after(100, self.ai_move)  # Reduced delay for faster response

    def check_draw_after_move(self):
        """
        Checks if the game is a draw after a move and handles it.
        """
        if self.game.is_terminal() and not self.game.check_win(*self.game.last_move, update_winning_sequence=False):
            self.status_label.config(text="It's a draw!")
            self.end_game()

    def activate_block_mode(self):
        """
        Activates the block mode, allowing the user to block a tile on the next click.
        """
        if self.game.user_blocks_remaining <= 0:
            messagebox.showwarning("No Blocks Left", "You have no block moves remaining.")
            return

        if self.game.turn != 'X':
            messagebox.showwarning("Not Your Turn", "It's not your turn!")
            return

        self.block_mode = True
        self.remove_mode = False
        self.block_button.config(relief=tk.SUNKEN)
        self.remove_button.config(relief=tk.RAISED)
        self.status_label.config(text="Select a tile to block.")
        self.update_buttons()

    def activate_remove_mode(self):
        """
        Activates the remove mode, allowing the user to remove an AI tile.
        """
        if self.game.user_power_moves_remaining <= 0:
            messagebox.showwarning("No Power Moves Left", "You have no power moves remaining.")
            return

        if self.game.turn != 'X':
            messagebox.showwarning("Not Your Turn", "It's not your turn!")
            return

        self.remove_mode = True
        self.block_mode = False
        self.remove_button.config(relief=tk.SUNKEN)
        self.block_button.config(relief=tk.RAISED)
        self.status_label.config(text="Select an AI tile to remove.")
        self.update_buttons()

    def show_help(self):
        """
        Opens a new window displaying the game rules.
        """
        help_window = tk.Toplevel(self.root)
        help_window.title("ConnectZ - Rulebook")

        # Set the window size to be large but within screen bounds
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = min(int(screen_width * 2 / 3), 800)
        window_height = min(int(screen_height * 2 / 3), 600)
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        help_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        help_window.resizable(True, True)

        # Set background color
        help_window.configure(bg='#f0f0f0')

        # Create a canvas for scrolling
        canvas = tk.Canvas(help_window, bg='#f0f0f0')
        scrollbar = tk.Scrollbar(help_window, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#f0f0f0')

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Function to handle mousewheel scrolling
        def _on_mousewheel(event):
            if event.num == 4:  # Linux scroll up
                canvas.yview_scroll(-1, "units")
            elif event.num == 5:  # Linux scroll down
                canvas.yview_scroll(1, "units")
            else:  # Windows and MacOS
                canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        # Bind mousewheel events when cursor enters and leaves the canvas
        def _bind_to_mousewheel(event):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
            canvas.bind_all("<Button-4>", _on_mousewheel)
            canvas.bind_all("<Button-5>", _on_mousewheel)

        def _unbind_from_mousewheel(event):
            canvas.unbind_all("<MouseWheel>")
            canvas.unbind_all("<Button-4>")
            canvas.unbind_all("<Button-5>")

        # Bind events to scrollable_frame
        scrollable_frame.bind("<Enter>", _bind_to_mousewheel)
        scrollable_frame.bind("<Leave>", _unbind_from_mousewheel)

        # Now add content to scrollable_frame
        # Use Labels with appropriate fonts and styles

        # Create a list to keep track of content labels
        content_widgets = []

        # Title
        title_label = tk.Label(scrollable_frame, text="ConnectZ - Rulebook", font=("Helvetica", 20, "bold"), fg="dark blue", bg='#f0f0f0')
        title_label.pack(pady=(20, 10), fill='x', expand=True)
        content_widgets.append(title_label)

        # Sections
        sections = [
            ("1. Objective", "The goal of ConnectZ is to be the first player to align a consecutive sequence of 5 pieces horizontally, vertically, or diagonally on a 10x10 grid."),
            ("2. Players", "There are two players:\n\n        • Player X (Human)\n        • Player O (AI)"),
            ("3. Gameplay", "Starting the Game:\n\n        • Player X always makes the first move.\n\nPlacing Pieces:\n\n        • Click on any empty tile to place your piece (X). The piece will occupy the selected tile and change its color to light blue.\n\nBlocking Tiles:\n\nEach player has 1 block move available. To block a tile:\n\n        1. Click the Block button.\n        2. Select an empty tile to block. The tile will display a 'B' and change its color to grey.\n        3. Blocking a tile allows you to make an additional move.\n\nRemoving Tiles:\n\nEach player has 3 power moves to remove an opponent's piece. To remove a tile:\n\n        1. Click the Remove button.\n        2. Select an AI tile (O) to remove. The tile will be cleared and revert to an empty state.\n        3. Removing a tile switches the turn to the opponent."),
            ("4. AI Behavior", "The AI uses the Minimax algorithm with alpha-beta pruning to decide its moves. You can set the AI's difficulty level to Easy, Medium, or Hard, which adjusts the depth of the Minimax search:\n\n        • Easy: Depth 1\n        • Medium: Depth 2\n        • Hard: Depth 3"),
            ("5. Winning the Game", "Align 5 of your pieces (X) consecutively in any direction (horizontal, vertical, or diagonal) to win. The AI (O) follows the same objective. If the board is filled without any player achieving the objective, the game ends in a draw."),
            ("6. Restarting the Game", "Click the Restart Game button at any time to reset the board and start a new game."),
            ("7. Status Indicators", ""),  # We'll handle this section separately
            ("8. Additional Information", "After each AI move, the status will display the action taken by the AI, including the tile coordinates and the computation time. The winning sequence will be highlighted in gold at the end of the game."),
            ("", "Enjoy playing ConnectZ!"),
        ]

        for heading, content in sections:
            if heading:
                heading_label = tk.Label(scrollable_frame, text=heading, font=("Helvetica", 16, "bold"), fg="blue", bg='#f0f0f0', anchor='w')
                heading_label.pack(anchor="w", pady=(15, 5), padx=20, fill='x')
                content_widgets.append(heading_label)
            if heading == "7. Status Indicators":
                # Create a Text widget for this section
                content_text = tk.Text(scrollable_frame, font=("Times New Roman", 13), wrap='word', bg='#f0f0f0', bd=0, height=6)
                content_text.pack(anchor="w", pady=5, padx=20, fill='x')

                # Insert the content with tags
                content_text.insert('end', '• ')
                content_text.insert('end', 'Your Blocks', 'your_blocks')
                content_text.insert('end', ': Shows the number of block moves you have remaining.\n')

                content_text.insert('end', '• ')
                content_text.insert('end', 'AI Blocks', 'ai_blocks')
                content_text.insert('end', ': Shows the number of block moves the AI has remaining.\n')

                content_text.insert('end', '• ')
                content_text.insert('end', 'Your Power Moves', 'your_power_moves')
                content_text.insert('end', ': Shows the number of power moves you have remaining to remove AI tiles.\n')

                content_text.insert('end', '• ')
                content_text.insert('end', 'AI Power Moves', 'ai_power_moves')
                content_text.insert('end', ': Shows the number of power moves the AI has remaining to remove your tiles.\n')

                # Configure tags for colors
                content_text.tag_config('your_blocks', foreground='blue', font=("Times New Roman", 13, 'bold'))
                content_text.tag_config('ai_blocks', foreground='red', font=("Times New Roman", 13, 'bold'))
                content_text.tag_config('your_power_moves', foreground='green', font=("Times New Roman", 13, 'bold'))
                content_text.tag_config('ai_power_moves', foreground='gold', font=("Times New Roman", 13, 'bold'))

                # Disable editing
                content_text.config(state='disabled')

                content_widgets.append(content_text)
            else:
                content_label = tk.Label(scrollable_frame, text=content, font=("Times New Roman", 13), wraplength=window_width - 60, justify="left", bg='#f0f0f0', anchor='w')
                content_label.pack(anchor="w", pady=5, padx=20, fill='x')
                content_widgets.append(content_label)

        # Add some space at the end
        spacer = tk.Label(scrollable_frame, text="", bg='#f0f0f0')
        spacer.pack(pady=20)

        # Function to update wraplengths of labels
        def update_wraplengths(event):
            new_width = help_window.winfo_width()
            wraplength = new_width - 60  # Adjust as needed
            for widget in content_widgets:
                if isinstance(widget, tk.Label):
                    widget.config(wraplength=wraplength)
                    widget.update_idletasks()

        # Bind the function to the Configure event of the help_window
        help_window.bind("<Configure>", update_wraplengths)

    def ai_move(self):
        """
        Handles the AI's move.
        """
        if self.game.game_over:
            return

        # Disable all buttons to prevent user interaction during AI's turn
        self.disable_all_buttons()

        # Start AI move in a separate thread to keep GUI responsive
        threading.Thread(target=self.perform_ai_move, daemon=True).start()

    def perform_ai_move(self):
        """
        Performs the AI's move and updates the GUI accordingly.
        """
        depth = self.get_minimax_depth()
        move, runtime, win = self.game.ai_move(depth)

        # Update the GUI on the main thread
        self.root.after(0, self.update_ai_move, move, runtime, win)

    def update_ai_move(self, move, runtime, win):
        """
        Updates the GUI based on the AI's move.

        :param move: Tuple (action, x, y) of AI's move
        :param runtime: Time taken for AI to decide
        :param win: Boolean indicating if AI won
        """
        if move:
            action, x, y = move
            if action == 'place':
                btn = self.buttons[(x, y)]
                btn.config(text='O', state='disabled', bg='light coral', disabledforeground='black')

                if win:
                    self.status_label.config(text=f"AI placed at ({x}, {y}) in {runtime:.2f} seconds.\nAI wins!")
                    self.end_game()
                    return
                else:
                    self.status_label.config(text=f"AI placed at ({x}, {y}) in {runtime:.2f} seconds.\nPlayer X's turn.")
            elif action == 'block':
                btn = self.buttons[(x, y)]
                btn.config(text='B', state='disabled', bg='grey', disabledforeground='black')
                self.update_block_labels()
                self.status_label.config(text=f"AI blocked tile at ({x}, {y}) in {runtime:.2f} seconds.\nAI is making an additional move.")

                # AI makes an additional move since blocking allows it
                additional_move, additional_runtime, additional_win = self.game.ai_move(self.get_minimax_depth())
                if additional_move:
                    add_action, add_x, add_y = additional_move
                    if add_action == 'place':
                        add_btn = self.buttons[(add_x, add_y)]
                        add_btn.config(text='O', state='disabled', bg='light coral', disabledforeground='black')
                        if additional_win:
                            self.status_label.config(text=f"AI placed at ({add_x}, {add_y}) in {additional_runtime:.2f} seconds.\nAI wins!")
                            self.end_game()
                            return
                        else:
                            self.status_label.config(text=f"AI placed at ({add_x}, {add_y}) in {additional_runtime:.2f} seconds.\nPlayer X's turn.")
                    elif add_action == 'block':
                        add_btn = self.buttons[(add_x, add_y)]
                        add_btn.config(text='B', state='disabled', bg='grey', disabledforeground='black')
                        self.update_block_labels()
                        self.status_label.config(text=f"AI blocked another tile at ({add_x}, {add_y}) in {additional_runtime:.2f} seconds.\nPlayer X's turn.")
                    elif add_action == 'remove':
                        # Perform remove
                        self.game.remove_tile(add_x, add_y, switch_turn=False)  # Switch turn after removal
                        add_btn = self.buttons[(add_x, add_y)]
                        add_btn.config(text=' ', state='disabled', bg='SystemButtonFace')
                        self.update_power_move_labels()
                        self.status_label.config(text=f"AI removed your tile at ({add_x}, {add_y}) in {additional_runtime:.2f} seconds.\nPlayer X's turn.")
            elif action == 'remove':
                # Perform remove
                self.game.remove_tile(x, y, switch_turn=True)  # Switch turn after removal
                btn = self.buttons[(x, y)]
                btn.config(text=' ', state='disabled', bg='SystemButtonFace')
                self.update_power_move_labels()
                self.status_label.config(text=f"AI removed your tile at ({x}, {y}) in {runtime:.2f} seconds.\nPlayer X's turn.")
            else:
                # No valid moves left, it's a draw
                self.status_label.config(text="It's a draw!")
                self.end_game()
                return

            # Check for draw after AI's move
            self.check_draw_after_ai_move()

            # Re-enable buttons for the player's turn
            self.enable_all_buttons()
            self.update_buttons()
            # Update the status label to indicate it's the player's turn
            if not self.game.game_over and action != 'block':  # Avoid overwriting if additional move is made
                self.game.turn = 'X'  # Switch turn back to user
        else:
            # No valid moves left, it's a draw!
            self.status_label.config(text="It's a draw!")
            self.end_game()
            return

    def check_draw_after_ai_move(self):
        """
        Checks if the game is a draw after the AI's move and handles it.
        """
        if self.game.is_terminal() and not self.game.check_win(*self.game.last_move, update_winning_sequence=False):
            self.status_label.config(text="It's a draw!")
            self.end_game()

    def disable_all_buttons(self):
        """
        Disables all board buttons to prevent user interaction.
        """
        for btn in self.buttons.values():
            btn.config(state='disabled')

    def enable_all_buttons(self):
        """
        Enables all board buttons that are empty for user interaction.
        """
        for (x, y), btn in self.buttons.items():
            if self.game.board[x][y] == ' ':
                btn.config(state='normal')
            elif self.game.board[x][y] == 'B':
                btn.config(state='disabled')

    def update_buttons(self):
        """
        Updates the buttons based on the current mode.
        """
        for (x, y), btn in self.buttons.items():
            cell = self.game.board[x][y]
            if self.remove_mode:
                # Enable all buttons
                btn.config(state='normal')
                # Set the text and appearance accordingly
                if cell == 'O':
                    btn.config(text='O', bg='light coral', disabledforeground='black')
                elif cell == 'X':
                    btn.config(text='X', bg='light blue', disabledforeground='black')
                elif cell == 'B':
                    btn.config(text='B', bg='grey', disabledforeground='black')
                elif cell == ' ':
                    btn.config(text=' ', bg='SystemButtonFace')
            elif self.block_mode:
                if cell == ' ':
                    btn.config(text=' ', state='normal', bg='SystemButtonFace')
                else:
                    btn.config(state='disabled')
            else:
                if cell == ' ':
                    btn.config(text=' ', state='normal', bg='SystemButtonFace')
                elif cell == 'X':
                    btn.config(text='X', state='disabled', bg='light blue', disabledforeground='black')
                elif cell == 'O':
                    btn.config(text='O', state='disabled', bg='light coral', disabledforeground='black')
                elif cell == 'B':
                    btn.config(text='B', state='disabled', bg='grey', disabledforeground='black')

    def highlight_winning_sequence(self):
        """
        Highlights the winning sequence by changing button backgrounds to gold.
        """
        if not self.game.winning_sequence:
            return

        for pos in self.game.winning_sequence:
            self.buttons[pos]['bg'] = 'gold'

    def end_game(self):
        """
        Handles the end of the game by disabling all buttons and highlighting the winning sequence.
        """
        self.game.game_over = True
        self.disable_all_buttons()
        self.update_buttons()
        self.highlight_winning_sequence()
        self.root.update_idletasks()  # Ensure the GUI updates before showing the message

        if self.game.check_win(*self.game.last_move, update_winning_sequence=False):
            if self.game.turn == 'X':
                messagebox.showinfo("Game Over", "Player X wins! Congratulations!")
            else:
                messagebox.showinfo("Game Over", "AI wins! Better luck next time.")
        else:
            messagebox.showinfo("Game Over", "It's a draw! No more viable moves.")

    def restart_game(self):
        """
        Restarts the game by resetting the game board and GUI components.
        """
        confirm = messagebox.askyesno("Restart Game", "Are you sure you want to restart the game?")
        if confirm:
            # Reset the game board
            self.game = GameBoard(self.size, self.target)
            self.game.turn = 'X'
            self.game.game_over = False
            self.block_mode = False
            self.remove_mode = False
            self.block_button.config(relief=tk.RAISED)
            self.remove_button.config(relief=tk.RAISED)

            # Reset all buttons
            for (x, y), btn in self.buttons.items():
                btn.config(text=' ', state='normal', bg='SystemButtonFace')

            # Reset labels
            self.update_block_labels()
            self.update_power_move_labels()

            # Update status label
            self.status_label.config(text="Player X's turn")
            self.update_buttons()

    def update_block_labels(self):
        """
        Updates the block count labels for both user and AI.
        """
        self.user_block_label.config(text=f"Your Blocks: {self.game.user_blocks_remaining}")
        self.ai_block_label.config(text=f"AI Blocks: {self.game.ai_blocks_remaining}")

    def update_power_move_labels(self):
        """
        Updates the power move count labels for both user and AI.
        """
        self.user_power_label.config(text=f"Your Power Moves: {self.game.user_power_moves_remaining}")
        self.ai_power_label.config(text=f"AI Power Moves: {self.game.ai_power_moves_remaining}")

def main():
    root = tk.Tk()
    gui = ConnectZGUI(root, size=10, target=5)
    root.mainloop()

if __name__ == "__main__":
    main()
