from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import traceback
from pymongo import MongoClient
import os

# Update the MongoClient to use the provided connection string
client = MongoClient("mongodb+srv://ihub:ihub@test-portal.lcgyx.mongodb.net/test_portal_db?retryWrites=true&w=majority")
db = client["test_portal_db"]  # Ensure this matches the database name in your connection string
questions_collection = db['Coding_Questions_Library']
final_questions_collection = db['finalQuestions']

PROBLEMS_FILE_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'Frontend', 'public', 'json', 'questions.json')

def fetch_Questions(request):
    try:
        # Query the MongoDB collection
        coding_questions = list(questions_collection.find({}, {'_id': 1, 'title': 1, 'level': 1, 'problem_statement': 1,'samples':1,'hidden_samples':1}))
        
        # Map _id to id (convert ObjectId to string)
        for question in coding_questions:
            question['id'] = str(question.pop('_id'))  # Rename `_id` to `id`
        
        # Return the questions as a JSON response
        return JsonResponse({'problems': coding_questions}, status=200)

    except PyMongoError as e:
        # Log the error (optional)
        print(f"Database error: {e}")

        # Return an error response
        return JsonResponse({'error': 'Failed to fetch questions from the database'}, status=500)

    except Exception as e:
        # Catch any other unexpected errors
        print(f"Unexpected error: {e}")
        return JsonResponse({'error': 'An unexpected error occurred'}, status=500)

def save_problem_data(new_problem):
    """
    Adds a new problem to the problems array in Coding_Questions_Library. If a document with ObjectId already exists,
    it appends the new problem to problems; otherwise, it creates a new document.
    """
    try:
        # Structure the problem data
        problem_data = {
            "id": new_problem.get('id'),
            "title": new_problem.get('title', ''),
            "role": new_problem.get('role', []),
            "level": new_problem.get('level', ''),
            "problem_statement": new_problem.get('problem_statement', ''),
            "samples": new_problem.get('samples', []),
            "hidden_samples": new_problem.get('hidden_samples', [])
        }

        # Convert the main document ID to ObjectId
        main_document_id = ObjectId('6731ed9e1005131d602865de')
        existing_document = questions_collection.find_one({'_id': main_document_id})

        if existing_document:
            # Append new problem to the problems array
            result = questions_collection.update_one(
                {'_id': main_document_id},
                {'$push': {'problems': problem_data}}
            )
            message = 'Problem added to existing document!'
        else:
            # Create a new document if it doesn’t exist, with the problems array initialized
            new_document = {
                "_id": main_document_id,
                "problems": [problem_data]
            }
            result = questions_collection.insert_one(new_document)
            message = 'New document created and problem added!'

        if result:
            return JsonResponse({
                'message': message,
                'problem_id': problem_data['id']
            }, status=201)
        else:
            raise Exception("Failed to save the document")

    except Exception as e:
        return JsonResponse({
            'error': f'Error saving problem data: {str(e)}'
        }, status=400)

@csrf_exempt
def publish_questions(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            selected_questions = data.get('questions', [])

            # Verify that selected_questions is a valid list
            if not isinstance(selected_questions, list) or not selected_questions:
                return JsonResponse({'error': 'No questions selected'}, status=400)

            # Process selected questions only
            all_problems = []
            for question in selected_questions:
                question_data = questions_collection.find_one({"id": question['id']}, {"_id": 0})
                if question_data:
                    all_problems.append(question_data)

            # Save to finalQuestions collection
            contest_id = data.get('contestId', 'default_contest')
            visible_to = data.get('students', [])

            existing_document = final_questions_collection.find_one({"contestId": contest_id})

            if existing_document:
                final_questions_collection.update_one(
                    {"contestId": contest_id},
                    {'$push': {'problems': {'$each': all_problems}}}
                )
                message = 'Questions appended to existing contest!'
            else:
                final_questions_collection.insert_one({
                    "contestId": contest_id,
                    "problems": all_problems,
                    "visible_to": visible_to
                })
                message = 'Questions published successfully!'

            return JsonResponse({'message': message}, status=200)

        except Exception as e:
            return JsonResponse({'error': f'Error publishing questions: {str(e)}'}, status=500)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)


@csrf_exempt
def modify_problem_data(new_problem):
    """
    Modifies an existing problem in `Coding_Questions_Library` based on its ID.
    """
    try:
        problem_id = new_problem.get("id")
        result = questions_collection.update_one(
            {'problems.id': problem_id},  # Match within the `problems` array by `id`
            {'$set': {'problems.$': new_problem}}  # Update the matched problem
        )

        if result.modified_count > 0:
            return JsonResponse({'message': 'Problem modified successfully!'}, status=200)
        else:
            return JsonResponse({'error': 'Problem not found or not modified'}, status=404)

    except Exception as e:
        print("Error modifying problem:", str(e))
        traceback.print_exc()
        return JsonResponse({'error': 'Failed to modify problem data'}, status=500)


def delete_problem_data(problem_id):
    """
    Deletes a problem from `Coding_Questions_Library` based on its ID within the `problems` array.
    """
    try:
        # Use `$pull` to remove the specific problem from the `problems` array
        result = questions_collection.update_one(
            {},  # Assuming there's only one document; otherwise, specify a filter if needed
            {'$pull': {'problems': {'id': problem_id}}}
        )

        if result.modified_count > 0:
            return JsonResponse({'message': 'Problem deleted successfully!'}, status=200)
        else:
            return JsonResponse({'error': 'Problem not found for deletion'}, status=404)

    except Exception as e:
        print("Error deleting problem:", str(e))
        traceback.print_exc()
        return JsonResponse({'error': 'Failed to delete problem data'}, status=500)


@csrf_exempt
def save_problem(request):
    """
    Handles saving, modifying, and deleting problems in `Coding_Questions_Library`.
    """
    if request.method == 'GET':
        return fetch_Questions(request)

    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            new_problem = data.get("problems", [])[0]
            return save_problem_data(new_problem)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            print("An error occurred:", str(e))
            traceback.print_exc()
            return JsonResponse({'error': str(e)}, status=500)

    elif request.method == 'PUT':
        try:
            data = json.loads(request.body)
            new_problem = data.get("problems", [])[0]
            return modify_problem_data(new_problem)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            print("An error occurred:", str(e))
            traceback.print_exc()
            return JsonResponse({'error': str(e)}, status=500)

    elif request.method == 'DELETE':
        try:
            print("entered")
            data = json.loads(request.body)
            problem_id = data.get("id")
            print(problem_id)
            return delete_problem_data(problem_id)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            print("An error occurred:", str(e))
            traceback.print_exc()
            return JsonResponse({'error': str(e)}, status=500)

    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)
@csrf_exempt
def upload_bulk_coding_questions(request):
    if request.method == "POST":
        try:
            # Check if file exists in request
            uploaded_file = request.FILES.get("file")
            if not uploaded_file:
                return JsonResponse({"error": "No file uploaded."}, status=400)

            # Read file content
            file_content = uploaded_file.read().decode("utf-8")
            
            # Parse JSON
            data = json.loads(file_content)
            if not isinstance(data, list):  # Expecting a list of coding questions
                return JsonResponse({"error": "Invalid JSON format. Expected an array."}, status=400)

            # Insert data into MongoDB
            result = questions_collection.insert_many(data)
            return JsonResponse({"message": f"Successfully uploaded {len(result.inserted_ids)} coding questions."})

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON file."}, status=400)
        except Exception as e:
            return JsonResponse({"error": f"An error occurred: {str(e)}"}, status=500)

    return JsonResponse({"error": "Invalid request method."}, status=405)

@csrf_exempt
def fetch_coding_questions(request):
    try:
        # Fetch all coding questions from MongoDB
        questions = list(questions_collection.find({}, {"_id": 0}))  # Exclude MongoDB ObjectId from response
        
        # Return questions as JSON
        return JsonResponse({"questions": questions}, safe=False)

    except Exception as e:
        return JsonResponse({"error": f"An error occurred: {str(e)}"}, status=500)