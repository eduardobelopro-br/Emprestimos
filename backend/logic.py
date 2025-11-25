def calculate_monthly_discount_rate(monthly_payment: float, prepayment_value: float) -> float:
    """
    Calculates the monthly discount percentage when prepaying a loan installment.
    Formula: (Monthly Payment - Prepayment Value) / Prepayment Value * 100
    """
    if prepayment_value <= 0:
        return 0.0
    return ((monthly_payment - prepayment_value) / prepayment_value) * 100

def calculate_cdb_monthly_return(cdi_rate: float) -> float:
    """
    Calculates the approximate monthly return of a CDB paying 105% of CDI.
    Formula: (CDI Rate * 1.05) / 12
    """
    return (cdi_rate * 1.05) / 12

def get_recommendation(discount_rate: float, cdb_return: float) -> str:
    """
    Returns a recommendation based on the comparison between discount rate and CDB return.
    """
    if discount_rate > cdb_return:
        return "Adiantar"
    else:
        return "Investir"
