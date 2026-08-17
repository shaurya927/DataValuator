from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from fastapi.responses import Response
import csv
import io
import logging

logger = logging.getLogger(__name__)

from app.config import Settings, get_settings
from app.database import get_valuation_summary, get_valuations, get_all_valuations, get_refined_valuations, get_valuation_by_index, get_valuation_count, update_valuation_scores, batch_update_category, get_valuation_comparison, get_all_run_summaries
from app.models.valuation import ValuationSummary, SampleListResponse, SampleValuation, DistributionData, EmbeddingPoint, WeightConfig, BatchUpdateRequest
import numpy as np

router = APIRouter(prefix="/api/valuation", tags=["valuation"])

@router.get("/compare")
async def compare_runs(run_a: str = Query(...), run_b: str = Query(...), settings: Settings = Depends(get_settings)):
    """Compare valuations between two runs."""
    comparison = await get_valuation_comparison(settings.DB_PATH, run_a, run_b)
    if not comparison:
        raise HTTPException(status_code=404, detail="No overlapping samples found")
    
    # Compute summaries
    summary_a = await get_valuation_summary(settings.DB_PATH, run_a)
    summary_b = await get_valuation_summary(settings.DB_PATH, run_b)
    
    counts_a = {r['category']: r['count'] for r in summary_a}
    counts_b = {r['category']: r['count'] for r in summary_b}
    
    # Category changes
    changes = []
    overlap = 0
    for row in comparison:
        if row['cat_a'] != row['cat_b']:
            changes.append({
                'sample_index': row['sample_index'],
                'from_category': row['cat_a'],
                'to_category': row['cat_b'],
                'score_a': row['score_a'],
                'score_b': row['score_b']
            })
        else:
            overlap += 1
    
    return {
        "run_a_summary": {"category_counts": counts_a, "total": sum(counts_a.values())},
        "run_b_summary": {"category_counts": counts_b, "total": sum(counts_b.values())},
        "category_changes": changes[:500],  # Limit to 500 for API response size
        "total_changes": len(changes),
        "overlap_count": overlap,
        "total_samples": len(comparison)
    }

@router.get("/all-summaries")
async def all_summaries(settings: Settings = Depends(get_settings)):
    """Get summaries for all completed runs."""
    return await get_all_run_summaries(settings.DB_PATH)

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
    vals = await get_valuations(settings.DB_PATH, run_id, limit=per_page, offset=offset, sort_by=sort_by, sort_order=sort_order, category_filter=category_filter)
    total = await get_valuation_count(settings.DB_PATH, run_id, category_filter)
    samples = [SampleValuation(**v) for v in vals]
    return SampleListResponse(total=total, samples=samples)

@router.get("/{run_id}/sample/{sample_index}", response_model=SampleValuation)
async def get_single_sample(run_id: str, sample_index: int, settings: Settings = Depends(get_settings)):
    val = await get_valuation_by_index(settings.DB_PATH, run_id, sample_index)
    if not val:
        raise HTTPException(status_code=404, detail="Not found")
    return SampleValuation(**val)

@router.get("/{run_id}/distribution", response_model=List[DistributionData])
async def get_distribution(run_id: str, settings: Settings = Depends(get_settings)):
    vals = await get_all_valuations(settings.DB_PATH, run_id)
    if not vals:
        return []
    scores = [v.get("unified_score", 0.0) for v in vals if v.get("unified_score") is not None]
    if not scores:
        return []
    counts, bin_edges = np.histogram(scores, bins=10, range=(0.0, 1.0))
    return [DistributionData(metric="unified_score", bins=bin_edges[:-1].tolist(), counts=counts.tolist())]

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
        # Fallback to exporting valuations if the original dataset was deleted
        exclude_categories = [c.strip() for c in exclude.split(",") if c.strip()]
        rows = await get_refined_valuations(settings.DB_PATH, run_id, exclude_categories)
        if not rows:
            raise HTTPException(status_code=404, detail="No valuations found for this run")
        csv_content = _build_csv(rows)
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=refined_valuations_{run_id[:8]}.csv"},
        )

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
                    logger.warning(f"Failed to cleanup {path}: {e}")

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

@router.post("/{run_id}/recompute")
async def recompute_scores(run_id: str, weights: WeightConfig, settings: Settings = Depends(get_settings)):
    """Recompute unified scores with custom weights."""
    from app.engine.valuator import compute_unified_scores
    vals = await get_all_valuations(settings.DB_PATH, run_id)
    if not vals:
        raise HTTPException(status_code=404, detail="No valuations found")
    
    forgetting = np.array([v['forgetting_count'] for v in vals])
    avg_loss = np.array([v['avg_loss'] for v in vals])
    aum = np.array([v['aum_score'] for v in vals])
    tracin = np.array([v['tracin_score'] for v in vals])
    rarity = np.array([v['rarity_score'] for v in vals])
    
    w = [weights.forgetting, weights.loss, weights.aum, weights.tracin, weights.rarity]
    scores, categories = compute_unified_scores(forgetting, avg_loss, aum, tracin, rarity, weights=w)
    
    updates = [(float(scores[i]), categories[i], vals[i]['sample_index']) for i in range(len(vals))]
    await update_valuation_scores(settings.DB_PATH, run_id, updates)
    
    # Return new summary
    from collections import Counter
    counts = Counter(categories)
    total = len(categories)
    removal = counts.get('harmful', 0) + counts.get('redundant', 0)
    return {
        "total_samples": total,
        "category_counts": dict(counts),
        "recommended_removal_percentage": round((removal / total * 100) if total > 0 else 0, 1),
        "weights_applied": w
    }

@router.post("/{run_id}/batch-update")
async def batch_update(run_id: str, req: BatchUpdateRequest, settings: Settings = Depends(get_settings)):
    """Batch update category for specified samples."""
    valid_categories = {'high_value', 'normal', 'redundant', 'harmful', 'suspicious'}
    if req.category not in valid_categories:
        raise HTTPException(status_code=400, detail=f"Invalid category. Must be one of: {valid_categories}")
    await batch_update_category(settings.DB_PATH, run_id, req.sample_indices, req.category)
    return {"updated": len(req.sample_indices), "category": req.category}

