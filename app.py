import math
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Utleiekalkulator", layout="wide")

st.title("Utleiekalkulator")
st.write("Beregn egenkapital, lånekostnader og netto kontantstrøm før skatt.")

# -------------------------
# Hjelpefunksjoner
# -------------------------
def annuity_payment(principal: float, annual_rate_percent: float, years: int) -> float:
    """
    Beregner fast månedlig terminbeløp for annuitetslån.
    """
    months = years * 12
    monthly_rate = annual_rate_percent / 100 / 12

    if principal <= 0 or months <= 0:
        return 0.0

    if monthly_rate == 0:
        return principal / months

    payment = principal * (monthly_rate * (1 + monthly_rate) ** months) / ((1 + monthly_rate) ** months - 1)
    return payment


def serial_schedule_first_month(principal: float, annual_rate_percent: float, years: int) -> tuple[float, float, float]:
    """
    Returnerer første måneds totalbeløp, avdrag og renter for serielån.
    """
    months = years * 12
    monthly_rate = annual_rate_percent / 100 / 12

    if principal <= 0 or months <= 0:
        return 0.0, 0.0, 0.0

    monthly_principal = principal / months
    first_month_interest = principal * monthly_rate
    first_month_total = monthly_principal + first_month_interest

    return first_month_total, monthly_principal, first_month_interest


def serial_schedule_last_month(principal: float, annual_rate_percent: float, years: int) -> tuple[float, float, float]:
    """
    Returnerer siste måneds totalbeløp, avdrag og renter for serielån.
    """
    months = years * 12
    monthly_rate = annual_rate_percent / 100 / 12

    if principal <= 0 or months <= 0:
        return 0.0, 0.0, 0.0

    monthly_principal = principal / months
    remaining_before_last = monthly_principal
    last_month_interest = remaining_before_last * monthly_rate
    last_month_total = monthly_principal + last_month_interest

    return last_month_total, monthly_principal, last_month_interest


def format_nok(value: float) -> str:
    return f"{value:,.0f} kr".replace(",", " ")


# -------------------------
# Sidebar / input
# -------------------------
st.sidebar.header("Inndata")

purchase_price = st.sidebar.number_input(
    "Kjøpesum",
    min_value=0,
    value=3_000_000,
    step=50_000,
)

equity_percent = st.sidebar.slider(
    "EK-krav (%)",
    min_value=0,
    max_value=100,
    value=15,
    step=1,
)

closing_cost_percent = st.sidebar.number_input(
    "Omkostninger (%)",
    min_value=0.0,
    max_value=20.0,
    value=2.5,
    step=0.1,
)

monthly_rent = st.sidebar.number_input(
    "Månedlig leie",
    min_value=0,
    value=18_000,
    step=500,
)

electricity = st.sidebar.number_input(
    "Strøm per måned",
    min_value=0,
    value=1_000,
    step=100,
)

common_costs = st.sidebar.number_input(
    "Felleskost per måned",
    min_value=0,
    value=2_500,
    step=100,
)

municipal_fees = st.sidebar.number_input(
    "Kommunale avgifter per måned",
    min_value=0,
    value=800,
    step=100,
)

other_costs = st.sidebar.number_input(
    "Andre kostnader per måned",
    min_value=0,
    value=500,
    step=100,
)

loan_type = st.sidebar.selectbox(
    "Lånetype",
    ["Annuitetslån", "Serielån"],
)

interest_rate = st.sidebar.number_input(
    "Rente (%)",
    min_value=0.0,
    max_value=20.0,
    value=5.5,
    step=0.1,
)

repayment_years = st.sidebar.number_input(
    "Nedbetalingstid (år)",
    min_value=1,
    max_value=40,
    value=30,
    step=1,
)

# -------------------------
# Beregninger
# -------------------------
closing_costs = purchase_price * (closing_cost_percent / 100)
equity_required = purchase_price * (equity_percent / 100)
total_equity_needed = equity_required + closing_costs
loan_amount = purchase_price - equity_required

annual_rent = monthly_rent * 12
gross_yield_percent = (annual_rent / purchase_price * 100) if purchase_price > 0 else 0

monthly_operating_costs = electricity + common_costs + municipal_fees + other_costs

if loan_type == "Annuitetslån":
    monthly_loan_cost = annuity_payment(loan_amount, interest_rate, repayment_years)
    monthly_principal_payment = None
    monthly_interest_payment = None
    loan_info_text = "Fast terminbeløp hver måned."
else:
    first_total, first_principal, first_interest = serial_schedule_first_month(
        loan_amount, interest_rate, repayment_years
    )
    last_total, last_principal, last_interest = serial_schedule_last_month(
        loan_amount, interest_rate, repayment_years
    )
    monthly_loan_cost = first_total
    monthly_principal_payment = first_principal
    monthly_interest_payment = first_interest
    loan_info_text = "Terminbeløpet er høyest i starten og synker over tid."

monthly_cashflow_before_tax = monthly_rent - monthly_operating_costs - monthly_loan_cost
annual_cashflow_before_tax = monthly_cashflow_before_tax * 12

break_even_rent = monthly_operating_costs + monthly_loan_cost

# -------------------------
# Toppkort
# -------------------------
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Kjøpesum", format_nok(purchase_price))

with col2:
    st.metric("Egenkapital", format_nok(equity_required))

with col3:
    st.metric("Omkostninger", format_nok(closing_costs))

with col4:
    st.metric("Totalt EK-behov", format_nok(total_equity_needed))

st.divider()

# -------------------------
# Lån og kontantstrøm
# -------------------------
left, right = st.columns([1.2, 1])

with left:
    st.subheader("Låneberegning")

    if loan_type == "Annuitetslån":
        loan_df = pd.DataFrame(
            {
                "Post": [
                    "Lånetype",
                    "Lånebeløp",
                    "Rente",
                    "Nedbetalingstid",
                    "Månedlig terminbeløp",
                ],
                "Verdi": [
                    loan_type,
                    format_nok(loan_amount),
                    f"{interest_rate:.2f} %",
                    f"{repayment_years} år",
                    format_nok(monthly_loan_cost),
                ],
            }
        )
    else:
        last_total, _, last_interest = serial_schedule_last_month(loan_amount, interest_rate, repayment_years)

        loan_df = pd.DataFrame(
            {
                "Post": [
                    "Lånetype",
                    "Lånebeløp",
                    "Rente",
                    "Nedbetalingstid",
                    "Første måneds avdrag",
                    "Første måneds renter",
                    "Første måneds totalbeløp",
                    "Siste måneds totalbeløp",
                ],
                "Verdi": [
                    loan_type,
                    format_nok(loan_amount),
                    f"{interest_rate:.2f} %",
                    f"{repayment_years} år",
                    format_nok(monthly_principal_payment or 0),
                    format_nok(monthly_interest_payment or 0),
                    format_nok(monthly_loan_cost),
                    format_nok(last_total),
                ],
            }
        )

    st.dataframe(loan_df, use_container_width=True, hide_index=True)
    st.caption(loan_info_text)

with right:
    st.subheader("Kontantstrøm før skatt")

    cashflow_df = pd.DataFrame(
        {
            "Post": [
                "Månedlig leie",
                "Strøm",
                "Felleskost",
                "Kommunale avgifter",
                "Andre kostnader",
                "Lånekostnad per måned",
                "Netto kontantstrøm per måned",
                "Netto kontantstrøm per år",
                "Break-even leie per måned",
                "Brutto yield",
            ],
            "Verdi": [
                format_nok(monthly_rent),
                format_nok(electricity),
                format_nok(common_costs),
                format_nok(municipal_fees),
                format_nok(other_costs),
                format_nok(monthly_loan_cost),
                format_nok(monthly_cashflow_before_tax),
                format_nok(annual_cashflow_before_tax),
                format_nok(break_even_rent),
                f"{gross_yield_percent:.2f} %",
            ],
        }
    )

    st.dataframe(cashflow_df, use_container_width=True, hide_index=True)

st.divider()

# -------------------------
# Enkel vurdering
# -------------------------
st.subheader("Oppsummering")

if monthly_cashflow_before_tax > 0:
    st.success(
        f"Boligen gir positiv netto kontantstrøm før skatt på {format_nok(monthly_cashflow_before_tax)} per måned."
    )
elif monthly_cashflow_before_tax < 0:
    st.error(
        f"Boligen gir negativ netto kontantstrøm før skatt på {format_nok(abs(monthly_cashflow_before_tax))} per måned."
    )
else:
    st.info("Boligen går omtrent i null før skatt.")

st.write(
    f"""
- **Lånebeløp:** {format_nok(loan_amount)}
- **Totalt EK-behov:** {format_nok(total_equity_needed)}
- **Månedlige driftskostnader ekskl. lån:** {format_nok(monthly_operating_costs)}
- **Break-even leie:** {format_nok(break_even_rent)} per måned
- **Brutto yield:** {gross_yield_percent:.2f} %
"""
)

st.divider()

# -------------------------
# Ordforklaring
# -------------------------
with st.expander("Hva betyr tallene?"):
    st.write(
        """
**Totalt EK-behov** = egenkapital + omkostninger.

**Netto kontantstrøm før skatt** = leie minus lånekostnader og øvrige månedlige kostnader.

**Break-even leie** = hvor høy leien må være for at kontantstrøm før skatt blir 0.

**Brutto yield** = årlig leie delt på kjøpesum.
"""
    )
