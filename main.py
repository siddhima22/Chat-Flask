from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import SocketIO,join_room, leave_room,send
import random
from string import ascii_uppercase

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

rooms={}   #dictonary
def generate_unique_code(length):
    while True:
        code=""
        for _ in range(length):
            code += random.choice(ascii_uppercase)

        if code not in rooms:        #checks for code as a key in the dictonary
            break
    return code
@app.route('/', methods=['POST', 'GET'])    #to display routes using a decorator syntax, allows you to post and get data
def home():
    session.clear()           #deletes old data
    if request.method == 'POST':
        name = request.form.get('name')
        code = request.form.get('code')
        join = request.form.get('join', False)  #False is default value
        create = request.form.get('create', False)

        if not name:                              #name is empty
            return render_template('home.html', error="Please enter a name",code=code, name=name)  #to make code and name persistent even if details are wrong
        if join != False and not code:             #no code
            return render_template('home.html', error="Please enter a room code" ,code=code, name=name)
        
        room=code
        if create != False:
            room=generate_unique_code(4)
            rooms[room]={ "members":0 , "messages":[]}
        elif code not in rooms:
            return render_template('home.html', error="Room does not exist" ,code=code, name=name)
        
        session['room'] = room
        session['name'] = name         #semi permanent way of storing data on server,secure
        return redirect(url_for('room'))
    
    return render_template('home.html') #only works if method is not a post request

@app.route('/room')
def room():
    room=session.get('room')
    if room is None or session.get('name') is None or room not in rooms:
        return redirect(url_for('home'))
    return render_template('room.html',code=room, messages=rooms[room]["messages"])

@socketio.on('message')
def message(data):
    room=session.get('room')
    if room not in rooms:
        return
    content={
        'name':session.get('name'),
        'message':data['data']
    }
    send(content,to=room)
    rooms[room]["messages"].append(content)
    print(f"{session.get('name')} said: {data['data']}")

@socketio.on('connect')
def connect(auth):
    room=session.get('room')
    name = session.get('name')
    if not room or not name:
        return
    if room not in rooms:
        leave_room(room)
        return
    join_room(room)
    send({"name":name,"message":"has joined the room"},to=room)
    rooms[room]["members"] += 1
    print(f"{name} joined room {room}")
 
@socketio.on('disconnect')
def disconnect():
    room=session.get('room')
    name = session.get('name')
    leave_room(room)

    if room in rooms:
        rooms[room]["members"] -= 1
        if rooms[room]["members"] <= 0:
            del rooms[room]
    send({"name":name,"message":"has left the room"},to=room)
    print(f"{name} left room {room}")   #fstring


if __name__ == '__main__':
    socketio.run(app,debug=True) #automatically refresh


    #stored in ram
