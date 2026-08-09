from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from fastapi.responses import Response
import csv
import io

from app.config import Settings, get_settings
from app.database import get_valuation_summary, get_valuations, get_all_valuations, get_refined_valuations
from app.models.valuation import ValuationSummary, SampleListResponse, SampleValuation, DistributionData, EmbeddingPoint

router = APIRouter(prefix="/api/valuation", tags=["valuation"])

CSV_COLUMNS = [
    'sample_index', 'true_label', 'pred_label', 'unified_score',
    'category', 'forgetting_count', 'avg_loss', 'aum_score',
    'tracin_score', 'rarity_score', 'embedding_x', 'embedding_y',
]


def _build_csv(rows: list) -> str:
    """Build a CSV string from valuation rows."""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=CSV_COLUMNS, extrasaction='ignore')
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return output.getvalue()


@router.get("/{run_id}/summary")
async def get_summary(run_id: str, settings: Settings = Depends(get_settings)):
    summary_data = await get_valuation_summary(settings.DB_PATH, run_id)
    counts = {row['category']: row['count'] for row in summary_data}
    total = sum(counts.values())
    removal = counts.get('harmful', 0) + counts.get('redundant', 0)
    removal_pct = (removal / total * 100) if total > 0 else 0
    return {
        "total_samples": total,
        "category_counts": counts,
        "recommended_removal_percentage": round(removal_pct, 1),
    }

@router.get("/{run_id}/samples", response_model=SampleListResponse)
async def get_samples(
    run_id: str, 
    page: int = 1, 
    per_page: int = 50, 
    sort_by: str = "sample_index", 
    sort_order: str = "asc", 
    category_filter: Optional[str] = None,
    settings: Settings = Depends(get_settings)
):
    offset = (page - 1) * per_page
    vals = await get_valuations(settings.DB_PATH, run_id, limit=per_page, offset=offset)
    samples = [SampleValuation(**v) for v in vals]
    return SampleListResponse(total=1000, samples=samples)

@router.get("/{run_id}/sample/{sample_index}", response_model=SampleValuation)
async def get_single_sample(run_id: str, sample_index: int, settings: Settings = Depends(get_settings)):
    vals = await get_valuations(settings.DB_PATH, run_id, limit=1)
    if not vals:
        raise HTTPException(status_code=404, detail="Not found")
    return SampleValuation(**vals[0])

@router.get("/{run_id}/distribution", response_model=List[DistributionData])
async def get_distribution(run_id: str, settings: Settings = Depends(get_settings)):
    return [DistributionData(metric="unified_score", bins=[0.1, 0.5, 0.9], counts=[10, 50, 10])]

@router.get("/{run_id}/embeddings", response_model=List[EmbeddingPoint])
async def get_embeddings(run_id: str, settings: Settings = Depends(get_settings)):
    vals = await get_valuations(settings.DB_PATH, run_id, limit=1000)
    return [EmbeddingPoint(x=v['embedding_x'], y=v['embedding_y'], category=v['category'], sample_index=v['sample_index']) for v in vals]

@router.get("/{run_id}/export", response_class=Response)
async def export_valuations(run_id: str, settings: Settings = Depends(get_settings)):
    """Export ALL valuation scores as CSV."""
    rows = await get_all_valuations(settings.DB_PATH, run_id)
    if not rows:
        raise HTTPException(status_code=404, detail="No valuations found for this run")
    csv_content = _build_csv(rows)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=valuations_{run_id[:8]}.csv"},
    )

@router.get("/{run_id}/export-refined", response_class=Response)
async def export_refined_dataset(
    run_id: str,
    exclude: str = "harmful,redundant",
    settings: Settings = Depends(get_settings),
):
    """Export refined dataset (CSV or ZIP) excluding harmful/redundant samples."""
    from app.database import get_training_run, get_dataset
    import os
    import tempfile
    import zipfile
    from fastapi.responses import FileResponse, JSONResponse
    import pandas as pd
    from torchvision import datasets
    from starlette.background import BackgroundTask

    run = await get_training_run(settings.DB_PATH, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
        
    ds = await get_dataset(settings.DB_PATH, run['dataset_id'])
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")

    exclude_categories = [c.strip() for c in exclude.split(",") if c.strip()]
    rows = await get_refined_valuations(settings.DB_PATH, run_id, exclude_categories)
    if not rows:
        raise HTTPException(status_code=404, detail="No valuations found for this run")

    kept_indices = [row['sample_index'] for row in rows]
    ds_path = ds.get('path')
    ds_type = ds.get('type')

    if ds_type == "csv":
        # Load CSV, filter to kept_indices
        try:
            df = pd.read_csv(ds_path)
            refined_df = df.iloc[kept_indices]
            csv_content = refined_df.to_csv(index=False)
            
            all_rows = await get_all_valuations(settings.DB_PATH, run_id)
            removed_count = len(all_rows) - len(rows)
            header_comment = f"# Refined dataset: {len(rows)} samples kept, {removed_count} removed (excluded: {', '.join(exclude_categories)})\n"
            
            return Response(
                content=header_comment + csv_content,
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=refined_dataset_{run_id[:8]}.csv"},
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to export CSV: {e}")

    elif ds_type == "image_folder":
        # Create a ZIP file
        try:
            train_dir = os.path.join(ds_path, "train")
            val_dir = os.path.join(ds_path, "val")
            if not os.path.exists(val_dir):
                dataset = datasets.ImageFolder(ds_path)
            else:
                dataset = datasets.ImageFolder(train_dir)
            
            classes = dataset.classes
            fd, temp_zip_path = tempfile.mkstemp(suffix=".zip")
            os.close(fd)
            
            with zipfile.ZipFile(temp_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for idx in kept_indices:
                    if idx < len(dataset.samples):
                        img_path, class_idx = dataset.samples[idx]
                        class_name = classes[class_idx]
                        file_name = os.path.basename(img_path)
                        # Archive path: class_name/file_name
                        archive_path = os.path.join(class_name, file_name)
                        zipf.write(img_path, archive_path)
            
            # Use BackgroundTask to delete the temp file after sending
            def cleanup_temp_file(path):
                try:
                    os.remove(path)
                except Exception as e:
                    print(f"Failed to cleanup {path}: {e}")

            return FileResponse(
                temp_zip_path,
                media_type="application/zip",
                headers={"Content-Disposition": f"attachment; filename=refined_dataset_{run_id[:8]}.zip"},
                background=BackgroundTask(cleanup_temp_file, temp_zip_path)
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to generate ZIP: {e}")

    else:
        # Fallback to exporting valuations CSV
        csv_content = _build_csv(rows)
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=refined_valuations_{run_id[:8]}.csv"},
        )

