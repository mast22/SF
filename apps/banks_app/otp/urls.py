from django.urls import path
from .updaters.receive_credit_decision import callback_receive_credit_decision
from .updaters.control_result_agreement import callback_control_result_agreement


app_name = 'otp'
urlpatterns = [
    path('receive-credit-decision', callback_receive_credit_decision, name='receive-credit-decision'),
    path('control-result-agreement', callback_control_result_agreement, name='control-result-agreement'),
]
