# filename: elon_musk_tax_estimation.py

def calculate_capital_gains_tax(stock_sales, purchase_price, sell_price, tax_rate):
    """
    Calculate capital gains tax based on stock sales.
    
    :param stock_sales: Number of shares sold
    :param purchase_price: Price per share when purchased (strike price for options)
    :param sell_price: Selling price per share
    :param tax_rate: Capital gains tax rate (use long-term or short-term as applicable)
    :return: Total capital gains tax liability
    """
    gains = (sell_price - purchase_price) * stock_sales
    tax_liability = gains * tax_rate
    return tax_liability

def calculate_social_security_tax(income, max_income_cap, ss_tax_rate):
    """
    Calculate Social Security tax.
    
    :param income: Total income subjected to Social Security tax
    :param max_income_cap: Maximum income cap for Social Security
    :param ss_tax_rate: Social Security tax rate
    :return: Social Security tax liability
    """
    income_capped = min(income, max_income_cap)
    return income_capped * ss_tax_rate

def calculate_total_tax(stock_sales, purchase_price, sell_price, capital_gains_rate, income, max_income_cap, ss_tax_rate):
    """
    Calculate total tax obligations.
    
    :param stock_sales: Number of shares sold
    :param purchase_price: Price per share when purchased
    :param sell_price: Selling price per share
    :param capital_gains_rate: Capital gains tax rate
    :param income: Total income for the year
    :param max_income_cap: Maximum income cap for Social Security
    :param ss_tax_rate: Social Security tax rate
    :return: Total estimated tax liability
    """
    capital_gains_tax = calculate_capital_gains_tax(stock_sales, purchase_price, sell_price, capital_gains_rate)
    social_security_tax = calculate_social_security_tax(income, max_income_cap, ss_tax_rate)
    total_tax = capital_gains_tax + social_security_tax
    return total_tax

# Example usage:

# Set parameters (These would typically come from data collected on stock sales, tax rates, etc.)
stock_sales = 16000000  # Number of Tesla shares sold
purchase_price = 6.24  # Strike price per share (example)
sell_price = 1000  # Realistic selling price per share (example)
capital_gains_rate = 0.20  # Long-term capital gains tax rate (20%)
income = 280000000  # Estimated income for the year (example)
max_income_cap = 147000  # Social Security max income cap for 2021; update as needed
ss_tax_rate = 0.062  # Social Security rate (6.2%)

# Estimate total tax
estimated_tax = calculate_total_tax(stock_sales, purchase_price, sell_price, capital_gains_rate, income, max_income_cap, ss_tax_rate)
print(f"Estimated Total Tax Liability: ${estimated_tax:,.2f}")
