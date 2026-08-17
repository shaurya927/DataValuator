import aiosqlite
from pathlib import Path
from typing import List, Dict, Any, Optional

_db_connection = None

async def get_db(db_path: Path) -> aiosqlite.Connection:
    global _db_connection
    if _db_connection is None:
        _db_connection = await aiosqlite.connect(db_path)
        await _db_connection.execute('PRAGMA journal_mode=WAL')
        _db_connection.row_factory = aiosqlite.Row
    return _db_connection

async def close_db():
    global _db_connection
    if _db_connection is not None:
        await _db_connection.close()
        _db_connection = None

async def init_db(db_path: Path):
    db = await get_db(db_path)
    await db.execute("""
        CREATE TABLE IF NOT EXISTS datasets(
            id TEXT PRIMARY KEY,
            name TEXT,
            type TEXT,
            task_type TEXT,
            target_column TEXT,
            default_template TEXT,
            num_samples INT,
            num_classes INT,
            created_at TIMESTAMP,
            path TEXT
        )
    """)
    await db.execute("""
        CREATE TABLE IF NOT EXISTS training_runs(
            id TEXT PRIMARY KEY,
            dataset_id TEXT,
            model_name TEXT,
            task_type TEXT,
            target_column TEXT,
            template TEXT,
            epochs INT,
            learning_rate REAL,
            status TEXT,
            current_epoch INT,
            train_loss REAL,
            val_accuracy REAL,
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            checkpoint_dir TEXT,
            metrics_path TEXT,
            FOREIGN KEY(dataset_id) REFERENCES datasets(id)
        )
    """)
    await db.execute("""
        CREATE TABLE IF NOT EXISTS sample_valuations(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT,
            sample_index INT,
            forgetting_count INT,
            avg_loss REAL,
            aum_score REAL,
            tracin_score REAL,
            rarity_score REAL,
            unified_score REAL,
            category TEXT,
            embedding_x REAL,
            embedding_y REAL,
            FOREIGN KEY(run_id) REFERENCES training_runs(id)
        )
    """)
    await db.execute("""
        CREATE TABLE IF NOT EXISTS experiments(
            id TEXT PRIMARY KEY,
            run_id TEXT,
            type TEXT,
            config TEXT,
            status TEXT,
            original_accuracy REAL,
            result_accuracy REAL,
            samples_removed INT,
            precision REAL,
            recall REAL,
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            FOREIGN KEY(run_id) REFERENCES training_runs(id)
        )
    """)
    await db.commit()

async def create_dataset(db_path: Path, data: dict):
    db = await get_db(db_path)
    await db.execute(
        "INSERT INTO datasets (id, name, type, task_type, target_column, default_template, num_samples, num_classes, created_at, path) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (data['id'], data['name'], data['type'], data.get('task_type'), data.get('target_column'), data.get('default_template'), data['num_samples'], data['num_classes'], data['created_at'], data['path'])
    )
    await db.commit()

async def get_dataset(db_path: Path, dataset_id: str) -> Optional[dict]:
    db = await get_db(db_path)
    async with db.execute("SELECT * FROM datasets WHERE id = ?", (dataset_id,)) as cursor:
        row = await cursor.fetchone()
        return dict(row) if row else None

async def list_datasets(db_path: Path) -> List[dict]:
    db = await get_db(db_path)
    async with db.execute("SELECT * FROM datasets") as cursor:
        return [dict(row) for row in await cursor.fetchall()]

async def delete_dataset(db_path: Path, dataset_id: str):
    db = await get_db(db_path)
    # Manual cascade delete because PRAGMA foreign_keys might not be active
    async with db.execute("SELECT id FROM training_runs WHERE dataset_id = ?", (dataset_id,)) as cursor:
        runs = await cursor.fetchall()
        
    for run in runs:
        run_id = run['id']
        await db.execute("DELETE FROM sample_valuations WHERE run_id = ?", (run_id,))
        await db.execute("DELETE FROM experiments WHERE run_id = ?", (run_id,))
        
    await db.execute("DELETE FROM training_runs WHERE dataset_id = ?", (dataset_id,))
    await db.execute("DELETE FROM datasets WHERE id = ?", (dataset_id,))
    await db.commit()

async def create_training_run(db_path: Path, data: dict):
    db = await get_db(db_path)
    await db.execute(
        """INSERT INTO training_runs (id, dataset_id, model_name, task_type, target_column, template, epochs, learning_rate, status, 
           current_epoch, train_loss, val_accuracy, started_at, completed_at, checkpoint_dir, metrics_path) 
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (data['id'], data['dataset_id'], data['model_name'], data.get('task_type'), data.get('target_column'), data.get('template'),
         data['epochs'], data['learning_rate'], 
         data['status'], data['current_epoch'], data['train_loss'], data['val_accuracy'], 
         data['started_at'], data.get('completed_at'), data.get('checkpoint_dir'), data.get('metrics_path'))
    )
    await db.commit()

async def update_training_run(db_path: Path, run_id: str, data: dict):
    db = await get_db(db_path)
    set_clause = ", ".join([f"{k} = ?" for k in data.keys()])
    values = list(data.values()) + [run_id]
    await db.execute(f"UPDATE training_runs SET {set_clause} WHERE id = ?", values)
    await db.commit()

async def get_training_run(db_path: Path, run_id: str) -> Optional[dict]:
    db = await get_db(db_path)
    async with db.execute("SELECT * FROM training_runs WHERE id = ?", (run_id,)) as cursor:
        row = await cursor.fetchone()
        return dict(row) if row else None

async def list_training_runs(db_path: Path) -> List[dict]:
    db = await get_db(db_path)
    async with db.execute("SELECT * FROM training_runs") as cursor:
        return [dict(row) for row in await cursor.fetchall()]

async def insert_valuations_batch(db_path: Path, valuations: List[dict]):
    db = await get_db(db_path)
    await db.executemany(
        """INSERT INTO sample_valuations (run_id, sample_index, forgetting_count, avg_loss, aum_score, 
           tracin_score, rarity_score, unified_score, category, embedding_x, embedding_y) 
           VALUES (:run_id, :sample_index, :forgetting_count, :avg_loss, :aum_score, :tracin_score, 
           :rarity_score, :unified_score, :category, :embedding_x, :embedding_y)""",
        valuations
    )
    await db.commit()

async def get_valuations(db_path: Path, run_id: str, limit: int = 100, offset: int = 0, sort_by: str = "sample_index", sort_order: str = "asc", category_filter: Optional[str] = None) -> List[dict]:
    allowed_sort_cols = {"sample_index", "forgetting_count", "avg_loss", "aum_score", "tracin_score", "rarity_score", "unified_score"}
    if sort_by not in allowed_sort_cols:
        sort_by = "sample_index"
    
    order = "DESC" if sort_order.lower() == "desc" else "ASC"
    
    query = "SELECT * FROM sample_valuations WHERE run_id = ?"
    params = [run_id]
    
    if category_filter:
        query += " AND category = ?"
        params.append(category_filter)
        
    query += f" ORDER BY {sort_by} {order} LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    db = await get_db(db_path)
    async with db.execute(query, tuple(params)) as cursor:
        return [dict(row) for row in await cursor.fetchall()]

async def get_valuation_by_index(db_path: Path, run_id: str, sample_index: int) -> Optional[dict]:
    db = await get_db(db_path)
    async with db.execute("SELECT * FROM sample_valuations WHERE run_id = ? AND sample_index = ?", (run_id, sample_index)) as cursor:
        row = await cursor.fetchone()
        return dict(row) if row else None

async def get_valuation_count(db_path: Path, run_id: str, category_filter: Optional[str] = None) -> int:
    db = await get_db(db_path)
    if category_filter:
        async with db.execute("SELECT COUNT(*) FROM sample_valuations WHERE run_id = ? AND category = ?", (run_id, category_filter)) as cursor:
            return (await cursor.fetchone())[0]
    else:
        async with db.execute("SELECT COUNT(*) FROM sample_valuations WHERE run_id = ?", (run_id,)) as cursor:
            return (await cursor.fetchone())[0]


async def get_valuation_summary(db_path: Path, run_id: str) -> List[dict]:
    db = await get_db(db_path)
    async with db.execute("SELECT category, COUNT(*) as count FROM sample_valuations WHERE run_id = ? GROUP BY category", (run_id,)) as cursor:
        return [dict(row) for row in await cursor.fetchall()]


async def get_all_valuations(db_path: str, run_id: str) -> List[dict]:
    """Get all valuations for a run without limit."""
    db = await get_db(db_path)
    async with db.execute(
        "SELECT * FROM sample_valuations WHERE run_id = ? ORDER BY sample_index",
        (run_id,)
    ) as cursor:
        return [dict(row) for row in await cursor.fetchall()]


async def get_refined_valuations(db_path: str, run_id: str, exclude_categories: list = None) -> List[dict]:
    """Get valuations excluding specified categories (harmful/redundant by default)."""
    if exclude_categories is None:
        exclude_categories = ['harmful', 'redundant']
    placeholders = ','.join(['?'] * len(exclude_categories))
    db = await get_db(db_path)
    async with db.execute(
        f"SELECT * FROM sample_valuations WHERE run_id = ? AND category NOT IN ({placeholders}) ORDER BY sample_index",
        [run_id] + exclude_categories
    ) as cursor:
        return [dict(row) for row in await cursor.fetchall()]

async def update_valuation_scores(db_path, run_id: str, updates: list):
    """Bulk update unified_score and category for a run.
    updates is a list of (unified_score, category, sample_index) tuples."""
    db = await get_db(db_path)
    await db.executemany(
        "UPDATE sample_valuations SET unified_score = ?, category = ? WHERE run_id = ? AND sample_index = ?",
        [(score, cat, run_id, idx) for score, cat, idx in updates]
    )
    await db.commit()

async def batch_update_category(db_path, run_id: str, sample_indices: list, category: str):
    """Update category for specified sample indices."""
    db = await get_db(db_path)
    placeholders = ','.join(['?'] * len(sample_indices))
    await db.execute(
        f"UPDATE sample_valuations SET category = ? WHERE run_id = ? AND sample_index IN ({placeholders})",
        [category, run_id] + sample_indices
    )
    await db.commit()

async def get_valuation_comparison(db_path, run_a: str, run_b: str) -> list:
    """Get side-by-side comparison of two runs' valuations joined on sample_index."""
    db = await get_db(db_path)
    async with db.execute(
        """SELECT a.sample_index, 
                  a.unified_score as score_a, a.category as cat_a,
                  b.unified_score as score_b, b.category as cat_b
           FROM sample_valuations a
           INNER JOIN sample_valuations b ON a.sample_index = b.sample_index
           WHERE a.run_id = ? AND b.run_id = ?
           ORDER BY a.sample_index""",
        (run_a, run_b)
    ) as cursor:
        return [dict(row) for row in await cursor.fetchall()]

async def get_all_run_summaries(db_path) -> list:
    """Get summaries for all completed training runs with their category counts."""
    db = await get_db(db_path)
    # First get completed runs
    async with db.execute(
        "SELECT id, model_name, val_accuracy, epochs, learning_rate, started_at FROM training_runs WHERE status = 'completed' ORDER BY started_at DESC"
    ) as cursor:
        runs = [dict(row) for row in await cursor.fetchall()]
    
    # For each run, get category counts
    for run in runs:
        async with db.execute(
            "SELECT category, COUNT(*) as count FROM sample_valuations WHERE run_id = ? GROUP BY category",
            (run['id'],)
        ) as cursor:
            cats = {row['category']: row['count'] for row in await cursor.fetchall()}
            run['category_counts'] = cats
            run['total_samples'] = sum(cats.values())
    
    return runs


async def create_experiment(db_path: Path, data: dict):
    db = await get_db(db_path)
    await db.execute(
        """INSERT INTO experiments (id, run_id, type, config, status, original_accuracy, result_accuracy, 
           samples_removed, precision, recall, started_at, completed_at) 
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (data['id'], data['run_id'], data['type'], data['config'], data['status'], data.get('original_accuracy'), 
         data.get('result_accuracy'), data.get('samples_removed'), data.get('precision'), data.get('recall'), 
         data['started_at'], data.get('completed_at'))
    )
    await db.commit()

async def update_experiment(db_path: Path, experiment_id: str, data: dict):
    db = await get_db(db_path)
    set_clause = ", ".join([f"{k} = ?" for k in data.keys()])
    values = list(data.values()) + [experiment_id]
    await db.execute(f"UPDATE experiments SET {set_clause} WHERE id = ?", values)
    await db.commit()

async def get_experiment(db_path: Path, experiment_id: str) -> Optional[dict]:
    db = await get_db(db_path)
    async with db.execute("SELECT * FROM experiments WHERE id = ?", (experiment_id,)) as cursor:
        row = await cursor.fetchone()
        return dict(row) if row else None

async def list_experiments(db_path: Path) -> List[dict]:
    db = await get_db(db_path)
    async with db.execute("SELECT * FROM experiments") as cursor:
        return [dict(row) for row in await cursor.fetchall()]
