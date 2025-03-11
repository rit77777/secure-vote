from django.urls import path

from . import views

urlpatterns = [
    path('new_transaction/', views.TransactionView.as_view(), name="new_transaction"),
    path('chain/', views.ChainView.as_view(), name="chain"),
    path('mine_block/', views.MineBlockView.as_view(), name="mine_block"),
    path('register_node/', views.RegisterNodeView.as_view(), name="register_node"),
    path('register_with/', views.RegisterWithNodeView.as_view(), name="register_with"),
    path('add_block/', views.AddBlockView.as_view(), name='add_block'),
    path('pending_transactions/', views.PendingTransactionsView.as_view(), name='pending_transactions'),
    path('chain_validity/', views.ChainValidityView.as_view(), name='chain_validity'),
    path('reset_blockchain/', views.ResetBlockchainView.as_view(), name='reset_blockchain'),
    path('tamper_block/', views.TamperBlockView.as_view(), name='tamper_block'),
    path('sync_with_honest_nodes/', views.SyncWithNodesView.as_view(), name='sync_with_nodes'),
]