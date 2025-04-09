# data_fetching.py
import yfinance as yf
import streamlit as st
import requests

funds = {
    "iShares MSCI World ETF": {
        "ticker": "URTH",
        "type": "Equity",
        "description": "Global developed markets equity exposure."
    },
    "SPDR S&P 500 ETF Trust": {
        "ticker": "SPY",
        "type": "Equity",
        "description": "Large-cap US equity exposure."
    },
    "iShares Euro Govt Bond 10-25yr UCITS ETF": {
        "ticker": "IEGA.DE",
        "type": "Bond",
        "description": "Eurozone government bonds with 10-25 years maturity."
    },
    "Vanguard FTSE All-World UCITS ETF": {
        "ticker": "VWRD.L",
        "type": "Equity",
        "description": "Global diversified equity exposure."
    },
    "Xtrackers MSCI Emerging Markets UCITS ETF": {
        "ticker": "XMME.DE",
        "type": "Equity",
        "description": "Emerging markets equity exposure."
    },
}

def fetch_logo():
    logo_url = "https://raw.githubusercontent.com/softdatahardtruth/prototyp_unit_linked/main/allianz-logo.svg"
    response = requests.get(logo_url)
    if response.status_code == 200:
        svg_content = response.text
        st.markdown(f'<div style="text-align: center; margin-bottom: 20px;">{svg_content}</div>', unsafe_allow_html=True)

def display_fund_details(selected_funds, allocations):
    st.subheader("Fund Details")
    cols = st.columns(len(selected_funds))
    for idx, fund in enumerate(selected_funds):
        details = funds[fund]
        with cols[idx]:
            st.markdown(f"**{fund}**")
            st.markdown(f"- **Ticker:** {details['ticker']}")
            st.markdown(f"- **Type:** {details['type']}")
            st.markdown(f"- {details['description']}")

    if sum(allocations.values()) > 0:
        st.markdown("### Allocation Overview")
        labels = [fund for fund in selected_funds if allocations[fund] > 0]
        sizes = [allocations[fund] for fund in selected_funds if allocations[fund] > 0]

        fig1, ax1 = plt.subplots(figsize=(4, 4))
        ax1.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
        ax1.axis('equal')
        st.pyplot(fig1)

def fetch_fund_data(selected_funds):
    fund_data = {}
    for fund in selected_funds:
        ticker = funds[fund]["ticker"]
        data = yf.download(ticker, period="5y", interval="1mo").dropna()
        fund_data[fund] = data
    return fund_data
