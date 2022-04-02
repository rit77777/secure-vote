from django.urls import path

from . import views

urlpatterns = [
    path('new_transaction/', views.new_transactions, name="new_transactions"),
    path('chain/', views.get_chain, name="get_chain"),
    path('mine_block/', views.mine_block, name="mine_block"),
    path('register_node/', views.register_new_peers, name="register_new_peers"),
    path('register_with/', views.register_with_existing_node, name="register_with_existing_node"),
    path('add_block/', views.verify_and_add_block, name='verify_and_add_block'),
    path('pending_tx/', views.pending_transactions, name='pending_transactions'),
    path('chain_validity/', views.check_if_chain_tampered, name='check_if_chain_tampered'),
]