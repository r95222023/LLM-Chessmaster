
from dotenv import load_dotenv
import logging
from langchain import hub
from langchain.agents import AgentExecutor, create_react_agent
from langgraph.constants import Send
from langgraph.graph import END, StateGraph, START
from langgraph.checkpoint.memory import MemorySaver

from langchain.globals import set_verbose, set_debug
from typing import List, TypedDict

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from typing import List

import chess

class GraphState(TypedDict):
    turn: str
    winner: str
    user_input: str
    board_states: list
    moves: list
    messages: list
    comments: list

def get_user_input(board):
    legal_moves = ", ".join([str(move) for move in board.legal_moves])
    print(f"Possible moves are: {legal_moves}")
    user_input = input("It's your turn. Please make your move.")
    return user_input

def create_llm_ai_player(agent):
    def ai_player(board):
        turn = 'white' if board.turn == chess.WHITE else 'black'
        board_state = board.fen()
        legal_moves = ", ".join([str(move) for move in board.legal_moves])
        result = agent.invoke(board_state, turn, legal_moves)
        # move = chess.Move.from_uci(result.move)
        return result.move, result.comment
    return ai_player

def create_stock_fish_ai_player(stock_fish_path, skill_level=0):
    engine = chess.engine.SimpleEngine.popen_uci(stock_fish_path)
    # Configure Stockfish to a specific skill level
    engine.configure({"Skill Level": skill_level})
    def ai_player(board):
        result = engine.play(board, chess.engine.Limit(time=0.001))
        move = result.move
        return move, ""
    return ai_player


class ChessIterable:
    def __init__(self, app, config):
        initial_state = config['initial_state']

        self.app = app
        self.state_values = initial_state
        # self.stream = self.app.stream(initial_state, config, stream_mode="values")
        self.config = config

    def get_state(self):
        return self.app.get_state(self.config)

    def next(self, user_input=None):
        should_go = True
        state = None
        for event in self.app.stream(self.state_values, self.config, stream_mode="values"):
            pass
        # while should_go:
        #     self.iter.__next__()
        #     state = self.get_state()
        #     if state.next[0] == "interruption_node":
        #         should_go =False
        self.app.update_state(self.config, {"user_input": user_input}, as_node="interruption_node")

        continued_stream = self.app.stream(None, self.config, stream_mode="values")

        it = iter(continued_stream)
        it.__next__() # interruption node
        results = it.__next__() # player node

        state = self.get_state()
        self.state_values = state.values
        return results


class Chess:
    def __init__(self, ai_player=None, user_player=get_user_input, config=None, player_config=None, board_state=None, verbose=False, comment=True, max_moves=10):
        logger = logging.getLogger()
        if verbose:
            logging.basicConfig(level=logging.INFO)
        else:
            logging.basicConfig(level=logging.ERROR)

        self.compiled = False
        self.workflow = None
        self.ai_player = ai_player
        self.user_player = get_user_input

        # self.workflow = StateGraph(GraphState)
        self.comment = comment
        self.max_moves = max_moves
        self.config = config or {"configurable": {"thread_id": "1"}}
        self.player_config = player_config or {'white': 'ai', 'black':'ai'}
        if not ai_player:
            self.set_player('white', 'user')
            self.set_player('black', 'user')
        else:
            self.set_player('white', self.player_config['white'])
            self.set_player('black', self.player_config['black'])
        # Initialize a chess board
        self.board = chess.Board(board_state) if board_state else chess.Board()

    def set_player(self, color, player_type):
        self.player_config[color] = player_type

    def set_config(self, config):
        self.config = config

    def get_iterable(self, board_state=None):
        memory = MemorySaver()
        if board_state:
            self.board = chess.Board(board_state)
        else:
            board_state = self.board.fen()

        initial_state = {"turn": 'white' if self.board.turn == chess.WHITE else 'black', "messages":[("system", "")], "winner": "",
                           "board_states": [board_state], "moves": [], "comments": ["Play!"]}
        app = self.compile(checkpointer=memory, interrupt_before=["interruption_node"])

        return ChessIterable(app, {**self.config, "initial_state": initial_state, "board_state": board_state})

    def stream(self, initial_state=None, board_state=None, stream_mode="values"):
        board_state = board_state or self.board.fen()
        if not self.compiled:
            app = self.compile()
        else:
            app = self.workflow
        initial_state = initial_state or {"turn": 'white' if self.board.turn == chess.WHITE else 'black', "messages":[("system", "")], "winner": "",
                           "board_states": [board_state], "moves": [], "comments": ["Play!"]}
        return app.stream(initial_state, self.config, stream_mode=stream_mode)

    def invoke(self, initial_state=None, board_state=None):
        board_state = board_state or self.board.fen()
        if not self.compiled:
            app = self.compile()
        else:
            app = self.workflow
        initial_state = initial_state or {"turn": 'white' if self.board.turn == chess.WHITE else 'black', "messages":[("system", "")], "winner": "",
                           "board_states": [board_state], "moves": [], "comments": ["Play!"]}
        return app.invoke(initial_state)

    def compile(self, checkpointer=None, interrupt_before=[]):
        workflow = StateGraph(GraphState)
        workflow.add_node("board_node", self.board_node)
        workflow.add_node("player_node", self.player_node)
        workflow.add_node("interruption_node", self.interruption_node)
        workflow.add_node("finish_node", self.finish_node)

        # Build graph
        workflow.add_edge(START, "board_node")
        workflow.add_conditional_edges(
            "board_node",
            self.decide_finish,
            {
                "finish": "finish_node",
                "play": "interruption_node"
            },
        )
        workflow.add_edge("interruption_node", "player_node")
        workflow.add_edge("player_node", "board_node")
        workflow.add_edge("finish_node", END)
        self.workflow = workflow.compile(checkpointer=checkpointer, interrupt_before=interrupt_before)
        self.compiled = True
        return self.workflow

    def get_legal_moves(self):
        return [str(move) for move in self.board.legal_moves]

    def make_move(self, move_str):
        # print(f'make move {self.board.legal_moves}')
        move = chess.Move.from_uci(move_str)
        # print(move_str)
        # print(move in self.board.legal_moves)
        if move in self.board.legal_moves:
            self.board.push(move)
        else:
            logging.error(f"move {move} is invalid.")
            return None

        # Get the piece name.
        piece = self.board.piece_at(move.to_square)
        piece_symbol = piece.unicode_symbol()
        piece_name = (
            chess.piece_name(piece.piece_type).capitalize()
            if piece_symbol.isupper()
            else chess.piece_name(piece.piece_type)
        )
        return f"Moved {piece_name} ({piece_symbol}) from " \
               f"{chess.SQUARE_NAMES[move.from_square]} to " \
               f"{chess.SQUARE_NAMES[move.to_square]}."


    def finish_node(self, state: GraphState):
        """
        Find suitable tool to solve the problem

        Args:
            state (dict): The current graph state

        Returns:
            state (dict): New key added to state, generation
        """
        # State
        winner = state["winner"]
        messages = state["messages"]

        if winner=="white":
            messages += [("system", "White player wins!")]
        elif winner=="black":
            messages += [("system", "Black player wins!")]
        elif winner=="draw":
            messages += [("system", "Draw!")]

        return {**state, "messages": messages}

    def interruption_node(self,  state: GraphState):
        """
        Pseudo node for human-in-the-loop interactions
        """
        print(f"interupt: {state}")
        return state

    def board_node(self, state: GraphState):
        """
        Find suitable tool to solve the problem

        Args:
            state (dict): The current graph state

        Returns:
            state (dict): New key added to state, generation
        """
        logging.info('____BOARD NODE____')

        # State
        turn = state["turn"]
        # board_states = state["board_states"]
        # moves = state["moves"]
        winner = state["winner"]
        comments = state["comments"]
        messages = state["messages"]

        if self.comment:
            print(f"{comments[-1]}\n {messages[-1][1]}\n")
        print(f"{self.board}\n\n###############")

        board = self.board
        if board.is_checkmate():
            if turn == 'black':
                winner = "black"
            else:
                winner = "white"
        elif board.is_stalemate() or board.is_insufficient_material() or board.is_seventyfive_moves() or board.is_fivefold_repetition() or board.is_variant_draw():
            winner = "draw"

        return {**state, "winner": winner}

    def player_node(self, state: GraphState):
        turn = 'white' if self.board.turn == chess.WHITE else 'black'
        user_input = state['user_input']
        logging.info('____PLAYER NODE____')
        # print(f"user input {user_input}")

        # print(f"player_config {turn} {self.player_config}")
        # print(user_input or self.player_config[turn] == 'user')

        if user_input or self.player_config[turn] == 'user':
            new_state = self.user_player_node(state)
            if new_state['user_input'] == 'invalid_move':
                print('invalid move: ai will make a move for you.')
                return self.ai_player_node(state)
            return new_state
        elif self.player_config[turn] == 'ai':
            return self.ai_player_node(state)

    def user_player_node(self, state: GraphState):
        """
        Find suitable tool to solve the problem

        Args:
            state (dict): The current graph state

        Returns:
            state (dict): New key added to state, generation
        """
        logging.info('____USER PLAYER SUBNODE____')
        # State
        turn = 'white' if self.board.turn==chess.WHITE else 'black'
        board_states = state["board_states"]
        moves = state["moves"]
        messages = state["messages"]
        user_input = state["user_input"]
        comments = state["comments"]

        user_input = user_input if user_input else self.user_player(self.board)
        move_result = self.make_move(user_input)
        is_move_valid = move_result is not None
        # print(f"is_move_valid {is_move_valid}")

        if is_move_valid:
            logging.info(f"Human {turn} player made a move: {user_input}")
            board_states.append(self.board.fen())
            moves.append(user_input)
            messages.append(("user", move_result))
            comments.append("")
            return {**state, "board_states": board_states, "moves": moves, "turn": turn, "comments":comments, "messages": messages, "user_input":None }
        else:
            return {"user_input": "invalid_move"}

    def ai_player_node(self, state: GraphState):
        """
        Find suitable tool to solve the problem

        Args:
            state (dict): The current graph state

        Returns:
            state (dict): New key added to state, generation
        """
        logging.info('____AI PLAYER SUBNODE____')
        # State
        is_move_valid = False
        # State
        turn = 'white' if self.board.turn==chess.WHITE else 'black'
        board_states = state["board_states"]
        moves = state["moves"]
        messages = state["messages"]
        comments = state["comments"]

        board_state = self.board.fen()
        # legal_moves = self.get_legal_moves()
        while not is_move_valid:
            move, comment = self.ai_player(self.board)
            move_result = self.make_move(move)
            is_move_valid = move_result is not None

        logging.info(f"AI {turn} player made a move: {move}")

        board_states.append(board_state)
        moves.append(move)
        messages.append((f"ai {turn} player", move_result))
        comments.append(f"AI {turn} player: {comment}")

        return {**state, "board_states": board_states, "moves": moves, "turn": turn, "messages": messages, "comments": comments}

    ### Edges
    def decide_finish(self, state: GraphState):
        """
        Determines whether to reflect.

        Args:
            state (dict): The current graph state

        Returns:
            str: Next node to call
        """

        winner = state["winner"]
        moves = state["moves"]

        if winner or len(moves) > self.max_moves:
            return "finish"
        else:
            return "play"



class Move(BaseModel):
    move: str = Field(description="best next move")
    comment: str = Field(description="your comment for the move")


class ChessAgent:
    prompt_template = """You are a chess expert, the current board's Forsyth–Edwards notation (FEN) is {board_state}, and it's {turn} turn. 
                Possible next moves are: {legal_moves}. Please make next move based on current board position."""

    def __init__(self, llm):
        self.llm = llm
        self.structured_llm = llm.with_structured_output(Move)

    def invoke(self, board_state, turn, legal_moves):
        prompt = self.prompt_template.format(board_state=board_state, turn=turn, legal_moves=legal_moves)
        move = self.structured_llm.invoke(prompt)
        return move

def create_ai_chess_app(llm, board_state, ai_agent=None, config=None):
    config = config or {"configurable": {"thread_id": "1"}, "recursion_limit": 100}
    chess_ai_agent = ai_agent(llm) if ai_agent else ChessAgent(llm)
    llm_ai_player = create_llm_ai_player(chess_ai_agent)

    chess_app = Chess(ai_player=llm_ai_player, board_state=board_state)
    chess_app.set_config(config)
    return chess_app
