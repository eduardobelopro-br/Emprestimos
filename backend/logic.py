def calculate_monthly_discount_rate(valor_parcela: float, valor_parcela_adiantada: float) -> float:
    """
    Calculates the monthly discount percentage when prepaying.
    Formula: (Normal Payment - Prepayment Value) / Prepayment Value * 100
    """
    if valor_parcela_adiantada == 0:
        return 0
    return ((valor_parcela - valor_parcela_adiantada) / valor_parcela_adiantada) * 100

def calculate_cdb_monthly_return(taxa_cdi: float) -> float:
    """
    Calculates the monthly return of investing in CDB at 105% of CDI.
    Formula: (CDI * 1.05) / 12
    """
    return (taxa_cdi * 1.05) / 12

def get_recommendation(discount_rate: float, cdb_return: float) -> str:
    """
    Returns a recommendation based on the comparison between discount rate and CDB return.
    """
    if discount_rate > cdb_return:
        return "Adiantar"
    else:
        return "Investir"

def calculate_remaining_installments(data_cadastro, qtd_total_parcelas: int, dia_vencimento: int, current_date) -> int:
    """
    Calculate how many installments remain based on dates.
    
    Args:
        data_cadastro: datetime - when the loan started
        qtd_total_parcelas: int - total number of installments
        dia_vencimento: int - day of month payment is due (1-31)
        current_date: datetime - current date for calculation
    
    Returns:
        int - number of remaining installments
    """
    # Calculate months elapsed
    months_elapsed = (current_date.year - data_cadastro.year) * 12 + (current_date.month - data_cadastro.month)
    
    # Adjust based on day of month
    if current_date.day >= dia_vencimento:
        months_elapsed += 1
    
    # Calculate remaining
    remaining = qtd_total_parcelas - months_elapsed
    
    # Ensure we don't return negative values
    return max(0, remaining)
