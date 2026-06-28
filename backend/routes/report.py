from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from services.report_service import generate_pdf

router = APIRouter()


@router.get("/report/{domain}")
async def export_report(domain: str):
    try:
        pdf_bytes = generate_pdf(domain)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")

    filename = f"{domain}-tos-report.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
