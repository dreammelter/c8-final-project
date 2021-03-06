from django.shortcuts import render
from django.http import HttpResponseRedirect
# <HINT> Import any new Models here
from .models import Course, Enrollment, Question, Choice, Submission
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views import generic
from django.contrib.auth import login, logout, authenticate
import logging
# Get an instance of a logger
logger = logging.getLogger(__name__)
# Create your views here.


def registration_request(request):
    context = {}
    if request.method == 'GET':
        return render(request, 'onlinecourse/user_registration_bootstrap.html', context)
    elif request.method == 'POST':
        # Check if user exists
        username = request.POST['username']
        password = request.POST['psw']
        first_name = request.POST['firstname']
        last_name = request.POST['lastname']
        user_exist = False
        try:
            User.objects.get(username=username)
            user_exist = True
        except:
            logger.error("New user")
        if not user_exist:
            user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name,
                                            password=password)
            login(request, user)
            return redirect("onlinecourse:index")
        else:
            context['message'] = "User already exists."
            return render(request, 'onlinecourse/user_registration_bootstrap.html', context)


def login_request(request):
    context = {}
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['psw']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('onlinecourse:index')
        else:
            context['message'] = "Invalid username or password."
            return render(request, 'onlinecourse/user_login_bootstrap.html', context)
    else:
        return render(request, 'onlinecourse/user_login_bootstrap.html', context)


def logout_request(request):
    logout(request)
    return redirect('onlinecourse:index')


def check_if_enrolled(user, course):
    is_enrolled = False
    if user.id is not None:
        # Check if user enrolled
        num_results = Enrollment.objects.filter(user=user, course=course).count()
        if num_results > 0:
            is_enrolled = True
    return is_enrolled


# CourseListView
class CourseListView(generic.ListView):
    template_name = 'onlinecourse/course_list_bootstrap.html'
    context_object_name = 'course_list'

    def get_queryset(self):
        user = self.request.user
        courses = Course.objects.order_by('-total_enrollment')[:10]
        for course in courses:
            if user.is_authenticated:
                course.is_enrolled = check_if_enrolled(user, course)
        return courses


class CourseDetailView(generic.DetailView):
    model = Course
    template_name = 'onlinecourse/course_detail_bootstrap.html'


def enroll(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    user = request.user

    is_enrolled = check_if_enrolled(user, course)
    if not is_enrolled and user.is_authenticated:
        # Create an enrollment
        Enrollment.objects.create(user=user, course=course, mode='honor')
        course.total_enrollment += 1
        course.save()

    return HttpResponseRedirect( reverse(viewname='onlinecourse:course_details', args=(course.id,)) )


# <HINT> A example method to collect the selected choices from the exam form from the request object
def extract_answers(request):
    submitted_answers = []
    for key in request.POST:
        if key.startswith('choice'):
            value = request.POST[key]
            choice_id = int(value)
            submitted_answers.append(choice_id)
    return submitted_answers


# <HINT> Create a submit view to create an exam submission record for a course enrollment,
def submit(request, course_id):
    # Get user and course, then the enrollment obj from when they joined course
    course = get_object_or_404(Course, pk=course_id)
    user = request.user
    enrollment_obj = Enrollment.objects.filter(user=user, course=course).get() #filter then get the object..

    #Create Submission obj referring to enrollment
    submission = Submission.objects.create(enrollment_id=enrollment_obj.id) #send ID over instead

    #Collect the list of choices from the exam form
    choices = extract_answers(request)

    #Break out each choice so we can add em to submission the obj
    for choice in choices:
        # get id for each choice in the list (from the Choice Objects)
        c = Choice.objects.filter(id=int(choice)).get() # typecasting to int? for safety i guess (thing says "Any").
        # ...and you know what, I broke the Choices model last time by setting a string for ID earlier.

        # add choice to submission obj using ID
        submission.choices.add(c)

    #Save the changes to submission
    submission.save()

    #redirect to 'show_exam_result'
    ## reverse() is used to avoid hardcoding a URL and can instead use the namespaced viewname
    # ...submission ID is sent over as additional argument in the redirect
    # ...alongside course ID cuz the show_exam_result view is gonna look for that too
    return HttpResponseRedirect( reverse(viewname="onlinecourse:show_exam_result", args=(course.id, submission.id)) )


# <HINT> Create an exam result view to check if learner passed exam and show their question results and result for each question,
def show_exam_result(request, course_id, submission_id):
    # Apparently we're sending all this to a context later so..
    context = {}

    #Get course + submission with the given IDs
    course = Course.objects.get(id=course_id)
    submission = Submission.objects.get(id=submission_id)

    # We're gonna grade these so put gather up the choices from the submission
    to_grade = submission.choices.all() # note to self: this is a set/list cuz ManyToMany
    score = 0 # to keep track

    # The spec shared with us wants to show which answers were right/wrong
    # so we need to know what was selected. Grab from Submissions object
    selections = Submission.objects.filter(id=submission_id).values_list('choices', flat=True)
    # values_list() returns tuples, but if you enable 'flat', it just sends a nice list of singular values
    # ref https://stackoverflow.com/questions/37205793/django-values-list-vs-values

    # and now we grade - with reference to the question a choice belongs to: it holds the grading scale
    # check just for the stuff that's right by filtering for "is_correct"
    for i in to_grade.filter(is_correct=True).values_list('questions_id'):
        # up the score with the amount set for the grade in the Question Obj.
        score += Question.objects.filter(id=i[0]).first().grade

    # finally send off everything in a context bundle for use in the template
    context['course'] = course #why was I sending the ID and not the object over again??
    context['selections'] = selections
    context['grade'] = score

    # render the context
    return render(request, 'onlinecourse/exam_result_bootstrap.html', context)


