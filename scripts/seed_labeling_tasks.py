"""
Seed script: insert test LabelingTask rows for Discord labeling flow testing.
Usage: python scripts/seed_labeling_tasks.py
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlmodel import Session
from app.database import engine
from app.models import LabelingTask, SQLModel

SQLModel.metadata.create_all(engine)

SEED_TASKS = [
    {
        "source_id": "鼎泰豐信義店:匿名用戶A:2024-01-10",
        "content_json": {
            "text": "這家餐廳超棒！強烈推薦！服務一流！食物超好吃！五星！",
            "rating": 5,
            "author": "匿名用戶A",
            "date": "2024-01-10",
        },
        "pre_label": "fake",
        "pre_confidence": 0.52,
    },
    {
        "source_id": "鼎泰豐信義店:王小明:2024-01-12",
        "content_json": {
            "text": "點了招牌小籠包和炒飯，小籠包皮薄汁多，但炒飯稍微偏油。整體來說CP值不錯，會再來。",
            "rating": 4,
            "author": "王小明",
            "date": "2024-01-12",
        },
        "pre_label": "real",
        "pre_confidence": 0.61,
    },
    {
        "source_id": "某燒肉店:活動帳號01:2024-01-15",
        "content_json": {
            "text": "打卡送飲料！快來參加活動，留五星評論有好禮相送，機會難得不要錯過！",
            "rating": 5,
            "author": "活動帳號01",
            "date": "2024-01-15",
        },
        "pre_label": "fake",
        "pre_confidence": 0.38,
    },
    {
        "source_id": "某拉麵店:陳大頭:2024-01-18",
        "content_json": {
            "text": "湯頭偏鹹，麵條Q彈。等了大概20分鐘才上菜，環境有點吵但可接受。叉燒肉量有點少。",
            "rating": 3,
            "author": "陳大頭",
            "date": "2024-01-18",
        },
        "pre_label": "real",
        "pre_confidence": 0.67,
    },
    {
        "source_id": "某咖啡廳:新帳號用戶:2024-01-20",
        "content_json": {
            "text": "環境超好超美，咖啡也很香，服務人員很親切，下次還要再來！強烈推薦大家來！",
            "rating": 5,
            "author": "新帳號用戶",
            "date": "2024-01-20",
        },
        "pre_label": "fake",
        "pre_confidence": 0.45,
    },
]

def seed():
    with Session(engine) as session:
        # 避免重複插入
        from sqlmodel import select
        existing = session.exec(select(LabelingTask)).all()
        if existing:
            print(f"已有 {len(existing)} 筆資料，略過 seed。若要重新 seed 請先清空 labeling_tasks 資料表。")
            return

        for task_data in SEED_TASKS:
            task = LabelingTask(
                project_type="review_trust",
                source_id=task_data["source_id"],
                content_json=task_data["content_json"],
                pre_label=task_data["pre_label"],
                pre_confidence=task_data["pre_confidence"],
                status="pending",
            )
            session.add(task)

        session.commit()
        print(f"✓ 插入 {len(SEED_TASKS)} 筆測試 LabelingTask")
        print("現在可以呼叫 GET /api/labeling/pending 確認資料")

if __name__ == "__main__":
    seed()
