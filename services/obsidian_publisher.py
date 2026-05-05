from datetime import datetime
from github import Github
from config import GITHUB_TOKEN, GITHUB_REPO, OBSIDIAN_IDEAS_PATH


def _build_clarifications_block(questions: list[str]) -> str:
    if not questions:
        return ""
    items = "\n".join(f"- [ ] {q}" for q in questions)
    return f"""

---

## ❓ Требуют уточнения

{items}
"""


def _split_value_and_reason(raw: str) -> tuple[str, str]:
    """Split 'value | reason' into (value, reason)."""
    if "|" in raw:
        parts = raw.split("|", 1)
        return parts[0].strip(), parts[1].strip()
    return raw.strip(), ""


def build_markdown(rice: dict, raw_idea: str) -> str:
    date = datetime.now().strftime("%Y-%m-%d")
    title = rice.get("НАЗВАНИЕ", "Без названия")
    описание = rice.get("ОПИСАНИЕ", "—")
    вывод = rice.get("ВЫВОД", "—")
    метрики = rice.get("МЕТРИКИ", "—")
    риски = rice.get("РИСКИ", "—")
    score = rice.get("RICE_SCORE", "—")
    уточнения_raw = rice.get("УТОЧНЕНИЯ", "нет")
    уточнения_list = (
        [q.strip() for q in уточнения_raw.split("|") if q.strip()]
        if уточнения_raw.lower() != "нет"
        else []
    )

    охват_val, охват_why = _split_value_and_reason(rice.get("ОХВАТ", "—"))
    влияние_val, влияние_why = _split_value_and_reason(rice.get("ВЛИЯНИЕ", "—"))
    уверен_val, уверен_why = _split_value_and_reason(rice.get("УВЕРЕННОСТЬ", "—"))
    затраты_val, затраты_why = _split_value_and_reason(rice.get("ЗАТРАТЫ", "—"))

    tags = "idea, rice, needs-clarification" if уточнения_list else "idea, rice"

    return f"""---
title: {title}
date: {date}
tags: [{tags}]
---

# {title}

**Дата:** {date}

---

## Исходная идея

{raw_idea}

---

## Описание

{описание}

---

## RICE Оценка

### Итог

| Критерий | Значение |
|---|---|
| Охват (Reach) | {охват_val} |
| Влияние (Impact) | {влияние_val} |
| Уверенность (Confidence) | {уверен_val} |
| Затраты (Effort) | {затраты_val} |
| **RICE Score** | **{score}** |

### Обоснование

**Охват — {охват_val}**
{охват_why if охват_why else "—"}

**Влияние — {влияние_val}**
{влияние_why if влияние_why else "—"}

**Уверенность — {уверен_val}**
{уверен_why if уверен_why else "—"}

**Затраты — {затраты_val}**
{затраты_why if затраты_why else "—"}

---

## Метрики

{метрики}

---

## Риски

{риски}

---

## Вывод

{вывод}
{_build_clarifications_block(уточнения_list)}"""


def publish_to_obsidian(rice: dict, raw_idea: str) -> str:
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(GITHUB_REPO)

    date = datetime.now().strftime("%Y-%m-%d")
    title_slug = rice.get("НАЗВАНИЕ", "idea").replace(" ", "_").replace("/", "-")[:50]
    filename = f"{date}_{title_slug}.md"
    path = f"{OBSIDIAN_IDEAS_PATH}/{filename}"

    content = build_markdown(rice, raw_idea)

    repo.create_file(
        path=path,
        message=f"idea: {rice.get('НАЗВАНИЕ', 'new idea')}",
        content=content,
    )
    return filename
