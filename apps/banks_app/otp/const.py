from apps.orders.const import CreditProductStatus


OTP_SCORING_DECISIONS = {
    '1': CreditProductStatus.SUCCESS,
    '0': CreditProductStatus.REJECTED,
    '3': CreditProductStatus.SUCCESS_VALIDATION_REQUIRED,
    '4': CreditProductStatus.SHORT_APPROVED,
    '5': CreditProductStatus.GOODS_INFO_REQUIRED,
    '-1': CreditProductStatus.TECHNICAL_ERROR,
}
