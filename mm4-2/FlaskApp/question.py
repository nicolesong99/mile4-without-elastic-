from flask import Blueprint, render_template, abort, Flask, request, url_for, json, redirect, Response, session, g
from werkzeug.security import check_password_hash, generate_password_hash
import  datetime, json
from flask_mail import Mail
from flask_mail import Message
import pymongo 
from pymongo import MongoClient
import time
from bson.objectid import ObjectId

client = MongoClient('130.245.170.76', 27017)
bp = Blueprint('question', __name__, template_folder='templates')

db = client.stack
userTable = db['user'] 
answerTable = db['answer']
questionTable = db['question']
ipTable = db['ip']
upvoteTable = db['upvote']
mediaTable = db['mediaID']


from cassandra.cluster import Cluster
cluster = Cluster(['130.245.170.76'])
cassSession = cluster.connect(keyspace='hw5')

@bp.app_errorhandler(404)
def handle404(error):
    return responseNO({'status': 'error', 'error': '404 error'})
@bp.app_errorhandler(500)
def handle505(error):
    return responseNO({'status': 'error', 'error': '500 error'})

@bp.route('/questions/add', methods=["POST", "GET"])
def addQuestion():
    if request.method == "GET":
        return render_template('addQuestion.html')
    if(request.method == 'POST'):
        name = request.cookies.get('token')
        if not name:
            print('Add Question Wrong SESSION', (name))     
            return responseNO({'status': 'error', 'error': 'Wrong user session'})

        title = None
        body = None
        tags = None
        media = []
        d = request.json
        

        if 'media' in d:
            media = request.json['media']
            print('Quesiotns/ADD +++++++++++++++++++++++++++++MEDIA: ', media)
            if len(media) != 0:
                for item in media:
                        is_found = mediaTable.find_one({"mediaID": item})
                        if is_found:
                            print('Media ID FOUND IN ANOTHER QUESTION ')
                            return responseOK({ 'status': 'error', 'error':"media ID already exists"}) 
                        
                        query = "SELECT * FROM imgs WHERE fileID = '" + item + "';"
                        row = cassSession.execute(query)[0]
                        name = row[3]
                        if name != request.cookies.get('token'):
                            return responseOK({ 'status': 'error', 'error':"media does not belong to poster"}) 

        if ('title' in d) and ('body' in d) and ('tags' in d) :
            title = request.json['title'].encode("utf-8")
            body = request.json['body'].encode("utf-8")
            tags = request.json['tags']
        else:
            return responseOK({'status': 'error', 'error': 'Json key doesnt exist'})
                
        username = request.cookies.get('token')
        user_filter = userTable.find_one({'username': username})
        reputation = user_filter['reputation']
        question =  {
                                    'user': {   'username': str(username),
                                                        'reputation': reputation
                                                    },
                                    'title': title, 
                                    'body': body,
                                    'score': 0,
                                    'view_count': 0,
                                    'answer_count': 0,
                                    'timestamp': int(time.time()),
                                    'media': media,
                                    'tags': tags,
                                    'accepted_answer_id': None,
                                    'username': str(username),
                                    'realIP': request.remote_addr
                                }
        pid = questionTable.insert(question)
        pid = str(pid)
        for item in media:
            mediaTable.insert({"mediaID": item, 'pid': pid})

        return responseOK({ 'status': 'OK', 'id':pid}) 

@bp.route('/questions/<IDD>', methods=[ "GET", 'DELETE'])
def getQuestion(IDD):
    pid = ObjectId(str(IDD))
    if request.method == 'GET':
        #print("=========================QUESTION/ID====GET===============================")
        result = questionTable.find_one({"_id": pid})

        if( result == None):
            print("QUESTION ID DOESNT EXIST")
            print(request.remote_addr)
            return responseOK({'status':'error', 'error': 'id doesnt exist'})
        ip = request.remote_addr
        ip = str(ip)
        plus = 0

        name = request.cookies.get('token')
        
        if not name:
            if ipTable.find_one({'ip':ip , 'pid':pid}) == None:
                ipTable.insert({'ip':ip, 'pid': pid})
                plus = 1
        else:
            if ipTable.find_one({'ipN': name , 'pid':pid} ) == None:
                ipTable.insert({'ipN' : name, 'pid': pid})
                plus = 1
        
        count = result['view_count']
        questionTable.update_one({'_id':pid}, { "$set": {'view_count': count + plus}} )
        result = questionTable.find_one({'_id':pid})
        score = result['score']
        view_count = result['view_count']
        answer_count = result['answer_count']
        media = result['media']
        tags = result['tags']
        title = result['title']
        body = result['body']
        pid = str(result['_id'])
        timestamp = result['timestamp']
        
        user = result['user']['username']
        reputation = userTable.find_one({'username':user})
        reputation = reputation['reputation']

        question =  {   'status':'OK',
                            "question": {
                                    "score": score,
                                    "view_count": view_count,
                                    "answer_count": 0,
                                    "media": media,
                                    "tags": tags,
                                    "accepted_answer_id": result['accepted_answer_id'],
                                    "title": title,
                                    "body": body,
                                    "id": pid,
                                    "timestamp": timestamp,
                                    "user": {
                                                'username': user,
                                                'reputation' :reputation
                                            }
                                    }
                        }
        return responseOK(question)

    elif request.method == 'DELETE':
        print("=========================QUESTION/ID====DELETE===============================")
        name = request.cookies.get('token')
        
        if not name:
            print('Add Question Wrong SESSION')     
            return responseNO({'status': 'error', 'error': 'Wrong user session'})
        else:
            pid = ObjectId(str(IDD))
            result = questionTable.find_one({'_id':pid})
            if( result == None):
                print('FAILED DELTED, invalid QUESTIONS ID')
                return responseNO({'status':'error','error':'Question does not exist'})

            username = result['user']['username']
            if name != username:
                print('FAILED DELTED, user is not original')
                return responseNO({'status':'error', 'error': 'Not orginal user'})
            else:
                print('SUCCESSFULLY DELTED, user is original')
                question_delete = questionTable.find_one({'_id': pid})
                allMedia = question_delete['media']
                for m in allMedia:
                    query = "DELETE FROM imgs WHERE fileID = '" + m + "';"
                    print('=============', m)
                    row = cassSession.execute(query)
                
                answer_delete = answerTable.find({'pid': pid})
                for a in answer_delete:
                    ans_media = a['media']
                    for i in ans_media:
                        query = "DELETE FROM imgs WHERE fileID = '" + i + "';"
                        print('=============', m)
                        row = cassSession.execute(query)


                questionTable.delete_one({'_id': pid})
                answerTable.delete_many({'pid': pid})
                ipTable.delete_many({'pid': pid})
                return responseOK({'status': 'OK'})
                

@bp.route('/questions/<IDD>/answers/add', methods=["POST", "GET"])
def addAnswer(IDD):
    if request.method == 'POST':
        name = request.cookies.get('token')
        if not name:
            print("NO session answer")
            return responseOK({'status': 'error','error': 'not logged in'})
        
        pid = ObjectId(str(IDD))
        body = request.json['body']
        media = []
        
        if ('media' in request.json):
            media = request.json['media']
            print('Answers/ADD media: ++++++++++++++++++++++ANSWER++++++MEDIA ', media)
            if len(media) != 0:
                for item in media:
                        is_found = mediaTable.find_one({"mediaID": item})
                        if is_found != None: #if id exist already, return error
                            return responseOK({ 'status': 'error', 'error':"media ID already exists"}) 
                        
                        query = "SELECT * FROM imgs WHERE fileID = '" + item + "';"
                        row = cassSession.execute(query)[0]
                        name = row[3]
                        if name != request.cookies.get('token'):
                            return responseOK({ 'status': 'error', 'error':"media does not belong to poster"}) 

        userID = userTable.find_one({'username': request.cookies.get('token')})['_id']
        userID = str(userID)
        
        answer =    {
                    'pid': pid,
                    'body':body,
                    'media': media,
                    'user': request.cookies.get('token'),
                    'userID':  userID,
                    'timestamp': (time.time()),
                    'is_accepted': False,
                    'score' : 0,
                    'username': request.cookies.get('token')
                    }
        aid = answerTable.insert(answer)
        aid = str(aid)

        if len(media) != 0:
            for item in media:
                    is_found = mediaTable.find_one({"mediaID": item})
                    if is_found == None:
                        mediaTable.insert({"mediaID": item, 'aid': aid})
                    else:
                        return responseOK({ 'status': 'error', 'error':"media ID already exists"}) 

        return responseOK({'status': 'OK', 'id': str(aid)})

@bp.route('/questions/<IDD>/answers', methods=['GET'])
def getAnswers(IDD):
    if request.method == 'GET':
        
        pid = ObjectId(str(IDD))
        allAnswers = answerTable.find({'pid': pid})
        answerReturn = {"status":"OK", 'answers': []}

        for result in allAnswers:
            temp =  {
                        'id': str(result['_id']),
                        'user': result['user'],
                        'body': result['body'],
                        'score': result['score'],
                        'is_accepted': result['is_accepted'],
                        'timestamp': result['timestamp'],
                        'media': result['media']
                    }
            answerReturn['answers'].append(temp)
        #print(answerReturn)

        return responseOK(answerReturn)

@bp.route('/questions/<IDD>/upvote', methods=['POST'])
def upvoteQuestion(IDD):
    if request.method == 'POST':
        pid = str(IDD)
        name = request.cookies.get('token')
        if not name:
            print('upvote Wrong session')
            return responseOK({'status': 'error','error': 'Please login to upvote question'})
        print('===========================/questions/<IDD>/upvote===================================')
        upvote = request.json['upvote']
        user = request.cookies.get('token')
        print ([pid, upvote, user]  )
        result = upvoteTable.find_one({'username' : user, 'pid': pid} )
        questionResult = questionTable.find_one( {'_id': ObjectId(str(IDD)) })
        realUser = questionResult['username']
        if upvote == True:
            if result == None:
                upvoteTable.insert({'username': user, 'pid': pid, 'vote': 1})
                updateQuestionScore(pid, realUser, 1, 1)
            elif result['vote'] ==  1:
                upvoteTable.update_one({'username':user, 'pid': pid} , { "$set": {'vote': 0} } )
                updateQuestionScore(pid, realUser, -1,-1)   
            elif result['vote'] ==  0:
                upvoteTable.update_one({'username':user, 'pid': pid} , { "$set": {'vote': 1} } )
                updateQuestionScore(pid, realUser, 1, 1)
            elif result['vote'] == -1:
                upvoteTable.update_one({'username':user, 'pid': pid} , { "$set": {'vote': 1} } )
                updateQuestionScore(pid, realUser, 2, 1)
        #################################################FALSE##########################################
        elif upvote == False:
            if result == None:
                upvoteTable.insert({'username': user, 'pid': pid, 'vote': -1})
                updateQuestionScore(pid, realUser, -1, -1)
            elif result['vote'] ==  -1:
                upvoteTable.update_one({'username':user, 'pid': pid} , { "$set": {'vote': 0} } )            
                updateQuestionScore(pid, realUser, 1, 1)    
            elif result['vote'] ==  0:
                upvoteTable.update_one({'username':user, 'pid': pid} , { "$set": {'vote': -1} } )
                updateQuestionScore(pid, realUser, -1, -1)
            elif result['vote'] == 1:
                upvoteTable.update_one({'username':user, 'pid': pid} , { "$set": {'vote': -1} } )
                updateQuestionScore(pid, realUser, -2, -1)
        return responseOK({'status': 'OK'})

@bp.route('/answers/<IDD>/upvote', methods=['POST'])
def upvoteAnswer(IDD):
    if request.method == 'POST':
        aid = str(IDD)
        
        name = request.cookies.get('token')
        if not name:
            return responseOK({'status': 'error','error': 'Please login to upvote answer'})
        print('===========================/answers/<IDD>/upvote===================================')
        upvote = request.json['upvote']
        user = request.cookies.get('token')
        print ([aid, upvote, user]  )
        result = upvoteTable.find_one({'username' : user, 'aid': aid} )
        answerResult = answerTable.find_one( {'_id': ObjectId(str(IDD)) })
        if answerResult == None:
            return responseNO({'status': 'error','error': 'ID Doesnt exist'})
        realUser = answerResult['username']
        if upvote == True:
            if result == None:
                upvoteTable.insert({'username': user, 'aid': aid, 'vote': 1})
                updateAnswerScore(aid, realUser, 1,1)   
            elif result['vote'] ==  1:
                upvoteTable.update_one({'username':user, 'aid': aid} , { "$set": {'vote': 0} } )
                updateAnswerScore(aid, realUser, -1,-1) 
            elif result['vote'] ==  0:
                upvoteTable.update_one({'username':user, 'aid': aid} , { "$set": {'vote': 1} } )
                updateAnswerScore(aid, realUser, 1, 1)
            elif result['vote'] == -1:
                upvoteTable.update_one({'username':user, 'aid': aid} , { "$set": {'vote': 1} } )
                updateAnswerScore(aid, realUser, 2, 1)
        #################################################FALSE##########################################
        elif upvote == False:
            if result == None:
                upvoteTable.insert({'username': user, 'aid': aid, 'vote': -1})
                updateAnswerScore(aid, realUser, -1, -1)
            elif result['vote'] ==  -1:
                upvoteTable.update_one({'username':user, 'aid': aid} , { "$set": {'vote': 0} } )            
                updateAnswerScore(aid, realUser, 1, 1)  
            elif result['vote'] ==  0:
                upvoteTable.update_one({'username':user, 'aid': aid} , { "$set": {'vote': -1} } )
                updateAnswerScore(aid, realUser, -1, -1)
            elif result['vote'] == 1:
                upvoteTable.update_one({'username':user, 'aid': aid} , { "$set": {'vote': -1} } )
                updateAnswerScore(aid, realUser, -2, -1)
        return responseOK({'status': 'OK'})



@bp.route('/answers/<IDD>/accept', methods=['POST'])
def acceptAnswer(IDD):
    if request.method == 'POST':
        name = request.cookies.get('token')
        if not name:
            return responseOK({'status': 'error','error': 'Please login to accept answer'})
        aid = ObjectId(str(IDD))
        print('--------------------------------------ACCEPT--------------------------')
        answer = answerTable.find_one({'_id': aid})
        if answer == None:
            return responseNO({'status': 'error','error': 'ID Doesnt exist'})
        pid = answer['pid']
        
        question = questionTable.find_one({'_id': pid })
        poster = question['username']
        if request.cookies.get('token') != poster:
            return responseOK({'status': 'error', 'error': 'Not original poster'})
        
        qq = questionTable.find_one({'_id': pid })
        if qq['accepted_answer_id'] != None: #if answer already revolved the question
            return responseOK({'status': 'error', 'error':'Question already resolved'}) 

        answerTable.update_one({'_id': aid}, { "$set": {'is_accepted': True} })
        questionTable.update_one({'_id': pid }, { "$set": {'accepted_answer_id': IDD}} )
    
    return responseOK({'status': 'OK'})


@bp.route('/searchOK', methods=['GET'])
def searchOK():
    if request.method == 'GET':
        result = questionTable.find()
        login= 0
        if len(session) == 0:
            login = 0
        else:
            login = 1
        return render_template('questionTable.html', questionTable=result, login= login)

@bp.route('/search', methods=['POST'])
def search():
    if request.method == 'POST':
        print('--------------------------------Search-----------------------------')
        timestamp = time.time()
        if 'timestamp' in request.json:
            timestamp = request.json['timestamp']
        
        limit = 25
        if 'limit' in request.json:
            limit = request.json['limit']

        query = ''
        if 'q' in request.json:
            query = request.json['q'].encode("utf-8").strip().lower()

        sort_by = 'score'
        if 'sort_by' in request.json:
            print('-------found sortby')
            sort_by = request.json['sort_by']

        tags = []
        if 'tags' in request.json:
            print('-------found tags')
            tags = request.json['tags']

        has_media = False
        if 'has_media' in request.json:
            print('-------found has_media')
            has_media = request.json['has_media']

        accepted = False
        if 'accepted' in request.json:
            print('-------found accept')
            accepted = request.json['accepted']

        print("query: ", query)
        print("timestamp: ", timestamp )
        print("limit: ", limit)
        print("sort_by: ", sort_by)
        print("tags: ", tags )
        print("has_media: ", has_media)
        print("accepted: ", accepted)
        
        answer = filter_with_query(query, timestamp, limit, sort_by, tags, has_media, accepted)
        return responseOK(answer)


def responseOK(stat):
    data = stat
    jsonData = json.dumps(data)
    respond = Response(jsonData,status=200, mimetype='application/json')
    return respond

def responseNO(stat):
    data = stat
    jsonData = json.dumps(data)
    respond = Response(jsonData,status=404, mimetype='application/json')
    return respond


def updateQuestionScore(pid, user, qval, uval):
    question = questionTable.find_one( {'_id': ObjectId(pid)} )
    new_score = question['score'] + qval                            #plus one to question
    questionTable.update_one( {'_id': ObjectId(pid)} , { "$set": {'score': new_score} } )
    
    user_filter = userTable.find_one({'username': user})    #plus one to user reputation
    new_rep = user_filter['reputation']
    if new_rep == 1 and uval < 0:
        print('CANNOT ADD TO USER REP ', uval)
        return
    new_repp = new_rep + uval
    print("NEW REPP +++++++++++++++++ " ,new_repp )
    userTable.update_one({'username': user}, { "$set": {'reputation': new_repp} } )


def updateAnswerScore(aid, user, aval, uval):
    answer = answerTable.find_one( {'_id': ObjectId(aid)} )
    new_score = answer['score'] + aval                          #plus one to answer
    answerTable.update_one( {'_id': ObjectId(aid)} , { "$set": {'score': new_score} } )
    
    user_filter = userTable.find_one({'username': user})    #plus one to user reputation
    new_rep = user_filter['reputation']
    if new_rep == 1 and uval < 0:
        print('CANNOT ADD TO USER REP ', uval)
        return
    new_repp = new_rep + uval
    userTable.update_one({'username': user}, { "$set": {'reputation': new_repp} } )

def filter_with_query(query, timestamp, limit, sort_by, tags, has_media, accepted):
    my_query = {}
    my_query["timestamp"] = {"$lt": timestamp}

    if len(query) != 0:
        my_query["$text"]= {"$search": query }
    if accepted == True:
        my_query["accepted_answer_id"] = {"$ne": None}
    if has_media == True:
        my_query["media"] = {"$ne": []}
    if tags != []:
        my_query["tags"] = {"$all": tags}

    allQuestion =   questionTable.find(my_query).sort(sort_by, pymongo.DESCENDING)
    questFilter =[]
    count = 0
    for q in allQuestion:
        if count < limit:
            temp = {    'id': str(q['_id']),
                        'title':q['title'],
                        'body': q['body'],
                        'tags': q['tags'],
                        'answer_count': 0,
                        'media': q['media'],
                        'accepted_answer_id': q['accepted_answer_id'] ,
                        'user':q['user'],
                        'timestamp': q['timestamp'],
                        'score': q['score'],
                        "view_count": q['view_count']
                        }
            questFilter.append(temp)
            count+=1
        else:
            break
    return {'status' : 'OK', 'questions': questFilter, 'length': len(questFilter)}

def is_login(username, password):
    user = userTable.find_one({'username': username, 'password': password})
    if user == None:
        return False
    return True