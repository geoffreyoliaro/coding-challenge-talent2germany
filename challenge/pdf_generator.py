from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.units import inch
from io import BytesIO
from datetime import datetime


class TenantScreeningPDFGenerator:
    """Generate PDF reports for tenant screening results."""

    def __init__(self):
        self.styles = getSampleStyleSheet()
        # Add custom styles
        self.styles.add(ParagraphStyle(
            name='CenteredTitle',
            parent=self.styles['Title'],
            alignment=1,  # Center alignment
        ))
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            spaceAfter=12,
        ))
        self.styles.add(ParagraphStyle(
            name='SmallText',
            parent=self.styles['Normal'],
            fontSize=8,
        ))

    def generate_pdf(self, results_data):
        """
        Generate a PDF report from tenant screening results.

        Args:
            results_data: Dictionary containing evaluation results

        Returns:
            BytesIO: PDF file as a bytes buffer
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter,
                                rightMargin=72, leftMargin=72,
                                topMargin=72, bottomMargin=72)

        # Build the PDF content
        elements = []

        # Add title
        elements.append(Paragraph("Tenant Screening Report", self.styles['CenteredTitle']))
        elements.append(Spacer(1, 0.25 * inch))

        # Add date
        current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        elements.append(Paragraph(f"Generated on: {current_date}", self.styles['SmallText']))
        elements.append(Spacer(1, 0.25 * inch))

        # Add tenant information
        elements.append(Paragraph("Tenant Information", self.styles['SectionHeader']))
        tenant_info = results_data.get('tenant_info', {})
        tenant_data = [
            ["Name:", f"{tenant_info.get('first_name', '')} {tenant_info.get('last_name', '')}"],
            ["Date of Birth:", tenant_info.get('dob', 'N/A')],
            ["Gender:", tenant_info.get('gender', 'N/A')],
            ["Nationality:", tenant_info.get('nationality', 'N/A')],
            ["Location:", tenant_info.get('location', 'N/A')],
        ]
        tenant_table = Table(tenant_data, colWidths=[1.5 * inch, 4 * inch])
        tenant_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(tenant_table)
        elements.append(Spacer(1, 0.25 * inch))

        # Add match summary
        elements.append(Paragraph("Match Summary", self.styles['SectionHeader']))
        match_counts = results_data.get('match_counts', {})
        total_matches = sum(match_counts.values())

        match_summary_data = [
            ["Category", "Count", "Percentage"],
            ["High Relevance", match_counts.get('HIGH_RELEVANCE', 0),
             f"{(match_counts.get('HIGH_RELEVANCE', 0) / total_matches * 100) if total_matches else 0:.1f}%"],
            ["Medium Relevance", match_counts.get('MEDIUM_RELEVANCE', 0),
             f"{(match_counts.get('MEDIUM_RELEVANCE', 0) / total_matches * 100) if total_matches else 0:.1f}%"],
            ["Low Relevance", match_counts.get('LOW_RELEVANCE', 0),
             f"{(match_counts.get('LOW_RELEVANCE', 0) / total_matches * 100) if total_matches else 0:.1f}%"],
            ["Not Relevant", match_counts.get('NOT_RELEVANT', 0),
             f"{(match_counts.get('NOT_RELEVANT', 0) / total_matches * 100) if total_matches else 0:.1f}%"],
            ["Total", total_matches, "100.0%"],
        ]

        summary_table = Table(match_summary_data, colWidths=[2 * inch, 1.5 * inch, 1.5 * inch])
        summary_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 0.25 * inch))

        # Add detailed match results
        elements.append(Paragraph("Detailed Match Results", self.styles['SectionHeader']))

        evaluated_matches = results_data.get('evaluated_matches', [])
        for i, match in enumerate(evaluated_matches):
            # Add match header with background color based on category
            category = match.get('match_category', '')
            if category == 'HIGH_RELEVANCE':
                bg_color = colors.pink
            elif category == 'MEDIUM_RELEVANCE':
                bg_color = colors.lightyellow
            elif category == 'LOW_RELEVANCE':
                bg_color = colors.lightblue
            else:
                bg_color = colors.lightgrey

            match_header_data = [[
                                     f"Match #{i + 1}: {match.get('first_name', '')} {match.get('last_name', '')} - {match.get('match_label', '')}"]]
            match_header = Table(match_header_data, colWidths=[5 * inch])
            match_header.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), bg_color),
                ('BOX', (0, 0), (-1, -1), 1, colors.black),
                ('PADDING', (0, 0), (-1, -1), 6),
            ]))
            elements.append(match_header)

            # Add match details
            match_details_data = [
                ["ID:", str(match.get('id', 'N/A'))],
                ["Date of Birth:", match.get('dob', 'N/A')],
                ["Gender:", match.get('gender', 'N/A')],
                ["Nationality:", match.get('nationality', 'N/A')],
                ["Location:", match.get('location', 'N/A')],
                ["Risk Type:", match.get('risk_type', 'N/A')],
                ["Relevance Score:", f"{match.get('relevance_score', 0) * 100:.1f}%"],
            ]
            match_details = Table(match_details_data, colWidths=[1.5 * inch, 3.5 * inch])
            match_details.setStyle(TableStyle([
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('PADDING', (0, 0), (-1, -1), 4),
            ]))
            elements.append(match_details)

            # Add match reasons
            match_reasons = match.get('match_reasons', [])
            if match_reasons:
                elements.append(Paragraph("Match Reasons:", self.styles['Italic']))
                for reason in match_reasons:
                    elements.append(Paragraph(f"• {reason}", self.styles['Normal']))

            # Add mismatch reasons
            mismatch_reasons = match.get('mismatch_reasons', [])
            if mismatch_reasons:
                elements.append(Paragraph("Mismatch Reasons:", self.styles['Italic']))
                for reason in mismatch_reasons:
                    elements.append(Paragraph(f"• {reason}", self.styles['Normal']))

            elements.append(Spacer(1, 0.25 * inch))

        # Add footer
        elements.append(Spacer(1, 0.5 * inch))
        elements.append(
            Paragraph("This report is generated automatically and should be reviewed by a qualified professional.",
                      self.styles['SmallText']))
        elements.append(Paragraph("Confidential - For authorized use only", self.styles['SmallText']))

        # Build the PDF
        doc.build(elements)
        buffer.seek(0)
        return buffer

