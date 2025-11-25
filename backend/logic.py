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

def calculate_remaining_installments(start_date, total_installments: int, monthly_due_day: int, current_date) -> int:
    """
    Calculate how many installments remain based on dates.
    
    Args:
        start_date: datetime - when the loan started
        total_installments: int - total number of installments
        monthly_due_day: int - day of month payment is due (1-31)
        current_date: datetime - current date for calculation
    
    Returns:
        int - number of remaining installments
    """
    # Calculate months elapsed
    months_elapsed = (current_date.year - start_date.year) * 12 + (current_date.month - start_date.month)
    
    # Adjust based on day of month
    if current_date.day >= monthly_due_day:
        months_elapsed += 1
    
    # Calculate remaining
    remaining = total_installments - months_elapsed
    
    # Ensure we don't return negative values
    return max(0, remaining)
