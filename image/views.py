from django.shortcuts import render
from django.template import RequestContext
from django.contrib import messages
from django.conf import settings
from django.core.files.storage import default_storage
from django.http import FileResponse, Http404
import pymysql
import imagehash
import hashlib
from urllib.parse import unquote
from django.http import HttpResponse,HttpResponseBadRequest
from django.core.files.storage import FileSystemStorage
import os
from cryptography.fernet import Fernet
import io
from Blockchain import *
from Block import *
from datetime import date
import cv2
import numpy as np
import base64
import random
from datetime import datetime
from scipy.spatial.distance import euclidean
from PIL import Image, ImageEnhance, ImageOps


# Generate a key for encryption (do this once and save the key securely)
key = b'3SnF2wi_z7UvudwtC6iFIFSjmyaw22vVQE0yD6DHdJM='
cipher_suite = Fernet(key)

global username, password, contact, email, address

blockchain = Blockchain()
if os.path.exists('blockchain_contract.txt'):
    with open('blockchain_contract.txt', 'rb') as fileinput:
        blockchain = pickle.load(fileinput)
    fileinput.close()

face_detection = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
recognizer = cv2.face_LBPHFaceRecognizer.create()

def index(request):
    if request.method == 'GET':
       return render(request, 'index.html', {})

def Admin(request):
    if request.method == 'GET':
       return render(request, 'Admin.html', {})

def Welcome(request, username):
    if username is None or username == '':
        return render(request, 'regret.html', {'message', 'Username is required'})
    return render(request, 'welcome.html', {'username':username})

    
def Login(request):
    if request.method == 'GET':
       return render(request, 'Login.html', {})

def fingerLogin(request):
    if request.method == 'GET':
        return render(request, 'fingerLogin.html',{})
    
def Login_decision(request):
    if request.method == 'GET':
        return render(request, 'LoginDecision.html',{})

def Register(request):
    if request.method == 'GET':
       return render(request, 'Register.html', {})
def RegisterDecision(request):
    if request.method == 'GET':
        return render(request, 'RegisterDecision.html',{})

def fingerRegister(request):
    if request.method == 'GET':
        return render(request, 'fingerRegister.html',{})

def register_finger(request):
    if request.method == 'POST':
        username = request.POST.get('username', None)
        password = request.POST.get('password', None)
        contact = request.POST.get('contact', None)
        email = request.POST.get('email', None)
        address = request.POST.get('address', None)
        file = request.FILES.get('file_upload', None)
        
        if not all([username, password, contact, email, address, file]):
            context = {'data': 'All fields are required'}
            return render(request, 'fingerRegister.html', context)
        
        # Save the file
        file_path = default_storage.save(f'image/static/fingerprint/{username}.png', file)
        file_name = file.name
        
        # Connect to the database
        db_connection = pymysql.connect(
            host='127.0.0.1',
            port=3306,
            user='root',
            password='12345',
            database='facial_login',
            charset='utf8'
        )
        db_cursor = db_connection.cursor()
        
        # Check if the user already exists in the `finger_register` table
        check_user_query_finger_register = "SELECT COUNT(*) FROM finger_register WHERE username = %s OR email = %s"
        db_cursor.execute(check_user_query_finger_register, (username, email))
        user_count_finger_register = db_cursor.fetchone()[0]
        
        if user_count_finger_register > 0:
            context = {'data': 'User already registered in fingerprint table'}
        else:
            # Check if the user exists in the other table `register`
            check_user_query_register = "SELECT COUNT(*) FROM register WHERE username = %s"
            db_cursor.execute(check_user_query_register, (username,))
            user_count_register = db_cursor.fetchone()[0]
            
            if user_count_register > 0:
                context = {'data': 'User already registered in another table'}
            else:
                # Register the new user
                register = 'Fingerprint'
                insert_query = "INSERT INTO finger_register (username, password, contact, email, address, image, register) VALUES (%s, %s, %s, %s, %s, %s, %s)"
                db_cursor.execute(insert_query, (username, password, contact, email, address, file_name, register))
                db_connection.commit()
                
                if db_cursor.rowcount == 1:
                    context = {'data': 'Signup Process Completed'}
                else:
                    context = {'data': 'Unable to register'}
        
        db_cursor.close()
        db_connection.close()
        
        return render(request, 'fingerRegister.html', context)
    
    context = {'data': 'Invalid request method'}
    return render(request, 'fingerRegister.html', context)

def preprocess_image(image_file):
    image = Image.open(image_file)
    image = image.convert('L')
    image = image.resize((256, 256))
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2.0)
    image = ImageOps.autocontrast(image, cutoff=5)
    return image

def extract_features(image):
    image_array = np.array(image)
    return image_array.flatten()

def compare_features(features1, features2):
    distance = euclidean(features1, features2)
    threshold = 1000
    return distance < threshold

def login_finger(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        uploaded_image = request.FILES.get('file')
        
        # Connect to the database
        db_connection = pymysql.connect(host='127.0.0.1', port=3306, user='root', password='12345', database='facial_login', charset='utf8')
        db_cursor = db_connection.cursor()
        
        # Check user credentials
        check_user_query = "SELECT * FROM finger_register WHERE username = %s AND password = %s"
        db_cursor.execute(check_user_query, (username, password))
        user = db_cursor.fetchone()
        
        if user:
            stored_image_path = f'image/static/fingerprint/{username}.png'
            
            if default_storage.exists(stored_image_path):
                with default_storage.open(stored_image_path, 'rb') as stored_image_file:
                    stored_image = preprocess_image(stored_image_file)
                    
                if uploaded_image:
                    uploaded_image = preprocess_image(uploaded_image)
                    
                    stored_features = extract_features(stored_image)
                    uploaded_features = extract_features(uploaded_image)
                    
                    if compare_features(uploaded_features, stored_features):
                        return render(request, 'welcome.html', {'username': username})
                    else:
                        return render(request, 'fingerLogin.html', {'data': 'Fingerprint does not match'})
                else:
                    return render(request, 'fingerLogin.html', {'data': 'Uploaded image is missing'})
            else:
                return render(request, 'fingerLogin.html', {'data': 'User or Image not found'})
        else:
            return render(request, 'fingerLogin.html', {'data': 'Invalid User Login Details'})
    
    return render(request, 'login.html')



def WebCam(request):
    if request.method == 'GET':
        data = str(request)
        formats, imgstr = data.split(';base64,')
        imgstr = imgstr[0:(len(imgstr)-2)]
        data = base64.b64decode(imgstr)
        if os.path.exists("image/static/photo/test.png"):
            os.remove("image/static/photo/test.png")
        with open('image/static/photo/test.png', 'wb') as f:
            f.write(data)
        f.close()
        context= {'data':"done"}
        return HttpResponse("Image saved")    

def checkUser(name):
    flag = 0
    for i in range(len(blockchain.chain)):
          if i > 0:
              b = blockchain.chain[i]
              data = b.transactions[0]
              print(data)
              arr = data.split("#")
              if arr[0] == name:
                  flag = 1
                  break
    return flag            


def Signup(request):
    if request.method == 'POST':
      global username, password, contact, email, address
      username = request.POST.get('username', False)
      password = request.POST.get('password', False)
      contact = request.POST.get('contact', False)
      email = request.POST.get('email', False)
      address = request.POST.get('address', False)
      context= {'data':'Capture Your face'}
      if not username or not password or not contact or not email or not address:
        messages.error(request, "ALL fields are required.")
        return render(request, "Register.html",{'error_message':"All fields are required."})

      return render(request, 'CaptureFace.html', context)

def AdminLogin(request):
    pass

def saveSignup(request):
    if request.method == 'POST':
        global username, password, contact, email, address

        # Load and process the image
        img = cv2.imread('image/static/photo/test.png')
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        face_component = None
        faces = face_detection.detectMultiScale(gray, 1.3, 5)

        for (x, y, w, h) in faces:
            face_component = img[y:y+h, x:x+w]

        if face_component is not None:
            # Save the face component image
            face_image_path = f'image/static/profiles/{username}.png'
            cv2.imwrite(face_image_path, face_component)

            # Connect to the database
            db_connection = pymysql.connect(
                host='127.0.0.1',
                port=3306,
                user='root',
                password='12345',
                database='facial_login',
                charset='utf8'
            )
            db_cursor = db_connection.cursor()

            # Check if the user already exists in the `register` table
            check_user_query_register = "SELECT COUNT(*) FROM register WHERE username = %s"
            db_cursor.execute(check_user_query_register, (username,))
            user_count_register = db_cursor.fetchone()[0]

            if user_count_register > 0:
                context = {'data': 'User already registered through Facial'}
            else:
                # Check if the user exists in the `finger_register` table
                check_user_query_finger_register = "SELECT COUNT(*) FROM finger_register WHERE username = %s"
                db_cursor.execute(check_user_query_finger_register, (username,))
                user_count_finger_register = db_cursor.fetchone()[0]

                if user_count_finger_register > 0:
                    context = {'data': 'User already registered through fingerprint'}
                else:
                    # Insert the new user into the `register` table
                    register = 'Facial'
                    insert_query = """
                        INSERT INTO register (username, password, contact, email, address, register) 
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """
                    db_cursor.execute(insert_query, (username, password, contact, email, address, register))
                    db_connection.commit()

                    if db_cursor.rowcount == 1:
                        context = {'data': 'Signup Process Completed'}
                    else:
                        context = {'data': 'Unable to register'}

            # Close the database connection
            db_cursor.close()
            db_connection.close()

            return render(request, 'Register.html', context)
        else:
            context = {'data': 'Unable to detect face or user is already registered'}
            return render(request, 'Register.html', context)

    context = {'data': 'Invalid request method'}
    return render(request, 'Register.html', context) 

def getOutput(status):
    print(status)
    
def UserLogin(request):
    if request.method == 'POST':
        global username
        username = request.POST.get('username', False)
        password = request.POST.get('password', False)
        status = 'none'
        con = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = '12345', database = 'facial_login',charset='utf8')
        with con:
            cur = con.cursor()
            cur.execute("select * FROM register")
            rows = cur.fetchall()
            for row in rows:
                if row[0] == username and row[1] == password:
                    status = 'success'
                    break
        if status == 'success':
            context= {'data':'<center><font size="3" color="black">Welcome '+username+'<br/><br/><br/><br/><br/>'}
            return render(request, 'Cast.html', context)
        else:
            context= {'data':'Invalid login details'}
            return render(request, 'Login.html', context)

def getUserImages():
    names = []
    ids = []
    faces = []
    dataset = "image/static/profiles"
    count = 0
    for root, dirs, directory in os.walk(dataset):
        for j in range(len(directory)):
            pilImage = Image.open(root+"/"+directory[j]).convert('L')
            imageNp = np.array(pilImage,'uint8')
            name = os.path.splitext(directory[j])[0]
            names.append(name)
            faces.append(imageNp)
            ids.append(count)
            count = count + 1
    print(str(names)+" "+str(ids))        
    return names, ids, faces 

def getName(predict, ids, names):
    name = "Unable to get name"
    for i in range(len(ids)):
        if ids[i] == predict:
            name = names[i]
            break
    return name         


def ValidateUser(request):
    if request.method == 'POST':
        global username
        status = "unable to predict user"
        img = cv2.imread('image/static/photo/test.png')
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        face_component = None
        faces = face_detection.detectMultiScale(img,scaleFactor=1.1,minNeighbors=5,minSize=(30,30),flags=cv2.CASCADE_SCALE_IMAGE)
        status = "Unable to predict.Please retry"
        #for (x, y, w, h) in faces:
        #    face_component = gray[y:y+h, x:x+w]
        if len(faces) > 0:
            faces = sorted(faces, reverse=True,key=lambda x: (x[2] - x[0]) * (x[3] - x[1]))[0]
            (fX, fY, fW, fH) = faces
            face_component = gray[fY:fY + fH, fX:fX + fW]
        else:
            status = 'Unable to detect face'
            
        if face_component is not None:
            names, ids, faces = getUserImages()
            recognizer.train(faces, np.asarray(ids))
            predict, conf = recognizer.predict(face_component)
            print(str(predict)+" === "+str(conf))
            if(conf < 80):
                validate_user = getName(predict, ids, names)
                print(str(validate_user)+" "+str(username))
                if validate_user == username:
                    status = "success"
        else:
            status = "Unable to detect face"
        if status == "success":
            flag = checkUser(username)
            if flag == 0:
                output = getOutput("User predicted as : "+username+"<br/><br/>")
                context= {
                    'data':output,
                    'username': username,
                    'id': ids,
                    'faces': faces ,  
                }

                return render(request, 'welcome.html', context)
            else:
                context= {'data':"User not Recognised"}
            return render(request, 'login.html', context)
        else:
            context= {'data':status}
            return render(request, 'login.html', context)

def Profile(request):
    username = request.GET.get('username')
        # Connect to the MySQL database using pymysql
    con = pymysql.connect(
        host='127.0.0.1',
        port=3306,
        user='root',
        password='12345',
        database='facial_login',
        charset='utf8'
    )
    names, ids, arrays  = getUserImages()
    def numpy_array_to_base64(array):
        img = Image.fromarray(array)
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
        return img_str

    images_base64 = [numpy_array_to_base64(array) for array in arrays]

     # Initialize empty dictionary to store user data
    user_data = {}

    with con:
        cur = con.cursor()
        
        # Check in the 'register' table
        cur.execute("SELECT * FROM register WHERE username = %s", (username,))
        row = cur.fetchone()
        
        if row:
            user_data = {
                'username': row[0],
                'email': row[3],  # Assuming email is in the 4th column
                'contact': row[2],
                'address': row[4],
                'register': row[6],
            }
        else:
            # Check in the 'finger_register' table
            cur.execute("SELECT * FROM finger_register WHERE username = %s", (username,))
            row = cur.fetchone()
            
            if row:
                user_data = {
                    'username': row[1],
                    'email': row[4],  # Assuming email is in the 4th column
                    'contact': row[3],
                    'address': row[5],
                    'register': row[7],
                }
            else:
                # User not found in either table
                user_data = {'error': 'User not found'}

    # Pass the user data to the template
    context = {
        'user_data': user_data,
        'username': username
    }

    return render(request, 'profile.html', context)

def upload(request):
    if request.method == 'GET':
        username = request.GET.get('username', '')
    return render(request, 'upload.html', {'username': username})

def doc_upload(request):
    username = request.GET.get('username', 'Noname')
    if request.method == 'POST':
        username = request.POST.get('username')
        doc_name = request.POST.get('docname')
        doc_desc = request.POST.get('docdesc')
        docupload = request.FILES.get('docupload')

        if not docupload:
            messages.error(request, "Please upload  a document.")
            return render(request, 'upload.html')


        # Validate the uploaded file type
        allowed_file_types = ['application/pdf', 'application/msword',
                              'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                              'text/plain']

        if docupload.content_type not in allowed_file_types:
            messages.error(request, "Only .pdf, .docx, .doc, or .txt files are allowed.")
            return render(request, 'upload.html')
        
        #encrypted the uploaded file
        try:
            encrypted_file_content = encrypt_file(docupload)

            #save the encrypted file 
            if not os.path.exists(os.path.join('image/static/encrypted_files')):
                os.makedirs(os.path.join('image/static/encrypted_files'))
            
            save_path = os.path.join('image/static/encrypted_files',f"{username}-{docupload.name}" + '.enc')
            file_name_path = f"{username}-{docupload.name}.enc"
            with open(save_path, 'wb') as encrypted_file:
                encrypted_file.write(encrypted_file_content)
        except Exception as e:
            messages.error(request, f"An error occurred during upload or encryption: {e}")
            return render(request, 'upload.html', {'username':username})

        #mysql connectivity

        db_connection = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = '12345', database = 'facial_login',charset='utf8')
        db_cursor = db_connection.cursor()

        sql_query = "INSERT INTO documents(username,doc_name,doc_desc,doc_path) VALUES ('"+username+"','"+doc_name+"','"+doc_desc+"','"+file_name_path+"')"
        db_cursor.execute(sql_query)
        db_connection.commit()
    return render(request, 'upload.html', {'username': username,'message': 'Document Uploaded', 'enc': 'Ecrypt complete'})


def encrypt_file(uploaded_file):
    file_data = uploaded_file.read()
    encrypted_data = cipher_suite.encrypt(file_data)
    return encrypted_data


def decrypt_file(encrypted_file_path):
    try:
        with open(encrypted_file_path, 'rb') as encrypted_file:
            encrypted_data = encrypted_file.read()
        decrypted_data = cipher_suite.decrypt(encrypted_data)
        return decrypted_data
    except Exception as e:
        print(f"Error decrypting file: {e}")
        raise


def adminPage(request):
    db_connection = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = '12345', database = 'facial_login',charset='utf8')
    db_cursor = db_connection.cursor()
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
    else:
        username = 'admin'
        password = 'admin'

    if username == 'admin' and password == 'admin':

        try:
            db_cursor = db_connection.cursor()
            sql_query1 = "SELECT * FROM register"
            db_cursor.execute(sql_query1)
            rows = db_cursor.fetchall()
            products = []
            for row in rows:
                products.append({
                    'username': row[0],
                    'password':row[1],
                    'contact':row[2],
                    'email':row[3],
                    'address': row[4],
                    'id': row[5],
                    'register':row[6]
                })
            sql_query2 = "SELECT * FROM finger_register"
            db_cursor.execute(sql_query2)
            rows = db_cursor.fetchall()
            users = []
            for row in rows:
                users.append({
                    'id':row[0],
                    'username': row[1],
                    'password':row[2],
                    'contact':row[3],
                    'email':row[4],
                    'address': row[5],
                    'image': row[6],
                    'register':row[7]
                })
            return render(request, 'adminPage.html',{'products':products, 'users':users})
        finally:
            db_connection.close()
    else:
        return render(request, 'Admin.html',{'error':"User not found"})


def edit_product(request):
    pass;



def data_upload(request):
    if request.method == 'GET':
        db_connection = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = '12345', database = 'facial_login',charset='utf8')
        db_cursor = db_connection.cursor()
        try:
            db_cursor = db_connection.cursor()
            sql_query = "SELECT * FROM documents"
            db_cursor.execute(sql_query)
            rows = db_cursor.fetchall()
            data_upload = []
            for row in rows:
                data_upload.append({
                    'id': row[0],
                    'username':row[1],
                    'doc_name':row[2],
                    'doc_desc':row[3],
                    'doc_path':row[4],
                    'timestamp': row[5],
                })
            return render(request, 'adminPage.html',{'data_upload':data_upload})
        finally:
            db_connection.close()

def view_doc_user(request,username):
    if request.method == "GET":
        db_connection = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = '12345', database = 'facial_login',charset='utf8')
        db_cursor = db_connection.cursor()
        try:
            db_cursor = db_connection.cursor()
            sql_query = "SELECT * FROM documents  where username = %s"
            db_cursor.execute(sql_query, (username,))
            rows = db_cursor.fetchall()
            data_upload = []
            for row in rows:
                data_upload.append({
                    'id': row[0],
                    'username':row[1],
                    'doc_name':row[2],
                    'doc_desc':row[3],
                    'doc_path':row[4],
                    'timestamp': row[5],
                })
            return render(request, 'userPage.html',{'data_upload':data_upload,'username':username})
        finally: 
            db_connection.close()

def view_doc(request,username):
    if request.method == "GET":
        db_connection = pymysql.connect(host='127.0.0.1',port = 3306,user = 'root', password = '12345', database = 'facial_login',charset='utf8')
        db_cursor = db_connection.cursor()
        try:
            db_cursor = db_connection.cursor()
            sql_query = "SELECT * FROM documents  where username = %s"
            db_cursor.execute(sql_query, (username,))
            rows = db_cursor.fetchall()
            data_upload = []
            for row in rows:
                data_upload.append({
                    'id': row[0],
                    'username':row[1],
                    'doc_name':row[2],
                    'doc_desc':row[3],
                    'doc_path':row[4],
                    'timestamp': row[5],
                })
            return render(request, 'adminPage.html',{'data_upload':data_upload})
        finally: 
            db_connection.close()





def download_file(request, file_name):
    # Normalize the file name for URL encoding
    file_name = unquote(file_name)
    
    # Construct the path for the encrypted file
    encrypted_file_path = os.path.join(settings.BASE_DIR, 'image', 'static', 'encrypted_files', file_name)
    
    # Check if the encrypted file exists
    if not os.path.isfile(encrypted_file_path):
        print(f"Encrypted file does not exist: {encrypted_file_path}")
        raise Http404("Encrypted file does not exist")
    
    # Decrypt the file
    try:
        decrypted_data = decrypt_file(encrypted_file_path)
    except Exception as e:
        print(f"Error decrypting file: {e}")
        raise Http404("Error decrypting file")

    # Remove the first part of the filename
    base_file_name = file_name
    if file_name.endswith('.enc'):
        base_file_name = file_name[:-4]  # Remove .enc extension

    # Extract the actual filename by removing the first part
    # Assuming the first part of the filename is separated by an underscore (_)
    parts = base_file_name.split('-', 1)
    if len(parts) > 1:
        base_file_name = parts[1]
    else:
        base_file_name = parts[0]  # If no separator, use the whole base file name

    # Create an HTTP response with the decrypted content
    response = HttpResponse(decrypted_data, content_type='application/octet-stream')
    response['Content-Disposition'] = f'attachment; filename="{base_file_name}"'

    return response