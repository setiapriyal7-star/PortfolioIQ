
# ============================================================
# PORTFOLIOIQ
# Personalised Portfolio Risk Intelligence Dashboard
# ============================================================

# 1. IMPORT LIBRARIES
import os
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# 2. PAGE CONFIGURATION
st.set_page_config(
    page_title="PortfolioIQ | Portfolio Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 3. DESIGN AND STYLING
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
    }

    .stApp {
        background: #080F1C;
        color: #EDF3FC;
    }

    [data-testid="stSidebar"] {
        background: #101B2D;
        border-right: 1px solid #24334A;
    }

    .hero {
        background: linear-gradient(120deg, #14243A, #123D48);
        padding: 30px;
        border: 1px solid #2D5360;
        border-radius: 18px;
        margin-bottom: 22px;
    }

    .hero h1 {
        font-family: 'Manrope', sans-serif;
        font-size: 36px;
        font-weight: 800;
        color: #F4F8FF;
        margin-bottom: 4px;
    }

    .hero p {
        color: #B7CBD9;
        font-size: 14px;
        margin-bottom: 0;
    }

    .eyebrow {
        color: #63D9C1;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 2px;
    }

    .profile-card {
        background: #12263A;
        border: 1px solid #285064;
        border-radius: 14px;
        padding: 20px;
        margin: 12px 0 20px 0;
    }

    .profile-label {
        color: #77CFC2;
        font-size: 11px;
        letter-spacing: 1.5px;
        font-weight: 700;
    }

    .profile-value {
        font-size: 23px;
        font-weight: 700;
        color: #FFFFFF;
        margin-top: 5px;
    }

    .small-note {
        color: #9DAFC3;
        font-size: 12px;
    }

    [data-testid="stMetric"] {
        background: #111E30;
        border: 1px solid #263950;
        padding: 16px;
        border-radius: 13px;
    }

    [data-testid="stMetricLabel"] {
        color: #AFC1D4;
    }

    [data-testid="stMetricValue"] {
        color: #F4F7FC;
    }

    h1, h2, h3 {
        font-family: 'Manrope', sans-serif;
    }

    div[data-testid="stTabs"] button {
        color: #B8C8D9;
        font-weight: 600;
    }

    div[data-testid="stTabs"] button[aria-selected="true"] {
        color: #63D9C1;
    }

    .stButton button, .stDownloadButton button {
        border-radius: 9px;
    }

    hr {
        border-color: #28384D;
    }
</style>
""", unsafe_allow_html=True)


# 4. PROJECT SETTINGS AND STOCK INFORMATION
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

STOCK_FILES = {
    "Reliance Industries": "Reliance.csv",
    "TCS": "TCS.csv",
    "HDFC Bank": "HDFC_Bank.csv",
    "ITC": "ITC.csv",
    "Larsen & Toubro": "LT.csv"
}

DEFAULT_ALLOCATIONS = {
    "Reliance Industries": 30000,
    "TCS": 25000,
    "HDFC Bank": 20000,
    "ITC": 15000,
    "Larsen & Toubro": 10000
}


# 5. LOAD AND PREPARE HISTORICAL DATA
@st.cache_data
def load_market_data():

    stock_data = {}

    for stock, filename in STOCK_FILES.items():

        filepath = os.path.join(DATA_DIR, filename)

        if not os.path.exists(filepath):
            raise FileNotFoundError(
                f"Missing dataset: {filename}"
            )

        df = pd.read_csv(filepath)

        df["Date"] = pd.to_datetime(df["Date"])
        df = df.sort_values("Date")
        df = df.drop_duplicates(subset="Date")
        df = df.set_index("Date")

        stock_data[stock] = pd.to_numeric(
            df["Close"], errors="coerce"
        )

    prices = pd.concat(stock_data, axis=1)

    benchmark_path = os.path.join(DATA_DIR, "Nifty50.csv")

    if not os.path.exists(benchmark_path):
        raise FileNotFoundError("Missing Nifty50.csv")

    benchmark_df = pd.read_csv(benchmark_path)
    benchmark_df["Date"] = pd.to_datetime(
        benchmark_df["Date"]
    )
    benchmark_df = benchmark_df.sort_values("Date")
    benchmark_df = benchmark_df.drop_duplicates(
        subset="Date"
    )
    benchmark_df = benchmark_df.set_index("Date")

    benchmark = pd.to_numeric(
        benchmark_df["Close"], errors="coerce"
    )

    prices["Nifty 50"] = benchmark

    prices = prices.sort_index()
    prices = prices.replace([np.inf, -np.inf], np.nan)
    prices = prices.dropna()

    return prices


# 6. SIDEBAR: PERSONAL INVESTOR INPUTS
st.sidebar.markdown("## ◈ PORTFOLIOIQ")
st.sidebar.caption("PERSONAL PORTFOLIO INTELLIGENCE")
st.sidebar.divider()

st.sidebar.markdown("### Your investor profile")

investor_name = st.sidebar.text_input(
    "Your name",
    value="Investor",
    max_chars=40
)

experience = st.sidebar.selectbox(
    "Investment experience",
    ["Beginner", "Intermediate", "Experienced"]
)

risk_profile = st.sidebar.selectbox(
    "Risk appetite",
    ["Conservative", "Moderate", "Aggressive"]
)

horizon = st.sidebar.selectbox(
    "Investment horizon",
    ["Less than 1 year", "1–3 years", "3–5 years", "5+ years"]
)

risk_free_rate = st.sidebar.slider(
    "Annual risk-free rate (%)",
    min_value=0.0,
    max_value=12.0,
    value=6.5,
    step=0.5
)

st.sidebar.divider()
st.sidebar.markdown("### Build your portfolio")

selected_stocks = st.sidebar.multiselect(
    "Select your stocks",
    options=list(STOCK_FILES.keys()),
    default=list(STOCK_FILES.keys())
)

if not selected_stocks:
    st.warning("Please select at least one stock to continue.")
    st.stop()

investments = {}

for stock in selected_stocks:

    investments[stock] = st.sidebar.number_input(
        f"{stock} (₹)",
        min_value=1000,
        max_value=100000000,
        value=DEFAULT_ALLOCATIONS[stock],
        step=1000,
        key=f"amount_{stock}"
    )

total_investment = sum(investments.values())

st.sidebar.divider()

st.sidebar.metric(
    "Total portfolio investment",
    f"₹{total_investment:,.0f}"
)

st.sidebar.caption(
    "Your inputs are used to personalise this analysis. "
    "They are not stored as a user account."
)


# 7. LOAD DATA AND PERFORM VALIDATION
try:
    all_prices = load_market_data()

except Exception as error:
    st.error(f"Unable to load market data: {error}")
    st.stop()

if total_investment <= 0:
    st.error("Your total investment must be greater than zero.")
    st.stop()

available_columns = selected_stocks + ["Nifty 50"]

prices = all_prices[available_columns].dropna()

if len(prices) < 30:
    st.error("Not enough historical observations for reliable analysis.")
    st.stop()


# 8. FINANCIAL CALCULATIONS
daily_returns = prices.pct_change().dropna()

weights = pd.Series(investments, dtype=float) / total_investment

portfolio_returns = (
    daily_returns[selected_stocks]
    .mul(weights, axis=1)
    .sum(axis=1)
)

benchmark_returns = daily_returns["Nifty 50"]

portfolio_index = (1 + portfolio_returns).cumprod() * 100
benchmark_index = (1 + benchmark_returns).cumprod() * 100

number_of_days = len(portfolio_returns)

total_return = portfolio_index.iloc[-1] / 100 - 1

annual_return = (
    (1 + total_return) ** (252 / number_of_days) - 1
)

annual_volatility = (
    portfolio_returns.std() * np.sqrt(252)
)

benchmark_volatility = (
    benchmark_returns.std() * np.sqrt(252)
)

daily_risk_free = (
    (1 + risk_free_rate / 100) ** (1 / 252) - 1
)

excess_daily_return = portfolio_returns - daily_risk_free

sharpe_ratio = (
    excess_daily_return.mean() / portfolio_returns.std()
) * np.sqrt(252) if portfolio_returns.std() != 0 else 0

benchmark_variance = benchmark_returns.var()

beta = (
    portfolio_returns.cov(benchmark_returns) /
    benchmark_variance
) if benchmark_variance != 0 else 0

running_peak = portfolio_index.cummax()

drawdown = portfolio_index / running_peak - 1

maximum_drawdown = drawdown.min()

daily_var_95 = -portfolio_returns.quantile(0.05)

downside_returns = np.minimum(portfolio_returns, 0)

downside_deviation = (
    np.sqrt(np.mean(downside_returns ** 2)) * np.sqrt(252)
)

sortino_ratio = (
    (annual_return - risk_free_rate / 100) /
    downside_deviation
) if downside_deviation != 0 else 0

stock_betas = {}

for stock in selected_stocks:

    stock_betas[stock] = (
        daily_returns[stock].cov(benchmark_returns) /
        benchmark_variance
    ) if benchmark_variance != 0 else 0

correlation = daily_returns[selected_stocks].corr()

largest_weight = weights.max()
largest_stock = weights.idxmax()

portfolio_value_index = total_investment * portfolio_index / 100

latest_value = portfolio_value_index.iloc[-1]


# 9. PERSONALIZED RISK DIAGNOSTICS
if annual_volatility * 100 <= 15:
    measured_risk = "Lower historical volatility"
elif annual_volatility * 100 <= 25:
    measured_risk = "Moderate historical volatility"
else:
    measured_risk = "Higher historical volatility"

risk_thresholds = {
    "Conservative": 15,
    "Moderate": 25,
    "Aggressive": 40
}

personalised_observations = []

if annual_volatility * 100 > risk_thresholds[risk_profile]:

    personalised_observations.append(
        "Your portfolio's historical volatility is above "
        "the indicative level used for your selected risk profile."
    )

else:

    personalised_observations.append(
        "Your historical volatility is within the indicative "
        "range used for your selected risk profile."
    )

if largest_weight > 0.40:

    personalised_observations.append(
        f"{largest_stock} represents {largest_weight:.1%} "
        "of your portfolio. This creates concentration risk."
    )

if len(selected_stocks) < 3:

    personalised_observations.append(
        "Your portfolio contains fewer than three selected "
        "stocks, so diversification across this stock universe is limited."
    )

if beta > 1.2:

    personalised_observations.append(
        "Your portfolio has relatively high sensitivity "
        "to movements in the Nifty 50."
    )

if maximum_drawdown < -0.20:

    personalised_observations.append(
        "The historical analysis includes a drawdown exceeding 20%. "
        "Consider whether you can tolerate similar losses."
    )

if horizon == "Less than 1 year" and annual_volatility * 100 > 15:

    personalised_observations.append(
        "Your short investment horizon may make large market "
        "fluctuations particularly important to consider."
    )


# 10. DASHBOARD HEADER
st.markdown("""
<div class="hero">
    <div class="eyebrow">INVESTMENT INTELLIGENCE • INDIA</div>
    <h1>PORTFOLIOIQ</h1>
    <p>Understand your portfolio. Measure your risk. Make informed decisions.</p>
</div>
""", unsafe_allow_html=True)

st.markdown(
    f"""
    <div class="profile-card">
        <div class="profile-label">YOUR PERSONAL INVESTMENT DASHBOARD</div>
        <div class="profile-value">Welcome, {investor_name}.</div>
        <div class="small-note">
            {risk_profile} investor &nbsp; • &nbsp;
            {experience} experience &nbsp; • &nbsp;
            Horizon: {horizon}
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

st.caption(
    f"Analysis period: {prices.index.min().date()} to "
    f"{prices.index.max().date()} | "
    f"{len(prices):,} aligned trading observations"
)


# 11. DASHBOARD TABS
tab_overview, tab_risk, tab_stress, tab_method = st.tabs([
    "◈ Portfolio Overview",
    "◆ Risk Intelligence",
    "⚡ Stress Simulator",
    "ⓘ Methodology"
])


# ============================================================
# TAB 1: PORTFOLIO OVERVIEW
# ============================================================

with tab_overview:

    st.markdown("### Your portfolio at a glance")

    metric1, metric2, metric3, metric4 = st.columns(4)

    metric1.metric(
        "Total invested",
        f"₹{total_investment:,.0f}"
    )

    metric2.metric(
        "Historical portfolio return",
        f"{total_return * 100:.2f}%"
    )

    metric3.metric(
        "Annualised return",
        f"{annual_return * 100:.2f}%"
    )

    metric4.metric(
        "Historical annual volatility",
        f"{annual_volatility * 100:.2f}%"
    )

    st.markdown("### Portfolio performance")

    performance = pd.DataFrame({
        "PortfolioIQ": portfolio_index,
        "Nifty 50": benchmark_index
    })

    fig_performance = px.line(
        performance,
        x=performance.index,
        y=["PortfolioIQ", "Nifty 50"],
        labels={
            "value": "Growth of ₹100",
            "index": "Date",
            "variable": "Investment"
        },
        color_discrete_sequence=["#63D9C1", "#E5B86B"],
        template="plotly_dark"
    )

    fig_performance.update_layout(
        height=420,
        paper_bgcolor="#080F1C",
        plot_bgcolor="#111E30",
        legend_title_text=""
    )

    st.plotly_chart(fig_performance, use_container_width=True)

    left, right = st.columns(2)

    with left:

        st.markdown("### Asset allocation")

        allocation_df = pd.DataFrame({
            "Stock": selected_stocks,
            "Investment": [investments[s] for s in selected_stocks]
        })

        fig_pie = px.pie(
            allocation_df,
            names="Stock",
            values="Investment",
            hole=0.68,
            template="plotly_dark",
            color_discrete_sequence=[
                "#63D9C1", "#E5B86B", "#7397D4",
                "#A78BFA", "#E58D9A"
            ]
        )

        fig_pie.update_layout(
            height=370,
            paper_bgcolor="#080F1C"
        )

        st.plotly_chart(fig_pie, use_container_width=True)

    with right:

        st.markdown("### Investment breakdown")

        allocation_df["Weight"] = (
            allocation_df["Investment"] / total_investment * 100
        )

        allocation_df["Investment"] = allocation_df[
            "Investment"
        ].apply(lambda x: f"₹{x:,.0f}")

        allocation_df["Weight"] = allocation_df[
            "Weight"
        ].apply(lambda x: f"{x:.2f}%")

        st.dataframe(
            allocation_df,
            use_container_width=True,
            hide_index=True
        )

        st.metric(
            "Latest modelled portfolio value",
            f"₹{latest_value:,.0f}"
        )

        st.caption(
            "Historical model value based on your entered allocation "
            "and the selected historical return series."
        )

    st.markdown("### Investor profile summary")

    st.info(
        f"You selected a {risk_profile.lower()} risk profile "
        f"with a {horizon.lower()} investment horizon. "
        f"Your portfolio currently shows {measured_risk.lower()}."
    )


# ============================================================
# TAB 2: RISK INTELLIGENCE
# ============================================================

with tab_risk:

    st.markdown("### How much risk are you taking?")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Portfolio beta",
        f"{beta:.2f}"
    )

    c2.metric(
        "Maximum drawdown",
        f"{maximum_drawdown * 100:.2f}%"
    )

    c3.metric(
        "Sharpe ratio",
        f"{sharpe_ratio:.2f}"
    )

    c4.metric(
        "Sortino ratio",
        f"{sortino_ratio:.2f}"
    )

    st.markdown("### Portfolio drawdown")

    fig_drawdown = go.Figure()

    fig_drawdown.add_trace(
        go.Scatter(
            x=drawdown.index,
            y=drawdown * 100,
            fill="tozeroy",
            name="Drawdown",
            line=dict(color="#E58D9A", width=2)
        )
    )

    fig_drawdown.update_layout(
        template="plotly_dark",
        height=350,
        paper_bgcolor="#080F1C",
        plot_bgcolor="#111E30",
        yaxis_title="Drawdown (%)"
    )

    st.plotly_chart(fig_drawdown, use_container_width=True)

    left, right = st.columns(2)

    with left:

        st.markdown("### Stock correlation")

        fig_corr = px.imshow(
            correlation,
            text_auto=".2f",
            zmin=-1,
            zmax=1,
            color_continuous_scale="RdYlGn",
            aspect="auto",
            template="plotly_dark"
        )

        fig_corr.update_layout(
            height=420,
            paper_bgcolor="#080F1C"
        )

        st.plotly_chart(fig_corr, use_container_width=True)

    with right:

        st.markdown("### Historical risk contribution indicators")

        beta_df = pd.DataFrame({
            "Stock": selected_stocks,
            "Portfolio weight (%)": [
                weights[s] * 100 for s in selected_stocks
            ],
            "Stock beta": [
                stock_betas[s] for s in selected_stocks
            ]
        })

        beta_df["Portfolio weight (%)"] = beta_df[
            "Portfolio weight (%)"
        ].round(2)

        beta_df["Stock beta"] = beta_df["Stock beta"].round(2)

        st.dataframe(
            beta_df,
            use_container_width=True,
            hide_index=True
        )

        st.markdown("**95% historical daily Value at Risk**")

        st.metric(
            "Estimated daily loss threshold",
            f"{daily_var_95 * 100:.2f}%"
        )

        st.caption(
            "Historical VaR estimates a loss threshold from observed "
            "daily returns. It is not a maximum possible loss."
        )

    st.markdown("### Your personalised portfolio observations")

    for observation in personalised_observations:
        st.warning(observation)

    if not personalised_observations:

        st.success(
            "No major warning was triggered by the selected "
            "diagnostic thresholds. This does not mean the portfolio "
            "is risk-free."
        )


# ============================================================
# TAB 3: MARKET STRESS SIMULATOR
# ============================================================

with tab_stress:

    st.markdown("### What if the market crashes?")

    st.write(
        "Choose a hypothetical fall in the Nifty 50. "
        "PortfolioIQ estimates the impact using the portfolio's "
        "historical beta."
    )

    market_shock = st.slider(
        "Assumed Nifty 50 market decline (%)",
        min_value=5,
        max_value=50,
        value=20,
        step=5
    )

    estimated_portfolio_change = max(
        -0.95,
        beta * (-market_shock / 100)
    )

    estimated_loss = (
        total_investment * estimated_portfolio_change
    )

    estimated_value = total_investment + estimated_loss

    a, b, c = st.columns(3)

    a.metric(
        "Initial investment",
        f"₹{total_investment:,.0f}"
    )

    b.metric(
        "Estimated scenario loss",
        f"₹{abs(estimated_loss):,.0f}"
    )

    c.metric(
        "Estimated scenario value",
        f"₹{estimated_value:,.0f}"
    )

    st.markdown("### Impact by stock")

    scenario_rows = []

    for stock in selected_stocks:

        stock_change = max(
            -0.95,
            stock_betas[stock] * (-market_shock / 100)
        )

        amount = investments[stock]

        impact = amount * stock_change

        scenario_rows.append({
            "Stock": stock,
            "Investment": amount,
            "Estimated change (%)": stock_change * 100,
            "Estimated gain/loss (₹)": impact
        })

    scenario_df = pd.DataFrame(scenario_rows)

    st.dataframe(
        scenario_df.style.format({
            "Investment": "₹{:,.0f}",
            "Estimated change (%)": "{:.2f}%",
            "Estimated gain/loss (₹)": "₹{:,.0f}"
        }),
        use_container_width=True,
        hide_index=True
    )

    st.warning(
        "This is a simplified beta-based hypothetical stress test, "
        "not a market forecast. Actual stock movements may differ "
        "substantially."
    )


# ============================================================
# TAB 4: METHODOLOGY AND DOWNLOADABLE REPORT
# ============================================================

with tab_method:

    st.markdown("### How PortfolioIQ works")

    st.write(
        "PortfolioIQ uses historical adjusted closing prices "
        "to calculate daily returns, portfolio performance and "
        "risk indicators."
    )

    with st.expander("1. Daily stock returns"):

        st.latex(r"R_t = \\frac{P_t-P_{t-1}}{P_{t-1}}")

        st.write(
            "Daily return measures the percentage change in a "
            "stock's adjusted closing price."
        )

    with st.expander("2. Portfolio return"):

        st.latex(r"R_p = \\sum_{i=1}^{n} w_i R_i")

        st.write(
            "Portfolio return is calculated as the weighted sum "
            "of individual stock returns. The model assumes "
            "constant portfolio weights, equivalent to periodic "
            "rebalancing in this simplified analysis."
        )

    with st.expander("3. Annualised volatility"):

        st.latex(r"\\sigma_{annual} = \\sigma_{daily}\\sqrt{252}")

        st.write(
            "Volatility measures the variation in daily returns. "
            "252 is the approximate number of trading days in a year."
        )

    with st.expander("4. Beta"):

        st.latex(
            r"\\beta_p = "
            r"\\frac{Cov(R_p,R_m)}{Var(R_m)}"
        )

        st.write(
            "Beta measures the historical sensitivity of the "
            "portfolio to movements in the Nifty 50."
        )

    with st.expander("5. Maximum drawdown"):

        st.latex(
            r"MDD = \\min\\left(\\frac{V_t}{Peak_t}-1\\right)"
        )

        st.write(
            "Maximum drawdown measures the largest percentage "
            "fall from a previous portfolio peak."
        )

    with st.expander("6. Sharpe ratio and Sortino ratio"):

        st.latex(
            r"Sharpe = \\frac{R_p-R_f}{\\sigma_p}"
        )

        st.write(
            "The Sharpe ratio evaluates excess return relative "
            "to total volatility. Sortino uses downside deviation "
            "instead of total volatility."
        )

    st.divider()

    st.markdown("### Download your portfolio report")

    report_df = pd.DataFrame({
        "Stock": selected_stocks,
        "Investment (INR)": [
            investments[s] for s in selected_stocks
        ],
        "Portfolio Weight (%)": [
            weights[s] * 100 for s in selected_stocks
        ],
        "Historical Beta": [
            stock_betas[s] for s in selected_stocks
        ]
    })

    st.download_button(
        label="Download holdings report (CSV)",
        data=report_df.to_csv(index=False).encode("utf-8"),
        file_name="PortfolioIQ_Holdings_Report.csv",
        mime="text/csv"
    )

    summary_df = pd.DataFrame([{
        "Investor": investor_name,
        "Risk profile": risk_profile,
        "Experience": experience,
        "Investment horizon": horizon,
        "Total investment": total_investment,
        "Historical return (%)": total_return * 100,
        "Annualised return (%)": annual_return * 100,
        "Annualised volatility (%)": annual_volatility * 100,
        "Beta": beta,
        "Maximum drawdown (%)": maximum_drawdown * 100,
        "Sharpe ratio": sharpe_ratio,
        "Sortino ratio": sortino_ratio,
        "Historical daily VaR 95 (%)": daily_var_95 * 100
    }])

    st.download_button(
        label="Download portfolio analysis report (CSV)",
        data=summary_df.to_csv(index=False).encode("utf-8"),
        file_name="PortfolioIQ_Analysis_Report.csv",
        mime="text/csv"
    )

    st.caption(
        "PortfolioIQ is an educational analytics tool, not "
        "personalised financial advice or a recommendation to buy "
        "or sell securities."
    )


# 12. FOOTER
st.divider()

st.markdown(
    """
    <div style="text-align:center; color:#8195AA; padding:10px;">
        <b>PORTFOLIOIQ</b> &nbsp; | &nbsp;
        Personal Portfolio Risk Intelligence<br>
        <span style="font-size:11px;">
            Built with Python, Streamlit, Pandas, NumPy and Plotly
        </span>
    </div>
    """,
    unsafe_allow_html=True
)
