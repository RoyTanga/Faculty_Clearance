from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from .views import UploadDocumentView

urlpatterns = [
    path('classify/', views.classify_clearance, name='classify_clearance'),
    path('faculty/signup/', views.faculty_signup, name='faculty_signup'),
    path('super/signup/', views.admin_signup, name='admin_signup'),
    path('login/', views.custom_login, name='login'),
    path('faculty_dashboard/', views.faculty_dashboard, name='faculty_dashboard'),
    path('super/dashboard/', views.admin_dashboard, name='super_dashboard'),
    path('upload/', UploadDocumentView.as_view(), name='upload_document'),
    path('predict/<int:set_id>/', views.predict_clearances, name='predict_clearances'),
    path('logout/', views.custom_logout, name='logout'),
    path('document/<int:pk>/', views.document_detail, name='document_detail'),
    path('create_new_clearance_set/', views.create_new_clearance_set, name='create_new_clearance_set'),
    path('create-new-set/', views.create_new_set, name='create_new_set'),
    path('upload-document/<int:set_id>/<str:clearance_type>/', views.upload_document, name='upload_document'),
    path('predict-all/', views.predict_all, name='predict_all'),
]
