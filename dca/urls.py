from django.urls import path, include
from . import views

app_name = 'dca'

urlpatterns = [
    path('', views.get_DCA_data, name='get_DCA_data')
]