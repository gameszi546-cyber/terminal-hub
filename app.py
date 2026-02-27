from flask import Flask, render_template, send_from_directory, jsonify, request
import os

app = Flask(__name__)
BASE_DIR = os.path.join(os.getcwd(), 'storage')

# Состояния системы
music_state = {"current_track": None, "is_playing": False, "timestamp": 0.0}
game_state = {"board": [""] * 9, "current_player": "X", "winner": None, "status": "Ход: X"}
drawing_state = {"lines": []}

AUTO_FOLDERS = {
    'mods': 'Игровые Моды', 
    'builds': 'Сборки Проектов', 
    'test_files': 'Тестовые Файлы', 
    'music': 'Музыка', 
    'extra': 'Дополнительно'
}

for f in list(AUTO_FOLDERS.keys()) + ['tools', 'games']:
    os.makedirs(os.path.join(BASE_DIR, f), exist_ok=True)

@app.route('/')
def index():
    # Папки
    main_data = {fid: {'name': fname, 'files': sorted(os.listdir(os.path.join(BASE_DIR, fid)))} 
                 for fid, fname in AUTO_FOLDERS.items() if fid not in ['music', 'extra']}
    
    # Ссылки из .txt файлов
    extra_items = []
    e_path = os.path.join(BASE_DIR, 'extra')
    for fn in sorted(os.listdir(e_path)):
        item = {'name': fn, 'display': fn.replace('.txt', ''), 'url': None}
        if fn.endswith('.txt'):
            try:
                with open(os.path.join(e_path, fn), 'r', encoding='utf-8') as f:
                    c = f.read().strip()
                    if c.startswith('http'): item['url'] = c
            except: pass
        extra_items.append(item)

    # Игры (папка_тип)
    g_path = os.path.join(BASE_DIR, 'games')
    structured_games = {'local': [], 'steam': []}
    for folder in [d for d in os.listdir(g_path) if os.path.isdir(os.path.join(g_path, d))]:
        if '_' in folder:
            name, gtype = folder.rsplit('_', 1)
            gtype = gtype.lower()
            if gtype in ['local', 'steam']:
                files = os.listdir(os.path.join(g_path, folder))
                structured_games[gtype].append({
                    'display_name': name, 'folder_name': folder,
                    'torrent': next((f for f in files if f.endswith('.torrent')), None),
                    'fix': next((f for f in files if f.endswith('.exe')), None)
                })

    music_files = [f for f in os.listdir(os.path.join(BASE_DIR, 'music')) if f.endswith(('.mp3', '.wav'))]
    tools_files = sorted(os.listdir(os.path.join(BASE_DIR, 'tools')))

    return render_template('index.html', main_folders=main_data, extra_items=extra_items, 
                           tools=tools_files, games=structured_games, music=music_files)

# --- API ---
@app.route('/music/state')
def get_music_state(): return jsonify(music_state)

@app.route('/music/control', methods=['POST'])
def control_music():
    data = request.json
    if "track" in data: music_state["current_track"] = data["track"]; music_state["timestamp"] = 0.0
    if "is_playing" in data: music_state["is_playing"] = data["is_playing"]
    if "timestamp" in data: music_state["timestamp"] = float(data["timestamp"])
    return jsonify({"success": True})

@app.route('/game/state')
def g_state(): return jsonify(game_state)

@app.route('/game/move', methods=['POST'])
def g_move():
    idx = request.json.get('index')
    if game_state["board"][idx] == "" and not game_state.get("winner"):
        game_state["board"][idx] = game_state["current_player"]
        win = [(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)]
        if any(game_state["board"][a]==game_state["board"][b]==game_state["board"][c]!="" for a,b,c in win):
            game_state["winner"] = game_state["current_player"]
            game_state["status"] = f"ПОБЕДА: {game_state['winner']}!"
        elif "" not in game_state["board"]:
            game_state["status"] = "НИЧЬЯ!"
        else:
            game_state["current_player"] = "O" if game_state["current_player"] == "X" else "X"
            game_state["status"] = f"Ход: {game_state['current_player']}"
    return jsonify(game_state)

@app.route('/game/reset', methods=['POST'])
def g_reset():
    global game_state
    game_state = {"board": [""] * 9, "current_player": "X", "winner": None, "status": "Ход: X"}
    return jsonify(game_state)

@app.route('/drawing/state')
def d_state(): return jsonify(drawing_state)

@app.route('/drawing/draw', methods=['POST'])
def d_draw():
    drawing_state["lines"].append(request.json.get('line'))
    return jsonify({"success": True})

@app.route('/drawing/clear', methods=['POST'])
def d_clear(): drawing_state["lines"] = []; return jsonify({"success": True})

@app.route('/download/<path:filename>')
def download(filename): return send_from_directory(BASE_DIR, filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
