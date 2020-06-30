def chunks(lst, chunk_size):
    for idx in range(0, len(lst), chunk_size):
        yield lst[idx:idx + chunk_size]
