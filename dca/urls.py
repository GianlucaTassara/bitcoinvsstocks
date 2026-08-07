from django.urls import path

from . import views

app_name = "dca"

urlpatterns = [path("", views.get_DCA_data, name="get_DCA_data")]
