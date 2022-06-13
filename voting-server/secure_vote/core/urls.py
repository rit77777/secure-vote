from django.urls import path

from . import views

urlpatterns = [
    #------------------------Registration------------------------#
    path('login/', views.login_page, name="login"),
    path('login_otp/', views.login_otp, name="login_otp"),
    path('logout/', views.logout_page, name="logout"),
    path('register/', views.register_page, name="register"),
    path('register_otp/', views.register_otp, name="register_otp"),
    
    #------------------------Voting------------------------#
    path('', views.home, name='home'),
    path('success/', views.success, name='success'),
    path('mine_success/', views.mine_success, name='mine_success'),
    path('mine/', views.mine, name='mine'),
    path('voting/', views.voting, name='voting'),
    path('all_votes/', views.all_votes, name='all_votes'),
    path('submit/', views.submit, name='submit'),
    path('count_votes/', views.count_votes, name='count_votes'),
    path('chart_votes/', views.chart_votes, name='chart_votes'),
    path('register_node/', views.register_node, name='register_node'),
    path('sync_with_honest_nodes/', views.sync_with_honest_nodes, name='sync_with_honest_nodes'),
]