def chunk_files(files: list[dict], max_files_per_chunk: int = 3):
    chunks = []

    current_chunk = []

    for file in files:
        current_chunk.append(file)

        if len(current_chunk) >= max_files_per_chunk:
            chunks.append(current_chunk)
            current_chunk = []

    if current_chunk:
        chunks.append(current_chunk)

    return chunks
