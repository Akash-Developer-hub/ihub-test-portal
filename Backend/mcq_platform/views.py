# views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from pymongo import MongoClient
import json
import jwt
import datetime
import csv
from io import StringIO


# Initialize MongoDB client
client = MongoClient("mongodb+srv://ihub:ihub@test-portal.lcgyx.mongodb.net/test_portal_db?retryWrites=true&w=majority")
db = client["test_portal_db"]  # Replace with your database name
collection = db["MCQ_Assessment_Data"]  # Replace with your collection name
assessment_questions_collection = db["TestQuestion"]


SECRET_KEY = "Rahul"

@csrf_exempt
def start_contest(request):
    if request.method == "POST":
        try:
            # Parse the incoming request body
            data = json.loads(request.body)
            contest_id = data.get("contestId")
            if not contest_id:
                return JsonResponse({"error": "Contest ID is required"}, status=400)
            
            # Generate a JWT token
            payload = {
                "contestId": contest_id,
                "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1),  # Token valid for 1 hour
            }
            token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")

            return JsonResponse({"token": token}, status=200)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Invalid request method"}, status=400)

def generate_token(contest_id):
    payload = {
        "contest_id": contest_id,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)  # Token expiration
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def decode_token(token):
    print("Decode")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        contest_id = payload.get("contestId")  # Ensure correct key
        if not contest_id:
            raise ValueError("Invalid token: 'contestId' not found.")
        return contest_id
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired.")
    except jwt.InvalidTokenError:
        raise ValueError("Invalid token.")


@csrf_exempt
def save_data(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            contest_id = data.get("contestId")
            if not contest_id:
                return JsonResponse({"error": "contestId is required"}, status=400)
            
            collection.insert_one(data)
            return JsonResponse({"message": "Data saved successfully", "contestId": contest_id}, status=200)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Invalid request method"}, status=400)


@csrf_exempt
def save_question(request):
    if request.method == "POST":
        try:
            # Validate Authorization Header
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return JsonResponse({"error": "Authorization header missing or invalid."}, status=401)

            # Decode the token to get the contest_id
            token = auth_header.split(" ")[1]
            contest_id = decode_token(token)

            # Parse the request body
            data = json.loads(request.body)
            questions = data.get("questions", [])
            if not questions:
                return JsonResponse({"error": "No questions provided"}, status=400)

            # Check if the contest_id already exists
            assessment = assessment_questions_collection.find_one({"contest_id": contest_id})
            if not assessment:
                # Create a new contest entry if it doesn't exist
                print(f"Creating new contest entry for contest_id: {contest_id}")
                assessment_questions_collection.insert_one({
                    "contest_id": contest_id,
                    "questions": []
                })
                assessment = {"contest_id": contest_id, "questions": []}

            # Add new questions to the contest
            existing_questions = assessment.get("questions", [])
            last_question_id = max((q.get("question_id", 0) for q in existing_questions), default=0)

            for i, question in enumerate(questions):
                question["question_id"] = last_question_id + i + 1
                existing_questions.append(question)

            # Update the MongoDB document
            assessment_questions_collection.update_one(
                {"contest_id": contest_id},
                {"$set": {"questions": existing_questions}}
            )
            return JsonResponse({
                "message": "Questions saved successfully!",
                "questions": [{"question_id": q["question_id"], **q} for q in questions]
            }, status=200)
        except ValueError as e:
            return JsonResponse({"error": str(e)}, status=401)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Invalid request method"}, status=400)


@csrf_exempt
def get_questions(request):
    if request.method == "GET":
        print("GET request received")
        try:
            # Validate Authorization Header
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                print("Authorization header missing or invalid")
                return JsonResponse({"error": "Unauthorized access"}, status=401)

            # Decode the token to get the contest_id
            token = auth_header.split(" ")[1]
            contest_id = decode_token(token)
            print(f"Decoded contest ID: {contest_id}")

            # Check if the contest exists in the database
            assessment = assessment_questions_collection.find_one({"contest_id": contest_id})
            if not assessment:
                # If no contest found, create a new entry with an empty questions list
                print(f"Creating new contest entry for contest_id: {contest_id}")
                assessment_questions_collection.insert_one({
                    "contest_id": contest_id,
                    "questions": []
                })
                assessment = {"contest_id": contest_id, "questions": []}

            # Fetch the questions
            questions = assessment.get("questions", [])
            print(f"Fetched questions: {questions}")
            return JsonResponse({"questions": questions}, status=200)
        except ValueError as e:
            print(f"Authorization error: {str(e)}")
            return JsonResponse({"error": str(e)}, status=401)
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Invalid request method"}, status=400)


@csrf_exempt
def update_question(request):
    if request.method == "PUT":
        try:
            token = request.headers.get("Authorization").split(" ")[1]
            contest_id = decode_token(token)

            data = json.loads(request.body)
            question_id = data.get("question_id")

            result = assessment_questions_collection.update_one(
                {
                    "contest_id": contest_id,
                    "questions.question_id": question_id,
                },
                {
                    "$set": {
                        "questions.$.questionType": data.get("questionType", "MCQ"),
                        "questions.$.question": data.get("question", ""),
                        "questions.$.options": data.get("options", []),
                        "questions.$.correctAnswer": data.get("correctAnswer", ""),
                        "questions.$.mark": data.get("mark", 0),
                        "questions.$.negativeMark": data.get("negativeMark", 0),
                        "questions.$.randomizeOrder": data.get("randomizeOrder", False),
                    }
                }
            )

            if result.matched_count == 0:
                return JsonResponse({"error": "Question not found"}, status=404)

            return JsonResponse({"message": "Question updated successfully"})
        except ValueError as e:
            return JsonResponse({"error": str(e)}, status=401)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Invalid request method"}, status=400)


@csrf_exempt
def finish_contest(request):
    if request.method == "POST":
        try:
            # Validate Authorization Header
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return JsonResponse({"error": "Authorization header missing or invalid."}, status=401)

            # Decode the token to get the contest_id
            token = auth_header.split(" ")[1]
            contest_id = decode_token(token)

            # Get the list of questions from the request body
            data = json.loads(request.body)
            questions_data = data.get("questions", [])

            if not questions_data:
                return JsonResponse({"error": "No question data provided."}, status=400)

            # Retrieve the existing entry for the contest_id
            existing_entry = collection.find_one({"contestId": contest_id})

            if existing_entry:
                # Update the existing entry with the new questions data
                collection.update_one(
                    {"contestId": contest_id},
                    {"$set": {"questions": questions_data}}  # Save the entire questions data
                )
            else:
                # If no entry exists for this contest_id, create a new one with all the question data
                collection.insert_one({
                    "contestId": contest_id,
                    "questions": questions_data,  # Store the full question data here
                    "assessmentOverview": {},  # Preserve the structure
                    "testConfiguration": {}
                })

            return JsonResponse({"message": "Contest finished successfully!"}, status=200)
        except ValueError as e:
            return JsonResponse({"error": str(e)}, status=401)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Invalid request method"}, status=400)


@csrf_exempt
def bulk_upload_questions(request):
    if request.method == "POST":
        try:
            # Validate Authorization Header
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return JsonResponse({"error": "Authorization header missing or invalid."}, status=401)

            # Decode the token to get the contest_id
            token = auth_header.split(" ")[1]
            contest_id = decode_token(token)

            # Retrieve the uploaded file
            file = request.FILES.get("file")
            if not file:
                return JsonResponse({"error": "No file uploaded"}, status=400)

            # Parse CSV content
            file_data = file.read().decode("utf-8")
            csv_reader = csv.DictReader(StringIO(file_data))
            questions = []
            for row in csv_reader:
                question = {
                    "questionType": "MCQ",  # Assuming MCQ for bulk upload
                    "question": row.get("question", "").strip(),
                    "options": [
                        row.get("option_1", "").strip(),
                        row.get("option_2", "").strip(),
                        row.get("option_3", "").strip(),
                        row.get("option_4", "").strip(),
                        row.get("option_5", "").strip(),
                        row.get("option_6", "").strip(),
                    ],
                    "correctAnswer": row.get("correct_answer", "").strip(),
                    "mark": int(row.get("mark", 0)),
                    "negativeMark": int(row.get("negative_marking", 0)),
                    "randomizeOrder": False,  # Default to False
                }
                questions.append(question)

            return JsonResponse({"questions": questions}, status=200)
        except ValueError as e:
            return JsonResponse({"error": str(e)}, status=401)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Invalid request method"}, status=400)