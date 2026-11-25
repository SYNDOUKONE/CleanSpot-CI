FROM python:3.12-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r requirements.txt

COPY backend/app ./app
COPY models/detection/yolov8n.pt /models/detection/yolov8n.pt
ENV CLEANSPOT_COCO_WEIGHTS=/models/detection/yolov8n.pt

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
