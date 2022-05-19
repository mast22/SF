from django.middleware.common import CommonMiddleware


class OTPAppendSlashWorkAroundCommonMiddleware(CommonMiddleware):
    def should_redirect_with_slash(self, request):
        """ Не добавляем "/" для коллбеков ОТП, потому что Алексей дал им неправильный адрес """
        if request.path_info.endswith('receive-credit-decision') or request.path_info.endswith(
                'control-result-agreement'):
            return False
        super(OTPAppendSlashWorkAroundCommonMiddleware, self).should_redirect_with_slash(request)
