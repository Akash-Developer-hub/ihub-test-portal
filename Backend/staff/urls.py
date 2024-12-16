from django.urls import path
from .views import staff_login, staff_signup  # Replace with actual imports if necessary
from .assessment import create_assessment
from .Mcq_question import bulk_upload, upload_single_question, fetch_all_questions

urlpatterns = [
    # Authentication
    path("login/", staff_login, name="staff_login"),
    path("signup/", staff_signup, name="staff_signup"),

    # Assessment API
    path('api/create-assessment/', create_assessment, name='create_assessment'),

    #mcq
    path("api/mcq-bulk-upload/", bulk_upload, name="mcq_bulk_upload"),
    path("api/upload-single-question/", upload_single_question, name="upload_single_question"),
    path("api/fetch-all-questions/", fetch_all_questions, name="fetch_all_questions"),


]

