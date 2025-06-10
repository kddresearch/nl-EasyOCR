from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
import easyocr
import uvicorn

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
        print(f"Received file: {file.filename}, langs: {langs}, detail: {detail}, gpu: {gpu}")
        languages = [l.strip() for l in langs.split(",") if l.strip()]
        reader = get_reader(languages, gpu)
        img_bytes = await file.read()
        result = reader.readtext(img_bytes, detail=detail)
        return JSONResponse({"result": result})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def health_check():
    return {"status": "ok", "message": "EasyOCR server is running"}


if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=80)
