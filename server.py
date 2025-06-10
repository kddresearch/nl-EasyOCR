from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
import easyocr
import uvicorn
import numpy as np # Import numpy

app = FastAPI(
    title="EasyOCR FastAPI Server",
    description="Upload an image and get OCR results",
)

# Cache readers by (tuple(langs), gpu_flag)
_readers: dict[tuple[tuple[str, ...], bool], easyocr.Reader] = {}


def get_reader(langs: list[str], gpu: bool) -> easyocr.Reader:
    key = (tuple(langs), gpu)
    if key not in _readers:
        _readers[key] = easyocr.Reader(langs, gpu=gpu)
    return _readers[key]

def to_native_types(data):
    """
    Recursively converts numpy types in a data structure to native Python types
    to ensure JSON serialization.
    """
    if isinstance(data, list):
        return [to_native_types(item) for item in data]
    if isinstance(data, tuple):
        return tuple(to_native_types(item) for item in data)
    if isinstance(data, np.integer):
        return int(data)
    if isinstance(data, np.floating):
        return float(data)
    if isinstance(data, np.ndarray):
        return data.tolist()
    return data


@app.post("/readtext")
async def readtext_endpoint(
    file: UploadFile = File(...),
    langs: str = Form("en"),
    detail: int = Form(1),
    gpu: bool = Form(False),
):
    """
    Perform OCR on an uploaded image.
    - file: image to OCR
    - langs: comma-separated language codes, e.g. "en,fr,ch_sim"
    - detail: 1 for full output, 0 for flat list of strings
    - gpu: whether to use GPU
    """
    try:
        print(
            f"Received file: {file.filename}, langs: {langs}, detail: {detail}, gpu: {gpu}"
        )
        languages = [l.strip() for l in langs.split(",") if l.strip()]
        reader = get_reader(languages, gpu)
        img_bytes = await file.read()
        result = reader.readtext(img_bytes, detail=detail)

        # --- SOLUTION: Convert the result before returning ---
        serializable_result = to_native_types(result)

        return JSONResponse({"result": serializable_result})
    except Exception as e:
        # It's good practice to log the full exception for debugging
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def health_check():
    return {"status": "ok", "message": "EasyOCR server is running"}


if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=80)
