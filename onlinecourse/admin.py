from django.contrib import admin
from .models import Course, Lesson, Instructor, Learner, Question, Choice

# <HINT> Register QuestionInline and ChoiceInline classes here
class QuestionInline(admin.TabularInline):
    model = Question

class ChoiceInline(admin.StackedInline):
    model = Choice
    # Make up to 4 choices available
    extra = 4

class LessonInline(admin.StackedInline):
    model = Lesson
    extra = 5


# Register your models here.
class CourseAdmin(admin.ModelAdmin):
    inlines = [LessonInline]
    list_display = ('name', 'pub_date')
    list_filter = ['pub_date']
    search_fields = ['name', 'description']


class LessonAdmin(admin.ModelAdmin):
    list_display = ['title']


# <HINT> Register Question and Choice models here
class QuestionAdmin(admin.ModelAdmin):
    inlines = [QuestionInline, ChoiceInline]
    list_display = ('question')

admin.site.register(Course, CourseAdmin)
admin.site.register(Lesson, LessonAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Instructor)
admin.site.register(Learner)
