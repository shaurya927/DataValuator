import requests
import time
import os

BASE_URL = "http://127.0.0.1:8000/api"

def run_test():
    print("1. Creating dummy dataset...")
    csv_path = "dummy_dataset.csv"
    with open(csv_path, "w") as f:
        f.write("feature1,feature2,target\n")
        for i in range(100):
            f.write(f"{i*0.1},{i*0.2},{i%2}\n")
    
    print("2. Uploading dataset...")
    with open(csv_path, "rb") as f:
        res = requests.post(f"{BASE_URL}/datasets/upload", files={"file": f})
    
    assert res.status_code == 200, f"Upload failed: {res.text}"
    dataset_id = res.json()["id"]
    print(f"Dataset uploaded, ID: {dataset_id}")

    print("3. Starting training run...")
    config = {
        "dataset_id": dataset_id,
        "model_name": "tabular",
        "epochs": 2,
        "learning_rate": 0.01
    }
    res = requests.post(f"{BASE_URL}/training/start", json=config)
    assert res.status_code == 200, f"Start training failed: {res.text}"
    run_id = res.json()["run_id"]
    print(f"Training started, run ID: {run_id}")

    print("4. Waiting for training to complete...")
    while True:
        res = requests.get(f"{BASE_URL}/training/history")
        runs = res.json()
        run = next((r for r in runs if r["id"] == run_id), None)
        if run:
            if run["status"] == "completed":
                print("Training completed!")
                break
            elif run["status"] == "failed":
                print("Training failed!")
                break
            else:
                print(f"Status: {run['status']}, Epoch: {run.get('current_epoch', 0)}")
        time.sleep(1)

    print("5. Getting valuation summary...")
    res = requests.get(f"{BASE_URL}/valuation/{run_id}/summary")
    assert res.status_code == 200, f"Valuation summary failed: {res.text}"
    print(f"Summary: {res.json()}")

    print("6. Starting pruning experiment...")
    exp_config = {
        "run_id": run_id,
        "type": "prune",
        "exclude_categories": ["harmful", "redundant"]
    }
    res = requests.post(f"{BASE_URL}/experiments/prune", json=exp_config)
    assert res.status_code == 200, f"Start experiment failed: {res.text}"
    exp_id = res.json()["experiment_id"]
    print(f"Experiment started, ID: {exp_id}")

    print("7. Waiting for experiment to complete...")
    while True:
        res = requests.get(f"{BASE_URL}/experiments/{exp_id}/results")
        if res.status_code == 200:
            exp_data = res.json()
            if exp_data["status"] == "completed":
                print(f"Experiment completed! Original Acc: {exp_data['original_accuracy']}, Result Acc: {exp_data['result_accuracy']}, Removed: {exp_data['samples_removed']}")
                break
            elif exp_data["status"] == "failed":
                print("Experiment failed!")
                break
        time.sleep(1)

    os.remove(csv_path)
    print("Smoke test finished successfully!")

if __name__ == "__main__":
    run_test()
