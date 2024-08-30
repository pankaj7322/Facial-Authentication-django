from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path('Login.html', views.Login, name="Login"),
    path('Signup', views.Signup, name="Signup"),
    path("WebCam", views.WebCam, name="WebCam"),
    path('UserLogin', views.UserLogin, name="UserLogin"),
    path("saveSignup", views.saveSignup, name="saveSignup"),
    path('Admin.html', views.Admin, name="Admin"), 
    path("CastVote.html", views.CastVote, name="CastVote"),
    path('Register.html', views.Register, name="Register"),
    path("ValidateUser", views.ValidateUser, name="ValidateUser"),
]