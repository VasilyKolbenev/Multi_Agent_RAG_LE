import os, uuid, json, textwrap, time
from typing import Any, Dict, List, Optional, Generator

# Делаем langextract опциональным, чтобы деплой на Railway не падал при отсутствии пакета
try:
    import langextract as lx
except Exception as _e:
    lx = None
    print("[langx] LangExtract is not available, extraction endpoints will be limited.")

MODEL_ID = os.environ.get("LX_MODEL_ID", "gpt-4o-mini")  # Используем поддерживаемую модель

DEFAULT_PROMPT = textwrap.dedent("""Извлеки из текста именованные сущности (organization, person, date, money) и отношения между ними.
Строго используй текст источника (не перефразируй). Верни атрибуты: type, value, optional_attrs.
""")

def _examples_default():
    return [lx.data.ExampleData(
        text="Компания ACME выручила $12.4M во 2 квартале 2025 года.",
        extractions=[
            lx.data.Extraction(extraction_class="organization", extraction_text="ACME"),
            lx.data.Extraction(extraction_class="money", extraction_text="$12.4M", attributes={"period":"Q2 2025"}),
        ],
    )]

def run_extraction(text_or_url: str, prompt: Optional[str]=None, examples: Optional[List[Dict[str, Any]]]=None) -> Dict[str, Any]:
    if lx is None:
        # LangExtract не установлен — тихо возвращаем пустой результат
        return {"job_id": "disabled", "items": []}
    prompt = prompt or DEFAULT_PROMPT
    ex = _examples_default()
    if examples:
        ex = [lx.data.ExampleData(
                text=e.get("text",""),
                extractions=[lx.data.Extraction(extraction_class=it.get("class","entity"), extraction_text=it.get("text",""), attributes=it.get("attributes",{}))
                             for it in e.get("extractions",[])]
             ) for e in examples]

    # --- DEBUG LANGEXTRACT PARAMS ---
    from . import config
    # ПРИНУДИТЕЛЬНО используем поддерживаемую модель (Railway переопределяет переменную)
    lx_model_id = "gpt-4o-mini"  # Принудительно, так как Railway имеет старое значение в Variables
    api_key = config.OPENAI_API_KEY
    print("="*50)
    print("🔍 DEBUG: LangExtract Parameters")
    print(f"  - Model ID: {lx_model_id}")
    print(f"  - API Key Set: {'Yes' if api_key else 'No'}")
    print("="*50)
    # --- END DEBUG ---

    try:
        result = lx.extract(
            text_or_documents=text_or_url,
            prompt_description=prompt,
            examples=ex,
            model_id=lx_model_id,
            api_key=api_key,
            fence_output=True,
            use_schema_constraints=False,
        )
    except Exception as e:
        print("="*50)
        print("❌ CRITICAL: LangExtract failed with an exception!")
        print(f"   Error: {e}")
        import traceback
        traceback.print_exc()
        print("="*50)
        # Возвращаем пустой результат, чтобы не ломать весь процесс
        return {"job_id": "error", "items": []}
    
    job_id = uuid.uuid4().hex[:8]
    out_dir = os.path.join("data", "extracts", job_id); os.makedirs(out_dir, exist_ok=True)
    lx.io.save_annotated_documents([result], output_name="result.jsonl", output_dir=out_dir)
    html = lx.visualize(os.path.join(out_dir, "result.jsonl"))
    with open(os.path.join(out_dir, "viz.html"), "w", encoding="utf-8") as f:
        f.write(html.data if hasattr(html, 'data') else html)
    flat = []
    # Обрабатываем новую структуру LangExtract - result может быть AnnotatedDocument
    if hasattr(result, 'documents'):
        # Старая структура
        for doc in result.documents:
            for ann in doc.annotations:
                flat.append({"class": ann.extraction_class, "text": ann.extraction_text, "attributes": ann.attributes or {}, "doc_char_start": ann.char_start, "doc_char_end": ann.char_end})
    elif hasattr(result, 'extractions'):
        # Новая структура - result.extractions содержит список извлечений
        for extraction in result.extractions:
            flat.append({
                "class": extraction.extraction_class, 
                "text": extraction.extraction_text, 
                "attributes": extraction.attributes or {}, 
                "doc_char_start": getattr(extraction, 'char_start', 0), 
                "doc_char_end": getattr(extraction, 'char_end', 0)
            })
        print(f"✅ LangExtract успешно извлек {len(flat)} сущностей!")
    elif hasattr(result, 'annotations'):
        # Альтернативная структура - result.annotations
        for ann in result.annotations:
            flat.append({"class": ann.extraction_class, "text": ann.extraction_text, "attributes": ann.attributes or {}, "doc_char_start": ann.char_start, "doc_char_end": ann.char_end})
    else:
        # Если структура неизвестна, показываем отладочную информацию
        print(f"⚠️ Unknown LangExtract result structure: {type(result)}")
        print(f"Available attributes: {dir(result)}")
    
    return {"job_id": job_id, "items": flat}

def stream_extraction(text_or_url: str, prompt: Optional[str]=None) -> Generator[Dict[str, Any], None, None]:
    start = time.time()
    yield {"event":"start","t":0}
    time.sleep(0.2); yield {"event":"fetch","msg":"Получаем документ","t":time.time()-start}
    time.sleep(0.2); yield {"event":"analyze","msg":"LLM извлекает сущности","t":time.time()-start}
    res = run_extraction(text_or_url, prompt=prompt)
    time.sleep(0.2); yield {"event":"save","msg":"Сохраняем JSONL и визуализацию","t":time.time()-start,"job_id":res["job_id"]}
    time.sleep(0.2); yield {"event":"done","result":res,"t":time.time()-start}
