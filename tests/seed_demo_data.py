"""
Генерирует синтетические лиды с разными UTM-метками, чтобы наполнить
дашборд данными для демонстрации. Запуск: python tests/seed_demo_data.py
"""

import asyncio
import random

import httpx

BACKEND_URL = "http://127.0.0.1:8000"

SOURCES = ["yandex_direct", "google_ads", "instagram", "vk", "direct"]
CAMPAIGNS = ["remont_leto2026", "dom_pod_kluch", "brand_zapros"]
PROJECT_TYPES = ["Квартира", "Дом", "Коммерция"]
NAMES = ["Анна", "Дмитрий", "Мария", "Сергей", "Ольга", "Игорь"]


async def seed(count: int = 40):
    success = 0
    failed = 0
    async with httpx.AsyncClient(timeout=10) as client:
        for i in range(count):
            payload = {
                "name": random.choice(NAMES),
                "phone": f"9{random.randint(100000000, 999999999)}",
                "source": "form",
                "project_type": random.choice(PROJECT_TYPES),
                "utm_source": random.choice(SOURCES),
                "utm_medium": "cpc",
                "utm_campaign": random.choice(CAMPAIGNS),
            }
            try:
                resp = await client.post(f"{BACKEND_URL}/webhook/form", json=payload)
                if resp.status_code == 200:
                    print(i + 1, "OK", resp.json())
                    success += 1
                else:
                    print(i + 1, "HTTP ERROR", resp.status_code, resp.text[:200])
                    failed += 1
            except Exception as exc:
                print(i + 1, "FAILED:", exc)
                failed += 1

            await asyncio.sleep(0.2)  # небольшая пауза, чтобы не заваливать сервер

    print(f"\nГотово. Успешно: {success}, с ошибкой: {failed}")


if __name__ == "__main__":
    asyncio.run(seed())