from huggingface_hub import snapshot_download

snapshot_download(
    repo_id="google/gemma-3-4b-it",
    local_dir="./gemma-3-4b-it",
    local_dir_use_symlinks=False,
    num_threads=8
)