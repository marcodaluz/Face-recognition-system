import cv2
import os
import mysql.connector
from flask import Flask, request, render_template,redirect, url_for
from datetime import date
from datetime import datetime
import numpy as np
from sklearn.neighbors import KNeighborsClassifier
import pandas as pd
import joblib
from flask import Flask, jsonify
from datetime import datetime


# Defining Flask App
app = Flask(__name__)

# Number of images to take for each user
nimgs = 10

# Saving Date today in 2 different formats
datetoday = date.today().strftime("%m_%d_%y")


# Initializing VideoCapture object to access WebCam
face_detector = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')


# If these directories don't exist, create them
if not os.path.isdir('static'):
    os.makedirs('static')
if not os.path.isdir('static/faces'):
    os.makedirs('static/faces')

#################
def create_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        passwd="",
        database="teste2"
    )

##função que vai buscar todos os users a base de dados
def get_all_users():
    connection = create_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM Employee")
    users = cursor.fetchall()
    cursor.close()
    connection.close()
    return users

#####################################################################  save data in database ########################################################
# Function to save user data to database
def save_user_data(newuserid, newusername,password,cargo, departamento,HoraEntrada, HoraSaida):
    connection = create_db_connection()
    cursor = connection.cursor()
    sql_query = "INSERT INTO Employee (userid, username, password, cargo, departamento, HoraEntrada, HoraSaida) VALUES (%s, %s, %s, %s, %s, %s, %s)"
    val = (newuserid, newusername,password,cargo, departamento,HoraEntrada, HoraSaida)
    cursor.execute(sql_query, val)
    connection.commit()
    cursor.close()
    connection.close()

#save entry attendance
def save_attendance_to_db(userid, username, current_date, current_time):
    connection = create_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM EntryRecord WHERE userid = %s AND data = %s", (userid, current_date))
    attendance_record = cursor.fetchone()

    if attendance_record is None:
        sql_query = "INSERT INTO EntryRecord (userid, username, data, hora) VALUES (%s, %s, %s, %s)"
        val = (userid, username, current_date, current_time)
        cursor.execute(sql_query, val)
        connection.commit()

    cursor.close()
    connection.close()


#save exit attendance
def save_attendance_to_db_exit(userid, username, current_date, current_time):
    connection = create_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM ExitRecord WHERE userid = %s AND data = %s", (userid, current_date))
    attendance_record = cursor.fetchone()
    if attendance_record is None:
        sql_query = "INSERT INTO ExitRecord (userid, username, data, hora) VALUES (%s, %s, %s, %s)"
        val = (userid, username, current_date, current_time)
        cursor.execute(sql_query, val)
        connection.commit()

    cursor.close()
    connection.close()    

#############################################################################################################################
#############



# extract the face from an image
def extract_faces(img):
    if img is not None and img.shape[0] > 0 and img.shape[1] > 0:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        face_points = face_detector.detectMultiScale(
            gray, 1.2, 5, minSize=(20, 20))
        return face_points
    else:
        return []


# Identify face using ML model
def identify_face(facearray):
    model = joblib.load('static/face_recognition_model.pkl')
    return model.predict(facearray)


# A function which trains the model on all the faces available in faces folder
def train_model():
    faces = []
    labels = []
    userlist = os.listdir('static/faces')
    for user in userlist:
        for imgname in os.listdir(f'static/faces/{user}'):
            img = cv2.imread(f'static/faces/{user}/{imgname}')
            resized_face = cv2.resize(img, (50, 50))
            faces.append(resized_face.ravel())
            labels.append(user)
    faces = np.array(faces)
    knn = KNeighborsClassifier(n_neighbors=5)
    knn.fit(faces, labels)
    joblib.dump(knn, 'static/face_recognition_model.pkl')

################## ROUTING FUNCTIONS #########################

@app.route('/')
def home():
    
    return render_template('login.html')
@app.route('/loginSuccessful')
def loginSuccessful():
    return render_template('dashboard.html')

@app.route('/adduseradmin')
def adduseradmin():
    
    return render_template('adduseradmin.html')

@app.route('/dashboard')
def dashboard():
   
    return render_template('dashboard.html')

@app.route('/adduser')
def adduser():
    
    return render_template('adduser.html')

@app.route('/users')
def users():
    users_list = get_all_users()
    return render_template('users.html', users=users_list)

##################################################################### Routes for user admin ########################################################
@app.route('/addAdmin', methods=['POST'])
def addAdmin():
    username = request.form.get('username')
    password = request.form.get('password')
    position = request.form.get('position')    
    connection = create_db_connection()
    cursor = connection.cursor()
    
    if not username or not password:
       return "Error: Provide username and password in the request body.", 400
    
    comando = 'INSERT INTO useradmin (username,password,position) VALUES (%s, %s, %s)'
    valores = (username, password, position)
    cursor.execute(comando, valores)
    connection.commit()
    cursor.close()
    connection.close()
    return render_template('adduseradmin.html')


# get user admin
@app.route('/usersadmin', methods=['GET'])
def getUserAdmin():
    connection = create_db_connection()
    cursor = connection.cursor()
    command = 'SELECT id, username, password, position FROM useradmin'
    cursor.execute(command)
    usersdb = cursor.fetchall()
    users = [{'id': id, 'username': username, 'password': password, 'position': position} 
             for id, username, password, position in usersdb]
    return render_template('users_admin.html', users=users)

# Routes for admin login
@app.route('/login', methods=['POST'])
def login():
    connection = create_db_connection()
    cursor = connection.cursor()
    username = request.form.get('username')
    password = request.form.get('password')
    print("Username:", request.form.get('username'))
    print("Password:", request.form.get('password'))
    
    if not username or not password:
        return "Error: Provide username and password in the request body", 400
    
    command = 'SELECT * FROM useradmin WHERE username = %s AND password = %s'
    values = (username, password)
    cursor.execute(command, values)
    utilizador = cursor.fetchone()
    if utilizador:
        return redirect(url_for('loginSuccessful'))
    else:
        return render_template('login.html')



# Recognition functionality. 
#####################################################################  adicionar e reconhecimentos rotas ########################################################
@app.route('/markAttendanceEntry', methods=['GET'])
def start():
    if 'face_recognition_model.pkl' not in os.listdir('static'):
        return render_template('home1.html', mess='There is no trained model in the static folder. Please add a new face to continue.')

    ret = True
    cap = cv2.VideoCapture(0)
    while ret:
        ret, frame = cap.read()
        if len(extract_faces(frame)) > 0:
            (x, y, w, h) = extract_faces(frame)[0]
            cv2.rectangle(frame, (x, y), (x+w, y+h), (86, 32, 251), 1)
            cv2.rectangle(frame, (x, y), (x+w, y-40), (86, 32, 251), -1)
            face = cv2.resize(frame[y:y+h, x:x+w], (50, 50))
            identified_person = identify_face(face.reshape(1, -1))[0]
           
            # Save attendance to DB
            userid = identified_person.split('_')[1]
            username = identified_person.split('_')[0]
            current_date = datetime.now().strftime("%Y-%m-%d")  # Only the date
            current_time = datetime.now().strftime("%H:%M:%S")  # Only the time
            save_attendance_to_db(userid, username, current_date, current_time)  # Adjust this function to accept date and time separately
            cv2.putText(frame, f'{identified_person}', (x+5, y-5),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.imshow('Attendance', frame)
        if cv2.waitKey(1) == 27:  # 27 is the ASCII code for the ESC key
            break
    cap.release()
    cv2.destroyAllWindows()
    
    return render_template('dashboard.html')

@app.route('/markAttendanceExit', methods=['GET'])
def exit():
    if 'face_recognition_model.pkl' not in os.listdir('static'):
        return render_template('home1.html', mess='There is no trained model in the static folder. Please add a new face to continue.')

    ret = True
    cap = cv2.VideoCapture(0)
    while ret:
        ret, frame = cap.read()
        if len(extract_faces(frame)) > 0:
            (x, y, w, h) = extract_faces(frame)[0]
            cv2.rectangle(frame, (x, y), (x+w, y+h), (86, 32, 251), 1)
            cv2.rectangle(frame, (x, y), (x+w, y-40), (86, 32, 251), -1)
            face = cv2.resize(frame[y:y+h, x:x+w], (50, 50))
            identified_person = identify_face(face.reshape(1, -1))[0]
           
            # Save attendance to DB
            userid = identified_person.split('_')[1]
            username = identified_person.split('_')[0]
            current_date = datetime.now().strftime("%Y-%m-%d")  # Only the date
            current_time = datetime.now().strftime("%H:%M:%S")  # Only the time
            save_attendance_to_db_exit(userid, username, current_date, current_time)  # Adjust this function to accept date and time separately
            cv2.putText(frame, f'{identified_person}', (x+5, y-5),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.imshow('Attendance', frame)
        if cv2.waitKey(1) == 27:  # 27 is the ASCII code for the ESC key
            break
    cap.release()
    cv2.destroyAllWindows()
    
    return render_template('dashboard.html')

# A function to add a new user.
# This function will run when we add a new user.

@app.route('/add', methods=['POST'])
def add():
    newusername = request.form['newusername']
    newuserid = request.form['newuserid']
    password = request.form['password']
    cargo = request.form['cargo']
    departamento = request.form['departamento']
    HoraEntrada = request.form['horaentrada']
    HoraSaida= request.form['horasaida']
    # Salvar os dados do usuário na base de dados
    save_user_data(newuserid, newusername,password,cargo, departamento,HoraEntrada, HoraSaida)

    userimagefolder = 'static/faces/' + newusername + '_' + str(newuserid)
    if not os.path.isdir(userimagefolder):
        os.makedirs(userimagefolder)
    i, j = 0, 0
    cap = cv2.VideoCapture(0)
    while True:
        _, frame = cap.read()
        faces = extract_faces(frame)
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 20), 2)
            cv2.putText(frame, f'Images Captured: {i}/{nimgs}', (30, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 20), 2, cv2.LINE_AA)
            if j % 5 == 0:
                name = newusername + '_' + str(i) + '.jpg'
                cv2.imwrite(userimagefolder + '/' + name, frame[y:y + h, x:x + w])
                i += 1
            j += 1
        if j == nimgs * 5:
            break
        cv2.imshow('Adding new User', frame)
        if cv2.waitKey(1) == 27:
            break
    cap.release()
    cv2.destroyAllWindows()
    print('Training Model')
    train_model()
    
    return render_template('adduser.html')

#####################################################################  presencas routes ########################################################
@app.route('/entryRecord') 
def entryRecord():
    connection = create_db_connection()
    cursor = connection.cursor()
    cursor.execute("""
        SELECT p.id, p.userid, p.username, p.data, p.hora, u.HoraEntrada 
        FROM EntryRecord p
        LEFT JOIN Employee u ON p.userid = u.userid  
        ORDER BY p.data DESC, p.hora DESC
    """)
    attendances = cursor.fetchall()
    cursor.close()
    connection.close()
    return render_template('entryRecords.html', attendances=attendances)

@app.route('/exitRecord')
def exitRecord():
    connection = create_db_connection()
    cursor = connection.cursor()
    cursor.execute("""
        SELECT s.id, s.userid, s.username, s.data, s.hora, u.HoraSaida 
        FROM ExitRecord s
        LEFT JOIN Employee u ON s.userid = u.userid  
        ORDER BY s.data DESC, s.hora DESC
    """)
    attendances = cursor.fetchall()
    cursor.close()
    connection.close()
    return render_template('eixtRecords.html', attendances=attendances)

#####################################################################  mobile routs ########################################################
@app.route('/attendance/<int:userid>', methods=['GET'])
def get_user_attendance(userid):
    connection = create_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM EntryRecord WHERE userid = %s", (userid,))
    user_attendance = cursor.fetchall()
    cursor.close()
    connection.close()

    # Converter os resultados em um formato JSON
    attendance_json = []
    for attendance in user_attendance:
        attendance_dict = {
            "userid": attendance[1],
            "username": attendance[2],
            "data": attendance[3].strftime("%Y-%m-%d"),
            "hora": str(attendance[4])  # Converter timedelta para string
        }
        attendance_json.append(attendance_dict)
     
    return jsonify(attendance_json)
#--#
@app.route('/outs/<int:userid>', methods=['GET'])
def get_user_out(userid):
    connection = create_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM ExitRecord WHERE userid = %s", (userid,))
    user_attendance = cursor.fetchall()
    cursor.close()
    connection.close()

    # Converter os resultados em um formato JSON
    attendance_json = []
    for attendance in user_attendance:
        attendance_dict = {
            "userid": attendance[1],
            "username": attendance[2],
            "data": attendance[3].strftime("%Y-%m-%d"),
            "hora": str(attendance[4])  # Converter timedelta para string
        }
        attendance_json.append(attendance_dict)
     
    return jsonify(attendance_json)

#--#
@app.route('/loginapp', methods=['POST'])
def api_login():
    if request.method == 'POST':
        data = request.get_json()

        if 'username' in data and 'password' in data:
            username = data['username']
            password = data['password']

            # Query the database to check login credentials
            connection = create_db_connection()
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM Employee WHERE username = %s AND password = %s", (username, password))
            user = cursor.fetchone()
            cursor.close()
            connection.close()

            if user:
                # User found, return user information (excluding password)
                user_info = {
                    'userid': user[0],
                    'username': user[1],
                    'cargo': user[3],
                    'departamento': user[4],
                    'HoraEntrada': str(user[5]),
                    'HoraSaida': str(user[6])
                }
                return jsonify(user_info), 200
            else:
                # Invalid credentials
                return jsonify({'error': 'Invalid username or password'}), 401

        else:
            return jsonify({'error': 'Missing username or password in the request'}), 400
if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=False)
    