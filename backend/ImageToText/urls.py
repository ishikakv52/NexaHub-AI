from django.urls import path
from .views import ImageToTextView

urlpatterns = [

    path(
        'extract-text/',
        ImageToTextView.as_view(),
        name='extract-text'
    ),

]