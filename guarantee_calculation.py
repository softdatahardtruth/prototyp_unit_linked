import numpy as np
from scipy.stats import norm
import matplotlib.pyplot as plt

def black_scholes_put(S, K, T, r, sigma):
    """
    Berechnet den Preis einer europäischen Put-Option mit der Black-Scholes-Formel.
    """
    if S <= 0 or K <= 0 or T <= 0 or sigma <= 0:
        return 0.0

    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    put_price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)

    return put_price

def calculate_option_prices(initial_investment, time_horizon, risk_free_rate, volatility, guarantee_levels):
    option_prices = []
    for level in guarantee_levels:
        if level == 0.0:
            option_price = 0.0
        else:
            strike = initial_investment * level
            option_price = black_scholes_put(initial_investment, strike, time_horizon, risk_free_rate, volatility)
        option_prices.append(option_price / initial_investment * 100)  # als Prozentsatz
    return option_prices

def plot_guarantee_vs_cost(guarantee_levels, option_prices):
    plt.figure(figsize=(10, 6))
    plt.plot(guarantee_levels * 100, option_prices, marker='o')
    plt.title('Kosten der Garantie in Abhängigkeit vom Garantieniveau')
    plt.xlabel('Garantieniveau (%)')
    plt.ylabel('Optionskosten (% der Investition)')
    plt.grid(True)
    plt.show()

def plot_sensitivity_volatility(initial_investment, time_horizon, risk_free_rate, guarantee_levels):
    vols = [0.10, 0.15, 0.20, 0.25]
    plt.figure(figsize=(10, 6))
    for vol in vols:
        prices = calculate_option_prices(initial_investment, time_horizon, risk_free_rate, vol, guarantee_levels)
        plt.plot(guarantee_levels * 100, prices, marker='o', label=f'Volatilität: {int(vol * 100)}%')
    plt.title('Sensitivität: Volatilität der Fondsanlage')
    plt.xlabel('Garantieniveau (%)')
    plt.ylabel('Optionskosten (% der Investition)')
    plt.legend()
    plt.grid(True)
    plt.show()

def plot_sensitivity_time(initial_investment, risk_free_rate, volatility, guarantee_levels):
    terms = [10, 20, 30, 40]
    plt.figure(figsize=(10, 6))
    for term in terms:
        prices = calculate_option_prices(initial_investment, term, risk_free_rate, volatility, guarantee_levels)
        plt.plot(guarantee_levels * 100, prices, marker='o', label=f'Laufzeit: {term} Jahre')
    plt.title('Sensitivität: Laufzeit der Versicherung')
    plt.xlabel('Garantieniveau (%)')
    plt.ylabel('Optionskosten (% der Investition)')
    plt.legend()
    plt.grid(True)
    plt.show()
