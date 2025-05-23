from fpdf import FPDF
import pandas as pd
from io import BytesIO
import tempfile
from datetime import datetime

class PDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 12)
        self.cell(0, 10, "Allianz VitaVerde - Simulation Report", 0, 1, "C")

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 10, f"Generated by Allianz VitaVerde Simulator - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 0, 0, "C")

def generate_pdf_report(summary_df, advisor_name, client_name, buffer_pie, buffer_chart,
                        contribution, duration, insurance_cost_rate, setup_cost_rate, death_benefit_option, guarantee_options):
    pdf = PDF()
    pdf.add_page()

    pdf.set_font("Arial", "", 12)

    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Allianz VitaVerde - Simulation Report", ln=True)
    pdf.set_font("Arial", "I", 10)
    pdf.cell(0, 10, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True)
    pdf.cell(0, 10, f"Advisor: {advisor_name} | Client: {client_name}", ln=True)

    pdf.set_font("Arial", "", 12)
    pdf.ln(5)
    pdf.cell(0, 10, f"Monthly Contribution: {contribution}", ln=True)
    pdf.cell(0, 10, f"Investment Horizon: {duration} years", ln=True)
    pdf.cell(0, 10, f"Insurance Cost: {insurance_cost_rate * 100:.2f}%", ln=True)
    pdf.cell(0, 10, f"Setup Cost: {setup_cost_rate * 100:.2f}%", ln=True)
    pdf.cell(0, 10, f"Death Benefit Guarantee: {'Yes' if death_benefit_option else 'No'}", ln=True)
    pdf.cell(0, 10, f"Contribution Guarantee: {guarantee_options}", ln=True)

    pdf.ln(10)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Fund Allocation", ln=True)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
        tmpfile.write(buffer_pie.getvalue())
        pdf.image(tmpfile.name, w=100)

    pdf.ln(10)
    pdf.cell(0, 10, "Scenario Comparison", ln=True)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
        tmpfile.write(buffer_chart.getvalue())
        pdf.image(tmpfile.name, w=150)

    pdf.ln(10)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Simulation Summary", ln=True)
    pdf.set_font("Arial", "", 10)

    for idx, row in summary_df.iterrows():
        pdf.multi_cell(
            0, 8,
            f"{row['Scenario']}: "
            f"Paid-in: {row['Paid-in Capital (EUR)']} | "
            f"After Tax: {row['After Tax (EUR)']} | "
            f"Guaranteed Payout: {row['Guaranteed Payout (EUR)']}"
        )

    pdf.set_y(-30)
    pdf.set_font("Arial", "I", 8)
    pdf.cell(0, 10, "Generated by Allianz VitaVerde Simulator", 0, 0, 'C')

    # Verwenden Sie dest='S' um die PDF-Daten als String zu erhalten
    pdf_output = pdf.output(dest='S').encode('latin1')
    pdf_buffer = BytesIO(pdf_output)
    pdf_buffer.seek(0)
    return pdf_buffer

def generate_excel_report(simulation_results, summary_df):
    excel_buffer = BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
        pd.DataFrame(simulation_results).to_excel(writer, sheet_name="Simulation Results")
        summary_df.to_excel(writer, sheet_name="Summary", index=False)

    excel_buffer.seek(0)
    return excel_buffer
