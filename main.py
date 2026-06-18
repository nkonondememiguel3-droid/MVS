

from ingestion.ingestion import loads


if __name__ == "__main__":
    count: int = 0
    for sample in loads("datasets/librispeech"):
        if count == 10:
            break

        count += 1
        print(f"The location of the converted audio file is {sample[2]}.")

