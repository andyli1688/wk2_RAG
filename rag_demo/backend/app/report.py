"""
Report generation module: Generate final Markdown and JSON reports
"""
import logging
from datetime import datetime
from typing import List

from app.models import (
    ClaimAnalysis, ReportSummary, AnalysisReport,
    Claim
)
from app.utils import logger

logger = logging.getLogger(__name__)


def generate_summary(analyses: List[ClaimAnalysis]) -> ReportSummary:
    """
    Generate summary statistics from claim analyses
    
    Args:
        analyses: List of ClaimAnalysis objects
    
    Returns:
        ReportSummary object
    """
    total = len(analyses)
    fully = sum(1 for a in analyses if a.coverage == "fully_addressed")
    partially = sum(1 for a in analyses if a.coverage == "partially_addressed")
    not_addressed = sum(1 for a in analyses if a.coverage == "not_addressed")
    
    avg_confidence = sum(a.confidence for a in analyses) / total if total > 0 else 0
    
    # Collect gaps
    all_gaps = []
    for analysis in analyses:
        if analysis.gaps:
            all_gaps.extend(analysis.gaps)
    
    # Get unique gaps
    key_gaps = list(set(all_gaps))[:10]  # Top 10 unique gaps
    
    # Collect recommended actions
    all_actions = []
    for analysis in analyses:
        if analysis.recommended_actions:
            all_actions.extend(analysis.recommended_actions)
    
    # Get unique actions
    priority_actions = list(set(all_actions))[:10]  # Top 10 unique actions
    
    return ReportSummary(
        total_claims=total,
        fully_addressed=fully,
        partially_addressed=partially,
        not_addressed=not_addressed,
        average_confidence=round(avg_confidence, 2),
        key_gaps=key_gaps,
        priority_actions=priority_actions
    )


def generate_markdown_report(
    report_id: str,
    claims: List[Claim],
    analyses: List[ClaimAnalysis],
    summary: ReportSummary
) -> str:
    """
    Generate Markdown formatted report
    
    Args:
        report_id: Report identifier
        claims: Original claims
        analyses: Claim analyses
        summary: Summary statistics
    
    Returns:
        Markdown formatted report string
    """
    md = f"""# Short Report Rebuttal Analysis Report

**Report ID**: {report_id}
**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## Executive Summary

This report provides a comprehensive analysis of {summary.total_claims} claims from the short report, assessing the extent to which internal evidence addresses each claim.

### Coverage Statistics

- **Fully Addressed**: {summary.fully_addressed} claims ({summary.fully_addressed/summary.total_claims*100:.1f}%)
- **Partially Addressed**: {summary.partially_addressed} claims ({summary.partially_addressed/summary.total_claims*100:.1f}%)
- **Not Addressed**: {summary.not_addressed} claims ({summary.not_addressed/summary.total_claims*100:.1f}%)
- **Average Confidence**: {summary.average_confidence}/100

### Key Findings

"""

    if summary.key_gaps:
        md += "**Key Evidence Gaps**:\n"
        for gap in summary.key_gaps:
            md += f"- {gap}\n"
        md += "\n"

    if summary.priority_actions:
        md += "**Recommended Priority Actions**:\n"
        for action in summary.priority_actions:
            md += f"- {action}\n"
        md += "\n"

    md += "---\n\n## Detailed Analysis\n\n"
    
    # Group by coverage
    fully = [a for a in analyses if a.coverage == "fully_addressed"]
    partially = [a for a in analyses if a.coverage == "partially_addressed"]
    not_addressed = [a for a in analyses if a.coverage == "not_addressed"]
    
    # Create claim lookup
    claim_dict = {c.claim_id: c for c in claims}
    
    # Fully addressed
    if fully:
        md += "### ✅ Fully Addressed Claims\n\n"
        for analysis in fully:
            claim = claim_dict.get(analysis.claim_id)
            md += f"#### {analysis.claim_id}: {claim.claim_text if claim else 'Unknown'}\n\n"
            md += f"**Type**: {claim.claim_type if claim else 'Unknown'} | **Pages**: {', '.join(map(str, claim.page_numbers)) if claim else 'N/A'}\n\n"
            md += f"**Analysis**:\n{analysis.reasoning}\n\n"
            md += f"**Confidence**: {analysis.confidence}/100\n\n"
            if analysis.citations:
                md += "**Citation Sources**:\n"
                for i, cit in enumerate(analysis.citations, 1):
                    md += f"{i}. {cit.doc_title} (Chunk: {cit.chunk_id})\n"
                    md += f"   > {cit.quote[:200]}...\n\n"
            md += "---\n\n"
    
    # Partially addressed
    if partially:
        md += "### ⚠️ Partially Addressed Claims\n\n"
        for analysis in partially:
            claim = claim_dict.get(analysis.claim_id)
            md += f"#### {analysis.claim_id}: {claim.claim_text if claim else 'Unknown'}\n\n"
            md += f"**Type**: {claim.claim_type if claim else 'Unknown'} | **Pages**: {', '.join(map(str, claim.page_numbers)) if claim else 'N/A'}\n\n"
            md += f"**Analysis**:\n{analysis.reasoning}\n\n"
            md += f"**Confidence**: {analysis.confidence}/100\n\n"
            if analysis.citations:
                md += "**Citation Sources**:\n"
                for i, cit in enumerate(analysis.citations, 1):
                    md += f"{i}. {cit.doc_title} (Chunk: {cit.chunk_id})\n"
                    md += f"   > {cit.quote[:200]}...\n\n"
            if analysis.gaps:
                md += "**Evidence Gaps**:\n"
                for gap in analysis.gaps:
                    md += f"- {gap}\n"
                md += "\n"
            if analysis.recommended_actions:
                md += "**Recommended Actions**:\n"
                for action in analysis.recommended_actions:
                    md += f"- {action}\n"
                md += "\n"
            md += "---\n\n"
    
    # Not addressed
    if not_addressed:
        md += "### ❌ Not Addressed Claims\n\n"
        for analysis in not_addressed:
            claim = claim_dict.get(analysis.claim_id)
            md += f"#### {analysis.claim_id}: {claim.claim_text if claim else 'Unknown'}\n\n"
            md += f"**Type**: {claim.claim_type if claim else 'Unknown'} | **Pages**: {', '.join(map(str, claim.page_numbers)) if claim else 'N/A'}\n\n"
            md += f"**Analysis**:\n{analysis.reasoning}\n\n"
            md += f"**Confidence**: {analysis.confidence}/100\n\n"
            if analysis.citations:
                md += "**Citation Sources**:\n"
                for i, cit in enumerate(analysis.citations, 1):
                    md += f"{i}. {cit.doc_title} (Chunk: {cit.chunk_id})\n"
                    md += f"   > {cit.quote[:200]}...\n\n"
            if analysis.gaps:
                md += "**Evidence Gaps**:\n"
                for gap in analysis.gaps:
                    md += f"- {gap}\n"
                md += "\n"
            if analysis.recommended_actions:
                md += "**Recommended Actions**:\n"
                for action in analysis.recommended_actions:
                    md += f"- {action}\n"
                md += "\n"
            md += "---\n\n"

    md += "\n## Appendix\n\n"
    md += "This report was auto-generated by the Short Report Rebuttal Assistant.\n"
    md += "Professional analyst review is recommended.\n"
    
    return md


def generate_json_report(
    report_id: str,
    claims: List[Claim],
    analyses: List[ClaimAnalysis],
    summary: ReportSummary
) -> dict:
    """
    Generate JSON formatted report
    
    Args:
        report_id: Report identifier
        claims: Original claims
        analyses: Claim analyses
        summary: Summary statistics
    
    Returns:
        Dictionary representation of the report
    """
    return {
        "report_id": report_id,
        "generated_at": datetime.now().isoformat(),
        "summary": summary.dict(),
        "claims": [c.dict() for c in claims],
        "analyses": [a.dict() for a in analyses]
    }


def create_analysis_report(
    report_id: str,
    claims: List[Claim],
    analyses: List[ClaimAnalysis]
) -> AnalysisReport:
    """
    Create complete analysis report
    
    Args:
        report_id: Report identifier
        claims: Original claims
        analyses: Claim analyses
    
    Returns:
        AnalysisReport object
    """
    summary = generate_summary(analyses)
    markdown = generate_markdown_report(report_id, claims, analyses, summary)
    json_data = generate_json_report(report_id, claims, analyses, summary)
    
    return AnalysisReport(
        report_id=report_id,
        generated_at=datetime.now(),
        summary=summary,
        claim_analyses=analyses,
        markdown=markdown,
        json_data=json_data
    )
