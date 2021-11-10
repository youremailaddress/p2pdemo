from threading import Lock
import base64,time
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5 as PKCS1_cipher
from flask import Flask, request, abort,jsonify,render_template,copy_current_request_context
import datetime,json
from flask_socketio import SocketIO, emit, join_room, leave_room, \
    close_room, rooms, disconnect
from keys import pub,sec

key = RSA.importKey(pub)
seckey = RSA.importKey(sec)

def encrypt_data(key,msg):
    cipher = PKCS1_cipher.new(key)
    encrypt_text = base64.b64encode(cipher.encrypt(bytes(msg.encode("utf8"))))
    return encrypt_text.decode('utf-8')

def decrypt_data(seckey,encrypt_msg):
    cipher = PKCS1_cipher.new(seckey)
    back_text = cipher.decrypt(base64.b64decode(encrypt_msg), 0)
    return back_text.decode('utf-8')

app = Flask(__name__)
socketio = SocketIO(app)
thread = None
thread_lock = Lock()
_dataStore = []
Gonggao = {'title':'','content':''}

def getrooms():
    returnlis = []
    for i in _dataStore:
        returnlis.append(i['rooms'])
    return returnlis

def getdicbyroomname(name):
    for i in _dataStore:
        if i['rooms'] == name:
            return i

def write_log(s):    
    with open('ajsqxizoakz.xuz', 'a+') as f:
        f.write('[%s]%s\n' % (str(datetime.datetime.now()), s))

@app.route('/',methods=['GET'])
def index():
    return render_template('index.html',pub=pub,title=Gonggao['title'],content=Gonggao['content'])

@app.route('/create',methods=['POST'])
def create():
    ency = request.form['data']
    try:
        data = decrypt_data(seckey, ency)
        data = json.loads(data)
    except:
        return '''{"msg":"Key unsupported."}'''
    if data['data'] == '' or '/' in data['data']:
        return '''{"msg":"Key unsupported."}'''
    elif data['data'] not in getrooms() and int(time.time())-int(data['timestamp'])<5:
        _dataStore.append({'rooms':data['data'],'members':[]})
        return '''{"msg":"Successfully create new room."}'''
    return '''{"msg":"Room has already exists."}'''

@app.route('/<roomname>',methods=['GET','POST'])
def room(roomname):
    if request.method == 'GET':
        if roomname not in getrooms():
            return '''<script>alert("Plz create room first!");location.href='/'</script>'''
        else:
            return render_template('room.html',RoomName=roomname,pub=pub)
    if request.method == 'POST':
        if roomname not in getrooms():
            return '''Plz create room first!'''
        else:
            data = request.form['data']
        try:
            data = json.loads(data)
            enc = data['enc']
            sign = data['sign']
        except:
            return '''REJECTED.'''
        print(decrypt_data(seckey, enc))
        return '''{"msg":"Room has already exists."}'''

@app.route('/UIShsJDAU78S7TW3hsadudy98978ADH8dh7gs7G7Au7',methods=['POST'])
def AddToAll():
    if request.method == 'POST':
        data = request.form['data']
        data = json.loads(data)
        Gonggao['title'] = data['title']
        Gonggao['content'] = data['content']
        return '''OK!!'''

@socketio.event
def getpeoplelist(msg):
    if msg['room'] not in getrooms():
        return
    else:
        emit("onlinelist",{"lis":getdicbyroomname(msg['room'])['onlinelist']})

@socketio.event
def join(msg):
    if msg["room"] not in getrooms():
        return
    else:
        item = getdicbyroomname(msg['room'])
        if item.get('onlinelist') == None:
            item['onlinelist']= [(msg['uuid'],msg['pub'],int(time.time()))]
        else:
            item['onlinelist'].append((msg['uuid'],msg['pub'],int(time.time())))
@socketio.event
def beat(msg):
    if msg["room"] not in getrooms():
        return
    else:
        item = getdicbyroomname(msg['room'])
        if item.get('onlinelist') == None:
            return
        else:
            lis = item.get('onlinelist')
            for it in lis[::]:
                uuid,_,tim = it
                if uuid == msg['uuid']:
                    lis.remove(it)
                    lis.append((uuid,_,int(time.time())))
                elif int(time.time())-tim > 120:
                    lis.remove(it)
            item['onlinelist'] = lis

if __name__ == '__main__':
    socketio.run(app,port=1921)