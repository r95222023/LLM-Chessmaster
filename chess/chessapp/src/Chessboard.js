import { useState, useEffect} from "react";
import { Chess } from "chess.js";
import { Chessboard } from "react-chessboard";

const socket = new WebSocket('ws://localhost:8000/chess/');
socket.onopen = function() {
  console.log('ChessLLM webSocket connection established.');
};
let resolve, promise;

export default function ChessBoard() {
  const [options, setOptions] = useState({white_player:'human', black_player:'ai', random: false, openai_key:'', model: 'ollama-llama3.1', board_state:''});
  const [game, setGame] = useState(new Chess());
  const [states, setStates] = useState([]);
  const [lastComment, setLastComment] = useState("");
  const [showBoard, setShowBoard] = useState(false);


  // Runs only on the first render
  useEffect(() => {
    socket.onmessage = function(event) {
      const data = JSON.parse(event.data);
      switch (data['message']) {
        case'next_move_received':
          if(promise){
            console.log('next_move_received', data);

            resolve(data)
          } else {
            console.log('failed to resove the promise: make sure the promise is defined')
          }
          break
        default:
          console.log('invalid message:', data);
      }
    };
  }, []);

  const updateView = (move, comment) =>{
    game.move(move)
    setGame(new Chess(game.fen()))
    let currentStates = [...states, {move: move, board_state: game.fen(), comment: comment || ''}]
    setStates(currentStates);
    setLastComment(comment)
    console.log(currentStates)
  }

  const updatePlayerOptions = (e) => {
    const player = e.target.id
    const _options = {...options}
    _options[player] = e.target.value
    setOptions(_options)

  }

  const isOpenAIModel = (model) => {
    return model.indexOf('openai') >= 0
  }

  const makeMoveServer = async (move) => {
    const msg_str = JSON.stringify({'message': 'next_move', 'move': {'from': move.from, 'to': move.to}, 'turn': game.turn})
    // send the request
    console.log('send message', msg_str)
    socket.send(msg_str);
    promise = new Promise((res, rej) => {resolve = res;});
    const result = await promise

    return result
  }

  const makeMove = async (move) => {
    console.log('move', move)
    let comment = ''
    if(!move){
      const result = await makeMoveServer({'from': '', 'to': '', 'promotion': 'q'});
      move = result.move
      comment = result.comment
      updateView(move, comment)
    } else {
      try {
        // put upteView before makeMoveServer for faster response
        updateView(move, comment)
        await makeMoveServer(move);
      } catch (error) {
        console.log(error)
        return null
      }
    }
    return move
  }

  const makeAiMove = async () => {
    await makeMove();

    if(game.turn()==='b'){
      makeFirstMoveObj[options.black_player]();
    } else {
      makeFirstMoveObj[options.white_player]();
    }
  }

  async function makeRandomMove() {
    const possibleMoves = game.moves({ verbose: true });
    if (game.isGameOver() || game.isDraw() || possibleMoves.length === 0) return; // exit if the game is over
    const randomIndex = Math.floor(Math.random() * possibleMoves.length);
    const nextMove = possibleMoves[randomIndex]
    await makeMove(nextMove);
    // if (options.white_player==='random' && options.black_player==='random'){
    //   setTimeout(makeRandomMove, 3000);
    // }
    if(game.turn()==='b'){
      makeFirstMoveObj[options.black_player]();
    } else {
      makeFirstMoveObj[options.white_player]();
    }
  }
  const makeFirstMoveObj = {'ai': ()=>{setTimeout(makeAiMove, 500)}, 'random': ()=>{setTimeout(makeRandomMove, 3000);console.log('random move')}, 'human': () => {}}

  function onDrop(sourceSquare, targetSquare) {
    const move = makeMove({
      from: sourceSquare,
      to: targetSquare,
      promotion: "q", // always promote to a queen for example simplicity
    });

    // Skip illegal move
    if (move === null) return false;
    if(game.turn()==='b'){
      makeFirstMoveObj[options.black_player]();
    } else {
      makeFirstMoveObj[options.white_player]();
    }

    return true;
  }

  function start_game() {
    setShowBoard(true)
    if(options.board_state){
      setGame(new Chess(options.board_state))
    }
    const llm_config = {'model': options.model, 'api_key': options.openai_key}
    const _options = {'white_player': options.white_player, 'black_player': options.black_player}
    const msg_str = JSON.stringify({'message': 'start', 'llm_config': llm_config, 'options': _options, board_state:options.board_state})
    socket.send(msg_str);
    // const makeFirstMoveObj = {'ai': makeAiMove, 'random': makeRandomMove, 'human': () => {}}
    if(game.turn()==='b'){
      makeFirstMoveObj[options.black_player]();
    } else {
      makeFirstMoveObj[options.white_player]();
    }
  }

  return(
     <div>
        <div style={{display: !showBoard ? "block" : "none", marginTop:"20px"}}>
          <h1>Chess Game powered by Large Language Model</h1>
          <h2>How to play:</h2>
          <span>1. Select a LLM as AI player. Openai models such as gpt-4o and gpt-4o-mini require openai api key.</span> <br></br>
          <span>2. Select player type for white and black player. Player type can be human, ai or random.
          </span><br></br>
          <span>AI player is powered by selected LLM model while random player move randomly. </span> <br></br>
          <span>3. Type in starting position in Forsyth–Edwards Notation(FEN) to start a custom game.. </span> <br></br>
          <span>4. Click start button to start the game!</span>
          <h2>Setup:</h2>
          <div>
            <label>LLM model:</label>
            <select name="llm" id="llm" value={options.model} onChange={e=> setOptions({...options, 'model':e.target.value})}>
              <option value="openai-gpt-4o">Openai: gpt-4o</option>
              <option value="openai-gpt-4o-mini">Openai: gpt-4o-mini</option>
              <option value="ollama-llama3.1">Ollama: llama3.1</option>
            </select>
          </div>
          <div style={{ display: isOpenAIModel(options.model) ? "block" : "none"}}>
            <label>Openai_key:</label>
            <input type="text" placeholder="Openai Key" value={options.openai_key} onChange={e=> setOptions({...options, 'openai_key':e.target.value})}/>
          </div>
          <label>White Player:</label>
          <select name="white_player" id="white_player" value={options.white_player} onChange={updatePlayerOptions}>
            <option value="human">Human</option>
            <option value="ai">AI</option>
            <option value="random">Random</option>
          </select>
          <label>Black Player:</label>
          <select name="black_player" id="black_player" value={options.black_player} onChange={updatePlayerOptions}>
            <option value="human">Human</option>
            <option value="ai">AI</option>
            <option value="random">Random</option>
          </select>
          <div>
          <label>Starting Position (FEN):</label>
          <input type="text" placeholder="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1" value={options.board_state} onChange={e=> setOptions({...options, 'board_state':e.target.value})}/>
          </div>
          <br/>
          <h2>Play!</h2>
          <button class="button button1" type="button" onClick={start_game}>Start!</button>
        </div>
        {
          (showBoard)?
          <div style={{width:"70vw", max_width:"70vh", margin: "3rem auto", minHeight: "500px", maxHeight: "800px" }}>
            <h3>{lastComment}</h3>
            <Chessboard position={game.fen()} onPieceDrop={onDrop} />
          </div>
          : <div></div>
        }
     </div>
  )
}